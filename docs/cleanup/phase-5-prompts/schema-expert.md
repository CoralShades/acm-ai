You are the SCHEMA-EXPERT specialist in a 6-agent Phase 5 audit for the ACM-AI SF reconciliation sprint. READ-ONLY review. No code changes, no migration creation.

Working directory is /mnt/d/ailocal/acm-ai. Branch `feat/sf-reconciliation-20260411`.

## Context to read

1. `docs/cleanup/assumptions-and-decisions.md`
2. `docs/cleanup/session-log-2026-04-11.md`
3. `docs/sprint-artifacts/full-audit-2026-04-11/PHASE-1-FINDINGS.md`
4. `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
5. `config/sf-schema-snapshot.json` — the runtime snapshot
6. `git log --oneline main..HEAD`

## Your domain: schema + database

SurrealDB migrations, Pydantic domain models, field_schema config, E38-S2 migration plan.

Inspect: `migrations/*.surql` (especially the latest ones defining `building_record` and `acm_record`), `open_notebook/domain/acm.py` (BuildingRecord + ACMRecord), `open_notebook/database/`, `config/sf-schema-snapshot.json`.

## Questions to answer

1. How many fields on `BuildingRecord` and `ACMRecord` are NOT in the sf-schema-snapshot extractable set? List the DEAD FIELDS explicitly — this is direct input for E38-S2.
2. Database schema drift: does the SurrealDB `building_record` and `acm_record` table definition have columns that no longer map to any real SF field? These are candidates for a DROP FIELD migration.
3. `field_schema` table vs `config/sf-schema-snapshot.json` — which is canonical at runtime? Is there a conflict?
4. Migration safety for E38-S2: if the parent writes a migration to drop non-SF fields, what's the rollback plan? Any columns with production data that would be lost?
5. Pydantic validator drift: are there validators on BuildingRecord/ACMRecord that enforce BAR-only rules? (The test suite already found `internal_id must start with 'BLD#'` at `acm.py:953`.) Find others.

## Output

1. Write findings to `docs/cleanup/phase-5-audit-schema-expert.md`: Scope, Findings (include the explicit dead-field list for E38-S2), Recommendations, References.
2. Print final ≤250-word summary starting with "=== SCHEMA-EXPERT SUMMARY ===". Include the dead-field count in the summary.

Do not propose writing migrations — just enumerate. Exit cleanly.
