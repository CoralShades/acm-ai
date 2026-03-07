---
description: Inspect LangGraph thread state and optionally dump to JSON Crack
allowed-tools: Bash
argument-hint: <thread_id> [--dump] [--node NODE_NAME]
---

# Graph Inspect

Inspect a LangGraph thread's state via the local API at `:2024`.

## Instructions

### 1. Check LangGraph API Availability

```bash
if ! curl -s http://127.0.0.1:2024/ok > /dev/null 2>&1; then
  echo "LangGraph API is not running."
  echo "Start it with: uv run langgraph dev --no-browser"
  exit 1
fi
```

### 2. Parse Arguments

- `$1` = thread_id (required — if not provided, list recent threads)
- `--dump` = dump state to JSON file for JSON Crack
- `--node NODE_NAME` = filter state to show only a specific node's output

### 3. If No Thread ID — List Recent Threads

```bash
echo "=== Recent Threads ==="
curl -s "http://127.0.0.1:2024/threads?limit=10" | python -m json.tool
```

### 4. Get Thread State

```bash
THREAD_ID="$1"
curl -s "http://127.0.0.1:2024/threads/${THREAD_ID}/state" | python -m json.tool
```

### 5. Filter by Node (if --node specified)

```bash
curl -s "http://127.0.0.1:2024/threads/${THREAD_ID}/state" \
  | python -c "
import sys, json
state = json.load(sys.stdin)
values = state.get('values', {})
node = '${NODE_NAME}'
if node in values:
    print(json.dumps(values[node], indent=2))
else:
    print(f'Node \"{node}\" not found in state. Available keys: {list(values.keys())}')
"
```

### 6. Get Checkpoint History

```bash
echo "=== Checkpoint History ==="
curl -s "http://127.0.0.1:2024/threads/${THREAD_ID}/history" | python -m json.tool
```

### 7. Dump to JSON Crack (if --dump)

```bash
uv run python scripts/dump_state_json.py ${THREAD_ID}
echo "State dumped. Open JSON Crack at http://localhost:8888 and paste/upload the JSON file."
```

### 8. Present Summary

```markdown
## Thread State: {thread_id}

### Thread Info
- Graph: {graph_name}
- Created: {timestamp}
- Checkpoints: {count}

### Current State
- Stage: {current_stage}
- Records: {count}
- Error: {error or "none"}

### Available State Keys
[list of top-level keys in state.values]
```
