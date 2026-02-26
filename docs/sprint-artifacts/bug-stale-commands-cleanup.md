# Bug: Stale Running Commands — Post-Race-Condition Cleanup

**Status:** done
**Priority:** P1 (Maintenance)
**Discovered:** 2026-02-26 (Pipeline Audit)
**Completed:** 2026-02-26
**Related:** [bug-worker-race-condition.md](bug-worker-race-condition.md)

---

## Description

After the worker race condition fix (migration 34 + atomic claim pattern), 11 commands were left
with `status = 'running'` in the `command` table. These commands predated the atomic claim fix —
they were started by worker processes that died without completing, and they were never claimed
(all had `claimed_by = null`, `claimed_at = null`).

No active worker was processing them. They would never complete or fail on their own. They needed
to be explicitly marked `failed` so that:
1. Queue monitoring dashboards show accurate counts
2. E20-S5 extraction re-validation can start from a clean baseline
3. The `running` state no longer implies active in-flight work

## Evidence (Audit — 2026-02-26)

### Command table before cleanup

| Status    | Count |
|-----------|-------|
| completed | 605   |
| failed    | 27    |
| running   | **11** (stale) |

### Stale command breakdown

| Command Name   | Count | claimed_by | claimed_at |
|----------------|-------|------------|------------|
| `embed_chunk`  | 8     | null       | null       |
| `acm_extract`  | 2     | null       | null       |
| `process_source` | 1   | null       | null       |

All 11 commands had `claimed_by = null` — they were **never atomically claimed** by any worker.
This confirms they are pre-fix residue, not commands stuck mid-execution.

Affected sources:
- `source:2kztcmafrmg1zvyq2z48` (Broadmeadows Police Station, PDF variant A)
- `source:ma2uopaoecemjp90l7gf` (Broadmeadows Police Station, PDF variant B)

### extraction_progress table

| Status | Count |
|--------|-------|
| failed | 2     |

No `running` entries — clean.

### acm_record duplicate check

- **50 total records** across 3 sources
- **0 duplicates** found (all `cnt = 1` per `source_id + sample_no` composite key)
- Migration 34's dedup already ran; the 3 sources are genuinely distinct document uploads

## Root Cause

The surreal-commands library marks a command `running` when the handler is invoked. Before the
atomic claim fix (Bug #60), there was no mechanism to prevent a dead worker's command from staying
`running` permanently. The fix added `claimed_by` / `claimed_at` but did not retroactively clean
up commands that had already been set to `running` before migration 34 landed.

## Acceptance Criteria

- [x] 0 `running` commands in the `command` table
- [x] All stale commands marked `failed` with an audit trail in the `result` field
- [x] `extraction_progress` has no stale `running` entries
- [x] 0 duplicate `acm_record` rows (no race condition data corruption)
- [x] `completed` and `failed` are the only command statuses present

## Fix Applied (2026-02-26)

Database-only operation. No code changes.

```surrealql
-- Fail all running commands (none had claimed_by set — all are pre-fix residue)
UPDATE command
  SET status = 'failed',
      result = 'Marked as failed during stale command cleanup (2026-02-26)'
WHERE status = 'running';
```

### Command table after cleanup

| Status    | Count |
|-----------|-------|
| completed | 605   |
| failed    | **38** (+11) |
| running   | **0** ✓ |

## Verification

```bash
curl -s -X POST "http://localhost:8000/sql" -u root:root \
  -H "surreal-ns: open_notebook" -H "surreal-db: development" \
  -H "Accept: application/json" -H "Content-Type: application/surrealql" \
  --data "SELECT status, count() AS total FROM command GROUP BY status;"
# Expected: [{"status":"completed","total":605},{"status":"failed","total":38}]
```

## Guard Rails Applied

- ✅ No code files modified
- ✅ No records deleted — only `UPDATE status`
- ✅ No tables dropped, no migrations run
- ✅ Duplicate check performed before any action on `acm_record`
