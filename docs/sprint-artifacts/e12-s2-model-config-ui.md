# Story E12-S2: AI Model Configuration UI

**Epic:** E12 — Extraction Settings & Configuration UI
**Priority:** P1
**Status:** ready-for-dev
**Change Proposal:** SCP-20260207 (2026-02-07)
**Depends on:** E12-S1 (done)
**Blocks:** none

---

## User Story

**As a** user (operator or administrator),
**I want to** configure which AI models are used for each extraction stage,
**So that** I can balance cost, speed, and accuracy per operation without changing code.

---

## Background

The ACM-AI extraction pipeline runs across multiple AI-driven stages, each with different latency and token-cost profiles. Currently, model assignments are managed directly in SurrealDB — the `model` table stores available models and the `open_notebook:default_models` record stores which model is used for each operation. There is no UI surface for operators to adjust these assignments.

This story adds an "AI Models" settings page (or sub-section) under the CONFIGURE section, extending the `api/routers/settings.py` router created in E12-S1. It leverages the existing model registry so operators can point different extraction stages to different models without SurrealDB queries.

**Critical data model note:** Models are stored in SurrealDB `model` table — they are NOT read from `.env` at runtime. The `.env` `DEFAULT_EXTRACTION_MODEL` is only used during initial provisioning/seeding. To change the active model for a stage, both the relevant `model` table record and `open_notebook:default_models` must be updated.

**Prerequisite (must be done first):**
- E12-S1: Extraction Method Settings Page (drafted) — provides the `api/routers/settings.py` router scaffold and the `settingsApi.ts` frontend client that this story extends.

---

## Acceptance Criteria

### Settings Page

- [ ] Settings page accessible under the CONFIGURE section at route `/settings/models`
- [ ] Navigation entry: CONFIGURE > "AI Models" (alongside "Extraction" from E12-S1)
- [ ] Page title: "AI Model Configuration"

### Model Selection Per Extraction Stage

- [ ] The following extraction stages are listed, each with a model selector:
  - **Structure Analysis** — E1-S16 (TOC & document structure)
  - **Building Inventory** — E1-S17 (building metadata compilation)
  - **ACM Extraction** — E1-S3 (main per-building extraction)
  - **Page Tagging** — E1-S18 (section classification)
  - **Product Classification** — E1-S9 (taxonomy classification)
  - **Corrective Validation** — E1-S15 (RAG validation loop)
- [ ] Each stage selector is a dropdown populated from the `model` table via `GET /api/models`
- [ ] Current model assignment is loaded from `open_notebook:default_models` on page mount
- [ ] Stage displays the currently assigned model name and provider (e.g., "claude-3-5-haiku-20241022 via Anthropic")

### Cost and Speed Indicators

- [ ] Each model option in the dropdown shows a cost/speed tier badge:
  - Fast / Low Cost (e.g., Haiku-class models)
  - Balanced (e.g., Sonnet-class models)
  - Thorough / High Cost (e.g., Opus-class models)
- [ ] Tier is derived from a static mapping or a `tier` field on the model record
- [ ] Tooltip on each tier badge explains the trade-off

### Test Button

- [ ] Each stage row has a "Test" button
- [ ] Clicking "Test" runs a minimal extraction on a pre-defined sample page using the selected model
- [ ] Test result shown inline: success with latency ms, or error with message
- [ ] Test button disabled until a model is selected

### Settings Persistence

- [ ] "Save Configuration" button — persists all stage-to-model assignments
- [ ] Save updates `open_notebook:default_models` via PUT `/api/settings/models`
- [ ] Success toast on save; error toast on failure
- [ ] "Reset to Defaults" button with confirmation dialog — restores original seeded assignments
- [ ] Unsaved changes indicator when form is dirty

### UX

- [ ] Loading skeleton while fetching model list and current assignments
- [ ] Error state with retry if `GET /api/models` or `GET /api/settings/models` fails
- [ ] If no models are configured in the registry, a warning banner is shown: "No models available. Add models in the Models section before configuring stages."

