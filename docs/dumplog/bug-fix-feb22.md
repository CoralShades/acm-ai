# Bug Triage & Fix Plan — ACM-AI

## Context
Demi identified 11 bugs during manual testing (9 unique after deduplication). These range from critical extraction pipeline failures when switching AI models, to UI regressions and branding updates. This plan maps each bug to either an existing story or a new bug-fix story, provides concrete file-level fixes, and defines implementation order.

---

## Bug-to-Story Mapping

| # | Bug | Size | Story | Epic |
|---|-----|------|-------|------|
| 1+9 | Multi-model compatibility + document format | **XL** | **NEW: E1-S28 through E1-S30** (3 stories) | Epic 1 |
| 2 | Blank loading spinner | **S** | **NEW: BUG-auth-loading-ux** | Epic 14 |
| 3/5 | No navigation after upload | **S** | **NEW: BUG-post-upload-navigation** | Epic 7 |
| 4/6 | Extraction progress panel | **M** | **Augment E15-S2** + **NEW: BUG-extraction-progress-fix** | Epic 15 |
| 7 | Column naming regressions | **S** | **NEW: BUG-grid-column-fixes** | Epic 2 |
| 8 | Negative results regression | **M** | **NEW: BUG-negative-results-regression** | Epic 1 |
| 10 | Query data undefined | **XS** | **NEW: BUG-site-config-query-fix** | Standalone |
| 11 | UI/UX polish + VAEA branding | **S** | **NEW: BUG-ui-ux-vaea-branding** | Epic 14 |

---

## Implementation Order (Priority)

### Phase 1: Quick Wins (1-2 hours total)
These are single-file fixes that unblock testing immediately.

#### Story: BUG-site-config-query-fix (XS)
**File:** `frontend/src/lib/api/acm.ts:145`
```
- return response.data.templates
+ return response.data.templates ?? []
```

#### Story: BUG-grid-column-fixes (S)
**Files to modify:**
1. `frontend/src/components/acm/ACMGrid.tsx`
   - Line 214: `headerName: 'Building ID'` → `'Building Code'`
   - Line 215: `headerTooltip` → `'Building code identifier'`
   - Lines 269-276: Replace `material_description` column with merged column:
     - `headerName: 'ACM Product Type'`
     - `valueGetter`: return `acm_product_type || material_description`
     - `headerTooltip: 'AI-classified product type (falls back to raw description)'`
   - Lines 285-293: Remove `risk_status` column definition entirely (keep backend field)
2. `api/routers/acm.py`
   - Line 294 (CSV): `"Building ID"` → `"Building Code"`
   - Line 304 (CSV): `"Material Condition"` → `"Condition"`
   - Line 409 (Excel): `"Building ID"` → `"Building Code"`

#### Story: BUG-post-upload-navigation (S)
**Files to modify:**
1. `frontend/src/components/sources/AddSourceDialog.tsx`
   - After line 372 (after `submitSingleSource` completes): add `router.push(\`/sources/\${createdSource.id}\`)`
   - Import `useRouter` from `next/navigation`
2. `frontend/src/components/upload/UploadProgressStep.tsx`
   - Line 204: Change `handleDone()` to navigate to the specific source if only one was uploaded

#### Story: BUG-ui-ux-vaea-branding (S)
**Files to modify:**
1. `frontend/src/config/branding.ts:16` — `name: 'ACM-AI'` → `name: 'VAEA | ACM AI'`
2. `frontend/public/manifest.json` — Update `name` and `short_name`
3. Replace these files with converted versions of `docs/vaea-assets/VAEA_Ripple2_FavIcon_0.png`:
   - `frontend/public/logo.png` (32x32 or 64x64)
   - `frontend/public/icon.png` (192x192 for manifest)
   - `frontend/public/icon.svg` (SVG conversion)
   - `frontend/public/favicon.ico` (ICO conversion)
4. `frontend/src/app/(dashboard)/sources/[id]/page.tsx:343` — Add `overflow-x-auto` to TabsList wrapper
5. `frontend/src/components/ui/command.tsx:93` — Increase `max-h-[300px]` to `max-h-[400px]` or `max-h-[min(400px,60vh)]`

---

### Phase 2: Frontend UX Fixes (2-3 hours)

