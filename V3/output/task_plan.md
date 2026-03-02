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

## Phase: Epics & Stories v3.0 (BMAD /create-epics-and-stories)

### 0. Pre-Read & Context Gathering
- [x] Load Party Mode plan (primary epic/story source)
- [x] Load Multi-Agent Audit (story estimates, missing stories J11-J14)
- [x] Load PRD v3.0 (FR traceability)
- [x] Load Architecture v3.0 (file impact, data model)
- [x] Load UX Design spec (frontend story detail)
- [x] Load SCP-V3 (archival decisions, carry-forward items)
- [x] Load Tech Research (provider implementation estimates)
- [x] Load current 05-epics-and-stories.md (format, existing content)

### 1. Epic 30: V3 Foundation — Schema + Config (8 stories)
- [x] E30-S1: SF Schema Config Loader (5 SP)
- [x] E30-S2: Building Record Table + Domain Model (5 SP)
- [x] E30-S3: ACM Record SF Item__c Alignment (3 SP)
- [x] E30-S4: Dependent Picklist Validator (5 SP)
- [x] E30-S5: Data Migration Script (3 SP)
- [x] E30-S6: BAR→SF Vocabulary Transition (2 SP)
- [x] E30-S7: Two-Phase Extraction Prompts (3 SP)
- [x] E30-S8: Anthropic Claude Direct API + OpenRouter Fallback (3 SP)
- [x] Schema Freeze Gate documentation

### 2. Epic 31: Multi-Provider Extraction (6 stories)
- [x] E31-S1: MinerU 2.x Integration + Validation (2 SP)
- [x] E31-S2: Provider Adapter Framework (3 SP)
- [x] E31-S3: Consensus Layer Core (3 SP)
- [x] E31-S4: Raw Extraction Table + Storage (2 SP)
- [x] E31-S5: Pipeline Integration (3 SP)
- [x] E31-S6: Dual-Provider Benchmark (2 SP)

### 3. Epic 32: AI Processing & Validation (6 stories)
- [x] E32-S1: Building__c AI Extraction Node (3 SP)
- [x] E32-S2: Item__c AI Extraction Node (3 SP)
- [x] E32-S3: SF Validation + Correction Loop (3 SP)
- [x] E32-S4: Classifier Update (SF Taxonomy) (2 SP)
- [x] E32-S5: Extraction Pipeline E2E Test (3 SP)
- [x] E32-S6: Ollama Model Evaluation Spike (2 SP)

### 4. Epic 33: Frontend & UX (8 stories)
- [x] E33-S1: Upload Wizard + Extraction Progress (3 SP)
- [x] E33-S2: Building Grid + Item Grid (Two-View) (5 SP)
- [x] E33-S3: Dependent Picklist Cell Editors (3 SP)
- [x] E33-S4: SF Validation Badges + Record Wizard (3 SP)
- [x] E33-S5: Raw Table Review (Opt-In) (3 SP)
- [x] E33-S6: Provenance Viewer (3 SP)
- [x] E33-S7: Building Detail Page (3 SP)
- [x] E33-S8: Salesforce-Ready Export UI (2 SP)

### 5. Epic 34: Integration, Streaming & Polish (5 stories)
- [x] E34-S1: PipelineEventBus + SSE Endpoints (3 SP)
- [x] E34-S2: Record-by-Record Streaming (2 SP)
- [x] E34-S3: Bulk Operations (2 SP)
- [x] E34-S4: Performance Optimization (2 SP)
- [x] E34-S5: Canonical Artifact Update (3 SP)

### 6. Appendices
- [x] Epic Overview table (E30-E34)
- [x] Dependency graph (text diagram)
- [x] SP summary table
- [x] Schema freeze gate specification
- [x] FR traceability matrix
- [x] Audit finding coverage matrix

### 7. Verification
- [x] 05-epics-and-stories.md updated with V3 epics
- [x] Each epic has 5-10 well-defined stories (E30:8, E31:6, E32:6, E33:8, E34:5 = 33 stories)
- [x] Each story has AC, SP, dependencies, files, risk
- [x] Schema freeze gate present (after E30-S6)
- [x] Migration/cutover stories exist (E30-S5=J11, E30-S6=J12)
- [x] Total SP realistic: 97 SP (target was 80-120)
- [x] Dependency graph is clear and acyclic
- [x] No story exceeds 5 SP (max is 5 SP on E30-S1, S2, S4, E33-S2)
- [x] All audit findings J1-J22 addressed (J11→E30-S5, J12→E30-S6, J13→E34-S5, J14→E33-S7)
- [x] FR traceability matrix covers all 36 V3 FRs
