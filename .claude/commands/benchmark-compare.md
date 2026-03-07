---
description: Compare extraction benchmark results across models (accuracy, cost, speed)
allowed-tools: Bash, Read, Glob, Grep
argument-hint: <source_id> [--models model1,model2]
---

# Benchmark Compare

Compare extraction results across different models for the same source document.

## Instructions

### 1. Parse Arguments

- `$1` = source_id (required)
- `--models` = comma-separated model names to compare (optional, default: all available)

### 2. Find Benchmark Data

Look for existing benchmark results:

```bash
# Check for E36 benchmark logs
ls docs/sprint-artifacts/e36/logs/*.json 2>/dev/null

# Check for Langfuse traces with different models
LANGFUSE_URL="${LANGFUSE_BASE_URL:-http://localhost:3000}"
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_URL/api/public/traces?sessionId=extraction-${SOURCE_ID}&limit=20" \
  | python -m json.tool
```

### 3. Extract Metrics per Model

For each model/run found, extract:
- Records extracted
- Total duration
- Total cost
- Token usage
- Correction loop count
- Error count

### 4. Present Comparison

```markdown
## Benchmark Comparison: {source_id}

### Model Comparison

| Metric | {Model 1} | {Model 2} | {Model 3} |
|--------|-----------|-----------|-----------|
| Records Extracted | | | |
| Duration (s) | | | |
| Total Cost ($) | | | |
| Prompt Tokens | | | |
| Completion Tokens | | | |
| Correction Loops | | | |
| Errors | | | |
| Cost/Record ($) | | | |

### Winner by Category
- **Accuracy** (most records): {model}
- **Speed** (lowest duration): {model}
- **Cost** (lowest total): {model}
- **Efficiency** (lowest cost/record): {model}

### Recommendations
[Which model to use for production based on trade-offs]
```

### 5. If No Data Available

Report: "No benchmark data found for source {source_id}. Run extractions with different models first, or check E36 benchmark logs at docs/sprint-artifacts/e36/logs/"
