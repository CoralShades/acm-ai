---
description: Debug Pydantic validation failures via Logfire OTel spans in Langfuse
allowed-tools: Bash, Read, Grep
argument-hint: <source_id> [--models MODEL1,MODEL2]
---

# Debug Pydantic

Debug Pydantic validation failures for an extraction by examining Logfire OTel spans in Langfuse.

## Instructions

### 1. Safety Check

Verify Logfire is properly configured:

```bash
echo "=== Logfire Configuration ==="
echo "LOGFIRE_ENABLED:       ${LOGFIRE_ENABLED:-not set}"
echo "LANGFUSE_ENABLED:      ${LANGFUSE_ENABLED:-not set}"
echo "LANGFUSE_PUBLIC_KEY:   ${LANGFUSE_PUBLIC_KEY:+SET}"
echo "LANGFUSE_SECRET_KEY:   ${LANGFUSE_SECRET_KEY:+SET}"
```

If `LOGFIRE_ENABLED` is not `true`, explain that Pydantic tracing requires:
1. `LOGFIRE_ENABLED=true` in `.env`
2. `LANGFUSE_ENABLED=true` with valid keys
3. `logfire` package installed (`uv add logfire`)

### 2. Parse Arguments

- `$1` = source_id (required)
- `--models` = comma-separated list of Pydantic model names to focus on (optional)

Default model set (safe for instrumentation):
- `ACMExtractionRecord`
- `BuildingRoomContext`
- `ACMItemRecord`
- `ACMExtractionResult`
- `ACMItemExtractionResult`
- `NormalizedExtractionResult`

### 3. Search Langfuse for OTel Spans

```bash
LANGFUSE_URL="${LANGFUSE_BASE_URL:-http://localhost:3000}"

# Search for Pydantic validation spans
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_URL/api/public/observations?type=SPAN&name=pydantic&limit=50" \
  | python -m json.tool
```

### 4. Analyze Results

For each Pydantic validation span:
- Check status (OK vs ERROR)
- Extract model name from span attributes
- For errors: extract validation error details
- Cross-reference with the trace's LLM output

### 5. Present Analysis

```markdown
## Pydantic Validation Report: {source_id}

### Configuration
- Logfire: {enabled/disabled}
- Instrumented Models: {list}

### Validation Results

| Model | Validations | Successes | Failures | Common Errors |
|-------|------------|-----------|----------|---------------|

### Failure Details

#### {Model Name} — {error count} failures
- **Error**: {validation error}
- **Field**: {field name}
- **Input**: {relevant input snippet}
- **Trace**: {trace_id}

### Recommendations
1. [field-level fix suggestions]
2. [prompt improvement suggestions]
```

### 6. Instrumentation Guidance

If no OTel spans found, provide guidance on enabling selective instrumentation:

```python
# Add to startup or test script (NEVER blanket instrument)
import logfire
logfire.instrument_pydantic(
    include={
        "ACMExtractionRecord",
        "BuildingRoomContext",
        "ACMItemRecord",
    }
)
```

**WARNING**: Never suggest `logfire.instrument_pydantic()` without `include={}`. This causes ~48K traces per run.
