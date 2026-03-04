# Tech Spec: E30-S2 — Building Record Table + Domain Model

**Story ID:** E30-S2
**Epic:** E30 — V3 Foundation: Schema + Config
**Sprint:** V3-1
**Story Points:** 5
**Risk Level:** HIGH
**Story Type:** both (backend + frontend)
**Status:** Ready for Development
**Dependencies:** E30-S1 (completed)

---

## User Story

As a system architect, I want a dedicated `building_record` table and `BuildingRecord` domain model that captures all 29+ extractable Salesforce `Building__c` fields so that building-level data is normalised into its own entity, enabling per-building CRUD operations, server-generated internal IDs, and a clean FK relationship from `acm_record` — without breaking any existing extraction pipeline or API.

---

## Acceptance Criteria

| ID   | Criterion | Verification Method |
|------|-----------|---------------------|
| AC1  | New `building_record` table in SurrealDB with 29+ extractable SF `Building__c` fields | Migration 40 review + DB introspection after migration runs |
| AC2  | `BuildingRecord(ObjectModel)` Pydantic model in domain layer with SF field aliases (`AliasChoices` pattern) | Unit test: instantiate with both BAR and SF field names |
| AC3  | `internal_id` field for server-generated building IDs (pattern: `BLD#{source_short}_{seq:03d}`) | Unit test: assert pattern matches `BLD#SCHOOLNA_001` format |
| AC4  | FK: `acm_record.building_record_id` added as `option<record<building_record>>` (new field, does NOT change existing `building_id`) | Migration review + unit test: save ACMRecord with `building_record_id=None` succeeds |
| AC5  | CRUD API endpoints: `GET/POST/PUT/DELETE /api/acm/buildings/{source_id}` | Integration test: full CRUD lifecycle |
| AC6  | Building-filtered ACM record queries: `GET /api/acm/records?building_record_id=building_record:xxx` | Integration test: filter returns only matching records |
| AC7  | `source_id` FK on `building_record` links to source table | Unit test: `BuildingRecord.get_by_source()` returns records for a source |
| AC8  | Embedding fields preserved on `BuildingRecord` (`embedding`, `embedding_text`, `embedding_model`, `embedded_at`, `enriched_text`) | Unit test: fields accept values and are included in `_prepare_save_data()` |
| AC9  | Unit tests for `BuildingRecord` CRUD and FK constraints | Test file `tests/test_building_record.py` with full coverage |
| AC10 | Migration includes indexes on `source_id` and `internal_id` | Migration review: `DEFINE INDEX` statements present |

---

## Architecture

### 1. Table Design — `building_record`

A new first-class SurrealDB table. All fields are optional except `internal_id` and `source_id`, matching the SF `Building__c` object schema loaded by E30-S1.

**Core identification fields:**

| Field | DB Type | Description |
|-------|---------|-------------|
| `internal_id` | `string` | Server-generated: `BLD#{source_short}_{seq:03d}` |
| `source_id` | `record<source>` | FK to source table |
| `building_code` | `option<string>` | Original building identifier from PDF (was `building_id` on ACMRecord) |

**Fields moving from ACMRecord to BuildingRecord (conceptual — ACMRecord keeps its flat fields for backwards compatibility):**

| BuildingRecord Field | SF API Name | DB Type |
|---------------------|-------------|---------|
| `building_name` | `Building_Name__c` | `option<string>` |
| `building_year` | `Estimated_Year_Build_New__c` | `option<string>` |
| `building_construction` | `Construction_Type__c` | `option<string>` |
| `building_address` | `Building_Address__c` | `option<string>` |
| `suburb` | `Suburb__c` | `option<string>` |
| `postcode` | `Postcode__c` | `option<string>` |
| `building_type` | `Building_Type__c` | `option<string>` |

**Additional SF `Building__c` fields (bringing total to 29+):**

| BuildingRecord Field | SF API Name | DB Type |
|---------------------|-------------|---------|
| `building_category` | `Building_Category__c` | `option<string>` |
| `building_address_lga` | `Building_Address_LGA__c` | `option<string>` |
| `building_address_region` | `Building_Address_Region__c` | `option<string>` |
| `roof_type` | `Roof_Type__c` | `option<string>` |
| `number_of_levels` | `Number_of_Levels__c` | `option<int>` |
| `est_building_size_m2` | `Est_Building_Size_m2__c` | `option<float>` |
| `estimated_year_build` | `Estimated_Year_Build_New__c` | `option<string>` |
| `frequency_of_use` | `Frequency_of_Use__c` | `option<string>` |
| `daily_duration` | `Daily_Duration__c` | `option<string>` |
| `level_of_activity` | `Level_of_Activity__c` | `option<string>` |
| `public_access` | `Public_Access__c` | `option<string>` |
| `mobile_plant` | `Mobile_Plant__c` | `option<string>` |
| `owned_or_leased` | `Owned_or_Leased__c` | `option<string>` |
| `asbestos_register_available` | `Asbestos_Register_Available__c` | `option<string>` |
| `audit_report_available` | `Audit_Report_Available__c` | `option<string>` |
| `date_of_audit_report` | `Date_of_Audit_Report__c` | `option<string>` |
| `no_identified_acms` | `No_Identified_ACMs__c` | `option<int>` |
| `no_identified_acms_note` | `No_Identified_ACMs_Note__c` | `option<string>` |
| `site_name` | `Site_Name__c` | `option<string>` |
| `school_uid` | `School_UID__c` | `option<string>` |
| `building_unique_id` | `Building_Unique_ID__c` | `option<string>` |
| `external_id` | `External_ID__c` | `option<string>` |
| `building_out_of_scope` | `Building_Out_Of_Scope_New__c` | `option<bool>` |
| `building_out_of_scope_comments` | `Building_Out_Of_Scope_Comments__c` | `option<string>` |
| `demolished_status` | `Demolished_Status__c` | `option<string>` |
| `demolition_date` | `Demolition_Date__c` | `option<string>` |
| `demolition_type` | `Demolition_Type__c` | `option<string>` |
| `demolition_comments` | `Demolition_Comments__c` | `option<string>` |
| `additional_comments` | `Additional_Comments__c` | `option<string>` |
| `within_your_portfolio` | `Within_Your_Portfolio__c` | `option<string>` |
| `psb_district_region` | `PSB_District_Region__c` | `option<string>` |
| `state` | `State__c` | `option<string>` |
| `country` | `Country__c` | `option<string>` |
| `gps_coordinates` | `GPS_Coordinates_provided_by_metro__c` | `option<string>` |
| `capital_works_project_details` | `Capital_Works_Project_Provide_Details__c` | `option<string>` |
| `possible_capital_works_project` | `Possible_Capital_Works_Project__c` | `option<string>` |

**Embedding fields (AC8):**

| Field | DB Type |
|-------|---------|
| `embedding` | `option<array<float>>` |
| `embedding_text` | `option<string>` |
| `embedding_model` | `option<string>` |
| `embedded_at` | `option<datetime>` |
| `enriched_text` | `option<string>` |

### 2. FK Strategy (CRITICAL — Backwards-Compatible)

**What we do in E30-S2:**

