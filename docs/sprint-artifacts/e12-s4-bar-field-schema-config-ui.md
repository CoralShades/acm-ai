# Story E12-S4: BAR Field Schema Configuration UI

**Epic:** E12 — Extraction Settings & Configuration UI
**Priority:** P1
**Status:** drafted
**Change Proposal:** SCP-20260208 (2026-02-08) — Course Correction CP-2

---

## User Story

**As a** system administrator or compliance officer,
**I want to** view and manage the BAR field schema configuration through a dedicated settings UI,
**So that** I can configure which fields are extracted, customise display names, control field ordering, manage picklist values, and toggle business rules — all without developer intervention.

---

## Background

E1-S11 (Generic Configurable Parser with BAR Field Schema) redefined the extraction architecture: three specialised parsers (Prensa, Greencap, Generic) were replaced by one configurable parser driven by a field schema stored in SurrealDB. The field schema is sourced from `register_row.schema.json` (47 fields) and `register_enums.json` (controlled picklist values per field).

This story provides the admin UI at `/settings/field-schema` to inspect and modify that configuration. Changes made here propagate to extraction (field list, enum validation), the AG Grid spreadsheet (column visibility, headers), and Excel/CSV export (column order, labels).

**Dependency:** E1-S11 must be done before this story can be implemented. E1-S11 is done as of the current sprint (see `sprint-status.yaml`).

---

## Acceptance Criteria

### Field Schema Editor
- [ ] Settings page at `/settings/field-schema` accessible from the sidebar CONFIGURE section
- [ ] Displays all 47 BAR fields in a drag-reorder list (ordered by current `sort_order`)
- [ ] Each field row shows: BAR column letter, internal key, display name, field type, required/optional badge, active toggle
- [ ] Drag to reorder changes `sort_order` (persisted on save)
- [ ] Per-field edit modal:
  - [ ] Edit display name (label shown in grid headers and export)
  - [ ] Toggle required vs optional
  - [ ] Toggle active (inactive fields are excluded from extraction output and grid columns)
  - [ ] View internal key and BAR column letter (read-only)
- [ ] Save button persists changes via `PUT /api/settings/field-schema`
- [ ] Reset to Defaults button restores schema from seeded BAR Excel baseline

### Picklist Value Editor
- [ ] Each field with a controlled enum has an expandable "Edit Picklist" section
- [ ] Displays current allowed values in a list
- [ ] Add / remove / rename values
- [ ] Import picklist from BAR Excel template (parses the `.xlsm` dropdown definitions)
- [ ] Changes persisted with the field schema

### Business Rules Editor
- [ ] List of active business rules (e.g., "Negative result → N/A for Condition and Disturbance")
- [ ] Toggle each rule on/off
- [ ] View rule description and affected fields
- [ ] Add custom rules is out of scope for this story (view + toggle only)

### Config Import / Export
- [ ] "Export as JSON" button — downloads current field schema config as JSON
- [ ] "Import from BAR Excel" button — upload a `.xlsm`/`.xlsx` file; system extracts field list and picklists
- [ ] "Reset to Defaults" applies the seeded baseline from `register_row.schema.json` + `register_enums.json`
- [ ] Import shows a diff preview before confirming

### General
- [ ] All changes are reflected immediately in:
  - Extraction pipeline (next extraction run uses updated schema)
  - AG Grid column definitions (columns regenerated from field config)
  - Excel/CSV export (column order and headers updated)
- [ ] API endpoints: `GET /api/settings/field-schema`, `PUT /api/settings/field-schema`
- [ ] Unsaved changes indicator (dirty state) prevents accidental navigation away

---

## Technical Notes

### Backend

**New endpoint in `api/routers/settings.py`:**
```
GET  /api/settings/field-schema   → Returns FieldSchemaConfig (list of FieldDef)
PUT  /api/settings/field-schema   → Accepts updated FieldSchemaConfig, persists to SurrealDB
```

