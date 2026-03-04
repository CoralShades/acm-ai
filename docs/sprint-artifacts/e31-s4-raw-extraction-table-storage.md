# Tech Spec: E31-S4 — Raw Extraction Table + Storage

**Sprint:** V3-3
**Story Points:** 2
**Risk:** LOW
**Type:** Backend
**Status:** ready-for-dev
**Depends on:** E31-S2 (Provider Adapter Framework — DONE, commit f1152678)

---

## 1. Problem Statement

After E31-S2 introduced the `ProviderRegistry` + `NormalizedExtractionResult` abstraction, the
extraction pipeline calls `provider.extract(pdf_path)` and receives a list of `NormalizedTable`
objects. However, that raw output is immediately discarded after being converted into
`acm_table_section` rows.

This creates three problems:

1. **No audit trail.** If Docling and MinerU disagree on a table, there is no way to compare
   their raw outputs after the fact. The raw HTML, markdown, bounding boxes, and confidence
   scores from each provider are lost.

2. **Consensus merge is impossible without raw inputs.** E31-S3 (upcoming) will implement a
   consensus algorithm. It needs per-provider raw outputs persisted in the database, not
   reconstructed from `acm_table_section` which already merges everything into one record.

3. **Officer edits have no provenance.** When a user manually corrects an extracted table cell,
   there is nowhere to record what was changed, by whom, and from what original value.

This story introduces `raw_extraction` as a first-class table that stores the per-provider raw
output from each extraction run, and adds `consensus_tier` / `consensus_scores` metadata columns
to `acm_table_section` to record how each merged section was produced.

---

## 2. Solution Design

### 2.1 SurrealDB Schema

#### New table: `raw_extraction`

One row per provider per page per extraction run. The `provider_id` + `source_id` + `page_number`
combination uniquely identifies a provider's view of a given page.

```
raw_extraction
  id                  auto (SurrealDB ULID)
  source_id           record<source>           -- FK to source table
  provider_id         string                   -- "docling" | "mineru" | ...
  extraction_backend  string                   -- e.g. "docling:2.x", "mineru:2.7"
  page_number         int                      -- 1-based page number from NormalizedTable.page
  raw_html            option<string>           -- NormalizedTable.html
  raw_markdown        option<string>           -- NormalizedTable.markdown
  structured_json     option<string>           -- serialised JSON of NormalizedTable.columns + row data
  bbox                option<object>           -- NormalizedTable.bbox as dict {x,y,width,height,page}
  confidence          option<float>            -- overall table confidence (0.0–1.0)
  officer_edits       array                    -- list of edit objects (default [])
  created_at          datetime
```

The `officer_edits` array stores edit event objects in this shape (validated at the application
layer only, stored as opaque objects in SurrealDB):

```json
{
  "field": "raw_html",
  "old_value": "...",
  "new_value": "...",
  "edited_by": "officer@example.com",
  "edited_at": "2026-03-04T10:00:00Z"
}
```

#### Additive columns on existing table: `acm_table_section`

These two columns support E31-S3 (consensus algorithm) without requiring a schema migration at
that point:

```
acm_table_section
  consensus_tier      option<string>   -- "single_provider" | "multi_provider_agreement" | "multi_provider_conflict" | "manual_override"
  consensus_scores    option<object>   -- {docling: 0.95, mineru: 0.88, agreement: 0.92}
```

### 2.2 Domain Models

#### `RawExtraction` (new class in `open_notebook/domain/acm.py`)

```python
class RawExtraction(ObjectModel):
    table_name = "raw_extraction"

    source_id: str
    provider_id: str
    extraction_backend: str
    page_number: int
    raw_html: Optional[str] = None
    raw_markdown: Optional[str] = None
    structured_json: Optional[str] = None
    bbox: Optional[dict] = None
    confidence: Optional[float] = None
    officer_edits: List[dict] = Field(default_factory=list)
    created_at: Optional[datetime] = None
```

Class methods:
- `get_by_source(source_id, provider=None)` — list all raw extractions for a source, with optional provider filter
- `delete_by_source(source_id)` — bulk delete (used when re-extracting)

#### `ACMTableSection` — additive fields (extend existing class)

```python
consensus_tier: Optional[str] = None
consensus_scores: Optional[dict] = None
```

