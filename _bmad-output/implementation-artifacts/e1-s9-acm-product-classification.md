# Story 1.9: ACM Product Classification

**Status:** done
**Created:** 2026-02-05
**Implemented:** 2026-02-06
**Epic:** E1 - ACM Data Extraction Pipeline
**Priority:** P0 (Victorian BAR Compliance)

## Story

**As a** system processing ACM data,
**I want** to automatically classify ACM items into Product Group/Type using the official Victorian BAR taxonomy,
**So that** BAR export columns AA-AC (ACM Product Group, ACM GROUP NAME EXCEL, ACM Product Type) are properly populated and the register is BAR-compliant.

## Context

### Problem
Victorian Government BAR (Building Asbestos Register) exports require proper ACM product classification in columns AA-AC. Currently:
- Extracted ACM records have `product` and `material_description` fields but no taxonomy classification
- BAR export cannot populate the required Product Group (AA) and Product Type (AC) columns
- Manual classification of hundreds of records per document is not feasible
- Different friability types (Friable vs Non-friable) require different taxonomy trees

### Solution
Create an ACM Product Classification system that:
1. Uses pattern-based regex matching for common ACM product types (primary method)
2. Falls back to LLM classification for ambiguous items
3. Selects appropriate taxonomy (T1-T8 Non-friable or T1-T6 Friable) based on friability
4. Provides API endpoint for batch classification
5. Supports user override for manual corrections

### Dependencies
- **Depends on:**
  - E1-S3 (Two-Stage Extraction Pipeline) - Classification happens during Stage 2 INTERPRET
  - E1-S2 (Domain Model) - ACMRecord must have `acm_product_group` and `acm_product_type` fields
  - E1-S4 (API Endpoints) - For the classification endpoint
- **Blocks:**
  - E5-S2 (Excel BAR Export) - Cannot properly populate columns AA-AC without classification

## Acceptance Criteria

### AC1: Pattern-Based Classification
- **Given:** An ACM item with `product` and `material_description` fields
- **When:** The classifier processes the item
- **Then:** Common ACM types are matched using regex patterns:
  - `vinyl sheet`, `vinyl tiles`, `linoleum` → T3 Vinyl products
  - `fibre cement`, `flat sheeting`, `weatherboard` → T1 Cement products
  - `mastic`, `gasket`, `caulking` → T4 Gasket products
  - `lagging`, `insulation`, `vermiculite` → T3 Insulation (friable) or T8 Insulation (non-friable)
  - `bitumen`, `malthoid`, `electrical components` → T2 Bitumen products
- **And:** Classification uses the correct taxonomy based on friability value

### AC2: Taxonomy Selection by Friability
- **Given:** An ACM item with `friable` field set
- **When:** Classifying the product
- **Then:**
  - If `friable` == "Friable" → Use T1-T6 Friable taxonomy
  - If `friable` == "Non-friable" or "Non Friable" → Use T1-T8 Non-friable taxonomy
  - If `friable` is null/empty → Default to Non-friable taxonomy

### AC3: LLM Fallback Classification
- **Given:** An ACM item that doesn't match any regex patterns
- **When:** The pattern-based classifier returns no match
- **Then:**
  - System uses LLM with few-shot prompting
  - LLM receives taxonomy context and item description
  - Returns `product_group`, `product_type`, and `confidence` score
  - Confidence below threshold (< 0.7) flags for manual review

### AC4: Database Field Support
- **Given:** ACM records need to store classification data
- **When:** Classification is performed
- **Then:** Results are stored in existing ACMRecord fields:
  - `acm_product_group`: e.g., "T3 Vinyl products"
  - `acm_product_type`: e.g., "Vinyl sheet"

### AC5: User Override Capability
- **Given:** A classified ACM record
- **When:** User wants to correct the classification
- **Then:**
  - PUT `/api/acm/records/{id}` accepts `acm_product_group` and `acm_product_type` updates
  - Override is persisted in database
  - Override flag indicates manual correction (optional)

### AC6: Classification API Endpoint
- **Given:** Frontend or batch process needs classification
- **When:** API call is made
- **Then:**
  - `POST /api/acm/classify` accepts single item or batch
  - Request includes: `item_description`, `friability` (optional)
  - Response includes: `product_group`, `product_type`, `confidence`
  - `POST /api/acm/classify/batch` processes all records for a source

## Tasks / Subtasks

### Phase 1: Create Taxonomy Module

