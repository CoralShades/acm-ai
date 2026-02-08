# Story 5.4: Export Field Mapping Configuration

Status: ready-for-dev

## Story

As a **power user**,
I want **to configure how ACM-AI fields map to BAR columns**,
so that **I can customize exports for different BAR versions and ensure government submission compliance**.

## Acceptance Criteria

1. **AC1 - View Mappings UI**: Frontend page/panel displays current ACM-AI field → BAR column mappings in a two-column table format showing source field, target BAR column, and mapping status (mapped/unmapped/computed).

2. **AC2 - Edit Mappings**: User can reassign which ACM-AI field maps to which BAR column via dropdown selection. Changes persist and take effect on next export.

3. **AC3 - Computed/Derived Fields**: Support derived field mappings (e.g., `friability_display` derived from `friable`, `risk_status` derived from condition + disturbance_potential). Computed fields shown differently in UI (read-only with formula indicator).

4. **AC4 - Default Mappings**: System ships with a pre-configured default mapping based on `docs/reference/bar-schema.md` Field Mapping table. Default covers all 47 BAR columns (A-AU).

5. **AC5 - Export Mapping Config**: User can download current mapping as JSON file for backup/sharing.

6. **AC6 - Import Mapping Config**: User can upload a mapping JSON file to restore or share configurations.

7. **AC7 - API Endpoints**: `GET /api/acm/mappings` returns current mapping. `PUT /api/acm/mappings` updates mapping. `POST /api/acm/mappings/reset` restores defaults.

## Dependencies

- **E5-S3 (BAR Template Management)**: Must be completed first. E5-S3 creates the BAR template model and parsing service. This story builds ON TOP of that template infrastructure to configure field-level mappings.
- **E5-S2 (Excel Export)**: Already done. Current export uses hardcoded 13-column mapping (`api/routers/acm.py:359-373`). This story enables the Excel export to use configurable mappings instead.

## Tasks / Subtasks

- [ ] Task 1: Create FieldMapping domain model and default mapping data (AC: 4, 7)
  - [ ] 1.1 Create `open_notebook/domain/field_mapping.py` with FieldMapping model
  - [ ] 1.2 Create `open_notebook/domain/default_bar_mapping.json` with all 47 BAR column mappings
  - [ ] 1.3 Create DB migration for `field_mapping` table
- [ ] Task 2: Create API endpoints for mapping CRUD (AC: 5, 6, 7)
  - [ ] 2.1 Add Pydantic request/response models to `api/models.py`
  - [ ] 2.2 Add GET/PUT/POST endpoints to `api/routers/acm.py`
  - [ ] 2.3 Add export-as-JSON and import-from-JSON endpoints
- [ ] Task 3: Create frontend FieldMappingConfig component (AC: 1, 2, 3)
  - [ ] 3.1 Create `frontend/src/components/acm/FieldMappingConfig.tsx`
  - [ ] 3.2 Add TypeScript types and API client methods
  - [ ] 3.3 Integrate into settings/export UI area
- [ ] Task 4: Write tests (AC: all)
  - [ ] 4.1 Backend unit tests for mapping model and API
  - [ ] 4.2 Frontend component tests (if test framework exists)
- [ ] Task 5: Run lint, tests, build verification

## Dev Notes

### Architecture Patterns to Follow

- **Domain model pattern**: Follow `SiteConfig` (`open_notebook/domain/site_config.py`) for DB-backed configuration model. Uses `ObjectModel` base class with `table_name` ClassVar and repository methods.
- **API pattern**: Follow existing ACM router patterns in `api/routers/acm.py`. Use Pydantic models from `api/models.py` for request/response types.
- **Frontend pattern**: Follow existing ACM components in `frontend/src/components/acm/`. Use React Query for API calls, TypeScript types in `frontend/src/lib/types/acm.ts`.

### Existing Export Infrastructure (DO NOT REINVENT)

The current export endpoints are at:
- **CSV**: `api/routers/acm.py:237-317` - Uses 13 hardcoded columns
- **Excel**: `api/routers/acm.py:328-439` - Uses 13 hardcoded columns with openpyxl formatting
- **Frontend API client**: `frontend/src/lib/api/acm.ts:80-99` - `exportCsv()` and `exportExcel()`

This story creates the mapping configuration. A **future enhancement** (not this story) will wire the export endpoints to use the configured mappings instead of hardcoded columns.

### BAR Schema Reference

47 BAR columns defined in [bar-schema.md](docs/reference/bar-schema.md):
- **Required (A-AH)**: 34 columns - Department through Disturbance Potential
- **Recommended (AI-AU)**: 13 columns - Quantity through Photo Reference

