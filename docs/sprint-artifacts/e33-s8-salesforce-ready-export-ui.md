# E33-S8: Salesforce-Ready Export UI

## Story

**ID**: E33-S8
**Title**: Salesforce-Ready Export UI
**Sprint**: V3-6
**Story Points**: 2
**Risk**: LOW
**Type**: Frontend + Backend
**Dependencies**: E30-S2 (Building Record Table), E30-S3 (ACM Record SF Alignment), E33-S4 (Validation Badges)

### Acceptance Criteria

- AC1: Export dialog accessible from building grid toolbar: /source/:id/export
- AC2: Two-file CSV export: Building__c.csv + Item__c.csv with exact SF API field names as headers
- AC3: Excel export: two-sheet workbook with Building__c and Item__c tabs
- AC4: External ID linkage: Building__c.External_ID__c referenced by Item__c.Building__r.External_ID__c
- AC5: Site config merge: officer-configured fields merged into all export records
- AC6: Export blocked when validation errors exist
- AC7: Selected buildings: option to export only selected buildings
- AC8: BAR backward compatibility: Export as BAR Excel option retained

---

## Overview

This story adds a Salesforce Data Loader-ready export UI to the ACM register view. Instead of a single flat CSV/Excel with BAR field names, the export now produces two separate files matching Salesforce object structures: `Building__c` and `Item__c`. The existing BAR Excel export is retained as a backward-compatible option.

---

## Technical Design

### Architecture

```
ExportDialog.tsx (Radix Dialog)
  ├── Format selection: SF CSV | SF Excel | BAR Excel (legacy)
  ├── Building selection: All or selected only (AC7)
  ├── Validation guard: blocked if errors exist (AC6, already in E33-S4)
  └── Download triggers:
        ├── SF CSV → GET /api/acm/export/sf-csv?source_id=X&building_ids=... → ZIP (2 CSVs)
        ├── SF Excel → GET /api/acm/export/sf-excel?source_id=X&building_ids=... → XLSX (2 sheets)
        └── BAR Excel → GET /api/acm/export/excel?source_id=X (existing endpoint)
```

### SF Field Mapping

The export uses exact SF API field names as column headers. The mapping from ACMRecord/BuildingRecord fields to SF API names is the reverse of `fieldApiToRecordKey()` in `acm-field-mapping.ts`.

**Building__c columns** (from `building_fields_summary.md` via field_schema):
Key fields: `External_ID__c`, `Building_Name__c`, `Building_Code__c`, `Building_Type__c`, `Building_Category__c`, `Building_Address__c`, `Suburb__c`, `Postcode__c`, etc.

**Item__c columns** (from `item_fields_summary.md` via field_schema):
Key fields: `Building__r.External_ID__c` (FK), `ACM_Name__c`, `ACM_Description__c`, `Room_ID__c`, `Room_Name__c`, `Friability_of_Material__c`, `ACM_Classification__c`, `Risk_Status__c`, `Result__c`, etc.

### External ID Linkage (AC4)

- `BuildingRecord.external_id` or `BuildingRecord.building_unique_id` serves as `External_ID__c`
- If neither exists, generate: `{source_short}_{building_code}` as External_ID__c
- Item__c rows reference `Building__r.External_ID__c` = the parent building's External_ID__c
- This enables Salesforce Data Loader to create proper parent-child relationships

### Site Config Merge (AC5)

The SiteConfig for the source contains officer-configured fields (department, agency, site_name, etc.). These are merged into Building__c records before export:
- `Department__c` from SiteConfig.department
- `Agency__c` from SiteConfig.agency
- Other officer-configured building-level fields

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/components/acm/ExportDialog.tsx` | Create | Export dialog with format selection, building filter, validation guard |
| `frontend/src/app/(dashboard)/source/[id]/page.tsx` | Modify | Replace inline export button with ExportDialog trigger |
| `frontend/src/lib/api/acm.ts` | Modify | Add `exportSfCsv`, `exportSfExcel` API methods |
| `api/routers/acm.py` | Modify | Add `/export/sf-csv` and `/export/sf-excel` endpoints |
| `open_notebook/extractors/exporters/sf_export.py` | Create | SF export logic: field mapping, External ID generation, site config merge |
| `tests/test_sf_export.py` | Create | Unit tests for SF export field mapping and External ID linkage |

---

## Component Specifications

### ExportDialog (`ExportDialog.tsx`)

```tsx
interface ExportDialogProps {
  sourceId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  totalErrors: number           // From validation summary
  selectedBuildingIds?: string[] // From building selection (optional)
}
```

**Content:**
- Radio group for export format:
  - "Salesforce CSV (2 files)" — downloads a ZIP containing Building__c.csv + Item__c.csv
  - "Salesforce Excel (2 sheets)" — downloads XLSX with Building__c + Item__c tabs
  - "BAR Excel (legacy)" — uses existing export endpoint
- Checkbox: "Export selected buildings only" (disabled if no buildings selected)
- Warning banner if `totalErrors > 0`: "N validation errors must be resolved before export"
- Export button (disabled if errors exist)

### Backend: SF CSV Export (`/export/sf-csv`)

```python
@router.get("/export/sf-csv")
async def export_sf_csv(
    source_id: str,
    building_ids: Optional[str] = Query(None, description="Comma-separated building IDs"),
):
    """Export as ZIP containing Building__c.csv + Item__c.csv with SF API field names."""
```

Returns a ZIP file with two CSVs. Each CSV has SF API names as headers.

### Backend: SF Excel Export (`/export/sf-excel`)

```python
@router.get("/export/sf-excel")
async def export_sf_excel(
    source_id: str,
    building_ids: Optional[str] = Query(None, description="Comma-separated building IDs"),
):
    """Export as XLSX with Building__c and Item__c sheets."""
```

Returns a single XLSX with two sheets.

### SF Export Module (`sf_export.py`)

Core logic for SF field mapping, shared by both CSV and Excel endpoints:

```python
def get_building_sf_mapping() -> list[tuple[str, str]]:
    """Return [(sf_api_name, building_record_field), ...] for Building__c export."""

def get_item_sf_mapping() -> list[tuple[str, str]]:
    """Return [(sf_api_name, acm_record_field), ...] for Item__c export."""

def generate_external_id(building: BuildingRecord, source_id: str) -> str:
    """Generate External_ID__c for a building if not already set."""

async def merge_site_config(buildings: list[dict], source_id: str) -> list[dict]:
    """Merge SiteConfig fields into building export dicts."""
```

---

## Testing Strategy

### Backend Tests (`tests/test_sf_export.py`)
- `get_building_sf_mapping()` returns correct SF API names
- `get_item_sf_mapping()` returns correct SF API names
- `generate_external_id()` creates consistent IDs
- External ID linkage: Item__c.Building__r.External_ID__c matches Building__c.External_ID__c
- Site config merge adds department/agency fields
- Building ID filter works correctly

### Build Verification
- `cd frontend && npm run build` passes
- `uv run ruff check .` passes

---

## Edge Cases

1. **No buildings**: Export should return 404 or empty ZIP with headers only
2. **Missing site config**: Export proceeds without site config fields (they're optional)
3. **No External ID**: Generate from source_id + building_code
4. **Selected buildings filter**: Only export matching buildings and their items

---

## Out of Scope

- Salesforce Data Loader automation (manual upload)
- Real-time SF API integration
- Export history/audit trail