### 2.3 Repository Layer

No new repository functions required. The `RawExtraction` domain model uses the existing
`ObjectModel` base class which delegates to `repo_create`, `repo_query`, and `repo_delete`.

The `source_commands.py` wiring (AC2) calls `RawExtraction(...).save()` directly on the domain
object, following the same pattern as `source_intelligence` in E30-S9.

### 2.4 API Endpoint

```
GET /api/acm/raw-extractions/{source_id}
  ?provider=docling      (optional, filters by provider_id)
  ?page_number=3         (optional, filters by page_number)
```

Response shape:

```json
{
  "extractions": [
    {
      "id": "raw_extraction:abc123",
      "source_id": "source:xyz",
      "provider_id": "docling",
      "extraction_backend": "docling:2.x",
      "page_number": 3,
      "raw_html": "<table>...</table>",
      "raw_markdown": "| col1 | col2 |...",
      "structured_json": "{...}",
      "bbox": {"x": 0.0, "y": 0.0, "width": 100.0, "height": 50.0, "page": 3},
      "confidence": 0.95,
      "officer_edits": [],
      "created_at": "2026-03-04T10:00:00Z"
    }
  ],
  "total": 1,
  "source_id": "source:xyz"
}
```

### 2.5 Wiring in `source_commands.py`

After the provider extracts tables and before `_store_docling_tables` is called, iterate over
`extraction_result.tables` and persist each `NormalizedTable` as a `RawExtraction` record.

The `extraction_backend` value is derived from `extraction_result.provider_id` plus a version
suffix obtained via `provider.__class__.__name__` or a new optional `backend_version` property.
For the current sprint, use `f"{extraction_result.provider_id}:2.x"` as a safe constant.

---

## 3. File Changes Table

| File | Action | Description |
|------|--------|-------------|
| `migrations/42.surrealql` | CREATE | Define `raw_extraction` table + additive fields on `acm_table_section` |
| `migrations/42_down.surrealql` | CREATE | Rollback: remove `raw_extraction`, remove additive fields |
| `open_notebook/domain/acm.py` | MODIFY | Add `RawExtraction` domain class; add `consensus_tier` and `consensus_scores` fields to `ACMTableSection` |
| `api/models.py` | MODIFY | Add `RawExtractionResponse` and `RawExtractionListResponse` Pydantic models |
| `api/routers/acm.py` | MODIFY | Add `GET /raw-extractions/{source_id}` endpoint |
| `commands/source_commands.py` | MODIFY | Wire `RawExtraction.save()` after each provider extraction run |
| `tests/test_raw_extraction_storage.py` | CREATE | Unit tests (all mocked, no live DB) |

---

## 4. Implementation Steps

### Step 1 — Create migration 42

Create `migrations/42.surrealql`:

```sql
-- Migration 42: Raw extraction table + consensus columns on acm_table_section (E31-S4)
-- Stores per-provider raw output from each extraction run before consensus merge.

DEFINE TABLE IF NOT EXISTS raw_extraction SCHEMAFULL;

-- Foreign key to source document
DEFINE FIELD IF NOT EXISTS source_id           ON TABLE raw_extraction TYPE record<source>;

-- Provider identification
DEFINE FIELD IF NOT EXISTS provider_id         ON TABLE raw_extraction TYPE string;
DEFINE FIELD IF NOT EXISTS extraction_backend  ON TABLE raw_extraction TYPE string;

-- Page-level data
DEFINE FIELD IF NOT EXISTS page_number         ON TABLE raw_extraction TYPE int;

-- Raw outputs from the provider
DEFINE FIELD IF NOT EXISTS raw_html            ON TABLE raw_extraction TYPE option<string>;
DEFINE FIELD IF NOT EXISTS raw_markdown        ON TABLE raw_extraction TYPE option<string>;
DEFINE FIELD IF NOT EXISTS structured_json     ON TABLE raw_extraction TYPE option<string>;

-- Provenance / quality fields
DEFINE FIELD IF NOT EXISTS bbox                ON TABLE raw_extraction TYPE option<object>;
DEFINE FIELD IF NOT EXISTS confidence          ON TABLE raw_extraction TYPE option<float>;

-- Officer correction audit trail (array of edit event objects)
DEFINE FIELD IF NOT EXISTS officer_edits       ON TABLE raw_extraction TYPE array DEFAULT [];

-- Timestamps
DEFINE FIELD IF NOT EXISTS created_at          ON TABLE raw_extraction TYPE option<datetime> DEFAULT time::now();

-- Indexes for common query patterns
DEFINE INDEX IF NOT EXISTS idx_raw_extraction_source_id
    ON TABLE raw_extraction
    FIELDS source_id;

DEFINE INDEX IF NOT EXISTS idx_raw_extraction_source_provider
    ON TABLE raw_extraction
    FIELDS source_id, provider_id;

-- Additive columns on acm_table_section for consensus merge metadata (E31-S3 prep)
DEFINE FIELD IF NOT EXISTS consensus_tier   ON TABLE acm_table_section TYPE option<string>;
DEFINE FIELD IF NOT EXISTS consensus_scores ON TABLE acm_table_section TYPE option<object>;
```