- [x] **Task 1.1: Create taxonomy.py normalizer** (AC: 1, 2)
  - [x] Create `open_notebook/extractors/normalizers/__init__.py` (package init)
  - [x] Create `open_notebook/extractors/normalizers/taxonomy.py`
  - [x] Load taxonomy JSON files: `register_taxonomy.nonfriable.json`, `register_taxonomy.friable.json`
  - [x] Implement `classify_product(item_description: str, friability: str) -> tuple[str, str]`
  - [x] Define regex patterns for common ACM types (per product-taxonomy.md)
  - **Files:** `open_notebook/extractors/normalizers/taxonomy.py`

- [x] **Task 1.2: Implement pattern-based classification** (AC: 1)
  - [x] Define `CLASSIFICATION_PATTERNS` list with regex, friability, group, type tuples
  - [x] Implement pattern matching logic with case-insensitive search
  - [x] Handle partial matches and prioritize more specific patterns
  - [x] Return (product_group, product_type) on match, (None, None) on no match
  - **Files:** `open_notebook/extractors/normalizers/taxonomy.py`

### Phase 2: LLM Fallback Classification

- [x] **Task 2.1: Create LLM classification prompt** (AC: 3)
  - [x] Create `prompts/acm/classification.jinja` template
  - [x] Include few-shot examples for each product group
  - [x] Include taxonomy reference (groups and types)
  - [x] Request structured JSON output with confidence
  - **Files:** `prompts/acm/classification.jinja`

- [x] **Task 2.2: Implement LLM fallback in taxonomy.py** (AC: 3)
  - [x] Create `classify_with_llm(item_description: str, friability: str) -> dict`
  - [x] Use Esperanto for multi-provider LLM abstraction
  - [x] Parse JSON response and extract classification
  - [x] Handle LLM errors gracefully (return low confidence)
  - **Files:** `open_notebook/extractors/normalizers/taxonomy.py`

### Phase 3: API Endpoints

- [x] **Task 3.1: Add classification endpoint** (AC: 6)
  - [x] Add `POST /api/acm/classify` to `api/routers/acm.py`
  - [x] Create `ClassifyRequest` and `ClassifyResponse` models in `api/models.py`
  - [x] Implement single-item classification
  - [x] Return product_group, product_type, confidence
  - **Files:** `api/routers/acm.py`, `api/models.py`

- [x] **Task 3.2: Add batch classification endpoint** (AC: 6)
  - [x] Add `POST /api/acm/classify/batch` endpoint
  - [x] Accept `source_id` parameter
  - [x] Classify all records for source, update database
  - [x] Return summary: total, classified, skipped, errors
  - **Files:** `api/routers/acm.py`

- [x] **Task 3.3: Verify record update endpoint** (AC: 5)
  - [x] Verify `PUT /api/acm/records/{id}` accepts classification fields
  - [x] Add `acm_product_group` and `acm_product_type` to update model if missing
  - **Files:** `api/routers/acm.py`, `api/models.py`

### Phase 4: Database Schema Updates

- [x] **Task 4.1: Add classification fields to migration** (AC: 4)
  - [x] Check existing `acm_record` schema for classification fields
  - [x] If missing, create migration `migrations/14.surrealql` to add:
    - `acm_product_group TYPE option<string>`
    - `acm_product_type TYPE option<string>`
    - `classification_confidence TYPE option<float>`
    - `classification_override TYPE option<bool>`
  - [x] Add indexes for filtering by product group
  - **Files:** `migrations/14.surrealql`

- [x] **Task 4.2: Update ACMRecord domain model** (AC: 4)
  - [x] Add `acm_product_group` field to `open_notebook/domain/acm.py`
  - [x] Add `acm_product_type` field
  - [x] Add optional `classification_confidence` and `classification_override` fields
  - **Files:** `open_notebook/domain/acm.py`

### Phase 5: Integration & Testing

