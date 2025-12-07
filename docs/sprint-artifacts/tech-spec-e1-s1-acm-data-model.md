# Tech-Spec: E1-S1 ACM Data Model

**Created:** 2025-12-07
**Status:** Ready for Development
**Epic:** E1 - ACM Data Extraction Pipeline
**Story:** S1 - Create ACM Data Model

---

## Overview

### Problem Statement

ACM-AI needs to store structured Asbestos Containing Material (ACM) Register data extracted from PDF documents. Currently, the system can process PDFs via Docling but has no dedicated schema to store hierarchical ACM data (School → Building → Room → ACM Item) with proper relationships to source documents.

### Solution

Create a new SurrealDB table `acm_record` with a comprehensive schema that:
- Links each ACM record to its source PDF document
- Captures the full hierarchical structure (school, building, room)
- Stores all ACM-specific fields (product, material, friable status, risk level, etc.)
- Includes page number for citation support
- Supports efficient querying by building, room, and risk status

### Scope

**In Scope:**
- SurrealDB table definition for `acm_record`
- Migration file (10.surrealql and 10_down.surrealql)
- Indexes for common query patterns
- Delete event to cascade when source is deleted

**Out of Scope:**
- Python domain model (E1-S2)
- API endpoints (E1-S4)
- Extraction logic (E1-S3)
- Frontend components (E2)

---

## Context for Development

### Codebase Patterns

#### 1. Migration File Pattern
Location: `migrations/`
- Files named: `{number}.surrealql` (up) and `{number}_down.surrealql` (down)
- Current highest: `9.surrealql` → new file should be `10.surrealql`
- Uses `DEFINE TABLE IF NOT EXISTS`, `DEFINE FIELD IF NOT EXISTS`
- Uses `DEFINE EVENT IF NOT EXISTS` for cascade deletes

Example from `1.surrealql`:
```surrealql
DEFINE TABLE IF NOT EXISTS source SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS title ON TABLE source TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created ON source DEFAULT time::now() VALUE $before OR time::now();
DEFINE EVENT IF NOT EXISTS source_delete ON TABLE source WHEN ($after == NONE) THEN {
    delete source_embedding where source == $before.id;
};
```

#### 2. Relationship Pattern
From existing schema:
```surrealql
DEFINE FIELD IF NOT EXISTS source ON TABLE source_embedding TYPE record<source>;
```

#### 3. Index Pattern
```surrealql
DEFINE INDEX IF NOT EXISTS idx_source_title ON TABLE source COLUMNS title SEARCH ANALYZER my_analyzer BM25 HIGHLIGHTS;
```

### Files to Reference

| File | Purpose |
|------|---------|
| `migrations/1.surrealql` | Base schema pattern for source, note, notebook |
| `migrations/9.surrealql` | Latest migration, shows current patterns |
| `docs/acm-ai/03-prd.md` | ACM Record schema requirements (Section 5.1) |
| `docs/acm-ai/04-architecture.md` | Technical design for ACM tables |

### Technical Decisions

1. **SCHEMAFULL vs SCHEMALESS**: Use `SCHEMAFULL` for data integrity (consistent with existing tables)
2. **Field Types**: Use `option<T>` for nullable fields (matches existing pattern)
3. **Foreign Key**: Use `record<source>` for source_id relationship
4. **Timestamps**: Use same pattern as existing tables with `time::now()` defaults
5. **Cascade Delete**: Add event to delete ACM records when source is deleted

---

## Implementation Plan

### Tasks

- [ ] **Task 1: Create migration file `migrations/10.surrealql`**
  - Define `acm_record` table with SCHEMAFULL
  - Define all fields matching PRD Section 5.1 schema
  - Add indexes for source_id, building_id, room_id, risk_status
  - Add cascade delete event

- [ ] **Task 2: Create rollback file `migrations/10_down.surrealql`**
  - Remove indexes
  - Remove event
  - Remove table

- [ ] **Task 3: Test migration**
  - Run migration against dev database
  - Verify table created with correct schema
  - Test cascade delete behavior
  - Test rollback works

- [ ] **Task 4: Document schema**
  - Update `docs/acm-ai/04-architecture.md` if needed
  - Add comments in migration file

### Acceptance Criteria

- [ ] **AC1**: Migration file `10.surrealql` exists and executes without errors
  - Given: A fresh SurrealDB database
  - When: Migration 10.surrealql is executed
  - Then: Table `acm_record` is created with all defined fields

- [ ] **AC2**: All fields from PRD are present in schema
  - Given: The acm_record table exists
  - When: Schema is inspected
  - Then: All fields match PRD Section 5.1 (source_id, school_name, building_id, room_id, product, material_description, extent, location, friable, material_condition, risk_status, result, page_number, etc.)

- [ ] **AC3**: Indexes created for efficient querying
  - Given: The acm_record table exists
  - When: Indexes are listed
  - Then: Indexes exist for source_id, building_id, risk_status

