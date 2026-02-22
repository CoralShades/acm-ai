# Story E12-S3: Processing Options Configuration

**Epic:** E12 — Extraction Settings & Configuration UI
**Priority:** P1
**Status:** ready-for-dev
**Change Proposal:** SCP-20260207 (2026-02-07)
**Depends on:** E12-S1 (done)
**Blocks:** none

---

## User Story

**As a** user (operator or administrator),
**I want to** configure extraction processing parameters such as chunk size, confidence thresholds, retry attempts, and timeout values,
**So that** I can tune extraction performance and reliability for different document types without code changes.

---

## Background

The ACM-AI extraction pipeline has several tuneable runtime parameters — chunk size for page batching, confidence thresholds for MinerU table detection, retry limits for corrective validation, batch size for bulk operations, and timeout values per page and per document. Currently these are hardcoded constants scattered across the extractors and pipeline code.

This story adds a "Processing" settings page under the CONFIGURE section, extending the `api/routers/settings.py` router created in E12-S1. Changes to processing configuration take effect on the next extraction run — no restart is required.

**Prerequisite (must be done first):**
- E12-S1: Extraction Method Settings Page (drafted) — provides the `api/routers/settings.py` router scaffold and the `settingsApi.ts` frontend client that this story extends.

---

## Acceptance Criteria

### Settings Page

- [ ] Settings page accessible under the CONFIGURE section at route `/settings/processing`
- [ ] Navigation entry: CONFIGURE > "Processing" (alongside "Extraction" and "AI Models")
- [ ] Page title: "Processing Configuration"

### Processing Parameters

- [ ] **Chunk Size** — Number input, range 2000–8000 tokens, default 4000
  - Label: "Page Chunk Size (tokens)"
  - Help text: "Maximum tokens sent per LLM call during page-level extraction. Larger chunks reduce API calls but may exceed model context limits."
- [ ] **Confidence Threshold** — Decimal number input, range 0.0–1.0 (step 0.05), default 0.7
  - Label: "MinerU Table Confidence Threshold"
  - Help text: "Minimum confidence score for MinerU to accept a detected table. Lower values extract more tables but may include false positives."
- [ ] **Max Correction Attempts** — Integer input, range 1–5, default 3
  - Label: "Max Corrective Validation Attempts"
  - Help text: "How many times the corrective RAG validation loop (E1-S15) may attempt to fix an extraction before accepting the result."
- [ ] **Batch Size** — Integer input, range 1–10, default 3
  - Label: "Batch Size for Bulk Operations"
  - Help text: "Number of documents processed concurrently during bulk extraction. Higher values are faster but increase memory and API usage."

### Timeout Settings

- [ ] **Per-Page Timeout** — Integer input, range 10–120 seconds, default 60
  - Label: "Per-Page Extraction Timeout (seconds)"
  - Help text: "Maximum time allowed for extracting a single document page before the stage is marked as timed out."
- [ ] **Total Document Timeout** — Integer input, range 1–30 minutes, default 15
  - Label: "Total Document Timeout (minutes)"
  - Help text: "Maximum time allowed for the full extraction pipeline on a single document. Applies to all stages combined."

### Output Preferences

- [ ] **Store Raw JSON** — Toggle (default: enabled)
  - Label: "Store Raw Extraction JSON"
  - Help text: "Persist the verbatim Stage 1 extraction output for audit and debugging. Disable to save storage on high-volume deployments."
- [ ] **Auto-Classify** — Toggle (default: enabled)
  - Label: "Auto-Run Product Classification"
  - Help text: "Automatically run taxonomy classification (E1-S9) after extraction completes. Disable to classify manually."
- [ ] **Auto-Normalize** — Toggle (default: enabled)
  - Label: "Auto-Run Wording Normalization"
  - Help text: "Automatically normalize consultant recommendations (E1-S12) after extraction. Disable for manual review workflows."

### Presets

- [ ] Three preset buttons apply a named configuration to all fields:
  - **Fast** — Chunk: 3000, Confidence: 0.6, Max Corrections: 1, Batch: 5, Page Timeout: 30s, Doc Timeout: 5min, Store Raw: off, Auto-Classify: on, Auto-Normalize: on
  - **Balanced** (default) — Chunk: 4000, Confidence: 0.7, Max Corrections: 3, Batch: 3, Page Timeout: 60s, Doc Timeout: 15min, Store Raw: on, Auto-Classify: on, Auto-Normalize: on
  - **Thorough** — Chunk: 6000, Confidence: 0.8, Max Corrections: 5, Batch: 1, Page Timeout: 120s, Doc Timeout: 30min, Store Raw: on, Auto-Classify: on, Auto-Normalize: on
- [ ] Selecting a preset populates all fields but does not auto-save
- [ ] Active preset badge shown if current values match a preset exactly

### Settings Persistence

- [ ] "Save Configuration" button — persists settings via PUT `/api/settings/processing`
- [ ] Settings loaded on page mount via GET `/api/settings/processing`
- [ ] Success toast on save; error toast on failure
- [ ] "Reset to Defaults" button with confirmation dialog — restores Balanced preset values
- [ ] Unsaved changes indicator when form is dirty

### UX

