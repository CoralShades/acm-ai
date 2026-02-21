# Story E11-S2: Hybrid Search Service

**Epic:** E11 — Search & Retrieval Enhancement
**Priority:** P1
**Status:** done
**Change Proposal:** SCP-2026-02-07 (RAG Strategy Alignment, CP-19)

---

## User Story

**As a** system serving ACM compliance queries,
**I want to** combine BM25 keyword search with vector semantic search using Reciprocal Rank Fusion,
**So that** exact matches (sample numbers, room names, building codes) and conceptual matches (material descriptions, hygienist recommendations) both surface relevant records — improving on the current vector-only approach.

---

## Background

E11-S1 (Parent Document Retrieval, done) established the `acm_table_section` parent-child relationship and the vector search infrastructure at `GET /api/acm/search`. That story provides the parent context enrichment this story builds upon.

E1-S14 (Contextual Embedding Enrichment, done) created enriched embeddings using hierarchical context (Building, Level, Room, Page) prepended before vectorization. These enriched embeddings are the vector side of the hybrid search.

The current search is **vector-only**, which means exact token matches (e.g., sample number "NTL-0012", room code "R003") score poorly because semantic similarity does not weight exact string matches highly. A hybrid approach combining BM25 (which excels at exact lexical matches) with vector search (which handles conceptual similarity) via Reciprocal Rank Fusion (RRF) is the standard solution.

**This story does not change the embedding pipeline or extraction.** It adds a new retrieval layer on top of existing data.

### Current Search Infrastructure (from E11-S1)

```
GET /api/acm/search?query=...&source_id=...&limit=...&include_parent=true
  → vector::similarity::cosine() on acm_record.embedding
  → returns ACMSearchResultResponse with optional parent_context
```

Location: `api/routers/acm.py` (~line 504 for search endpoint)

---

## Acceptance Criteria

- [ ] **SurrealDB full-text search indexes** created for ACM fields via migration:
  - Analyzer: `acm_analyzer` with `TOKENIZERS class FILTERS lowercase, snowball(en)`
  - Index: `acm_fulltext ON acm_record FIELDS product, material_description, room_name, building_name` using the analyzer
  - Index: `acm_sample_idx ON acm_record FIELDS sample_no` (exact lookup for sample numbers)
- [ ] **`HybridSearchService` class** implemented with:
  - `bm25_search(query, source_id, top_k)` — full-text keyword search via SurrealDB `SEARCH` operator
  - `vector_search(query, source_id, top_k)` — existing cosine similarity search
  - `reciprocal_rank_fusion(bm25_results, vector_results, k=60)` — RRF score merging
  - `search(query, source_id, top_k, bm25_weight, vector_weight)` — public API combining both
- [ ] **Chat context builder updated** — `format_acm_context()` in `open_notebook/graphs/source_chat.py` uses hybrid search for retrieval instead of full table dump
- [ ] **API endpoint** — existing `GET /api/acm/search` extended (or new endpoint `GET /api/acm/hybrid-search`) to use `HybridSearchService`; accepts optional `search_mode` parameter: `"hybrid"` (default), `"vector"`, `"bm25"` for comparison
- [ ] **Parent context enrichment** — hybrid search results pass through the same `include_parent` enrichment as the existing vector search (reuse from E11-S1)
- [ ] **Performance** — search returns results in <500ms for a source with 1000+ records
- [ ] **Benchmark documented** — a simple comparison test showing hybrid search result quality vs vector-only on 3 representative queries (e.g., sample number lookup, building name lookup, description conceptual match); results documented in the Dev Agent Record
- [ ] **Dependency added** — `rank-bm25` package added to `pyproject.toml` (used for any in-Python BM25 scoring as fallback or supplement to SurrealDB full-text)
- [ ] **Tests pass** — `uv run pytest` passes; new tests cover `HybridSearchService` unit tests and the search endpoint with `search_mode` variants

---

## Technical Notes

### Architecture: Hybrid Search with RRF

```
User query: "vinyl tiles B00A"
      │
      ├── BM25 (keyword) ──→ SurrealDB SEARCH ANALYZER ──→ ranked list by BM25 score
      │                       ["vinyl tiles B00A row 1" rank 1, "B00A ceiling" rank 2, ...]
      │
      └── Vector (semantic) ──→ cosine similarity on embedding ──→ ranked list by cosine score
                               ["Non-friable ceiling tiles" rank 1, "vinyl sheet flooring" rank 2, ...]
                                        │
                         RRF(k=60): score[id] += 1/(k + rank)
                                        │
                              Merged & sorted by RRF score
                                        │
                         Enrich top-K with parent context (E11-S1)
```

### Service Location

Create new file: `api/services/acm_hybrid_search_service.py`