Create `migrations/42_down.surrealql`:

```sql
-- Rollback migration 42: Remove raw_extraction table + consensus columns (E31-S4)

REMOVE INDEX IF EXISTS idx_raw_extraction_source_provider ON TABLE raw_extraction;
REMOVE INDEX IF EXISTS idx_raw_extraction_source_id ON TABLE raw_extraction;
REMOVE TABLE IF EXISTS raw_extraction;

REMOVE FIELD IF EXISTS consensus_tier   ON TABLE acm_table_section;
REMOVE FIELD IF EXISTS consensus_scores ON TABLE acm_table_section;
```

### Step 2 — Add `RawExtraction` domain class to `open_notebook/domain/acm.py`

Append the following class after the `ACMTableSection` class (after line 1087). Also add
`consensus_tier` and `consensus_scores` fields to the `ACMTableSection` class body.

**2a. Modify `ACMTableSection`** — add two fields immediately after the `table_type` field
(around line 1019):

```python
    consensus_tier: Optional[str] = Field(
        default=None,
        description="How consensus was reached: 'single_provider' | 'multi_provider_agreement' | 'multi_provider_conflict' | 'manual_override'",
    )
    consensus_scores: Optional[dict] = Field(
        default=None,
        description="Per-provider confidence scores and agreement score: {provider_id: float, ..., agreement: float}",
    )
```

**2b. Add `RawExtraction` class** at the end of the file:

```python
class RawExtraction(ObjectModel):
    """Per-provider raw extraction output stored before consensus merge (E31-S4).

    One row per provider per page per extraction run. Stores the raw HTML,
    markdown, and structured JSON emitted by a provider adapter, along with
    bounding box and confidence data for provenance tracking.

    The officer_edits field accumulates an audit trail of manual corrections
    applied to this raw extraction row.
    """

    table_name: ClassVar[str] = "raw_extraction"

    # FK to source document
    source_id: str

    # Provider identification
    provider_id: str = Field(
        ...,
        description="Stable provider ID from ProviderRegistry (e.g. 'docling', 'mineru')",
    )
    extraction_backend: str = Field(
        ...,
        description="Provider + version string (e.g. 'docling:2.x', 'mineru:2.7')",
    )

    # Page-level data
    page_number: int = Field(
        ...,
        description="1-based page number from NormalizedTable.page",
    )

    # Raw outputs
    raw_html: Optional[str] = None
    raw_markdown: Optional[str] = None
    structured_json: Optional[str] = Field(
        default=None,
        description="JSON-serialised column headers + row data from NormalizedTable",
    )

    # Provenance
    bbox: Optional[dict] = Field(
        default=None,
        description="Bounding box dict {x, y, width, height, page} from NormalizedTable.bbox",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Overall table confidence (0.0–1.0) from the provider",
    )

    # Audit trail
    officer_edits: List[dict] = Field(
        default_factory=list,
        description="Ordered list of officer edit events applied to this raw row",
    )

    # Timestamp
    created_at: Optional[datetime] = None

    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, v):
        if not v:
            raise InvalidInputError("source_id is required")
        if isinstance(v, str) and not v.startswith("source:"):
            return f"source:{v}"
        return str(v)

    @field_validator("provider_id")
    @classmethod
    def validate_provider_id(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("provider_id cannot be empty")
        return v.strip()

    @field_validator("page_number")
    @classmethod
    def validate_page_number(cls, v):
        if v < -1:
            raise InvalidInputError("page_number must be >= -1 (-1 means unknown)")
        return v

    @classmethod
    async def get_by_source(
        cls,
        source_id: str,
        provider: Optional[str] = None,
        page_number: Optional[int] = None,
    ) -> List["RawExtraction"]:
        """Get raw extractions for a source, with optional provider and page filters."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            conditions = ["source_id = $source_id"]
            params: dict = {"source_id": ensure_record_id(source_id)}

            if provider:
                conditions.append("provider_id = $provider_id")
                params["provider_id"] = provider

            if page_number is not None:
                conditions.append("page_number = $page_number")
                params["page_number"] = page_number

            where_clause = " AND ".join(conditions)
            result = await repo_query(
                f"SELECT * FROM raw_extraction WHERE {where_clause} ORDER BY page_number, provider_id",
                params,
            )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(
                f"Error fetching raw extractions for source {source_id}: {e}"
            )
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_source(cls, source_id: str) -> int:
        """Delete all raw extractions for a source. Returns count deleted."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "DELETE raw_extraction WHERE source_id = $source_id RETURN BEFORE",
                {"source_id": ensure_record_id(source_id)},
            )
            return len(result) if result else 0
        except Exception as e:
            logger.error(
                f"Error deleting raw extractions for source {source_id}: {e}"
            )
            raise DatabaseOperationError(e)

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id is proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        return data
```