1. **ACMRecord keeps `building_id` as a string** — no type change, no rename, no removal. All existing extraction code and tests continue working.
2. **ACMRecord gets a NEW optional field `building_record_id: Optional[str] = None`** that will hold `building_record:xxx` when a building record is linked.
3. **BuildingRecord stores the original building code** in `building_code` field (the raw value that was `building_id` on ACMRecord).
4. **Migration 40** uses `DEFINE FIELD IF NOT EXISTS building_record_id ON TABLE acm_record TYPE option<record<building_record>>` — additive only.

**What E30-S5 (Data Migration) does later:**

- Creates `BuildingRecord` rows from distinct building data already on ACMRecords
- Populates `acm_record.building_record_id` with the FK to the newly created building records
- (Optionally drops flat `building_*` fields from `acm_record`)

**For AC4:** The migration DEFINES `building_record_id` on `acm_record` as `option<record<building_record>>`, but does NOT alter the existing `building_id` field. The API query endpoint (AC6) uses `building_record_id` for filtering.

### 3. ID Generation (AC3)

```python
async def generate_internal_id(source_id: str) -> str:
    """Generate BLD#{source_short}_{seq:03d}.

    source_short = first 8 chars of source name (uppercase, spaces → underscore).
    seq = count of existing BuildingRecords for this source + 1.
    """
    from open_notebook.domain.notebook import Source

    source = await Source.get(source_id)
    source_short = (
        source.name[:8].upper().replace(" ", "_")
        if source.name
        else "UNKNOWN"
    )
    existing = await BuildingRecord.get_by_source(source_id)
    seq = len(existing) + 1
    return f"BLD#{source_short}_{seq:03d}"
```

**Pattern examples:**
- Source "School Name Report.pdf" → `BLD#SCHOOL_N_001`, `BLD#SCHOOL_N_002`
- Source "ps1234.pdf" → `BLD#PS1234.P_001`

### 4. Migration 40.surrealql Design

**Additive only — no destructive changes:**

```sql
-- Migration 40: Create building_record table + FK field on acm_record (E30-S2)
-- Additive only. Does NOT alter existing acm_record.building_id field.

DEFINE TABLE IF NOT EXISTS building_record SCHEMAFULL;

-- Core identification
DEFINE FIELD IF NOT EXISTS internal_id               ON TABLE building_record TYPE string;
DEFINE FIELD IF NOT EXISTS source_id                 ON TABLE building_record TYPE record<source>;
DEFINE FIELD IF NOT EXISTS building_code             ON TABLE building_record TYPE option<string>;

-- Fields from ACMRecord (building-level)
DEFINE FIELD IF NOT EXISTS building_name             ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_year             ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_construction     ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_address          ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS suburb                    ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS postcode                  ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_type             ON TABLE building_record TYPE option<string>;

-- Additional SF Building__c fields
DEFINE FIELD IF NOT EXISTS building_category         ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_address_lga      ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_address_region   ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS roof_type                 ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS number_of_levels          ON TABLE building_record TYPE option<int>;
DEFINE FIELD IF NOT EXISTS est_building_size_m2      ON TABLE building_record TYPE option<float>;
DEFINE FIELD IF NOT EXISTS estimated_year_build      ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS frequency_of_use          ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS daily_duration            ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS level_of_activity         ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS public_access             ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS mobile_plant              ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS owned_or_leased           ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS asbestos_register_available ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS audit_report_available    ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS date_of_audit_report      ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS no_identified_acms        ON TABLE building_record TYPE option<int>;
DEFINE FIELD IF NOT EXISTS no_identified_acms_note   ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS site_name                 ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS school_uid                ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_unique_id        ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS external_id               ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_out_of_scope     ON TABLE building_record TYPE option<bool>;
DEFINE FIELD IF NOT EXISTS building_out_of_scope_comments ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS demolished_status         ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS demolition_date           ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS demolition_type           ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS demolition_comments       ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS additional_comments       ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS within_your_portfolio     ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS psb_district_region       ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS state                     ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS country                   ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gps_coordinates           ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS capital_works_project_details ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS possible_capital_works_project ON TABLE building_record TYPE option<string>;

-- Embedding fields
DEFINE FIELD IF NOT EXISTS embedding                 ON TABLE building_record TYPE option<array<float>>;
DEFINE FIELD IF NOT EXISTS embedding_text            ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS embedding_model           ON TABLE building_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS embedded_at               ON TABLE building_record TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS enriched_text             ON TABLE building_record TYPE option<string>;

-- Timestamps (standard ObjectModel fields)
DEFINE FIELD IF NOT EXISTS created                   ON TABLE building_record TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS updated                   ON TABLE building_record TYPE option<datetime>;

-- Indexes (AC10)
DEFINE INDEX IF NOT EXISTS idx_building_source_id    ON TABLE building_record COLUMNS source_id;
DEFINE INDEX IF NOT EXISTS idx_building_internal_id  ON TABLE building_record COLUMNS internal_id UNIQUE;

-- Add FK field to acm_record (additive, does NOT change existing building_id)
DEFINE FIELD IF NOT EXISTS building_record_id        ON TABLE acm_record TYPE option<record<building_record>>;
DEFINE INDEX IF NOT EXISTS idx_acm_building_record   ON TABLE acm_record COLUMNS building_record_id;
```

### 5. API Design (AC5, AC6)

**Building CRUD endpoints (AC5):**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/acm/buildings?source_id=xxx` | List all building records for a source |
| `GET` | `/api/acm/buildings/{building_id}` | Get a single building record by ID |
| `POST` | `/api/acm/buildings` | Create building record (auto-generates `internal_id`) |
| `PUT` | `/api/acm/buildings/{building_id}` | Update building record |
| `DELETE` | `/api/acm/buildings/{building_id}` | Delete building record |

**Building-filtered ACM queries (AC6):**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/acm/records?source_id=xxx&building_record_id=building_record:xxx` | Filter ACM records by building FK |

### 6. Backwards Compatibility

**What keeps working (no changes):**
- All existing `ACMRecord` creation code (`building_id` remains a string)
- All existing extraction pipeline code (no changes needed)
- All existing tests (`building_id` field unchanged)
- Existing `GET /api/acm/jobs/{source_id}/buildings` endpoint (aggregates from `acm_record`)
- Existing `PUT /api/acm/jobs/{source_id}/buildings/{building_id}` endpoint

**What is new:**
- `BuildingRecord` model and CRUD in `open_notebook/domain/acm.py`
- `building_record_id` FK on `ACMRecord` (optional, `None` for all existing records)
- New API endpoints for building records at `/api/acm/buildings`
- New `building_record_id` query param on existing `/api/acm/records` endpoint