- [ ] Loading skeleton while fetching current settings
- [ ] Error state with retry if API unreachable
- [ ] Input validation with inline error messages:
  - Chunk size outside 2000–8000 → "Must be between 2000 and 8000 tokens"
  - Confidence outside 0.0–1.0 → "Must be between 0.0 and 1.0"
  - Non-integer where integer required → "Must be a whole number"
- [ ] Changes take effect on the next extraction run (no restart required); this is noted in a page-level info banner

---

## Technical Notes

### Backend API (extend `api/routers/settings.py` from E12-S1)

New endpoints added to the existing `settings.py` router:

```
GET  /api/settings/processing      → Returns ProcessingConfig
PUT  /api/settings/processing      → Updates ProcessingConfig, returns saved record
```

`ProcessingConfig` Pydantic model:

```python
class ProcessingConfig(BaseModel):
    chunk_size: int = 4000
    mineru_confidence_threshold: float = 0.7
    max_correction_attempts: int = 3
    batch_size: int = 3
    per_page_timeout_seconds: int = 60
    total_document_timeout_minutes: int = 15
    store_raw_json: bool = True
    auto_classify: bool = True
    auto_normalize: bool = True
```

SurrealDB persistence: single global record `processing_config:global` in a new `processing_config` table.

Domain model location: extend `open_notebook/domain/settings.py` (created in E12-S1) with `ProcessingConfig`.

### SurrealDB Migration

New migration file (increment next available number):

```sql
-- processing_config table
DEFINE TABLE processing_config SCHEMAFULL;
DEFINE FIELD chunk_size                    ON processing_config TYPE int;
DEFINE FIELD mineru_confidence_threshold   ON processing_config TYPE float;
DEFINE FIELD max_correction_attempts       ON processing_config TYPE int;
DEFINE FIELD batch_size                    ON processing_config TYPE int;
DEFINE FIELD per_page_timeout_seconds      ON processing_config TYPE int;
DEFINE FIELD total_document_timeout_minutes ON processing_config TYPE int;
DEFINE FIELD store_raw_json                ON processing_config TYPE bool;
DEFINE FIELD auto_classify                 ON processing_config TYPE bool;
DEFINE FIELD auto_normalize                ON processing_config TYPE bool;

-- Seed defaults (Balanced preset)
INSERT INTO processing_config {
    id: processing_config:global,
    chunk_size: 4000,
    mineru_confidence_threshold: 0.7,
    max_correction_attempts: 3,
    batch_size: 3,
    per_page_timeout_seconds: 60,
    total_document_timeout_minutes: 15,
    store_raw_json: true,
    auto_classify: true,
    auto_normalize: true
};
```

### Frontend Location

```
frontend/src/app/(dashboard)/settings/processing/page.tsx
```

Component: `frontend/src/components/settings/ProcessingConfigForm.tsx`

API client: Extend `frontend/src/lib/api/settingsApi.ts` (created in E12-S1) with processing config endpoints.

TypeScript types: Extend `frontend/src/lib/types/settings.ts` with `ProcessingConfig` type and a `PROCESSING_PRESETS` constant object.

### Sidebar Integration

The CONFIGURE section in `AppSidebar.tsx` already exists (added in E14-S2, extended by E12-S1 and E12-S2). Add:

```tsx
{ label: "Processing", href: "/settings/processing", icon: <SlidersIcon /> }
```

### State Management

Use React Hook Form with Zod for validation. Use React Query (`useQuery` for GET, `useMutation` for PUT). Follows patterns from E12-S1 and E12-S2.

### Zod Schema (reference)

```ts
const processingConfigSchema = z.object({
  chunk_size: z.number().int().min(2000).max(8000),
  mineru_confidence_threshold: z.number().min(0).max(1),
  max_correction_attempts: z.number().int().min(1).max(5),
  batch_size: z.number().int().min(1).max(10),
  per_page_timeout_seconds: z.number().int().min(10).max(120),
  total_document_timeout_minutes: z.number().int().min(1).max(30),
  store_raw_json: z.boolean(),
  auto_classify: z.boolean(),
  auto_normalize: z.boolean(),
});
```

---

## Key Files to Create/Modify

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/settings/processing/page.tsx` | New settings page (route) |
| `frontend/src/components/settings/ProcessingConfigForm.tsx` | New form component with number inputs, toggles, and preset buttons |
| `frontend/src/lib/api/settingsApi.ts` | Extend with `getProcessingConfig`, `updateProcessingConfig` |
| `frontend/src/lib/types/settings.ts` | Add `ProcessingConfig` type and `PROCESSING_PRESETS` constant |
| `api/routers/settings.py` | Add GET/PUT `/api/settings/processing` endpoints |
| `open_notebook/domain/settings.py` | Add `ProcessingConfig` Pydantic model |
| `migrations/XX_processing_config.surrealql` | New migration — `processing_config` table with seeded defaults |
| `frontend/src/components/layout/AppSidebar.tsx` | Add "Processing" nav item under CONFIGURE |

---

## Dependencies

- **Requires:**
  - E12-S1: Extraction Method Settings Page (drafted) — must be implemented first; provides `api/routers/settings.py`, `settingsApi.ts`, and the settings page structure
- **Blocks:** none

---

## Estimated Effort

M (Medium) — New settings page with form validation, number inputs, presets logic, and a new SurrealDB migration. Additive to E12-S1 router scaffold. No novel infrastructure; follows established patterns.

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
