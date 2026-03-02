# ACM-AI V3 Unified Plan — Party Mode Synthesis

> **Date**: 2026-03-02
> **Participants**: Winston (Architect), Mary (BA), John (PM), Amelia (Dev), Quinn (QA), Bob (SM), Sally (UX), Paige (Tech Writer), Murat (Test Architect)
> **Facilitator**: BMad Master
> **Status**: COMPLETE — Ready for BMAD Planning Cycle
> **Input Documents**: 12 pre-read documents (see Appendix A)

---

## 1. Consensus Decisions

### Topic 1: Multi-Provider Extraction + Consensus Layer

| Question | Decision | Rationale |
|----------|----------|-----------|
| Provider adapter interface | `ExtractionProvider` protocol in `providers/base.py` | Async, extensible, each adapter normalizes to `NormalizedExtractionResult` |
| Where does consensus happen? | **BEFORE LLM interpretation** — merge raw table extractions, interpret once | Avoids N×LLM cost. LLM sees consensus-merged table, not per-provider tables |
| Storage model | Unified `acm_table_section` + `provider_results` JSONB column | One row per consensus table, per-provider raw output for provenance |
| Voting algorithm | Per-field confidence-weighted voting (stages 1-3 only for V1) | Stage 1: key-field anchor, Stage 2: fuzzy string, Stage 3: row position. Skip embedding semantic for V1 |
| Confidence thresholds | HIGH (all agree), MEDIUM (2/3 agree), LOW (1 provider), CONTESTED (disagree on high-stakes field) | Tier assignment drives UI badges and human review priority |
| MinerU 2.x torch constraint | Test `--dry-run` first. Fallback: subprocess bridge | `torch 2.10` vs `mineru` constraint `<2.7`. Risk: medium. Mitigation: subprocess bridge adds ~2s latency |
| PaddlePaddle isolation | Subprocess bridge (not Docker) for local dev | Docker for production. Subprocess keeps dev simple |
| GPU sharing | Sequential execution: Docling first (~22s), then MinerU (~14s) | 24 GB VRAM sufficient for either. Avoid fragmentation. Total: ~36s dual-provider |
| E29 interaction | Extends `strategy_registry.py` with `F9_PROVIDER_CONFLICT`, `F10_CONSENSUS_ARBITRATION` | Clean fit with existing fallback contract |
| Implement now vs later | Docling + MinerU 2.x NOW. Google Doc AI FUTURE epic | Zero cloud dependency, fine-tunable, cross-page stitching (MinerU), ~6.5 SP vs 8-12 SP |

### Topic 2: New UI Flows

| Question | Decision | Rationale |
|----------|----------|-----------|
| Page flow | Upload → Progress (SSE) → Building Grid → Item Grid. Raw Table Review = opt-in | Default flow respects officer time. Raw table always saved for audit |
| Raw → AI table relationship | 1:many via `raw_row_id` FK | One raw row may produce 0-N AI records (empty rows, merged cells) |
| Building ID assignment | Server-side during extraction: `BLD#{source_short}_{seq:03d}` | Deterministic, generated in `orchestrator.py`, NOT the SF `Building_Name__c` |
| Provenance viewer | PDF.js + bbox overlay. Cell-level coordinates stored | Slide-over panel: top = PDF page + highlight, bottom = lineage table |
| AG Grid dependent picklists | Custom cell editors with `field_schema` dependency chain query | `getValues()` callback filters valid values based on controller selection |
| SF validation failures | Inline badges (red/orange/yellow) in AG Grid, NOT blocking gates | Officers fix via record wizard modal. Bulk operation: "Fix all invalid X" |
| Two-view layout | Building list sidebar + Item grid. Building-by-building workflow | Matches SF workflow. Officers work one building at a time |
| Raw table storage | New `raw_extraction_table`: `{id, source_id, provider_id, page, raw_html, raw_markdown, structured_json, bbox, officer_edits[], created_at}` | Preserves PRE-consensus, PRE-AI data for full provenance chain |

### Topic 3: AI Batching Strategy + Model Routing

