from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
import hashlib
import logging
import os
from dotenv import load_dotenv

from utils.chroma_client import chroma_manager
from utils.chunking import chunker

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chroma Vector DB Middleware",
    description="Community intelligence data ingestion service",
    version="1.0.0"
)

security = HTTPBearer()

class IngestRequest(BaseModel):
    platform: str = Field(..., description="Platform name (e.g., Lovable, Replit)")
    source: str = Field(..., description="Source name (e.g., Reddit, Discord)")
    id: str = Field(..., description="Original post/thread ID from source")
    timestamp: datetime = Field(..., description="Content timestamp in ISO 8601 format")
    deeplink: HttpUrl = Field(..., description="Direct link to content")
    author: HttpUrl = Field(..., description="Author profile URL")
    title: str = Field(..., description="Post/comment title")
    body: str = Field(..., description="Content to embed")
    isComment: bool = Field(..., description="True for comments, False for posts")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_token = os.getenv("BEARER_TOKEN")
    if not expected_token:
        logger.error("BEARER_TOKEN not configured")
        raise HTTPException(status_code=500, detail="Authentication not configured")

    if credentials.credentials != expected_token:
        logger.warning(f"Invalid token attempt: {credentials.credentials[:10]}...")
        raise HTTPException(status_code=403, detail="Invalid authentication token")

    return credentials.credentials

def generate_chroma_id(data: dict) -> str:
    platform = data['platform'].lower().replace(' ', '_')
    source = data['source'].lower().replace(' ', '_')

    if data['isComment']:
        unique_hash = hashlib.md5(
            f"{data['timestamp']}{data['author']}".encode()
        ).hexdigest()[:8]
        return f"{platform}_{source}_comment_{data['id']}_{unique_hash}"
    else:
        return f"{platform}_{source}_post_{data['id']}"

@app.post("/ingest")
async def ingest_data(
    request: IngestRequest,
    test: bool = Query(False, description="Use test collection if true"),
    token: str = Depends(verify_token)
):
    try:
        logger.info(f"Processing {request.source} {request.platform} {'comment' if request.isComment else 'post'} ID: {request.id}")

        collection = await chroma_manager.get_or_create_collection_async(is_test=test)

        base_chroma_id = generate_chroma_id(request.model_dump())

        base_metadata = {
            "platform": request.platform,
            "source": request.source,
            "original_id": request.id,
            "timestamp": request.timestamp.isoformat(),
            "deeplink": str(request.deeplink),
            "author": str(request.author),
            "title": request.title,
            "is_comment": request.isComment,
            "parent_post_id": request.id if request.isComment else None,
            "ingested_at": datetime.utcnow().isoformat()
        }

        chunks = chunker.prepare_chunks_with_metadata(
            content=request.body,
            base_metadata=base_metadata,
            title=request.title if not request.isComment else "",
            is_comment=request.isComment
        )

        ids = []
        documents = []
        metadatas = []

        for chunk_data in chunks:
            chunk_index = chunk_data["metadata"]["chunk_index"]

            if len(chunks) > 1:
                chroma_id = f"{base_chroma_id}_chunk_{chunk_index}"
            else:
                chroma_id = base_chroma_id

            ids.append(chroma_id)
            documents.append(chunk_data["content"])
            metadatas.append(chunk_data["metadata"])

        await chroma_manager.upsert_async(collection, ids, documents, metadatas)

        logger.info(f"Successfully ingested {len(chunks)} chunks for ID: {request.id}")

        return {
            "status": "success",
            "chroma_ids": ids,
            "chunks_created": len(chunks),
            "base_id": base_chroma_id
        }

    except Exception as e:
        logger.error(f"Failed to ingest data: {e}")

        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    try:
        is_healthy = await chroma_manager.health_check_async()
        if is_healthy:
            return {"status": "healthy", "chroma": "connected"}
        else:
            raise HTTPException(status_code=503, detail="Chroma database unavailable")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/retrieve/{chroma_id}")
async def retrieve_by_id(
    chroma_id: str,
    test: bool = Query(False, description="Use test collection if true"),
    token: str = Depends(verify_token)
):
    try:
        collection = await chroma_manager.get_or_create_collection_async(is_test=test)

        result = await chroma_manager.get_async(collection, [chroma_id])

        if not result["ids"]:
            raise HTTPException(status_code=404, detail="Content not found")

        return {
            "id": result["ids"][0],
            "content": result["documents"][0] if result["documents"] else None,
            "metadata": result["metadatas"][0] if result["metadatas"] else None
        }
    except Exception as e:
        logger.error(f"Failed to retrieve content: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@app.post("/search")
async def semantic_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results to return"),
    test: bool = Query(False, description="Use test collection if true"),
    token: str = Depends(verify_token)
):
    try:
        collection = await chroma_manager.get_or_create_collection_async(is_test=test)

        results = await chroma_manager.query_async(collection, [query], limit)

        if not results["ids"] or not results["ids"][0]:
            return {
                "query": query,
                "results": [],
                "count": 0
            }

        search_results = []
        for i in range(len(results["ids"][0])):
            search_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i] if results["documents"] and results["documents"][0] else None,
                "metadata": results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else None,
                "distance": results["distances"][0][i] if results["distances"] and results["distances"][0] else None
            })

        return {
            "query": query,
            "results": search_results,
            "count": len(search_results)
        }
    except Exception as e:
        logger.error(f"Failed to perform search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import os

    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get("PORT", 8000))

    # Get number of workers from environment variable
    workers = int(os.environ.get("WORKERS", 4))

    # In production, use multiple workers for better throughput
    # For development, you can set WORKERS=1 to disable multiprocessing
    logger.info(f"Starting server on port {port} with {workers} workers")

    if workers > 1:
        uvicorn.run(
            "main:app",  # Use module:app format for multiprocessing
            host="0.0.0.0",
            port=port,
            workers=workers,
            access_log=False,  # Reduce logging overhead in production
            log_level="info"
        )
    else:
        # Single worker mode for development
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")