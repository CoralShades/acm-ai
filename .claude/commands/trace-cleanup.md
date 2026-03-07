---
description: Delete Langfuse traces matching criteria (with dry-run safety)
allowed-tools: Bash
argument-hint: [--tag TAG] [--name PATTERN] [--before DATE] [--dry-run]
---

# Trace Cleanup

Delete Langfuse traces matching filter criteria. Always runs in dry-run mode unless `--confirm` is explicitly passed.

## Instructions

### 1. Check Langfuse Configuration

```bash
if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ]; then
  echo "ERROR: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set"
  exit 1
fi
```

### 2. Parse Arguments

- `--tag TAG`: Filter by tag (e.g., `acm-extraction`)
- `--name PATTERN`: Filter by trace name pattern
- `--before DATE`: Delete traces before this date (YYYY-MM-DD)
- `--dry-run`: (default) List matching traces WITHOUT deleting
- `--confirm`: Actually delete matching traces

**IMPORTANT**: Default to dry-run mode. Only delete when `--confirm` is explicitly provided.

### 3. List Matching Traces (Dry Run)

```bash
LANGFUSE_URL="${LANGFUSE_BASE_URL:-http://localhost:3000}"

# List traces matching criteria
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_URL/api/public/traces?limit=50" \
  | python -m json.tool
```

Filter the results locally by tag, name pattern, and date.

### 4. Display Dry Run Results

```markdown
## Trace Cleanup — Dry Run

### Filter Criteria
- Tag: {tag or "any"}
- Name: {pattern or "any"}
- Before: {date or "any"}

### Matching Traces: {count}

| Trace ID | Name | Date | Tags | Duration |
|----------|------|------|------|----------|

To delete these traces, re-run with `--confirm`.
```

### 5. Delete (Only with --confirm)

If `--confirm` is passed, delete matching traces in batches of 50:

```bash
# Delete a single trace
curl -s -X DELETE -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_URL/api/public/traces/{trace_id}"
```

Report results:
```markdown
## Trace Cleanup — Complete

- Traces matched: {count}
- Traces deleted: {deleted}
- Errors: {errors}
```

### 6. Safety

- ALWAYS default to dry-run
- Confirm with the user before deletion if `--confirm` was provided
- Process in batches of 50 to avoid API rate limits
- Report any deletion errors individually