| Question | Decision | Rationale |
|----------|----------|-----------|
| Extraction provider | Anthropic Claude Sonnet direct API (FR-1409) | Remove OpenRouter intermediary. Direct API for reliability + feature parity |
| Classification | Regex first (80%), Claude Sonnet fallback | Existing E29 classifier pattern. Cost-efficient |
| Enrichment | Configurable: Ollama local OR Claude Haiku | Low-stakes, high-volume. Officer doesn't see model choice |
| Embeddings | Ollama local ONLY | $0 cost, no cloud dependency, no data leaves machine |
| Token limits | Not a practical constraint (200K context) | Typical building section: 3-8K tokens. Batch large buildings at ~15 items/call |
| Batching granularity | Per-building (existing orchestrator pattern) | Two calls per building: Building__c fields, then Item__c fields |
| Structured output | Pydantic models via Claude `tool_use` | `BuildingExtractionResult` + `ACMItemExtractionResult` Pydantic schemas |
| Provider failure | Existing F7 fallback + skip building + preserve partial results | No cascading failure. Each building is independent |
| Esperanto abstraction | Remove from extraction path. Keep for Ollama/enrichment | Extraction: direct `ChatAnthropic`. Other tasks: Esperanto model provisioning |
| Capability registry | Extend E29-S4 with `ModelCapability` enum + `ModelPolicy` | `EXTRACTION`, `CLASSIFICATION`, `ENRICHMENT`, `EMBEDDING` capabilities |
| Cost projection | ~$1,000-1,650 for 2,000 documents | < 1% of manual cost ($200K-400K). Optimize for accuracy, not cost |

### Topic 4: SSE Streaming + AG-UI

| Question | Decision | Rationale |
|----------|----------|-----------|
| Protocol | SSE (not WebSockets) | One-way server→client sufficient. Auto-reconnect. Simpler lifecycle |
| Endpoint categories | (1) Extraction pipeline, (2) AI processing, (3) Bulk operations | Three SSE endpoint groups, each filtered by operation ID |
| Worker integration | `PipelineEventBus` (in-memory `asyncio.Queue`) | No external message broker. SSE endpoints subscribe to bus |
| Frontend state | Zustand for streaming, React Query for data. SSE triggers RQ refetch | Clean separation: SSE = signals, RQ = data |
| Record streaming | Records appear in AG Grid as they're validated | Officers can work on completed buildings while extraction continues |
| Long operations | Progress percentage + estimated time remaining | Based on pages-processed / total-pages ratio |
| AG-UI events | Sub-step events within existing `ORCHESTRATOR` StageId | Don't add new pipeline stages. Keep StageId enum stable |
| Error handling | Toasts for non-fatal, modals for fatal | "MinerU failed for pages 12-15, using Docling only" = toast |

### Topic 5: AI Model Strategy

| Question | Decision | Rationale |
|----------|----------|-----------|
| Extraction AI | Anthropic Claude Sonnet ONLY (direct API) | FR-1409 approved. Adapter pattern mitigates lock-in |
| FR-1409 clarification | "Sole AI **interpretation** provider for extraction" | Ollama for embeddings and Google Doc AI for table extraction are not "extraction AI" |
| User-facing AI choice | **Invisible.** No model selection in upload wizard | Officers care about accuracy, not which model runs. Admin settings only |
| Testing matrix | Nightly: full `{provider} × {model} × {format}`. Per-PR: Broadmeadows only | CI cost: ~$0.50/run for Claude API |
| Vendor lock-in | Mitigated by adapter pattern + Pydantic structured output | Switching AI provider = prompt rewrite, not architecture change |
| Data sovereignty | Anthropic: API data NOT used for training. Ollama: fully local | VAEA-compliant. Google Assured Workloads available for future |

---

## 2. Architecture Outline

### 2.1 High-Level Data Model

```
source
  ├── raw_extraction_table (provider, bbox, raw HTML/markdown)
  ├── acm_table_section (consensus-merged, provider_results JSONB)
  ├── building_record (SF Building__c mapped, 29+ fields)
  │     └── acm_record (SF Item__c mapped, 35+ fields)
  ├── site_config (officer-configured SF fields)
  └── field_schema (SF picklists, dependency chains, version)
```

### 2.2 Pipeline Flow (V3 Target)

```
Phase 1: PDF Processing
  PDF → PyMuPDF (text) + Docling (tables) + MinerU (tables)
  → raw_extraction_table (per-provider)
  → Consensus Layer (merge → unified tables)
  → acm_table_section (consensus-merged)

Phase 2: Structure Analysis
  Table-derived structure (page ranges, building groups)
  + Heuristic enrichment (TOC, building names, metadata)
  → Building Inventory + Page Tags

Phase 3: AI Extraction (per building)
  Orchestrator → Building__c extraction (Claude Sonnet)
               → Item__c extraction (Claude Sonnet)
  → Raw BuildingRecord + ACMRecord candidates

Phase 4: Validation & Correction
  Pydantic schema validation
  → Picklist value validation (exact SF values)
  → Dependency chain validation (Friability→Group→Type, BuildingType→Category)
  → AI correction loop (Claude Sonnet, max 3 retries, single-record context)
  → Dedup + No-Access recovery

Phase 5: Review & Export
  → building_record + acm_record in SurrealDB
  → AG Grid (building list + item grid, dependent picklists)
  → Provenance viewer (PDF.js + bbox overlay)
  → Export: Building__c.csv + Item__c.csv (SF Data Loader ready)
```

