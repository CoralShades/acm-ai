# Story 11.1: Parent Document Retrieval

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **system**,
I want **to store ACM table sections as parent documents linked to child ACM records**,
so that **search results include full table context alongside matched individual records, enabling richer retrieval and compliance auditing**.

## Acceptance Criteria

1. `acm_table_section` table created in SurrealDB with fields: `source_id`, `page_start`, `page_end`, `raw_html`, `raw_text`, `building_name`, `table_type`
2. `parent_table_id` field added to `acm_record` linking each record to its parent table section via `option<record<acm_table_section>>`
3. Extraction pipeline (both regex and LangGraph paths) stores raw table sections during Stage 1 extraction, creating `ACMTableSection` records
4. Each extracted `ACMRecord` references its parent table section via `parent_table_id`
5. Search API (`GET /api/acm/search`) returns parent context alongside matched records when `include_parent=true` query parameter is set
6. Chat context builder fetches parent context for cited records, providing richer table-level context
7. Migration script for existing records: backfill parent references by matching `source_id` + `page_number` range to table sections
8. Backward compatible: records without `parent_table_id` (pre-existing) still work in all search and display flows

## Tasks / Subtasks

- [x] Task 1: Create SurrealDB migration for `acm_table_section` table and `parent_table_id` field (AC: #1, #2)
  - [x] 1.1 Create `migrations/18.surrealql` with `acm_table_section` table definition (source_id, page_start, page_end, raw_html, raw_text, building_name, table_type, created)
  - [x] 1.2 Add `parent_table_id` field to `acm_record` table as `option<record<acm_table_section>>`
  - [x] 1.3 Create indexes: `section_source` on source_id, `section_pages` on page_start+page_end, `acm_parent` on acm_record.parent_table_id
  - [x] 1.4 Create `migrations/18_down.surrealql` rollback migration
- [x] Task 2: Create `ACMTableSection` Pydantic domain model (AC: #1, #3)
  - [x] 2.1 Create `ACMTableSection` class in `open_notebook/domain/acm.py` extending `ObjectModel`
  - [x] 2.2 Fields: `source_id: str`, `page_start: int`, `page_end: int`, `raw_html: Optional[str]`, `raw_text: Optional[str]`, `building_name: Optional[str]`, `table_type: Optional[str]` (values: "register", "lab_report", "metadata")
  - [x] 2.3 Add class method `get_by_source(source_id: str) -> List[ACMTableSection]`
  - [x] 2.4 Add class method `get_by_page_range(source_id: str, page: int) -> Optional[ACMTableSection]` for lookup by page number
  - [x] 2.5 Add `parent_table_id: Optional[str] = None` field to existing `ACMRecord` model
- [x] Task 3: Update extraction pipeline to create table sections (AC: #3, #4)
  - [x] 3.1 Parent section creation handled in save layer (`save_records()` in acm_extraction.py) using BuildingInventory data. The regex path (`acm_extractor.py`) is a pure extraction function returning dicts — DB operations are architecturally separated into the save layer where both extraction paths converge.
  - [x] 3.2 In `open_notebook/graphs/acm_extraction.py` (LangGraph path): `save_records()` creates `ACMTableSection` records from BuildingInventory before saving ACM records
  - [x] 3.3 Link each `ACMRecord` to its parent section via `section_map` (building_id → section_id) during record creation
  - [x] 3.4 Edge cases: records with no matching building get `parent_table_id=None`; `page_end` falls back to `page_start` when not available; force re-extraction deletes existing sections first
- [x] Task 4: Update search API to include parent context (AC: #5)
  - [x] 4.1 Add `include_parent: bool = False` query parameter to `GET /api/acm/search` endpoint in `api/routers/acm.py`
  - [x] 4.2 When `include_parent=true`, fetch parent `ACMTableSection` for each result and include in response
  - [x] 4.3 Add `parent_context` field to search response model containing the parent section's `raw_text`, `building_name`, `page_start`, `page_end`
  - [x] 4.4 Ensure no N+1 query: batch-fetch parent sections for all results in one query
- [x] Task 5: Update chat context builder (AC: #6)
  - [x] 5.1 In `open_notebook/graphs/source_chat.py`, `format_acm_context()` fetches `ACMTableSection.get_by_source()` to provide table-level context summary with building names, page ranges, and types
  - [x] 5.2 Include parent context summary (building, page range, table type) in chat context alongside individual record data
- [x] Task 6: Backfill migration for existing records (AC: #7)
  - [x] 6.1 Add `POST /api/acm/backfill-parents` endpoint to `api/routers/acm.py`
  - [x] 6.2 Implementation: query all `acm_record` where `parent_table_id IS NULL`, match each record's `source_id + page_number` to an `acm_table_section` page range, update `parent_table_id`
  - [x] 6.3 Support optional `source_id` filter parameter
  - [x] 6.4 Return count of records updated
- [x] Task 7: Unit and integration tests (AC: #1-#8)
  - [x] 7.1 Test `ACMTableSection` CRUD (create, get_by_source, get_by_page_range, delete_by_source) - 13 tests
  - [x] 7.2 Test extraction pipeline creates table sections and links records (via ACMRecord parent_table_id field tests)
  - [x] 7.3 Test search API with `include_parent=true` returns parent context
  - [x] 7.4 Test search API with `include_parent=false` (default) returns `parent_context: null`
  - [x] 7.5 Test backward compatibility: records without parent_table_id work in search and embedding
  - [x] 7.6 Test backfill endpoint links existing records to sections (3 test cases)
  - [x] 7.7 Full regression: 800/805 passed (5 pre-existing failures unrelated to E11-S1)

## Dev Notes

### Critical Context

This story implements **Parent Document Retrieval** as defined in the RAG Strategy Alignment change proposal (CP-5, CP-13, CP-19 from `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-07.md`). The pattern is:

1. During extraction, store the **full table section** (spanning multiple pages) as a "parent document"
2. Individual ACM records (extracted rows) are "child documents" linked via `parent_table_id`
3. When search finds a child record, the full parent table context can be returned alongside it
4. This enables the chat and search systems to provide richer, more contextual responses

### Architecture Pattern

```
PDF Extraction:
  Table Block (pages 14-16) → ACMTableSection { source_id, page_start=14, page_end=16, raw_text, building_name="B00A" }
       │
       ├── ACMRecord { product="Vinyl Tiles", parent_table_id=section_id, page_number=14 }
       ├── ACMRecord { product="Cement Sheet", parent_table_id=section_id, page_number=15 }
       └── ACMRecord { product="Gasket", parent_table_id=section_id, page_number=16 }

Search/Retrieval:
  Query → Vector Search → ACMRecord (child) → fetch parent ACMTableSection → return both
```

### Current Embedding Architecture (from E1-S14)

The embedding pipeline is already functional:

```
ACMRecord → get_enriched_embedding_text() → ACMEmbeddingService.embed_records() → SurrealDB MTREE index
```

- Vector index: `acm_embedding_idx` on `acm_record.embedding` (MTREE, 1536 dimensions, COSINE)
- Search endpoint: `GET /api/acm/search` using `vector::similarity::cosine()`
- Enriched text format: `"Level: {area_type} | Page: {page_number} | Building: {building_name} | Room: {room_name} | Product: ..."`
- Embedding fields: `embedding`, `embedding_text`, `enriched_text`, `embedding_model`, `embedded_at`

**This story does NOT change the embedding pipeline** - it adds a parallel "parent context" retrieval layer.

### Domain Model Pattern

All domain models extend `ObjectModel` from `open_notebook/domain/base.py`:

```python
class ObjectModel(BaseModel):
    id: Optional[str] = None
    table_name: ClassVar[str] = ""
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    @classmethod
    async def get(cls, id: str) -> T
    @classmethod
    async def get_all(cls, order_by=None) -> List[T]
    async def save(self) -> None
    async def delete(self) -> None
```

Follow this pattern exactly for `ACMTableSection`.

### Database Access Pattern

Repository layer in `open_notebook/database/repository.py`:

```python
async def repo_query(query_str: str, vars: Optional[Dict] = None) -> List[Dict]
async def repo_create(table: str, data: Dict) -> Dict
async def repo_update(table: str, id: str, data: Dict) -> List[Dict]
async def repo_delete(record_id: Union[str, RecordID])
```

Use `repo_query()` for the parent section lookup by page range:
```python
@classmethod
async def get_by_page_range(cls, source_id: str, page: int) -> Optional["ACMTableSection"]:
    results = await repo_query(
        "SELECT * FROM acm_table_section WHERE source_id = $source_id AND page_start <= $page AND page_end >= $page LIMIT 1",
        {"source_id": source_id, "page": page}
    )
    return cls(**results[0]) if results else None
```

### Migration Details

**Next migration number:** 18 (latest is `migrations/17.surrealql` for field_schema table)

```sql
-- migrations/18.surrealql: Parent Document Retrieval (E11-S1)

-- Create parent table section table
DEFINE TABLE acm_table_section SCHEMAFULL;
DEFINE FIELD source_id ON acm_table_section TYPE record<source>;
DEFINE FIELD page_start ON acm_table_section TYPE int;
DEFINE FIELD page_end ON acm_table_section TYPE int;
DEFINE FIELD raw_html ON acm_table_section TYPE option<string>;
DEFINE FIELD raw_text ON acm_table_section TYPE option<string>;
DEFINE FIELD building_name ON acm_table_section TYPE option<string>;
DEFINE FIELD table_type ON acm_table_section TYPE option<string>;
DEFINE FIELD created ON acm_table_section TYPE datetime DEFAULT time::now();

DEFINE INDEX section_source ON acm_table_section FIELDS source_id;
DEFINE INDEX section_pages ON acm_table_section FIELDS page_start, page_end;

-- Add parent reference to acm_record
DEFINE FIELD parent_table_id ON acm_record TYPE option<record<acm_table_section>>;
DEFINE INDEX acm_parent ON acm_record FIELDS parent_table_id;
```

```sql
-- migrations/18_down.surrealql
REMOVE INDEX acm_parent ON TABLE acm_record;
REMOVE FIELD parent_table_id ON TABLE acm_record;
REMOVE TABLE acm_table_section;
```

### Extraction Integration Points

**Regex path** (`open_notebook/extractors/acm_extractor.py`):
- MinerU extracts tables with `page`, `html`, `bbox` metadata
- Each table block becomes an `ACMTableSection`
- The `building_name` is already tracked per table block via building header parsing
- Page ranges are known from MinerU's per-page table grouping

**LangGraph path** (`open_notebook/graphs/acm_extraction.py`):
- The `extract_records` node processes markdown content with page markers (`<!-- Page N -->`)
- Table blocks are identifiable by the building header pattern: `^([A-Z]\d+[A-Z]?)\s*[-–]\s*(.+?)$`
- Each building section (from header to next header) defines a table section's page range

**Orchestrator path** (`open_notebook/extractors/orchestrator.py`, E1-S20):
- The agentic orchestrator already identifies buildings and their page ranges via `BuildingInventory`
- `BuildingMeta` contains: `building_code`, `building_name`, `page_start`, `page_end`
- This is the **ideal source** for `ACMTableSection` data - the orchestrator already knows exactly which pages belong to which building

### Previous Story Learnings (E1-S14)

From E1-S14 code review:
- **Avoid duplication**: E1-S14 had a bug where Building/Room appeared in both context prefix AND raw text. Ensure parent context doesn't duplicate data already in the record.
- **Batch operations**: Use batch queries when fetching parent sections for search results (avoid N+1).
- **Domain model location**: New model goes in `open_notebook/domain/acm.py` (same file as `ACMRecord`).
- **Migration pattern**: Simple forward/rollback pair, auto-runs on API startup.
- **Test pattern**: Use `tests/test_acm_*.py` naming, mock SurrealDB calls.

### Anti-Patterns to Avoid

- **DO NOT** modify the embedding pipeline or vector index - parent document retrieval is a separate retrieval layer
- **DO NOT** fetch parent context by default in search results - use `include_parent=true` opt-in to avoid performance regression
- **DO NOT** create a separate domain file for `ACMTableSection` - put it in `acm.py` alongside `ACMRecord` for cohesion
- **DO NOT** make parent_table_id required - it must be Optional for backward compatibility
- **DO NOT** add new Python dependencies - SurrealDB already supports all needed queries
- **DO NOT** block extraction if table section creation fails - extraction must succeed even without parent linking

### Search Response Enhancement

Current search response shape:
```python
{
    "records": [ACMRecord, ...],
    "total": int,
    "query": str
}
```

Enhanced response when `include_parent=true`:
```python
{
    "records": [
        {
            ...ACMRecord fields...,
            "parent_context": {
                "id": "acm_table_section:xxx",
                "building_name": "B00A Main Block",
                "page_start": 14,
                "page_end": 16,
                "table_type": "register",
                "raw_text": "Full table text content..."  # Truncated if very long
            }
        }
    ],
    "total": int,
    "query": str
}
```

### Project Structure Notes

- Alignment with existing extraction pipeline patterns (MinerU → tables → records)
- `ACMTableSection` sits between `source` and `acm_record` in the data hierarchy
- No frontend changes required for this story (backend-only)
- E11-S2 (Hybrid Search) will build on this by using parent context in search ranking

### Testing Approach

Extend existing test files:

1. **`tests/test_parent_document.py`** (new file):
   - `TestACMTableSectionModel`: CRUD operations, get_by_source, get_by_page_range
   - `TestParentLinking`: extraction creates sections and links records
   - `TestSearchWithParent`: search includes parent context when requested
   - `TestBackfillEndpoint`: backfill links existing records

2. **Regression tests**: Run full `uv run pytest` to ensure no breakage

### References

- [Sprint Change Proposal](_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-07.md) - CP-5, CP-13, CP-19
- [PRD FR-210, FR-211](PRD Section 2.2) - Parent Document Retrieval requirements
- [Architecture CP-13](Architecture Section 3.1) - Database schema design
- [acm.py](open_notebook/domain/acm.py) - ACMRecord model with embedding fields
- [acm_extractor.py](open_notebook/extractors/acm_extractor.py) - Regex extraction pipeline
- [acm_extraction.py](open_notebook/graphs/acm_extraction.py) - LangGraph extraction
- [orchestrator.py](open_notebook/extractors/orchestrator.py) - Agentic orchestrator with BuildingInventory
- [repository.py](open_notebook/database/repository.py) - Database access patterns
- [acm_embedding_service.py](api/services/acm_embedding_service.py) - Embedding service patterns
- [acm.py router](api/routers/acm.py) - Search endpoint at ~line 504
- [E1-S14 Story](e1-s14-contextual-embedding-enrichment.md) - Previous story with embedding learnings
- [Migration 17](migrations/17.surrealql) - Latest migration (field_schema table)
- [Migration 12](migrations/12.surrealql) - Embedding schema reference

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Test run: 23/23 passed in `tests/test_parent_document.py`
- Regression: 800/805 passed (5 pre-existing failures in test_acm_ai_extraction.py and test_acm_extractor_integration.py — ConfidenceDistribution subscript issue + field accuracy assertions)

### Completion Notes List

1. **Migration 18** created following exact pattern from Dev Notes spec. Forward + rollback migrations.
2. **ACMTableSection model** extends ObjectModel with source_id validator (auto-prefix), get_by_source, get_by_page_range, delete_by_source methods. Uses repo_query for all DB operations.
3. **ACMRecord extended** with parent_table_id field. _prepare_save_data converts to RecordID. Backward compatible (defaults to None).
4. **Extraction pipeline**: Parent section creation in `save_records()` (save layer) using BuildingInventory from orchestrator state. Section map links building_id → section_id. Force re-extraction deletes sections first.
5. **Design decision (Task 3.1)**: `acm_extractor.py` is a pure extraction function returning List[dict] without DB access. Parent section creation belongs in the save layer where both extraction paths converge, not in the extraction function.
6. **Search API**: `include_parent=true` opt-in parameter per anti-patterns guidance. ParentContextResponse model with building_name, page_start, page_end, table_type, raw_text.
7. **Chat context**: `format_acm_context()` enhanced to fetch and display ACMTableSection summary after record formatting.
8. **Backfill endpoint**: POST /api/acm/backfill-parents with optional source_id filter. Matches records by source_id + page_number range.
9. **Bug fix**: Added missing `from loguru import logger` import to source_chat.py (used in the E11-S1 exception handler on line 249).

### File List

| File | Action | Description |
|------|--------|-------------|
| `migrations/18.surrealql` | Created | acm_table_section table, parent_table_id field, indexes |
| `migrations/18_down.surrealql` | Created | Rollback migration |
| `open_notebook/domain/acm.py` | Modified | ACMTableSection class, parent_table_id on ACMRecord |
| `open_notebook/graphs/acm_extraction.py` | Modified | save_records creates sections from BuildingInventory, extract_acm_from_source deletes sections on force |
| `open_notebook/graphs/source_chat.py` | Modified | format_acm_context adds parent table section summary, added logger import |
| `api/models.py` | Modified | ParentContextResponse, BackfillParentsRequest/Response models |
| `api/routers/acm.py` | Modified | search include_parent param, backfill-parents endpoint |
| `tests/test_parent_document.py` | Created | 23 tests across 6 test classes |

### Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-02-09 | Initial implementation of all 7 tasks | E11-S1 Parent Document Retrieval |
| 2026-02-09 | Fixed missing logger import in source_chat.py | Bug found during review |
| 2026-02-10 | Code review: 6 issues found, all fixed | Adversarial code review |
| 2026-02-10 | Fix: Added `updated` field to migration 18 (SCHEMAFULL table requires explicit field) | Issue #2 HIGH |
| 2026-02-10 | Fix: Replaced N+1 per-record parent query with batch fetch via `get_by_source` + direct ID lookup | Issues #1+#4 HIGH+MEDIUM |
| 2026-02-10 | Fix: Added `_extract_page_range_text()` helper, sections now populate `raw_text` from source content | Issue #3 MEDIUM |
| 2026-02-10 | Fix: Changed `logger.debug` to `logger.warning` in source_chat.py exception handler | Issue #6 LOW |
| 2026-02-10 | Fix: Added integration test for `save_records` parent section creation (TestSaveRecordsParentCreation) | Issue #5 MEDIUM |
| 2026-02-10 | Updated search test mocks from `get_by_page_range` to `get_by_source` to match batch fetch refactor | Test alignment |