The complete ACM-AI → BAR field mapping table is at [bar-schema.md#field-mapping](docs/reference/bar-schema.md#field-mapping-acm-ai--bar).

### ACM-AI Source Fields Available

From `ACMRecord` domain model (`open_notebook/domain/acm.py`):
- **Core**: source_id, school_name, school_code, building_id, building_name, building_year, building_construction
- **Room**: room_id, room_name, room_area, area_type
- **ACM data**: product, material_description, extent, location, friable, material_condition, risk_status, result
- **AI-extracted** (E1-S7): disturbance_potential, sample_no, sample_result, identifying_company, quantity, acm_labelled, acm_label_details, hygienist_recommendations, psb_supplied_acm_id, removal_status, date_of_removal
- **Classification** (E1-S9): acm_product_group, acm_product_type
- **Normalization** (E1-S12): normalized_action

From `SiteConfig` domain model (`open_notebook/domain/site_config.py`):
- department, agency, building_type, owned_or_leased, frequency_of_use, public_access, building_unique_id

### Computed/Derived Fields (AC3)

These BAR columns are derived, not directly stored:
- **Column Z** (`friability_display`): Display name derived from `friable` enum
- **Column AB** (`acm_group_display`): Display name derived from `acm_product_group`
- **`risk_status`**: Derived from condition + disturbance_potential (already computed)

### Default Mapping Structure (AC4)

The default mapping JSON should follow this structure per entry:
```json
{
  "bar_column": "A",
  "bar_field_name": "Department",
  "acm_ai_field": "department",
  "source_model": "site_config",
  "mapping_type": "direct",
  "required": true,
  "notes": ""
}
```

Where `mapping_type` is one of: `"direct"`, `"computed"`, `"unmapped"`.
Where `source_model` is one of: `"acm_record"`, `"site_config"`.

### File Changes Required

| File | Action | Purpose |
|------|--------|---------|
| `open_notebook/domain/field_mapping.py` | CREATE | FieldMapping domain model |
| `open_notebook/domain/default_bar_mapping.json` | CREATE | Default 47-column mapping data |
| `migrations/16.surrealql` | CREATE | field_mapping table schema |
| `migrations/16_down.surrealql` | CREATE | Rollback migration |
| `api/models.py` | MODIFY | Add FieldMapping request/response models |
| `api/routers/acm.py` | MODIFY | Add mapping CRUD endpoints |
| `frontend/src/components/acm/FieldMappingConfig.tsx` | CREATE | Mapping configuration UI |
| `frontend/src/lib/types/acm.ts` | MODIFY | Add FieldMapping TypeScript types |
| `frontend/src/lib/api/acm.ts` | MODIFY | Add mapping API client methods |
| `tests/test_field_mapping.py` | CREATE | Backend unit tests |

### Anti-Patterns to Avoid

- **DO NOT** modify existing CSV/Excel export logic. This story only creates the mapping configuration; wiring it into exports is a separate concern.
- **DO NOT** store full Excel files. Only store mapping metadata (JSON structure).
- **DO NOT** create a separate page/route for mappings. Integrate into existing ACM settings or export area.
- **DO NOT** use AG Grid Enterprise for the mapping table. Use a simple HTML table or shadcn/ui table component.
- **DO NOT** hardcode BAR column letters in code. Load from `default_bar_mapping.json`.

### SurrealDB Migration Pattern

Follow existing migration pattern (see `migrations/15.surrealql`):
```sql
-- Migration 16: Add field_mapping table for BAR export configuration (E5-S4)
DEFINE TABLE field_mapping SCHEMAFULL;
DEFINE FIELD name ON field_mapping TYPE string;
DEFINE FIELD mappings ON field_mapping TYPE array;
DEFINE FIELD is_default ON field_mapping TYPE bool DEFAULT false;
DEFINE FIELD created ON field_mapping TYPE datetime DEFAULT time::now();
DEFINE FIELD updated ON field_mapping TYPE datetime DEFAULT time::now();
DEFINE INDEX field_mapping_name ON field_mapping FIELDS name UNIQUE;
```

### Testing Requirements

- Test default mapping loads correctly and covers all 47 BAR columns
- Test CRUD API endpoints (GET, PUT, POST reset)
- Test mapping export/import round-trip
- Test computed field types are handled correctly
- Test validation rejects invalid field names
- Run `uv run pytest` - all tests must pass
- Run `uv run ruff check .` - lint clean
- Run `cd frontend && npm run build` - build succeeds

### Previous Story Learnings (from E5-S3 story file)

- BAR = Building Asbestos Register - Victorian Government mandated Excel format (~47 columns A-AU)
- Two sample BAR templates exist: `docs/samplePDF/Clutch_Broadmeadows_Police_BAR.xlsx` and `docs/samplePDF/Clucth_Alexandra_District_BAR.xlsm`
- 34 required + 13 recommended columns
- Complete field mapping defined in `docs/reference/bar-schema.md`
- Use `openpyxl` for Excel operations (already a dependency)
- Follow `SiteConfig` domain model patterns for configuration storage

### Project Structure Notes

- Backend domain models: `open_notebook/domain/`
- API endpoints: `api/routers/acm.py`
- API models: `api/models.py`
- Frontend components: `frontend/src/components/acm/`
- Frontend types: `frontend/src/lib/types/acm.ts`
- Frontend API client: `frontend/src/lib/api/acm.ts`
- Migrations: `migrations/`
- Tests: `tests/`

### References

- [Source: docs/reference/bar-schema.md] - Complete BAR column definitions and field mapping
- [Source: open_notebook/domain/acm.py] - ACMRecord domain model with all available fields
- [Source: open_notebook/domain/site_config.py] - SiteConfig domain model (building-level BAR fields)
- [Source: api/routers/acm.py:237-439] - Existing export endpoints (CSV + Excel)
- [Source: _bmad-output/planning-artifacts/acm-ai/05-epics-and-stories.md#epic-5] - Epic 5 requirements
- [Source: _bmad-output/implementation-artifacts/e5-s3-bar-template-management.md] - Previous story context
- [Source: docs/sprint-artifacts/sprint-status.yaml] - Sprint tracking

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### Change Log

### File List
