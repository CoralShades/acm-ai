# Story E5-S3: BAR Template Management

**Epic:** E5 — Export Functionality
**Priority:** P0 (epic promoted from P1)
**Status:** done
**Change Proposal:** Sprint Change Proposal CP#3 (2026-02-04)

---

## User Story

**As a** user managing ACM exports,
**I want to** upload official Victorian Government BAR Excel templates and manage versioning,
**So that** all exports are guaranteed to be compliant with the current BAR specification.

---

## Background

E5-S2 (Excel BAR Export) is complete, producing `.xlsx` files with column headers hardcoded from the known BAR specification. However, the Victorian Government periodically updates BAR templates. This story introduces a proper template management system: upload the official `.xlsm`/`.xlsx` BAR template, extract its column structure, validate the ACM-AI schema maps to all required columns, and version-track templates so exports always use the active version.

This is a prerequisite for E5-S4 (Export Field Mapping Configuration), which configures how ACM-AI internal fields map to the discovered template columns.

**Dependency chain:**
```
E5-S2 (done) → E5-S3 (this story) → E5-S4 (Field Mapping)
```

---

## Acceptance Criteria

- [ ] Admin UI accessible at `/settings/bar-templates` (or nested under Settings)
- [ ] Drag-and-drop upload zone for `.xlsm` / `.xlsx` BAR template files
- [ ] On upload, system parses template header row(s) to extract all column names and letters
- [ ] Validation report shows: columns found, columns mapped in ACM-AI, unmapped columns (gaps)
- [ ] Template stored in SurrealDB `bar_template` table with version metadata
- [ ] Version history list: shows all uploaded templates with upload date, filename, column count, active indicator
- [ ] "Set Active" button to designate which template version is used for exports
- [ ] Preview panel showing extracted column structure (column letter, column name, field type if detectable)
- [ ] Default template bundled with system (Clucth_Alexandra_District_BAR.xlsm seed)
- [ ] API endpoints:
  - `GET /api/bar-templates` — list all template versions
  - `POST /api/bar-templates/upload` — upload new template
  - `GET /api/bar-templates/{id}` — get template metadata and column structure
  - `PUT /api/bar-templates/{id}/activate` — set as active template
  - `DELETE /api/bar-templates/{id}` — delete non-active template version
- [ ] Warning banner if no template is active
- [ ] Export endpoints (`/api/acm/export/excel`, `/api/acm/export/csv`) respect active template column order

---

## Technical Notes

### Backend: Pydantic Model

```python
# open_notebook/domain/bar_template.py
class BARTemplateColumn(BaseModel):
    column_letter: str        # e.g., "A", "B", "AA"
    column_name: str          # Header text from template
    field_type: str | None    # Inferred: "text", "enum", "date", "number"
    is_required: bool = False

class BARTemplate(BaseModel):
    id: str | None = None
    filename: str
    version_label: str        # e.g., "v2024.1" or derived from filename
    uploaded_at: datetime
    is_active: bool = False
    column_count: int
    columns: list[BARTemplateColumn]
    raw_header_row: list[str]  # Verbatim header values for audit
    notes: str | None = None
```

### Backend: SurrealDB Table

```sql
-- migrations/XX_bar_template.surrealql
DEFINE TABLE bar_template SCHEMAFULL;
DEFINE FIELD filename ON bar_template TYPE string;
DEFINE FIELD version_label ON bar_template TYPE string;
DEFINE FIELD uploaded_at ON bar_template TYPE datetime;
DEFINE FIELD is_active ON bar_template TYPE bool DEFAULT false;
DEFINE FIELD column_count ON bar_template TYPE int;
DEFINE FIELD columns ON bar_template TYPE array;
DEFINE FIELD raw_header_row ON bar_template TYPE array;
DEFINE FIELD notes ON bar_template TYPE option<string>;
DEFINE INDEX bar_template_active ON bar_template COLUMNS is_active;
```

### Backend: Template Parsing

```python
# api/services/bar_template_service.py
import openpyxl

def parse_bar_template(file_bytes: bytes, filename: str) -> BARTemplate:
    """
    Open the .xlsx/.xlsm workbook, find the register sheet,
    read the first non-empty header row, extract column letters + names.
    """
    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    # Locate register sheet — look for sheet named "Register" or first sheet
    ws = wb["Register"] if "Register" in wb.sheetnames else wb.active
    # Read header row (skip rows until non-empty found, max scan 5 rows)
    ...
```

### Backend: Router

```python
# api/routers/bar_templates.py
router = APIRouter(prefix="/api/bar-templates", tags=["bar-templates"])

@router.post("/upload")
async def upload_template(file: UploadFile = File(...)) -> BARTemplate:
    ...

@router.get("")
async def list_templates() -> list[BARTemplate]:
    ...

@router.put("/{template_id}/activate")
async def activate_template(template_id: str) -> BARTemplate:
    # Deactivate current active, set new one
    ...
```

Add router to `api/main.py`.

### Frontend: Settings Page

```
frontend/src/app/(dashboard)/settings/bar-templates/page.tsx
frontend/src/components/settings/BARTemplateUploader.tsx
frontend/src/components/settings/BARTemplateVersionList.tsx
frontend/src/components/settings/BARTemplateColumnPreview.tsx
```

- Use `react-dropzone` (already a project dependency via E7-S2) for the upload zone
- React Query mutation for upload, React Query query for list
- Column preview: virtual list (AG Grid or simple table) for templates with 47+ columns
- "Set Active" uses optimistic update — show spinner on button, revert on error

### Integration with Export

The Excel/CSV export endpoints should call `GET /api/bar-templates?active=true` to determine column order. If no active template, fall back to hardcoded BAR column order from E5-S2 (backward compatible).

---

## Key File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `open_notebook/domain/bar_template.py` | NEW | `BARTemplate`, `BARTemplateColumn` Pydantic models |
| `api/services/bar_template_service.py` | NEW | Template parsing, activation logic |
| `api/routers/bar_templates.py` | NEW | REST endpoints for template management |
| `api/main.py` | MODIFY | Register `bar_templates` router |
| `migrations/XX_bar_template.surrealql` | NEW | SurrealDB schema for `bar_template` table |
| `frontend/src/app/(dashboard)/settings/bar-templates/page.tsx` | NEW | Settings page route |
| `frontend/src/components/settings/BARTemplateUploader.tsx` | NEW | Drag-drop upload component |
| `frontend/src/components/settings/BARTemplateVersionList.tsx` | NEW | Version history list with Set Active |
| `frontend/src/components/settings/BARTemplateColumnPreview.tsx` | NEW | Column structure preview panel |
| `frontend/src/lib/api/bar-templates.ts` | NEW | API client functions |

---

## Dependencies

- **Requires:** E5-S2 (Excel BAR Export — done)
- **Blocks:** E5-S4 (Export Field Mapping Configuration)

---

## Estimated Effort

M (Medium) — New backend service with file parsing, new SurrealDB table, and a multi-component admin UI. Core complexity is the template parsing (openpyxl header scan) and the activation toggle logic (ensure only one active template at a time).

---

## Dev Agent Record

> To be filled in by implementing agent.

- [ ] Build status: —
- [ ] Files verified: —
- [ ] Pages verified: —
- [ ] Notes: —