```python
from collections import defaultdict
from typing import Optional
from open_notebook.database.repository import repo_query

class HybridSearchService:
    """Combines BM25 keyword search with vector semantic search using RRF."""

    async def search(
        self,
        query: str,
        source_id: str,
        top_k: int = 20,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> list[dict]:
        bm25_results = await self.bm25_search(query, source_id, top_k * 2)
        vector_results = await self.vector_search(query, source_id, top_k * 2)
        return self.reciprocal_rank_fusion(bm25_results, vector_results)[:top_k]

    async def bm25_search(self, query: str, source_id: str, top_k: int) -> list[dict]:
        """Full-text search using SurrealDB SEARCH operator."""
        results = await repo_query(
            """
            SELECT id, product, material_description, room_name, building_name,
                   search::score(0) AS bm25_score
            FROM acm_record
            WHERE source_id = $source_id
              AND (product @0@ $query
                OR material_description @0@ $query
                OR room_name @0@ $query
                OR building_name @0@ $query)
            ORDER BY bm25_score DESC
            LIMIT $limit
            """,
            {"source_id": source_id, "query": query, "limit": top_k},
        )
        return results

    async def vector_search(self, query: str, source_id: str, top_k: int) -> list[dict]:
        """Semantic search using cosine similarity on enriched embeddings."""
        # Embed the query using existing embedding service
        # Then: SELECT *, vector::similarity::cosine(embedding, $query_vec) AS score ...
        # (reuse existing search logic from api/routers/acm.py)
        ...

    def reciprocal_rank_fusion(self, *result_lists, k: int = 60) -> list[dict]:
        """Merge ranked lists via RRF: score[id] += 1 / (k + rank)."""
        scores: dict[str, float] = defaultdict(float)
        record_map: dict[str, dict] = {}
        for results in result_lists:
            for rank, record in enumerate(results):
                record_id = record["id"]
                scores[record_id] += 1.0 / (k + rank + 1)
                record_map[record_id] = record
        sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
        return [record_map[rid] for rid in sorted_ids]
```

### SurrealDB Migration

Create `migrations/19.surrealql`:

```sql
-- Migration 19: Hybrid Search Full-Text Indexes (E11-S2)

DEFINE ANALYZER acm_analyzer
  TOKENIZERS class
  FILTERS lowercase, snowball(en);

DEFINE INDEX acm_fulltext ON TABLE acm_record
  FIELDS product, material_description, room_name, building_name
  SEARCH ANALYZER acm_analyzer BM25;

DEFINE INDEX acm_sample_idx ON TABLE acm_record
  FIELDS sample_no;
```

Create `migrations/19_down.surrealql`:

```sql
REMOVE INDEX acm_fulltext ON TABLE acm_record;
REMOVE INDEX acm_sample_idx ON TABLE acm_record;
REMOVE ANALYZER acm_analyzer;
```

**Note:** Check current migration count first. `migrations/18.surrealql` was created by E11-S1. The next available number is 19 unless another migration was added after E11-S1 merged.

### API Endpoint Changes

Extend `GET /api/acm/search` in `api/routers/acm.py` to accept:
```
?query=...&source_id=...&limit=20&include_parent=false&search_mode=hybrid
```

`search_mode` values: `"hybrid"` (default), `"vector"`, `"bm25"`

This allows A/B comparison without a breaking change.

### Chat Context Builder Update

In `open_notebook/graphs/source_chat.py`, `format_acm_context()` currently dumps all records for a source. Replace with a targeted hybrid search call:

```python
# Before: fetches all records and formats as table
records = await ACMRecord.get_by_source(source_id)

# After: retrieves top-K most relevant records for the current query
hybrid_svc = HybridSearchService()
results = await hybrid_svc.search(query=user_message, source_id=source_id, top_k=20)
```

This change reduces token usage for large documents (100+ record SAMPs) and improves answer relevance.

### Dependencies

Add to `pyproject.toml`:
```toml
"rank-bm25>=0.2.2",
```

Note: The primary BM25 implementation should use SurrealDB's native `SEARCH ANALYZER BM25` for performance. The `rank-bm25` Python package is a fallback for in-memory scoring when needed (e.g., unit tests without a live SurrealDB instance).

---

## Files to Create or Modify

| File | Action | Description |
|------|--------|-------------|
| `api/services/acm_hybrid_search_service.py` | Create | HybridSearchService class |
| `api/routers/acm.py` | Modify | Add `search_mode` param to search endpoint, wire HybridSearchService |
| `open_notebook/graphs/source_chat.py` | Modify | Replace full table dump with hybrid search in `format_acm_context()` |
| `migrations/19.surrealql` | Create | Full-text analyzer + indexes |
| `migrations/19_down.surrealql` | Create | Rollback migration |
| `pyproject.toml` | Modify | Add `rank-bm25` dependency |
| `tests/test_hybrid_search.py` | Create | Unit tests for HybridSearchService and search endpoint |
| `api/models.py` | Modify | Add `search_mode` field to request models if needed |

---

## Dependencies

- **Requires:** E11-S1 (done — parent document retrieval infrastructure, `include_parent` search param)
- **Requires:** E1-S14 (done — enriched embeddings on ACM records, existing vector search endpoint)
- **Blocks:** Reranking (future P2 — BGE-reranker would wrap this hybrid service)

---

## Estimated Effort

L (Large) — Two new code paths (BM25 + RRF) plus SurrealDB migration, chat context refactor, and API endpoint extension. The SurrealDB SEARCH operator syntax requires verification against the installed SurrealDB version. Benchmark documentation adds additional effort.

---

## Dev Agent Record

_To be filled in during implementation._

### Agent Model Used

_TBD_

### Debug Log References

_TBD_

### Completion Notes

_TBD_

### File List

_TBD_

### Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-02-20 | Story doc created | Backlog story ready for tech-spec drafting |
