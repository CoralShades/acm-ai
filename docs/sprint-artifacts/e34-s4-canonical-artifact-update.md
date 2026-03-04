# E34-S4: Canonical Artifact Update -- Tech Spec

## Overview

This story is a documentation audit and update to bring all canonical project artifacts into sync with the actual V3 implementation. Over the course of V3 development (E30-E34, 37 stories, 110 SP), the codebase evolved significantly. Planning artifacts (PRD, architecture doc, epics file) were written before implementation and now contain placeholder or aspirational content that does not match what was built. This story reconciles every canonical doc with ground truth.

The work is primarily editorial -- no production code changes, no migrations, no tests. The deliverable is a set of updated documentation files that accurately describe the system as implemented.

---

## Background / Context

### Current State of Canonical Artifacts

| Artifact | Location | Current Version | Issue |
|----------|----------|-----------------|-------|
| PRD | `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` | v3.0 | FR tables written pre-implementation; V3 FRs (1400-1800 series) need verification against actual features |
| Architecture | `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` | v3.0 | Component names, file paths, and diagrams from planning phase; need update to match actual implementation |
| Epics & Stories | `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` | v3.0 | V3 epics (E30-E34) listed as "Planned"; need actual SP spent, completion dates, status |
| Sprint Status | `docs/sprint-artifacts/sprint-status.yaml` | Updated 2026-03-04 | E30-E34 entries exist but several stories still marked `backlog` that are actually `done` (see discrepancy list below) |
| CLAUDE.md | `CLAUDE.md` | V3 partial | Contains some V3 info (MinerU 2.x, venv pattern) but missing V3-specific patterns (consensus layer, provider adapters, SF validation, two-view UI, SSE streaming) |
| README.md | `README.md` | Pre-V3 | Roadmap section still says "Next for ACM-AI" with items now complete; no V3 feature summary |
| prd.json | `prd.json` | v3.0 | Machine-readable story tracker; 35/37 stories marked `passes: true`; E30-S8 and E34-S4 remain |
| TypeScript types | `frontend/src/lib/types/*.ts` | V3 | 10 type files created during V3; need verification against actual API response shapes |

### Sprint Status Discrepancies

The following stories are marked `done` in `prd.json` but show `backlog` in `sprint-status.yaml`:

| Story | prd.json | sprint-status.yaml | Correct Status |
|-------|----------|--------------------|----------------|
| E32-S2 | `passes: true`, date 2026-03-04 | `backlog` | `done` |
| E32-S7 | `passes: true`, date 2026-03-05 | `backlog` | `done` |
| E33-S7 | `passes: true`, date 2026-03-05 | `backlog` | `done` |
| E33-S8 | `passes: true`, date 2026-03-05 | `backlog` | `done` |

### V3 Story Summary (from prd.json)

37 total stories across 5 epics. 35 completed, 1 deferred (E30-S8), 1 in progress (E34-S4).

| Epic | Title | Stories | Done | SP |
|------|-------|---------|------|----|
| E30 | V3 Foundation -- Schema + Config | 9 | 8/9 (S8 deferred) | 32 |
| E31 | V3 Multi-Provider Extraction | 8 | 8/8 | 21 |
| E32 | V3 AI Processing & Validation | 8 | 8/8 | 22 |
| E33 | V3 Frontend & UX | 8 | 8/8 | 25 |
| E34 | V3 Integration, Streaming & Polish | 4 | 3/4 (S4 = this story) | 9 |

---

