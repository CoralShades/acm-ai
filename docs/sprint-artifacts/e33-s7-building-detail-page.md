# E33-S7: Building Detail Page

## Story

**ID**: E33-S7
**Title**: Building Detail Page
**Sprint**: V3-6
**Story Points**: 3
**Risk**: MEDIUM
**Type**: Frontend
**Dependencies**: E30-S2 (Building Record Table), E33-S2 (Building Grid + Item Grid)

### Acceptance Criteria

- AC1: Building detail view accessible from building sidebar click or dedicated route
- AC2: Displays all 29+ Building__c fields in structured form layout (grouped: identity, location, construction, inspection)
- AC3: Editable fields with SF picklist dropdowns where applicable
- AC4: BuildingType -> Category dependent picklist cascading on edit
- AC5: Save button persists changes via PUT /api/acm/buildings/{id}
- AC6: Validation badges on invalid fields
- AC7: Navigation: building detail <-> item grid for the same building
- AC8: Responsive form layout with proper accessibility labels

---

## Overview

This story adds a dedicated building detail page/panel showing all Building__c fields in an editable form. Officers can view and edit building-level metadata, with dependent picklist cascading for BuildingType->Category. The view is accessible both from the building sidebar (expanding the existing detail panel) and via a dedicated route.

---

## Technical Design

### Entry Points

1. **Building sidebar**: Click building name → navigate to building detail route
2. **Dedicated route**: `/source/:id/building/:buildingId`
3. **Navigation back**: "View Items" button returns to `/source/:id` with building pre-selected

### Existing Backend

- `PUT /api/acm/buildings/{building_id}` — already exists, accepts `BuildingRecordUpdateRequest`
- `GET /api/acm/buildings?source_id=X` — list buildings (existing)
- Field schema at `GET /api/acm/field-schema` — has `building_fields` with SF field defs

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/components/acm/BuildingDetailForm.tsx` | Create | Editable form showing all Building__c fields grouped by category |
| `frontend/src/app/(dashboard)/source/[id]/building/[buildingId]/page.tsx` | Create | Dedicated building detail page route |
| `frontend/src/lib/hooks/useBuildingDetail.ts` | Create | React Query hooks for building get/update |
| `frontend/src/lib/api/acm.ts` | Modify | Add `getBuilding(id)`, `updateBuilding(id, data)` methods |
| `frontend/src/lib/types/building.ts` | Modify | Add `BuildingRecordUpdateRequest` type |
| `frontend/src/components/acm/BuildingSidebar.tsx` | Modify | Add link/button to navigate to building detail page |

---

## Component Specifications

### BuildingDetailForm

```tsx
interface BuildingDetailFormProps {
  building: BuildingRecord
  sourceId: string
  schema: SFFieldSchemaConfig | null
  onSave: (data: Partial<BuildingRecord>) => void
  isSaving: boolean
}
```

**Field Groups:**
1. **Identity**: building_code, building_name, internal_id (read-only), external_id, building_unique_id, site_name, school_uid
2. **Location**: building_address, suburb, postcode, state, country, building_address_lga, building_address_region, gps_coordinates, psb_district_region
3. **Construction**: building_type (picklist), building_category (dependent on type), building_construction, roof_type, number_of_levels, est_building_size_m2, building_year
4. **Usage**: frequency_of_use, daily_duration, level_of_activity, public_access, mobile_plant, owned_or_leased, within_your_portfolio
5. **Inspection**: asbestos_register_available, audit_report_available, date_of_audit_report, no_identified_acms, no_identified_acms_note
6. **Demolition**: demolished_status, demolition_date, demolition_type, demolition_comments, building_out_of_scope, building_out_of_scope_comments
7. **Other**: additional_comments, capital_works_project_details, possible_capital_works_project

**Dependent Picklist (AC4):**
- BuildingType -> BuildingCategory uses `DependentPicklistEditor` in `mode="form"` (from E33-S3)
- Schema has `building_fields.fields` with `is_dependent` and `controller_field` markers

**Save Logic:**
- Track dirty fields (compare to original)
- Only send changed fields in PUT request
- Show toast/feedback on save success

---

## Out of Scope

- Inline validation against SF picklists (use existing validation badges from E33-S4 where applicable)
- Building-level extraction re-run
- Building deletion
