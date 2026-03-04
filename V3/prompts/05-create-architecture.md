# 05: Create Architecture — V3 Technical Design

> **BMAD Command:** `/bmad-bmm-create-architecture`
> **Agent:** Winston — 🏗️ Architect
> **Depends On:** 04-edit-prd (updated PRD with V3 FRs)
> **Output:** Updated `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`
> **Run in:** Fresh context window
> **Can run in parallel with:** 06-create-ux

---

## Pre-Read Documents

### Requirements
- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — Updated PRD (from Step 04)
- `V3/output/v3-party-mode-plan.md` — Party Mode consensus decisions

### Technical Context
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Current architecture (to be updated)
- `docs/architecture/e29-architecture-delta.md` — E29 changes (retained work)
- `V3/output/tech-research-extraction-providers.md` — Provider evaluation (from Step 02)
- `V3/output/solution-architecture-v3.md` — Client solution architecture (from P0)
- `V3/output/e30-multi-agent-audit-unified.md` — Winston's findings (W1-W12) + Amelia's file impact matrix

### Schema References
- `V3/output/building_fields_summary.md` — SF Building__c fields
- `V3/output/item_fields_summary.md` — SF Item__c fields

### Current Codebase (scan structure)
- `open_notebook/domain/acm.py` — Current ACMRecord model
- `open_notebook/extractors/orchestrator.py` — Current orchestrator
- `open_notebook/graphs/acm_extraction.py` — Current extraction graph
- `api/routers/acm.py` — Current ACM API
- `api/model_provisioning.py` — Current model provisioning

---

## Prompt

```text
/bmad-bmm-create-architecture

## V3 Architecture Document

### Context
Create the V3 architecture document that covers ALL new requirements from the updated PRD. This replaces/extends the current architecture doc. The current system has Epics 1-28 + E29 S1-S4 implemented.

### Architecture Sections Required

#### 1. Data Model — Building__c + Item__c Split
- `building_record` table mapped to SF Building__c (29+ extractable fields)
- `acm_record` table mapped to SF Item__c (updated field names with Pydantic aliases)
- Master-detail FK: `acm_record.building_id → building_record.id`
- `raw_extraction` table — stores raw provider output BEFORE AI processing
- `extraction_provenance` table — full lineage (page, bbox, provider, model, confidence, timestamps)
- `field_schema` table evolution — SF picklist values, dependency chains, versioning
- Include Mermaid ER diagram with SF API field names (per audit finding W5)
- Address: building_id FK change (W4), labelled bool→picklist (Amelia's risk), embedding preservation

#### 2. Extraction Pipeline — Triple-Provider Architecture
Design the parallel extraction pipeline:
```
PDF Upload
├── PyMuPDF → source.full_text (unchanged)
├── Docling Direct API → DataFrames
├── Provider 2 (from tech research recommendation)
└── Consensus Layer → normalized records with confidence scores
```
- Provider adapter interface (abstract base class)
- Result normalization format
- Consensus voting algorithm
- Confidence scoring: HIGH (2+ providers), MEDIUM (1 provider), LOW (0 providers)
- Storage model for multi-provider results in `acm_table_section` / `raw_extraction`
- Integration with existing orchestrator (E29 S3-S4 capability registry)
- Feature flags for provider enablement

#### 3. AI Processing + Batching
- Two-phase extraction: Building__c fields → Item__c fields per building
- Smart batching strategy (by building, by token budget, by table count)
- Multi-provider routing (extend capability registry for Ollama/OpenRouter/Google/Anthropic)
- Pydantic structured output contracts per provider
- Fallback and retry strategy
- AI model strategy (per Party Mode consensus from Topic 5)

#### 4. Dependent Picklist Validation
- Friability → ACM_Classification → ACM_Sub_Classification chain (18 × 2 = 36 valid combos)
- Building_Type → Building_Category → Building_Sub_Category chain (114 types → 13 categories)
- SalesforcePicklistValidator class design
- Warn vs reject policy (per Party Mode decision)
- Integration point with E29-S6 validator

#### 5. Provenance Data Model
Design full extraction lineage:
- Per-record: source page number, table bounding box coordinates, extraction provider, AI model used, confidence score, consensus match status, raw vs AI-enriched flag
- Edit history: who changed what, when, previous values
- UI interaction: how provenance data feeds the click-to-source feature
- Storage: embedded in record vs separate provenance table vs event log

#### 6. SSE + Real-Time Architecture
- Event types: extraction progress, AI processing progress, validation results, export progress
- SSE endpoint design (extend existing `/api/agui/extraction/{id}/stream`)
- AG-UI event protocol for frontend micro-transactions
- Worker/command integration — how commands emit SSE events
- Frontend state management pattern (Zustand store for streaming state)

#### 7. Frontend Architecture
- Page flow: Upload Wizard → Raw Table → AI Processing → Building View → Item View
- Component architecture for new views
- AG Grid configuration for two-view layout + dependent picklist cascading
- Provenance viewer panel design
- State management for multi-step wizard

#### 8. Export Architecture
- Building__c.csv + Item__c.csv (SF Data Loader format)
- Two-sheet Excel export
- External ID linkage for parent-child matching
- BAR format backward compatibility (if needed)

#### 9. Migration Strategy
- Additive migration approach (new SF fields alongside BAR fields during transition)
- Data migration script for existing records (BAR → SF vocabulary)
- "Good" → "Stable" condition mapping and other vocabulary transformations
- Rollback plan

#### 10. API Design
- New endpoints for building CRUD, raw extraction CRUD, provenance queries
- Updated export endpoints for SF format
- Multi-provider extraction trigger endpoint
- SSE subscription endpoints

### Constraints
- Build on E29 S1-S4 work (JSON parser, benchmark harness, unified orchestrator, capability registry)
- Design for 3 providers, implement 2 now
- SurrealDB as the database (no switching)
- Next.js 15 + React 19 frontend (no switching)
- FastAPI backend (no switching)
- Must handle 2000+ production documents from various consulting firms
```

---

## Verification Checklist

After running:
- [ ] `04-architecture.md` updated with all 10 sections
- [ ] Mermaid ER diagram present with SF API field names
- [ ] Provider adapter interface designed
- [ ] Consensus layer algorithm specified
- [ ] Provenance data model fully defined
- [ ] SSE event types enumerated
- [ ] Migration strategy documented
- [ ] All audit findings (W1-W12) addressed