### Step 3 — Add Pydantic models to `api/models.py`

Add the following two classes after the `RawTableResponse` class (around line 642):

```python
class RawExtractionResponse(BaseModel):
    """Response model for a single raw extraction record (E31-S4)."""

    id: str
    source_id: str
    provider_id: str
    extraction_backend: str
    page_number: int
    raw_html: Optional[str] = None
    raw_markdown: Optional[str] = None
    structured_json: Optional[str] = None
    bbox: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    officer_edits: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[str] = None


class RawExtractionListResponse(BaseModel):
    """Response for GET /api/acm/raw-extractions/{source_id} (E31-S4)."""

    extractions: List[RawExtractionResponse]
    total: int
    source_id: str
```

Note: `Dict` and `Any` are already imported at the top of `api/models.py`.

### Step 4 — Add API endpoint to `api/routers/acm.py`

**4a. Add imports.** In the import block at the top of `api/routers/acm.py`, add
`RawExtractionListResponse` and `RawExtractionResponse` to the `from api.models import (...)`
statement, and add `RawExtraction` to the `from open_notebook.domain.acm import (...)` statement.

**4b. Add the endpoint.** Insert the following handler anywhere in the router file, recommended
placement is after the existing raw tables endpoint (search for `RawTableResponse` usage):

