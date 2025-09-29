import chromadb
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class ChromaClientManager:
    def __init__(self):
        self._client: Optional[chromadb.Client] = None

    def get_client(self) -> chromadb.Client:
        if self._client is None:
            try:
                # ChromaDB 0.3.29 uses HttpClient for cloud connections
                self._client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    port=443,
                    ssl=True,
                    headers={
                        "Authorization": f"Bearer {os.getenv('CHROMA_API_KEY')}",
                        "X-Chroma-Token": os.getenv('CHROMA_API_KEY')
                    }
                )
                logger.info("Chroma Cloud client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Chroma client: {e}")
                raise
        return self._client

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

    def health_check(self) -> bool:
        try:
            client = self.get_client()
            client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"Chroma health check failed: {e}")
            return False

chroma_manager = ChromaClientManager()