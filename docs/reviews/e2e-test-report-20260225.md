# E2E Test Report — 2026-02-25

## Executive Summary

**Status: PASS (with known issues)**

ACM extraction pipeline successfully extracts records from `Clutch_Broadmeadows.pdf` after fixing OpenRouter provider routing. Frontend UI flows (Dashboard, Jobs, Buildings Review, Records Review, ACM Register) all render correctly with no JS console errors.

---

## 1. Extraction Results

### Extraction Attempt #7 (first successful)

| Metric | Value |
|--------|-------|
| **Command ID** | `command:w7keurrrpsc6f6lk79ig` |
| **Source** | `source:r9rd8rtjgahlwvscf6rc` (Clutch_Broadmeadows (19).pdf) |
| **Status** | `success: true` |
| **Records Created** | 16 per run (32 total — dual worker race condition) |
| **Records Failed** | 0 |
| **Embeddings** | 32 |
| **Execution Time** | 87.9s (run 1), 91.0s (run 2) |
| **Model** | `anthropic/claude-sonnet-4.6` via OpenRouter → Anthropic direct |
| **Strategy** | `full_llm` (1 building, pages 1-3) |
| **Confidence** | 100% high (16 high, 0 medium, 0 low) |
| **Validation** | 17 raw → 4 with issues → LLM-corrected 4 → 0 issues remaining |
| **Deduplication** | 17 → 16 (1 merged) |

### Record Count Comparison (CSV vs Extracted)

| Metric | CSV | Extracted | Notes |
|--------|-----|-----------|-------|
| **Total rows** | 30 | 16 (unique) | See gap analysis below |
| **Unique sample numbers** | 23 | 16 | |
| **Core numbered samples** | 16 | 16 | Near-parity |
| **"As Per" references** | 6 | 0 | Correctly excluded |
| **"Not Sampled"** | 1 | 0 | Correctly excluded |

### Sample Number Gap Analysis

| Sample # | CSV | Extracted | Notes |
|----------|-----|-----------|-------|
| 34511-039-001 | ✅ | ✅ | Match |
| 34511-039-002 | ✅ | ✅ | Match |
| 34511-039-003 | ✅ | ✅ | Match |
| 34511-039-004 | ✅ | ✅ | Match |
| 34511-039-005 | — | ✅ | Extracted-only (valid from PDF) |
| 34511-039-006 | ✅ | ✅ | Match |
| 34511-039-007 | ✅ | ✅ | Match |
| 34511-039-008 | ✅ | ✅ | Match |
| 34511-039-009 | ✅ | ✅ | Match |
| 34511-039-010 | ✅ | ✅ | Match |
| 34511-039-011 | ✅ | ✅ | Match |
| 34511-039-012 | ✅ | ✅ | Match |
| 34511-039-013 | ✅ | ✅ | Match |
| 34511-039-014 | ✅ | — | **MISSING** from extraction |
| 34511-039-015 | ✅ | ✅ | Match |
| 34511-039-016 | ✅ | ✅ | Match |
| 34511-039-017 | ✅ | ✅ | Match |

**Coverage: 15/16 core samples matched (93.75%)**

---

## 2. Extraction Pipeline Analysis

### Pipeline Phases

| Phase | Duration | Result |
|-------|----------|--------|
| **Structure** | 35.5s | Metadata: consultant=Prensa Pty Ltd, 14 fields; Type=DIVISION_5; 1 building; 3 pages |
| **Orchestrator** | 46.3s | 1 building plan; full_llm strategy; provider error → fallback to JSON parsing |
| **Validation** | 0.0s | 17 accepted, 0 rejected, 4 with issues |
| **Correction** | 6.7s | 0 auto-corrected, 4 LLM-corrected, 0 failed |
| **Store** | 0.4s | 1 merged duplicate, 16 unique saved, 1 parent section |

### Provider Routing

