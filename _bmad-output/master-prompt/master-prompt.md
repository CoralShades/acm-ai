# Master Prompt: BMAD-Driven E2E Gap Analysis & Fix for ACM Extraction Pipeline

## Context

Use `/planning-with-files` for all context management. Create planning files in `_bmad-output/gap-analysis-fix/` before any work begins.

### E2E Test Results (2026-02-11)
- **Score**: 5.0/10 FAIL (previous: 5.5/10, delta: -0.5, pass threshold: >= 7.0)
- **Records**: 8/31 extracted (25.8%) - 20 negatives completely skipped
- **Core ID Accuracy**: 53.6% (product/location column confusion)
- **Assessment Accuracy**: 87.5% (friable/condition/risk strong)
- **Compliance Accuracy**: 0% (fields missing from API entirely)
- **Classification**: 0% (never populated)
- **UI/UX**: 8 bugs (3 medium, 3 low, 2 informational)
- **Full findings**: `_bmad-output/e2e-test-2026-02-11/` (reporter/, data-validator/, browser-pilot/, log-monitor/, health-checker/)
- **GitHub Issue**: #14

### Root Cause Summary
7 stories marked "done" have incomplete acceptance criteria. 2 stories are completely missing. The primary blocker is that the extraction prompt skips all negative results (65% of records).

---

## Phase 1: Sprint Status & Gap Analysis (BMAD Workflows)

### Step 1.1: Run Sprint Status
```
/bmad:bmm:workflows:sprint-status
```
This surfaces the current sprint state, identifies blockers, and routes to the right next step. Feed it: "The latest E2E test scored 5.0/10 FAIL. I need to identify which stories have gaps."

### Step 1.2: Run Analyst Gap Analysis (Agent Team)

Create a team with 3 agents to analyze failures in parallel:

```
TeamCreate: team_name="gap-analysis"

Task 1: "Analyze extraction failures and map to stories"
  - Agent: analyst (subagent_type: bmad-analyst, model: sonnet)
  - Read: _bmad-output/e2e-test-2026-02-11/data-validator/findings.md
  - Read: _bmad-output/e2e-test-2026-02-11/log-monitor/findings.md
  - Read: docs/sprint-artifacts/sprint-status.yaml
  - Read: _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md
  - Output: Gap analysis mapping each failure to story + gap type
  - Write to: _bmad-output/gap-analysis-fix/analyst/findings.md

Task 2: "Analyze extraction pipeline code for prompt and mapping issues"
  - Agent: extraction-reviewer (subagent_type: acm-extraction-core, model: sonnet)
  - Read: open_notebook/graphs/acm_extraction.py (focus on extract_records, prepare_context)
  - Read: open_notebook/extractors/orchestrator.py
  - Read: prompts/acm/extraction* (extraction prompt templates)
  - Read: open_notebook/domain/acm.py (ACMRecord model)
  - Read: api/models.py (ACMRecordResponse - missing fields)
  - Output: Root cause analysis for negative records, product/location confusion, missing fields
  - Write to: _bmad-output/gap-analysis-fix/extraction-reviewer/findings.md

Task 3: "Analyze API schema gaps and UI enum mismatches"
  - Agent: schema-reviewer (subagent_type: acm-schema-expert, model: sonnet)
  - Read: api/models.py (ACMRecordResponse at line 429)
  - Read: open_notebook/domain/acm.py (full domain model)
  - Read: _bmad-output/e2e-test-2026-02-11/browser-pilot/findings.md (UI bugs)
  - Read: migrations/ (latest migration files)
  - Output: List of missing API fields, enum mismatches, schema fixes needed
  - Write to: _bmad-output/gap-analysis-fix/schema-reviewer/findings.md
```

Dependencies: Tasks 1, 2, 3 run in parallel. No blockers.

### Step 1.3: Synthesize Findings

After all 3 agents complete, the team lead reads all findings and creates:
- `_bmad-output/gap-analysis-fix/master/synthesis.md` - Unified gap analysis
- Categorize into: Reopen Story, New Story, Quick Fix

---

## Phase 2: Sprint Course Correction (BMAD Workflow)

### Step 2.1: Run Correct-Course Workflow
```
/bmad:bmm:workflows:correct-course
```

Feed it the synthesized findings from Phase 1. This workflow will:
1. Analyze impact of the E2E failures on the sprint
2. Propose story changes (reopen, extend AC, create new)
3. Generate a Sprint Change Proposal document

### Step 2.2: Expected Change Proposal Content

