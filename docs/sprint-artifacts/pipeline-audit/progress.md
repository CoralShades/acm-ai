# Progress: ACM Pipeline Audit
Date: 2026-03-14

## Completed
- Step 1: Enumerate all SurrealDB tables from migrations — 42 tables found (40 active + 2 removed)
- Step 2: Map Pydantic domain models to SurrealDB tables — 14 models mapped, 11 tables have no dedicated model
- Step 3: Trace LangGraph acm_extraction graph — 11 nodes documented with full state/DB I/O matrix
- Step 4: Trace source_commands.py pre-graph steps — 7-step sequence documented
- Step 5: Map API endpoints to SurrealDB queries — 40+ endpoints across 5 routers cataloged
- Step 6: Map frontend components to API endpoints — 10 screens/panels with full data flow traced
- Step 7: Identify orphaned tables — 11 orphaned tables found (8 knowledge graph + 3 config singletons)
- Step 8: Identify orphaned domain models — 0 orphaned models (all actively used)
- Step 9: Produce final audit document — findings.md written with 9 sections
- Step 10: Save findings — findings.md at docs/sprint-artifacts/pipeline-audit/findings.md

## In Progress
(none)

## Blocked
(none)
