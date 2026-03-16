# extraction_progress table status stuck at "running" — pipeline logger terminal status bug

> **GitHub Issue**: #99
> **Discovered**: 2026-03-05 (E36-S4 Ollama benchmark)
> **Finding**: F012
> **Priority**: BLOCKER
> **Status**: Open

## Problem

The `extraction_progress` SurrealDB table does NOT reliably update to "completed" status after the worker finishes extraction. The pipeline logger writes the initial "running" status but fails to write the terminal "completed" status for most runs. This makes polling-based completion detection unreliable.

## Evidence

During E36-S4 benchmark (12 extraction runs):
- **7 of 12 runs** "timed out" at 600s despite the worker completing extraction and saving records
- The extraction_progress table showed `status="running"` indefinitely
- Records were correctly saved to the database — only the progress tracking was wrong
- **False timeout rate: 58%** (7/12)

```sql
-- Extraction completed, records saved, but progress stuck at "running"
SELECT * FROM extraction_progress WHERE command_id = 'command:o7v2dg3fdhopoxf23z5x';
-- Returns: status = "running", updated_at = 10+ minutes ago
-- Meanwhile: GET /api/acm/records?source_id=... returns 20+ records
```

## Root Cause Investigation

The pipeline logger (`PipelineLogger`) writes status updates to `extraction_progress` via `_persist_state()`. The terminal status should be written when:

1. The LangGraph extraction graph reaches its END node
2. `save_records()` completes → calls `pipeline_logger.stage_exit(StageId.STORE)`
3. The command handler in `acm_commands.py` finishes

**Possible causes (investigate in order):**

1. **Graph END node doesn't call terminal status**: Check if the final node calls `pipeline_logger.finalize()` or `_persist_state(status="completed")`
2. **Silent DB write failure**: The final `_persist_state()` call may fail silently if the SurrealDB connection is being cleaned up
3. **Race condition**: The command framework marks the command as done before the logger writes terminal status
4. **Missing finalize call**: `acm_extract_command()` may not call a finalize method on the pipeline logger after the graph completes

### Investigation Steps

```python
# Step 1: Check pipeline_logger.py for finalize/terminal write
grep -n "completed\|finalize\|terminal" open_notebook/extractors/pipeline_logger.py

# Step 2: Check if acm_commands.py calls finalize
grep -n "finalize\|completed\|pipeline_logger" commands/acm_commands.py

# Step 3: Check the extraction graph's final node
grep -n "stage_exit.*STORE\|status.*completed" open_notebook/graphs/acm_extraction.py

# Step 4: Add debug logging to _persist_state
# In pipeline_logger.py:_persist_state():
#   logger.info(f"[PERSIST] Writing status={status} for command={self.command_id}")
```

## Impact

- **Frontend**: Extraction progress spinner never stops for affected runs
- **SSE streaming**: Clients polling `/api/acm/extraction-progress/{id}` get stale "running" data
- **Automation**: Benchmark/test scripts cannot detect completion via progress API
- **Workaround**: Record-count polling (`GET /api/acm/records`) is a reliable fallback

## Fix

1. Add explicit terminal status write in `acm_extract_command()` after extraction completes:
```python
# In acm_commands.py, after line ~250 (after extraction graph returns)
if pipeline_logger and command_id:
    await pipeline_logger.finalize(status="completed", records=result.total_records)
```

2. Add DB write verification logging in `PipelineLogger._persist_state()`

3. Consider a worker-side fallback: if `extraction_progress.status != "completed"` after the command finishes, force-update it

## Key Files

- [`open_notebook/extractors/pipeline_logger.py`](../../open_notebook/extractors/pipeline_logger.py) — PipelineLogger class, `_persist_state()`
- [`commands/acm_commands.py`](../../commands/acm_commands.py) — `acm_extract_command()` (lines 104-310)
- [`api/routers/extraction_events.py`](../../api/routers/extraction_events.py) — SSE/polling endpoints
- [`open_notebook/graphs/acm_extraction.py`](../../open_notebook/graphs/acm_extraction.py) — graph nodes calling pipeline logger

## Related

- GitHub Issue: [#99](https://github.com/CoralShades/acm-ai/issues/99)
- Finding: F012 in [`docs/sprint-artifacts/e36/findings.md`](../sprint-artifacts/e36/findings.md)
- Evidence: [`docs/sprint-artifacts/e36/benchmark-results/summary.md`](../sprint-artifacts/e36/benchmark-results/summary.md)
- Story: E27-S2 (Pipeline Logger)
- Benchmark script: [`scripts/benchmark_ollama.py`](../../scripts/benchmark_ollama.py)
