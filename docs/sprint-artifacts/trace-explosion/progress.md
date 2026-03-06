# Progress: Trace Explosion Fix

## Session: 2026-03-07

### Last Completed Milestone
- Root cause identified: `logfire.instrument_pydantic()` creates OTel span per Pydantic
  validation; each becomes top-level Langfuse trace due to missing parent context

### Current Active Task
- Applying fix to logfire_config.py

### Blockers
- None

### Files Modified
- `open_notebook/observability/logfire_config.py` (remove instrument_pydantic call)
- `.env` (LOGFIRE_ENABLED=false default)
- `docs/development/observability.md` (document trace explosion risk)

### Next Planned Action
- Verify Langfuse trace count normal after restart
- Commit and push