---

## Technical Notes

### Backend API (extend `api/routers/settings.py` from E12-S1)

New endpoints added to the existing `settings.py` router:

```
GET  /api/settings/models      → Returns ModelConfigSettings
PUT  /api/settings/models      → Updates ModelConfigSettings, returns saved record
```

`ModelConfigSettings` Pydantic model:

```python
class StageModelAssignment(BaseModel):
    stage: str                  # e.g. "structure_analysis"
    model_id: str               # SurrealDB record ID, e.g. "model:h2ucwvxqwo76y7vqw1bz"
    model_display_name: str     # populated on read, e.g. "claude-3-5-haiku-20241022"

class ModelConfigSettings(BaseModel):
    stage_assignments: list[StageModelAssignment]
```

Stage keys (used as `stage` values):
- `structure_analysis`
- `building_inventory`
- `acm_extraction`
- `page_tagging`
- `product_classification`
- `corrective_validation`

SurrealDB persistence: update relevant fields in `open_notebook:default_models`. This record already exists and is the canonical source for runtime model routing.

Domain model location: extend `open_notebook/domain/settings.py` (created in E12-S1).

### Existing model API

The `model` table and its REST endpoint (`GET /api/models`) already exist. No new backend model infrastructure is required — this story only reads from the existing registry.

Confirmed working model (for reference in tests): `model:h2ucwvxqwo76y7vqw1bz` = `claude-3-5-haiku-20241022` via direct Anthropic.

OpenRouter note: Qwen 2.5 72B and similar OpenRouter models may not expose `structured-outputs` via all providers (Novita, DeepInfra). Prefer models with confirmed structured output support (Claude family, Llama 3.3, Mistral Nemo) for extraction stages.

### Frontend Location

```
frontend/src/app/(dashboard)/settings/models/page.tsx
```

Component: `frontend/src/components/settings/ModelConfigForm.tsx`

API client: Extend `frontend/src/lib/api/settingsApi.ts` (created in E12-S1) with model config endpoints.

TypeScript types: Extend `frontend/src/lib/types/settings.ts` with `ModelConfigSettings`, `StageModelAssignment`.

### Sidebar Integration

The CONFIGURE section in `AppSidebar.tsx` already exists (added in E14-S2, extended by E12-S1). Add:

```tsx
{ label: "AI Models", href: "/settings/models", icon: <SparklesIcon /> }
```

### State Management

Use React Hook Form with Zod for the settings form. Use React Query for data fetching (`useQuery` for GET, `useMutation` for PUT). Follows patterns established in E12-S1 (ExtractionSettingsForm) and E1-S8 (SiteConfigForm).

---

## Key Files to Create/Modify

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/settings/models/page.tsx` | New settings page (route) |
| `frontend/src/components/settings/ModelConfigForm.tsx` | New form component with per-stage model selectors |
| `frontend/src/lib/api/settingsApi.ts` | Extend with `getModelConfig`, `updateModelConfig` |
| `frontend/src/lib/types/settings.ts` | Add `ModelConfigSettings`, `StageModelAssignment` types |
| `api/routers/settings.py` | Add GET/PUT `/api/settings/models` endpoints |
| `open_notebook/domain/settings.py` | Add `ModelConfigSettings` Pydantic model |
| `frontend/src/components/layout/AppSidebar.tsx` | Add "AI Models" nav item under CONFIGURE |

---

## Dependencies

- **Requires:**
  - E12-S1: Extraction Method Settings Page (drafted) — must be implemented first; provides `api/routers/settings.py`, `settingsApi.ts`, and the settings page structure
- **Blocks:** none

---

## Estimated Effort

M (Medium) — New settings page and form component. Backend is additive to the router scaffold from E12-S1. Complexity is in the per-stage model selector UX and the test button integration with the existing extraction infrastructure.

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