### 2.3 UI Structure

```
/upload           → Upload Wizard (3 steps: drop PDF, select provider, extract)
/extraction/:id   → Extraction Progress (SSE-powered, stage labels, building cards)
/source/:id/raw   → Raw Table Review (opt-in, editable AG Grid)
/source/:id        → Building Grid (sidebar list) + Item Grid (per-building)
/source/:id/provenance/:recordId → Provenance Viewer (PDF.js + lineage)
/source/:id/export → Export Dialog (Building__c + Item__c, CSV/Excel)
/admin/settings   → AI Provider Config, Field Schema, Site Config
```

---

## 3. Epic Boundary Recommendations

### Epic 30: Foundation & SF Schema (20 SP, 8 stories)

**Goal**: SF schema infrastructure, data model split, dependent picklist validation.

| # | Story | SP | Description |
|---|-------|----|-------------|
| E30-S1 | SF Schema Config Loader | 5 | Parse building_list.txt + item_list.txt → JSON configs. Load into field_schema table. Dependency chain mappings. Startup loading. |
| E30-S2 | Building Record Table + Domain Model | 5 | New migration: building_record with 29 extractable SF fields. BuildingRecord Pydantic model. Master-detail FK: acm_record.building_id → building_record.id. CRUD API endpoints. |
| E30-S3 | ACM Record SF Item__c Alignment | 4 | Additive migration (new SF fields alongside old). Pydantic aliases for 35+ fields. 294-value Item_Name picklist. Dual-schema coexistence during cutover. |
| E30-S4 | Dependent Picklist Validator | 5 | SalesforcePicklistValidator class. Friability→Classification→SubClassification (36 combos). BuildingType→Category→SubCategory (114→13). Strict case-sensitive. Warn-not-reject policy. |
| E30-S5 | Data Migration Script | 3 | Migrate existing acm_record building fields to building_record. "Good"→"Stable" vocabulary migration. Rollback plan. |
| E30-S6 | BAR→SF Vocabulary Transition | 2 | Cross-cutting: update BAR field names→SF names in validators, normalizers, test fixtures (33+ files). "Good"→"Stable", "T3 Vinyl products"→"Vinyl products". |
| E30-S7 | Two-Phase Extraction Prompts | 4 | New Building__c extraction prompt (SF field names, constrained picklists). Updated Item__c extraction prompt (SF vocabulary, dynamic picklist injection, Item_Name subsetting by Product Group). |
| E30-S8 | Anthropic Claude Direct API | 3 | Replace Esperanto/OpenRouter extraction path with direct ChatAnthropic. Capability registry extension. Feature-flag for transition. Benchmarks pass. |

**Schema Freeze Gate after E30-S6** — all downstream epics depend on stable SF schema.

**Dependencies**: E29 S1-S4 (completed). No external dependencies.

### Epic 31: Multi-Provider Extraction (18 SP, 6 stories)

**Goal**: Add MinerU 2.x as second extraction provider, build consensus layer.

| # | Story | SP | Description |
|---|-------|----|-------------|
| E31-S1 | MinerU 2.x Integration + Validation | 3 | Install MinerU in main venv (or subprocess bridge if torch conflict). Verify no dependency conflicts. Run on Broadmeadows, compare to Docling. |
| E31-S2 | Provider Adapter Framework | 3 | ExtractionProvider protocol. DoclingAdapter (refactor existing). MinerUAdapter. NormalizedExtractionResult schema. Provider registry. |
| E31-S3 | Consensus Layer Core | 3 | RecordMatcher (stages 1-3). ConsensusEngine (per-field weighted voting). ConflictResolver (weighted majority + provider priority). Confidence tier assignment. |
| E31-S4 | Raw Extraction Table + Storage | 2 | New raw_extraction_table migration. Store per-provider raw output. Link to acm_table_section via consensus merge. Provider metadata JSONB. |
| E31-S5 | Pipeline Integration | 3 | Wire providers into orchestrator (parallel sequential execution). Emit consensus telemetry via PipelineLogger. Strategy registry F9/F10 fallbacks. |
| E31-S6 | Dual-Provider Benchmark | 2 | Broadmeadows: 31/31 (consensus >= single-provider). Alexander: >= 42/43 (cross-page stitching improvement). Per-provider accuracy breakdown documented. |

