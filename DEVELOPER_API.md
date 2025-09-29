# Intelligence Ingestor API Documentation

## Overview
The Intelligence Ingestor is a FastAPI service that processes and stores community intelligence data in ChromaDB Cloud. It's designed to ingest posts and comments from various platforms and sources.

## Base URL
**Production:** `https://intelligence-ingestor-production.up.railway.app`

## Authentication
All endpoints require Bearer token authentication.

```http
Authorization: Bearer YOUR_TOKEN_HERE
```

## Endpoints

### Health Check
Check if the service and ChromaDB connection are healthy.

```http
GET /health
Authorization: Bearer YOUR_TOKEN_HERE
```

**Response:**
```json
{
  "status": "healthy",
  "chroma": "connected"
}
```

### Ingest Data
Process and store community intelligence data.

```http
POST /ingest?test=false
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN_HERE
```

**Query Parameters:**
- `test` (optional): Set to `true` to use the test collection instead of production

**Request Body:**
```json
{
  "platform": "string",      // Platform name (e.g., "Lovable", "Replit")
  "source": "string",        // Source name (e.g., "Reddit", "Discord")
  "id": "string",           // Original post/thread ID from source
  "timestamp": "2024-01-15T10:30:00Z",  // ISO 8601 format
  "deeplink": "https://example.com/post", // Direct link to content
  "author": "https://example.com/user",   // Author profile URL
  "title": "string",        // Post/comment title
  "body": "string",         // Content to embed
  "isComment": false        // true for comments, false for posts
}
```

**Response:**
```json
{
  "status": "success"
}
```

## Data Processing Behavior

### ID Generation
The service generates unique ChromaDB IDs based on:
- **Posts:** `{platform}_{source}_post_{id}`
- **Comments:** `{platform}_{source}_comment_{id}_{hash}`

Where `{hash}` is an 8-character MD5 hash of timestamp + author to ensure comment uniqueness.

### Duplicate Handling
- **Same ID sent twice:** The service uses `upsert` operations, so existing records are updated with new data
- **No error thrown:** Duplicate ingestion is handled gracefully
- **Metadata updated:** All metadata fields are refreshed with the latest values

### Content Chunking
Long content is automatically split into chunks:
- **Single chunk:** Uses base ChromaDB ID
- **Multiple chunks:** Appends `_chunk_{index}` to the ID
- **Metadata preserved:** Each chunk maintains full metadata context

### Metadata Structure
Each ingested item includes:
```json
{
  "platform": "source platform",
  "source": "content source",
  "original_id": "source ID",
  "timestamp": "ISO timestamp",
  "deeplink": "original URL",
  "author": "author profile URL",
  "title": "content title",
  "is_comment": true/false,
  "parent_post_id": "ID if comment",
  "ingested_at": "processing timestamp",
  "chunk_index": 0,
  "total_chunks": 1
}
```

## Error Responses

### Authentication Errors
```json
{
  "detail": "Invalid authentication token"
}
```

### Service Unavailable
```json
{
  "detail": "Service temporarily unavailable"
}
```

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Example Usage

### Ingest a Blog Post
```bash
curl -X POST "https://intelligence-ingestor-production.up.railway.app/ingest?test=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "Lovable",
    "source": "Reddit",
    "id": "abc123",
    "timestamp": "2024-01-15T10:30:00Z",
    "deeplink": "https://reddit.com/r/programming/comments/abc123",
    "author": "https://reddit.com/u/developer",
    "title": "How to Build Better APIs",
    "body": "Here are some best practices for API development...",
    "isComment": false
  }'
```

### Ingest a Comment
```bash
curl -X POST "https://intelligence-ingestor-production.up.railway.app/ingest?test=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "Replit",
    "source": "Discord",
    "id": "parent_post_id",
    "timestamp": "2024-01-15T10:35:00Z",
    "deeplink": "https://discord.com/channels/123/456/789",
    "author": "https://discord.com/users/987654",
    "title": "",
    "body": "Great point about API versioning!",
    "isComment": true
  }'
```

## Best Practices

1. **Use test collection:** Set `?test=true` during development
2. **Unique IDs:** Ensure source IDs are unique within platform+source combination
3. **Valid timestamps:** Use proper ISO 8601 format
4. **Meaningful titles:** Provide descriptive titles for posts (can be empty for comments)
5. **Error handling:** Check response status and handle failures gracefully

## Rate Limits
No explicit rate limits are currently enforced, but please be respectful of the service resources.

## Support
For issues or questions, please check the deployment logs or contact the development team.