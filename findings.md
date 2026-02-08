# Findings: Agent Creation for ACM-AI

## Source Document Analysis

### BMad Workflows (from .claude/commands/bmad/)
- 8 agent roles defined: PM, SM, Dev, Architect, QA/TEA, Tech Writer, Analyst, UX Designer
- Workflows include: PRD creation/validation, sprint planning, story creation, code review, retrospective
- Config at `_bmad/bmm/config.yaml` with planning artifacts at `_bmad-output/`

### Sprint Change Proposal: Victorian BAR (2026-02-04)
- Schema expansion from 20 to 50 fields
- Multi-format PDF support (Prensa, Greencap, Generic)
- New stories: E1-S7, E1-S8, E2-S8, E5-S3, E5-S4, E7-S7
- Key domain: Victorian BAR (Building Asbestos Register) format

### Sprint Change Proposal: RAG Strategy (2026-02-07)
- 6 RAG strategy gaps: Agentic, Contextual, Parent-Doc, Hybrid, Corrective, Reranking
- New stories: E1-S13/S14/S15 + Epic 11 (E11-S1, E11-S2)
- 25 change proposals across PRD, Architecture, Epics, Pipeline

### Sprint Change Proposal: Workflow Extraction (2026-02-07)
- 5 extraction intelligence gaps from N8N workflow analysis
- New stories: E1-S16/S17/S18/S19 + Epic 12 (Settings UI) + Epic 13 (Knowledge Graph)
- Status: PENDING APPROVAL

## Previous Session Context
- Sprint status YAML was fixed: 7 missing entries added (E1-S14 through E1-S20)
- E1-S13 identity conflict resolved: kept as "fix-page-reference-tracking", agentic orchestrator is E1-S20
- E1 now has 20 stories total, project has 74 stories (50 done, 24 remaining)
- Concurrent dev lanes designed: Lane A (Backend), Lane B (Frontend)

## Existing Agents (7 generic, already created)
architect, debugger, docs-writer, refactorer, researcher, security-reviewer, test-writer

## Key Project Paths for Agent Context
- Sprint status: `docs/sprint-artifacts/sprint-status.yaml`
- Planning: `_bmad-output/project-planning-artifacts/acm-ai/`
- Tech specs: `docs/sprint-artifacts/tech-spec-*.md`
- Extractors: `open_notebook/extractors/`
- Parsers: `open_notebook/extractors/parsers/`
- Graphs: `open_notebook/graphs/`
- Domain: `open_notebook/domain/`
- Migrations: `migrations/`
- Frontend: `frontend/src/`
- Tests: `tests/`
