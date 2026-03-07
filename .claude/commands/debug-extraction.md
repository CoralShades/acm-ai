---
description: Root-cause debug a failed extraction by correlating traces, state, logs, and DB records
allowed-tools: Bash, Read, Grep
argument-hint: <source_id>
---

# Debug Extraction

Comprehensive root-cause debugging for a failed or problematic extraction. Correlates Langfuse traces, LangGraph state, Docker logs, and SurrealDB records.

## Instructions

### 1. Parse Arguments

`$1` = source_id (required). If not provided, ask the user.

### 2. Step 1 — Langfuse Trace Analysis

```bash
LANGFUSE_URL="${LANGFUSE_BASE_URL:-http://localhost:3000}"

# Check if Langfuse is available
if curl -s "$LANGFUSE_URL/api/public/health" > /dev/null 2>&1; then
  echo "Langfuse: Available"

  # Fetch traces for this source
  curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
    "$LANGFUSE_URL/api/public/traces?sessionId=extraction-${SOURCE_ID}&limit=5" \
    | python -m json.tool
else
  echo "Langfuse: NOT AVAILABLE — skipping trace analysis"
fi
```

Look for: error spans, failed nodes, correction loop count, total duration.

### 3. Step 2 — LangGraph State (if dev server running)

```bash
if curl -s http://127.0.0.1:2024/ok > /dev/null 2>&1; then
  echo "LangGraph API: Available"
  curl -s "http://127.0.0.1:2024/threads?limit=5" | python -m json.tool
else
  echo "LangGraph API: NOT AVAILABLE — skipping state inspection"
fi
```

### 4. Step 3 — SurrealDB Records

```bash
# Check what records exist for this source
curl -s -X POST http://localhost:8000/sql \
  -H "Content-Type: application/json" \
  -H "NS: open_notebook" \
  -H "DB: development" \
  -u "root:root" \
  -d "SELECT count() as total, status FROM acm_record WHERE source_id = '${SOURCE_ID}' GROUP BY status;" \
  | python -m json.tool 2>/dev/null || echo "SurrealDB: NOT AVAILABLE"
```

### 5. Step 4 — Docker Log Analysis

```bash
echo "=== API Errors (last 50 lines) ==="
docker logs acm-ai-api 2>&1 | grep -i "error\|exception\|traceback" | tail -20 2>/dev/null || echo "No API container logs"

echo "=== Worker Errors (last 50 lines) ==="
docker logs acm-ai-worker 2>&1 | grep -i "error\|exception\|traceback" | tail -20 2>/dev/null || echo "No Worker container logs"
```

### 6. Step 5 — Synthesis

Combine findings into a structured diagnostic report:

```markdown
## Extraction Debug Report: {source_id}

### Summary
- **Status**: FAILED / PARTIAL / SLOW / UNKNOWN
- **Root Cause**: [one-line description]
- **Affected Stage**: [stage name]

### Data Sources Used
- Langfuse: [available/unavailable]
- LangGraph API: [available/unavailable]
- SurrealDB: [available/unavailable]
- Docker Logs: [available/unavailable]

### Trace Analysis
[Findings from Langfuse]

### State Analysis
[Findings from LangGraph]

### Database Records
- Total records: {count}
- By status: {breakdown}

### Log Analysis
[Errors found in Docker logs]

### Root Cause
[Synthesized root cause]

### Recommendations
1. [actionable step]
2. [actionable step]
```

## Notes

- This command works in degraded mode — it reports what it can find even if some services are unavailable
- The more services running, the more complete the diagnosis
- For best results, run with Langfuse enabled and LangGraph dev server active