## File Changes

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` | MODIFY | Update to v3.1; verify V3 FRs against implementation |
| 2 | `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` | MODIFY | Update component names, file paths, diagrams to match actual code |
| 3 | `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` | MODIFY | Update E30-E34 status to Done with actual SP and dates |
| 4 | `docs/sprint-artifacts/sprint-status.yaml` | MODIFY | Fix discrepancies; add completion dates; update epic statuses |
| 5 | `CLAUDE.md` | MODIFY | Add V3-specific patterns and conventions |
| 6 | `README.md` | MODIFY | Add V3 feature summary; update roadmap section |
| 7 | `prd.json` | MODIFY | Mark E34-S4 as passes: true with implementedDate |
| 8 | `docs/sprint-artifacts/e34-s4-canonical-artifact-update.md` | EXISTS | This tech spec (already created) |

---

## Implementation Plan

### AC1: PRD Updated to v3.1 with Implementation-Verified FRs

**File:** `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md`

1. Update version header from `v3.0` to `v3.1` and add changelog entry for this update.
2. Review Section 11 (V3 Scope Expansion) -- verify each FR against actual implementation:

| FR Series | Topic | Verification Source |
|-----------|-------|---------------------|
| FR-1400 | SF Schema Alignment | `open_notebook/extractors/parsers/config_loader.py`, `open_notebook/domain/acm.py` |
| FR-1500 | Multi-Provider Extraction | `open_notebook/extractors/providers/`, `open_notebook/extractors/consensus/` |
| FR-1600 | Two-View Building/Item UI | `frontend/src/app/(dashboard)/source/[id]/page.tsx`, `frontend/src/components/acm/` |
| FR-1700 | SSE Streaming | `open_notebook/extractors/pipeline_event_bus.py`, `api/routers/v3_streaming.py` |
| FR-1800 | AI Strategy + Capability Registry | `open_notebook/extractors/acm_schemas_v3.py`, `open_notebook/extractors/prompt_context_builder.py` |

3. For each FR row, verify the "Acceptance Criteria" column matches what was actually built. Update any that diverge.
4. Update the "Status" column header note to reflect 35/37 stories complete.

### AC2: Architecture Doc Updated with Implementation-Verified Component Names and File Paths

**File:** `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`

1. Update version header to v3.1.
2. Verify and update the following sections with actual file paths:

| Architecture Section | Key Components to Verify |
|---------------------|--------------------------|
| Extraction Pipeline | `open_notebook/extractors/providers/` (DoclingAdapter, MinerUAdapter, ProviderRegistry), `open_notebook/extractors/consensus/engine.py` (ConsensusEngine), `open_notebook/extractors/consensus/resolver.py` (ConflictResolver) |
| Data Model | `open_notebook/domain/acm.py` (ACMRecord with SF aliases, BuildingRecord, RawExtraction, ACMTableSection), migration files 38-45+ |
| SF Validation | `open_notebook/extractors/normalizers/enums.py`, `open_notebook/extractors/parsers/config_loader.py` |
| Frontend | `frontend/src/app/(dashboard)/source/[id]/page.tsx`, `frontend/src/components/acm/BuildingSidebar.tsx`, `frontend/src/components/acm/ItemGrid.tsx` |
| SSE Infrastructure | `open_notebook/extractors/pipeline_event_bus.py`, `api/routers/v3_streaming.py`, `frontend/src/lib/hooks/useV3SSE.ts`, `frontend/src/lib/stores/streamingStore.ts` |
| Pre-extraction Intelligence | `open_notebook/extractors/page_tagger.py`, `open_notebook/extractors/building_inventory.py`, `open_notebook/extractors/document_structure.py` |

3. Verify ASCII diagrams reference correct component names (not planning-phase placeholders).

### AC3: Epics and Stories Updated with Actual SP Spent and Completion Dates

**File:** `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`

1. Update the Epic Overview table: change E30-E34 Status from "Planned" to actual status:
   - E30: Done (8/9; S8 deferred to V4)
   - E31: Done (8/8)
   - E32: Done (8/8)
   - E33: Done (8/8)
   - E34: Done (4/4)

2. For each V3 story (E30-S1 through E34-S4), add:
   - Actual completion date (from `prd.json` `implementedDate` field)
   - Status: Done (or Deferred for E30-S8)
   - Note any scope changes from original plan

3. Update the story count in the header: total stories implemented across all epics.

### AC4: sprint-status.yaml Updated with E30-E34 Entries

**File:** `docs/sprint-artifacts/sprint-status.yaml`

Fix the following discrepancies (stories marked backlog that are actually done):

```yaml
# These need status changed from backlog to done:
e32-s2-item-ai-extraction-node: done           # Was: backlog. Completed 2026-03-04
e32-s7-sf-first-validation-pipeline: done       # Was: backlog. Completed 2026-03-05
e33-s7-building-detail-page: done               # Was: backlog. Completed 2026-03-05
e33-s8-salesforce-ready-export-ui: done          # Was: backlog. Completed 2026-03-05
```

Update epic statuses:
```yaml
epic-32: done    # Was: backlog. All 8 stories done.
epic-33: done    # Was: backlog. All 8 stories done.
epic-34: done    # Was: in-progress. Will be done after E34-S4. (Update after this story completes.)
```

Update the `updated` field to current date and add reconciliation note.

### AC5: Frontend TypeScript Interfaces Verified Against Actual API Response Shapes

The following TypeScript interfaces must be verified against their corresponding backend Pydantic models / API response shapes:

| TypeScript Interface | File | Backend Model | API Endpoint |
|---------------------|------|---------------|--------------|
| `ACMRecord` | `frontend/src/lib/types/acm.ts` | `ACMRecordResponse` in `api/models.py` | `GET /api/acm/records` |
| `ACMRecordListResponse` | `frontend/src/lib/types/acm.ts` | `ACMRecordListResponse` in `api/models.py` | `GET /api/acm/records` |
| `ACMStats` | `frontend/src/lib/types/acm.ts` | `ACMStatsResponse` in `api/models.py` | `GET /api/acm/stats` |
| `BuildingRecord` | `frontend/src/lib/types/building.ts` | `BuildingRecordResponse` in `api/models.py` | `GET /api/acm/buildings` |
| `BuildingListResponse` | `frontend/src/lib/types/building.ts` | `BuildingRecordListResponse` in `api/models.py` | `GET /api/acm/buildings` |
| `SFFieldSchemaConfig` | `frontend/src/lib/types/sf-schema.ts` | `SFFieldSchemaConfigResponse` in `api/models.py` | `GET /api/acm/field-schema` |
| `PipelineRunState` | `frontend/src/lib/types/pipeline.ts` | `PipelineRunState` in `open_notebook/extractors/pipeline_logger.py` | `GET /api/acm/extraction-progress/{id}` |
| `StageId` / `StageStatus` | `frontend/src/lib/types/pipeline.ts` | `StageId` / `StageStatus` enums in backend | SSE events |
| `RawExtractionRecord` | `frontend/src/lib/types/acm.ts` | `RawExtractionResponse` in `api/models.py` | `GET /api/acm/raw-extractions/{source_id}` |
| `ProvenanceData` | `frontend/src/lib/types/acm.ts` | `ProvenanceResponse` in `api/models.py` | `GET /api/acm/provenance/{record_id}` |
| `SourceIntelligence` | `frontend/src/lib/types/intelligence.ts` | `SourceIntelligenceResponse` in `api/models.py` | `GET /api/acm/intelligence/{source_id}` |
| `V3EventEnvelope` | `frontend/src/lib/types/v3-streaming.ts` | SSE event JSON shape | `GET /api/v3/stream/*` |
| `CommandJobStatusResponse` | `frontend/src/lib/types/acm.ts` | Job status from surreal-commands | `GET /api/acm/extraction-status/{command_id}` |

**Verification process:**
1. For each row, read the backend Pydantic model and compare field names, types, and optionality against the TypeScript interface.
2. If any field is missing, extra, or has a different type, update the TypeScript interface to match the backend.
3. Pay special attention to V3-added fields: `validation_status`, `validation_errors` on ACMRecord; `record_count` on BuildingRecord; consensus fields on ProvenanceData.
4. Document any intentional divergences (e.g., frontend adds client-side computed fields not present in API).

### AC6: BMAD Story Files Created in docs/sprint-artifacts/ for All E30-E34 Stories

The following stories already have tech spec files in `docs/sprint-artifacts/`:

| Story | Tech Spec File | Exists |
|-------|---------------|--------|
| E30-S1 | `e30-s1-sf-schema-config-loader.md` | YES |
| E30-S2 | `e30-s2-building-record-table-domain-model.md` | YES |
| E30-S3 | `e30-s3-acm-record-sf-item-alignment.md` | YES |
| E30-S4 | `e30-s4-dependent-picklist-validator.md` | YES |
| E30-S5 | `e30-s5-data-migration-script.md` | YES |
| E30-S6 | `e30-s6-bar-sf-vocabulary-transition.md` | YES |
| E30-S7 | `e30-s7-two-phase-extraction-prompts.md` | YES |
| E30-S8 | N/A (deferred -- no spec needed) | N/A |
| E30-S9 | `e30-s9-persist-pre-extraction-intelligence.md` | YES |
| E31-S1 | `e31-s1-mineru-2x-integration-validation.md` | YES |
| E31-S2 | `e31-s2-provider-adapter-framework.md` | YES |
| E31-S3 | `e31-s3-consensus-layer-core.md` | YES |
| E31-S4 | `e31-s4-raw-extraction-table-storage.md` | YES |
| E31-S5 | `e31-s5-pipeline-integration.md` | YES |
| E31-S6 | `e31-s6-dual-provider-benchmark.md` | YES |
| E31-S7 | `e31-s7-pipeline-event-bus-sse-infrastructure.md` | YES |
| E31-S8 | `e31-s8-pre-extraction-quality-hardening.md` | YES |
| E32-S1 | `e32-s1-building-extraction-node.md` | YES |
| E32-S2 | `e32-s2-item-extraction-node.md` | YES |
| E32-S3 | `e32-s3-sf-validation-correction-loop.md` | YES |
| E32-S4 | `e32-s4-classifier-update-sf-taxonomy.md` | YES |
| E32-S5 | `e32-s5-extraction-pipeline-e2e-test.md` | YES |
| E32-S6 | `e32-s6-ollama-model-evaluation-spike.md` | YES |
| E32-S7 | `e32-s7-sf-first-validation-pipeline.md` | YES |
| E32-S8 | N/A (added late; create stub) | **NO** |
| E33-S1 | `e33-s1-upload-wizard-extraction-progress.md` | YES |
| E33-S2 | `e33-s2-building-grid-item-grid-two-view.md` | YES |
| E33-S3 | `e33-s3-dependent-picklist-cell-editors.md` | YES |
| E33-S4 | `e33-s4-sf-validation-badges-record-wizard.md` | YES |
| E33-S5 | `e33-s5-raw-table-review.md` | YES |
| E33-S6 | `e33-s6-provenance-viewer.md` | YES |
| E33-S7 | `e33-s7-building-detail-page.md` | YES |
| E33-S8 | `e33-s8-salesforce-ready-export-ui.md` | YES |
| E34-S1 | `e34-s1-record-by-record-streaming.md` | YES |
| E34-S2 | `e34-s2-bulk-operations.md` | YES |
| E34-S3 | `e34-s3-performance-optimization.md` | YES |
| E34-S4 | `e34-s4-canonical-artifact-update.md` | YES (this file) |

**Stories needing new BMAD story files:**

Only **E32-S8** (Ollama Token-Budget Content Chunking) is missing a tech spec. Create a minimal retrospective-style stub at `docs/sprint-artifacts/e32-s8-ollama-token-budget-chunking.md` with: title, overview (1 paragraph), status (Done), key files changed, and completion date.

### AC7: CLAUDE.md Updated with V3-Specific Patterns and Conventions

**File:** `CLAUDE.md`

Add a new `## V3 Architecture Patterns` section covering:

1. **Provider Adapter Framework**
   - Protocol: `ExtractionProvider` in `open_notebook/extractors/providers/base.py`
   - Adapters: `DoclingAdapter`, `MinerUAdapter` in `open_notebook/extractors/providers/`
   - Registry: `ProviderRegistry` in `open_notebook/extractors/providers/__init__.py`
   - Pattern: adapters normalize provider output to common `RawExtraction` domain objects

2. **Consensus Layer**
   - `RecordMatcher` in `open_notebook/extractors/consensus/engine.py` -- 3-stage record matching
   - `ConsensusEngine` in `open_notebook/extractors/consensus/engine.py` -- confidence-weighted voting
   - `ConflictResolver` in `open_notebook/extractors/consensus/resolver.py` -- L1-L4 escalation

3. **Salesforce Schema Alignment**
   - Config loader: `open_notebook/extractors/parsers/config_loader.py`
   - SF field definitions: `V3/sf_schema/building_fields_summary.md`, `V3/sf_schema/item_fields_summary.md`
   - Dependent picklist validation: `SalesforcePicklistValidator` in config_loader
   - Normalizer enums: `open_notebook/extractors/normalizers/enums.py`

4. **Two-View Frontend (Building Grid + Item Grid)**
   - Route: `/source/[id]` with `BuildingSidebar` + `ItemGrid`
   - Store: `frontend/src/lib/stores/buildingStore.ts` (Zustand)
   - Hooks: `useBuildings`, `useACMItems` in `frontend/src/lib/hooks/`
   - AG Grid dynamic columns from `GET /api/acm/field-schema`

5. **SSE Streaming (PipelineEventBus)**
   - Backend: `open_notebook/extractors/pipeline_event_bus.py`
   - SSE endpoints: `api/routers/v3_streaming.py`
   - Frontend hook: `frontend/src/lib/hooks/useV3SSE.ts`
   - Zustand store: `frontend/src/lib/stores/streamingStore.ts`
   - Event categories: `extraction`, `ai`, `bulk`

6. **V3 Frontend Type Files**
   - `frontend/src/lib/types/acm.ts` -- ACMRecord, RawExtraction, Provenance types
   - `frontend/src/lib/types/building.ts` -- BuildingRecord, BuildingListResponse
   - `frontend/src/lib/types/pipeline.ts` -- PipelineRunState, StageId, StageStatus
   - `frontend/src/lib/types/sf-schema.ts` -- SFFieldSchemaConfig, SFFieldDef
   - `frontend/src/lib/types/intelligence.ts` -- SourceIntelligence, DocumentMeta, BuildingInventory
   - `frontend/src/lib/types/v3-streaming.ts` -- V3EventEnvelope

7. **V3 API Endpoints (added by E30-E34)**
   - `GET /api/acm/buildings?source_id=X` -- Building records with record_count
   - `GET /api/acm/field-schema` -- SF field schema config
   - `GET /api/acm/raw-extractions/{source_id}` -- Raw extraction records
   - `GET /api/acm/provenance/{record_id}` -- Record provenance with consensus data
   - `GET /api/acm/intelligence/{source_id}` -- Pre-extraction intelligence
   - `GET /api/v3/stream/{category}/{id}` -- SSE streaming endpoints
   - `POST /api/acm/bulk-edit` -- Bulk field edit
   - `POST /api/acm/bulk-validate` -- Bulk re-validation
   - `GET /api/acm/validation-summary/{source_id}` -- Validation summary

Also update the existing "V3 Sprint Status" entry in CLAUDE.md to reflect completion (35/37 stories done, 95%).

### AC8: README Updated with V3 Feature Summary

**File:** `README.md`

1. Update the "Roadmap" section (currently around line 305):
   - Move current "Phase 1 - Core Extraction (COMPLETE)" to a "Completed Milestones" subsection
   - Add "Phase 2 - V3 Salesforce Integration (COMPLETE)" with bullet points:
     - Salesforce schema alignment (Building__c + Item__c field mappings)
     - Multi-provider extraction (Docling + MinerU) with consensus layer
     - Two-view Building/Item register UI with AG Grid
     - Real-time SSE extraction progress streaming
     - Dependent picklist validation with SF vocabulary
     - Raw extraction table review and provenance viewer
     - Bulk operations (edit, validate, export)
     - Salesforce-ready CSV/Excel export

2. Update the "Next for ACM-AI" section -- remove items now complete and add actual next items:
   - Ollama-first provider priority (E30-S8, deferred)
   - Salesforce data push integration
   - Multi-tenant deployment
   - Role-based access control

3. Update the "Key Features" / "ACM-Specific Capabilities" section to mention V3 capabilities (SF alignment, multi-provider extraction, consensus layer).

4. Update the service ports table if needed (frontend port 8503 per MEMORY.md vs 8502 in README).

---

## Testing

This story has no production code changes. Verification is manual:

1. **Diff review**: Every modified file should be reviewed for accuracy against the codebase.
2. **Link check**: Verify any file paths mentioned in updated docs actually exist (use `Glob` tool).
3. **prd.json consistency**: After updating sprint-status.yaml, verify it is consistent with prd.json story statuses.
4. **Frontend build**: Run `cd frontend && npm run build` to confirm no TypeScript interface changes break the build.
5. **Backend lint**: Run `uv run ruff check .` to confirm no Python changes are needed.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Stale information in updated docs | Medium | Low | Cross-reference every claim against actual code files |
| TypeScript interface mismatch found | Low | Medium | Fix the interface and verify build passes |
| Missing tech spec file for E32-S8 | Low | Low | Create minimal stub with key implementation details |

---

## Dependencies

- All other E34 stories (S1, S2, S3) must be complete before this story can fully update sprint-status.yaml and prd.json.
- No code dependencies -- purely documentation.

---

## Estimated Effort

- PRD update: 30 min (verify FR tables, update version)
- Architecture doc update: 45 min (verify file paths, update diagrams)
- Epics & stories update: 20 min (update status table)
- Sprint-status.yaml fixes: 15 min (fix 4 discrepancies + epic statuses)
- TypeScript interface verification: 30 min (13 interfaces to check)
- BMAD story file for E32-S8: 10 min (stub)
- CLAUDE.md V3 patterns: 30 min (7 sections)
- README V3 summary: 20 min (roadmap + features)
- **Total: ~3.5 hours (3 SP)**