```python
@router.get(
    "/raw-extractions/{source_id}",
    response_model=RawExtractionListResponse,
)
async def list_raw_extractions(
    source_id: str,
    provider: Optional[str] = Query(
        None,
        description="Filter by provider_id (e.g. 'docling', 'mineru')",
    ),
    page_number: Optional[int] = Query(
        None,
        description="Filter by page number (1-based)",
    ),
):
    """
    List per-provider raw extraction outputs for a source document.

    Returns one record per provider per page. Use the provider query param
    to narrow results to a single provider's output.
    """
    try:
        extractions = await RawExtraction.get_by_source(
            source_id,
            provider=provider,
            page_number=page_number,
        )

        items = [
            RawExtractionResponse(
                id=str(e.id or ""),
                source_id=str(e.source_id),
                provider_id=e.provider_id,
                extraction_backend=e.extraction_backend,
                page_number=e.page_number,
                raw_html=e.raw_html,
                raw_markdown=e.raw_markdown,
                structured_json=e.structured_json,
                bbox=e.bbox,
                confidence=e.confidence,
                officer_edits=e.officer_edits,
                created_at=str(e.created_at) if e.created_at else None,
            )
            for e in extractions
        ]

        return RawExtractionListResponse(
            extractions=items,
            total=len(items),
            source_id=source_id,
        )
    except Exception as e:
        logger.error(f"Error listing raw extractions for source {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 5 — Wire `RawExtraction.save()` in `source_commands.py`

**5a. Add import.** At the top of `commands/source_commands.py`, add `RawExtraction` to the
existing import from `open_notebook.domain.acm` (or add a new import if the domain is not yet
imported there):

```python
from open_notebook.domain.acm import RawExtraction
```

**5b. Add `_store_raw_extractions` helper function** after the existing
`_store_docling_tables` function (around line 178):

```python
async def _store_raw_extractions(
    source_id: str,
    extraction_result,  # NormalizedExtractionResult
) -> int:
    """
    Persist per-provider raw extraction outputs to the raw_extraction table.

    Called immediately after provider.extract() succeeds, before
    _store_docling_tables. Returns count of rows stored.
    """
    import json

    stored = 0
    provider_id = extraction_result.provider_id
    backend_label = f"{provider_id}:2.x"

    for table in extraction_result.tables:
        bbox_dict = None
        if table.bbox is not None:
            bbox_dict = {
                "x": table.bbox.x,
                "y": table.bbox.y,
                "width": table.bbox.width,
                "height": table.bbox.height,
                "page": table.bbox.page,
            }

        # Serialise column + row count into structured_json
        structured = json.dumps(
            {
                "columns": table.columns,
                "row_count": table.row_count,
                "col_count": table.col_count,
                "table_index": table.table_index,
            }
        )

        raw = RawExtraction(
            source_id=source_id,
            provider_id=provider_id,
            extraction_backend=backend_label,
            page_number=table.page,
            raw_html=table.html,
            raw_markdown=table.markdown,
            structured_json=structured,
            bbox=bbox_dict,
            confidence=None,  # NormalizedTable has no top-level confidence in E31-S2
            officer_edits=[],
        )
        await raw.save()
        stored += 1

    logger.info(
        f"Stored {stored} raw extractions for source {source_id} "
        f"(provider={provider_id})"
    )
    return stored
```

**5c. Call `_store_raw_extractions` inside the provider extraction block.**

In the `process_source_command` function, locate the block that starts:

```python
provider = get_provider_registry().get_default()
extraction_result = provider.extract(
    pdf_path, pipeline_logger=docling_pl
)
```

After `extraction_result` is assigned and before `docling_tables = [...]`, insert:

```python
# E31-S4: Persist raw per-provider outputs before converting to acm_table_section
await _store_raw_extractions(str(processed_source.id), extraction_result)
```

The full updated block should look like:

```python
provider = get_provider_registry().get_default()
extraction_result = provider.extract(
    pdf_path, pipeline_logger=docling_pl
)
# E31-S4: Persist raw per-provider outputs before converting to acm_table_section
await _store_raw_extractions(str(processed_source.id), extraction_result)
docling_tables = [
    {
        "table_index": t.table_index,
        "page": t.page,
        "rows": t.row_count,
        "columns": t.columns,
        "csv": t.csv,
        "markdown": t.markdown,
        "html": t.html,
    }
    for t in extraction_result.tables
]
```

### Step 6 — Write tests

Create `tests/test_raw_extraction_storage.py` per the Test Plan in Section 6.

---

## 5. Acceptance Criteria Mapping

| AC | Requirement | Satisfied By |
|----|-------------|--------------|
| AC1 | `raw_extraction` table with all listed columns | `migrations/42.surrealql` Step 1 |
| AC2 | Store per-provider raw output after each extraction run | `_store_raw_extractions()` in `source_commands.py`, Step 5 |
| AC3 | Link to `acm_table_section` via consensus merge | `acm_table_section` keeps its existing `source_id` FK; `raw_extraction` also links via `source_id`. The consensus merge (E31-S3) will use both. The schema is ready now. |
| AC4 | `consensus_tier` and `consensus_scores` columns on `acm_table_section` | `migrations/42.surrealql` additive fields + `ACMTableSection` domain model update |
| AC5 | `GET /api/acm/raw-extractions/{source_id}` with provider filtering | Endpoint in `api/routers/acm.py`, Step 4 |
| AC6 | Unit tests for raw extraction storage and retrieval | `tests/test_raw_extraction_storage.py`, Step 6 |

**AC3 note:** The story brief says "Link to acm_table_section via consensus merge." This is a
forward reference to E31-S3. E31-S4 does not implement the merge — it only establishes the
`raw_extraction` rows and the `consensus_tier`/`consensus_scores` columns that E31-S3 will
populate. Both tables share `source_id` as the join key, which is sufficient for E31-S3.

---

## 6. Test Plan

File: `tests/test_raw_extraction_storage.py`

All tests mock SurrealDB via `unittest.mock.patch("open_notebook.domain.acm.repo_query")` and
`unittest.mock.patch("open_notebook.domain.acm.repo_create")` or via the TestClient for API
tests. No live database is required.

### 6.1 Domain Model Tests (`TestRawExtractionModel`)

**test_raw_extraction_validate_source_id_adds_prefix**
- Create `RawExtraction(source_id="abc123", provider_id="docling", extraction_backend="docling:2.x", page_number=1)`
- Assert `source_id == "source:abc123"`

**test_raw_extraction_validate_source_id_accepts_prefixed**
- Create with `source_id="source:abc123"`
- Assert `source_id == "source:abc123"` (no double prefix)

**test_raw_extraction_validate_source_id_required**
- Attempt `RawExtraction(source_id="", ...)` and expect `InvalidInputError` or `ValidationError`

**test_raw_extraction_empty_provider_id_raises**
- Attempt `RawExtraction(source_id="source:abc", provider_id="", ...)` and expect `ValidationError`

**test_raw_extraction_page_number_minus_one_allowed**
- Create with `page_number=-1` (unknown page)
- Assert no exception

**test_raw_extraction_page_number_invalid**
- Attempt `page_number=-2` and expect `ValidationError`

**test_raw_extraction_officer_edits_defaults_to_empty_list**
- Create without `officer_edits` keyword
- Assert `officer_edits == []`

**test_raw_extraction_bbox_is_optional**
- Create without `bbox`
- Assert `bbox is None`

### 6.2 Repository Query Tests (`TestRawExtractionRepository`)

**test_get_by_source_calls_correct_query**

```python
@patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
async def test_get_by_source_calls_correct_query(self, mock_query):
    mock_query.return_value = [
        {
            "id": "raw_extraction:001",
            "source_id": "source:abc",
            "provider_id": "docling",
            "extraction_backend": "docling:2.x",
            "page_number": 1,
            "officer_edits": [],
        }
    ]
    results = await RawExtraction.get_by_source("source:abc")
    assert len(results) == 1
    assert results[0].provider_id == "docling"
    mock_query.assert_called_once()
    call_args = mock_query.call_args[0][0]
    assert "source_id = $source_id" in call_args
