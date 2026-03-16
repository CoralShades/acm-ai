# E2E Chat Components Test Report

Date: 2026-03-16
Branch: ACMV3
Source: `source:26mrq83frdwa6zanrzfw` (Clutch_Broadmeadows (29).pdf, 41 records, 1 building)

## Test Results

### Test 1: Job Detail Page — No Crash
**Status: PASS**
- Screenshot: `10-job-detail-fixed.png`
- Page loads correctly with overview tab, 41 records, 1 building, metadata
- No "Failed to load Job Detail" error (bug was fixed: `crud_agent` → `crud` name mismatch)

### Test 2: CRUD Chat Panel Renders
**Status: PASS**
- Screenshot: `11-source-smart-chat.png`
- CRUD Chat panel visible on right side of source detail page
- Shows title "CRUD Chat", initial message, input field, "Powered by CopilotKit"
- ChatModelSelector "Default" pill visible in header

### Test 3: Chat Query — LLM Response
**Status: PASS (partial)**
- Screenshot: `12-chat-query-response.png`
- Sent "Show me all high risk ACM records" via chat
- LLM responded with text asking to "select a job first"
- **Issue**: Agent doesn't have source_id context despite being on the job page
- No tool call was made (no ACMTableResult rendered)
- Backend AG-UI endpoint was invoked successfully (no 500 errors)

### Test 4: Model Selector
**Status: PASS**
- Screenshot: `13-model-selector-open.png`
- "Default" pill clicked, popover opened showing all 12 language models:
  - gemma3:27b, qwen2.5:7b, qwen3:latest, qwen2.5:14b, qwen3:32b
  - llama3.1:8b-instruct-q8_0, llama3.1:8b, phi4:14b-q4_K_M, mistral:7b
  - phi4:14b, deepseek-r1:8b, qwen2.5:32b
- Each shows model name and "ollama" provider label
- Compact, clean design matching the app's style

### Test 5: CRUD Chat After Fix
**Status: PASS**
- Screenshot: `14-crud-chat.png`
- Chat panel loads without crash
- Model selector visible and functional
- Chat input field ready for messages

## Bugs Found

### BUG-1: CRUD Agent Name Mismatch (FIXED)
- **Severity**: P1 (Blocker)
- **Root Cause**: `useCoAgent({ name: 'crud_agent' })` in JobCrudChatPanel didn't match backend registration `name: 'crud'` in copilot-crud/route.ts
- **Fix**: Changed to `useCoAgent({ name: 'crud' })`
- **Evidence**: Before fix: `02b-job-detail-crash.png`, `04-chat-page-crash.png`. After fix: `10-job-detail-fixed.png`

### BUG-2: CRUD Agent Missing source_id Context (Pre-existing)
- **Severity**: P2 (Important)
- **Description**: CRUD agent responds "select a job first" even when on job page. The source_id from useCoAgent state may not be reaching the backend `set_crud_context(source_id)` call.
- **Root Cause**: The `source_id` is set in `useCoAgent` initialState, but CopilotKit may not forward it before the first message. The CRUD agent's `call_crud_agent()` reads `state.get("source_id")` which may be None on first invocation.
- **Suggested Fix**: Pass source_id in the makeSystemMessage so the agent knows the context, or ensure useCoAgent state syncs before first message.

### BUG-3: CopilotKit "1 Issue" Badge
- **Severity**: P3 (Minor)
- **Description**: Red "1 Issue" badge appears in bottom-left corner on chat pages
- **Likely Cause**: CopilotKit runtime warning or error notification
- **Note**: showDevConsole is set to false, but this badge may be from the error boundary

## Pre-existing Screenshots (Before Fix)
- `01-jobs-page.png` — Jobs list page
- `02-job-detail.png` — Job detail page (Overview tab)
- `02b-job-detail-crash.png` — "Failed to load Job Detail" error
- `03-source-detail.png` — Source detail page
- `04-chat-page-crash.png` — "Failed to load CRUD Chat" error

## Verification Checklist
- [x] Job detail page loads without crash
- [x] CRUD Chat panel renders
- [x] Chat input accepts messages
- [x] LLM responds to queries (via AG-UI/CopilotKit)
- [x] ChatModelSelector visible and opens with 12 models
- [x] Model selector shows provider labels
- [ ] Tool calls render as structured components (not tested — agent needs source context)
- [ ] HITL approval dialog (not tested — requires tool call first)
- [ ] Row cap expandable (not tested — requires ACMTableResult)
