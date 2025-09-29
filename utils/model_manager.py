"""
Shared model manager to prevent ONNX corruption in multi-worker environments.
Uses file locking and proper initialization order.
"""
import os
import time
import logging
import tempfile
import threading
from pathlib import Path
import chromadb

logger = logging.getLogger(__name__)

class ModelManager:
    """Singleton model manager with file locking for multi-worker safety."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not ModelManager._initialized:
            self._lock_file = None
            self._model_ready = False
            ModelManager._initialized = True

    def ensure_model_ready(self):
        """Ensure ONNX model is ready with cross-platform process safety."""
        if self._model_ready:
            return True

        # Use a simple lock file approach that works on Windows
        lock_path = Path(tempfile.gettempdir()) / "chroma_model_init.lock"
        max_wait = 60  # Maximum wait time in seconds
        check_interval = 0.5

        for _ in range(int(max_wait / check_interval)):
            try:
                # Try to create lock file exclusively (atomic operation)
                with open(lock_path, 'x') as lock_file:
                    lock_file.write(str(os.getpid()))

                logger.info("Acquired model initialization lock")

                try:
                    # Check if model already exists and is valid
                    if self._check_model_exists():
                        logger.info("Model already exists and is valid")
                        self._model_ready = True
                        return True

                    # Initialize model
                    self._initialize_model()
                    self._model_ready = True
                    logger.info("Model initialization complete")
                    return True

                finally:
                    # Always clean up lock file
                    try:
                        lock_path.unlink()
                    except:
                        pass

            except FileExistsError:
                # Another process is initializing, wait
                logger.info("Waiting for another process to initialize model...")
                time.sleep(check_interval)

                # Check if model became ready
                if self._check_model_exists():
                    logger.info("Model initialized by another process")
                    self._model_ready = True
                    return True

            except Exception as e:
                logger.error(f"Model initialization error: {e}")
                try:
                    lock_path.unlink()
                except:
                    pass
                return False

        logger.error("Model initialization timeout")
        return False

    def _check_model_exists(self):
        """Check if ONNX model files exist and are valid."""
        model_path = Path.home() / ".cache" / "chroma" / "onnx_models" / "all-MiniLM-L6-v2" / "onnx" / "model.onnx"

        if not model_path.exists():
            return False

        # Check if file is not corrupted (basic size check)
        try:
            size = model_path.stat().st_size
            return size > 1000000  # Model should be > 1MB
        except:
            return False

    def _initialize_model(self):
        """Initialize the ONNX model by creating a test client and collection."""
        logger.info("Initializing ONNX model...")

        # Create a test client to trigger model download
        client = chromadb.CloudClient(
            api_key=os.getenv('CHROMA_API_KEY'),
            tenant=os.getenv('CHROMA_TENANT'),
            database=os.getenv('CHROMA_DATABASE')
        )

        # Create a temporary collection to trigger model initialization
        try:
            collection = client.get_or_create_collection(
                name="model-init-temp",
                metadata={"description": "Temporary collection for safe model initialization"}
            )

            # Trigger embedding generation
            collection.upsert(
                ids=["init_test"],
                documents=["Model initialization test"],
                metadatas=[{"purpose": "initialization"}]
            )

            # Clean up
            client.delete_collection(name="model-init-temp")

        except Exception as e:
            logger.warning(f"Model initialization collection error: {e}")
            # Don't fail if cleanup fails

# Global instance
model_manager = ModelManager()