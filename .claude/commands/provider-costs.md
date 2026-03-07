---
description: Analyze extraction costs by provider and model
allowed-tools: Bash
argument-hint: [--since YYYY-MM-DD] [--provider MODEL] [--top N]
---

# Provider Costs

Aggregate ACM extraction costs by provider/model from Langfuse GENERATION observations.

## Instructions

### 1. Check Langfuse Configuration

```bash
if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ]; then
  echo "ERROR: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set"
  exit 1
fi
```

### 2. Fetch GENERATION Observations

```bash
LANGFUSE_URL="${LANGFUSE_BASE_URL:-http://localhost:3000}"

# Fetch LLM call observations
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_URL/api/public/observations?type=GENERATION&limit=200" \
  | python -m json.tool
```

### 3. Aggregate by Model

Parse the response and group by `model` field. For each model, calculate:
- Number of calls
- Total prompt tokens
- Total completion tokens
- Total cost
- Average cost per call

### 4. Present Cost Breakdown

```markdown
## Provider Cost Analysis

### Period: {from_date} to {to_date}

| Model | Calls | Prompt Tokens | Completion Tokens | Total Cost | Avg Cost/Call |
|-------|-------|---------------|-------------------|------------|---------------|

### Top Expensive Extractions

| Source ID | Model | Cost | Duration | Records |
|-----------|-------|------|----------|---------|

### Summary
- Total Spend: ${total}
- Most Used Model: {model}
- Most Expensive Model: {model}
- Avg Cost per Extraction: ${avg}
```

### 5. Handle Arguments

- `--since`: Filter observations by `fromTimestamp` parameter
- `--provider`: Filter to specific model name
- `--top`: Limit to top N most expensive (default: 10)

### 6. If No Data

Report: "No GENERATION observations found. Have any extractions been run with LANGFUSE_ENABLED=true?"
