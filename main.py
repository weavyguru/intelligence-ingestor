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

        collection = chroma_manager.get_or_create_collection(is_test=test)

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

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        logger.info(f"Successfully ingested {len(chunks)} chunks for ID: {request.id}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Failed to ingest data: {e}")

        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "chroma": "bypassed", "note": "Railway deployment test"}

if __name__ == "__main__":
    import uvicorn
    import os

    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get("PORT", 8000))

    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)