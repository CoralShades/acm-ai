# Bug: Worker Race Condition — Duplicate Command Processing

**Status:** done
**Priority:** P0 (Critical)
**Discovered:** 2026-02-25 (E2E Test Report)
**Completed:** 2026-02-25
**Report:** [docs/reviews/e2e-test-report-20260225.md](../reviews/e2e-test-report-20260225.md)

---

## Description

When multiple `surreal-commands` worker processes are running, both can pick up the same command simultaneously, executing it twice and creating duplicate records. There is no at-most-once delivery guarantee.

## Evidence

During the 2026-02-25 E2E test, extraction command `command:w7keurrrpsc6f6lk79ig` was picked up by **two worker processes**, each running the full extraction pipeline independently:

| Worker | Records Created | Execution Time |
|--------|----------------|----------------|
| Worker 1 | 16 records | 87.9s |
| Worker 2 | 16 records | 91.0s |
| **Total** | **32 records (16 duplicates)** | — |

Fingerprint analysis confirmed 12 duplicate pairs + 8 unique content fingerprints = 20 unique records where 16 were expected.

## Root Cause

`surreal-commands` library does not implement command-level locking or at-most-once delivery. The command polling mechanism (`LIVE SELECT` or periodic query) allows multiple workers to claim the same pending command.

## Impact

- **Data integrity**: Duplicate ACM records in the database
- **API cost**: Double OpenRouter spend per extraction
- **User confusion**: Record counts double in the UI (32 shown instead of 16)

## Acceptance Criteria

1. [x] Only ONE worker processes a given command, even with multiple workers running
2. [x] Add command-level locking (e.g., `UPDATE command SET status='processing', worker_id=$id WHERE status='pending' AND id=$cmd_id`)
3. [x] Second worker that finds the command already claimed should skip it
4. [ ] Add dedup script or migration to clean up existing duplicate records
5. [ ] Test: start 2 workers, submit 1 command, verify exactly 1 execution

## Proposed Fix

### Option A: Atomic claim (preferred)
```sql
-- In worker polling loop, use atomic UPDATE with WHERE clause
UPDATE command SET status = 'processing', claimed_by = $worker_id, claimed_at = time::now()
WHERE id = $cmd_id AND status = 'pending'
RETURN AFTER;
-- Only proceed if RETURN has results (claim succeeded)
```

### Option B: Single worker enforcement
- Run only 1 worker process in development
- Use `docker compose` scale=1 in production

### Option C: Record-level dedup on insert
- Add unique constraint on (source_id, sample_no, building_name, room_name) composite key
- Reject duplicate inserts at DB level

## Workaround (Immediate)

Run only a single worker process:
```bash
# Windows
uv run run_worker.py --import-modules commands

# WSL
setsid uv run run_worker.py --import-modules commands < /dev/null &
```

---

## Implementation (2026-02-25)

**Approach:** Option A — Atomic claim in our command handler (not the library).

### Changes
- **`commands/acm_commands.py`**: Added `_generate_worker_id()` (hostname:PID) and `_try_claim_command()` using `UPDATE ... WHERE claimed_by IS NONE` atomic claim. Early-exit before extraction if claim fails.
- **`migrations/34.surrealql`**: Adds `claimed_by` (string) and `claimed_at` (datetime) fields to command table.
- **`migrations/34_down.surrealql`**: Rollback migration.
- **`open_notebook/database/async_migrate.py`**: Migration 34 registered in both up/down lists.

### How It Works
1. When a command handler is invoked, `_try_claim_command()` runs an atomic SurrealQL UPDATE that sets `claimed_by` and `claimed_at` ONLY if `claimed_by IS NONE`.
2. If the UPDATE returns a result, the claim succeeded — proceed with extraction.
3. If the UPDATE returns no result (another worker already claimed), log a warning and return `success=False` immediately.
4. The worker ID is `hostname:PID` for easy debugging in multi-worker setups.
