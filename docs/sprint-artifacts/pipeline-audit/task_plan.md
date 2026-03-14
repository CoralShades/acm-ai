# Task Plan: Audit ACM Pipeline — Tables, Data Flow, Graph Nodes, and Frontend Mapping
Date: 2026-03-14
Status: COMPLETE

## Goal
Audit the full ACM extraction pipeline to document: (1) all SurrealDB tables and their relationships, (2) which tables map to which frontend screens, (3) how LangGraph nodes populate each table, (4) which tables/models are outdated or disconnected from active graph nodes.

## Steps
- [x] Step 1: Enumerate all SurrealDB tables from migrations (1–49) — 42 tables (40 active + 2 removed)
- [x] Step 2: Map Pydantic domain models (`open_notebook/domain/`) — 14 models mapped
- [x] Step 3: Trace LangGraph `acm_extraction` graph — 11 nodes with full I/O matrix
- [x] Step 4: Trace `source_commands.py` pre-graph steps — 7-step sequence documented
- [x] Step 5: Map API endpoints to SurrealDB queries — 40+ endpoints cataloged
- [x] Step 6: Map frontend components to API endpoints — 10 screens/panels traced
- [x] Step 7: Identify orphaned tables — 11 orphaned (8 knowledge graph + 3 config singletons)
- [x] Step 8: Identify orphaned domain models — 0 orphaned (all active)
- [x] Step 9: Produce final audit document — 9-section findings.md
- [x] Step 10: Save findings to `docs/sprint-artifacts/pipeline-audit/findings.md`

## Risks
- Some tables may be populated by background workers (`commands/`) rather than the graph — need to check both paths
- V3 tables may shadow V1/V2 tables with similar names but different schemas
- Some domain models may be "planned but not implemented" (from BMAD stories)

## Follow-Up
- 2026-03-14: Post-audit pipeline debug (commit `476c285e`) resolved several node-level failures identified in §3.2. See cross-reference in findings.md and `docs/sprint-artifacts/pipeline-debug/` for full details.
