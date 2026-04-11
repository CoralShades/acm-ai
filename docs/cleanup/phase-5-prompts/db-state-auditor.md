You are the DB-STATE-AUDITOR specialist added to the Phase 5 audit. READ-ONLY review. No migrations, no schema changes, no data writes.

Working directory: `/mnt/d/ailocal/acm-ai`. Branch `feat/sf-reconciliation-20260411`.

## Context to read first

1. `docs/cleanup/assumptions-and-decisions.md` — 20 durable decisions
2. `docs/cleanup/session-log-2026-04-11.md` — session narrative
3. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
4. `config/sf-schema-snapshot.json` — the target runtime schema
5. Invoke the `/acm-observability` skill for the 6-tool observability stack reference (Langfuse sessionId convention, LangGraph API endpoints at :2024)

## Live services

- SurrealDB WebSocket: `ws://127.0.0.1:8000/rpc` (credentials in `.env`: `root`/`root`, namespace `open_notebook`, database `development`)
- SurrealDB container: `acm-ai-db` (Up 2 days, healthy)
- API may be booting at `http://localhost:5055`
- Langfuse available at `http://localhost:3000`

## Your mission — live DB state inspection

Use SurrealDB SQL queries (via `uv run python scripts/run_surrealdb_query.py` if it exists, or the `surrealdb` Python SDK, or `docker exec acm-ai-db surreal sql --conn http://localhost:8000 --user root --pass root --ns open_notebook --db development --pretty`) to answer:

1. **Live schema vs snapshot drift**: Run `INFO FOR TABLE building_record` and `INFO FOR TABLE acm_record`. Compare the returned field list against `config/sf-schema-snapshot.json`. Report drift: columns in the DB table that are NOT in the snapshot, and fields in the snapshot that are NOT in the DB table.

2. **Record counts**: `SELECT count() FROM building_record GROUP ALL`, same for `acm_record`, `source`, `notebook`, `extraction_progress`. Are there orphan records? Records with source_id pointing at deleted sources?

3. **Dead field usage**: For the 46 dead fields identified by the schema-expert agent, run `SELECT count() FROM acm_record WHERE <field> != NULL` (or equivalent). Which of the 46 actually have non-null data in production? That's the data-loss risk for E38-S2.

4. **Extraction pipeline state**: Are there commands stuck in `status='running'`? `SELECT id, command, status, claimed_by, created FROM surreal_commands WHERE status = 'running'`.

5. **Observability tables**: Does `agui_events` or `pipeline_event` have recent entries? That tells us if the pipeline is actually running traces.

6. **Cross-check with Langfuse** (if helpful): query recent traces via curl if Langfuse is up. Look for traces tagged with `extraction-source:*` showing recent extraction attempts.

## Output

1. Write findings to `docs/cleanup/phase-5-audit-db-state.md` with sections: Scope, Live Queries Run, Findings (drift table, record counts, dead-field data-loss list, stuck commands, observability state), Recommendations (critical/high/medium/low), References.
2. Print final ≤300-word summary starting with "=== DB-STATE SUMMARY ===". Include the dead-field data-loss count in the summary.

If a query fails (table doesn't exist, connection refused, etc.), LOG the failure and continue with the next query. Do not treat a single failed query as fatal. Exit cleanly when done.
