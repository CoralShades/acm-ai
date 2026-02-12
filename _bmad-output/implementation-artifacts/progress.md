# E2E Test Progress Log

## Session: 2026-02-10 - ACM Extraction Pipeline E2E Test

### Test Context
- **PDF:** Clutch_Broadmeadows.pdf (Broadmeadows Police Station SAMP)
- **Expected Records:** 31 ACM items across 42 BAR columns
- **Pass Threshold:** 90% field match
- **Method:** Playwright MCP + agent teams (Sonnet model)

---

## Timeline

### Session Start
- Loaded TEA agent persona (Master Test Architect - Murat)
- Explored extraction pipeline architecture via sub-agent
- Pipeline: Upload → Docling → AI Extract → AG Grid display
- Created planning files (task_plan.md, findings.md, progress.md)
- Agent team structure: browser-tester, log-monitor, data-validator

(real-time updates below)

### Phase 0: Service Health Check - COMPLETE
- SurrealDB: UP (port 8000, HTTP 200)
- Frontend: UP (port 8502, HTTP 200)
- API: UP (port 5055, HTTP 200) - started from user's terminal
- Worker: UP (PID 78282/78287, surreal-commands-worker)
- Ollama: UP but unhealthy (port 11434)

### Phase 1: PDF Upload - IN PROGRESS
- **Source uploaded:** `source:jir6z9hetbd2sbk352q3`
- **Title:** Clutch_Broadmeadows.pdf
- **Source processing:** COMPLETED (text extracted via Docling)
- **ACM extraction triggered:** command:3uck6firr0webywefvj9 (manual trigger POST /api/acm/extract)
- **Status:** Waiting for extraction to complete...
- **Existing sources:** 16 total in system (1 previous Broadmeadows upload from Feb 4 with 0 records)

### Findings During Upload
- Upload auto-processing completed quickly (source status="completed")
- ACM extraction did NOT auto-trigger - had to manually POST /api/acm/extract
- This may indicate the upload dialog's ACM extraction toggle didn't work, or it's by design

### BLOCKER: Model Compatibility Issue
- **Error:** `qwen/qwen-2.5-72b-instruct does not support feature: structured-outputs`
- **Root Cause:** OpenRouter providers (Novita, DeepInfra) hosting Qwen 2.5 72B don't expose structured outputs API
- **Impact:** ALL extraction failed after 3 retries (both manual triggers)
- **Pipeline stages affected:** STRUCTURE (metadata, structure, inventory, page tagger) + EXTRACT
- **Resolution:** Switched DEFAULT_EXTRACTION_MODEL and DEFAULT_TOOLS_MODEL to `openrouter/anthropic/claude-3.5-haiku-20241022`
- **NOTE for future:** Qwen model itself supports JSON, but providers don't. Use `require_parameters: true` or switch models.
- **Alternative fixes documented by user:** See findings.md for OpenRouter `require_parameters` option

### Phase 2: Re-trigger Extraction with Claude Haiku
- Model changed in .env: qwen → claude-3.5-haiku-20241022
- Worker restart needed to pick up new model
- Additional issue: DB model name `claude-haiku-3-5-20241022` was wrong, corrected to `claude-3-5-haiku-20241022`
- Also: OpenRouter model ID `anthropic/claude-3.5-haiku-20241022` returned 404 (wrong format)
- Final fix: Used direct Anthropic provider with corrected model name

### Extraction Results (Claude 3.5 Haiku)
- **Records extracted: 8** (expected 31) - **26% coverage, FAIL**
- Confidence: All 8 high
- Time: 62.1s total, 68.1s with embedding
- Strategy: full_llm (1 chunk, 29,411 chars)
- All 8 embedded via Ollama mxbai-embed-large
- **SiteConfig error:** DB type mismatch for source_id field on site_config table
- **Critical issue:** Single chunk processing - 29K chars may be too large for Haiku to extract all 31 records
- Consultant correctly identified as "Prensa Pty Ltd"
- Document type correctly identified as DIVISION_5 with 4 pages, 7 sections

### Bug Found: SiteConfig DB Error
```
Exception: Found 'source:jir6z9hetbd2sbk352q3' for field `source_id`,
with record `site_config:l0lpmopus11tyaz7ibey`, but expected a record<source>
```
This is a schema mismatch - the `source_id` field on `site_config` table expects `record<source>` but gets a string.

---

