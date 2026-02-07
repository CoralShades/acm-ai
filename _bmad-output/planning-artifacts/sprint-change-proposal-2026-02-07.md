# Sprint Change Proposal - RAG Strategy Alignment

> **Date:** 2026-02-07
> **Triggered by:** Research findings from `docs/reference/RAG Strategies for ACM-AI.md`
> **Scope:** PRD, Architecture, Epics & Stories, Extraction Pipeline
> **Status:** APPROVED (2026-02-07)
> **Approved by:** Demi

---

## 1. Issue Summary

### Problem Statement

Research into RAG (Retrieval-Augmented Generation) strategies for ACM-AI has revealed 6 significant gaps between the documented project artifacts and what's needed for robust PDF extraction, data management, and retrieval. The current documents describe a **static, linear extraction pipeline** with basic embedding support, but modern document intelligence requires:

- **Agentic orchestration** for dynamic tool selection
- **Contextual embedding enrichment** for meaningful semantic search
- **Parent-child document relationships** for proper retrieval context
- **Hybrid search** combining keyword and semantic approaches
- **Corrective validation loops** for self-healing extraction
- **Reranking** for query result prioritization (future)

### Context

- Discovered during research phase, not during story implementation failure
- Research document: `docs/reference/RAG Strategies for ACM-AI.md`
- Sprint is 88% complete (50/57 stories done) - all existing work remains valid
- The changes are **additive enhancements** that build on top of the completed foundation

### Critical Insight

> ACM-AI's primary function is **structured data extraction from PDFs**, not question-answering over a knowledge base. RAG strategies are applied in service of **extraction accuracy** (Agentic RAG, Corrective RAG) and **post-extraction querying** (Hybrid Search, Contextual Retrieval, Parent Document Retrieval, Reranking).

---

## 2. Impact Analysis

### 2.1 Gap Assessment

| # | RAG Strategy | Priority | PRD Coverage | Architecture Coverage | Gap Severity |
|---|-------------|----------|-------------|----------------------|-------------|
| 1 | Agentic RAG | P0 | Not covered | Partial (static parser routing) | HIGH |
| 2 | Contextual Retrieval | P0 | FR-203 mentions embeddings only | Not covered | HIGH |
| 3 | Parent Document Retrieval | P0 | Not covered | Not covered | HIGH |
| 4 | Hybrid Search | P1 | FR-304 (grid search only) | Not covered | MEDIUM |
| 5 | Corrective RAG | P1 | Implicit (validation in Stage 2) | Partial (schema validation) | MEDIUM |
| 6 | Reranking | P2 | Not covered | Not covered | LOW |

### 2.2 Epic Impact

| Epic | Status | Impact | Details |
|------|--------|--------|---------|
| E1 (Extraction) | needs-expansion | **HIGH** | +3 new stories for Agentic, Contextual, Corrective |
| E4 (Chat) | done | **MEDIUM** | Chat context builder updated via E11 stories |
| E9 (Documents) | in-progress | LOW | Could benefit from hybrid search later |
| **NEW E11** | proposed | **NEW EPIC** | Search & Retrieval Enhancement (2 stories) |
| All others | done/backlog | None | No changes needed |

### 2.3 Artifact Impact

| Artifact | Sections Affected | Change Type |
|----------|-------------------|-------------|
| PRD (03-prd.md) | FR-102, FR-203, FR-501, new FRs, Section 5.8, 6.2, 9, 10 | Update + Add |
| Architecture (04-architecture.md) | Section 5 (pipeline), Section 7 (chat), DB schema | Update + Add |
| Epics (05-epics-and-stories.md) | E1 stories, new E11 epic, dependency graph, MVP scope | Update + Add |
| Extraction Pipeline (extraction-pipeline.md) | Pipeline stages, output processing | Update |
| Sprint Status (sprint-status.yaml) | Story counts, new stories | Update |

### 2.4 Story Count Impact

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total Stories | 57 | 62 | +5 |
| Stories Done | 50 | 50 | 0 |
| Stories Remaining | 7 | 12 | +5 |
| Total Epics | 10 | 11 | +1 |

