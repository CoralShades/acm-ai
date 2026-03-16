# Session: Audit and fix frontend UI issues across all ACM pages

## Skills to Load

/planning-with-files — persistent markdown plan for session continuity
/subagent-driven-development — fresh subagent per task with review gates
/verification-before-completion — verify work before claiming done
/react-best-practices — React performance, hooks, patterns
/next-best-practices — Next.js App Router, file conventions

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Frontend running: `curl http://localhost:8503`
- Branch: `git checkout ACMV3` (or create feature branch `frontend-audit-fix`)
- At least one completed extraction exists (so tables/records/buildings are populated for testing)

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| AG Grid | Enterprise React data grid for `ItemGrid` and `BuildingGrid` views. Supports row grouping, column pinning, virtual scrolling, dynamic columns from SF schema API. |
| ProvenanceViewer | PDF page viewer component that highlights source table region for a selected ACM record using bounding box data. Wrapped in `next/dynamic` to avoid SSR issues. |
| BuildingSidebar | Left-panel component on `/source/[id]` listing all buildings for a source. Clicking a building filters the ItemGrid. |
| ItemGrid | AG Grid component showing `ACMRecord` items for selected building. Columns dynamically generated from `GET /api/acm/field-schema`. |
| SFFieldSchemaConfig | TypeScript type for the Salesforce field schema config. Used to dynamically generate AG Grid column definitions. |
| Building__c | Salesforce object for a physical building. The extraction pipeline produces one `BuildingRecord` per building. Fields include `Building_Address__c`, `Suburb__c`, `Postcode__c`, `State__c`. |
| Item__c | Salesforce object for an individual ACM sample. Maps to `ACMExtractionRecord` in `open_notebook/domain/acm.py`. |
| CopilotKit | Real-time AI copilot framework providing `useCopilotReadable` / `useCopilotAction` hooks for the chat interface. |
| Zustand store | Client-state management. Key stores: `buildingStore` (selected building), `streamingStore` (SSE events), `notebookStore`. |
| Dependent picklist | SF pattern where one field's options depend on another field's value (e.g., Condition depends on Friable). Validated by `SalesforcePicklistValidator`. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. Lives in `.claude/skills/`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. Use `sonnet` for complex, `haiku` for simple tasks. |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep. |

---

## Current State

- Branch: ACMV3 (last commit: `docs(prompt-gen): add community skills section`)
- Sprint: V3-8, 6 stories remaining (E35-S3..S8)
- Frontend port: 8503 (Next.js dev)
- All V3-1 through V3-7 stories complete (37/37)
- Known UI issues: Multiple pages have naming gaps, missing metadata, broken dropdowns, missing provenance, and page integration gaps
- 4-table data flow: `raw_extraction_table` → `acm_table_section` → `building_record` → `acm_record`
- Backend APIs exist: `/api/acm/buildings`, `/api/acm/field-schema`, `/api/acm/raw-extractions`, `/api/acm/provenance`, `/api/acm/intelligence`

---

## Key Files

Files this session will read or modify. Verify all paths exist before starting.

**Read (reference):**
- `D:/ailocal/acm-ai/CLAUDE.md` — project instructions and architecture
- `D:/ailocal/acm-ai/open_notebook/domain/acm.py` — ACMRecord, BuildingRecord domain models (field names)
- `D:/ailocal/acm-ai/V3/output/building_fields_summary.md` — SF Building__c field definitions
- `D:/ailocal/acm-ai/V3/output/item_fields_summary.md` — SF Item__c field definitions
- `D:/ailocal/acm-ai/api/routers/acm.py` — ACM API endpoints
- `D:/ailocal/acm-ai/frontend/src/lib/types/acm.ts` — ACMRecord, RawExtraction types
- `D:/ailocal/acm-ai/frontend/src/lib/types/building.ts` — BuildingRecord types
- `D:/ailocal/acm-ai/frontend/src/lib/types/sf-schema.ts` — SFFieldSchemaConfig types
- `D:/ailocal/acm-ai/frontend/src/lib/types/intelligence.ts` — SourceIntelligence types

