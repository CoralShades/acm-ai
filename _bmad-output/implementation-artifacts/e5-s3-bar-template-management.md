# Story 5.3: BAR Template Management

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want to **use official BAR Excel templates**,
so that **exports are guaranteed to be compliant with Victorian Government requirements**.

## Acceptance Criteria

1. Upload official BAR template (.xlsm/.xlsx) via API endpoint
2. System extracts column structure (header names, column order) from the uploaded template
3. Validates that ACM-AI schema can map to all template columns
4. Shows mapping gaps/warnings (columns in template without matching ACM-AI fields)
5. Template versioning support (store version, upload date, mark active)
6. Default template bundled with system (extracted from existing sample BAR files)
7. API endpoints: `GET /api/acm/templates` (list), `POST /api/acm/templates` (upload), `GET /api/acm/templates/{id}` (details), `DELETE /api/acm/templates/{id}` (remove)
8. Frontend UI to manage templates (upload, view, set default, delete)

## Tasks / Subtasks

- [ ] Task 1: Create BARTemplate domain model (AC: #5, #6)
  - [ ] 1.1 Create `open_notebook/domain/bar_template.py` with BARTemplate model
  - [ ] 1.2 Define fields: id, name, version, columns (list), column_count, mapping_coverage, is_default, file_hash, created_at, updated_at
  - [ ] 1.3 Add CRUD methods following SiteConfig patterns (get, list, create, delete, set_default)
  - [ ] 1.4 Create SurrealDB migration for `bar_template` table
- [ ] Task 2: Create template parser service (AC: #2, #3, #4)
  - [ ] 2.1 Create `open_notebook/services/bar_template_parser.py`
  - [ ] 2.2 Implement `parse_template(file_bytes, filename)` - reads header row from uploaded Excel
  - [ ] 2.3 Implement `validate_mapping(template_columns)` - compares against bar-schema.md field mapping
  - [ ] 2.4 Return `TemplateParseResult` with: columns found, mapping_coverage %, unmapped columns, warnings
  - [ ] 2.5 Handle both .xlsx and .xlsm file formats
- [ ] Task 3: Create default bundled template (AC: #6)
  - [ ] 3.1 Extract column structure from `docs/samplePDF/Clutch_Broadmeadows_Police_BAR.xlsx`
  - [ ] 3.2 Store as a seed/default template that auto-creates on first API startup
  - [ ] 3.3 Add migration or startup hook to seed default template
- [ ] Task 4: Create API endpoints (AC: #7)
  - [ ] 4.1 Add template routes to `api/routers/acm.py`
  - [ ] 4.2 `GET /api/acm/templates` - list all templates
  - [ ] 4.3 `POST /api/acm/templates` - upload new template (multipart form)
  - [ ] 4.4 `GET /api/acm/templates/{id}` - get template details with mapping analysis
  - [ ] 4.5 `DELETE /api/acm/templates/{id}` - remove template (prevent deleting active default)
  - [ ] 4.6 `POST /api/acm/templates/{id}/set-default` - set template as active default
- [ ] Task 5: Create frontend template management UI (AC: #8)
  - [ ] 5.1 Create `frontend/src/components/acm/BARTemplateManager.tsx`
  - [ ] 5.2 Template list view with name, version, column count, coverage %, is_default badge
  - [ ] 5.3 Upload button with file input (accepts .xlsx, .xlsm)
  - [ ] 5.4 Template detail view showing column mapping table with gap/warning indicators
  - [ ] 5.5 Set default / delete actions
  - [ ] 5.6 Add template API methods to `frontend/src/lib/api/acm.ts`
  - [ ] 5.7 Integrate into ACM toolbar or settings area (accessible from export dropdown)
- [ ] Task 6: Integration testing
  - [ ] 6.1 Test upload with sample BAR files
  - [ ] 6.2 Test column extraction accuracy
  - [ ] 6.3 Test mapping validation (coverage percentage)
  - [ ] 6.4 Test default template seeding on fresh install
  - [ ] 6.5 Test .xlsm macro-enabled file handling

## Dev Notes

### Critical Context

**BAR = Building Asbestos Register** - Victorian Government mandated Excel format for tracking asbestos in government buildings. Templates have ~47 columns (A-AU) in specific order. See [bar-schema.md](docs/reference/bar-schema.md) for the authoritative column specification.

**Two sample BAR templates exist in the project:**
- `docs/samplePDF/Clutch_Broadmeadows_Police_BAR.xlsx` (1.3 MB)
- `docs/samplePDF/Clucth_Alexandra_District_BAR.xlsm` (630 KB, macro-enabled)

These are real Victorian Government templates with full formatting, data validation dropdowns, and conditional logic.

### Current Excel Export State (E5-S2)

The existing Excel export at `api/routers/acm.py:326-437` only exports **13 columns** (not BAR-compliant). It uses `openpyxl` with basic formatting. This story does NOT modify the export itself - it manages the templates that E5-S4 (Field Mapping) and future BAR export will use.

**Dependency chain:** E5-S2 (Excel Export - DONE) --> **E5-S3 (Template Management)** --> E5-S4 (Field Mapping Config)

### BAR Column Structure (from bar-schema.md)

**47 columns total:** 34 required (A-AH) + 13 recommended (AI-AU)

```
A: Department, B: Agency, C: Sub Agency, D: Site Name, E: Building Name,
F: Building Type, G: Building Address, H: Suburb, I: Postcode,
J: Owned or Leased, K: Building Unique ID, L: Frequency of use,
M: Public Access?, N: Date of Inspection, O: Estimated Year Built,
P: Est. Building Size, Q: Number of Levels, R: Construction Type,
S: Roof Type, T: Internal/External, U: Level, V: Room or Area,
W: Location in Room, X: Specific Item/ACM Name, Y: Friability,
Z: FRIABILITY NAME EXCEL, AA: ACM Product Group,
AB: ACM GROUP NAME EXCEL, AC: ACM Product Type,
AD: NATA Sample number, AE: Sample Result, AF: Identifying Company,
AG: Condition, AH: Disturbance Potential,
AI: Quantity, AJ: Labelled, AK: Label Details,
AL: Hygienist Recommendations, AM: Additional Comments,
AN: PSB ACM ID, AO: Assumed Removed?, AP: Date of Removal,
AQ: Quantity Removed, AR: Removal Notification No,
AS: EPA Certificate No, AT: Removal Comments, AU: Photo Reference
```

### ACM-AI to BAR Field Mapping

The complete field mapping is defined in [bar-schema.md](docs/reference/bar-schema.md#field-mapping). All 47 BAR columns have a corresponding ACM-AI field. Two fields are **derived** (not stored):
- Column Z (`friability_display`) - derived from `friable`
- Column AB (`acm_group_display`) - derived from `acm_product_group`

The template parser must validate that the uploaded template's columns match this mapping.

### Existing Patterns to Follow

**Domain Model Pattern** - Follow `SiteConfig` at `open_notebook/domain/site_config.py`:
```python
class SiteConfig(ObjectModel):
    source_id: str
    department: Optional[str] = None
    # ... fields ...

    @classmethod
    def get_by_source(cls, source_id: str) -> Optional["SiteConfig"]:
        ...

    @classmethod
    def get_templates(cls) -> list:
        ...
```
Follow this ObjectModel pattern for BARTemplate. The `ObjectModel` base class provides `save()`, `delete()`, SurrealDB integration.

**File Upload Pattern** - The project uses FastAPI `UploadFile` for file handling. See source upload patterns in `api/routers/source.py` for multipart form handling.

**openpyxl Template Parsing:**
```python
from openpyxl import load_workbook

def parse_template(file_bytes: bytes, filename: str) -> TemplateParseResult:
    wb = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    # Extract header row (row 1)
    headers = []
    for col in range(1, ws.max_column + 1):
        cell_value = ws.cell(row=1, column=col).value
        if cell_value:
            headers.append({
                "column_letter": get_column_letter(col),
                "column_index": col,
                "header_name": str(cell_value).strip()
            })
    wb.close()
    return TemplateParseResult(columns=headers, ...)
```

**API Client Pattern** - Follow existing acm.ts patterns:
```typescript
// frontend/src/lib/api/acm.ts
templates: {
  list: async (): Promise<BARTemplate[]> => {
    const response = await apiClient.get('/acm/templates');
    return response.data;
  },
  upload: async (file: File): Promise<BARTemplate> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/acm/templates', formData);
    return response.data;
  },
  // ...
}
```

**UI Components Available** (DO NOT create new ones):
- `dialog.tsx` - For template detail/upload modal
- `button.tsx` - Action buttons
- `dropdown-menu.tsx` - Template actions dropdown
- `badge.tsx` - Default template badge, coverage indicator
- `table.tsx` - Column mapping display
- `alert.tsx` - Mapping warnings/gaps
- `scroll-area.tsx` - Scrollable column list (47+ items)

### File Changes Required

| File | Action | Purpose |
|------|--------|---------|
| `open_notebook/domain/bar_template.py` | CREATE | BARTemplate domain model |
| `open_notebook/services/bar_template_parser.py` | CREATE | Template parsing and mapping validation service |
| `migrations/XX.surrealql` | CREATE | bar_template table schema (find next migration number) |
| `api/routers/acm.py` | MODIFY | Add template CRUD endpoints |
| `frontend/src/components/acm/BARTemplateManager.tsx` | CREATE | Template management UI component |
| `frontend/src/lib/api/acm.ts` | MODIFY | Add template API methods |
| `frontend/src/lib/types/acm.ts` | MODIFY | Add BARTemplate TypeScript type |
| `frontend/src/components/acm/ACMToolbar.tsx` | MODIFY | Add "Manage Templates" option to export dropdown |

### Anti-Patterns to Avoid

- **DO NOT** store the full Excel file in the database - only store parsed column metadata
- **DO NOT** modify the existing CSV/Excel export endpoints (E5-S2) - those are separate
- **DO NOT** implement the actual BAR-compliant export in this story - that's E5-S4's job
- **DO NOT** hardcode column mappings in the frontend - the mapping comes from the parsed template + bar-schema.md
- **DO NOT** use xlrd (deprecated) or pandas for Excel parsing - use openpyxl which is already a dependency
- **DO NOT** require macro execution from .xlsm files - just read the header row structure

### Migration Numbering

Check existing migrations to determine the next number:
```bash
ls migrations/*.surrealql
```
Use the next sequential number (e.g., if last is `15.surrealql`, create `16.surrealql`).

### Database Schema for bar_template

```sql
DEFINE TABLE bar_template SCHEMAFULL;
DEFINE FIELD name ON bar_template TYPE string;
DEFINE FIELD version ON bar_template TYPE option<string>;
DEFINE FIELD columns ON bar_template TYPE array;           -- Parsed header columns
DEFINE FIELD column_count ON bar_template TYPE int;
DEFINE FIELD mapping_coverage ON bar_template TYPE float;  -- Percentage (0-100)
DEFINE FIELD unmapped_columns ON bar_template TYPE array;  -- Columns without ACM-AI mapping
DEFINE FIELD is_default ON bar_template TYPE bool DEFAULT false;
DEFINE FIELD file_hash ON bar_template TYPE option<string>;-- SHA256 of uploaded file
DEFINE FIELD original_filename ON bar_template TYPE option<string>;
DEFINE FIELD created_at ON bar_template TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON bar_template TYPE datetime DEFAULT time::now();
DEFINE INDEX template_default ON bar_template FIELDS is_default;
```

### Dependencies

- **Depends on:** E5-S2 (Excel Export) - DONE
- **Blocks:** E5-S4 (Export Field Mapping Configuration)
- **Uses:** openpyxl (already installed)

### References

- [BAR Schema Reference](docs/reference/bar-schema.md) - Authoritative column definitions and field mappings
- [Architecture Section 6.1](../_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md) - AG Grid column groups
- [Architecture Section 4.2](../_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md) - BARExportOptions TypeScript interface
- [E5-S2 Tech Spec](docs/sprint-artifacts/tech-spec-e5-s2-excel-export.md) - Previous story implementation details
- [Sprint Change Proposal CP#3](../_bmad-output/sprint-change-proposal-20260204.md) - BAR format requirements
- [SiteConfig domain model](open_notebook/domain/site_config.py) - Template management pattern to follow
- [ACM API router](api/routers/acm.py) - Existing export endpoints (lines 235-437, 761-947)
- [Sample BAR: Broadmeadows](docs/samplePDF/Clutch_Broadmeadows_Police_BAR.xlsx)
- [Sample BAR: Alexandra](docs/samplePDF/Clucth_Alexandra_District_BAR.xlsm)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
