# Task Plan: Frontend UI Audit & Fix

## Workstream 1 — Research & Audit
- [ ] **1.1** Audit all page files: read current labels, data displayed, broken elements
- [ ] **1.2** Research old OpenNotebook chat (pre-CopilotKit) — document features, compare with CopilotKit
- [ ] **1.3** Trace 4-table data flow: `raw_extraction_table` → `acm_table_section` → `building_record` → `acm_record`
- [ ] **1.4** Document why ACM Register / building data might show "empty" after extraction
- [ ] **1.5** Prioritize fixes: critical → high → medium → low

## Workstream 2 — Quick Wins (Labels, Filters, Naming)
- [ ] **2.1** `/extract` page: Rename "Raw Extracted Records" → "AI Mapped Records"
- [ ] **2.2** `/extract` page: Clarify "Raw Tables" label (differentiate from AI Mapped)
- [ ] **2.3** `/jobs` page: Update filters to All / Extracting / Reviewing / Published
- [ ] **2.4** `/source/[id]/raw` page: Add clear provider tab labels with descriptions

## Workstream 3 — Missing Metadata
- [ ] **3.1** `/review/buildings` page: Add Building_Address__c, Suburb__c, Postcode__c, State__c fields
- [ ] **3.2** `/jobs` page: Add job card metadata (extraction counts, building count, ACM count, address)
- [ ] **3.3** `/jobs/[id]` overview: Add document metadata (consultant, site, date, type)
- [ ] **3.4** `/jobs/[id]` overview: Add building metadata (count, names, page ranges)
- [ ] **3.5** `/jobs/[id]` overview: Add PDF metadata (page count, TOC, file info)

## Workstream 4 — Bug Fixes
- [ ] **4.1** `/review/records` page: Fix broken dropdown cell editors (Friable, Condition, etc.)
- [ ] **4.2** Wire up dependent picklist validation to AG Grid cell editors
- [ ] **4.3** `/source/[id]/raw`: Fix provider tabs showing "0" or "Empty" — diagnose root cause

## Workstream 5 — Integration & Features
- [ ] **5.1** `/acm` page: Add Building Table alongside Item Table
- [ ] **5.2** `/acm` page: Add provenance widget button to each ACM record row
- [ ] **5.3** Integrate ACM register table functionality into `/jobs/[id]` detail view
- [ ] **5.4** `/jobs/[id]` page: Make grid ACM-specific (not generic) — add dropdowns, SF field alignment
- [ ] **5.5** ProvenanceViewer: Add PDF page preview with bbox overlay on source page

## Workstream 6 — Research Deliverables
- [ ] **6.1** Chat comparison: OpenNotebook chat vs CopilotKit — features matrix
- [ ] **6.2** PDF Markdown Renderer: Document current capabilities and gaps
- [ ] **6.3** Recommendation: which chat path forward (old OpenNotebook vs CopilotKit)

## Verification
- [ ] `cd frontend && npm run lint` — 0 errors
- [ ] `cd frontend && npm run build` — 0 errors
- [ ] `uv run ruff check .` — 0 errors (if backend changes)
- [ ] Browser verification of all modified pages
- [ ] Screenshots saved to sprint-artifacts/
