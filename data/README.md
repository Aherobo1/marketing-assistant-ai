# Marketing Assistant AI - Data Directory

This directory contains the data used by the Marketing Assistant AI system.

## Structure

- **past_campaigns/**: Contains JSON files of past marketing campaigns used for training and reference
- **user_queries/**: Stores user queries and requests for analytics and model improvement
- **style_guidelines/**: Contains brand tone and voice guidelines
- **vector_store/**: Generated vector database for content retrieval (created automatically)
- **db/**: Contains SQLite database files for structured data storage

## File Formats

### Past Campaigns

Past campaign files are stored as JSON with the following structure:

```json
{
  "content": "The actual marketing content text",
  "content_type": "email_campaign|social_media|blog_post|etc",
  "metadata": {
    "campaign_name": "Name of the campaign",
    "performance_metrics": {
      "open_rate": 0.42,
      "click_rate": 0.15,
      "conversion_rate": 0.08
    },
    "content_type": "Same as above",
    "added_at": "2024-01-01T12:00:00Z",
    "training_data": true
  },
  "document_id": "unique-identifier",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### User Queries

User query files store information about requests made to the AI:

```json
{
  "prompt": "The user's prompt text",
  "parameters": {
    "content_type": "Type of content requested",
    "tone": "Requested tone",
    "length": "short|medium|long",
    "include_cta": true|false
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "generated_content": "The AI-generated content",
  "feedback": "Optional user feedback",
  "performance_score": 0.95
}
```

### Brand Style Guidelines

Brand style is stored as a JSON file with the following structure:

```json
{
  "brand_name": "Adriana James",
  "tone": ["professional", "friendly", "inspirational"],
  "voice_characteristics": ["clear", "direct", "empowering"],
  "taboo_words": ["cheap", "discount", "bargain"],
  "preferred_terms": {
    "customers": "clients",
    "products": "solutions",
    "problems": "challenges"
  },
  "last_updated": "2024-01-01T12:00:00Z",
  "version": "1.0"
}
```

## Data Management

### Adding Past Campaigns

1. Use the API endpoint `POST /training-data` with the appropriate JSON payload
2. Alternatively, add a JSON file to the `past_campaigns` directory following the format above

### Updating Brand Style

1. Use the API endpoint `PUT /brand-style` with the updated style guidelines
2. The system will automatically update the style file and create a backup

### Managing User Queries

1. User queries are automatically stored when using the generation API
2. Each query is stored with its parameters, generated content, and any feedback
3. Use the `GET /user-queries` endpoint to retrieve historical data with pagination

### Vector Store Management

The vector store is automatically maintained by the system:
1. New content is automatically embedded and added to the store
2. Similar content can be retrieved using the `POST /find-similar` endpoint
3. The store is periodically optimized for performance

## Backup and Maintenance

1. All JSON files are versioned and can be restored if needed
2. The SQLite database is automatically backed up daily
3. The vector store can be rebuilt from the source content if necessary