**SurrealDB table:** `bar_schema_config`
- Stores the full `FieldSchemaConfig` as a single config record
- Key: `bar_schema_config:active` (singleton pattern consistent with other config tables)

**Existing models to extend (`open_notebook/extractors/parsers/field_config.py` from E1-S11):**
```python
class FieldDef(BaseModel):
    key: str               # internal field key
    bar_column: str        # BAR Excel column letter (e.g. "A", "AA")
    display_name: str      # customisable label
    field_type: str        # "string" | "enum" | "boolean" | "integer"
    required: bool
    active: bool           # if False, excluded from extraction and grid
    sort_order: int        # drag-reorder index
    allowed_values: list[str] | None   # enum picklist

class FieldSchemaConfig(BaseModel):
    fields: list[FieldDef]
    business_rules: list[BusinessRuleDef]
    version: str
    updated_at: datetime
```

### Frontend

**New page:** `frontend/src/app/(dashboard)/settings/field-schema/page.tsx`

**Drag-and-drop reordering:** `@dnd-kit/sortable` is NOT currently in `package.json`.
Options (in order of preference):
1. Install `@dnd-kit/core` + `@dnd-kit/sortable` — purpose-built, tree-shakeable, accessible
2. Use HTML5 `draggable` attribute with `onDragStart`/`onDrop` — no new dependency, acceptable for a settings list

Decision should be made at implementation time. If installing `@dnd-kit/sortable`:
```bash
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

**Edit modal:** Use existing Radix UI `Dialog` component (already in `package.json`).

**Import from Excel:** Use a file input accepting `.xlsm,.xlsx`. Send via `multipart/form-data` to a dedicated `POST /api/settings/field-schema/import` endpoint that parses the template server-side (Python `openpyxl`).

**State management:** React Query for server state (`useQuery`/`useMutation`). Local dirty state managed with `useState` or `useReducer` for the pending changes list.

### Integration Points

| Downstream System | Impact of Schema Change |
|---|---|
| `open_notebook/extractors/parsers/generic.py` | Re-reads `FieldSchemaConfig` on each extraction run |
| `frontend/src/components/acm/ACMSpreadsheet.tsx` (E2-S8) | Regenerates AG Grid column definitions from field config API |
| `api/routers/acm.py` export endpoints | Column order and headers sourced from active field config |

---

## Key Files

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/settings/field-schema/page.tsx` | New settings page (main deliverable) |
| `frontend/src/components/settings/FieldSchemaEditor.tsx` | New: drag-reorder field list component |
| `frontend/src/components/settings/FieldEditModal.tsx` | New: per-field edit modal |
| `frontend/src/components/settings/PicklistEditor.tsx` | New: enum value editor |
| `frontend/src/components/settings/BusinessRulesList.tsx` | New: rule toggle list |
| `api/routers/settings.py` | Add `field-schema` GET/PUT endpoints |
| `open_notebook/domain/settings.py` | Add `FieldSchemaConfig` domain model if not already in `field_config.py` |
| `migrations/XX-bar-schema-config.surrealql` | New table: `bar_schema_config` |

---

## Dependencies

- **Requires:** E1-S11 (Generic Configurable Parser — done) — provides `FieldSchemaConfig`, `FieldDef` models and `GET/PUT /api/acm/field-config` endpoint
- **Note:** E1-S11 exposes `/api/acm/field-config`; this story uses `/api/settings/field-schema` — the settings router should delegate to the same underlying service, or the ACM field-config endpoint should be aliased under `/api/settings/`
- **Blocks:** Nothing (E12-S4 is a leaf story in the current dependency tree)

---

## Estimated Effort

M (Medium) — New page with several sub-components, two new backend endpoints, one new migration. No complex algorithmic logic; primarily CRUD UI wiring. Drag-and-drop is the highest-risk element if `@dnd-kit` requires install and testing.

---

## Dev Agent Record

*To be filled in during implementation.*

- Build status: —
- Files verified: —
- Pages verified: —
- Screenshot path: —
