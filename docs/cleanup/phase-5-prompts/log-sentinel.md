You are the LOG-SENTINEL specialist added to the Phase 5 audit. READ-ONLY review. No log rotation, no deletions.

Working directory: `/mnt/d/ailocal/acm-ai`. Branch `feat/sf-reconciliation-20260411`.

## Context to read first

1. `docs/cleanup/assumptions-and-decisions.md`
2. `docs/cleanup/session-log-2026-04-11.md`
3. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
4. Invoke the `/acm-observability` skill for the 6-tool stack reference
5. Read `docs/cleanup/phase-5-audit-extraction-pre.md` when it exists — its findings about stale imports and the `_merge_site_config()` bug inform your log grep patterns

## Log file locations

Primary:
- `logs/api.log` — most recent API server output
- `logs/api-error.log` — error-level API messages
- `logs/frontend.log` — Next.js dev server output
- `logs/acm-extraction.log` — historical extraction runs
- `logs/phase5-api-boot.log` — API boot attempted during this audit turn
- `logs/phase5-frontend-boot.log` — frontend boot attempted during this audit turn
- `logs/runs/` — per-run subdirectories (per-extraction log splits)

SurrealDB logs (Docker):
```bash
docker logs --tail 200 acm-ai-db 2>&1
docker logs --tail 200 acm-ai-langfuse 2>&1   # Langfuse stack
docker logs --tail 200 acm-ai-ollama 2>&1      # currently unhealthy per docker ps
```

## Your mission — historical + live log triage

1. **Recent errors** (last 500 lines of each log file):
   - `logs/api.log` and `logs/api-error.log` — any ERROR / CRITICAL / Traceback / exception patterns
   - `logs/frontend.log` — build errors, runtime errors, red text in the Next.js output
   - `docker logs --tail 500 acm-ai-db` — SurrealDB errors / warnings
   - `docker logs --tail 500 acm-ai-ollama` — WHY is this unhealthy? What does the status check say?

2. **SF field name grep**: Search logs for mentions of the fabricated SF field names from the Phase 1/2 audit. Specifically grep for: `Room_ID__c`, `ACM_Name__c`, `ACM_Description__c`, `Extent__c`, `Risk_Status__c`, `ACM_Labelled__c`, `Hygienist_Recommendations__c`, `Identifying_Company__c`, `Department__c`, `Agency__c`. Any occurrences in recent logs suggest live code still references them. Report with timestamp.

3. **Validation errors**: Grep for `REQUIRED_FIELD_MISSING`, `INVALID_PICKLIST_VALUE`, `ValidationError`, `pydantic_core`, `structured_output`. These are the patterns the SF import would fail with.

4. **Correction stage neutering**: Grep for `_llm_correct_records`, `LLM correction`, `auto_corrected`, `llm_corrected`, `[PIPELINE] Prompt template: acm/correction`. Post-Phase-2a, the `llm_corrected` counter should be 0 in recent runs. Verify.

5. **Boot status of the agents dispatched this turn**: tail `logs/phase5-api-boot.log` and `logs/phase5-frontend-boot.log` for success/failure indicators. If API booted, note the port and PID; if it failed, capture the error.

6. **docker ps review**: `docker ps --format '{{.Names}}\t{{.Status}}'` — which containers are healthy, which unhealthy? Any restart loops?

## Output

1. Write findings to `docs/cleanup/phase-5-audit-logs.md` with sections: Scope, Logs Examined (with line counts), Findings (grouped by severity), Grep Hit Tables (with file:line evidence), Recommendations.
2. Print final ≤300-word summary starting with "=== LOG-SENTINEL SUMMARY ===". Include error count per log file and fabricated-field hit count in the summary.

Do not rotate, delete, or truncate any log file. Pure reading. Exit cleanly when done.