### 7. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| FK type change breaks existing records | HIGH | Don't change `building_id` type. Add new `building_record_id` field instead. E30-S5 handles data migration. |
| 29+ field model becomes unwieldy | MEDIUM | Group fields logically in the Pydantic model with section comments. Use `AliasChoices` for all SF fields. |
| Building deduplication across sources | LOW | `internal_id` is per-source unique (`BLD#source_seq` pattern). Cross-source dedup is E30-S5's concern. |
| ID generation race condition | LOW | Sequential generation within `generate_internal_id()` using count query. Acceptable for V3-1 scope. UNIQUE index on `internal_id` provides final safety net. |
| Existing building review wizard breaks | HIGH | Wizard endpoints (`/api/acm/jobs/{source_id}/buildings`) are NOT modified. New CRUD endpoints are separate at `/api/acm/buildings`. |

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/domain/acm.py` | MODIFY (additive) | Add `BuildingRecord(ObjectModel)` class with all SF fields, `AliasChoices`, validators, `get_by_source()`, `generate_internal_id()`. Add `building_record_id` field to `ACMRecord`. |
| `api/routers/acm.py` | MODIFY (additive) | Add 5 CRUD endpoints for `/api/acm/buildings`. Add `building_record_id` query param to existing `list_acm_records`. Import new models. |
| `api/models.py` | MODIFY (additive) | Add `BuildingRecordCreateRequest`, `BuildingRecordUpdateRequest`, `BuildingRecordResponse`, `BuildingRecordListResponse` Pydantic models. |
| `migrations/40.surrealql` | CREATE | Define `building_record` table with all fields, indexes, and `building_record_id` FK on `acm_record`. |
| `migrations/40_down.surrealql` | CREATE | Rollback: `REMOVE TABLE building_record; REMOVE FIELD building_record_id ON TABLE acm_record;` |
| `tests/test_building_record.py` | CREATE | Unit tests for `BuildingRecord` model, CRUD, ID generation, FK constraints, API endpoints. |

**Files NOT to modify:**
- `open_notebook/domain/base.py` — no changes needed
- `open_notebook/extractors/acm_extractor.py` — extraction pipeline unchanged
- `commands/source_commands.py` — extraction commands unchanged
- `tests/test_acm_api.py` — existing ACM API tests remain unchanged
- `tests/test_acm_schemas.py` — existing schema tests remain unchanged

---

## Database Changes

### Migration 40: `migrations/40.surrealql`

See full SQL in Architecture Section 4 above.

**Key design decisions:**
- `SCHEMAFULL` table — strict schema enforcement (matches `acm_record` pattern)
- `building_year` stored as `option<string>` (not int) to accommodate SF picklist `Estimated_Year_Build_New__c` which has year ranges
- `DEFINE FIELD IF NOT EXISTS` throughout for safe re-run
- Two indexes: `idx_building_source_id` (non-unique, for source filtering) and `idx_building_internal_id` (UNIQUE, for ID generation safety)
- `building_record_id` on `acm_record` typed as `option<record<building_record>>` — SurrealDB enforces referential integrity

### Migration 40 Down: `migrations/40_down.surrealql`

```sql
-- Migration 40 down: Remove building_record table and FK field
-- WARNING: This will delete all building_record data.
REMOVE INDEX IF EXISTS idx_acm_building_record ON TABLE acm_record;
REMOVE FIELD IF EXISTS building_record_id ON TABLE acm_record;
REMOVE TABLE IF EXISTS building_record;
```

### Resulting DB Record Shape (`building_record:xxx`)

```json
{
  "id": "building_record:abc123",
  "internal_id": "BLD#SCHOOL_N_001",
  "source_id": "source:xyz789",
  "building_code": "B01",
  "building_name": "Main Building",
  "building_year": "1985",
  "building_construction": "Brick Veneer",
  "building_address": "123 School St",
  "suburb": "Kew",
  "postcode": "3101",
  "building_type": "School",
  "building_category": "Educational and training facilities",
  "roof_type": "Metal",
  "number_of_levels": 2,
  "est_building_size_m2": 450.0,
  "owned_or_leased": "Owned",
  "site_name": "Kew Primary School",
  "school_uid": "SCH001",
  "building_unique_id": "BLD-KPS-001",
  "embedding": null,
  "embedding_text": null,
  "embedding_model": null,
  "embedded_at": null,
  "enriched_text": null,
  "created": "2026-03-03T10:00:00.000Z",
  "updated": "2026-03-03T10:00:00.000Z"
}
```

---

## Domain Model — `open_notebook/domain/acm.py` (additions)

### BuildingRecord Class

```python
class BuildingRecord(ObjectModel):
    """
    Domain model for Building records.

    Represents a physical building extracted from SAMP documents.
    Maps to the Salesforce Building__c object with AliasChoices
    for dual BAR/SF field name support.

    Linked to ACMRecords via acm_record.building_record_id FK.
    """

    table_name: ClassVar[str] = "building_record"

    model_config = ConfigDict(populate_by_name=True)

    # --- Core identification ---
    internal_id: str = Field(
        ...,
        description="Server-generated ID: BLD#{source_short}_{seq:03d}",
    )
    source_id: str = Field(
        ...,
        description="FK to source document (record<source> in DB)",
    )
    building_code: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_code", "Building_Code__c"),
        description="Original building identifier from PDF (was building_id on ACMRecord)",
    )

    # --- Fields also on ACMRecord (building-level) ---
    building_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_name", "Building_Name__c"),
    )
    building_year: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_year", "Estimated_Year_Build_New__c"),
        description="Year built (SF picklist, stored as string)",
    )
    building_construction: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_construction", "Construction_Type__c"),
    )
    building_address: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_address", "Building_Address__c"),
    )
    suburb: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("suburb", "Suburb__c"),
    )
    postcode: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("postcode", "Postcode__c"),
    )
    building_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_type", "Building_Type__c"),
    )

    # --- Additional SF Building__c fields ---
    building_category: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_category", "Building_Category__c"),
        description="Dependent on Building_Type__c",
    )
    building_address_lga: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_address_lga", "Building_Address_LGA__c"),
    )
    building_address_region: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_address_region", "Building_Address_Region__c"),
    )
    roof_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("roof_type", "Roof_Type__c"),
    )
    number_of_levels: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("number_of_levels", "Number_of_Levels__c"),
    )
    est_building_size_m2: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("est_building_size_m2", "Est_Building_Size_m2__c"),
    )
    estimated_year_build: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("estimated_year_build", "Estimated_Year_Build_New__c"),
    )
    frequency_of_use: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("frequency_of_use", "Frequency_of_Use__c"),
    )
    daily_duration: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("daily_duration", "Daily_Duration__c"),
    )
    level_of_activity: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("level_of_activity", "Level_of_Activity__c"),
    )
    public_access: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_access", "Public_Access__c"),
    )
    mobile_plant: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("mobile_plant", "Mobile_Plant__c"),
    )
    owned_or_leased: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("owned_or_leased", "Owned_or_Leased__c"),
    )
    asbestos_register_available: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("asbestos_register_available", "Asbestos_Register_Available__c"),
    )
    audit_report_available: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("audit_report_available", "Audit_Report_Available__c"),
    )
    date_of_audit_report: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("date_of_audit_report", "Date_of_Audit_Report__c"),
    )
    no_identified_acms: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("no_identified_acms", "No_Identified_ACMs__c"),
    )
    no_identified_acms_note: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("no_identified_acms_note", "No_Identified_ACMs_Note__c"),
    )
    site_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("site_name", "Site_Name__c"),
    )
    school_uid: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("school_uid", "School_UID__c"),
    )
    building_unique_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_unique_id", "Building_Unique_ID__c"),
    )
    external_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("external_id", "External_ID__c"),
    )
    building_out_of_scope: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("building_out_of_scope", "Building_Out_Of_Scope_New__c"),
    )
    building_out_of_scope_comments: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_out_of_scope_comments", "Building_Out_Of_Scope_Comments__c"),
    )
    demolished_status: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("demolished_status", "Demolished_Status__c"),
    )
    demolition_date: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("demolition_date", "Demolition_Date__c"),
    )
    demolition_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("demolition_type", "Demolition_Type__c"),
    )
    demolition_comments: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("demolition_comments", "Demolition_Comments__c"),
    )
    additional_comments: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("additional_comments", "Additional_Comments__c"),
    )
    within_your_portfolio: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("within_your_portfolio", "Within_Your_Portfolio__c"),
    )
    psb_district_region: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("psb_district_region", "PSB_District_Region__c"),
    )
    state: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("state", "State__c"),
    )
    country: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("country", "Country__c"),
    )
    gps_coordinates: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("gps_coordinates", "GPS_Coordinates_provided_by_metro__c"),
    )
    capital_works_project_details: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("capital_works_project_details", "Capital_Works_Project_Provide_Details__c"),
    )
    possible_capital_works_project: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("possible_capital_works_project", "Possible_Capital_Works_Project__c"),
    )

    # --- Embedding fields (AC8) ---
    embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding for semantic search"
    )
    embedding_text: Optional[str] = Field(
        default=None, description="Combined text used to generate the embedding"
    )
    embedding_model: Optional[str] = Field(
        default=None, description="Model ID used to generate the embedding"
    )
    embedded_at: Optional[datetime] = Field(
        default=None, description="Timestamp when embedding was generated"
    )
    enriched_text: Optional[str] = Field(
        default=None, description="Contextually enriched text for embedding"
    )

    # --- Validators ---
    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, v):
        if not v:
            raise InvalidInputError("source_id is required")
        if isinstance(v, str) and not v.startswith("source:"):
            return f"source:{v}"
        return str(v)

    @field_validator("internal_id")
    @classmethod
    def validate_internal_id(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("internal_id cannot be empty")
        if not v.startswith("BLD#"):
            raise InvalidInputError(f"internal_id must start with 'BLD#', got '{v}'")
        return v.strip()

    # --- Class methods ---
    @classmethod
    async def get_by_source(cls, source_id: str) -> List["BuildingRecord"]:
        """Get all building records for a specific source document."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "SELECT * FROM building_record WHERE source_id = $source_id ORDER BY internal_id",
                {"source_id": ensure_record_id(source_id)},
            )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching building records for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_internal_id(cls, internal_id: str) -> Optional["BuildingRecord"]:
        """Get a building record by its internal_id."""
        if not internal_id:
            raise InvalidInputError("internal_id is required")
        try:
            result = await repo_query(
                "SELECT * FROM building_record WHERE internal_id = $internal_id LIMIT 1",
                {"internal_id": internal_id},
            )
            return cls(**result[0]) if result else None
        except Exception as e:
            logger.error(f"Error fetching building record by internal_id {internal_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_source(cls, source_id: str) -> int:
        """Delete all building records for a source. Returns count of deleted records."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "DELETE building_record WHERE source_id = $source_id RETURN BEFORE",
                {"source_id": ensure_record_id(source_id)},
            )
            return len(result) if result else 0
        except Exception as e:
            logger.error(f"Error deleting building records for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def generate_internal_id(cls, source_id: str) -> str:
        """Generate BLD#{source_short}_{seq:03d} for a new building."""
        from open_notebook.domain.notebook import Source

        source = await Source.get(source_id)
        source_short = (
            source.name[:8].upper().replace(" ", "_")
            if source.name
            else "UNKNOWN"
        )
        existing = await cls.get_by_source(source_id)
        seq = len(existing) + 1
        return f"BLD#{source_short}_{seq:03d}"

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id is proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        return data
```

### ACMRecord Addition (building_record_id field)

Add this field to the existing `ACMRecord` class, after the `building_type` field block:

```python
    # FK to building_record table (E30-S2, optional until E30-S5 data migration)
    building_record_id: Optional[str] = Field(
        default=None,
        description="FK to building_record table (record<building_record> in DB). "
                    "Populated by E30-S5 data migration.",
    )
```

Also update `ACMRecord._prepare_save_data()` to handle the new FK:

```python
    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id, parent_table_id, and building_record_id are proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        if data.get("parent_table_id"):
            data["parent_table_id"] = ensure_record_id(data["parent_table_id"])
        if data.get("building_record_id"):
            data["building_record_id"] = ensure_record_id(data["building_record_id"])
        return data
```

---

## API Changes

### New Endpoints — Building Record CRUD (AC5)

All new endpoints are added to `api/routers/acm.py` alongside existing endpoints.

#### `GET /api/acm/buildings`

List building records for a source.

**Request Parameters:**
- `source_id` (query, required) — Source ID to filter by

**Response: 200 OK**
```json
{
  "buildings": [
    {
      "id": "building_record:abc123",
      "internal_id": "BLD#SCHOOL_N_001",
      "source_id": "source:xyz789",
      "building_code": "B01",
      "building_name": "Main Building",
      "building_type": "School",
      "building_address": "123 School St",
      "suburb": "Kew",
      "postcode": "3101",
      "record_count": 15,
      "created": "2026-03-03T10:00:00.000Z",
      "updated": "2026-03-03T10:00:00.000Z"
    }
  ],
  "total": 1
}
```

#### `GET /api/acm/buildings/{building_id}`

Get a single building record.

**Path Parameters:**
- `building_id` — Building record ID (e.g., `building_record:abc123`)

**Response: 200 OK** — Full `BuildingRecordResponse` object.

**Response: 404 Not Found** — `{"detail": "Building record not found"}`

#### `POST /api/acm/buildings`

Create a new building record. `internal_id` is auto-generated.

**Request Body:**
```json
{
  "source_id": "source:xyz789",
  "building_code": "B01",
  "building_name": "Main Building",
  "building_type": "School"
}
```

**Response: 201 Created** — Full `BuildingRecordResponse` with generated `internal_id`.

#### `PUT /api/acm/buildings/{building_id}`

Update an existing building record.

**Request Body:** Any subset of `BuildingRecordUpdateRequest` fields (all optional).

**Response: 200 OK** — Updated `BuildingRecordResponse`.

#### `DELETE /api/acm/buildings/{building_id}`

Delete a building record.

**Response: 200 OK** — `{"deleted": true, "id": "building_record:abc123"}`

**Response: 404 Not Found** — `{"detail": "Building record not found"}`

### Modified Endpoint — ACM Record List (AC6)

#### `GET /api/acm/records` (existing, modified)

Add new optional query parameter:

- `building_record_id` (query, optional) — Filter by building record FK (e.g., `building_record:abc123`)

When provided, adds `AND building_record_id = $building_record_id` to the query WHERE clause.

### Preserved Existing Endpoints (no changes)

| Endpoint | Status |
|----------|--------|
| `GET /api/acm/jobs/{source_id}/buildings` | Unchanged — existing building review wizard |
| `PUT /api/acm/jobs/{source_id}/buildings/{building_id}` | Unchanged — existing building update |
| `GET /api/acm/records` (without `building_record_id` param) | Unchanged — backwards compatible |
| All other ACM endpoints | Unchanged |

---

## API Models — `api/models.py` (additions)

```python
# =============================================================================
# Building Record Models (E30-S2 — V3 Foundation)
# =============================================================================

class BuildingRecordCreateRequest(BaseModel):
    """Request to create a new BuildingRecord. internal_id is auto-generated."""

    source_id: str = Field(..., description="FK to source document")
    building_code: Optional[str] = Field(None, description="Original building code from PDF")
    building_name: Optional[str] = None
    building_year: Optional[str] = None
    building_construction: Optional[str] = None
    building_address: Optional[str] = None
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    building_type: Optional[str] = None
    building_category: Optional[str] = None
    building_address_lga: Optional[str] = None
    building_address_region: Optional[str] = None
    roof_type: Optional[str] = None
    number_of_levels: Optional[int] = None
    est_building_size_m2: Optional[float] = None
    estimated_year_build: Optional[str] = None
    frequency_of_use: Optional[str] = None
    daily_duration: Optional[str] = None
    level_of_activity: Optional[str] = None
    public_access: Optional[str] = None
    mobile_plant: Optional[str] = None
    owned_or_leased: Optional[str] = None
    asbestos_register_available: Optional[str] = None
    audit_report_available: Optional[str] = None
    date_of_audit_report: Optional[str] = None
    no_identified_acms: Optional[int] = None
    no_identified_acms_note: Optional[str] = None
    site_name: Optional[str] = None
    school_uid: Optional[str] = None
    building_unique_id: Optional[str] = None
    external_id: Optional[str] = None
    building_out_of_scope: Optional[bool] = None
    building_out_of_scope_comments: Optional[str] = None
    demolished_status: Optional[str] = None
    demolition_date: Optional[str] = None
    demolition_type: Optional[str] = None
    demolition_comments: Optional[str] = None
    additional_comments: Optional[str] = None
    within_your_portfolio: Optional[str] = None
    psb_district_region: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    gps_coordinates: Optional[str] = None
    capital_works_project_details: Optional[str] = None
    possible_capital_works_project: Optional[str] = None


class BuildingRecordUpdateRequest(BaseModel):
    """Request to update a BuildingRecord. All fields optional."""

    building_code: Optional[str] = None
    building_name: Optional[str] = None
    building_year: Optional[str] = None
    building_construction: Optional[str] = None
    building_address: Optional[str] = None
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    building_type: Optional[str] = None
    building_category: Optional[str] = None
    building_address_lga: Optional[str] = None
    building_address_region: Optional[str] = None
    roof_type: Optional[str] = None
    number_of_levels: Optional[int] = None
    est_building_size_m2: Optional[float] = None
    estimated_year_build: Optional[str] = None
    frequency_of_use: Optional[str] = None
    daily_duration: Optional[str] = None
    level_of_activity: Optional[str] = None
    public_access: Optional[str] = None
    mobile_plant: Optional[str] = None
    owned_or_leased: Optional[str] = None
    asbestos_register_available: Optional[str] = None
    audit_report_available: Optional[str] = None
    date_of_audit_report: Optional[str] = None
    no_identified_acms: Optional[int] = None
    no_identified_acms_note: Optional[str] = None
    site_name: Optional[str] = None
    school_uid: Optional[str] = None
    building_unique_id: Optional[str] = None
    external_id: Optional[str] = None
    building_out_of_scope: Optional[bool] = None
    building_out_of_scope_comments: Optional[str] = None
    demolished_status: Optional[str] = None
    demolition_date: Optional[str] = None
    demolition_type: Optional[str] = None
    demolition_comments: Optional[str] = None
    additional_comments: Optional[str] = None
    within_your_portfolio: Optional[str] = None
    psb_district_region: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    gps_coordinates: Optional[str] = None
    capital_works_project_details: Optional[str] = None
    possible_capital_works_project: Optional[str] = None


class BuildingRecordResponse(BaseModel):
    """Single building record in API responses."""

    id: str
    internal_id: str
    source_id: str
    building_code: Optional[str] = None
    building_name: Optional[str] = None
    building_year: Optional[str] = None
    building_construction: Optional[str] = None
    building_address: Optional[str] = None
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    building_type: Optional[str] = None
    building_category: Optional[str] = None
    building_address_lga: Optional[str] = None
    building_address_region: Optional[str] = None
    roof_type: Optional[str] = None
    number_of_levels: Optional[int] = None
    est_building_size_m2: Optional[float] = None
    estimated_year_build: Optional[str] = None
    frequency_of_use: Optional[str] = None
    daily_duration: Optional[str] = None
    level_of_activity: Optional[str] = None
    public_access: Optional[str] = None
    mobile_plant: Optional[str] = None
    owned_or_leased: Optional[str] = None
    asbestos_register_available: Optional[str] = None
    audit_report_available: Optional[str] = None
    date_of_audit_report: Optional[str] = None
    no_identified_acms: Optional[int] = None
    no_identified_acms_note: Optional[str] = None
    site_name: Optional[str] = None
    school_uid: Optional[str] = None
    building_unique_id: Optional[str] = None
    external_id: Optional[str] = None
    building_out_of_scope: Optional[bool] = None
    building_out_of_scope_comments: Optional[str] = None
    demolished_status: Optional[str] = None
    demolition_date: Optional[str] = None
    demolition_type: Optional[str] = None
    demolition_comments: Optional[str] = None
    additional_comments: Optional[str] = None
    within_your_portfolio: Optional[str] = None
    psb_district_region: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    gps_coordinates: Optional[str] = None
    capital_works_project_details: Optional[str] = None
    possible_capital_works_project: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class BuildingRecordListResponse(BaseModel):
    """Response for building record list endpoint."""

    buildings: List[BuildingRecordResponse]
    total: int
```

---

## API Endpoint Implementation — `api/routers/acm.py` (additions)

```python
from open_notebook.domain.acm import ACMRecord, ACMTableSection, BuildingRecord
from api.models import (
    # ... existing imports ...
    BuildingRecordCreateRequest,
    BuildingRecordUpdateRequest,
    BuildingRecordResponse,
    BuildingRecordListResponse,
)


# --- Building Record CRUD (E30-S2) ---

@router.get("/buildings", response_model=BuildingRecordListResponse)
async def list_building_records(
    source_id: str = Query(..., description="Source ID to filter by (required)"),
):
    """List all building records for a source."""
    try:
        buildings = await BuildingRecord.get_by_source(source_id)
        return BuildingRecordListResponse(
            buildings=[
                BuildingRecordResponse(**b.model_dump())
                for b in buildings
            ],
            total=len(buildings),
        )
    except Exception as e:
        logger.error(f"Error listing building records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buildings/{building_id:path}", response_model=BuildingRecordResponse)
async def get_building_record(building_id: str):
    """Get a single building record by ID."""
    try:
        building = await BuildingRecord.get(building_id)
        return BuildingRecordResponse(**building.model_dump())
    except Exception as e:
        logger.error(f"Error getting building record {building_id}: {e}")
        raise HTTPException(status_code=404, detail="Building record not found")


@router.post("/buildings", response_model=BuildingRecordResponse, status_code=201)
async def create_building_record(request: BuildingRecordCreateRequest):
    """Create a new building record. internal_id is auto-generated."""
    try:
        internal_id = await BuildingRecord.generate_internal_id(request.source_id)
        data = request.model_dump(exclude_none=True)
        data["internal_id"] = internal_id
        building = BuildingRecord(**data)
        await building.save()
        return BuildingRecordResponse(**building.model_dump())
    except Exception as e:
        logger.error(f"Error creating building record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/buildings/{building_id:path}", response_model=BuildingRecordResponse)
async def update_building_record(building_id: str, request: BuildingRecordUpdateRequest):
    """Update an existing building record."""
    try:
        building = await BuildingRecord.get(building_id)
        update_data = request.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(building, key, value)
        await building.save()
        return BuildingRecordResponse(**building.model_dump())
    except Exception as e:
        logger.error(f"Error updating building record {building_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/buildings/{building_id:path}")
async def delete_building_record(building_id: str):
    """Delete a building record."""
    try:
        building = await BuildingRecord.get(building_id)
        await building.delete()
        return {"deleted": True, "id": building_id}
    except Exception as e:
        logger.error(f"Error deleting building record {building_id}: {e}")
        raise HTTPException(status_code=404, detail="Building record not found")
```

### Modification to Existing `list_acm_records` (AC6)

Add `building_record_id` parameter to the existing endpoint:

```python
@router.get("/records", response_model=ACMRecordListResponse)
async def list_acm_records(
    source_id: str = Query(..., description="Source ID to filter by (required)"),
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    building_record_id: Optional[str] = Query(
        None, description="Filter by building_record FK (e.g., building_record:xxx)"
    ),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    risk_status: Optional[str] = Query(
        None, description="Filter by risk status (Low/Medium/High)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Records per page"),
):
    # ... existing code ...
    # Add after the building_id condition block:
    if building_record_id:
        conditions.append("building_record_id = $building_record_id")
        params["building_record_id"] = ensure_record_id(building_record_id)
    # ... rest of existing code unchanged ...
```

---

## Frontend Changes

None for the domain model and API layer. Future stories (E30-S4+) will add building record UI components. The existing Building Review Wizard (`/api/acm/jobs/{source_id}/buildings`) is unchanged and continues to work against `acm_record` aggregation.

---

## Test Plan

### Unit Tests — `tests/test_building_record.py`

#### TestBuildingRecordModel (covers AC2, AC3, AC8)

```python
class TestBuildingRecordModel:

    def test_create_with_bar_field_names(self):
        """AC2: BuildingRecord accepts BAR field names."""
        record = BuildingRecord(
            internal_id="BLD#TESTSCHL_001",
            source_id="source:abc123",
            building_code="B01",
            building_name="Main Building",
            building_type="School",
        )
        assert record.building_name == "Main Building"
        assert record.building_type == "School"

    def test_create_with_sf_field_names(self):
        """AC2: BuildingRecord accepts SF API names via AliasChoices."""
        record = BuildingRecord(
            internal_id="BLD#TESTSCHL_001",
            source_id="source:abc123",
            Building_Name__c="Main Building",
            Building_Type__c="School",
            Building_Code__c="B01",
        )
        assert record.building_name == "Main Building"
        assert record.building_type == "School"
        assert record.building_code == "B01"

    def test_internal_id_validation_pattern(self):
        """AC3: internal_id must start with 'BLD#'."""
        import pytest
        with pytest.raises(Exception):
            BuildingRecord(
                internal_id="INVALID_001",
                source_id="source:abc123",
            )

    def test_internal_id_valid_pattern(self):
        """AC3: Valid internal_id pattern accepted."""
        record = BuildingRecord(
            internal_id="BLD#SCHOOL_N_001",
            source_id="source:abc123",
        )
        assert record.internal_id == "BLD#SCHOOL_N_001"

    def test_source_id_auto_prefix(self):
        """AC7: source_id without prefix gets 'source:' prepended."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="abc123",
        )
        assert record.source_id == "source:abc123"

    def test_embedding_fields_present(self):
        """AC8: Embedding fields exist and accept values."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
            embedding=[0.1, 0.2, 0.3],
            embedding_text="Main Building School",
            embedding_model="text-embedding-3-small",
            enriched_text="Building: Main Building | Type: School",
        )
        assert record.embedding == [0.1, 0.2, 0.3]
        assert record.embedding_text == "Main Building School"
        assert record.embedding_model == "text-embedding-3-small"
        assert record.enriched_text is not None

    def test_all_sf_fields_present(self):
        """AC1: BuildingRecord has 29+ SF Building__c fields."""
        sf_fields = [
            "building_code", "building_name", "building_year",
            "building_construction", "building_address", "suburb",
            "postcode", "building_type", "building_category",
            "building_address_lga", "building_address_region",
            "roof_type", "number_of_levels", "est_building_size_m2",
            "estimated_year_build", "frequency_of_use", "daily_duration",
            "level_of_activity", "public_access", "mobile_plant",
            "owned_or_leased", "asbestos_register_available",
            "audit_report_available", "date_of_audit_report",
            "no_identified_acms", "no_identified_acms_note",
            "site_name", "school_uid", "building_unique_id",
            "external_id", "building_out_of_scope",
            "building_out_of_scope_comments", "demolished_status",
            "demolition_date", "demolition_type", "demolition_comments",
            "additional_comments", "within_your_portfolio",
            "psb_district_region", "state", "country",
            "gps_coordinates", "capital_works_project_details",
            "possible_capital_works_project",
        ]
        model_fields = set(BuildingRecord.model_fields.keys())
        for field in sf_fields:
            assert field in model_fields, f"Missing SF field: {field}"
        assert len(sf_fields) >= 29

    def test_table_name(self):
        """BuildingRecord.table_name is 'building_record'."""
        assert BuildingRecord.table_name == "building_record"