- [ ] **AC4**: Cascade delete works
  - Given: An acm_record linked to a source
  - When: The source is deleted
  - Then: Associated acm_records are automatically deleted

- [ ] **AC5**: Rollback migration works
  - Given: Migration 10 has been applied
  - When: Migration 10_down is executed
  - Then: The acm_record table is completely removed

---

## Additional Context

### Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| SurrealDB v2 | Infrastructure | Already running in project |
| Migration runner | Tool | Existing migration system |
| Source table | Database | Must exist (from migration 1) |

### Testing Strategy

1. **Unit Test**: N/A (pure database schema)
2. **Integration Test**:
   - Create source
   - Insert ACM record linked to source
   - Query by building_id
   - Delete source → verify ACM records deleted
3. **Manual Verification**:
   - Use SurrealDB Studio or CLI to inspect schema
   - Run sample queries

### Schema Definition

```surrealql
-- ACM Record Table (to be placed in migrations/10.surrealql)

DEFINE TABLE IF NOT EXISTS acm_record SCHEMAFULL;

-- Foreign key to source document
DEFINE FIELD IF NOT EXISTS source_id ON TABLE acm_record TYPE record<source>;

-- School identification
DEFINE FIELD IF NOT EXISTS school_name ON TABLE acm_record TYPE string;
DEFINE FIELD IF NOT EXISTS school_code ON TABLE acm_record TYPE option<string>;

-- Building hierarchy
DEFINE FIELD IF NOT EXISTS building_id ON TABLE acm_record TYPE string;
DEFINE FIELD IF NOT EXISTS building_name ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS building_year ON TABLE acm_record TYPE option<int>;
DEFINE FIELD IF NOT EXISTS building_construction ON TABLE acm_record TYPE option<string>;

-- Room hierarchy
DEFINE FIELD IF NOT EXISTS room_id ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS room_name ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS room_area ON TABLE acm_record TYPE option<float>;
DEFINE FIELD IF NOT EXISTS area_type ON TABLE acm_record TYPE option<string>;

-- ACM item data
DEFINE FIELD IF NOT EXISTS product ON TABLE acm_record TYPE string;
DEFINE FIELD IF NOT EXISTS material_description ON TABLE acm_record TYPE string;
DEFINE FIELD IF NOT EXISTS extent ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS location ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS friable ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS material_condition ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS risk_status ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS result ON TABLE acm_record TYPE string;

-- Citation support
DEFINE FIELD IF NOT EXISTS page_number ON TABLE acm_record TYPE option<int>;
DEFINE FIELD IF NOT EXISTS extraction_confidence ON TABLE acm_record TYPE option<float>;

-- Timestamps (following existing pattern)
DEFINE FIELD IF NOT EXISTS created ON acm_record DEFAULT time::now() VALUE $before OR time::now();
DEFINE FIELD IF NOT EXISTS updated ON acm_record DEFAULT time::now() VALUE time::now();

-- Indexes for query performance
DEFINE INDEX IF NOT EXISTS idx_acm_source ON TABLE acm_record COLUMNS source_id;
DEFINE INDEX IF NOT EXISTS idx_acm_building ON TABLE acm_record COLUMNS building_id;
DEFINE INDEX IF NOT EXISTS idx_acm_room ON TABLE acm_record COLUMNS room_id;
DEFINE INDEX IF NOT EXISTS idx_acm_risk ON TABLE acm_record COLUMNS risk_status;

-- Cascade delete when source is deleted
DEFINE EVENT IF NOT EXISTS acm_record_source_delete ON TABLE source WHEN ($after == NONE) THEN {
    DELETE acm_record WHERE source_id == $before.id;
};
```

### Rollback Schema

```surrealql
-- Rollback for migration 10 (to be placed in migrations/10_down.surrealql)

REMOVE EVENT IF EXISTS acm_record_source_delete ON TABLE source;
REMOVE INDEX IF EXISTS idx_acm_source ON TABLE acm_record;
REMOVE INDEX IF EXISTS idx_acm_building ON TABLE acm_record;
REMOVE INDEX IF EXISTS idx_acm_room ON TABLE acm_record;
REMOVE INDEX IF EXISTS idx_acm_risk ON TABLE acm_record;
REMOVE TABLE IF EXISTS acm_record;
```

### Notes

1. **Field naming**: Using snake_case to match existing schema
2. **Required fields**: `source_id`, `school_name`, `building_id`, `product`, `material_description`, `result` are required (no `option<>`)
3. **Risk status values**: Expected values are "Low", "Medium", "High" but stored as string for flexibility
4. **Area type values**: Expected values are "Exterior", "Interior", "Grounds"
5. **Friable values**: Expected values are "Friable", "Non Friable"

---

## Next Stories After This

| Story | Description | Depends On |
|-------|-------------|------------|
| E1-S2 | Create ACM Record Domain Model (Python) | This story |
| E1-S3 | Implement ACM Extraction Transformation | E1-S2 |
| E1-S4 | Create ACM API Endpoints | E1-S2 |

---

*Tech-Spec generated by create-tech-spec workflow*
