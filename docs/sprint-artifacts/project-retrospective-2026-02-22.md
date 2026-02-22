# Project Retrospective — ACM-AI v1.0 (Feature Complete)

> **Date:** 2026-02-22
> **Scope:** Consolidated retrospective for all 16 completed epics (E1-E7, E9-E17)
> **Facilitator:** Bob (Scrum Master)
> **Status:** Feature Complete — 112/122 stories done, 10 archived

---

## Epic Summary

| Epic | Title | Stories | Highlights |
|------|-------|---------|------------|
| E1 | ACM Data Extraction Pipeline | 31 | MinerU integration, model capabilities, agentic orchestrator |
| E2 | AG Grid Spreadsheet Integration | 12 | Column visibility, BAR field type safety, bulk operations |
| E3 | Cell Citations & PDF Viewer | 4 | Clickable cells, PDF modal, page number tracking |
| E4 | Chat with ACM Context | 4 | CopilotKit, AG-UI protocol, supervisor agent |
| E5 | Export Functionality | 4 | CSV/Excel, BAR templates, field mapping config |
| E6 | Rebranding to ACM-AI | 4 | New branding, logo, color theme, landing page |
| E7 | Upload Wizard | 7 | Drag-drop, doc type detection, site config |
| E9 | Document Library Management | 3 | Library view, status dashboard, bulk operations |
| E10 | UI Simplification | 1 | ACM mode navigation filtering |
| E11 | Search & Retrieval Enhancement | 2 | Parent document retrieval, hybrid search |
| E12 | Extraction Settings & Configuration | 4 | Method settings, model config, processing options, field schema |
| E13 | Knowledge Graph Visualization | 3 | SurrealDB graph schema, API + dagre, React Flow |
| E14 | UX & Enterprise Readiness | 11 | VAEA branding, accessibility, keyboard nav, skeleton loading |
| E15 | Extraction Monitor & Live Logging | 2 | Log panel, dedicated monitor page |
| E16 | UX Enhancement Sprint | 3 | Dashboard home, record detail, empty states |
| E17 | Live Extraction Intelligence | 6 | AG-UI SSE, A2A agent card, reasoning display |

---

## Delivery Metrics

- **Total Stories**: 122 (112 done, 10 archived)
- **Completion Rate**: 92% (100% of non-archived stories)
- **Commits**: 281 across 12 development days
- **Change Proposals Navigated**: 5 (Victorian BAR, RAG strategy, document intelligence, course correction, extraction monitor)
- **Database Migrations**: 30+
- **Story Files**: 52
- **Sprint Reports**: 6

---

## What Went Well

### 1. Rapid Epic Delivery Through Autonomous Sprints
The Ralph autonomous loop completed 11 stories in a single sprint (E2-S8, E2-S11, E16-S3, E1-S23, E5-S3, E16-S1, E12-S1, E13-S1, E15-S2, E5-S4, E11-S2). This demonstrated that well-specified stories with clear acceptance criteria enable high-velocity autonomous implementation.

### 2. BMAD Workflow Integration
The BMAD methodology provided structure through sprint planning, story creation, code review, and status tracking. Having a canonical `sprint-status.yaml` as single source of truth prevented confusion across sessions.

### 3. Architecture Stability
The core architecture (FastAPI + SurrealDB + LangGraph + Next.js) proved robust enough to support 16 epics of feature development without major refactoring. The repository pattern, domain-driven design, and command pattern for async jobs scaled well.

### 4. Incremental Scope Expansion
Five sprint change proposals successfully expanded scope (E11, E12, E13, E14, E15, E16, E17) without destabilizing existing work. Each proposal was properly documented and integrated into sprint tracking.

### 5. Code Review Catching Real Issues
The adversarial code review process caught 12 issues in the final sprint batch, including:
- Batch size DoS vulnerability (source_bulk.py)
- Edge set injection risk (graph.py)
- Render-phase state mutation (KnowledgeGraph.tsx)
- DELETE FROM without WHERE clause (settings reset endpoints)

---

## Challenges and Growth Areas

### 1. Tracking Artifact Drift
**Pattern**: Stories were implemented but tracking artifacts weren't updated. This happened twice — E17 (6 stories) and the final batch (7 stories) were all implemented but remained marked as `ready-for-dev` in sprint-status.yaml.

**Root Cause**: Autonomous sprints focused on code delivery but skipped the "mark done" step. The Ralph loop's TEST phase failed on bare `ruff`/`pytest` commands (WSL environment issues), causing the loop to exit before the COMPLETE phase.

**Lesson**: Story completion should be atomic — implementation + verification + tracking update as a single unit.

### 2. Test Coverage Gaps
**Pattern**: No unit tests were written for new backend endpoints (source_bulk.py, graph.py, settings stage models). The deferred review issue "no test infrastructure" was never addressed.

