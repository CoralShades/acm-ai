# Story E12-S1: Extraction Method Settings Page

**Epic:** E12 — Extraction Settings & Configuration UI
**Priority:** P1
**Status:** done
**Change Proposal:** SCP-20260207 (2026-02-07)
**Blocks:** E12-S2, E12-S3

---

## User Story

**As a** user (operator or administrator),
**I want** a settings page to configure extraction methods and document intelligence pipeline options,
**So that** I can control how SAMP documents are processed without requiring developer intervention or code changes.

---

## Background

The document intelligence pipeline introduced in E1-S16 through E1-S19 added four new pre-extraction stages (TOC extraction, building inventory compilation, page-level section tagging, and enhanced metadata extraction). All four backend stories are now done. However, operators currently have no UI surface to toggle these pipeline stages, switch between extraction methods (MinerU / Docling / Hybrid), or manage per-source overrides.

This story delivers the primary settings page at `/settings/extraction`. It is the foundation for E12-S2 (AI Model Configuration) and E12-S3 (Processing Options), which extend the same settings area.

**Prerequisite backend work (all DONE):**
- E1-S16: Document Structure & TOC Extraction
- E1-S17: Building Inventory Compilation
- E1-S18: Page-Level Section Tagging
- E1-S19: Document Metadata Extraction Enhancement

---

## Acceptance Criteria

### Settings Page

- [ ] Settings page accessible via navigation under CONFIGURE section at route `/settings/extraction`
- [ ] Navigation entry: CONFIGURE > "Extraction"
- [ ] Page title: "Extraction Settings"

### Extraction Method Selection

- [ ] Radio group for extraction method: **MinerU** / **Docling** / **Hybrid** (default: Hybrid)
- [ ] Short description shown below each option:
  - MinerU: "ML-based table extraction, best accuracy for complex merged cells"
  - Docling: "Fast document parsing, good for standard table layouts"
  - Hybrid: "MinerU first, automatic fallback to Docling if MinerU fails (recommended)"
- [ ] Current selection persisted on save

### Fallback Behavior

- [ ] Toggle: "Enable automatic fallback if primary extraction method fails" (default: enabled)
- [ ] Disabled when Hybrid is selected (fallback is implicit in Hybrid mode)
- [ ] Help tooltip explaining the fallback chain

### Document Intelligence Pipeline Toggles

- [ ] Section heading: "Document Intelligence Stages"
- [ ] Toggle row for each stage — label, description, and on/off switch:
  - **TOC & Structure Extraction** (E1-S16): "Extract table of contents and section hierarchy before processing. Improves accuracy on multi-section SAMPs."
  - **Building Inventory Compilation** (E1-S17): "Compile a building inventory with page ranges before extraction. Enables targeted per-building extraction." Disabled when TOC extraction is off (dependency).
  - **Page-Level Section Tagging** (E1-S18): "Tag each page with its section type and confidence score. Allows section-specific extraction strategies."
  - **Document Metadata Enhancement** (E1-S19): "Extract comprehensive metadata (address, consultant, dates) from cover page and headers. Auto-fills BAR export fields."
- [ ] Dependency warning shown when attempting to enable Building Inventory without TOC extraction enabled

### Settings Persistence

- [ ] Settings saved to SurrealDB `extraction_settings` table via PUT `/api/settings/extraction`
- [ ] Settings loaded on page mount via GET `/api/settings/extraction`
- [ ] "Save Settings" button — shows success toast on save
- [ ] "Reset to Defaults" button with confirmation dialog

### Per-Source Override

- [ ] Checkbox: "Allow per-source override of these settings" (default: enabled)
- [ ] When enabled, source-level extraction options (e.g., in Upload Wizard) can diverge from global defaults
- [ ] When disabled, global settings are enforced for all sources

### UX

- [ ] Loading skeleton while fetching current settings
- [ ] Error state with retry if API unreachable
- [ ] Unsaved changes indicator when form is dirty (e.g., asterisk in page title or banner)
- [ ] Form resets to last saved state on navigation away if unsaved (with confirmation dialog)