---

## 3. Recommended Approach

### Selected Path: Direct Adjustment

Add new stories within existing epic structure and create one new epic. No rollback or MVP reduction needed.

**Rationale:**
- **Low risk:** All changes are additive - no existing work invalidated
- **Solid foundation:** 88% complete, extraction pipeline and embeddings already working
- **Incremental delivery:** Each new story delivers standalone value
- **No blocking dependencies:** New stories can be sequenced after current in-progress work

### Implementation Priority

| Order | Story | Priority | Depends On |
|-------|-------|----------|------------|
| 1 | E9-S3 (Document Actions) | Continue | Already drafted |
| 2 | E10-S1 (UI Simplification) | Continue | Already drafted |
| 3 | E1-S13 (Agentic Orchestrator) | P0 | E1-S3 (done) |
| 4 | E1-S14 (Contextual Enrichment) | P0 | E1-S6 (done) |
| 5 | E11-S1 (Parent Document Retrieval) | P0 | E1-S3 (done) |
| 6 | E1-S15 (Corrective Validation) | P1 | E1-S13 |
| 7 | E11-S2 (Hybrid Search) | P1 | E11-S1 |
| 8 | E1-S11 (Parser Framework) | P1 | E1-S2 (done) |
| 9 | E1-S12 (Wording Normalization) | P1 | E1-S3 (done) |
| 10 | E2-S8, E5-S3, E5-S4 | P1 | Various (done) |
| Future | Reranking | P2 | E11-S2 |

---

## 4. Detailed Change Proposals

### 4.1 PRD Updates (03-prd.md)

#### CP-1: Update FR-102 (Extraction Tool Selection)

```
Section: 2.1 Document Processing (FR-100 Series)

OLD:
| FR-102 | System shall extract text and tables from PDFs using Docling | P0 | Docling processes file and returns structured output |

NEW:
| FR-102 | System shall extract text and tables from PDFs using an agentic pipeline that selects from Docling (text/layout), MinerU (tables), and specialized parsers (lab results) based on content analysis | P0 | Agentic orchestrator correctly routes document sections to appropriate extraction tools |

Rationale: Static Docling-only extraction replaced with dynamic multi-tool selection via LangGraph agent
```

#### CP-2: Add FR-109 (Agentic RAG Orchestrator)

```
Section: 2.1 Document Processing (FR-100 Series) - NEW ROW

| FR-109 | System shall use an agentic orchestrator (LangGraph) to dynamically route document sections to appropriate extraction tools based on content analysis | P0 | Agent correctly identifies section types (metadata, table, lab results) and invokes appropriate tool for each |

Rationale: Gap 1 - Agentic RAG. Replace static get_parser() routing with LLM-driven agent
```

#### CP-3: Add FR-110 (Corrective RAG Validation)

```
Section: 2.1 Document Processing (FR-100 Series) - NEW ROW

| FR-110 | System shall implement corrective validation that automatically re-attempts extraction with corrective prompts when field validation fails | P1 | Failed validations trigger LLM re-extraction with max 3 attempts; extraction accuracy >90% with corrective loop |

Rationale: Gap 5 - Corrective RAG. Stage 2 validation currently returns errors but doesn't self-correct
```

#### CP-4: Update FR-203 (Contextual Embeddings)

```
Section: 2.2 Data Model (FR-200 Series)

OLD:
| FR-203 | System shall support vector embeddings for ACM records | P1 | Semantic search returns relevant records |

NEW:
| FR-203 | System shall generate vector embeddings for ACM records with contextual enrichment (Building, Level, Room, Page prepended to content before embedding) | P0 | Semantic search returns relevant records with hierarchical context awareness |

Rationale: Gap 2 - Contextual Retrieval. Anthropic's contextual retrieval pattern ensures embeddings understand document hierarchy
```

#### CP-5: Add FR-209, FR-210, FR-211 (Parent Document Retrieval)

