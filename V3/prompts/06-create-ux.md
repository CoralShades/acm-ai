# 06: Create UX Design — V3 UI Flows

> **BMAD Command:** `/bmad-bmm-create-ux-design`
> **Agent:** Sally — 🎨 UX Designer
> **Depends On:** 04-edit-prd (updated PRD with V3 UI FRs)
> **Output:** `_bmad-output/planning-artifacts/v3-ux-design.md`
> **Run in:** Fresh context window
> **Can run in parallel with:** 05-create-architecture

---

## Pre-Read Documents

- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — Updated PRD (FR-1800 series: UI flows)
- `V3/output/v3-party-mode-plan.md` — Party Mode consensus on UI flows (Topic 2)
- `V3/output/e30-multi-agent-audit-unified.md` — Section: "Quinn (QA)" for UI test requirements
- `V3/output/building_fields_summary.md` — SF Building__c fields (for building views)
- `V3/output/item_fields_summary.md` — SF Item__c fields (for item views, picklist dropdowns)

### Current Frontend (scan structure)
- `frontend/src/app/` — Current page structure
- `frontend/src/components/` — Current component library
- `frontend/src/components/ui/` — Shadcn/Radix base components available

---

## Prompt

```text
/bmad-bmm-create-ux-design

## V3 UX Design: New UI Flows for ACM-AI

### Context
ACM-AI V3 introduces significant new UI flows beyond the current single-view AG Grid. The frontend uses Next.js 15, React 19, Radix UI, Tailwind CSS 4, Zustand, and React Query. AG Grid is the spreadsheet component.

### Flows to Design

#### Flow 1: Upload Wizard
Multi-step wizard for document upload and extraction configuration:
1. **File Upload Step** — Drag-and-drop PDF upload (existing pattern, enhance)
2. **Provider Selection Step** — Choose extraction provider(s): Docling only, All providers, or specific combination. Show provider descriptions and expected accuracy.
3. **Document Type Step** — Confirm document type (SAMP report, asbestos register, audit report)
4. **Processing Options Step** — Configure: AI model preference, batch size, building detection mode
5. **Review + Submit Step** — Summary of selections, estimated processing time, submit button
6. **Progress Step** — Real-time SSE progress showing extraction by provider, consensus matching, AI processing. Record-by-record streaming into a preview table.

#### Flow 2: Raw Extracted Table View
After extraction completes, show raw provider output:
- AG Grid showing raw extracted data BEFORE AI processing
- Columns: provider source, page number, confidence, raw field values
- Inline editing — officers can correct raw data before AI processing
- Row highlighting by confidence level (HIGH=green, MEDIUM=yellow, LOW=red)
- "Send to AI Processing" button to trigger AI enrichment
- Save raw data to database (separate from AI-processed records)

#### Flow 3: Building List + Detail View
Two-level navigation for buildings:
- **Building List**: AG Grid showing all buildings for a source document
  - Columns: Building ID (BLD#001), Name, Address, Type, Category, Record Count, Status
  - Click row → drill into building detail
- **Building Detail**: Building__c fields in an editable form + child ACM items grid
  - Top section: Building fields (SF Building__c extractable fields)
  - Bottom section: AG Grid of ACM items for this building
  - Dependent picklist cascading: Building_Type → Category → Sub_Category

#### Flow 4: ACM Item Grid + Record Wizard
Detailed ACM item management:
- AG Grid with SF Item__c field columns
- Dependent picklist dropdowns: Friability → ACM_Classification → ACM_Sub_Classification
- Item_Name picklist (294 values) — filtered by selected ACM_Classification context
- Condition picklist: Poor, Fair, Stable, Unknown, N/A (negative), N/A (assumed negative)
- **Record Wizard**: Click edit on any row → opens a multi-step wizard:
  1. Classification step (Friability + Product Group + Product Type)
  2. Location step (Building, Level, Room, Internal/External)
  3. Assessment step (Condition, Disturbance Potential, Sample Result)
  4. Details step (Quantity, Assessor, Date, Recommendations, Comments)
  5. Review step (validation against SF picklists, warnings for mismatches)

#### Flow 5: Provenance Viewer
Click "Source" button on any record row:
- Side panel or modal opens showing extraction provenance
- **Source location**: PDF page number + table bounding box highlighted
- **Provider info**: Which provider(s) found this record, consensus confidence
- **AI processing**: Which model processed it, extraction confidence score
- **Edit history**: Timeline of all modifications (who, when, before/after values)
- **PDF viewer**: Embedded PDF.js viewer scrolled to the relevant page with bounding box overlay

#### Flow 6: Bulk Operations
Multi-select records for batch actions:
- Select multiple rows via checkboxes
- Actions: Bulk edit field, Bulk validate, Bulk export (CSV/Excel), Bulk delete
- Bulk edit: Choose field → set value → apply to all selected
- Validation: Run SF picklist validation on selected records, show results

### Design Requirements
- Follow existing Radix UI + Tailwind CSS 4 design system
- Dark mode support (existing design tokens)
- Responsive: desktop-first but functional on tablet
- Accessibility: ARIA labels on all interactive elements
- Loading states: Skeleton loaders for AG Grid, progress bars for operations
- Error states: Toast notifications for validation failures, inline error messages

### Deliverables
- Wireframes (ASCII/markdown) for each flow
- Component hierarchy diagram
- State management plan (which Zustand stores, which React Query queries)
- AG Grid column configuration specs (column defs for building grid + item grid)
- Navigation map showing how flows connect
- Dependent picklist interaction diagrams
```

---

## Verification Checklist

After running:
- [ ] UX design document created with all 6 flows
- [ ] Wireframes present for each flow
- [ ] Navigation map connecting all flows
- [ ] AG Grid column specs for building + item grids
- [ ] Dependent picklist interaction documented
- [ ] Provenance viewer panel designed
- [ ] State management plan included