```

#### TestBuildingRecordIDGeneration (covers AC3)

```python
@pytest.mark.asyncio
class TestBuildingRecordIDGeneration:

    async def test_generate_internal_id_format(self, mock_source):
        """AC3: Generated ID matches BLD#{source_short}_{seq:03d} pattern."""
        # mock_source.name = "School Name Report.pdf"
        internal_id = await BuildingRecord.generate_internal_id("source:test")
        assert internal_id.startswith("BLD#")
        assert "_" in internal_id
        # seq part should be 3 digits
        seq_part = internal_id.split("_")[-1]
        assert len(seq_part) == 3
        assert seq_part.isdigit()

    async def test_generate_internal_id_sequential(self, mock_source, mock_db):
        """AC3: Sequential IDs increment correctly."""
        id1 = await BuildingRecord.generate_internal_id("source:test")
        assert id1.endswith("_001")
        # After creating one record, next should be _002
        # (requires mock_db to return 1 existing record)

    async def test_generate_internal_id_source_short_truncation(self, mock_source):
        """AC3: Source name truncated to 8 chars."""
        # Source with long name should be truncated
        internal_id = await BuildingRecord.generate_internal_id("source:test")
        # BLD# + 8 chars max + _ + 3 digits
        prefix = internal_id[4:].split("_")[0]  # Strip BLD# and get source_short part
        assert len(prefix) <= 8
