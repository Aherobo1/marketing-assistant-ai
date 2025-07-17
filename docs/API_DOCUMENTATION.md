# Marketing Assistant AI - API Documentation

## API Endpoints

### Generate Copy

Generates marketing copy based on the provided prompt and parameters.

**Endpoint**: `/generate-copy`  
**Method**: POST  
**Content-Type**: application/json

**Request Body**:
```json
{
  "prompt": "Write a social media post for our new product launch",
  "content_type": "social_media",
  "tone": "professional",
  "length": "medium",
  "include_cta": true,
  "reference_similar_content": true,
  "max_tokens": 1000
}
```

**Response**:
```json
{
  "content": "Generated marketing content",
  "metadata": {
    "content_type": "social_media",
    "timestamp": "2024-01-01T12:00:00Z",
    "alignment_score": 0.95
  }
}
```

### List User Queries

Retrieves historical user queries with pagination.

**Endpoint**: `/user-queries`  
**Method**: GET  
**Query Parameters**:
- `page` (optional, default: 1): Page number
- `limit` (optional, default: 10): Items per page
- `content_type` (optional): Filter by content type

**Response**:
```json
{
  "items": [
    {
      "prompt": "Write a social media post...",
      "parameters": {
        "content_type": "social_media",
        "tone": "professional",
        "length": "medium",
        "include_cta": true
      },
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "limit": 10,
    "pages": 5
  }
}
```

### Update Brand Style

Updates the brand style guidelines.

**Endpoint**: `/brand-style`  
**Method**: PUT  
**Content-Type**: application/json

**Request Body**:
```json
{
  "tone": ["professional", "friendly", "inspiring"],
  "voice_characteristics": ["clear", "direct", "empowering"],
  "taboo_words": ["cheap", "discount", "bargain"],
  "preferred_terms": {
    "customers": "clients",
    "products": "solutions",
    "problems": "challenges"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Brand style updated successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Add Training Data

Adds new marketing content for AI training.

**Endpoint**: `/training-data`  
**Method**: POST  
**Content-Type**: application/json

**Request Body**:
```json
{
  "content_type": "email",
  "content": "Dear valued client...",
  "metadata": {
    "campaign_name": "Spring Launch 2024",
    "performance_metrics": {
      "open_rate": 0.42,
      "click_rate": 0.15
    }
  }
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Training data added successfully",
  "data_id": "unique-identifier"
}
```

### List Training Data

Retrieves available training data with pagination.

**Endpoint**: `/training-data`  
**Method**: GET  
**Query Parameters**:
- `page` (optional, default: 1): Page number
- `limit` (optional, default: 10): Items per page
- `content_type` (optional): Filter by content type

**Response**:
```json
{
  "items": [
    {
      "id": "unique-identifier",
      "content_type": "email_campaign",
      "preview": "Dear valued client...",
      "added_at": "2024-01-01T12:00:00Z",
      "performance_metrics": {
        "open_rate": 0.42,
        "click_rate": 0.15
      }
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "limit": 10,
    "pages": 5
  }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

Error responses include detailed messages:

```json
{
  "status": "error",
  "message": "Detailed error message",
  "code": "ERROR_CODE"
}
```
