# Story E13-S1: SurrealDB Knowledge Graph Entity Schema

**Epic:** E13 — Knowledge Graph Visualization
**Priority:** P1
**Status:** backlog
**Change Proposal:** SCP-20260207 (2026-02-07)
**Blocks:** E13-S2 (Knowledge Graph API) which blocks E13-S3 (React Flow UI)

---

## User Story

**As a** developer,
**I want** separate entity tables and relationship tables in SurrealDB with proper graph semantics,
**So that** document entities (Schools, Buildings, Rooms, ACM items) have typed graph relationships that can be traversed for compliance auditing and visualization.

---

## Background

The current `acm_record` table stores all fields inline (denormalized), with `building_id`, `room_id`, and `school_code` as embedded string fields. This design was correct for Phase 1 (fast extraction, flat spreadsheet views). For Phase 2 (knowledge graph visualization, multi-site portfolio management, cross-document relationship queries), we need SurrealDB RELATION tables and separate entity tables.

SurrealDB has native graph capabilities: `RELATE` statements, `->` traversal syntax, and RELATION table types. This story creates the schema foundation that E13-S2 (Graph API) and E13-S3 (React Flow UI) depend on.

**Why E1-S4 is the key dependency (not just any E1 story):**
E1-S4 created the `acm_record` table and established its field structure. The backfill migration in this story must correctly extract unique entities from the `acm_record.building_id`, `acm_record.room_id`, and `acm_record.school_code` fields that E1-S4 defined.

---

## Acceptance Criteria

### Entity Tables

- [ ] `school` entity table created with fields:
  - `school_code` (string, unique index)
  - `school_name` (string)
  - `address` (string, optional)
  - `suburb` (string, optional)
  - `postcode` (string, optional)
  - `source_ids` (array of source record IDs)
- [ ] `building` entity table created with fields:
  - `building_code` (string, e.g., "B00A", "D001")
  - `building_name` (string, optional)
  - `school_code` (string, foreign ref to `school`)
  - `year_constructed` (string, optional)
  - `construction_type` (string, optional)
  - `building_purpose` (string, optional)
  - `page_range_start` (int, optional — from building inventory)
  - `page_range_end` (int, optional)
  - Compound unique index on `(school_code, building_code)`
- [ ] `room` entity table created with fields:
  - `room_code` (string, e.g., "R001", "R002")
  - `room_name` (string, optional)
  - `building_code` (string, foreign ref to `building`)
  - `school_code` (string, for traversal efficiency)
  - `floor_level` (string, optional)
  - `area_sqm` (float, optional)
  - Compound unique index on `(school_code, building_code, room_code)`

### Relationship Tables (SurrealDB RELATION type)

- [ ] `school_has_building` RELATION table:
  - `FROM school TO building`
  - `in` field: school record ID
  - `out` field: building record ID
  - Optional metadata: `relationship_type` (default "contains")
- [ ] `building_has_room` RELATION table:
  - `FROM building TO room`
  - `in` field: building record ID
  - `out` field: room record ID
- [ ] `room_has_acm` RELATION table:
  - `FROM room TO acm_record`
  - `in` field: room record ID
  - `out` field: acm_record ID
  - Metadata: `risk_level` (string — denormalized for fast graph queries)
- [ ] `extracted_from` RELATION table:
  - `FROM acm_record TO source`
  - `in` field: acm_record ID
  - `out` field: source record ID
  - Metadata: `page_number` (int, optional), `table_id` (string, optional)

### Migration and Backfill

- [ ] Migration script (`migrations/XX_knowledge_graph_schema.surrealql`) created
- [ ] Migration creates all entity tables and relation tables
- [ ] Backfill logic populates `school`, `building`, `room` from existing `acm_record` data:
  - Group by unique `school_code` → insert `school` records
  - Group by unique `(school_code, building_id)` → insert `building` records
  - Group by unique `(school_code, building_id, room_id)` → insert `room` records
- [ ] Backfill creates all RELATION records linking entities to each other and to `acm_record`
- [ ] Migration is idempotent (safe to re-run)
- [ ] Migration runs within the existing auto-migration system on API startup

### Backward Compatibility

- [ ] `acm_record` table retains all existing inline fields (no fields removed or renamed)
- [ ] All existing API endpoints (`GET /api/acm/records`, etc.) continue to work unchanged
- [ ] New entity tables are additive only — no breaking changes

### Pydantic Domain Models

- [ ] `School` Pydantic model created in `open_notebook/domain/graph_entities.py`
- [ ] `Building` Pydantic model created in `open_notebook/domain/graph_entities.py`
- [ ] `Room` Pydantic model created in `open_notebook/domain/graph_entities.py`
- [ ] `SchoolHasBuilding`, `BuildingHasRoom`, `RoomHasACM`, `ExtractedFrom` relation models created
- [ ] Models follow existing domain patterns (dataclass or Pydantic BaseModel, same as `ACMRecord`)

### Graph Traversal Verification

- [ ] End-to-end graph traversal query works in SurrealDB:
  ```sql
  SELECT ->school_has_building->building->building_has_room->room->room_has_acm->acm_record.*
  FROM school WHERE school_code = 'SCH001'
  ```
