# Log Monitor - Task Plan

## Objective
Monitor API and worker logs during E2E extraction pipeline to capture timing, errors, model calls, and pipeline stages.

## Log Sources
1. **Worker log**: `/tmp/acm-worker.log` (stdout/stderr from worker PID 8978)
2. **API health**: `http://localhost:5055/health`
3. **API sources**: `http://localhost:5055/api/sources` (watch for new sources)

## Monitoring Strategy
1. Capture baseline worker log state (16 lines as of start)
2. Poll worker log every 15-30 seconds for new entries
3. Poll API for source/command changes
4. Record all extraction-related events with timestamps
5. Analyze errors, warnings, timing, model calls

## Key Events to Watch
- `acm_extract` command creation and execution
- Model selection (which model used for extraction)
- MinerU table extraction attempts/fallbacks
- LLM API calls (token counts, latency)
- Extraction pipeline stages (parse -> extract -> validate)
- Errors, stack traces, warnings
- Completion status and timing

## Output Files
- `progress.md`: Real-time log capture
- `findings.md`: Analysis summary
