# V3 Planning — Task Plan

## Phase: Party Mode Multi-Agent Debate + Synthesis

- [x] Load all 12 pre-read documents
- [x] Initialize planning files
- [x] Debate Topic 1: Multi-Provider Extraction + Consensus Layer
- [x] Debate Topic 2: New UI Flows (Wizard, Raw Tables, Provenance)
- [x] Debate Topic 3: AI Batching Strategy + Model Routing
- [x] Debate Topic 4: SSE Streaming + AG-UI Integration
- [x] Debate Topic 5: AI Model Strategy (All agents)
- [x] Synthesize into v3-party-mode-plan.md
- [x] Verification checklist pass

## Phase: Follow-Up — Open Question Resolution + AI Provider Update

- [x] Resolve Q1: Confirm Building_Sub_Category__c absent from SF schema
- [x] Resolve Q2: Validation policy — WARN on edit, REJECT on export
- [x] Resolve Q3: MinerU torch — test in E31-S1, subprocess bridge contingency
- [x] Resolve Q4: Google Doc AI — confirmed deferred
- [x] Resolve Q5: Cell-level bbox — accepted (~250KB negligible)
- [x] Resolve Q6: E29 R1/R2 — review during E32 story writing
- [x] Update Topic 3 table: OpenRouter fallback + Ollama full support
- [x] Update Topic 5 table: Multi-provider compatibility
- [x] Add E32-S6: Ollama Model Evaluation Spike (2 SP)
- [x] Add Capability Registry Routing Table (6 task types)
- [x] Update FR-1409 amendment: Anthropic default + OpenRouter fallback
- [x] Update E30-S4: Remove SubCategory, add WARN/REJECT policy
- [x] Update E30-S8: OpenRouter fallback preservation
- [x] Update totals: 32 stories, 90 SP
- [x] Update planning support files (progress.md, findings.md)

## Phase: MinerU Audit Corrections

- [x] CORRECTION 1: Fix torch constraint — `>2.6.0,<3` (compatible), not `<2.7`
- [x] CORRECTION 2: Add 3 MinerU backends (pipeline/VLM/hybrid), select hybrid
- [x] CORRECTION 3: Separate Alexander benchmark — completionState bug vs MinerU delta
- [x] CORRECTION 4: Add CUDA 12.6 verification checkpoint (low risk R11)
- [x] Eliminate Risk R1 (torch conflict)
- [x] Update Q3 resolution (no subprocess bridge needed)
- [x] Simplify E31-S1 from 3→2 SP
- [x] Update E31-S2 adapter description (VLM output normalization)
- [x] Update E31-S6 benchmark (separate Alexander targets)
- [x] Update consensus layer design (VLM image-based output handling)
- [x] Update raw_extraction_table schema (extraction_backend field)
- [x] Update Pipeline Phase 1 (hybrid backend)
- [x] Update totals: 32 stories, 89 SP
- [x] Update planning support files

## Phase: PRD v3.0 Edit (BMAD /edit-prd workflow)

### 1. Header & Introduction (High)
- [x] Update version to v3.0, date to 2026-03-02
- [x] Update change log entry for V3
- [x] Update scope (1.3) to note V3 expansion

### 2. Functional Requirements — New Sections (Critical)
- [x] Add 2.12: FR-1400 Series — Salesforce Schema Alignment (FR-1401–FR-1412 verbatim from SCP)
- [x] Add 2.13: FR-1500 Series — Multi-Provider Extraction (6 FRs from Party Mode)
- [x] Add 2.14: FR-1600 Series — UI/UX Flows (10 FRs from Party Mode)
- [x] Add 2.15: FR-1700 Series — Streaming & Observability (4 FRs from Party Mode)
- [x] Add 2.16: FR-1800 Series — AI Strategy (4 FRs from Party Mode)
- [x] Amend FR-1409 with Party Mode clarification

### 3. Non-Functional Requirements — Updates (High)
- [x] Add NFR-500 series: V3 Performance Targets
- [x] Add NFR-600 series: Data Sovereignty & Compliance

### 4. UI Requirements — Updates (High)
- [x] Add V3 UI structure and new components

### 5. Data Requirements — Major Updates (Critical)
- [x] Add 5.1.5: Building Record Schema (SF Building__c)
- [x] Add 5.1.6: Raw Extraction Table Schema
- [x] Update ACM Record Schema for SF fields + FKs (§5.1.7)
- [x] Add V3 API endpoints
- [x] Update enums for SF vocabulary
- [x] Add 5.3.1: Salesforce Export Format
- [x] Add 5.4.1: V3 Pipeline Architecture

### 6. New Section 11: V3 Scope (Critical)
- [x] Add V3 scope delineation section
- [x] Add epic boundary summary (E30-E34)
- [x] Add dependency graph
- [x] Add data model overview
- [x] Add AI capability routing table
- [x] Add FR traceability matrix