- [ ] Reverse traversal (from ACM record up to school) also works:
  ```sql
  SELECT <-room_has_acm<-room<-building_has_room<-building<-school_has_building<-school
  FROM acm_record WHERE id = acm_record:xyz
  ```

---

## Technical Notes

### SurrealDB RELATION Syntax

SurrealDB RELATION tables are created with:
```sql
DEFINE TABLE school_has_building TYPE RELATION FROM school TO building SCHEMAFULL;
DEFINE FIELD in ON school_has_building TYPE record<school>;
DEFINE FIELD out ON school_has_building TYPE record<building>;
```

Rows are inserted via:
```sql
RELATE school:sch001->school_has_building->building:sch001_b00a;
```

### Backfill Strategy

The backfill Python script (`open_notebook/database/graph_backfill.py`) should:

1. Query all distinct `school_code` values from `acm_record`
2. Upsert each into `school` table (use `UPDATE school:$id CONTENT {...} RETURN NONE`)
3. Query all distinct `(school_code, building_id)` pairs from `acm_record`
4. Upsert each into `building` table
5. Query all distinct `(school_code, building_id, room_id)` triples from `acm_record`
6. Upsert each into `room` table
7. For each `acm_record`, RELATE it to its `room`, which is related to its `building`, etc.

SurrealDB `UPSERT` (or `INSERT ... ON DUPLICATE KEY UPDATE`) avoids duplicate entity records on re-run.

### ID Generation Convention

Use deterministic IDs derived from natural keys to support idempotent backfill:
- `school:sch_{school_code}` (e.g., `school:sch_1234`)
- `building:bld_{school_code}_{building_code}` (e.g., `building:bld_1234_b00a`)
- `room:rm_{school_code}_{building_code}_{room_code}` (e.g., `room:rm_1234_b00a_r001`)

Lowercase, replace spaces/special chars with underscores.

### Migration File Location

Follow the existing migration naming pattern in `migrations/`. Check the highest-numbered existing migration and increment:
```
migrations/XX_knowledge_graph_schema.surrealql
```

The migration auto-runs via the existing mechanism in `api/main.py` (lifespan handler calls `run_migrations()`).

### Forward Integration Point for E13-S2

The Graph API story (E13-S2) will query:
```sql
SELECT * FROM building WHERE school_code = $school_code
  FETCH ->building_has_room->room, ->room->room_has_acm->acm_record
```

The schema defined here must support these queries efficiently. Consider adding indexes on `school_code` for all entity tables.

---

## Key Files to Create/Modify

| File | Change |
|------|--------|
| `migrations/XX_knowledge_graph_schema.surrealql` | New migration: entity tables + relation tables + indexes |
| `open_notebook/domain/graph_entities.py` | New: School, Building, Room Pydantic models + relation models |
| `open_notebook/database/graph_backfill.py` | New: backfill script to populate entities from acm_record |
| `open_notebook/database/graph_repository.py` | New: CRUD operations for entity tables (for E13-S2 to consume) |

---

## Dependencies

- **Requires:** E1-S4 (ACM API Endpoints — done) — establishes `acm_record` table schema that this story backfills from
- **Does NOT require:** E1-S16..S19 (Document Intelligence) — graph schema is independent of how records were extracted
- **Blocks:** E13-S2 (Knowledge Graph API & Data Service)
- **E13-S2 blocks:** E13-S3 (React Flow Knowledge Graph Visualization)

### Full E13 Dependency Chain

```
E1-S4 (done) → E13-S1 (this story) → E13-S2 (Graph API) → E13-S3 (React Flow UI)
```

---

## Estimated Effort

M (Medium) — Schema design is straightforward in SurrealDB. The migration SQL is moderate complexity. The main effort is the backfill logic to correctly extract and deduplicate entities from existing denormalized `acm_record` data, and ensuring idempotency.

---

## Priority Note

This story is rated **P1 (backlog)** and is lower priority than E12-S1 (Extraction Settings UI). Reasons:

1. E12 addresses immediate operator needs (model configuration, processing controls) with no prerequisite schema work
2. E13 requires schema migration and backfill — higher risk for production data
3. Knowledge graph visualization is a "Should Have" feature vs. E12's operational necessity
4. E13-S1 has no blockers of its own (E1-S4 is done) but it blocks two downstream stories (E13-S2, E13-S3) that are equally low priority

Recommended sequencing: complete E12-S1..S4 first, then begin E13-S1.

---

## Dev Agent Record

*This section is populated by the implementing dev agent upon completion.*

### Implementation Notes

*(empty — story not yet started)*

### Checklist

- [ ] Migration file created and verified with SurrealDB
- [ ] Backfill script tested on sample `acm_record` data
- [ ] All entity tables queryable via SurrealDB graph traversal
- [ ] Pydantic models created and validated
- [ ] Backward compatibility verified (existing API tests still pass)
- [ ] Build verification: `uv run ruff check .` passed
- [ ] Build verification: `uv run pytest` passed

### Files Verified

*(empty — story not yet started)*

### Evidence

*(empty — story not yet started)*