**Modify (likely — verify each exists first):**
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx` — rename "Raw Extracted Records" → "AI Mapped Records"
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/jobs/[id]/review/buildings/page.tsx` — add missing metadata fields (Address, Suburb, etc.)
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx` — fix broken dropdown editors
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/jobs/page.tsx` — update filters, add job card metadata
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — overview page metadata, integrate ACM table
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/source/[id]/page.tsx` — source detail page improvements
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/source/[id]/raw/page.tsx` — provider tab labeling
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/acm/page.tsx` — ACM register table integration
- `D:/ailocal/acm-ai/frontend/src/components/acm/ItemGrid.tsx` — dropdown cell editors, provenance button
- `D:/ailocal/acm-ai/frontend/src/components/acm/BuildingSidebar.tsx` — building metadata display
- `D:/ailocal/acm-ai/frontend/src/components/acm/ProvenanceViewer.tsx` — PDF preview with bbox overlay
- `D:/ailocal/acm-ai/frontend/src/lib/stores/buildingStore.ts` — building metadata state
- `D:/ailocal/acm-ai/frontend/src/lib/hooks/useBuildings.ts` — building query hook

**Investigate (research phase):**
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/notebooks/components/ChatColumn.tsx` — old chat feature
- `D:/ailocal/acm-ai/frontend/src/app/(dashboard)/jobs/[id]/chat/page.tsx` — current chat implementation
- `D:/ailocal/acm-ai/open_notebook/graphs/` — old OpenNotebook chat graph

---

## Plan