Based on the E2E failure mapping, the change proposal should include:

**Stories to Reopen (Incomplete AC):**

| Story | Current Status | Issue | Required AC Addition |
|-------|---------------|-------|---------------------|
| E1-S7 | Done | Skips negative records (65% missed) | "Extract ALL records regardless of result type (Positive, Assumed Positive, Negative)" |
| E1-S7 | Done | Product/location column confusion | "Product field maps to CSV 'Specific Item/ACM Name', location maps to 'Location in Room'" |
| E1-S7 | Done | school_name shows filename | "Extract school/site name from document metadata, not filename" |
| E1-S4 | Done | Compliance fields missing from API | "ACMRecordResponse includes all BAR compliance fields: sample_no, quantity, acm_labelled, identifying_company, disturbance_potential, hygienist_recommendations" |
| E1-S3 | Done | Result conflates Positive/Assumed Positive | "Result enum: 'Positive', 'Assumed Positive', 'Negative' (not binary Detected/Not Detected)" |
| E1-S17 | Done | building_name not propagating to records | "Building inventory metadata propagates to all child ACM records" |
| E3-S4 | Done | page_number always null | "page_number populated for all extracted records from register page range" |

**New Stories Needed:**

| Story ID | Title | Priority | Description |
|----------|-------|----------|-------------|
| NEW-1 | Command Dependency Management | P0 | acm_extract must wait for process_source completion. Add dependency ordering to command dispatch. |
| NEW-2 | Model Provider Validation | P1 | Validate model IDs against provider API on save. Handle provider-specific ID formats (OpenRouter vs direct Anthropic). Persist working model config in seed data. |
| NEW-3 | Extraction Hallucination Guard | P2 | Validate extracted room names against building inventory. Reject records with unrecognized rooms. |

**Quick Fixes (No Story Needed):**

| Fix | File | Change |
|-----|------|--------|
| Friable enum mismatch | Frontend enum definition | Normalize "Non-friable" (hyphenated) across backend + frontend |
| area_type vocabulary | Extraction normalization | Map "Interior"/"Exterior" to "Internal"/"External" |
| Search filter broken | Frontend AG Grid config | Connect quickFilter API to search input onChange |
| Document library refresh | Frontend React Query | Invalidate sources query cache after upload mutation |

### Step 2.3: Apply Change Proposal
```
/bmad:bmm:agents:sm
```
Use the Scrum Master agent to apply the approved change proposal to:
- `docs/sprint-artifacts/sprint-status.yaml` (reopen stories, add new ones)
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` (add new story definitions)

---

## Phase 3: Implementation (Agent Team with BMAD Dev Workflow)

### Step 3.1: Create Implementation Team

```
TeamCreate: team_name="extraction-fix"
```

**Team Structure (5 agents):**

| Agent | subagent_type | model | Responsibility |
|-------|--------------|-------|----------------|
| sprint-lead | acm-sprint-lead | sonnet | Orchestrate work, manage dependencies, review |
| backend-dev | bmad-dev | sonnet | Fix extraction prompt, add API fields, fix race condition |
| extraction-specialist | acm-extraction-core | sonnet | Deep pipeline fixes (negative records, field mapping) |
| schema-dev | acm-schema-expert | sonnet | Migration for new API fields, enum normalization |
| qa-tester | bmad-qa | sonnet | Write tests, validate acceptance criteria |

### Step 3.2: Task Breakdown (Priority Order)

**P0 Tasks (Critical - Do First):**

```
Task 1: Fix extraction prompt to include negative records
  Owner: extraction-specialist
  Files: prompts/acm/extraction*.j2, open_notebook/graphs/acm_extraction.py
  AC: All 31 records extracted from Broadmeadows PDF (Positive + Assumed Positive + Negative)
  Verify: curl API returns total >= 28 records
  BlockedBy: none

Task 2: Fix race condition - acm_extract waits for process_source
  Owner: backend-dev
  Files: commands/acm_commands.py, commands/source_commands.py
  AC: acm_extract only starts after process_source completes. No "Source has no text content" errors.
  Verify: Upload new PDF, check worker logs for sequential execution
  BlockedBy: none