**Root Cause**: Story acceptance criteria focused on functional requirements. Test coverage wasn't in AC for most stories. The one pre-existing test failure (`source_chat` module import) was never fixed.

**Lesson**: Include "test coverage for new endpoints" as a standard AC for backend stories.

### 3. Model ID Configuration Fragility
**Pattern**: Hardcoded model IDs, token limits, and provider-specific patterns were scattered across the codebase. The `"haiku" in str(model_id)` pattern tested against SurrealDB record IDs instead of model names.

**Resolution**: E1-S28/S29/S30 created the model capabilities system with migration 20, but this came late (bug triage sprint). Earlier investment in this abstraction would have prevented issues.

**Lesson**: Data model abstractions should be built early, not retrofitted after bugs surface.

### 4. Frontend Build Environment Fragility
**Pattern**: Frontend builds occasionally failed with MODULE_NOT_FOUND errors in WSL2 environments. The `uv run` commands had encoding issues on Windows.

**Resolution**: Switched to `python3 -m` commands and added `run_worker.py` wrapper.

**Lesson**: CI/CD should run in consistent containerized environments, not developer workstations.

### 5. Sprint Change Proposal Volume
**Pattern**: 5 change proposals in 12 days added 7 new epics and expanded scope significantly. While each was justified, the cumulative effect was scope creep from 74 to 122 stories.

**Lesson**: Change proposals should include explicit impact assessment on overall timeline and completion targets.

---

## Key Insights

1. **Well-specified stories enable autonomous implementation.** Stories with clear file change tables, acceptance criteria, and tech specs were implementable by the Ralph loop with minimal intervention.

2. **The SurrealDB event relay pattern works well.** Bridging the worker/API process boundary via database events (E17-S1) was architecturally clean and extensible.

3. **React Flow with dagre layout is production-viable for knowledge graphs.** E13-S2/S3 delivered interactive graph visualization with custom nodes (School/Building/Room/ACM) and hierarchical layout without performance issues up to 200+ nodes.

4. **AG-UI protocol provides standardized extraction observability.** The SSE endpoint streaming extraction events (steps, tool calls, reasoning tokens) gives users meaningful real-time feedback.

5. **Document intelligence is the core value proposition, not traditional RAG.** The project evolved from a general RAG system to a specialized document intelligence platform for SAMP/ACM compliance.

---

## Technical Debt Inventory

| Item | Severity | Impact | Notes |
|------|----------|--------|-------|
| No test coverage for bulk/graph/settings APIs | High | Regressions undetected | Deferred from code review |
| Pre-existing source_chat module import error | Medium | One test always fails | Module restructuring needed |
| Favicon not converted from VAEA assets | Low | Cosmetic only | Needs image processing |
| Runtime ACM mode toggle not in settings UI | Low | Env-var works | Feature request |
| DocumentActions dropdown not created | Low | BulkActions has functionality | Feature gap |
| Frontend build fragility in WSL2 | Medium | CI/reliability | Docker containerization recommended |

---

## Process Improvements Made During Project

1. **Canonical artifact location** (`docs/sprint-artifacts/`) established, eliminating duplication with `_bmad-output/implementation-artifacts/`
2. **Ralph loop infrastructure** — signal handling, dry-run mode, iteration tracking, stop-gate hooks
3. **Model capabilities system** — dynamic token limits and provider defaults instead of hardcoded values
4. **BMAD config** (`_bmad/bmm/config.yaml`) created to point workflows at correct artifact location
5. **Story Verification Protocol** added to CLAUDE.md — build + file existence + browser verification

---

## Recommendations for Future Work

### Immediate (Pre-Production)
1. Add test coverage for new backend endpoints (source_bulk.py, graph.py, settings.py)
2. Fix source_chat module import error
3. Set up Docker-based CI/CD pipeline
4. Production deployment with environment configuration

### Near-Term Enhancements
1. E2E extraction accuracy improvements (currently ~87% on Broadmeadows test case)
2. Performance optimization for large documents (>100 pages)
3. Multi-tenant support for enterprise deployment
4. Audit trail and compliance logging

### Architecture Evolution
1. Consider event-driven architecture for extraction pipeline (replace polling with webhooks)
2. Evaluate embedding model upgrades for better semantic search
3. Consider GraphQL for more flexible frontend data fetching
4. Production-grade observability (OpenTelemetry, structured logging)

---

## Team Performance Summary

The project delivered **112 stories across 16 epics in 12 development days** with a single developer augmented by autonomous AI agents. Key success factors:
- BMAD methodology provided structure and traceability
- Ralph autonomous loop enabled batch story implementation
- Adversarial code review caught real security and quality issues
- Sprint change proposals allowed responsive scope management
- Clear architecture patterns (repository, DDD, command) scaled across all epics

**The project is feature-complete and ready for production preparation.**

---

> Retrospective facilitated by Bob (Scrum Master)
> Date: 2026-02-22
> Covering: E1-E7, E9-E17 (16 epics, 112 stories)