Read `docs/sprint-artifacts/task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: D:/ailocal/acm-ai/docs/sprint-artifacts/task_plan.md
- findings.md: D:/ailocal/acm-ai/docs/sprint-artifacts/findings.md
- progress.md: D:/ailocal/acm-ai/docs/sprint-artifacts/progress.md

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH

Load skills at the start of your session:
/dispatching-parallel-agents
/subagent-driven-development
/verification-before-completion

### Subagent Tasks

Dispatch the following subagents, using gates between phases:

#### Phase 1 — Research & Audit (dispatch in parallel)

##### Subagent A — Frontend Audit
Skills: /react-best-practices, /next-best-practices
Task:
1. Read every page file listed in Key Files above
2. For each page, document:
   - Current labels/headings (to verify renames needed)
   - Data displayed vs data available from backend APIs
   - Broken/missing UI elements (dropdowns, buttons, widgets)
   - Component imports and their current state
3. Write findings to `findings.md`
Expected output: Comprehensive audit report in `findings.md` with per-page status

##### Subagent B — Chat Feature Research
Skills: (none — read-only investigation)
Task:
1. Find the old OpenNotebook chat system (pre-CopilotKit)
2. Review `ChatColumn.tsx` and any related graph/backend components
3. Document: What features existed? How did it work? What's different from CopilotKit?
4. Write comparison to `findings.md` under "Chat Comparison" section
Expected output: Feature comparison matrix (OpenNotebook chat vs CopilotKit)

##### Subagent C — Data Flow Documentation
Skills: (none — read-only investigation)
Task:
1. Trace the 4-table data flow: `raw_extraction_table` → `acm_table_section` → `building_record` → `acm_record`
2. For each table: what fields exist, what populates it, what reads from it
3. Identify why ACM Register might show "empty" after extraction
4. Document in `findings.md` under "Data Flow" section
Expected output: Data flow documentation explaining table relationships and population triggers

**GATE 1:** After all Phase 1 subagents complete:
- Review `findings.md` for completeness
- Update `task_plan.md` with specific fix list per page
- Prioritize fixes: critical (broken) → high (missing data) → medium (labeling) → low (nice-to-have)

#### Phase 2 — Quick Wins (dispatch in parallel after Gate 1)

##### Subagent D — Label Renames & Filter Updates
Skills: /react-best-practices
Task:
1. `/extract` page: Rename "Raw Extracted Records" → "AI Mapped Records"
2. `/extract` page: Ensure "Raw Tables" label clearly differentiates from AI Mapped Records
3. `/jobs` page: Update filters to: All / Extracting / Reviewing / Published
4. `/source/[id]/raw` page: Add clear provider tab labels (Docling, MinerU) with descriptions
Expected output: Modified page files with correct labels and filters

##### Subagent E — Building Metadata Fields
Skills: /react-best-practices
Task:
1. `/review/buildings` page: Add missing fields from `building_record` schema:
   - `Building_Address__c` (Address)
   - `Suburb__c` (Suburb)
   - `Postcode__c` (Postcode)
   - `State__c` (State)
2. Read `BuildingRecord` type definition and backend API response to confirm field names
3. Add fields to the review form/display
Expected output: Building review page showing all metadata fields

**GATE 2:** After Phase 2 subagents complete:
- Run: `cd frontend && npm run lint`
- Run: `cd frontend && npm run build`
- Fix any build/lint errors before proceeding

#### Phase 3 — Complex Fixes (dispatch sequentially, depends on findings)

##### Subagent F — Dropdown/Picklist Fix
Skills: /react-best-practices
Task:
1. `/review/records` page: Diagnose broken dropdown editors (Friable, Condition, etc.)
2. Check AG Grid cell editor configuration for dependent picklists
3. Wire up `SalesforcePicklistValidator` data to cell editor options
4. Ensure dependent picklists work (e.g., Condition options depend on Friable value)
Expected output: Working dropdown cell editors with dependent picklist support

Context7: `resolve-library-id for "ag-grid" → query-docs for "cell editors custom cell editor component"`

##### Subagent G — Job Cards Metadata
Skills: /react-best-practices
Task:
1. `/jobs` page: Add metadata to job cards:
   - Raw extraction counts (Docling tables, MinerU tables)
   - AI Matched record count
   - Building count, ACM count
   - Location/Address info
2. May need to add/modify API endpoint for aggregated job stats
Expected output: Job cards displaying extraction metadata

##### Subagent H — Overview Page Enhancement
Skills: /react-best-practices
Task:
1. `/jobs/[id]` overview page: Add document, building, and PDF metadata sections
2. Wire up `GET /api/acm/intelligence/{source_id}` for document metadata
3. Display: consultant, site, date, document type, building count/names/page ranges, page count, TOC, file info
Expected output: Rich overview page with full document metadata

**GATE 3:** After Phase 3 subagents complete:
- Run: `cd frontend && npm run lint && npm run build`
- Browser verify: Navigate to each modified page, take screenshots
- Fix any regressions

#### Phase 4 — Integration & Advanced Features (sequential, high-risk)

##### Subagent I — ACM Table Integration
Skills: /react-best-practices, /next-best-practices
Task:
1. Integrate the `/acm` register table functionality into `/jobs/[id]` page
2. Add building table alongside item table (currently missing from ACM view)
3. Add provenance widget button to each row in the ACM table
4. Preserve existing working features: tabs, modal, edit from modal/row
Expected output: Unified job detail view with building table + ACM items + provenance

##### Subagent J — Provenance PDF Preview
Skills: /react-best-practices
Task:
1. Enhance `ProvenanceViewer` with PDF page preview
2. Render bbox overlay on the actual PDF page (highlighting extracted record region)
3. Wire up to row-level button in ItemGrid/ACM table
4. Use `table_bbox` data from `ACMRecord` for overlay coordinates
Expected output: Working provenance viewer with PDF bbox overlay

**GATE 4:** Final verification
- Run full verification checklist
- Browser verify all pages
- Document remaining issues (PDF renderer capabilities, chat decision)

### Integration Step (Main Agent)

After all subagents complete:
1. Review outputs from each subagent, resolve conflicts
2. Ensure consistent styling and component patterns across all modified pages
3. Run full verification checklist
4. Create commit with all changes

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "ag-grid" → query-docs for "cell editors dependent dropdown custom cell renderer"
2. resolve-library-id for "nextjs" → query-docs for "App Router dynamic routes layout groups"

---

## Verification Checklist

Run these commands in order before marking the session complete. All must pass.

- [ ] `cd frontend && npm run lint` — Frontend lint (0 errors)
- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] `uv run ruff check .` — Python lint (if backend changes made)
- [ ] `uv run pytest tests/ -x` — Backend tests (if backend changes made)
- [ ] Browser: Navigate to `/jobs` — verify filters and card metadata
- [ ] Browser: Navigate to `/jobs/{id}` — verify overview metadata sections
- [ ] Browser: Navigate to `/jobs/{id}/extract` — verify "AI Mapped Records" label
- [ ] Browser: Navigate to `/jobs/{id}/review/buildings` — verify Address/Suburb/Postcode/State fields
- [ ] Browser: Navigate to `/jobs/{id}/review/records` — verify dropdown editors open and work
- [ ] Browser: Navigate to `/source/{id}/raw` — verify provider tabs have clear labels
- [ ] Browser: Navigate to `/acm` — verify building table and provenance button present

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| NEW | 0 | — |
| MODIFY | ~15 | extract/page.tsx, buildings/page.tsx, records/page.tsx, jobs/page.tsx, jobs/[id]/page.tsx, source/[id]/page.tsx, source/[id]/raw/page.tsx, acm/page.tsx, ItemGrid.tsx, BuildingSidebar.tsx, ProvenanceViewer.tsx, buildingStore.ts, + others per findings |
| MOVE | 0 | — |
| DELETE | 0 | — |

---

## Commit Template

When work is complete, use this commit message structure:

```
fix(frontend): audit and fix UI issues across ACM pages

- Rename "Raw Extracted Records" → "AI Mapped Records" on extract page
- Add missing building metadata fields (Address, Suburb, Postcode, State)
- Fix broken dependent picklist dropdown editors in records grid
- Update job filters to status-based flow (All/Extracting/Reviewing/Published)
- Add document/building/PDF metadata to overview page
- Enhance job cards with extraction counts and building info
- Improve provider tab labeling on raw table view
- Integrate ACM register table with jobs detail view
- Add PDF bbox preview to provenance viewer

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```
