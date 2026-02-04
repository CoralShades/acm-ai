---
paths:
  - "migrations/**/*"
  - "open_notebook/database/**/*"
---

# SurrealDB Rules for ACM-AI

## Connection Configuration
```
URL: ws://localhost:8000/rpc
Namespace: open_notebook
Database: development
User: root
Password: root (dev only)
```

## Schema Migrations
Location: `migrations/`
- Auto-run on API startup
- Use sequential numbering: `001_initial.surql`

## Core Tables
- `notebook` - Container for sources and notes
- `source` - Uploaded documents and their processed content
- `note` - User and AI-generated notes
- `model` - AI model configurations
- `transformation` - Content transformation records
- `episode_profile` - Podcast/media episode data
- `speaker_profile` - Speaker identification data

## Relationships
```
source.notebook_id -> notebook
note.notebook_id -> notebook
```

## Vector Embeddings
Sources and notes can have vector embeddings for semantic search:
- Use `embedding` field
- Search with `vector::distance` functions

## Query Patterns
```surql
-- Fetch with relations
SELECT *, ->notebook.* FROM source WHERE notebook_id = $id;

-- Vector search
SELECT * FROM source WHERE embedding <|10|> $query_embedding;
```

## Repository Pattern
All database access through `open_notebook/database/`:
- Each entity has a dedicated repository
- Use async operations