---

## Technical Notes

### Backend API (to be created as part of this story)

New router: `api/routers/settings.py`

```
GET  /api/settings/extraction      → Returns ExtractionSettings
PUT  /api/settings/extraction      → Updates ExtractionSettings, returns saved record
```

`ExtractionSettings` Pydantic model fields:
```python
class ExtractionSettings(BaseModel):
    extraction_method: Literal["mineru", "docling", "hybrid"] = "hybrid"
    fallback_enabled: bool = True
    toc_extraction_enabled: bool = True
    building_inventory_enabled: bool = True
    page_tagging_enabled: bool = True
    metadata_enhancement_enabled: bool = True
    per_source_override_allowed: bool = True
```

Domain model location: `open_notebook/domain/settings.py`

SurrealDB table: `extraction_settings` — single global record (key: `extraction_settings:global`)

### Frontend Location

```
frontend/src/app/(dashboard)/settings/extraction/page.tsx
```

Component: `frontend/src/components/settings/ExtractionSettingsForm.tsx`

API client: `frontend/src/lib/api/settingsApi.ts`

### Sidebar Integration

The CONFIGURE section in `AppSidebar.tsx` already exists (added in E14-S2). Add navigation entry:

```tsx
{ label: "Extraction", href: "/settings/extraction", icon: <CogIcon /> }
```

### State Management

Use React Hook Form with Zod for the settings form. Use React Query for fetching and mutating settings. This matches patterns established in E1-S8 (SiteConfigForm) and E7-S7 (Upload Config).

### Dependency Rule (Building Inventory requires TOC)

Enforce in the form: if `toc_extraction_enabled` is toggled off, `building_inventory_enabled` must also be disabled with an inline warning:

> "Building Inventory requires TOC & Structure Extraction. Disabling TOC will also disable Building Inventory."

---

## Key Files to Create/Modify

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/settings/extraction/page.tsx` | New settings page (route) |
| `frontend/src/components/settings/ExtractionSettingsForm.tsx` | New form component |
| `frontend/src/lib/api/settingsApi.ts` | New API client for settings endpoints |
| `frontend/src/lib/types/settings.ts` | TypeScript types for ExtractionSettings |
| `api/routers/settings.py` | New router with GET/PUT `/api/settings/extraction` |
| `open_notebook/domain/settings.py` | New ExtractionSettings Pydantic domain model |
| `migrations/XX_extraction_settings.surrealql` | New migration — `extraction_settings` table |
| `api/main.py` | Register `settings` router |
| `frontend/src/components/layout/AppSidebar.tsx` | Add "Extraction" nav item under CONFIGURE |

---

## Dependencies

- **Requires (all DONE):**
  - E1-S16: Document Structure & TOC Extraction (done)
  - E1-S17: Building Inventory Compilation (done)
  - E1-S18: Page-Level Section Tagging (done)
  - E1-S19: Document Metadata Extraction Enhancement (done)
- **Blocks:**
  - E12-S2: AI Model Configuration UI (needs settings page scaffold and `settings.py` router)
  - E12-S3: Processing Options Configuration (needs settings page scaffold and `settings.py` router)

---

## Estimated Effort

M (Medium) — New settings page with form, new backend router, new SurrealDB migration. No novel infrastructure; follows established patterns from E1-S8 (SiteConfigForm) and E14-S2 (sidebar navigation).

---

## Dev Agent Record

> This section is populated by the implementing dev agent upon story completion.

### Implementation Notes

_To be filled in during implementation._

### Build Verification

| Check | Status |
|-------|--------|
| `npm run build` (frontend) | - |
| `uv run ruff check .` (backend) | - |
| `uv run pytest` (backend) | - |

### Files Verified

_List of files confirmed to exist after implementation._

### Pages Verified

_List of URLs tested in browser after implementation._

### Completion Date

_To be filled in upon story completion._