```

#### TestACMRecordBuildingFK (covers AC4)

```python
class TestACMRecordBuildingFK:

    def test_building_record_id_default_none(self):
        """AC4: building_record_id defaults to None."""
        record = ACMRecord(
            source_id="source:abc",
            building_id="B01",
            product="Roof Sheeting",
            material_description="Corrugated cement",
            result="Detected",
        )
        assert record.building_record_id is None

    def test_building_record_id_accepts_value(self):
        """AC4: building_record_id accepts building_record:xxx format."""
        record = ACMRecord(
            source_id="source:abc",
            building_id="B01",
            product="Roof Sheeting",
            material_description="Corrugated cement",
            result="Detected",
            building_record_id="building_record:xyz",
        )
        assert record.building_record_id == "building_record:xyz"

    def test_prepare_save_data_includes_building_record_id(self):
        """AC4: _prepare_save_data converts building_record_id to record format."""
        record = ACMRecord(
            source_id="source:abc",
            building_id="B01",
            product="Roof Sheeting",
            material_description="Corrugated cement",
            result="Detected",
            building_record_id="building_record:xyz",
        )
        data = record._prepare_save_data()
        assert "building_record_id" in data
```

#### TestBuildingRecordCRUD (covers AC5, AC9)

```python
@pytest.mark.asyncio
class TestBuildingRecordCRUD:

    async def test_save_and_get(self, db_session):
        """AC9: Save and retrieve a BuildingRecord."""
        building = BuildingRecord(
            internal_id="BLD#TESTSCHL_001",
            source_id="source:test_src",
            building_code="B01",
            building_name="Test Building",
        )
        await building.save()
        assert building.id is not None

        fetched = await BuildingRecord.get(building.id)
        assert fetched.internal_id == "BLD#TESTSCHL_001"
        assert fetched.building_name == "Test Building"

    async def test_get_by_source(self, db_session, building_records):
        """AC7: get_by_source returns all buildings for a source."""
        buildings = await BuildingRecord.get_by_source("source:test_src")
        assert len(buildings) > 0
        assert all(b.source_id == "source:test_src" for b in buildings)

    async def test_get_by_internal_id(self, db_session, building_records):
        """AC3: get_by_internal_id returns matching record."""
        building = await BuildingRecord.get_by_internal_id("BLD#TESTSCHL_001")
        assert building is not None
        assert building.internal_id == "BLD#TESTSCHL_001"

    async def test_update(self, db_session, building_records):
        """AC9: Update building record fields."""
        building = await BuildingRecord.get_by_internal_id("BLD#TESTSCHL_001")
        building.building_name = "Updated Name"
        await building.save()

        fetched = await BuildingRecord.get(building.id)
        assert fetched.building_name == "Updated Name"

    async def test_delete(self, db_session, building_records):
        """AC9: Delete a building record."""
        building = await BuildingRecord.get_by_internal_id("BLD#TESTSCHL_001")
        result = await building.delete()
        assert result is True

    async def test_delete_by_source(self, db_session, building_records):
        """AC9: Delete all building records for a source."""
        count = await BuildingRecord.delete_by_source("source:test_src")
        assert count > 0
        remaining = await BuildingRecord.get_by_source("source:test_src")
        assert len(remaining) == 0

    async def test_unique_internal_id_constraint(self, db_session):
        """AC10: Duplicate internal_id is rejected by UNIQUE index."""
        b1 = BuildingRecord(
            internal_id="BLD#DUPETEST_001",
            source_id="source:test_src",
        )
        await b1.save()

        b2 = BuildingRecord(
            internal_id="BLD#DUPETEST_001",
            source_id="source:test_src",
        )
        import pytest
        with pytest.raises(Exception):
            await b2.save()