**Dependencies**: E30 (schema freeze).

### Epic 32: AI Processing & Validation (16 SP, 5 stories)

**Goal**: Two-phase Building + Item extraction, SF-aligned validation, correction loop.

| # | Story | SP | Description |
|---|-------|----|-------------|
| E32-S1 | Building__c AI Extraction Node | 4 | New orchestrator node: extract Building__c fields per building using Claude Sonnet. Pydantic BuildingExtractionResult. Store as building_record. |
| E32-S2 | Item__c AI Extraction Node | 4 | New orchestrator node: extract Item__c fields per building using Claude Sonnet. Pydantic ACMItemExtractionResult. Link to building_record via FK. Item_Name subsetting by Product Group. |
| E32-S3 | SF Validation + Correction Loop | 3 | Pydantic validation against SF schema. Picklist validation (exact case-sensitive). Dependency chain enforcement. AI correction with single-record context (max 3 retries). Negative→N/A business rule. |
| E32-S4 | Classifier Update (SF Taxonomy) | 2 | Update regex patterns from BAR taxonomy to SF ACM_Classification/ACM_Sub_Classification values. 18 classification groups × friability. |
| E32-S5 | Extraction Pipeline E2E Test | 3 | Upload→extract (dual provider)→consensus→AI extraction→validation→correction→save. Broadmeadows 31/31, Alexander >= 42/43. All picklist values valid SF values. |

**Dependencies**: E30 (schema), E31 (providers).

### Epic 33: Frontend & UX (22 SP, 7 stories)

**Goal**: Upload wizard, building/item views, provenance, raw tables, export.

| # | Story | SP | Description |
|---|-------|----|-------------|
| E33-S1 | Upload Wizard + Extraction Progress | 4 | 3-step wizard: drop PDF, select provider mode (Quick/Thorough), extract. SSE-powered progress page with stage labels, building cards. |
| E33-S2 | Building Grid + Item Grid (Two-View) | 4 | Building list sidebar. Item grid per building. AG Grid columns from field_schema. BuildingRecord + ACMRecord data contracts. |
| E33-S3 | Dependent Picklist Cell Editors | 3 | AG Grid custom cell editors for SF dependent picklists. Friability→Classification→SubClassification cascading. BuildingType→Category cascading. |
| E33-S4 | SF Validation Badges + Record Wizard | 3 | Inline validation badges in AG Grid (red/orange/yellow). Record wizard modal for editing with SF picklist guidance. Bulk "Fix all" operations. |
| E33-S5 | Raw Table Review (Opt-In) | 3 | Editable AG Grid showing raw extraction output. Officer corrections saved to raw_extraction_table.officer_edits[]. Link to AI processing. |
| E33-S6 | Provenance Viewer | 3 | PDF.js rendering with bbox overlay. Extraction lineage table: provider, model, confidence, edit history. Slide-over panel from record row "Source" button. |
| E33-S7 | Salesforce-Ready Export | 2 | Building__c.csv + Item__c.csv with exact SF API field names. Excel with two sheets. External ID for parent-child Data Loader matching. Site config merge. |

**Dependencies**: E30 (schema), E32 (AI processing produces data for grid).

### Epic 34: Integration, Streaming & Polish (12 SP, 5 stories)

**Goal**: Full SSE streaming, AG-UI integration, performance, documentation.

| # | Story | SP | Description |
|---|-------|----|-------------|
| E34-S1 | PipelineEventBus + SSE Endpoints | 3 | In-memory event bus. Three SSE endpoint categories (extraction, AI processing, bulk). Zustand streaming store. SSE triggers React Query refetch. |
| E34-S2 | Record-by-Record Streaming | 2 | Records appear in AG Grid as validated. Officers work on completed buildings while extraction continues. Building completion events. |
| E34-S3 | Bulk Operations | 2 | Multi-select in AG Grid. Bulk edit (change field for selected records). Bulk validate (re-run SF validation). Bulk export (selected buildings). SSE progress. |
| E34-S4 | Performance Optimization | 2 | Broadmeadows < 120s total pipeline. Alexander < 300s. GPU memory management. Provider execution optimization. |
| E34-S5 | Canonical Artifact Update | 3 | PRD v3.0, Architecture doc v3.0, Epics-and-stories v3.0, Sprint-status.yaml, Frontend type contracts. BMAD story files for all stories. |

**Dependencies**: E30-E33 (builds on all prior epics).

---

## 4. Story Count Estimates