- [x] **Task 5.1: Integrate with extraction pipeline** (AC: 1, 2)
  - [x] Call `classify_product()` during extraction in `acm_extractor.py`
  - [x] Populate classification fields in `ExtractedACMRow.to_acm_record_dict()`
  - [x] Handle classification errors gracefully (don't fail extraction)
  - **Files:** `open_notebook/extractors/acm_extractor.py`

- [x] **Task 5.2: Create unit tests** (AC: 1, 2, 3)
  - [x] Test pattern matching for each product group
  - [x] Test friability-based taxonomy selection
  - [x] Test LLM fallback (mock LLM responses)
  - [x] Test batch classification
  - **Files:** `tests/test_taxonomy.py`

- [x] **Task 5.3: Create API tests** (AC: 5, 6)
  - [x] Test POST `/api/acm/classify` endpoint
  - [x] Test batch classification endpoint
  - [x] Test record update with classification fields
  - **Files:** `tests/test_acm_api.py`

## Dev Notes

### Architecture Patterns to Follow

**Backend:**
- Create new `normalizers` package under `open_notebook/extractors/` (matches existing pattern)
- Use Esperanto for LLM abstraction (see `open_notebook/graphs/` for examples)
- Follow existing endpoint patterns in `api/routers/acm.py`
- Use Jinja2 templates for prompts (see `prompts/` directory)

**Key Implementation Reference:**
- Taxonomy data files: `docs/samplePDF/instructions-sample/register_taxonomy.*.json`
- Product taxonomy reference: `docs/reference/product-taxonomy.md`
- BAR schema reference: `docs/reference/bar-schema.md`

### Taxonomy Structure

**Non-Friable (T1-T8):**
| Code | Product Group |
|------|---------------|
| T1 | Cement products |
| T2 | Bitumen products |
| T3 | Vinyl products |
| T4 | Gasket, friction products and adhesives |
| T5 | Coatings |
| T6 | Reinforced plastics/resins |
| T7 | Other |
| T8 | Insulation |

**Friable (T1-T6):**
| Code | Product Group |
|------|---------------|
| T1 | Cement products (f) |
| T2 | Vinyl products (f) |
| T3 | Insulation products (f) |
| T4 | Gasket products (f) |
| T5 | Textiles (f) |
| T6 | Other (f) |

### Classification Patterns (Example)

```python
CLASSIFICATION_PATTERNS = [
    # Vinyl products - Non-friable T3, Friable T2
    (r"vinyl\s*(sheet|flooring)", "Non-friable", "T3 Vinyl products", "Vinyl sheet"),
    (r"vinyl\s*tile", "Non-friable", "T3 Vinyl products", "Vinyl Tiles"),
    (r"linoleum", "Non-friable", "T3 Vinyl products", "Vinyl sheet"),

    # Cement products - T1 (both)
    (r"(fibre|fiber)\s*cement|fc\s*sheet", "Non-friable", "T1 Cement products", "Flat Sheeting"),
    (r"corrugated.*roof", "Non-friable", "T1 Cement products", "Corrugated Roof Sheeting"),
    (r"weatherboard", "Non-friable", "T1 Cement products", "Weatherboards"),

    # Gasket products - T4
    (r"mastic", "Non-friable", "T4 Gasket, friction products and adhesives", "Mastic"),
    (r"gasket", "Non-friable", "T4 Gasket, friction products and adhesives", "Gasket(s)"),

    # Insulation - T8 (non-friable) or T3 (friable)
    (r"lagging", "Friable", "T3 Insulation products (f)", "Lagging"),
    (r"millboard", "Non-friable", "T8 Insulation", "Millboard"),
    (r"vermiculite", "Friable", "T3 Insulation products (f)", "Vermiculite"),

    # Bitumen products - T2 (non-friable)
    (r"bitumen|bituminous", "Non-friable", "T2 Bitumen products", "Bituminous Membrane"),
    (r"malthoid", "Non-friable", "T2 Bitumen products", "Malthoid"),
]
```

### API Request/Response Models

```python
# api/models.py
class ClassifyRequest(BaseModel):
    item_description: str
    friability: Optional[Literal["Friable", "Non-friable"]] = None

class ClassifyResponse(BaseModel):
    product_group: Optional[str] = None
    product_type: Optional[str] = None
    confidence: float
    method: Literal["pattern", "llm", "none"]

class BatchClassifyRequest(BaseModel):
    source_id: str

class BatchClassifyResponse(BaseModel):
    total: int
    classified: int
    skipped: int
    errors: int
```

### Project Structure Notes

**New Files to Create:**
- `open_notebook/extractors/normalizers/__init__.py`
- `open_notebook/extractors/normalizers/taxonomy.py`
- `prompts/acm_classification.jinja2`
- `tests/test_taxonomy.py`
- `migrations/XX.surrealql` (if schema update needed - check existing migrations)

**Files to Modify:**
- `open_notebook/domain/acm.py` - Add classification fields if missing
- `open_notebook/extractors/acm_extractor.py` - Integrate classification call
- `api/routers/acm.py` - Add classification endpoints
- `api/models.py` - Add request/response models
- `tests/test_acm_api.py` - Add API tests

### Migration Check

Before creating new migration, check existing schema in `migrations/` for `acm_product_group` and `acm_product_type` fields. The ACMRecord domain model already has placeholder comments for these fields but they may need to be added to the database schema.

### Testing Standards

- Use pytest for backend tests
- Mock LLM calls to avoid API costs and ensure deterministic tests
- Test all product groups with at least one pattern each
- Test friability-based taxonomy selection
- Test edge cases: empty strings, unknown materials, ambiguous items

### Previous Story Intelligence (E1-S8)

From E1-S8 (Site Configuration Data Entry), key patterns:
- Use existing `ACMRecord` domain model patterns in `open_notebook/domain/acm.py`
- Follow `ObjectModel` base class for domain entities
- Add endpoints to existing `api/routers/acm.py` (don't create new router)
- Use `repo_query` for database operations
- Use React Query hooks pattern for frontend (if any UI needed)

### Git Intelligence

Recent commits show MinerU table extraction integration (E1-S10):
- MinerU fallback pattern in `acm_extractor.py` - follow similar try/except pattern
- Bounding box tracking added to ACMRecord - classification fields should follow same optional field pattern
- Performance testing approach - classification should be tested with real PDFs

### References

- [PRD Section 5.6](file://_bmad-output/project-planning-artifacts/acm-ai/03-prd.md#56-product-classification) - Product Classification Requirements
- [Architecture Section 5.2](file://_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#52-extraction-pipeline) - Two-Stage Pipeline
- [Product Taxonomy Reference](file://docs/reference/product-taxonomy.md) - Full Taxonomy Definition
- [BAR Schema Reference](file://docs/reference/bar-schema.md) - BAR Column Definitions
- [Epic E1-S9](file://_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md#e1-s9-acm-product-classification) - Story Definition
- [Existing ACM Extractor](file://open_notebook/extractors/acm_extractor.py) - Integration Point
- [ACM Domain Model](file://open_notebook/domain/acm.py) - Field Definitions

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References
- Pattern matching tested: 6 common ACM types verified
- Taxonomy loading verified: 8 non-friable groups, 6 friable groups
- API endpoints verified: imports successful
- ACM extractor tests: 34/34 passed
- Taxonomy unit tests: 65/65 passed (code review fix)
- ACM API tests: 28/28 passed (code review fix)

### Completion Notes List
- Phase 1: Created normalizers package with taxonomy.py
  - 60+ pattern definitions covering all major ACM product types
  - Dual taxonomy support (Non-friable T1-T8, Friable T1-T6)
  - Pattern matching returns 0.9 confidence for matches
- Phase 2: Created LLM fallback with prompts/acm/classification.jinja
  - Uses Esperanto for multi-provider abstraction
  - Few-shot examples for both friable and non-friable
  - JSON structured output with reasoning
- Phase 3: Added API endpoints to api/routers/acm.py
  - POST /api/acm/classify - single item classification
  - POST /api/acm/classify/batch - batch classification for source
  - GET /api/acm/taxonomy - get available taxonomy groups
- Phase 4: Database schema updates
  - Migration 14 adds acm_product_group, acm_product_type, classification_* fields
  - ACMRecord domain model updated with 5 new fields
  - ACMRecordUpdateRequest supports manual override
- Phase 5: Integrated with extraction pipeline
  - to_acm_record_dict() now includes classification
  - extract_acm_records() has classify parameter (default: True)
  - Classification runs synchronously during extraction

### File List

**Created:**
- `open_notebook/extractors/normalizers/__init__.py`
- `open_notebook/extractors/normalizers/taxonomy.py`
- `prompts/acm/classification.jinja`
- `migrations/14.surrealql`
- `migrations/14_down.surrealql`
- `tests/test_taxonomy.py` (65 tests - code review fix)

**Modified:**
- `open_notebook/domain/acm.py` - Added classification fields
- `open_notebook/extractors/acm_extractor.py` - Integrated classification
- `api/routers/acm.py` - Added classification endpoints, fixed response population
- `api/models.py` - Added classification request/response models, added fields to ACMRecordResponse
- `tests/test_acm_api.py` - Added classification API tests (code review fix)