```

#### TestBuildingRecordAPI (covers AC5, AC6)

```python
@pytest.mark.asyncio
class TestBuildingRecordAPI:

    async def test_list_buildings(self, async_client, building_records):
        """AC5: GET /api/acm/buildings returns building list."""
        response = await async_client.get(
            "/api/acm/buildings", params={"source_id": "source:test_src"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "buildings" in data
        assert "total" in data
        assert data["total"] > 0

    async def test_create_building(self, async_client):
        """AC5: POST /api/acm/buildings creates a building with auto-generated ID."""
        response = await async_client.post(
            "/api/acm/buildings",
            json={
                "source_id": "source:test_src",
                "building_code": "B99",
                "building_name": "New Building",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["internal_id"].startswith("BLD#")
        assert data["building_name"] == "New Building"

    async def test_get_building(self, async_client, building_records):
        """AC5: GET /api/acm/buildings/{id} returns single building."""
        building_id = building_records[0].id
        response = await async_client.get(f"/api/acm/buildings/{building_id}")
        assert response.status_code == 200

    async def test_update_building(self, async_client, building_records):
        """AC5: PUT /api/acm/buildings/{id} updates building."""
        building_id = building_records[0].id
        response = await async_client.put(
            f"/api/acm/buildings/{building_id}",
            json={"building_name": "Updated via API"},
        )
        assert response.status_code == 200
        assert response.json()["building_name"] == "Updated via API"

    async def test_delete_building(self, async_client, building_records):
        """AC5: DELETE /api/acm/buildings/{id} deletes building."""
        building_id = building_records[0].id
        response = await async_client.delete(f"/api/acm/buildings/{building_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

    async def test_filter_acm_records_by_building_record_id(self, async_client, linked_records):
        """AC6: GET /api/acm/records?building_record_id=xxx filters correctly."""
        response = await async_client.get(
            "/api/acm/records",
            params={
                "source_id": "source:test_src",
                "building_record_id": "building_record:test_bld",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # All returned records should have the matching building_record_id
        for record in data["records"]:
            assert record.get("building_record_id") in [
                "building_record:test_bld", None
            ]

    async def test_get_building_not_found(self, async_client):
        """AC5: GET /api/acm/buildings/{invalid} returns 404."""
        response = await async_client.get("/api/acm/buildings/building_record:nonexistent")
        assert response.status_code == 404
```

### Regression Tests

```python
class TestRegressionExistingEndpoints:

    async def test_existing_building_review_wizard_unaffected(self, async_client):
        """Regression: /api/acm/jobs/{source_id}/buildings still works."""
        response = await async_client.get(
            "/api/acm/jobs/source:test_src/buildings"
        )
        # Should return 200 (even if empty)
        assert response.status_code == 200

    async def test_acm_record_without_building_record_id(self, async_client):
        """Regression: ACMRecord creation still works without building_record_id."""
        # Existing extraction pipeline does not set building_record_id
        record = ACMRecord(
            source_id="source:abc",
            building_id="B01",
            product="Roof Sheeting",
            material_description="Corrugated cement",
            result="Detected",
        )
        assert record.building_record_id is None
        # Save should succeed
```

### Test Coverage Matrix

| AC   | Test Class | Test Method(s) |
|------|-----------|----------------|
| AC1  | TestBuildingRecordModel | `test_all_sf_fields_present` |
| AC2  | TestBuildingRecordModel | `test_create_with_bar_field_names`, `test_create_with_sf_field_names` |
| AC3  | TestBuildingRecordModel, TestBuildingRecordIDGeneration | `test_internal_id_valid_pattern`, `test_generate_internal_id_format`, `test_generate_internal_id_sequential` |
| AC4  | TestACMRecordBuildingFK | `test_building_record_id_default_none`, `test_building_record_id_accepts_value`, `test_prepare_save_data_includes_building_record_id` |
| AC5  | TestBuildingRecordAPI | `test_list_buildings`, `test_create_building`, `test_get_building`, `test_update_building`, `test_delete_building`, `test_get_building_not_found` |
| AC6  | TestBuildingRecordAPI | `test_filter_acm_records_by_building_record_id` |
| AC7  | TestBuildingRecordCRUD | `test_get_by_source` |
| AC8  | TestBuildingRecordModel | `test_embedding_fields_present` |
| AC9  | TestBuildingRecordCRUD | `test_save_and_get`, `test_update`, `test_delete`, `test_delete_by_source`, `test_unique_internal_id_constraint` |
| AC10 | Migration 40 review | `DEFINE INDEX` statements present for `source_id` and `internal_id` |

---

## Dependencies and Downstream Impact

### Dependencies (upstream)

| Dependency | Status | Notes |
|-----------|--------|-------|
| E30-S1: SF Schema Config Loader | Completed | Provides SF field definitions; `BuildingRecord` fields align with `Building__c` schema from `SFSchemaBundle` |

### Downstream Impact

| Story | Impact |
|-------|--------|
| E30-S3: ACM Record SF Item__c Alignment | None — E30-S3 is already completed and only touched `acm_record` Item fields |
| E30-S4: Room Record Table + Domain Model | Will follow same pattern as this story for `room_record` table |
| E30-S5: Data Migration | Will create `BuildingRecord` rows from existing `acm_record` building data and populate `building_record_id` FK |
| E30-S6+: V3 Extraction Agents | Will write to `BuildingRecord` directly during extraction |

---

## Implementation Notes for Dev Agent

### Critical Ordering Rules

1. **Create migration 40 first** — `BuildingRecord` model cannot be tested without the DB table.
2. **Implement `BuildingRecord` model second** — API endpoints depend on it.
3. **Add `building_record_id` to `ACMRecord` third** — small additive change, test with existing ACMRecord tests.
4. **Implement API endpoints last** — they compose the model layer.

### Implementation Checklist (step-by-step)

1. Create `migrations/40.surrealql` and `migrations/40_down.surrealql` exactly as specified.
2. Add `BuildingRecord` class to `open_notebook/domain/acm.py` — place it AFTER the `ACMTableSection` class at the bottom of the file.
3. Add `building_record_id` field to `ACMRecord` class (after the `building_type` field block, before `room_id`).
4. Update `ACMRecord._prepare_save_data()` to handle `building_record_id` via `ensure_record_id`.
5. Add API models to `api/models.py` — `BuildingRecordCreateRequest`, `BuildingRecordUpdateRequest`, `BuildingRecordResponse`, `BuildingRecordListResponse`.
6. Add CRUD endpoints to `api/routers/acm.py` — 5 new endpoints under `/buildings`.
7. Add `building_record_id` query param to existing `list_acm_records` endpoint.
8. Update imports in `api/routers/acm.py` to include `BuildingRecord` and new model classes.
9. Create `tests/test_building_record.py` with all test classes.
10. Run full test suite to verify no regressions.

### Pitfalls to Avoid

1. **Do NOT change `building_id` type on ACMRecord** — it stays as a string. The new FK field is `building_record_id`.
2. **Do NOT modify the existing `/api/acm/jobs/{source_id}/buildings` endpoint** — it aggregates from `acm_record` and is used by the Building Review Wizard.
3. **Do NOT import `BuildingRecord` in extraction pipeline code** — extraction still writes flat fields to `ACMRecord`. Building record creation is a separate concern.
4. **Path parameter for building IDs** must use `:path` converter — SurrealDB IDs contain colons (e.g., `building_record:abc123`).
5. **`building_year` is `str` not `int`** on BuildingRecord — it maps to the SF `Estimated_Year_Build_New__c` picklist which contains year ranges, not bare integers. This differs from `ACMRecord.building_year` which is `Optional[int]`.

### V3 Compliance

This story is part of V3 and must not compromise existing functionality:

1. **ACMRecord isolation**: `building_id` field is NOT modified. All 9 existing ACMRecord fields in the building hierarchy block remain unchanged.
2. **Extraction pipeline isolation**: No changes to `acm_extractor.py`, `source_commands.py`, or any extraction graph nodes.
3. **Existing API isolation**: `/api/acm/jobs/{source_id}/buildings` and `/api/acm/jobs/{source_id}/buildings/{building_id}` endpoints are unchanged.
4. **Test isolation**: All existing test files (`test_acm_api.py`, `test_acm_schemas.py`, `test_acm_extractor.py`, etc.) must continue to pass unchanged.

---

## Dev Agent Record

### Build Verification Checklist

- [ ] `uv run ruff check . --fix` passes with no errors
- [ ] `uv run ruff format .` passes
- [ ] `uv run pytest tests/test_building_record.py -v` — all new tests pass
- [ ] `uv run pytest tests/test_acm_api.py -v` — all existing ACM API tests still pass
- [ ] `uv run pytest tests/test_acm_schemas.py -v` — all existing schema tests still pass
- [ ] `uv run pytest tests/ -x` — full test suite passes
- [ ] `cd frontend && npm run build` — no frontend build errors (frontend not modified)
- [ ] `GET /api/acm/buildings?source_id=source:xxx` returns 200
- [ ] `POST /api/acm/buildings` creates record with auto-generated `internal_id`
- [ ] `GET /api/acm/records?source_id=xxx&building_record_id=building_record:yyy` filters correctly
- [ ] `GET /api/acm/jobs/{source_id}/buildings` still returns building review wizard data (regression)

### Files Verified

- [ ] `open_notebook/domain/acm.py` — `BuildingRecord` class added, `building_record_id` added to `ACMRecord`
- [ ] `api/routers/acm.py` — 5 CRUD endpoints added, `building_record_id` param added to `list_acm_records`
- [ ] `api/models.py` — 4 new model classes added
- [ ] `migrations/40.surrealql` — created with all fields, indexes, and FK
- [ ] `migrations/40_down.surrealql` — created with rollback SQL
- [ ] `tests/test_building_record.py` — created with all test classes

### Implementation Status

| Task | Status | Notes |
|------|--------|-------|
| Migration 40 (`40.surrealql`, `40_down.surrealql`) | Pending | |
| `BuildingRecord` domain model (`acm.py`) | Pending | |
| `ACMRecord.building_record_id` field (`acm.py`) | Pending | |
| `ACMRecord._prepare_save_data()` update (`acm.py`) | Pending | |
| API request/response models (`models.py`) | Pending | |
| Building CRUD endpoints (`acm.py` router) | Pending | |
| `list_acm_records` modification (`acm.py` router) | Pending | |
| Unit tests (`test_building_record.py`) | Pending | |
| Regression test run | Pending | |

---

*Tech spec authored by Ralph Scrum Master — 2026-03-03*
