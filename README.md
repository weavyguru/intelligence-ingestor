# Chroma Vector DB Middleware

A Python middleware service that ingests community data from various sources (Reddit, Discord, etc.) about development platforms (Lovable, Replit, etc.) and stores it in Chroma Cloud vector database.

## Features

- **FastAPI REST API** with bearer token authentication
- **Chroma Cloud integration** with automatic collection management
- **Smart content chunking** for optimal vector embedding
- **Duplicate handling** with upsert operations
- **Parent-child relationships** for comments and posts
- **Comprehensive error handling** and logging
- **Health monitoring** endpoint

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**🎉 Now with automated Azure deployment via GitHub Actions!**

### 2. Environment Setup

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env` file:
```
BEARER_TOKEN=your-secure-bearer-token-here
CHROMA_API_KEY=ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B
CHROMA_TENANT=cc8a08d9-0db3-472d-bc29-7a2b7cddbc55
CHROMA_DATABASE=weavy_community_intelligence
```

### 3. Start the Service

```bash
python main.py
```

The service will start on `http://localhost:8000`

## API Endpoints

### POST /ingest

Ingest community content into Chroma database.

**Query Parameters:**
- `test` (optional, boolean): Use test collection if true

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
    "platform": "Lovable",
    "source": "Reddit",
    "id": "abc123",
    "timestamp": "2024-01-15T10:30:00Z",
    "deeplink": "https://reddit.com/r/programming/comments/abc123",
    "author": "https://reddit.com/u/testuser",
    "title": "Test Post Title",
    "body": "This is the main content of the post that will be embedded",
    "isComment": false
}
```

**Response:**
```json
{"status": "success"}
```

### GET /health

Check service health status.

**Response:**
```json
{"status": "healthy", "chroma": "connected"}
```

## Testing

### Test with a Post

```bash
curl -X POST "http://localhost:8000/ingest?test=true" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "Lovable",
    "source": "Reddit",
    "id": "abc123",
    "timestamp": "2024-01-15T10:30:00Z",
    "deeplink": "https://reddit.com/r/programming/comments/abc123",
    "author": "https://reddit.com/u/testuser",
    "title": "Test Post Title",
    "body": "This is the main content of the post that will be embedded",
    "isComment": false
  }'
```

### Test with a Comment

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "Replit",
    "source": "Discord",
    "id": "xyz789",
    "timestamp": "2024-01-15T10:35:00Z",
    "deeplink": "https://discord.com/channels/123/456/789",
    "author": "https://discord.com/users/123456789",
    "title": "",
    "body": "This is a comment on the original post",
    "isComment": true
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Architecture

### ID Generation Strategy

- **Posts**: `{platform}_{source}_post_{id}`
- **Comments**: `{platform}_{source}_comment_{id}_{unique_hash}`
- **Chunks**: Base ID + `_chunk_{index}` (if content is chunked)

### Content Chunking

- Maximum ~512 tokens per chunk
- Sentence boundary preservation
- Context overlap between chunks (~50 tokens)
- Title included with each chunk for posts
- Comments typically not chunked unless very long

### Collections

- **Production**: `community_content`
- **Test**: `community_content-test`

### Metadata Schema

Each document includes comprehensive metadata:

```python
{
    "platform": str,           # Lovable, Replit, etc.
    "source": str,             # Reddit, Discord, etc.
    "original_id": str,        # Original ID from request
    "timestamp": str,          # ISO 8601 timestamp
    "deeplink": str,           # Direct URL to content
    "author": str,             # Author URL
    "title": str,              # Content title
    "is_comment": bool,        # Comment flag
    "parent_post_id": str,     # Post ID if comment
    "chunk_index": int,        # 0-based chunk index
    "total_chunks": int,       # Total chunks for content
    "ingested_at": str         # Server ingestion timestamp
}
```

## Error Handling

- **400**: Invalid request format or missing fields
- **403**: Invalid authentication token
- **500**: Internal server error (embedding failures, etc.)
- **503**: Service unavailable (Chroma connection issues)

## Logging

The service provides comprehensive logging including:
- Request processing status
- Chunking information
- Collection operations
- Error details
- Performance metrics

Logs are written to stdout in structured format suitable for log aggregation.

## Security

- Bearer token authentication for all endpoints
- Input validation on all fields
- No sensitive data logged
- Environment-based configuration

## Development

### Project Structure

```
project/
├── main.py              # Main FastAPI application
├── .env                 # Environment variables (not in git)
├── .env.example         # Example environment file
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── utils/
    ├── __init__.py
    ├── chunking.py     # Content chunking logic
    └── chroma_client.py # Chroma connection management
```

### Local Development

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in `.env`
3. Run the service: `python main.py`
4. View API docs: `http://localhost:8000/docs`

The service includes automatic API documentation via FastAPI's built-in Swagger UI.

## Production Considerations

- Use a proper secret management system instead of `.env` files
- Implement rate limiting for production use
- Monitor Chroma storage usage and implement cleanup strategies
- Consider adding retry logic with exponential backoff
- Set up proper log aggregation and monitoring
- Use a process manager like systemd or docker for deployment