| Epic | Stories | SP | Duration Est. | Critical Path? |
|------|---------|---:|:------------:|:--------------:|
| E30: Foundation & SF Schema | 8 | 20 | 8-10 days | **YES** — gates all others |
| E31: Multi-Provider Extraction | 6 | 18 | 6-8 days | YES — gates E32 |
| E32: AI Processing & Validation | 5 | 16 | 5-7 days | YES — gates E33 |
| E33: Frontend & UX | 7 | 22 | 8-10 days | Partial (S1-S2 gate S3-S7) |
| E34: Integration & Polish | 5 | 12 | 4-5 days | No (parallelizable) |
| **TOTAL** | **31** | **88** | **~31-40 days** | |

### Parallelization Opportunities

```
E30 (Foundation) ─────────────── SCHEMA FREEZE GATE ──┐
                                                       │
E31 (Providers) ──────────────────────────────────────┤
                                                       │
                      E32 (AI Processing) ─────────────┤
                                                       │
                      E33-S1,S2 (Core UI) ─────────────┤  ← can start after E30
                                                       │
                      E33-S3-S7 (Advanced UI) ─────────┤  ← after E32
                                                       │
                      E34 (Integration) ───────────────┘  ← after E32+E33-S2

Critical path: E30 → E31 → E32 → E33-S3 → E34
Parallel lane: E33-S1,S2 can start after E30 (API contracts defined)
```

---

## 5. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|:---------:|:------:|------------|
| R1 | **MinerU 2.x torch constraint blocks main-venv install** | Medium | High | Subprocess bridge fallback (adds ~2-3 SP). Test `--dry-run` in E31-S1 before committing to integration approach. |
| R2 | **SF schema complexity causes prompt regression** | Medium | High | Schema freeze gate between E30 and E31/E32. Benchmark gated: Broadmeadows 31/31 at every story. |
| R3 | **Consensus layer adds latency beyond target** | Medium | Medium | Sequential GPU execution. Record matching < 1s. Net latency ≈ max(Docling, MinerU) + 1s. Target: < 40s dual-provider. |
| R4 | **33+ test files need BAR→SF fixture updates** | High | Medium | E30-S6 dedicated story for vocabulary transition. Automate with find-and-replace scripts where possible. |
| R5 | **AG Grid dependent picklist cascading is complex** | Medium | Medium | AG Grid Enterprise has built-in support via `getValues()`. Prototype in E33-S3 before committing to full implementation. |
| R6 | **PDF.js provenance viewer performance on large PDFs** | Low | Medium | Lazy-load pages. Only render the page containing the target bbox. Don't load entire 50-page PDF into memory. |
| R7 | **Consensus false positives (different records matched as same)** | Low | High | Conservative threshold (0.85). MEDIUM tier flags for human review. Unit tests with edge cases. |
| R8 | **E29 S1-S4 code needs refactoring for SF alignment** | Medium | Medium | E30-S8 (Anthropic direct) and E30-S4 (validator) explicitly address E29 integration points. |
| R9 | **Production PDF format diversity breaks extraction** | High | High | Design for 3 providers, implement 2. MinerU cross-page stitching addresses the biggest gap. Fine-tuning available for new formats. |
| R10 | **Sprint duration exceeds estimate** | Medium | Medium | Parallelization (E33-S1,S2 alongside E31). Schema freeze gate prevents cascading delays. |

---

## 6. Open Questions

| # | Question | Owner | Blocking? | Recommended Resolution |
|---|----------|-------|:---------:|------------------------|
| Q1 | **Building_Sub_Category__c** — SCP references this field but it's not clearly visible in SF field summaries. Does this dependency chain (BuildingType→Category→**SubCategory**) exist in production SF? | Demi (verify with VAEA) | YES (E30-S4) | Verify in SF org. If no SubCategory, simplify to BuildingType→Category only. |
| Q2 | **Validation policy: warn vs reject** — Should invalid picklist values block export, or warn and allow override? | John (PM) + Demi | YES (E30-S4) | Recommend: warn-not-reject for extraction, reject for export (officer must fix before exporting). |
| Q3 | **MinerU 2.x torch compatibility** — Does `mineru` v2.7+ work with `torch 2.10`? | Amelia (test in E31-S1) | YES (E31 approach) | Test `pip install mineru --dry-run`. If fails, budget 3 SP for subprocess bridge. |
| Q4 | **Google Doc AI procurement** — Does VAEA procurement allow Google cloud AI services? | Demi (verify with VAEA) | NO (future epic) | Defer to post-V3. Assured Workloads available if approved. |
| Q5 | **Cell-level bbox storage** — How much storage overhead does cell-level (not just table-level) bbox tracking add? | Amelia (estimate in E31-S4) | NO | Estimate: ~500 bytes per cell × 50 cells per table × 10 tables per doc = ~250KB per doc. Negligible. |
| Q6 | **Existing E29 recovery stories (R1, R2)** — Do any fixes from these carry forward as explicit V3 requirements? | Bob (SM) | NO | Review R1 (benchmark fidelity) and R2 (match-gap) during E32 story writing. Carry forward applicable fixes. |