```

**test_get_by_source_with_provider_filter**

```python
@patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
async def test_get_by_source_with_provider_filter(self, mock_query):
    mock_query.return_value = []
    await RawExtraction.get_by_source("source:abc", provider="mineru")
    call_args = mock_query.call_args[0][0]
    assert "provider_id = $provider_id" in call_args
    params = mock_query.call_args[0][1]
    assert params["provider_id"] == "mineru"
```

**test_get_by_source_with_page_filter**

```python
@patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
async def test_get_by_source_with_page_filter(self, mock_query):
    mock_query.return_value = []
    await RawExtraction.get_by_source("source:abc", page_number=3)
    call_args = mock_query.call_args[0][0]
    assert "page_number = $page_number" in call_args
```

**test_delete_by_source_returns_count**

```python
@patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
async def test_delete_by_source_returns_count(self, mock_query):
    mock_query.return_value = [{"id": "raw_extraction:1"}, {"id": "raw_extraction:2"}]
    count = await RawExtraction.delete_by_source("source:abc")
    assert count == 2
```

**test_delete_by_source_empty_returns_zero**

```python
@patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
async def test_delete_by_source_empty_returns_zero(self, mock_query):
    mock_query.return_value = None
    count = await RawExtraction.delete_by_source("source:abc")
    assert count == 0
```

### 6.3 API Endpoint Tests (`TestRawExtractionsEndpoint`)

Use the standard `TestClient` fixture (same pattern as `tests/test_acm_api.py`):

```python
@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)
```

**test_list_raw_extractions_success**

```python
@patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
def test_list_raw_extractions_success(self, mock_get, client):
    from open_notebook.domain.acm import RawExtraction
    mock_record = RawExtraction(
        id="raw_extraction:001",
        source_id="source:abc",
        provider_id="docling",
        extraction_backend="docling:2.x",
        page_number=2,
        raw_html="<table></table>",
        raw_markdown="| a |",
        officer_edits=[],
    )
    mock_get.return_value = [mock_record]

    response = client.get("/api/acm/raw-extractions/source:abc")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["source_id"] == "source:abc"
    assert data["extractions"][0]["provider_id"] == "docling"
