# RAG Integration for Large Documentation

> **Using Retrieval Augmented Generation for documentation that exceeds context limits**

---

## When to Use RAG

| Documentation Size | Strategy |
|-------------------|----------|
| <40K chars | Load directly or split |
| 40K-100K chars | Split into chunks, use imports |
| >100K chars | **Use RAG** |
| Multiple large docs | **Use RAG** |
| Semantic search needed | **Use RAG** |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Context Window (limited)                        │   │
│  │  - CLAUDE.md (~8K)                              │   │
│  │  - Current conversation                          │   │
│  │  - RAG query results (~2-4K per query)          │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                         │ Query                         │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │  RAG Agent (n8n / Flowise / Custom)             │   │
│  │  - Semantic search                               │   │
│  │  - Returns relevant chunks only                  │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                         │ Vector Search                 │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Vector Store (Qdrant / Supabase / Pinecone)    │   │
│  │  - All documentation embedded                    │   │
│  │  - Chunked and indexed                          │   │
│  │  - Fast similarity search                        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Option 1: n8n RAG Workflow (Recommended)

Use the V3 Agentic RAG workflow from ai-base.

### Setup

1. **Import the workflow**:
   ```
   n8n/backup/workflows/V3_Local_Agentic_RAG_AI_Agent_MultiSchema.json
   ```

2. **Configure for documentation**:
   - Set file trigger to watch `docs/` directory
   - Configure embedding model: `nomic-embed-text`
   - Set up Postgres/Qdrant vector store

3. **Add webhook endpoint to CLAUDE.md**:
   ```markdown
   ## Documentation Lookup (RAG)

   For large documentation queries, use the RAG endpoint:
   - Endpoint: http://localhost:5678/webhook/rag-lookup
   - Method: POST
   - Body: {"query": "your question", "project_key": "default"}
   ```

### Query Pattern

When Claude needs information from large docs:

```markdown
User: What are the requirements for user authentication?

Claude: Let me search the documentation for authentication requirements.
        [Calls RAG endpoint with query: "user authentication requirements"]

        Based on the documentation search results:
        - SSO integration required (Epic E-001)
        - OAuth2 with PKCE flow
        - Session timeout: 30 minutes
        - MFA optional for v1
```

---

## Option 2: MCP-Based RAG

Use Supabase MCP for direct vector search.

### Configuration

In `.claude/settings.json`:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@anthropic/supabase-mcp"],
      "env": {
        "SUPABASE_URL": "http://localhost:8000",
        "SUPABASE_SERVICE_ROLE_KEY": "${SERVICE_ROLE_KEY}"
      }
    }
  }
}
```

### Query via MCP

```sql
-- Semantic search for documentation
SELECT content, metadata, 1 - (embedding <=> query_embedding) as similarity
FROM project_default.documents
WHERE 1 - (embedding <=> query_embedding) > 0.7
ORDER BY similarity DESC
LIMIT 5;
```

---

## Option 3: Custom RAG Command

Create a `/rag` command for documentation lookup.

### File: `.claude/commands/rag.md`

```markdown
---
description: Search large documentation using RAG
allowed-tools: Bash, WebFetch
argument-hint: <query>
---

# RAG Documentation Search

Search embedded documentation for relevant information.

## Process

1. **Construct query** from user input: $ARGUMENTS

2. **Call RAG endpoint**:
   ```bash
   curl -s -X POST http://localhost:5678/webhook/rag-lookup \
     -H "Content-Type: application/json" \
     -d '{"query": "$ARGUMENTS", "project_key": "default", "limit": 5}'
   ```

3. **Parse results** and present relevant excerpts

4. **Cite sources** with file paths and chunk references

## Output Format