#### Story: BUG-auth-loading-ux (S)
**Root cause:** `use-auth.ts:63` blocks render during Zustand hydration + sequential auth API calls.

**Files to modify:**
1. Create `frontend/src/app/(dashboard)/loading.tsx` — instant Next.js skeleton UI (not blank spinner)
2. `frontend/src/lib/hooks/use-auth.ts`
   - Cache `authRequired` result in persisted Zustand store so cold starts with cached value skip the `/api/auth/status` call
   - When `authRequired` was previously `false`, skip `checkAuthRequired()` entirely
3. `frontend/src/app/(dashboard)/layout.tsx:100-106`
   - Replace `<LoadingSpinner />` with a proper skeleton layout (sidebar outline + content skeleton)

#### Story: BUG-extraction-progress-fix (M)
**Root cause:** ACMTab uses polling-only `useExtractionStatus`, not the SSE-based `useExtractionProgress`. Colors are hardcoded.

**Files to modify:**
1. `frontend/src/components/acm/ExtractionProgressPanel.tsx`
   - Lines 54-56: Replace `border-blue-500/50 bg-blue-50/50` with semantic tokens (`border-primary/50 bg-primary/5`)
   - Lines 127-128: Replace green hardcodes with `border-success/50 bg-success/5` or `border-emerald-500/50`
2. `frontend/src/components/acm/StageProgressPill.tsx`
   - Lines 32-37: Replace `bg-blue-500` with `bg-primary`, `bg-green-500` with `bg-success`, `bg-red-500` with `bg-destructive`
3. `frontend/src/lib/hooks/use-extraction-status.ts`
   - Add SSE support (align with `use-extraction-progress.ts` pattern)
   - Persist full `pipelineState` + `logEntries` in sessionStorage (not just `commandId`)
   - On reload, restore state and reconnect SSE if extraction is still in progress
4. `frontend/src/components/acm/ACMTab.tsx`
   - Ensure the extraction banner/panel shows real-time stage progress (0/7 → 1/7 → etc.)

---

### Phase 3: Extraction Quality (3-4 hours)

#### Story: BUG-negative-results-regression (M)
**Investigation + fix:**
1. Check git history of `prompts/acm/extraction.jinja` for changes since PR #30
2. Check `open_notebook/extractors/acm_extractor.py` for any post-processing that filters results
3. Check `open_notebook/graphs/acm_extraction.py` `validate_records()` and `validate_records_strict()` for filtering logic
4. Strengthen the extraction prompt: add explicit examples of negative records that MUST be included
5. Add a post-extraction validation check: compare extracted count vs expected count (from page count heuristic)
6. Test with Broadmeadows PDF to verify negatives are captured

---

### Phase 4: Model Abstraction Layer (CRITICAL, largest effort — 2-3 days)

Split into 3 sub-stories for manageability:

#### Story: E1-S28 — Model Capabilities Schema & Configuration (L)
**Goal:** Create a model capabilities system so all code queries model limits dynamically.

**Files to create/modify:**
1. Create new migration `migrations/20.surrealql`:
   - Add fields to `model` table: `max_output_tokens`, `context_window`, `supports_structured_output`, `supports_tool_calling`, `embedding_dimensions`
   - Set defaults based on known model families
2. `open_notebook/domain/models.py`
   - Add capability fields to Model class
   - Add `get_max_output_tokens()`, `get_context_window()`, `get_embedding_dimensions()` methods
   - Add provider-specific defaults lookup (Anthropic Claude → 8192/32768, OpenAI → 16384, Ollama → varies)
3. `api/model_provisioning.py`
   - Line 88: Fix `"claude-haiku-3-5-20241022"` → `"claude-3-5-haiku-20241022"`
   - Populate capability fields during provisioning based on known model metadata
   - Add capability detection for OpenRouter models (query model metadata API)
4. `api/routers/models.py`
   - Expose model capabilities in GET /api/models response
   - Add PUT endpoint to update capabilities manually

#### Story: E1-S29 — Replace Hardcoded Token Limits (L)
**Goal:** Replace all 15+ hardcoded `max_tokens` values with dynamic lookups.

**Files to modify (all replace hardcoded values with `model.capabilities.max_output_tokens`):**