```

**test_list_raw_extractions_provider_filter_passed_through**

```python
@patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
def test_list_raw_extractions_provider_filter(self, mock_get, client):
    mock_get.return_value = []
    response = client.get("/api/acm/raw-extractions/source:abc?provider=mineru")
    assert response.status_code == 200
    mock_get.assert_called_once_with("source:abc", provider="mineru", page_number=None)
```

**test_list_raw_extractions_empty_source**

```python
@patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
def test_list_raw_extractions_empty(self, mock_get, client):
    mock_get.return_value = []
    response = client.get("/api/acm/raw-extractions/source:xyz")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["extractions"] == []
```

**test_list_raw_extractions_db_error_returns_500**

```python
@patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
def test_list_raw_extractions_db_error(self, mock_get, client):
    mock_get.side_effect = Exception("DB connection failed")
    response = client.get("/api/acm/raw-extractions/source:abc")
    assert response.status_code == 500
```

### 6.4 `ACMTableSection` Consensus Fields Tests (`TestACMTableSectionConsensus`)

**test_acm_table_section_accepts_consensus_tier**

```python
def test_acm_table_section_accepts_consensus_tier():
    section = ACMTableSection(
        source_id="source:abc",
        page_start=1,
        page_end=2,
        consensus_tier="single_provider",
    )
    assert section.consensus_tier == "single_provider"
```

**test_acm_table_section_consensus_fields_default_none**

```python
def test_acm_table_section_consensus_fields_default_none():
    section = ACMTableSection(
        source_id="source:abc",
        page_start=1,
        page_end=2,
    )
    assert section.consensus_tier is None
    assert section.consensus_scores is None
```

### 6.5 Source Commands Wiring Test (`TestStoreRawExtractions`)

**test_store_raw_extractions_saves_one_per_table**

```python
@pytest.mark.asyncio
@patch("commands.source_commands.RawExtraction")
async def test_store_raw_extractions_saves_one_per_table(mock_cls):
    from commands.source_commands import _store_raw_extractions
    from open_notebook.extractors.providers.base import NormalizedExtractionResult, NormalizedTable

    mock_instance = AsyncMock()
    mock_cls.return_value = mock_instance

    result = NormalizedExtractionResult(
        provider_id="docling",
        tables=[
            NormalizedTable(table_index=0, page=1, row_count=5, col_count=3,
                            columns=["A", "B", "C"], html="<table/>", markdown=""),
            NormalizedTable(table_index=1, page=2, row_count=3, col_count=3,
                            columns=["A", "B", "C"], html="<table/>", markdown=""),
        ],
    )

    count = await _store_raw_extractions("source:abc", result)
    assert count == 2
    assert mock_instance.save.call_count == 2
```

---

## 7. Verification Protocol

Before marking the story complete, the implementing agent MUST run:

```bash
cd "D:/ailocal/acm-ai"
uv run ruff check . --fix
uv run ruff format .
uv run pytest tests/test_raw_extraction_storage.py -v
```

All tests must pass (green). Ruff must report zero errors.

Additionally verify file existence:

```
migrations/42.surrealql                              -- must exist
migrations/42_down.surrealql                         -- must exist
open_notebook/domain/acm.py                          -- RawExtraction class present
api/models.py                                        -- RawExtractionResponse present
api/routers/acm.py                                   -- /raw-extractions/{source_id} route present
commands/source_commands.py                          -- _store_raw_extractions() present + called
tests/test_raw_extraction_storage.py                 -- created with >= 14 test functions
```

---

## 8. Out of Scope (Deferred to E31-S3)

- Consensus algorithm implementation
- Populating `consensus_tier` / `consensus_scores` on existing `acm_table_section` rows
- Merging multiple providers' `raw_extraction` rows into a single canonical `acm_table_section`
- Any frontend UI for viewing raw extractions
- The `officer_edits` write endpoint (the field is stored empty; edits will be added in a
  later story when the review UI is built)
