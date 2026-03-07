---
description: Inspect Langfuse traces for a source extraction
allowed-tools: Bash
argument-hint: <source_id> [--since YYYY-MM-DD] [--limit N]
---

# Trace Inspect

Fetch and display Langfuse traces for a source extraction, showing a waterfall view with durations, costs, and correction loop counts.

## Instructions

### 1. Parse Arguments

- `$1` = source_id (required)
- `--since` = date filter (optional, default: last 7 days)
- `--limit` = max traces to fetch (optional, default: 10)

If no source_id provided, ask the user for one.

### 2. Check Langfuse Configuration

```bash
if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ]; then
  echo "ERROR: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in .env"
  echo "Set LANGFUSE_ENABLED=true and configure keys to use trace inspection."
  exit 1
fi
```

### 3. Fetch Traces

```bash
LANGFUSE_URL="${LANGFUSE_BASE_URL:-http://localhost:3000}"
SOURCE_ID="$1"
SESSION_ID="extraction-${SOURCE_ID}"

# Fetch traces for this session
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_URL/api/public/traces?sessionId=${SESSION_ID}&limit=10" \
  | python -m json.tool
```

### 4. For Each Trace, Fetch Observations

```bash
# Get detailed trace with observations
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_URL/api/public/traces/{trace_id}" \
  | python -m json.tool
```

### 5. Build Waterfall View

Present results as a markdown table:

```markdown
## Trace Waterfall: {source_id}

### Traces Found: {count}

| Trace ID | Name | Duration | Status | Cost | LLM Calls |
|----------|------|----------|--------|------|-----------|

### Span Details (Latest Trace)

| Span | Type | Duration | Model | Tokens (in/out) | Cost |
|------|------|----------|-------|-----------------|------|

### Summary
- Total Cost: ${total}
- Total Duration: {duration}s
- Correction Loops: {count}
- Records Extracted: {count}
```

### 6. Handle Edge Cases

- No traces found: Report "No traces found for session extraction-{source_id}. Is LANGFUSE_ENABLED=true?"
- Langfuse unreachable: Report "Cannot reach Langfuse at {url}. Is the service running?"
- No observations: Report trace exists but has no spans (may be in progress)