```
Section: 2.2 Data Model (FR-200 Series) - NEW ROWS

| FR-209 | System shall store enriched text alongside raw text for each ACM record to support contextual semantic search | P0 | Both raw and enriched text available per record |
| FR-210 | System shall maintain parent-child relationships between ACM table sections (parent) and individual ACM items (child) for retrieval purposes | P0 | Parent table section linked to child ACM records via parent_table_id |
| FR-211 | When retrieving ACM records via semantic search, system shall return the parent table context alongside the matched record | P0 | Search results include full parent row context, not just matched field |

Rationale: Gap 3 - Parent Document Retrieval. Enables finding a child chunk but returning the full parent table context
```

#### CP-6: Add FR-506 (Hybrid Search)

```
Section: 2.5 Chat Integration (FR-500 Series) - NEW ROW

| FR-506 | Chat shall use hybrid search (BM25 keyword + vector semantic) with Reciprocal Rank Fusion to retrieve relevant ACM records | P1 | Exact match on sample numbers (BM25) combined with conceptual match on descriptions (vector) returns higher quality results than either alone |

Rationale: Gap 4 - Hybrid Search. Currently FR-304 is client-side grid search only; FR-203 is vector-only
```

#### CP-7: Update FR-501 (Chat Retrieval)

```
Section: 2.5 Chat Integration (FR-500 Series)

OLD:
| FR-501 | Chat shall include ACM spreadsheet data in context | P0 | AI can answer "What's in Building X?" |

NEW:
| FR-501 | Chat shall include ACM data in context via hybrid retrieval (keyword + semantic search) rather than full table dump | P0 | AI answers accurately using retrieved relevant records, not brute-force context loading |

Rationale: Current implementation dumps full table into context; hybrid retrieval is more efficient and accurate
```

#### CP-8: Add Section 5.8 (RAG Strategy Stack)

```
Section: 5.8 RAG Strategy Stack (NEW SECTION)

### 5.8 RAG Strategy Stack

> ACM-AI is a **Document Intelligence / Structured Extraction** system, not traditional RAG.
> RAG strategies serve two distinct purposes:
> 1. **Extraction accuracy:** Agentic RAG (dynamic tool selection), Corrective RAG (self-healing validation)
> 2. **Post-extraction querying:** Contextual Retrieval, Parent Document Retrieval, Hybrid Search, Reranking

| Strategy | Purpose | Priority | FR Reference |
|----------|---------|----------|-------------|
| Agentic RAG | Dynamic extraction tool orchestration | P0 | FR-109 |
| Contextual Retrieval | Hierarchical context in embeddings | P0 | FR-203, FR-209 |
| Parent Document Retrieval | Chunk hierarchy for context-rich retrieval | P0 | FR-210, FR-211 |
| Hybrid Search | BM25 + Vector with Reciprocal Rank Fusion | P1 | FR-506 |
| Corrective RAG | LLM validation loop for self-healing extraction | P1 | FR-110 |
| Reranking | Query result prioritization (BGE-reranker) | P2 | Future |

Rationale: Provides unified reference for all RAG strategies and their role in the system
```

#### CP-9: Update Section 6.2 (Dependencies)

```
Section: 6.2 New Dependencies - ADD ROWS

| rank-bm25 | ^0.2.0 | BM25 keyword search scoring |
| langchain-core | ^0.2.0 | LangGraph agentic orchestration |

Note in Section 10 (Technology Decisions): "BGE-reranker considered for future Phase 2+ query refinement"
```

#### CP-10: Update Section 9 (Open Items)

```
Section: 9 Open Items - ADD ROWS

| Evaluate BGE-reranker for query result prioritization | Dev team | Phase 2+ |
| UX specification and audit | User/Designer | After RAG alignment |
| Benchmark hybrid search vs vector-only for ACM queries | Dev team | During E11-S2 |
```

---

### 4.2 Architecture Updates (04-architecture.md)

#### CP-11: Add Section 5.0 (Agentic Orchestrator)