---

## 7. PRD Delta — New FRs Beyond FR-1401-1412

### Multi-Provider Extraction (FR-1500 series)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1501 | Support 2+ table extraction providers (Docling + MinerU) with consensus merging | P0 |
| FR-1502 | Per-field confidence scoring with consensus tier (HIGH/MEDIUM/LOW/CONTESTED) | P0 |
| FR-1503 | Store raw per-provider extraction results for provenance | P0 |
| FR-1504 | Sequential GPU execution to prevent VRAM contention | P1 |
| FR-1505 | Provider adapter interface for adding future extraction providers | P1 |
| FR-1506 | Cross-page table stitching (via MinerU) | P0 |

### UI / UX (FR-1600 series)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1601 | Upload wizard with provider selection (Quick/Thorough) | P0 |
| FR-1602 | SSE-powered extraction progress with building-by-building completion | P0 |
| FR-1603 | Two-view layout: building list + item grid per building | P0 |
| FR-1604 | AG Grid dependent picklist cascading (SF dependency chains) | P0 |
| FR-1605 | Inline SF validation badges (red/orange/yellow) | P0 |
| FR-1606 | Raw table review (opt-in, editable) | P1 |
| FR-1607 | Provenance viewer (PDF.js + bbox overlay + lineage table) | P1 |
| FR-1608 | Record wizard with SF picklist guidance | P1 |
| FR-1609 | Bulk operations (multi-select, bulk edit, bulk validate) | P1 |
| FR-1610 | Building ID auto-assignment (BLD#NNN) during extraction | P0 |

### Streaming & Observability (FR-1700 series)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1701 | SSE endpoints for extraction, AI processing, and bulk operations | P0 |
| FR-1702 | Record-by-record streaming to AG Grid during extraction | P1 |
| FR-1703 | Full extraction lineage: table → record → field with provider, model, confidence, edit history | P0 |
| FR-1704 | PipelineEventBus for worker→SSE event relay | P1 |

### AI Strategy (FR-1800 series)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1801 | Capability registry with ModelCapability enum (EXTRACTION, CLASSIFICATION, ENRICHMENT, EMBEDDING) | P0 |
| FR-1802 | Ollama local for embeddings (zero cloud dependency) | P1 |
| FR-1803 | AI model selection invisible to end users (admin settings only) | P0 |
| FR-1804 | Structured output via Pydantic models + Claude tool_use | P0 |

### FR-1409 Amendment

**FR-1409 (revised)**: Use Anthropic Claude Sonnet as the sole AI **interpretation** provider for Building__c and Item__c field extraction. Ollama local for embeddings and classification is permitted. Google Document AI as a future table extraction provider (not AI interpretation) is permitted.

---

## 8. Dependency Graph

```
                    E30: Foundation & SF Schema
                    ┌─────────────────────────────┐
                    │ S1: Schema Config Loader     │
                    │ S2: Building Record Model    │ ← blocked by S1
                    │ S3: ACM SF Alignment         │ ← blocked by S1
                    │ S4: Dependent Picklist Valid. │ ← blocked by S1
                    │ S5: Data Migration           │ ← blocked by S2, S3
                    │ S6: BAR→SF Vocabulary        │ ← blocked by S3
                    │ S7: Two-Phase Prompts        │ ← blocked by S1, S2, S3
                    │ S8: Anthropic Direct API     │ ← independent (any time after S1)
                    └────────────┬────────────────┘
                                 │
                    ═══ SCHEMA FREEZE GATE ═══
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                   ▼
   E31: Multi-Provider    E33-S1,S2: Core UI    (E34-S5: Docs)
   ┌─────────────────┐    ┌────────────────┐
   │ S1: MinerU Setup│    │ S1: Upload Wiz │
   │ S2: Adapters    │    │ S2: Bldg/Item  │
   │ S3: Consensus   │    │     Grid       │
   │ S4: Raw Storage │    └───────┬────────┘
   │ S5: Pipeline    │            │
   │ S6: Benchmark   │            │
   └────────┬────────┘            │
            │                     │
            ▼                     │
   E32: AI Processing             │
   ┌─────────────────┐            │
   │ S1: Bldg Extract│            │
   │ S2: Item Extract│            │
   │ S3: Validation  │            │
   │ S4: Classifier  │            │
   │ S5: E2E Test    │            │
   └────────┬────────┘            │
            │                     │
            ▼                     ▼
   E33-S3 through S7: Advanced UI
   ┌────────────────────────────┐
   │ S3: Picklist Editors       │
   │ S4: Validation Badges      │
   │ S5: Raw Table Review       │
   │ S6: Provenance Viewer      │
   │ S7: SF Export              │
   └────────────┬───────────────┘
                │
                ▼
   E34: Integration & Polish
   ┌────────────────────────────┐
   │ S1: EventBus + SSE        │
   │ S2: Record Streaming      │
   │ S3: Bulk Operations       │
   │ S4: Performance           │
   │ S5: Artifact Update       │
   └────────────────────────────┘
```

### Cross-Epic Dependencies

| Dependency | Source | Target | Type |
|------------|--------|--------|------|
| SF schema stability | E30-S6 (vocab transition) | E31, E32, E33 | **GATE** — no downstream work until schema frozen |
| Provider adapters | E31-S2 | E31-S3 (consensus needs adapters) | Sequential |
| Building record model | E30-S2 | E32-S1 (building extraction needs model) | Sequential |
| Consensus-merged tables | E31-S5 | E32-S1 (AI extraction needs merged tables) | Sequential |
| AI-processed records | E32-S1, S2 | E33-S2 (grid needs data) | Sequential |
| Field schema API | E30-S1 | E33-S3 (picklist editors need schema) | Sequential |
| SSE infrastructure | E34-S1 | E33-S1 (progress page needs SSE) | Parallel (E34-S1 can start early) |

---

## 9. Provenance Data Model

```sql
-- Raw extraction per provider (NEW)
DEFINE TABLE raw_extraction_table SCHEMAFULL;
DEFINE FIELD source_id ON raw_extraction_table TYPE record<source>;
DEFINE FIELD provider_id ON raw_extraction_table TYPE string;      -- "docling", "mineru", "google_docai"
DEFINE FIELD page_number ON raw_extraction_table TYPE int;
DEFINE FIELD raw_html ON raw_extraction_table TYPE option<string>;
DEFINE FIELD raw_markdown ON raw_extraction_table TYPE option<string>;
DEFINE FIELD structured_json ON raw_extraction_table TYPE option<object>;
DEFINE FIELD bbox ON raw_extraction_table TYPE option<object>;     -- {x, y, width, height}
DEFINE FIELD confidence ON raw_extraction_table TYPE option<float>;
DEFINE FIELD officer_edits ON raw_extraction_table TYPE option<array<object>>;
DEFINE FIELD created_at ON raw_extraction_table TYPE datetime DEFAULT time::now();

-- Consensus-merged table (evolve existing acm_table_section)
-- ADD fields:
DEFINE FIELD provider_results ON acm_table_section TYPE option<object>;   -- {docling: {...}, mineru: {...}}
DEFINE FIELD consensus_tier ON acm_table_section TYPE option<string>;     -- HIGH, MEDIUM, LOW, CONTESTED
DEFINE FIELD consensus_scores ON acm_table_section TYPE option<object>;   -- per-field agreement data

-- Building record (NEW — from E30-S2)
DEFINE TABLE building_record SCHEMAFULL;
DEFINE FIELD source_id ON building_record TYPE record<source>;
DEFINE FIELD internal_id ON building_record TYPE string;            -- BLD#001, BLD#002
DEFINE FIELD building_name ON building_record TYPE option<string>;  -- SF: Building_Name__c
DEFINE FIELD building_address ON building_record TYPE option<string>;
DEFINE FIELD suburb ON building_record TYPE option<string>;
DEFINE FIELD postcode ON building_record TYPE option<string>;
DEFINE FIELD state ON building_record TYPE option<string>;
DEFINE FIELD construction_type ON building_record TYPE option<string>;
DEFINE FIELD estimated_year_built ON building_record TYPE option<string>;
DEFINE FIELD number_of_levels ON building_record TYPE option<string>;
DEFINE FIELD est_building_size ON building_record TYPE option<string>;
DEFINE FIELD date_of_inspection ON building_record TYPE option<string>;
DEFINE FIELD roof_type ON building_record TYPE option<string>;
DEFINE FIELD page_number ON building_record TYPE option<int>;
DEFINE FIELD extraction_confidence ON building_record TYPE option<float>;
DEFINE FIELD extraction_provider ON building_record TYPE option<string>;
DEFINE FIELD extraction_model ON building_record TYPE option<string>;

-- ACM record (evolve existing — from E30-S3)
-- ADD fields:
DEFINE FIELD building_id ON acm_record TYPE option<record<building_record>>;  -- FK to building_record
DEFINE FIELD raw_row_id ON acm_record TYPE option<record<raw_extraction_table>>;
DEFINE FIELD extraction_provider ON acm_record TYPE option<string>;
DEFINE FIELD extraction_model ON acm_record TYPE option<string>;
DEFINE FIELD consensus_metadata ON acm_record TYPE option<object>;  -- {tier, scores, votes}
DEFINE FIELD edit_history ON acm_record TYPE option<array<object>>; -- [{user, field, old, new, timestamp}]
-- SF field aliases added via Pydantic (not separate DB columns)
```

---

## 10. Consensus Layer Design Specification

### Architecture

```
Provider Registry
  ├── DoclingAdapter  → NormalizedExtractionResult
  ├── MinerUAdapter   → NormalizedExtractionResult
  └── (Future: GoogleDocAIAdapter)
           │
    Result Normalizer
    Provider-specific → NormalizedRecord[]
           │
    Record Matcher (3 stages)
    Stage 1: Key-field anchor (page, building, room, product) — ~75%
    Stage 2: Fuzzy string (rapidfuzz Jaro-Winkler ≥0.85) — ~20%
    Stage 3: Row position fallback (same-table index proximity) — ~5%
           │
    Consensus Engine
    Per-field confidence-weighted voting
    Provider track-record weighting (Bayesian: Beta(correct+2, total+3))
           │
    Conflict Resolver
    L1: Weighted majority vote (default)
    L2: Provider priority hierarchy (domain-specific)
    L3: LLM arbitration (high-stakes fields only: result, friable, condition)
    L4: Human escalation queue (unresolved → AG Grid "Conflict" badge)
           │
    ConsensusResult
    + consensus_tier: HIGH | MEDIUM | LOW | CONTESTED
    + per_field_scores: {field: {value, confidence, providers[]}}
    + conflicts: [{field, values[], resolution, method}]
```

### Match Thresholds

| Composite Score | Classification | Action |
|:--------------:|:--------------:|--------|
| ≥ 0.85 | Confirmed match | Merge records, vote per-field |
| 0.65 – 0.84 | Probable match | Merge with MEDIUM flag |
| < 0.65 | Distinct records | Both preserved independently |

### Confidence Tier Assignment

| Tier | Condition | Action |
|------|-----------|--------|
| HIGH | All providers agree on all fields | Accept automatically |
| MEDIUM | 2/3 agree OR supermajority confidence (>0.8) | Accept with flag |
| LOW | Only 1 provider found the record | Accept with warning |
| CONTESTED | Providers disagree on high-stakes field | Trigger conflict resolution chain |

---

## Appendix A: Pre-Read Documents

| # | Document | Key Takeaway |
|---|----------|-------------|
| 1 | SCP-20260301-SF-salesforce-alignment.md | 12 approved FRs (FR-1401-1412), 10 stories, 28 SP |
| 2 | e30-multi-agent-audit-unified.md | 14 stories, ~48 SP (revised). Detailed gap analysis per agent |
| 3 | item_fields_summary.md | 154 fields, 23 picklists, 294 Item_Name values |
| 4 | building_fields_summary.md | 143 fields, 18 picklists, 114 Building_Type values |
| 5 | tech-research-extraction-providers.md | Docling + MinerU 2.x now, Google Doc AI later. Consensus layer design |
| 6 | solution-architecture-v3.md | Client-facing V3 spec. 5-phase pipeline. SF schema drives everything |
| 7 | heuristic-rules-reference.md | 60+ regex patterns. Carry forward, update BAR→SF vocabulary |
| 8 | bmad-architecture-audit.md | 6 gaps → E29. Tables-as-primary. Specialized agents. ~85% LLM cost reduction |
| 9 | 03-prd.md | Current PRD v1.6. FR-1401-1412 not yet merged |
| 10 | 04-architecture.md | Current architecture (BAR-oriented). Needs V3 refresh |
| 11 | e29-architecture-delta.md | Unified routing, fallback matrix F1-F8, strategy registry, agent decomposition |
| 12 | SCP-V3-scope-expansion.md | E29 S5-S8 + R1/R2 archived. E30 SCP preserved. V3 fresh BMAD cycle |

---

*Generated 2026-03-02 by Party Mode Multi-Agent Session*
*31 stories · 88 SP · 5 epics · ~31-40 days estimated*
*Next step: BMAD Planning Cycle — PRD v3.0 → Architecture v3.0 → Epics & Stories → Sprint Planning*