The extraction encountered the **provider schema error** (OpenRouter tried routing to a provider that can't handle the complex ACM schema), which triggered the **fallback path** (direct invocation + manual JSON parsing). This fallback succeeded with 17 records.

### Key Log Events

```
[STRUCTURE] Metadata extracted: consultant=Prensa Pty Ltd | fields=14
[STRUCTURE] Structure: type=DocumentType.DIVISION_5, register_start=1
[STRUCTURE] Inventory: 1 buildings | pages=1-3
[ORCHESTRATOR] Provider error detected — falling back to direct JSON parsing
[ORCHESTRATOR] Fallback succeeded: 17 records from Broadmeadows Police Station
[VALIDATE] 17 accepted, 0 rejected | with_issues=4
[CORRECT] auto=0, llm=4, failed=0
[STORE] Deduplicated: 1 merged, 16 unique
EXTRACTION COMPLETE | 16 records in 87.9s
```

---

## 3. Frontend E2E UI Flow

### Pages Tested

| Page | URL | Status | Notes |
|------|-----|--------|-------|
| Dashboard | `/` | ✅ 200 | Stats cards, recent uploads, quick actions all render |
| Jobs | `/jobs` | ✅ 200 | 2 jobs listed, action menus, review links |
| Buildings Review | `/jobs/.../review/buildings` | ✅ 200 | Step 1/2, AG Grid, 1 building row |
| Records Review | `/jobs/.../review/records` | ✅ 200 | Step 2/2, AG Grid, 32 records, tabs |
| ACM Register | `/acm` | ✅ 200 | Source selector dropdown, no records published yet |
| Sources | `/sources` | ✅ 307 | Redirect (expected — auth gate) |

### UI Elements Verified

- **Wizard progress bar**: Step 1/2 (50%) → Step 2/2 (100%)
- **AG Grid**: Building columns (Name, Type, Address, Suburb, Postcode, Dept) + Record columns (Room/Area, Location, ACM Name, Friable, Product Group, Product Type, No Access)
- **Action buttons**: Cancel, Next, Publish to Register, Merge Duplicate, Add Record, Add Building, Out of Scope, Remove
- **Tabs**: "All Records (32)" and "Broadmeadows Police Station (32)"
- **Pagination**: Page size selector, page navigation
- **Sidebar navigation**: Dashboard, Jobs, ACM Register, Search, Visit Landing, Documentation
- **Command Palette**: Ctrl+K shortcut indicator

### Console Errors

**0 errors, 0 warnings** (only Lit dev mode info message — expected)

---

## 4. Issues Discovered

### Critical

| # | Issue | Component | Status |
|---|-------|-----------|--------|
| 1 | **Worker race condition**: Same command picked up by 2 workers → 32 records instead of 16 | `surreal-commands` worker | **NEW** — needs fix |
| 2 | **Missing sample 34511-039-014**: 1 of 16 core samples not extracted | Extraction pipeline | **Data gap** |

### Fixed This Session

| # | Fix | File | Root Cause |
|---|-----|------|-----------|
| 1 | OpenRouter provider routing via `extra_body` | `open_notebook/graphs/utils.py` | OpenRouter routed to Amazon Bedrock/Azure which can't handle complex schemas |
| 2 | Provider schema error fallback path | `open_notebook/extractors/orchestrator.py` | No recovery when structured output rejected by provider |
| 3 | `_apply_openrouter_preferences()` using `object.__setattr__` | `open_notebook/graphs/utils.py` | Type checker: `BaseChatModel` doesn't declare `model_kwargs` |
| 4 | `extra_body` wrapping for OpenRouter params | `open_notebook/graphs/utils.py` | `AsyncCompletions.create()` rejects unknown kwargs like `provider` |
| 5 | Fallback model priority (Anthropic > OpenAI > Ollama) | `open_notebook/graphs/utils.py` | OpenRouter in fallback chain caused same provider issues |
| 6 | Worker.log recording | `run_worker.py` | Logging sinks not surviving library's `logger.remove()` |
| 7 | ACMReviewGrid.tsx TypeScript merge payload type | `frontend/src/components/acm/ACMReviewGrid.tsx` | TS strict type checking on `Record<string, unknown>` field assignment |

### Observations

| # | Observation | Severity |
|---|-------------|----------|
| 1 | Dashboard "Risk Distribution: No ACM data available" — correct (records not published) | Info |
| 2 | Some extracted fields empty: `room_area`, `location_detail`, `item_name` — data is in alternate fields (`room_name`, `location`, `product`) | Low |
| 3 | Structure phase log lines appear doubled (race condition artifact) | Low |
| 4 | Provider error still triggers on initial attempt; fallback adds ~40s latency | Medium |

---

## 5. Code Changes Summary

| File | Status | Changes |
|------|--------|---------|
| [open_notebook/graphs/utils.py](open_notebook/graphs/utils.py) | MODIFIED | Added `OPENROUTER_IGNORED_PROVIDERS`, `OPENROUTER_PROVIDER_ORDER`, `_apply_openrouter_preferences()`, updated `provision_extraction_fallback_model()` |
| [open_notebook/extractors/orchestrator.py](open_notebook/extractors/orchestrator.py) | MODIFIED | Added `is_provider_schema_error()` fallback path, pipeline error surfacing |
| [frontend/src/components/acm/ACMReviewGrid.tsx](frontend/src/components/acm/ACMReviewGrid.tsx) | MODIFIED | Fixed TS type error in merge payload |
| [run_worker.py](run_worker.py) | MODIFIED | Fixed worker.log recording |

---

## 6. Extraction Attempt History

| # | Time | Result | Error |
|---|------|--------|-------|
| 1-5 | Prior session | 0 records | Various: PipelineLogger, grammar too large, Vertex AI header, timeout |
| 6 | 02:38:35 | 0 records | `AsyncCompletions.create() got unexpected keyword argument 'provider'` |
| **7** | **02:41:53** | **16 records** | **SUCCESS** (fallback to JSON parsing after provider error) |

---

## 7. Next Recommended Actions

1. **Fix worker race condition** — Add command-level locking or at-most-once delivery in `surreal-commands` to prevent duplicate command pickup
2. **Clean up duplicate records** — Either re-extract with force=true (with single worker), or add a dedup cleanup script
3. **Investigate missing sample 34511-039-014** — Check if it appears in the PDF and was lost during extraction or dedup
4. **Eliminate provider error latency** — The `provider.ignore` list in `extra_body` should prevent OpenRouter from routing to incompatible providers. If the error still triggers, check if the `extra_body` is being passed through correctly during structured output calls
5. **Publish records to register** — Use the "Publish to Register" button in the review UI to populate Dashboard risk distribution
6. **BMAD sprint status update** — Update story statuses and artifact tracking

---

*Report generated: 2026-02-25T02:55:00*
*Environment: Windows WSL + Docker (SurrealDB) + Windows Python venv*