```
Section: 5.0 Agentic Orchestrator (NEW - before current Section 5.1)

### 5.0 Agentic Orchestrator (LangGraph)

The extraction pipeline is wrapped by an agentic orchestrator that dynamically decides
which tools to invoke based on document content analysis.

```python
# LangGraph agent with extraction tools
extraction_tools = [
    Tool("extract_metadata", "Extract site/building metadata from cover pages"),
    Tool("extract_acm_table", "Extract ACM register table using MinerU"),
    Tool("extract_lab_results", "Extract lab analysis results"),
    Tool("validate_acm_record", "Validate extracted record against BAR schema"),
    Tool("correct_extraction", "Re-extract with corrective prompt on validation failure"),
]

# Agent reasons about document sections:
# "This section is a table → use extract_acm_table (MinerU)"
# "This section is metadata text → use extract_metadata (Docling)"
# "This looks like lab results → use extract_lab_results (regex + LLM)"
```

**Replaces:** Static `get_parser()` routing in Section 5.2
**Integrates with:** Current Stage 0 (Preflight) → Stage 1 (Extract) → Stage 2 (Interpret)
**Technology:** LangGraph (already used in `open_notebook/graphs/`)

Rationale: Current pipeline uses detection-based routing (ConsultantParser.detect()).
Agentic approach enables dynamic, content-aware tool selection.
```

#### CP-12: Add Contextual Enrichment to Pipeline Output

```
Section: 5.1 (Pipeline Architecture) - Between Stage 2 output and OUTPUT section

### Contextual Enrichment Step

Before embedding, prepend hierarchical context to each ACM record:

```python
def enrich_for_embedding(record: ACMRecord) -> str:
    """Generate contextually enriched text for vector embedding."""
    return (
        f"Building: {record.building_name}\n"
        f"Level: {record.level or 'N/A'}\n"
        f"Room: {record.room_name or 'N/A'}\n"
        f"Page: {record.page_number}\n\n"
        f"{record.product} - {record.material_description or ''} - "
        f"Condition: {record.material_condition or 'Unknown'} - "
        f"Risk: {record.risk_status or 'Unknown'}"
    )
```

**Stores:** Both `raw_text` (original) and `enriched_text` (with context) per record

Rationale: Anthropic's contextual retrieval pattern. Ensures semantic search understands
the hierarchical position of each ACM item within the building structure.
```

#### CP-13: Add Parent Document Schema to Database

```
Section: 3.1 SurrealDB Tables - ADD TABLE

-- Parent Table Sections (for Parent Document Retrieval)
DEFINE TABLE acm_table_section SCHEMAFULL;
DEFINE FIELD source_id ON acm_table_section TYPE record<source>;
DEFINE FIELD page_start ON acm_table_section TYPE int;
DEFINE FIELD page_end ON acm_table_section TYPE int;
DEFINE FIELD raw_html ON acm_table_section TYPE option<string>;
DEFINE FIELD raw_text ON acm_table_section TYPE option<string>;
DEFINE FIELD building_name ON acm_table_section TYPE option<string>;
DEFINE FIELD table_type ON acm_table_section TYPE option<string>;  -- register, lab_report, metadata
DEFINE FIELD created_at ON acm_table_section TYPE datetime DEFAULT time::now();
DEFINE INDEX section_source ON acm_table_section FIELDS source_id;

-- Add parent reference to acm_record
DEFINE FIELD parent_table_id ON acm_record TYPE option<record<acm_table_section>>;
DEFINE FIELD enriched_text ON acm_record TYPE option<string>;  -- For contextual embedding

-- Full-text search indexes (for Hybrid Search BM25)
DEFINE ANALYZER acm_analyzer TOKENIZERS class FILTERS lowercase, snowball(en);
DEFINE INDEX acm_fulltext ON acm_record
  FIELDS product, material_description, room_name, building_name, nata_sample_number
  SEARCH ANALYZER acm_analyzer;

Rationale: Gap 3 (Parent Document) + Gap 4 (Hybrid Search) database infrastructure
```

#### CP-14: Add Section 7.3 (Hybrid Search Service)

