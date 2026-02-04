---
description: Search large documentation using RAG vector search
allowed-tools: Bash, WebFetch
argument-hint: <query>
---

# RAG Documentation Search

Search embedded documentation for relevant information using semantic similarity.

## When to Use

- Documentation too large to load directly (>40K chars)
- Need to find specific information across many files
- Semantic search (concept matching, not just keywords)

## Process

1. **Parse query**: $ARGUMENTS

2. **Call RAG endpoint**:
   ```bash
   curl -s -X POST http://localhost:5678/webhook/rag-lookup \
     -H "Content-Type: application/json" \
     -d '{
       "query": "$ARGUMENTS",
       "project_key": "default",
       "limit": 5,
       "threshold": 0.7
     }'
   ```

3. **Parse results**:
   - Extract relevant chunks
   - Note source files
   - Check similarity scores

4. **Present findings**:
   - Summarize key information
   - Cite sources with file paths
   - Suggest follow-up queries if needed

## Configuration

Update these values based on your setup:

| Setting | Default | Description |
|---------|---------|-------------|
| Endpoint | localhost:5678 | n8n webhook URL |
| project_key | default | Multi-schema project |
| limit | 5 | Max results |
| threshold | 0.7 | Min similarity (0-1) |

## Output Format

```markdown
## Search Results for: "$ARGUMENTS"

### Result 1 (Similarity: 0.89)
**Source**: docs/epics/epic-001-auth.md
**Section**: Acceptance Criteria

> [Relevant excerpt from the document]

### Result 2 (Similarity: 0.82)
**Source**: docs/requirements/security.md
**Section**: Authentication Requirements

> [Relevant excerpt from the document]

---

**Summary**: [Brief synthesis of findings]

**Related Queries**:
- [Suggested follow-up query 1]
- [Suggested follow-up query 2]
```

## Troubleshooting

### No results
- Lower threshold to 0.5
- Check if documents are indexed
- Try broader query terms

### Irrelevant results
- Raise threshold to 0.8
- Be more specific in query
- Add context: "authentication for mobile app"

### Endpoint not responding
- Check n8n is running: `docker ps | grep n8n`
- Verify webhook URL is correct
- Check workflow is active