Task 3: Persist model configuration fix
  Owner: schema-dev
  Files: migrations/, open_notebook/database/*, seed data
  AC: Default extraction model is claude-3-5-haiku-20241022 via direct Anthropic (not OpenRouter)
  Verify: Fresh DB init uses correct model. curl API model endpoint shows anthropic provider.
  BlockedBy: none
```

**P1 Tasks (High - Do After P0):**

```
Task 4: Fix product/location column mapping in extraction
  Owner: extraction-specialist
  Files: prompts/acm/extraction*.j2, open_notebook/graphs/acm_extraction.py
  AC: product maps to "Specific Item/ACM Name", location maps to "Location in Room"
  Verify: Extracted records have correct product and location values vs CSV
  BlockedBy: Task 1

Task 5: Add compliance fields to ACMRecordResponse
  Owner: schema-dev
  Files: api/models.py, api/routers/acm.py
  AC: API response includes sample_no, quantity, acm_labelled, identifying_company, disturbance_potential, hygienist_recommendations
  Verify: curl API returns compliance fields for records
  BlockedBy: none

Task 6: Fix result enum (Positive/Assumed Positive/Negative)
  Owner: extraction-specialist
  Files: open_notebook/domain/acm.py, prompts/acm/extraction*.j2
  AC: Result field uses 3 values matching BAR spec, not binary Detected/Not Detected
  Verify: Extracted records show "Positive", "Assumed Positive", or "Negative"
  BlockedBy: Task 1

Task 7: Propagate building_name and page_number to records
  Owner: extraction-specialist
  Files: open_notebook/graphs/acm_extraction.py (save_records, extract_records)
  AC: building_name populated from building inventory, page_number from register page range
  Verify: API records have non-null building_name and page_number
  BlockedBy: Task 1
```

**P2 Tasks (Medium - Do After P1):**

```
Task 8: Fix enum mismatches (friable, area_type)
  Owner: backend-dev
  Files: open_notebook/domain/acm.py, frontend enum definitions
  AC: "Non-friable" consistent across backend+frontend, "Internal"/"External" matches BAR
  BlockedBy: none

Task 9: Fix search filter in ACM grid
  Owner: backend-dev (or frontend-dev if Lane B)
  Files: frontend/src/app/(dashboard)/acm/page.tsx, AG Grid config
  AC: Typing in search box filters grid rows in real-time
  BlockedBy: none

Task 10: Write acceptance tests for extraction accuracy
  Owner: qa-tester
  Files: tests/test_acm_extraction.py (new or extended)
  AC: Test validates >= 28/31 records extracted from Broadmeadows PDF with correct field mapping
  BlockedBy: Tasks 1, 4, 6, 7
```

### Step 3.3: Execute Stories via BMAD Dev Workflow

For each task, the assigned agent runs:
```
/bmad:bmm:workflows:dev-story
```

This workflow:
1. Reads the tech spec and acceptance criteria
2. Implements with TDD (RED -> GREEN -> REFACTOR)
3. Runs verification (build, lint, test)
4. Updates sprint status

### Step 3.4: Concurrent Development Protocol

Per project memory, Lane A (backend) and Lane B (frontend) have separate worktrees:
- **Lane A**: `/mnt/d/ailocal/acm-ai/` on `main` - owns migrations, backend, sprint-status.yaml
- **Lane B**: `/mnt/d/ailocal/acm-ai-frontend/` on `lane-b` - owns frontend components

Tasks 1-7 are Lane A (backend). Tasks 8-9 may cross lanes. Task 10 is Lane A.

---

## Phase 4: Verification (E2E Re-Test with Agent Team)

### Step 4.1: Run E2E Test Again

After all P0+P1 fixes are implemented, re-run the E2E test using the same 5-agent team architecture from `_bmad-output/e2e-test-2026-02-11/`:

```
TeamCreate: team_name="e2e-retest"

Agents:
  - health-checker (haiku, general-purpose): Monitor services
  - log-monitor (haiku, general-purpose): Watch extraction logs
  - browser-pilot (haiku, general-purpose): Playwright upload + UI verification
  - data-validator (sonnet, general-purpose): CSV ground truth comparison
  - reporter (sonnet, general-purpose): Scorecard + GitHub Issue #14 update
```

Use the exact agent prompts from `_bmad-output/e2e-test-2026-02-11/master/task_plan.md` but with these additions:
- browser-pilot: Skip model fix (should be persisted now)
- data-validator: Expect >= 28 records, compliance fields present
- reporter: Compare against BOTH previous scores (5.5/10 and 5.0/10)

### Step 4.2: Success Criteria

| Phase | Target | Previous |
|-------|--------|----------|
| Service Health | 10/10 | 10/10 |
| PDF Upload | 10/10 | 8/10 |
| Extraction | >= 9/10 (28+ records) | 2.6/10 |
| Data Accuracy | >= 7/10 | 4.0/10 |
| UI/UX | >= 8/10 | 5.5/10 |
| **Overall** | **>= 7.0/10 PASS** | **5.0/10** |

### Step 4.3: If Re-Test Fails

```
/bmad:bmm:workflows:correct-course
```
Feed the new test results and iterate. Each cycle should improve the score.

---

## Phase 5: Retrospective (BMAD Workflow)

After achieving PASS (>= 7.0/10):
```
/bmad:bmm:workflows:retrospective
```

Capture:
- What stories had incomplete AC and why
- How to prevent premature "done" marking
- Whether E2E testing should be a sprint quality gate
- Agent team effectiveness metrics (tokens, time, accuracy)

---

## MCP Server Usage Guide

### Playwright (browser automation)
```
ToolSearch: "playwright" -> loads browser_navigate, browser_snapshot, browser_click, etc.
Use for: E2E re-test browser-pilot agent
Key tools: browser_navigate, browser_snapshot, browser_click, browser_fill_form, browser_file_upload, browser_take_screenshot, browser_evaluate
```

### GitHub (issue management)
```
ToolSearch: "github" -> loads issue_read, issue_write, add_issue_comment, etc.
Use for: Updating Issue #14 with test results
Alternative: gh CLI via Bash (already proven to work)
```

### Memory (persistent context)
```
ToolSearch: "memory" -> loads save_memory, search, get_observations
Use for: Saving key findings across sessions, retrieving past decisions
```

### Serena (semantic code tools)
```
ToolSearch: "serena" -> loads find_symbol, replace_symbol_body, get_symbols_overview
Use for: Precise code modifications in extraction pipeline
Key benefit: Symbol-level editing for acm_extraction.py changes
```

---

## File Reference

| File | Purpose | Used By |
|------|---------|---------|
| `_bmad-output/e2e-test-2026-02-11/` | Complete E2E test artifacts | All phases |
| `_bmad-output/e2e-test-2026-02-11/data-validator/comparison.md` | Record-by-record comparison | Phase 1 analyst |
| `_bmad-output/e2e-test-2026-02-11/reporter/scorecard.md` | Test scorecard | Phase 1, Phase 4 |
| `docs/sprint-artifacts/sprint-status.yaml` | Sprint state | Phase 1, Phase 2 |
| `docs/samplePDF/Clutch_Broadmeadows.csv` | Ground truth (31 records) | Phase 4 validator |
| `docs/samplePDF/Clutch_Broadmeadows.pdf` | Test input PDF | Phase 4 browser-pilot |
| `open_notebook/graphs/acm_extraction.py` | Main extraction pipeline | Phase 3 extraction fixes |
| `prompts/acm/` | Extraction prompt templates | Phase 3 prompt fixes |
| `api/models.py:429` | ACMRecordResponse (missing fields) | Phase 3 API fix |
| `open_notebook/domain/acm.py` | ACMRecord domain model | Phase 3 schema fix |
| `commands/acm_commands.py` | ACM extract command handler | Phase 3 race condition fix |
| `commands/source_commands.py` | Source processing command | Phase 3 race condition fix |
| `_bmad-output/master-prompt/research-claude-agents.md` | Agent teams documentation | Reference |
| `_bmad-output/master-prompt/research-bmad-catalog.md` | BMAD agent/workflow catalog | Reference |

---

## Quick Start

Copy and paste this to begin a new session:

```
I need to fix the ACM extraction pipeline based on E2E test results (5.0/10 FAIL).

Use /planning-with-files to manage context. Create files in _bmad-output/gap-analysis-fix/.

Follow the master prompt at _bmad-output/master-prompt/master-prompt.md which has 5 phases:
1. Sprint Status & Gap Analysis (BMAD workflows + 3-agent team)
2. Sprint Course Correction (/bmad:bmm:workflows:correct-course)
3. Implementation (5-agent team with bmad-dev workflow)
4. E2E Re-Test (5-agent team with Playwright)
5. Retrospective

Start with Phase 1: Run /bmad:bmm:workflows:sprint-status, then create a 3-agent gap analysis team.

Key context:
- E2E findings: _bmad-output/e2e-test-2026-02-11/
- 8/31 records extracted (65% negatives skipped)
- 7 stories have incomplete AC, 2 stories missing
- Race condition: acm_extract runs before process_source
- Model config: OpenRouter 404, manual fix needed each time
- Compliance fields missing from API response model
```
