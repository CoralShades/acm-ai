# Task Plan: Research Integration for ACM-AI

> **Goal:** Integrate research findings into PRD, Architecture, and Epics to refine project before development
> **Date:** 2026-02-05
> **Status:** Planning

---

## Executive Summary

### Key Research Findings to Integrate

1. **Two-Stage Pipeline Design** (NEW)
   - Stage 1: EXTRACT - verbatim values with provenance (page, table, confidence)
   - Stage 2: INTERPRET - normalize to BAR schema using rules
   - Current architecture shows single-stage - needs refactoring

2. **MinerU + Docling Hybrid** (NEW)
   - Docling: text/layout extraction, page classification
   - MinerU: complex table extraction with HTML structure
   - User confirmed: MinerU primary for tables

3. **Official BAR JSON Schema** (NEW - register_row.schema.json)
   - 47 columns (A-AU) with exact official field names
   - Current PRD uses ~50 fields with different naming
   - Must align to official schema

4. **Complete Enum Definitions** (NEW - register_enums.json)
   - SampleResult, Condition, DisturbancePotential, Friability
   - FrequencyOfUse, SpecificUses (319 items!), ConstructionType, RoofType
   - Current PRD has incomplete enum lists

5. **ACM Product Taxonomy** (NEW - register_taxonomy.*.json)
   - Non-friable: 8 groups (T1-T8) with 150+ product types
   - Friable: 6 groups (T1-T6) with 110+ product types
   - Critical for E1-S9 (Product Classification)

6. **Consultant Wording Normalization** (NEW)
   - Regex patterns to normalize recommendations to canonical actions
   - 6 universal actions defined
   - Not mentioned in current artifacts

7. **Extensible Multi-Consultant Architecture** (CONFIRMED)
   - User wants pluggable consultant-specific parsers
   - Current architecture shows patterns but needs formalization

### User Decisions (from AskUserQuestion)
- PDF Extraction: MinerU + Docling hybrid (recommended)
- Pipeline: Two-stage (Extract → Interpret)
- Consultants: Extensible multi-consultant design
- Schema: Merge BAR fields into expanded ACMRecord

---

## Phases

### Phase 1: Create Reference Documents
**Status:** complete
**Goal:** Create authoritative reference documents from research

| Task | Status | Notes |
|------|--------|-------|
| 1.1 Create BAR-schema.md reference | complete | docs/reference/bar-schema.md |
| 1.2 Create extraction-pipeline.md reference | complete | docs/reference/extraction-pipeline.md |
| 1.3 Create product-taxonomy.md reference | complete | docs/reference/product-taxonomy.md |
| 1.4 Create consultant-patterns.md reference | skipped | Included in extraction-pipeline.md |

### Phase 2: Update PRD
**Status:** complete
**Goal:** Align PRD with research findings

| Task | Status | Notes |
|------|--------|-------|
| 2.1 Update Section 5.1 (ACM Schema) | complete | Added reference to bar-schema.md, fixed enum comments |
| 2.2 Add Section 5.4 (Extraction Pipeline) | complete | Two-stage design documented |
| 2.3 Add Section 5.5 (Enum Definitions) | complete | Complete enum lists with business rules |
| 2.4 Add Section 5.6 (Product Taxonomy) | complete | T1-T8 taxonomy reference |
| 2.5 Add Section 5.7 (Consultant Support) | complete | Multi-format design |
| 2.6 Update Dependencies | complete | Added MinerU, openpyxl |

### Phase 3: Update Architecture
**Status:** complete
**Goal:** Refactor architecture for two-stage pipeline

| Task | Status | Notes |
|------|--------|-------|
| 3.1 Update Section 5.1 (Pipeline) | complete | New two-stage diagram |
| 3.2 Add MinerU integration | complete | Code example included |
| 3.3 Add Section 5.2 (Consultant Parser) | complete | Abstract base class defined |
| 3.4 Renamed Section 5.3 | complete | Consultant format patterns |

### Phase 4: Update Epics & Stories
**Status:** complete
**Goal:** Refine stories with implementation details

| Task | Status | Notes |
|------|--------|-------|
| 4.1 Update E1-S3 (Extraction) | complete | Two-stage pipeline with acceptance criteria |
| 4.2 Update E1-S9 (Classification) | complete | Official taxonomy reference |
| 4.3 Add E1-S10 (MinerU Integration) | complete | New story added |
| 4.4 Add E1-S11 (Consultant Parser) | complete | New story for extensibility |
| 4.5 Add E1-S12 (Wording Normalization) | complete | New story added |
| 4.6 Update dependencies table | complete | New stories included |

### Phase 5: Create Implementation Roadmap
**Status:** complete
**Goal:** Sequence work for development

| Task | Status | Notes |
|------|--------|-------|
| 5.1 Define implementation phases | complete | See below |
| 5.2 Identify dependencies | complete | Updated in Epics doc |
| 5.3 Update MVP scope | complete | Added new stories |

---

## Files Created/Modified

| File | Action | Phase |
|------|--------|-------|
| `_bmad-output/research-integration/task_plan.md` | Created | Setup |
| `_bmad-output/research-integration/findings.md` | Created | Setup |
| `_bmad-output/research-integration/progress.md` | Created | Setup |
| `docs/reference/bar-schema.md` | Created | Phase 1 |
| `docs/reference/extraction-pipeline.md` | Created | Phase 1 |
| `docs/reference/product-taxonomy.md` | Created | Phase 1 |
| `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` | Updated | Phase 2 |
| `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` | Updated | Phase 3 |
| `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` | Updated | Phase 4 |

---

## Implementation Roadmap

### Sprint 1: Foundation (E1-S10, E1-S11)
**Goal:** Set up extraction infrastructure

1. **E1-S10: MinerU Integration**
   - Install MinerU dependency
   - Create table extractor class
   - Test on sample PDFs

2. **E1-S11: Consultant Parser Framework**
   - Define abstract base class
   - Implement Prensa parser
   - Implement Greencap parser

### Sprint 2: Two-Stage Pipeline (E1-S3, E1-S12)
**Goal:** Implement Extract → Interpret pipeline

1. **E1-S3: Two-Stage Pipeline**
   - Stage 1: Extract with provenance
   - Stage 2: Interpret with normalization
   - Integration tests

2. **E1-S12: Wording Normalization**
   - Regex patterns for recommendations
   - Canonical action mapping

### Sprint 3: Classification & Config (E1-S9, E1-S8)
**Goal:** Complete extraction features

1. **E1-S9: Product Classification**
   - Pattern-based taxonomy
   - LLM fallback
   - User override

2. **E1-S8: Site Configuration**
   - Config form component
   - API endpoints
   - Storage

### Sprint 4: Export & UI (E5-S2, E2-S8, E7-S7)
**Goal:** BAR-compliant output

1. **E5-S2: Excel BAR Export**
   - 47-column output
   - openpyxl implementation

2. **E2-S8: Column Visibility**
   - Preset views
   - Persistence

3. **E7-S7: Upload Site Config**
   - Wizard integration

---

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |

---

## Key Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Use MinerU + Docling hybrid | MinerU has best table extraction; Docling good for text/layout | 2026-02-05 |
| Two-stage pipeline (Extract → Interpret) | Cleaner separation, better traceability, easier debugging | 2026-02-05 |
| Extensible multi-consultant design | Future-proof for new PDF formats | 2026-02-05 |
| Merge BAR fields into ACMRecord | Single source of truth, simpler than mapping layer | 2026-02-05 |