For each relevant result:
- Source: [file path]
- Relevance: [similarity score]
- Content: [relevant excerpt]
```

---

## Document Preparation for RAG

### Chunking Strategy

| Document Type | Chunk Size | Overlap |
|--------------|------------|---------|
| Epics | By story | 100 chars |
| API Docs | By endpoint | 50 chars |
| Architecture | By section | 200 chars |
| Requirements | By requirement | 100 chars |

### Metadata to Include

```json
{
  "file_path": "docs/epics/epic-001.md",
  "title": "User Authentication Epic",
  "type": "epic",
  "epic_id": "E-001",
  "status": "active",
  "last_updated": "2026-01-12",
  "tags": ["auth", "security", "mvp"]
}
```

### Embedding Workflow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Watch      │────▶│   Chunk      │────▶│   Embed      │
│   docs/      │     │   Content    │     │   Chunks     │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   Store in   │
                                          │   Vector DB  │
                                          └──────────────┘
```

---

## CLAUDE.md Integration

Add this section to your CLAUDE.md:

```markdown
## Large Documentation Access

### Directly Loadable (<40K chars)
- Project overview: This file
- API quick reference: @docs/api/quick-ref.md
- Current sprint: @docs/sprints/current.md

### RAG-Indexed (>40K chars)
Use `/rag <query>` to search:
- Full epic specifications
- Complete API documentation
- Historical requirements
- Decision logs

### Example Queries
- `/rag authentication requirements`
- `/rag API rate limiting`
- `/rag database schema for users`
```

---

## RAG Agent Configuration

### For n8n V3 Workflow

Modify the AI Agent node tools:

```json
{
  "tools": [
    {
      "name": "lookup_documentation",
      "description": "Search project documentation for relevant information",
      "parameters": {
        "query": "The search query",
        "doc_type": "epic|api|architecture|requirement (optional filter)"
      }
    },
    {
      "name": "list_documents",
      "description": "List all indexed documents with metadata"
    },
    {
      "name": "get_document_section",
      "description": "Get a specific section from a document",
      "parameters": {
        "file_path": "Path to the document",
        "section": "Section heading to retrieve"
      }
    }
  ]
}
```

---

## Query Optimization

### Good Queries (Semantic)

```
✅ "What are the acceptance criteria for user login?"
✅ "How does the payment flow work?"
✅ "What database tables store user data?"
```

### Bad Queries (Too Vague)

```
❌ "Tell me about the project"
❌ "What's in the docs?"
❌ "Everything about authentication"
```

### Query Enhancement

When processing queries:
1. Extract key concepts
2. Add context from current task
3. Include relevant metadata filters

```markdown
Original: "auth requirements"
Enhanced: "user authentication requirements acceptance criteria epic security"
```

---

## Performance Considerations

### Vector Store Selection

| Store | Best For | Latency |
|-------|----------|---------|
| Qdrant | Self-hosted, fast | <50ms |
| Supabase pgvector | Integrated with DB | <100ms |
| Pinecone | Cloud, scalable | <100ms |
| Chroma | Local dev | <50ms |

### Embedding Model Selection

| Model | Dimensions | Quality | Speed |
|-------|-----------|---------|-------|
| nomic-embed-text | 768 | Good | Fast |
| text-embedding-3-small | 1536 | Better | Medium |
| text-embedding-3-large | 3072 | Best | Slow |

### Cache Strategy

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Query      │────▶│   Check      │────▶│   Return     │
│   Received   │     │   Cache      │     │   Cached     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │ Miss
                            ▼
                     ┌──────────────┐
                     │   Vector     │
                     │   Search     │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Cache      │
                     │   Result     │
                     └──────────────┘
```

---

## Troubleshooting

### No Results Returned

1. Check if documents are embedded
2. Verify embedding model matches
3. Lower similarity threshold (try 0.5)
4. Check query for typos

### Irrelevant Results

1. Improve chunking strategy
2. Add metadata filters
3. Use more specific queries
4. Increase similarity threshold

### Slow Queries

1. Check vector index exists
2. Reduce result limit
3. Add metadata pre-filters
4. Consider caching

---

## Quick Start Checklist

```markdown
□ Vector store running (Qdrant/Supabase)
□ Embedding model available (Ollama nomic-embed-text)
□ Documents chunked and indexed
□ n8n workflow imported and active
□ Webhook endpoint accessible
□ CLAUDE.md updated with RAG instructions
□ /rag command created (optional)
□ Test query successful
```