```
Section: 7.3 Hybrid Search Service (NEW)

### 7.3 Hybrid Search Service

```python
class HybridSearchService:
    """Combines BM25 keyword search with vector semantic search using RRF."""

    def search(self, query: str, source_id: str, top_k: int = 20) -> list[ACMRecord]:
        # BM25 keyword search (exact match on sample numbers, room names)
        bm25_results = self.bm25_search(query, source_id, top_k)

        # Vector semantic search (conceptual match on descriptions)
        vector_results = self.vector_search(query, source_id, top_k)

        # Reciprocal Rank Fusion
        fused = self.reciprocal_rank_fusion(bm25_results, vector_results, k=60)

        # Fetch parent context for top results
        return self.enrich_with_parent_context(fused[:top_k])

    def reciprocal_rank_fusion(self, *result_lists, k=60):
        """Merge multiple ranked lists using RRF scoring."""
        scores = defaultdict(float)
        for results in result_lists:
            for rank, record in enumerate(results):
                scores[record.id] += 1.0 / (k + rank + 1)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Integrates with:** Chat context builder (Section 7.1) replaces full table dump
**Dependencies:** `rank-bm25`, SurrealDB full-text indexes
```

#### CP-15: Expand Stage 2 Validation for Corrective RAG

```
Section: 5.1.2 Stage 2 INTERPRET - Step 5 (Validation)

OLD: Validation returns errors list

NEW:
#### Step 5: Corrective Validation Loop

```python
async def validate_and_correct(
    record: ACMRecord,
    raw_item: RawACMItem,
    max_attempts: int = 3
) -> tuple[ACMRecord, list[ValidationError]]:
    """Validate record; on failure, re-extract with corrective prompt."""
    for attempt in range(max_attempts):
        errors = validate_record(record)
        if not errors:
            return record, []

        # Corrective re-extraction via LLM
        corrective_prompt = build_corrective_prompt(record, errors, raw_item)
        corrected = await llm_correct_extraction(corrective_prompt)
        record = merge_corrections(record, corrected)

    return record, validate_record(record)  # Return with remaining errors
```

**Configuration:** `max_correction_attempts: int = 3` in pipeline config
**Example correction:** If friability says "Bonded" instead of "Non-friable",
the corrective loop maps it automatically via LLM re-prompting.

Rationale: Current Stage 2 validation returns errors but doesn't attempt self-correction.
Corrective RAG significantly improves extraction accuracy for edge cases.
```

---

### 4.3 Epics & Stories Updates (05-epics-and-stories.md)

#### CP-16: Add E1-S13 (Agentic Orchestrator)

```
### E1-S13: Agentic Extraction Orchestrator (NEW - RAG Strategy)
**As a** system
**I want** a LangGraph agent that dynamically routes document sections to extraction tools
**So that** the extraction pipeline adapts to document content rather than relying on static routing

**Acceptance Criteria:**
- [ ] LangGraph agent wraps existing Stage 0/1/2 pipeline
- [ ] Agent has tools: extract_metadata, extract_acm_table, extract_lab_results, validate_acm_record
- [ ] Agent reasons about each document section and selects appropriate tool
- [ ] Agent handles mixed-content pages (text + tables on same page)
- [ ] Maintains backward compatibility with existing ConsultantParser framework
- [ ] Extraction accuracy equal to or better than static routing
- [ ] Logging/tracing for agent decisions (for debugging)

**Technical Notes:**
- Location: `open_notebook/graphs/acm_extraction.py` (extend existing LangGraph usage)
- Pattern: Follow existing graph patterns in `open_notebook/graphs/`
- Integration: Replaces static `get_parser()` with agent-driven tool selection
- Reference: PRD FR-109
```

#### CP-17: Add E1-S14 (Contextual Embedding Enrichment)

```
### E1-S14: Contextual Embedding Enrichment (NEW - RAG Strategy)
**As a** system
**I want** to prepend hierarchical context (Building, Level, Room, Page) to ACM records before embedding
**So that** semantic search understands the document hierarchy and returns more relevant results