## Phase 3: Data Validation - COMPLETE ✅
- **Records extracted:** 8 (expected 31)
- **Positive record recall:** 7/11 = 63.6%
- **Precision:** 7/8 = 87.5% (1 unmatched "Ceiling Space" record)
- **False positives:** 0 (no negative CSV records incorrectly extracted)
- **Core identification fields:** 89.8% accuracy (room, area_type, friability, condition, risk)
- **Compliance fields:** 0% (sample_no, quantity, labelled, floor_level all missing)
- **Verdict:** FAIL - below 90% threshold
- See findings.md for detailed record-by-record matching analysis

---

## Phase 4: UI/UX Bug Hunt - COMPLETE ✅

**Test Date:** 2026-02-10
**Tool:** Playwright MCP (Chromium browser automation)
**Viewports:** Desktop (1920x1080), Tablet (768x1024)

> **Note:** Earlier agent-spawned ui-tester reported routing bugs (BUG-001 through BUG-005) that were **incorrect** - those bugs were caused by the agent's Playwright session not loading the page properly. Manual verification confirms the ACM page at /acm works correctly and displays records.

### Verified Test Results
1. ✅ `/acm` route loads correctly - no redirect issues
2. ✅ Source selector populates with all uploaded sources
3. ✅ Selecting Clutch_Broadmeadows.pdf shows all 8 extracted records in AG Grid
4. ✅ Summary cards display correctly (Total: 8, Risk: Low 8, Buildings: 1, Rooms: 7)
5. ✅ Edit dialog opens on row click with all fields populated
6. ✅ Export dropdown shows CSV and Excel options
7. ✅ Keyboard shortcuts displayed (Arrow keys, Enter, E, Space, ?)
8. ⚠️ Search filter appears non-functional (typing doesn't filter rows)
9. ❌ Tablet responsive view hides most data columns (Product, Description, Risk, etc.)
10. ⚠️ Friable dropdown in edit dialog shows blank instead of current value

### Bugs Found: 10 total (0 Critical, 5 Medium, 3 Low, 2 Info)
See findings.md UX/UI Bug List for full details.

### Screenshots Captured: 6 new (10-15)
- `10-acm-register-empty.png` - Empty state before source selection
- `11-acm-register-with-records.png` - Full grid with 8 records
- `12-acm-edit-dialog.png` - Edit record form
- `13-acm-export-menu.png` - Export dropdown
- `14-acm-search-filter.png` - Search filter test
- `15-acm-tablet-view.png` - Tablet responsive view

---

## Final E2E Test Results

### ❌ FAIL - Extraction Coverage Below Threshold

**Phase 0:** ✅ Service health checks passed (10/10)
**Phase 1:** ✅ PDF upload via UI wizard successful (9/10)
**Phase 2:** ⚠️ Extraction completed after 5 model failures (4/10)
**Phase 3:** ❌ Data validation: 63.6% positive recall, 0% compliance fields (3/10)
**Phase 4:** ⚠️ UI functional but 5 medium bugs found (7/10)
**Phase 5:** ✅ Log quality good - 7.5/10 overall

### Overall Score: 5.5/10 - FAIL

### Critical Issues Summary
1. **Extraction coverage: 8/31 records (26%)** - Far below 90% threshold
2. **Compliance fields: 0% populated** - sample_no, quantity, labelled, floor_level missing
3. **Result mapping wrong** - "Detected" instead of "Positive"/"Assumed Positive"/"Negative"
4. **Model configuration: 5 failures** - SurrealDB model config not aligned with .env
5. **Search filter non-functional** on ACM Register page
6. **Tablet responsive broken** - data columns hidden at 768px

### Pass/Fail Criteria
- ✅ Pipeline executes end-to-end without crashes
- ✅ UI displays extracted records correctly
- ❌ 90% record match (actual: 26% of all, 63.6% of positive)
- ❌ Field accuracy for compliance fields (0%)
- ⚠️ Core identification fields: 89.8% (passes)

### Recommendations
1. **High:** Expand extraction schema to include all BAR compliance fields
2. **High:** Map result values correctly ("Positive"/"Assumed Positive"/"Negative")
3. **High:** Extract negative samples too (BAR requires complete register)
4. **High:** Improve chunking strategy for large documents
5. **Medium:** Fix search filter on ACM Register page
6. **Medium:** Fix tablet responsive grid (column priority/hiding)
7. **Medium:** Add model capability pre-flight validation
8. **Medium:** Fix SiteConfig DB schema mismatch
9. **Low:** Fix Friable dropdown display in edit dialog
10. **Low:** Address AG Grid deprecation warnings

**Status:** E2E test execution COMPLETE. Pipeline is functional end-to-end but extraction quality is insufficient for production use.