### 7. Testing, Rollout, Appendix (Medium)
- [x] Add V3 test scenarios (20 scenarios, T-V3-001 through T-V3-020)
- [x] Add V3 rollout phases (Phases 5-9)
- [x] Update glossary (11 new terms)
- [x] Update references (3 new)
- [x] Update change log (v3.0 entry)

### 8. Verification
- [x] All FR-1401–FR-1412 present (15 matches)
- [x] All FR-1500 series present (7 matches — 6 FRs + traceability)
- [x] All FR-1600 series present (11 matches — 10 FRs + traceability)
- [x] All FR-1700 series present (5 matches — 4 FRs + traceability)
- [x] All FR-1800 series present (5 matches — 4 FRs + traceability)
- [x] Existing FRs untouched (FR-100–FR-1100 series verified present)
- [x] Each new FR has testable acceptance criteria (spot-checked, all have pipe-delimited AC column)

## Phase: Architecture v3.0 (BMAD /create-architecture workflow)

### 0. Pre-Read & Research
- [x] Load all pre-read documents (PRD v3.0, Party Mode, current arch, e29 delta, tech research, solution arch, audit, SF field summaries)
- [x] Read current codebase files (acm.py, orchestrator.py, acm_extraction.py, acm router, model_provisioning)
- [x] Analyze current architecture doc structure for update strategy (3 agents completed)

### 1. Section 1: Data Model — Building__c + Item__c Split
- [x] Mermaid ER diagram with SF API field names
- [x] building_record table (SF Building__c)
- [x] acm_record evolution (SF Item__c with Pydantic aliases)
- [x] raw_extraction table (per-provider provenance)
- [x] extraction_provenance model
- [x] field_schema evolution (SF picklists, dependency chains, versioning)
- [x] Address W4 (building_id FK), W5 (SF field names), labelled bool→picklist risk

### 2. Section 2: Extraction Pipeline — Dual-Provider Architecture
- [x] Pipeline flow diagram (PDF → providers → consensus → AI → validation)
- [x] Provider adapter interface (ExtractionProvider protocol)
- [x] Result normalization format (NormalizedExtractionResult)
- [x] Consensus voting algorithm (3-stage matching, per-field voting)
- [x] Confidence scoring (HIGH/MEDIUM/LOW/CONTESTED)
- [x] Storage model for multi-provider results
- [x] Integration with E29 orchestrator (capability registry F9/F10)
- [x] Feature flags for provider enablement

### 3. Section 3: AI Processing + Batching
- [x] Two-phase extraction: Building__c → Item__c per building
- [x] Smart batching (per-building, token budget)
- [x] Multi-provider routing (capability registry extension)
- [x] Pydantic structured output contracts per provider
- [x] Fallback and retry strategy (Anthropic → OpenRouter)

### 4. Section 4: Dependent Picklist Validation
- [x] Friability → Classification → SubClassification chain (36 combos)
- [x] BuildingType → Category chain (114→13)
- [x] SalesforcePicklistValidator class design
- [x] Warn vs reject policy
- [x] Integration with E29-S6 validator

### 5. Section 5: Provenance Data Model
- [x] Per-record lineage (page, bbox, provider, model, confidence, consensus)
- [x] Edit history design
- [x] UI interaction (click-to-source)
- [x] Storage design (embedded vs separate table)

### 6. Section 6: SSE + Real-Time Architecture
- [x] Event types enumeration
- [x] SSE endpoint design (extend existing endpoints)
- [x] AG-UI event protocol for frontend
- [x] Worker/command integration (PipelineEventBus)
- [x] Frontend state management (Zustand streaming store)

### 7. Section 7: Frontend Architecture
- [x] Page flow diagram
- [x] Component architecture for new views
- [x] AG Grid configuration (two-view + dependent picklists)
- [x] Provenance viewer panel design
- [x] State management for multi-step wizard

### 8. Section 8: Export Architecture
- [x] Building__c.csv + Item__c.csv format
- [x] Two-sheet Excel export
- [x] External ID linkage
- [x] BAR backward compatibility

### 9. Section 9: Migration Strategy
- [x] Additive migration approach
- [x] Data migration script design
- [x] BAR → SF vocabulary mapping
- [x] Rollback plan

### 10. Section 10: API Design
- [x] New building CRUD endpoints
- [x] Raw extraction CRUD
- [x] Provenance query endpoints
- [x] SF export endpoints
- [x] Multi-provider extraction trigger
- [x] SSE subscription endpoints

### 11. Verification
- [x] All 10 sections present (13 sub-sections under §14)
- [x] Mermaid ER diagram with SF API field names (196 __c references)
- [x] Provider adapter interface designed (ExtractionProvider protocol)
- [x] Consensus layer algorithm specified (3-stage matching, 4-level conflict resolution)
- [x] Provenance data model fully defined (6-layer chain)
- [x] SSE event types enumerated (15 event types across 3 categories)
- [x] Migration strategy documented (6 additive migrations, rollback plan)
- [x] All audit findings (W1-W12) addressed (§14.11 traceability matrix)