**Acceptance Criteria:**
- [ ] Enrichment function generates contextual text per ACM record
- [ ] Both raw_text and enriched_text stored per record
- [ ] enriched_text field added to acm_record schema
- [ ] Embedding pipeline uses enriched_text for vectorization
- [ ] Semantic search quality improves (measured: relevant results in top-5)
- [ ] Re-embedding command for existing records
- [ ] Backward compatible: records without enriched_text still searchable

**Technical Notes:**
- Location: `open_notebook/extractors/acm_extractor.py` (enrichment step)
- Migration: Add enriched_text field to acm_record table
- Reference: PRD FR-203 (updated), FR-209
- Pattern: Anthropic's contextual retrieval
```

#### CP-18: Add E1-S15 (Corrective RAG Validation)

```
### E1-S15: Corrective RAG Validation Loop (NEW - RAG Strategy)
**As a** system
**I want** a corrective validation loop that re-attempts extraction with corrective prompts on failure
**So that** extraction accuracy improves automatically for edge cases and ambiguous values

**Acceptance Criteria:**
- [ ] Validation failures trigger LLM re-extraction with corrective prompt
- [ ] Corrective prompt includes: original value, validation error, expected format/enum
- [ ] Maximum 3 correction attempts before accepting with errors
- [ ] Auto-correction for common synonym mismatches (e.g., "Bonded" → "Non-friable")
- [ ] Correction attempts logged for debugging and accuracy tracking
- [ ] Configuration: max_correction_attempts, enable/disable corrective loop
- [ ] Extraction accuracy >90% with corrective loop enabled
- [ ] Corrections tracked: count of auto-corrected vs manual-review-needed

**Technical Notes:**
- Location: `open_notebook/extractors/acm_extractor.py` (Stage 2 enhancement)
- Depends on: E1-S13 (Agentic Orchestrator) for LLM tool integration
- Reference: PRD FR-110
- Pattern: Pydantic validators + retry loop
```

#### CP-19: Add Epic 11 with E11-S1 and E11-S2

```
## Epic 11: Search & Retrieval Enhancement (NEW)

> **Created:** 2026-02-07 (Sprint Change Proposal - RAG Strategy Alignment)
> **Rationale:** Post-extraction querying requires parent-child document relationships
> and hybrid search combining keyword and semantic approaches.

### E11-S1: Parent Document Retrieval (NEW - RAG Strategy)
**As a** system
**I want** to store ACM table sections as parent documents linked to child ACM records
**So that** search results include full table context alongside matched individual records

**Acceptance Criteria:**
- [ ] acm_table_section table created in SurrealDB
- [ ] Fields: source_id, page_start, page_end, raw_html, raw_text, building_name, table_type
- [ ] parent_table_id field added to acm_record linking to parent section
- [ ] Extraction pipeline stores raw table sections during Stage 1
- [ ] ACM records reference their parent table section
- [ ] Search API returns parent context alongside matched records
- [ ] Chat context builder fetches parent context for cited records
- [ ] Migration script for existing records (backfill parent references)

**Technical Notes:**
- Location: `open_notebook/domain/acm.py` (new ACMTableSection model)
- Migration: New table + field addition to acm_record
- Reference: PRD FR-210, FR-211
- Integration: Chat context builder (Section 7.1) updated

---

### E11-S2: Hybrid Search Service (NEW - RAG Strategy)
**As a** system
**I want** to combine BM25 keyword search with vector semantic search using Reciprocal Rank Fusion
**So that** exact matches (sample numbers, room names) and conceptual matches (material descriptions) both work well

**Acceptance Criteria:**
- [ ] SurrealDB full-text search indexes created for ACM fields
- [ ] BM25 search implementation for keyword matching
- [ ] Vector search using enriched embeddings (from E1-S14)
- [ ] Reciprocal Rank Fusion combining both result sets
- [ ] HybridSearchService class with configurable weights
- [ ] Chat context builder uses hybrid search instead of full table dump
- [ ] API endpoint for hybrid ACM search
- [ ] Performance: search returns results in <500ms for 1000+ records
- [ ] Benchmark: hybrid vs vector-only accuracy comparison documented