| File | Lines | Current Value | Change To |
|------|-------|---------------|-----------|
| `open_notebook/graphs/acm_extraction.py` | 75 | `DEFAULT_CONTEXT_WINDOW = 128000` | Query from model capabilities |
| `open_notebook/graphs/acm_extraction.py` | 995 | `8192 if "haiku"... else 32768` | `model.max_output_tokens` |
| `open_notebook/extractors/orchestrator.py` | 379 | `32768` | `model.max_output_tokens` |
| `open_notebook/extractors/metadata_extractor.py` | 226 | `2048` | `min(2048, model.max_output_tokens)` |
| `open_notebook/extractors/building_inventory.py` | 445 | `4096` | `min(4096, model.max_output_tokens)` |
| `open_notebook/extractors/document_structure.py` | 140 | `4096` | `min(4096, model.max_output_tokens)` |
| `open_notebook/extractors/page_tagger.py` | 352 | `2048` | `min(2048, model.max_output_tokens)` |
| `open_notebook/graphs/supervisor_agent.py` | 85, 106 | `8192` | `model.max_output_tokens` |
| `open_notebook/graphs/acm_analyst_agent.py` | 67, 88 | `8192` | `model.max_output_tokens` |
| `open_notebook/graphs/source_chat.py` | 73, 164, 188 | `50000`, `8192` | Dynamic |
| `open_notebook/graphs/chat.py` | 41, 64 | `8192` | Dynamic |

Also:
- `open_notebook/graphs/utils.py:27` — Add None guard for `large_context_model`
- `open_notebook/graphs/utils.py:77-87` — Improve `supports_tool_calling()` to check model capabilities field
- Add structured output pre-flight check: try `with_structured_output()`, catch provider error, fall back to JSON mode parsing

#### Story: E1-S30 — Dynamic Embedding Dimensions (M)
**Goal:** Support multiple embedding models with different vector dimensions.

**Files to modify:**
1. Create new migration `migrations/21.surrealql`:
   - DROP and recreate `acm_embedding_idx` with dimension from config
   - Or use a function-based approach that checks embedding length at query time
   - Alternative: Store dimension as a config value and use `REMOVE INDEX` + `DEFINE INDEX` dynamically
2. `commands/embedding_commands.py`
   - Before embedding, query the configured embedding model's dimensions
   - Validate embedding vector length matches the index dimension
   - If mismatch detected, log warning and suggest re-indexing
3. `open_notebook/domain/models.py`
   - `get_embedding_dimensions()` method returns configured dimension for the active embedding model
4. Add a management command or API endpoint to re-index embeddings when the embedding model changes
5. Update `fn::vector_search` in migration 9 pattern to handle dimension validation

---

## Verification Plan

### Per-story verification:
1. **All frontend changes:** `cd frontend && npm run lint && npm run build` (must pass)
2. **All backend changes:** `uv run ruff check . && uv run pytest tests/ -x`
3. **Column fixes:** Visual verification in browser (Playwright snapshot)
4. **Model capabilities:** Test with at least 3 providers (Ollama qwen3, OpenRouter Sonnet, Anthropic Haiku)
5. **Negative results:** Run extraction on Broadmeadows PDF, verify negative records included
6. **Embedding dimensions:** Test with mxbai-embed-large (1024) and text-embedding-3-small (1536)

### Integration test:
- Upload Broadmeadows PDF with Ollama local model
- Upload same PDF with OpenRouter Sonnet 4.6
- Verify both extract >20 records including negatives
- Verify progress panel shows all 7 stages updating in real-time
- Verify post-upload navigation lands on source detail page

---

## Sprint Status Updates Required
After implementation, update `docs/sprint-artifacts/sprint-status.yaml`:
- Add E1-S28, E1-S29, E1-S30 under Epic 1
- Add all BUG-* stories under appropriate epics
- Create tech-spec files in `docs/sprint-artifacts/` for each new story

## Team Execution Strategy
Use agent teams (sonnet model) with parallel work:
- **Backend specialist:** E1-S28 → E1-S29 → E1-S30 (sequential, has dependencies)
- **Frontend specialist:** BUG-grid-column-fixes + BUG-ui-ux-vaea-branding + BUG-auth-loading-ux + BUG-extraction-progress-fix (can parallelize quick wins)
- **QA specialist:** BUG-negative-results-regression investigation + test verification
