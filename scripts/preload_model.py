#!/usr/bin/env python3
"""
Pre-load ChromaDB ONNX models to prevent multi-worker race conditions.
Run this script before starting multi-worker deployment.
"""

import logging
import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preload_chroma_models():
    """Pre-load ChromaDB models to avoid race conditions."""
    try:
        logger.info("Pre-loading ChromaDB ONNX models...")

        # Create client to trigger model download
        client = chromadb.CloudClient(
            api_key=os.getenv('CHROMA_API_KEY'),
            tenant=os.getenv('CHROMA_TENANT'),
            database=os.getenv('CHROMA_DATABASE')
        )

        # Create temporary collection to force model initialization
        collection = client.get_or_create_collection(
            name="model-preload-temp",
            metadata={"purpose": "Model preloading"}
        )

        # Trigger embedding generation to download all model files
        collection.upsert(
            ids=["preload_test"],
            documents=["This document triggers ONNX model download and initialization"],
            metadatas=[{"type": "preload"}]
        )

        # Clean up
        try:
            client.delete_collection(name="model-preload-temp")
        except:
            pass

        logger.info("✅ ChromaDB models pre-loaded successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to pre-load models: {e}")
        return False

if __name__ == "__main__":
    success = preload_chroma_models()
    exit(0 if success else 1)