**Technical Notes:**
- Location: `api/search_service.py` (extend existing) or new `api/acm_search_service.py`
- Dependencies: `rank-bm25` package
- DB: Full-text search analyzer + index definitions
- Reference: PRD FR-506
- Integration: Updates chat context builder from E4
```

#### CP-20: Update Epic Overview Table

```
Section: Epic Overview - UPDATE

| Epic | Title | Priority | Stories | Status |
|------|-------|----------|---------|--------|
| E1 | ACM Data Extraction Pipeline | P0 | **15** (+3 RAG) | Done (10), Backlog (5) |
| ... (E2-E10 unchanged) ...
| E11 | Search & Retrieval Enhancement | **P0/P1** | **2** (new) | Backlog |

> **2026-02-07 Update:** RAG Strategy Alignment added 3 new stories to E1 and created new Epic 11 with 2 stories.
```

#### CP-21: Update Story Dependencies

```
Section: Story Dependencies - ADD

# RAG Strategy Enhancement (NEW 2026-02-07)
E1-S3 (Pipeline, done) → E1-S13 (Agentic Orchestrator)
E1-S6 (Embeddings, done) → E1-S14 (Contextual Enrichment)
E1-S13 (Agentic) → E1-S15 (Corrective Validation)
E1-S3 (Pipeline, done) → E11-S1 (Parent Document Retrieval)
E1-S14 (Contextual) + E11-S1 (Parent Doc) → E11-S2 (Hybrid Search)
```

#### CP-22: Update MVP Scope Summary

```
Section: MVP Scope Summary - ADD

**Must Have (MVP) - RAG Strategy (NEW 2026-02-07):**
- E1: **S13 (Agentic Orchestrator)** - Dynamic extraction tool selection
- E1: **S14 (Contextual Enrichment)** - Hierarchical embedding context
- E11: **S1 (Parent Document Retrieval)** - Chunk hierarchy for retrieval

**Should Have - RAG Strategy:**
- E1: **S15 (Corrective Validation)** - Self-healing extraction loop
- E11: **S2 (Hybrid Search)** - BM25 + Vector + RRF

**Future (Phase 2+):**
- Reranking (BGE-reranker) - Query result prioritization
```

---

### 4.4 Extraction Pipeline Updates (extraction-pipeline.md)

#### CP-23: Add Agentic Orchestrator Layer

```
Section: Pipeline Overview diagram - WRAP with agentic layer

Add between Stage 0 (Preflight) and Stage 1 (Extract):

  STAGE 0.5: AGENTIC ORCHESTRATOR (NEW)
  ┌────────────────────────────────────────────────────────────────────────┐
  │ LangGraph Agent                                                       │
  │ ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────────┐│
  │ │  Analyze     │──▶│  Select      │──▶│   Invoke Tool               ││
  │ │  Section     │   │  Tool        │   │   (Docling/MinerU/Regex)    ││
  │ └──────────────┘   └──────────────┘   └─────────────────────────────┘│
  └────────────────────────────────────────────────────────────────────────┘

Rationale: Replaces static parser routing with LLM-driven dynamic tool selection
```

#### CP-24: Add Corrective Validation Stage

```
Section: Between Stage 2 output and OUTPUT section

  STAGE 2.5: CORRECTIVE VALIDATION (NEW)
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Validation errors? → LLM re-extraction with corrective prompt         │
  │ Max 3 attempts → Accept with remaining errors or fully corrected      │
  └────────────────────────────────────────────────────────────────────────┘
```

#### CP-25: Add Contextual Enrichment + Parent Storage to Output Stage

```
Section: OUTPUT stage - EXPAND

  OUTPUT: Store + Index + Enrich
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────────┐
  │  SurrealDB   │   │  Parent Doc  │   │  Contextual  │   │   Vector   │
  │  (Records)   │   │  Sections    │   │  Enrichment  │   │ Embeddings │
  └──────────────┘   └──────────────┘   └──────────────┘   └────────────┘
