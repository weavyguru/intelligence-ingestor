import chromadb
import logging
import os
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List
from queue import Queue
import time

logger = logging.getLogger(__name__)

class ChromaClientManager:
    def __init__(self):
        self._client_pool: List[chromadb.CloudClient] = []
        self._pool_size = int(os.getenv('CHROMA_POOL_SIZE', '10'))
        self._available_clients = Queue()
        self._lock = threading.Lock()
        self._thread_pool = ThreadPoolExecutor(max_workers=20)
        self._initialized = False

    def _initialize_pool(self):
        """Initialize the connection pool with multiple ChromaDB clients."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            logger.info(f"Initializing ChromaDB connection pool with {self._pool_size} connections")

            for i in range(self._pool_size):
                try:
                    client = chromadb.CloudClient(
                        api_key=os.getenv('CHROMA_API_KEY'),
                        tenant=os.getenv('CHROMA_TENANT'),
                        database=os.getenv('CHROMA_DATABASE')
                    )
                    self._client_pool.append(client)
                    self._available_clients.put(client)
                    logger.debug(f"Created client {i+1}/{self._pool_size}")
                except Exception as e:
                    logger.error(f"Failed to create client {i+1}: {e}")
                    raise

            # Pre-warm the embedding model to avoid race conditions
            self._prewarm_model()

            self._initialized = True
            logger.info("ChromaDB connection pool initialized successfully")

    def _prewarm_model(self):
        """Pre-warm the ONNX embedding model to avoid initialization race conditions."""
        try:
            logger.info("Pre-warming ChromaDB embedding model...")

            # Get a client and create a temporary collection
            client = self._client_pool[0] if self._client_pool else self.get_client()

            # Create a minimal test collection to trigger model loading
            test_collection = client.get_or_create_collection(
                name="__model_prewarm__",
                metadata={"description": "Temporary collection for model pre-warming"}
            )

            # Add a small test document to trigger embedding model initialization
            test_collection.upsert(
                ids=["prewarm_test"],
                documents=["Test document for model initialization"],
                metadatas=[{"type": "prewarm"}]
            )

            # Clean up the test collection
            try:
                client.delete_collection(name="__model_prewarm__")
                logger.info("ChromaDB embedding model pre-warmed successfully")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup prewarm collection: {cleanup_error}")

        except Exception as e:
            logger.warning(f"Model pre-warming failed (continuing anyway): {e}")
            # Don't fail initialization if pre-warming fails

    def get_client(self) -> chromadb.CloudClient:
        """Get a client from the pool. Falls back to creating a new one if pool is not ready."""
        if not self._initialized:
            self._initialize_pool()

        try:
            # Try to get a client from the pool (non-blocking)
            client = self._available_clients.get_nowait()
            return client
        except:
            # If no clients available, create a temporary one
            logger.warning("No pooled clients available, creating temporary client")
            return chromadb.CloudClient(
                api_key=os.getenv('CHROMA_API_KEY'),
                tenant=os.getenv('CHROMA_TENANT'),
                database=os.getenv('CHROMA_DATABASE')
            )

    def return_client(self, client: chromadb.CloudClient):
        """Return a client to the pool."""
        if client in self._client_pool:
            self._available_clients.put(client)

    def get_collection_name(self, is_test: bool = False) -> str:
        base_name = "community_content"
        return f"{base_name}-test" if is_test else base_name

    def get_or_create_collection(self, is_test: bool = False):
        client = self.get_client()
        collection_name = self.get_collection_name(is_test)

        try:
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Community intelligence data collection"}
            )
            logger.info(f"Collection '{collection_name}' ready")
            return collection
        except Exception as e:
            logger.error(f"Failed to get/create collection '{collection_name}': {e}")
            raise
        finally:
            self.return_client(client)

    async def get_or_create_collection_async(self, is_test: bool = False):
        """Async version of get_or_create_collection using thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._thread_pool,
            self.get_or_create_collection,
            is_test
        )

    def health_check(self) -> bool:
        try:
            client = self.get_client()
            client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"Chroma health check failed: {e}")
            return False
        finally:
            self.return_client(client)

    async def health_check_async(self) -> bool:
        """Async version of health_check using thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._thread_pool,
            self.health_check
        )

    async def upsert_async(self, collection, ids: List[str], documents: List[str], metadatas: List[dict]):
        """Async upsert operation using thread pool."""
        def _upsert():
            return collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._thread_pool, _upsert)

    async def query_async(self, collection, query_texts: List[str], n_results: int):
        """Async query operation using thread pool."""
        def _query():
            return collection.query(
                query_texts=query_texts,
                n_results=n_results
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._thread_pool, _query)

    async def get_async(self, collection, ids: List[str]):
        """Async get operation using thread pool."""
        def _get():
            return collection.get(ids=ids)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._thread_pool, _get)

    def __init_batching__(self):
        """Initialize batching functionality."""
        self._batch_queue = []
        self._batch_size = int(os.getenv('CHROMA_BATCH_SIZE', '50'))
        self._batch_timeout = float(os.getenv('CHROMA_BATCH_TIMEOUT', '1.0'))
        self._last_batch_time = time.time()
        self._batch_lock = threading.Lock()

    async def add_to_batch(self, operation_type: str, **kwargs):
        """Add operation to batch queue."""
        if not hasattr(self, '_batch_queue'):
            self.__init_batching__()

        with self._batch_lock:
            batch_item = {
                'type': operation_type,
                'timestamp': time.time(),
                'future': asyncio.Future(),
                **kwargs
            }
            self._batch_queue.append(batch_item)

            # Check if we should process the batch
            current_time = time.time()
            should_process = (
                len(self._batch_queue) >= self._batch_size or
                current_time - self._last_batch_time >= self._batch_timeout
            )

            if should_process:
                asyncio.create_task(self._process_batch())

            return await batch_item['future']

    async def _process_batch(self):
        """Process queued batch operations."""
        if not hasattr(self, '_batch_queue'):
            return

        with self._batch_lock:
            if not self._batch_queue:
                return

            current_batch = self._batch_queue.copy()
            self._batch_queue.clear()
            self._last_batch_time = time.time()

        # Group operations by type and collection
        operation_groups = {}
        for item in current_batch:
            key = (item['type'], item.get('collection_name', 'default'))
            if key not in operation_groups:
                operation_groups[key] = []
            operation_groups[key].append(item)

        # Process each group
        for (op_type, collection_name), items in operation_groups.items():
            try:
                if op_type == 'upsert':
                    await self._batch_upsert(items)
                elif op_type == 'query':
                    await self._batch_query(items)
                # Add more batch operations as needed
            except Exception as e:
                # Set exception on all futures in the batch
                for item in items:
                    if not item['future'].done():
                        item['future'].set_exception(e)

    async def _batch_upsert(self, items):
        """Process batch upsert operations."""
        if not items:
            return

        # Combine all upsert data
        all_ids = []
        all_documents = []
        all_metadatas = []

        for item in items:
            all_ids.extend(item['ids'])
            all_documents.extend(item['documents'])
            all_metadatas.extend(item['metadatas'])

        try:
            # Get collection from first item
            collection = items[0]['collection']

            # Perform batch upsert
            result = await self.upsert_async(collection, all_ids, all_documents, all_metadatas)

            # Set results for all futures
            for item in items:
                if not item['future'].done():
                    item['future'].set_result(result)

        except Exception as e:
            for item in items:
                if not item['future'].done():
                    item['future'].set_exception(e)

    async def _batch_query(self, items):
        """Process batch query operations."""
        # For queries, we still process them individually as they have different parameters
        for item in items:
            try:
                result = await self.query_async(
                    item['collection'],
                    item['query_texts'],
                    item['n_results']
                )
                if not item['future'].done():
                    item['future'].set_result(result)
            except Exception as e:
                if not item['future'].done():
                    item['future'].set_exception(e)

chroma_manager = ChromaClientManager()