```

---

## 5. Implementation Handoff

### 5.1 Change Scope Classification: **Moderate**

This requires:
- Document updates (PRD, Architecture, Epics) - **SM/PM role**
- New story creation and backlog reorganization - **SM role**
- Implementation of 5 new stories - **Dev role**
- No fundamental replan needed - existing architecture holds

### 5.2 Handoff Plan

| Role | Responsibility | Deliverables |
|------|---------------|-------------|
| **SM (Scrum Master)** | Apply document edits from CPs 1-25 | Updated PRD, Architecture, Epics |
| **SM** | Update sprint-status.yaml with new stories | Updated tracking file |
| **SM** | Draft tech-specs for new stories (E1-S13, E1-S14, E1-S15, E11-S1, E11-S2) | Tech-spec files in sprint-artifacts/ |
| **Dev** | Implement stories in priority order | Working code, tests, verification |
| **User** | UX specification and audit (deferred) | UX spec document |

### 5.3 Success Criteria

- [ ] All 25 change proposals applied to project documents
- [ ] 5 new stories created with tech-specs
- [ ] Sprint status updated (57 → 62 stories)
- [ ] New Epic 11 added to tracking
- [ ] PRD Section 5.8 (RAG Strategy Stack) exists
- [ ] Architecture Section 5.0 (Agentic Orchestrator) exists
- [ ] Architecture Section 7.3 (Hybrid Search Service) exists
- [ ] Database schema includes acm_table_section table and full-text indexes
- [ ] UX spec/audit scheduled for after RAG alignment implementation

### 5.4 Notes

- **UX Specification:** User has requested a UX spec and audit after all document alignment is complete. This should be scheduled as a separate workflow after the RAG strategy stories are drafted.
- **Reranking:** Documented as Phase 2+ in PRD Section 9 (Open Items) and Architecture Section 10 (Technology Decisions). No story created for MVP.
- **Existing completed work:** All 50 completed stories remain valid. RAG enhancements build on top of the existing foundation without requiring any rework.

---

## Appendix: Change Proposal Index

| CP# | Target | Type | Description |
|-----|--------|------|-------------|
| CP-1 | PRD FR-102 | Update | Agentic multi-tool extraction |
| CP-2 | PRD FR-109 | Add | Agentic RAG orchestrator requirement |
| CP-3 | PRD FR-110 | Add | Corrective RAG validation requirement |
| CP-4 | PRD FR-203 | Update | Contextual embedding enrichment |
| CP-5 | PRD FR-209/210/211 | Add | Parent Document Retrieval requirements |
| CP-6 | PRD FR-506 | Add | Hybrid search requirement |
| CP-7 | PRD FR-501 | Update | Hybrid retrieval for chat |
| CP-8 | PRD Section 5.8 | Add | RAG Strategy Stack section |
| CP-9 | PRD Section 6.2 | Update | New dependencies |
| CP-10 | PRD Section 9 | Update | Open items (reranking, UX audit) |
| CP-11 | Arch Section 5.0 | Add | Agentic Orchestrator |
| CP-12 | Arch Pipeline | Add | Contextual Enrichment step |
| CP-13 | Arch DB Schema | Add | Parent doc table + full-text indexes |
| CP-14 | Arch Section 7.3 | Add | Hybrid Search Service |
| CP-15 | Arch Section 5.1.2 | Update | Corrective validation loop |
| CP-16 | Epics E1-S13 | Add | Agentic Orchestrator story |
| CP-17 | Epics E1-S14 | Add | Contextual Enrichment story |
| CP-18 | Epics E1-S15 | Add | Corrective Validation story |
| CP-19 | Epics E11 | Add | New epic + 2 stories |
| CP-20 | Epics Overview | Update | Epic table counts |
| CP-21 | Epics Dependencies | Update | RAG story dependencies |
| CP-22 | Epics MVP Scope | Update | RAG additions to scope |
| CP-23 | Pipeline | Add | Agentic layer diagram |
| CP-24 | Pipeline | Add | Corrective validation stage |
| CP-25 | Pipeline | Update | Enrichment + parent doc in output |
