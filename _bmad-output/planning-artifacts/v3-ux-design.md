# ACM-AI V3 UX Design — Complete UI Flow Specification

> **Author:** Sally (UX Designer)
> **Date:** 2026-03-03
> **Status:** Draft — Ready for Review
> **Output of:** `/bmad-bmm-create-ux-design` (06-create-ux)
> **Input Documents:** PRD v3.0, Party Mode Plan, SF Field Summaries, Multi-Agent Audit, Current Frontend Scan
> **Tech Stack:** Next.js 15, React 19, Radix UI, Tailwind CSS 4, Zustand, React Query, AG Grid

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Navigation Map](#2-navigation-map)
3. [Flow 1: Upload Wizard](#3-flow-1-upload-wizard)
4. [Flow 2: Raw Extracted Table View](#4-flow-2-raw-extracted-table-view)
5. [Flow 3: Building List + Detail View](#5-flow-3-building-list--detail-view)
6. [Flow 4: ACM Item Grid + Record Wizard](#6-flow-4-acm-item-grid--record-wizard)
7. [Flow 5: Provenance Viewer](#7-flow-5-provenance-viewer)
8. [Flow 6: Bulk Operations](#8-flow-6-bulk-operations)
9. [Component Hierarchy](#9-component-hierarchy)
10. [State Management Plan](#10-state-management-plan)
11. [AG Grid Column Specifications](#11-ag-grid-column-specifications)
12. [Dependent Picklist Interaction Diagrams](#12-dependent-picklist-interaction-diagrams)
13. [Accessibility & Responsive Design](#13-accessibility--responsive-design)
14. [Loading & Error States](#14-loading--error-states)

---

## 1. Design Philosophy

### The Officer's Story

Picture Sarah, an asbestos compliance officer at a Victorian government school. She has a 48-page SAMP PDF on her desk. Today she needs to get every ACM record into Salesforce — accurately, with full provenance, before the audit deadline.

**Before ACM-AI:** Sarah opens the PDF, squints at table rows spanning pages, manually types 200+ records into spreadsheets, cross-references picklist values, makes typos, misses items on page 23. It takes 3 days.

**With ACM-AI V3:** Sarah drops the PDF, watches buildings appear one by one as extraction streams in, reviews inline validation badges, fixes 4 flagged records via the record wizard, verifies source pages in the provenance viewer, and exports two clean SF Data Loader CSVs. Done in 20 minutes.

### Design Principles

1. **Progressive disclosure** — Show what matters now, reveal complexity on demand
2. **Building-by-building workflow** — Matches how officers think (and how SF is structured)
3. **Confidence-first** — Color-coded badges let officers focus on what needs attention
4. **Source always available** — One click from any record to the source PDF page
5. **Never block, always guide** — Validation warns during editing, blocks only on export

### User Persona

| Attribute | Value |
|-----------|-------|
| **Role** | Compliance Officer / Hygienist |
| **Tech level** | Intermediate — comfortable with spreadsheets, not developer tools |
| **Primary goal** | Get accurate ACM data into Salesforce quickly |
| **Pain points** | Manual data entry, picklist mismatches, missing records, no provenance trail |
| **Device** | Desktop (primary), tablet (field review) |

---

## 2. Navigation Map

### Site Map

```
/                           → Dashboard (stats, recent jobs)
│
├── /jobs                   → Job List (all uploaded documents)
│   │
│   └── /jobs/[id]          → Job Detail (EVOLVES existing page)
│       │                     Tabs: Overview | Buildings | Records | Content | Raw Tables | Log
│       │
│       ├── /jobs/[id]/extract     → Extraction Progress (SSE streaming)
│       │
│       ├── /jobs/[id]/review
│       │   ├── /buildings         → Building List Grid
│       │   └── /records           → ACM Item Grid (per-building filter)
│       │
│       └── /jobs/[id]/chat        → CRUD Chat (existing)
│
├── /upload                 → Upload Wizard (NEW — replaces current upload flow)
│
├── /acm                    → ACM Register (cross-source view, existing)
│
├── /documents              → Document Library (existing)
│
├── /extraction-monitor     → Active/History extractions (existing)
│
└── /settings               → Configuration (existing)
    ├── /field-schema        → SF Field Schema Manager
    ├── /extraction          → Provider & Model Config
    ├── /bar-templates       → Export Templates
    └── /models              → AI Model Config
```

### Flow Connections

```
                    ┌──────────────┐
                    │   Dashboard  │
                    │   (stats)    │
                    └──────┬───────┘
                           │ "Upload Document" CTA
                           ▼
                    ┌──────────────┐
                    │Upload Wizard │──── Steps 1-3 ────┐
                    │ /upload      │                    │
                    └──────────────┘                    ▼
                                                ┌──────────────┐
                    ┌───────────────────────────│  Extraction   │
                    │  "View Raw Data"          │  Progress     │
                    │  (opt-in link)            │ /jobs/[id]/   │
                    │                           │   extract     │
                    │                           └──────┬───────┘
                    ▼                                  │ auto-redirect on complete
             ┌──────────────┐                          ▼
             │  Raw Table   │◄─── tab ────┌──────────────────┐
             │  View        │             │   Job Detail      │
             │  (Raw Tables │             │   /jobs/[id]      │
             │   tab)       │             │                   │
             └──────────────┘             │  ┌─────────────┐  │
                                          │  │ Buildings   │  │
                                          │  │ tab         │  │
                    ┌─────────────────────│  └──────┬──────┘  │
                    │ click row           │         │          │
                    ▼                     │         ▼          │
             ┌──────────────┐             │  ┌─────────────┐  │
             │  Record      │◄── edit ────│  │ Records tab │  │
             │  Wizard      │  button     │  │ (Item Grid) │  │
             │  (modal)     │             │  └──────┬──────┘  │
             └──────────────┘             │         │          │
                                          │         │ "Source" │
                                          │         │  button  │
                                          │         ▼          │
                                          │  ┌─────────────┐  │
                                          │  │ Provenance  │  │
                                          │  │ Viewer      │  │
                                          │  │ (slide-over)│  │
                                          │  └─────────────┘  │
                                          │                   │
                                          │  ┌─────────────┐  │
                                          │  │Bulk Actions  │  │
                                          │  │ (toolbar)    │  │
                                          │  └─────────────┘  │
                                          └───────────────────┘
```

### Key Navigation Decisions

| Decision | Rationale |
|----------|-----------|
| Upload Wizard is a standalone `/upload` route | Focused flow, no distractions. Redirects to extraction progress on submit |
| Raw Table is a tab on Job Detail, not a separate route | Opt-in — officers see it when they want it, not forced into the flow |
| Provenance is a Sheet (slide-over), not a separate page | Officers need to see provenance while looking at the grid — no context switch |
| Record Wizard is a Dialog (modal), not a page | Quick edit flow — officer fixes one record and is back in the grid |
| Building/Record views are tabs on Job Detail | Evolves existing pattern. Officers don't need to navigate away from their job |

---

## 3. Flow 1: Upload Wizard

### User Story

> As a compliance officer, I want to upload a SAMP PDF and configure extraction so that I can start processing with minimal clicks.

### Party Mode Decision

Upload → Progress (SSE) → Building Grid. **3 steps** (simplified from 6): drop PDF, select provider mode (Quick/Thorough), extract. AI model selection is invisible to officers (admin settings only).

### Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Jobs                                   ACM-AI       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│        ① Upload ──────── ② Configure ──────── ③ Extract        │
│         [●]                 [ ]                   [ ]           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │                                                         │    │
│  │              ┌──────────────────────────┐               │    │
│  │              │                          │               │    │
│  │              │    📄  Drop PDF here     │               │    │
│  │              │                          │               │    │
│  │              │   or click to browse     │               │    │
│  │              │                          │               │    │
│  │              │   PDF up to 50MB         │               │    │
│  │              └──────────────────────────┘               │    │
│  │                                                         │    │
│  │  Selected: broadmeadows-samp-2024.pdf (12.4 MB)        │    │
│  │  48 pages detected                                      │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [Cancel]                                          [Next →]     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Step 2: Configure

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Jobs                                   ACM-AI       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│        ① Upload ──────── ② Configure ──────── ③ Extract        │
│         [✓]                 [●]                   [ ]           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  Document Type                                          │    │
│  │  ┌───────────────────────────────────────────────┐      │    │
│  │  │ ● SAMP Report (School Asbestos Mgmt Plan)    │      │    │
│  │  │ ○ Asbestos Register                           │      │    │
│  │  │ ○ Audit Report                                │      │    │
│  │  └───────────────────────────────────────────────┘      │    │
│  │                                                         │    │
│  │  Extraction Mode                                        │    │
│  │  ┌───────────────────────────────────────────────┐      │    │
│  │  │ ● Quick (Docling only)         ~20 seconds    │      │    │
│  │  │   Best for clean, well-formatted PDFs         │      │    │
│  │  │                                               │      │    │
│  │  │ ○ Thorough (Docling + MinerU)   ~45 seconds   │      │    │
│  │  │   Uses AI vision for complex tables.          │      │    │
│  │  │   Best for scanned or multi-page tables.      │      │    │
│  │  └───────────────────────────────────────────────┘      │    │
│  │                                                         │    │
│  │  Site Configuration (optional)                          │    │
│  │  ┌───────────────────────────────────────────────┐      │    │
│  │  │ Department: [Select...]           ▾           │      │    │
│  │  │ Organisation: [Select...]         ▾           │      │    │
│  │  └───────────────────────────────────────────────┘      │    │
│  │  These fields are not extractable from the document.    │    │
│  │  Set them here to apply to all records.                 │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [← Previous]                                      [Next →]     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Review & Extract

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Jobs                                   ACM-AI       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│        ① Upload ──────── ② Configure ──────── ③ Extract        │
│         [✓]                 [✓]                   [●]           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  Review Your Extraction                                 │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────┐        │    │
│  │  │ Document   broadmeadows-samp-2024.pdf       │        │    │
│  │  │ Pages      48                               │        │    │
│  │  │ Type       SAMP Report                      │        │    │
│  │  │ Mode       Thorough (Docling + MinerU)      │        │    │
│  │  │ Est. Time  ~45 seconds                      │        │    │
│  │  │ Department Dept. of Education                │        │    │
│  │  └─────────────────────────────────────────────┘        │    │
│  │                                                         │    │
│  │  After extraction, you'll see buildings and ACM         │    │
│  │  records appear in real-time. You can start reviewing   │    │
│  │  completed buildings while extraction continues.        │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [← Previous]                               [Start Extraction] │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Extraction Progress (auto-navigated after submit)

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Jobs           broadmeadows-samp-2024    ACM-AI     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Extracting...                              38% · ~28s left     │
│  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Pipeline Stages                                          │   │
│  │                                                          │   │
│  │  ✅ Structure Analysis          2.1s                     │   │
│  │  ✅ Docling Extraction          8.4s                     │   │
│  │  🔄 MinerU Extraction           12.1s (running)         │   │
│  │  ⬜ Consensus Merge             —                        │   │
│  │  ⬜ AI Extraction               —                        │   │
│  │  ⬜ Validation                  —                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Buildings Found (3)                                      │   │
│  │                                                          │   │
│  │  ✅ BLD#001 Main Building        12 records  [Review →]  │   │
│  │  🔄 BLD#002 Portable Classroom   extracting...           │   │
│  │  ⬜ BLD#003 Gymnasium            queued                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  💡 You can review completed buildings while extraction         │
│     continues. Click "Review →" on any completed building.      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
UploadWizardPage (/upload)
├── Wizard (existing ui/wizard)
│   ├── WizardProgress
│   ├── WizardContent
│   │   ├── WizardStepContent[upload]
│   │   │   └── FileDropzone (existing, enhanced)
│   │   │       └── PDF page count preview
│   │   ├── WizardStepContent[configure]
│   │   │   ├── DocumentTypeSelector (RadioGroup)
│   │   │   ├── ExtractionModeSelector (RadioGroup)
│   │   │   └── SiteConfigForm (existing, embedded)
│   │   └── WizardStepContent[review]
│   │       └── ExtractionSummaryCard
│   └── WizardFooter

ExtractionProgressPage (/jobs/[id]/extract)
├── ExtractionProgressHeader
│   └── ProgressBar (animated, percentage + ETA)
├── PipelineStageList
│   └── PipelineStageRow[] (icon + name + duration + status)
├── BuildingCardList
│   └── BuildingCard[] (id, name, record count, status, [Review →])
└── ExtractionHintBanner (dismissible)
```

---

## 4. Flow 2: Raw Extracted Table View

### User Story

> As a compliance officer, I want to review raw extraction output before AI processing so that I can correct obvious errors at the source.

### Party Mode Decision

Raw table review is **opt-in** — accessed via "Raw Tables" tab on Job Detail. Not part of the default flow. Raw data is always saved regardless of whether the officer reviews it.

### Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│  Job: broadmeadows-samp-2024                                    │
├─────────────────────────────────────────────────────────────────┤
│ Overview │ Buildings │ Records │ Content │[Raw Tables]│ Log     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Raw Extraction Output                                          │
│  Provider: Docling ▾ │ Page: All ▾ │ Confidence: All ▾         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ #  │Provider│Page│Confidence│Building    │Room      │... │   │
│  ├────┼────────┼────┼──────────┼────────────┼──────────┼────┤   │
│  │ 1  │Docling │ 12 │ 🟢 HIGH │Main Bldg   │Room 1    │    │   │
│  │ 2  │Docling │ 12 │ 🟢 HIGH │Main Bldg   │Room 2    │    │   │
│  │ 3  │MinerU  │ 12 │ 🟡 MED  │Main Bldg   │Room 1    │    │   │
│  │ 4  │Docling │ 13 │ 🔴 LOW  │Main Bldg   │Corridor  │    │   │
│  │ 5  │Docling │ 14 │ 🟢 HIGH │Portable 1  │Main Room │    │   │
│  │ 6  │MinerU  │ 14 │ 🟡 MED  │Portable 1  │Main Room │    │   │
│  │    │        │    │          │            │          │    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Legend: 🟢 HIGH (all providers agree)  🟡 MEDIUM (partial)     │
│          🔴 LOW (single provider)  🟠 CONTESTED (disagreement)  │
│                                                                 │
│  [Send to AI Processing]          Showing 6 of 42 raw rows     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Interaction Details

| Interaction | Behavior |
|-------------|----------|
| **Cell editing** | Double-click any cell to edit. Changes saved to `raw_extraction_table.officer_edits[]` |
| **Row color** | Background tint: green (HIGH), yellow (MEDIUM), red (LOW), orange (CONTESTED) |
| **Provider filter** | Dropdown to show only Docling, only MinerU, or All providers |
| **Page filter** | Number input or dropdown to filter by PDF page number |
| **Send to AI Processing** | Button triggers AI enrichment on raw data. Shows confirmation dialog: "This will re-run AI extraction using your corrected raw data. Existing AI-processed records will be replaced." |

### Component Hierarchy

```
RawTableTab (within Job Detail Tabs)
├── RawTableToolbar
│   ├── ProviderFilter (Select)
│   ├── PageFilter (Select)
│   ├── ConfidenceFilter (Select)
│   └── SendToAIButton (with ConfirmDialog)
├── RawTableGrid (DataGrid/AG Grid)
│   └── Custom cell renderers:
│       ├── ConfidenceBadgeRenderer (colored dot + text)
│       └── EditableCellRenderer (inline editing)
└── RawTableLegend
```

---

## 5. Flow 3: Building List + Detail View

### User Story

> As a compliance officer, I want to see all buildings in a document and drill into each one so that I can review and validate ACM records building by building.

### Party Mode Decision

Two-view layout: Building list sidebar + Item grid. Officers work one building at a time (matches SF workflow). Building IDs are server-assigned (`BLD#001`).

### Wireframe — Building Grid (Buildings Tab)

```
┌─────────────────────────────────────────────────────────────────┐
│  Job: broadmeadows-samp-2024          [Re-extract] [Export ▾]   │
├─────────────────────────────────────────────────────────────────┤
│ Overview │[Buildings]│ Records │ Content │ Raw Tables │ Log     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  3 Buildings · 31 Total Records · 2 Validation Issues           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │☐│Bldg ID  │Name              │Type    │Category │#Recs│⚠ │   │
│  ├──┼─────────┼──────────────────┼────────┼─────────┼─────┼──┤   │
│  │☐│BLD#001  │Main Building     │School  │Educati..│  18 │ 1│   │
│  │☐│BLD#002  │Portable Class. 1 │Classrm │Educati..│   8 │ 0│   │
│  │☐│BLD#003  │Gymnasium         │Gymnasi.│Educati..│   5 │ 1│   │
│  │  │         │                  │        │         │     │  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ⚠ = validation issues count. Click row to expand building.    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Wireframe — Building Detail (expanded view after clicking a row)

```
┌─────────────────────────────────────────────────────────────────┐
│  Job: broadmeadows-samp-2024                                    │
├─────────────────────────────────────────────────────────────────┤
│ Overview │[Buildings]│ Records │ Content │ Raw Tables │ Log     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ← All Buildings    BLD#001 — Main Building                     │
│                                                                 │
│  ┌── Building Details ──────────────────────────────────────┐   │
│  │                                                          │   │
│  │  Asset Name    [Main Building          ]                 │   │
│  │  Asset Type    [School                ▾]  ← picklist     │   │
│  │  Category      [Educational and tr... ▾]  ← dependent    │   │
│  │  Address       [123 School Road        ]                 │   │
│  │  Suburb        [Broadmeadows           ]                 │   │
│  │  Postcode      [3047                   ]                 │   │
│  │  State         [VIC                    ]                 │   │
│  │  Construction  [Brick veneer           ]                 │   │
│  │  Year Built    [1965                  ▾]                 │   │
│  │  Levels        [2                     ▾]                 │   │
│  │  Est. Size     [1200                   ] m²              │   │
│  │  Roof Type     [Metal                  ]                 │   │
│  │  Inspection    [2024-06-15             ]                 │   │
│  │                                                          │   │
│  │  [Save Changes]  [Reset]              Confidence: 92%    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌── ACM Items (18 records) ────────── [+ Add Record] ─────┐   │
│  │                                                          │   │
│  │  (AG Grid — see Flow 4 for full column spec)             │   │
│  │  │ # │Room     │Item Name │Friab │Prod Grp│Cond │⚠│ 📎 │   │
│  │  │ 1 │Room 1   │Ceiling   │Non-fr│Cement  │Fair │  │ 📎 │   │
│  │  │ 2 │Room 2   │Floor cov.│Non-fr│Vinyl   │Stab │  │ 📎 │   │
│  │  │ 3 │Corridor │Eave lini.│Friab │Cement  │Poor │🔴│ 📎 │   │
│  │  │...│         │          │      │        │     │  │    │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Building Detail — Editable Fields (from SF Building__c)

These are the **extractable** fields shown in the building detail form:

| Field | SF API Name | Input Type | Notes |
|-------|-------------|------------|-------|
| Asset Name | `Building_Name__c` | Text input | Required |
| Asset Type | `Building_Type__c` | Picklist (114 values) | Controller for Category |
| Asset Category | `Building_Category__c` | Dependent picklist (13 values) | Filtered by Type |
| Address | `Building_Address__c` | Text input | |
| Suburb | `Suburb__c` | Text input | |
| Postcode | `Postcode__c` | Text input | |
| State | `State__c` | Text input | Default: VIC |
| Construction Type | `Construction_Type__c` | Text input | Free text |
| Estimated Year Built | `Estimated_Year_Build_New__c` | Picklist (1700-2029) | |
| Number of Levels | `Number_of_Levels__c` | Picklist (2-100) | |
| Est. Size (m²) | `Est_Building_Size_m2__c` | Text input | Numeric |
| Roof Type | `Roof_Type__c` | Text input | Free text |
| Date of Inspection | `Date_of_Inspection__c` | Date picker | Read-only (formula) |
| Frequency of Use | `Frequency_of_Use__c` | Picklist (6 values) | |
| Public Access | `Public_Access__c` | Picklist (Yes/No) | |
| Owned or Leased | `Owned_or_Leased__c` | Picklist (2 values) | |

### Component Hierarchy

```
BuildingsTab (within Job Detail)
├── BuildingListView (default)
│   ├── BuildingSummaryBar (count, total records, issues)
│   ├── BuildingGrid (DataGrid/AG Grid)
│   │   └── BuildingRowActions (click → drill into detail)
│   └── BulkBuildingToolbar (when rows selected)
│
└── BuildingDetailView (when building selected)
    ├── BuildingDetailBreadcrumb ("← All Buildings > BLD#001")
    ├── BuildingDetailForm
    │   ├── BuildingTextField[] (for text fields)
    │   ├── BuildingPicklistField[] (for picklist fields)
    │   ├── DependentPicklistPair (Type → Category)
    │   ├── SaveButton + ResetButton
    │   └── ConfidenceBadge
    └── BuildingItemsGrid (AG Grid — ACM items for this building)
        ├── ItemGridToolbar (Add Record, bulk actions)
        └── ACMItemGrid (see Flow 4)
```

---

## 6. Flow 4: ACM Item Grid + Record Wizard

### User Story

> As a compliance officer, I want to review and edit individual ACM records with guided picklist selection so that the data matches Salesforce field requirements exactly.

### Wireframe — ACM Item Grid (Records Tab)

```
┌─────────────────────────────────────────────────────────────────┐
│  Job: broadmeadows-samp-2024                                    │
├─────────────────────────────────────────────────────────────────┤
│ Overview │ Buildings │[Records]│ Content │ Raw Tables │ Log     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Building: [All Buildings ▾] [BLD#001 Main] [BLD#002] [BLD#003]│
│                                                                 │
│  31 Records · 2 Validation Issues · [+ Add] [Bulk Actions ▾]   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │☐│ # │Bldg   │Room    │Item Name  │Friab  │Prod Grp│...  │   │
│  ├──┼───┼───────┼────────┼───────────┼───────┼────────┼─────┤   │
│  │☐│ 1 │BLD#001│Room 1  │Ceiling    │Non-fr.│Cement  │     │   │
│  │☐│ 2 │BLD#001│Room 1  │Wall lining│Non-fr.│Cement  │     │   │
│  │☐│ 3 │BLD#001│Room 2  │Floor cov. │Non-fr.│Vinyl   │     │   │
│  │☐│ 4 │BLD#001│Corridor│Eave lining│Friable│Cement  │ 🔴  │   │
│  │  │   │       │        │           │       │(f)     │     │   │
│  │☐│ 5 │BLD#001│Room 3  │Switchboard│Non-fr.│Cement  │     │   │
│  │  │   │       │        │           │       │        │     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  🔴 = validation error  🟠 = warning  🟡 = contested value     │
│                                                                 │
│  Row 4: Eave lining — Friable + "Cement (f)" is valid.          │
│  🔴 Condition is "Good" — not a valid SF value.                 │
│     Valid values: Poor, Fair, Stable, Unknown, N/A (negative),  │
│     N/A (assumed negative). [Fix →]                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Wireframe — Record Wizard (Modal)

Triggered by clicking "Edit" on any row or the [Fix →] link on a validation error.

```
┌─────────────────────────────────────────────────────────────────┐
│  ╔═══════════════════════════════════════════════════════════╗   │
│  ║  Edit ACM Record — BLD#001 / Room 1 / Ceiling            ║   │
│  ║                                                           ║   │
│  ║  ① Classification ── ② Location ── ③ Assessment ──       ║   │
│  ║  ④ Details ── ⑤ Review                                    ║   │
│  ║       [●]          [ ]          [ ]                       ║   │
│  ║                                                           ║   │
│  ║  ┌─────────────────────────────────────────────────┐      ║   │
│  ║  │                                                 │      ║   │
│  ║  │  Friability of Material                         │      ║   │
│  ║  │  ┌─────────────────────────────────┐            │      ║   │
│  ║  │  │ ● Non-friable                   │            │      ║   │
│  ║  │  │ ○ Friable                       │            │      ║   │
│  ║  │  └─────────────────────────────────┘            │      ║   │
│  ║  │                                                 │      ║   │
│  ║  │  ACM Product Group                              │      ║   │
│  ║  │  [Cement products           ▾]                  │      ║   │
│  ║  │  ℹ Filtered to Non-friable groups               │      ║   │
│  ║  │                                                 │      ║   │
│  ║  │  ACM Product Type                               │      ║   │
│  ║  │  [Compressed flat sheeting  ▾]                  │      ║   │
│  ║  │  ℹ Filtered to Cement products types            │      ║   │
│  ║  │                                                 │      ║   │
│  ║  │  Item Name                                      │      ║   │
│  ║  │  [Ceiling                   ▾] 🔍               │      ║   │
│  ║  │  ℹ 294 values — type to search                  │      ║   │
│  ║  │                                                 │      ║   │
│  ║  └─────────────────────────────────────────────────┘      ║   │
│  ║                                                           ║   │
│  ║  [Cancel]   [← Previous]                    [Next →]      ║   │
│  ║                                                           ║   │
│  ╚═══════════════════════════════════════════════════════════╝   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Record Wizard Steps

| Step | Fields | Validation |
|------|--------|------------|
| **1. Classification** | Friability, ACM Product Group (dependent), ACM Product Type (dependent), Item Name (searchable, 294 values) | Dependency chain: Friability → Group → Type. Item Name filtered by Product Group context |
| **2. Location** | Building (read-only), Level, Room or Area, Internal/External, Location in Room | Internal/External is picklist (Internal, External, External & Internal) |
| **3. Assessment** | Condition, Disturbance Potential, Sample Result, ASSEA Risk Level | Condition: Poor/Fair/Stable/Unknown/N/A(negative)/N/A(assumed negative). Sample: Positive/Assumed Positive/Negative/Assumed Negative/Negative-Treated as Positive |
| **4. Details** | Quantity, Units of Measure (auto), Assessor, Survey Date, Hygienist Recommendations, Additional Comments | Units auto-populated from ACM classification |
| **5. Review** | All fields summary, validation status | Red badges for invalid values, orange for warnings. "Save" button disabled until all errors resolved |

### Record Wizard — Step 5 Review

```
╔═══════════════════════════════════════════════════════════════╗
║  Edit ACM Record — BLD#001 / Room 1 / Ceiling                ║
║                                                               ║
║  ① Classification ── ② Location ── ③ Assessment ──           ║
║  ④ Details ── ⑤ Review                                        ║
║                              [●]                              ║
║                                                               ║
║  ┌─────────────────────────────────────────────────────┐      ║
║  │                                                     │      ║
║  │  Classification                                     │      ║
║  │    Friability:    Non-friable               ✅      │      ║
║  │    Product Group: Cement products           ✅      │      ║
║  │    Product Type:  Compressed flat sheeting  ✅      │      ║
║  │    Item Name:     Ceiling                   ✅      │      ║
║  │                                                     │      ║
║  │  Location                                           │      ║
║  │    Building:      BLD#001 Main Building     ✅      │      ║
║  │    Level:         Ground                    ✅      │      ║
║  │    Room:          Room 1                    ✅      │      ║
║  │    Int/Ext:       Internal                  ✅      │      ║
║  │                                                     │      ║
║  │  Assessment                                         │      ║
║  │    Condition:     Stable                    ✅      │      ║
║  │    Disturbance:   Low                       ✅      │      ║
║  │    Sample Result: Positive                  ✅      │      ║
║  │                                                     │      ║
║  │  Details                                            │      ║
║  │    Quantity:      25 m²                     ✅      │      ║
║  │    Assessor:      Smith Environmental       ✅      │      ║
║  │    Survey Date:   2024-06-15                ✅      │      ║
║  │                                                     │      ║
║  │  ✅ All fields valid for Salesforce export          │      ║
║  │                                                     │      ║
║  └─────────────────────────────────────────────────────┘      ║
║                                                               ║
║  [Cancel]   [← Previous]                    [Save Record]     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### AG Grid Cell Editors for Dependent Picklists

When an officer edits a cell directly in the grid (without opening the wizard), dependent picklist columns use custom AG Grid cell editors:

```
AG Grid Cell Edit Flow (Friability column):

  ┌────────────┐    User selects     ┌──────────────────┐
  │ Cell click  │──"Friable"────────→│ Product Group     │
  │ Friability  │                     │ cell auto-updates │
  │ [Non-fri ▾]│                     │ filter to (f)     │
  └────────────┘                     │ variants only     │
                                     └────────┬─────────┘
                                              │
                                     ┌────────▼─────────┐
                                     │ Product Type      │
                                     │ cell auto-updates │
                                     │ filter to friable │
                                     │ types only        │
                                     └──────────────────┘
```

### Component Hierarchy

```
RecordsTab (within Job Detail)
├── BuildingTabFilter (existing — building pill selector)
├── ItemGridToolbar
│   ├── AddRecordButton
│   ├── BulkActionsDropdown (see Flow 6)
│   ├── ValidationSummary ("2 issues")
│   └── RecordCount
├── ACMItemGrid (DataGrid/AG Grid)
│   ├── CheckboxColumn (for multi-select)
│   ├── RowNumberColumn
│   ├── BuildingColumn (text, filterable)
│   ├── RoomColumn (text, editable)
│   ├── ItemNameColumn (picklist editor, 294 values, searchable)
│   ├── FriabilityColumn (picklist editor, 2 values)
│   ├── ProductGroupColumn (dependent picklist editor)
│   ├── ProductTypeColumn (dependent picklist editor)
│   ├── ConditionColumn (picklist editor, 6 values)
│   ├── DisturbanceColumn (picklist editor, 5 values)
│   ├── SampleResultColumn (picklist editor, 5 values)
│   ├── QuantityColumn (numeric editor)
│   ├── ValidationBadgeColumn (colored icons)
│   └── ProvenanceButtonColumn (📎 → opens Provenance Viewer)
├── ValidationMessageBar (contextual, shows for selected row)
└── RecordWizardDialog (modal — opened by edit action)
    ├── Wizard (existing ui/wizard)
    │   ├── ClassificationStep
    │   │   ├── FriabilityRadioGroup
    │   │   ├── ProductGroupSelect (dependent)
    │   │   ├── ProductTypeSelect (dependent)
    │   │   └── ItemNameCombobox (searchable, 294 values)
    │   ├── LocationStep
    │   │   ├── BuildingField (read-only)
    │   │   ├── LevelInput
    │   │   ├── RoomInput
    │   │   └── InternalExternalSelect
    │   ├── AssessmentStep
    │   │   ├── ConditionSelect
    │   │   ├── DisturbanceSelect
    │   │   └── SampleResultSelect
    │   ├── DetailsStep
    │   │   ├── QuantityInput + UnitsDisplay (auto)
    │   │   ├── AssessorInput
    │   │   ├── SurveyDatePicker
    │   │   ├── RecommendationsTextarea
    │   │   └── CommentsTextarea
    │   └── ReviewStep
    │       ├── FieldSummaryList (all fields with ✅/🔴)
    │       └── ValidationResult
    └── WizardFooter (Save Record)
```

---

## 7. Flow 5: Provenance Viewer

### User Story

> As a compliance officer, I want to see exactly where a record came from in the source PDF so that I can verify extraction accuracy and demonstrate audit compliance.

### Party Mode Decision

Slide-over panel: top = PDF page + bbox highlight, bottom = lineage table. Cell-level coordinates stored. PDF.js for rendering.

### Wireframe — Provenance Slide-Over

```
┌─────────────── Main Content ──────────┬──── Provenance Panel (480px) ────┐
│                                       │                                   │
│  (AG Grid continues visible           │  📎 Source: BLD#001 / Room 1 /   │
│   behind the slide-over)              │     Ceiling                  [✕] │
│                                       │                                   │
│                                       │  ┌────────────────────────────┐   │
│                                       │  │                            │   │
│                                       │  │   ┌──────────────────┐    │   │
│                                       │  │   │ PDF Page 12      │    │   │
│                                       │  │   │                  │    │   │
│                                       │  │   │  ┌─── bbox ──┐  │    │   │
│                                       │  │   │  │ ▓▓▓▓▓▓▓▓▓ │  │    │   │
│                                       │  │   │  │ ▓ ROW 3  ▓ │  │    │   │
│                                       │  │   │  │ ▓▓▓▓▓▓▓▓▓ │  │    │   │
│                                       │  │   │  └───────────┘  │    │   │
│                                       │  │   │                  │    │   │
│                                       │  │   └──────────────────┘    │   │
│                                       │  │                            │   │
│                                       │  │   Page [12] of 48  [◀][▶] │   │
│                                       │  └────────────────────────────┘   │
│                                       │                                   │
│                                       │  ┌── Extraction Lineage ──────┐   │
│                                       │  │                            │   │
│                                       │  │  Source Table               │   │
│                                       │  │    Page: 12                 │   │
│                                       │  │    Table: 2 of 3           │   │
│                                       │  │    Row: 3                   │   │
│                                       │  │    Bbox: (52,340,510,28)   │   │
│                                       │  │                            │   │
│                                       │  │  Providers                  │   │
│                                       │  │    Docling: ✅ Found (0.94) │   │
│                                       │  │    MinerU:  ✅ Found (0.87) │   │
│                                       │  │    Consensus: HIGH          │   │
│                                       │  │                            │   │
│                                       │  │  AI Processing              │   │
│                                       │  │    Model: Claude Sonnet     │   │
│                                       │  │    Confidence: 0.92         │   │
│                                       │  │    Processed: 2024-06-15    │   │
│                                       │  │                            │   │
│                                       │  │  Edit History               │   │
│                                       │  │    ┌───────────────────┐   │   │
│                                       │  │    │ 15 Jun — AI       │   │   │
│                                       │  │    │ Created from      │   │   │
│                                       │  │    │ extraction        │   │   │
│                                       │  │    ├───────────────────┤   │   │
│                                       │  │    │ 15 Jun — Officer  │   │   │
│                                       │  │    │ Condition:        │   │   │
│                                       │  │    │ "Good" → "Stable" │   │   │
│                                       │  │    └───────────────────┘   │   │
│                                       │  │                            │   │
│                                       │  └────────────────────────────┘   │
│                                       │                                   │
└───────────────────────────────────────┴───────────────────────────────────┘
```

### Interaction Details

| Interaction | Behavior |
|-------------|----------|
| **Open** | Click 📎 (Source) button on any grid row → Sheet slides in from right |
| **PDF navigation** | Page arrows to move through PDF. Auto-scrolls to the relevant page on open |
| **Bbox highlight** | Semi-transparent colored overlay on the bounding box coordinates. Animated pulse on open |
| **Close** | Click ✕ or press Escape. Grid remains interactive behind the overlay |
| **Edit history** | Timeline view. Most recent first. Shows field name, old value → new value, timestamp, actor (AI/Officer) |
| **No bbox** | If record has no bbox data (regex-extracted), show "Page number only — no table coordinates available" |

### Component Hierarchy

```
ProvenanceSheet (Sheet/slide-over, right side, 480px)
├── ProvenanceHeader
│   ├── RecordIdentifier (Building / Room / Item)
│   └── CloseButton
├── PDFViewer (top half, ~50% height)
│   ├── PDFPageRenderer (PDF.js canvas)
│   ├── BboxOverlay (absolutely positioned div with border + semi-transparent fill)
│   └── PageNavigator (current page / total, prev/next buttons)
├── ProvenanceDetails (bottom half, scrollable)
│   ├── SourceTableSection
│   │   └── PageNumber, TableIndex, RowIndex, Bbox coordinates
│   ├── ProvidersSection
│   │   └── ProviderRow[] (icon, name, found/not-found, confidence)
│   ├── AIProcessingSection
│   │   └── ModelName, Confidence, ProcessedDate
│   └── EditHistoryTimeline
│       └── EditHistoryEntry[] (date, actor, field, old→new)
└── ProvenanceFooter (optional: "Open in full PDF viewer" link)
```

---

## 8. Flow 6: Bulk Operations

### User Story

> As a compliance officer, I want to select multiple records and perform batch actions so that I can efficiently fix common issues across many records at once.

### Wireframe — Bulk Actions Toolbar (appears when rows selected)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌── Bulk Actions (12 selected) ────────────────────────────┐   │
│  │                                                          │   │
│  │  [Edit Field ▾]  [Validate]  [Export ▾]  [Delete]        │   │
│  │                                          ────────        │   │
│  │  [Clear Selection]                       (destructive)   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Wireframe — Bulk Edit Dialog

```
╔═══════════════════════════════════════════════════════════════╗
║  Bulk Edit — 12 Records Selected                              ║
║                                                               ║
║  Select the field to update:                                  ║
║  ┌───────────────────────────────────────┐                    ║
║  │ Condition                          ▾  │                    ║
║  └───────────────────────────────────────┘                    ║
║                                                               ║
║  New value:                                                   ║
║  ┌───────────────────────────────────────┐                    ║
║  │ Stable                             ▾  │                    ║
║  └───────────────────────────────────────┘                    ║
║                                                               ║
║  Preview:                                                     ║
║  ┌─────────────────────────────────────────────────────┐      ║
║  │ 12 records will be updated:                         │      ║
║  │                                                     │      ║
║  │   8 records: "Good" → "Stable"                      │      ║
║  │   3 records: "Unknown" → "Stable"                   │      ║
║  │   1 record:  "Fair" → "Stable"                      │      ║
║  │                                                     │      ║
║  │ ⚠ This action cannot be undone.                     │      ║
║  └─────────────────────────────────────────────────────┘      ║
║                                                               ║
║  [Cancel]                                   [Apply to 12]     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### Wireframe — Bulk Validate Results

```
╔═══════════════════════════════════════════════════════════════╗
║  Validation Results — 12 Records                              ║
║                                                               ║
║  ┌─────────────────────────────────────────────────────┐      ║
║  │                                                     │      ║
║  │  ✅ 9 records passed all validation checks          │      ║
║  │                                                     │      ║
║  │  🔴 3 records have validation errors:               │      ║
║  │                                                     │      ║
║  │  BLD#001 / Corridor / Eave lining                   │      ║
║  │    Condition: "Good" is not a valid SF value         │      ║
║  │    [Fix → Stable]                                   │      ║
║  │                                                     │      ║
║  │  BLD#002 / Main Room / Floor covering               │      ║
║  │    Product Type: "Vinyl floor tiles" not found       │      ║
║  │    Closest match: "Vinyl tiles" [Apply]              │      ║
║  │                                                     │      ║
║  │  BLD#003 / Lab / Switchboard                        │      ║
║  │    Friability + Product Group mismatch               │      ║
║  │    "Non-friable" + "Insulation products (f)"         │      ║
║  │    [Open Record Wizard]                              │      ║
║  │                                                     │      ║
║  └─────────────────────────────────────────────────────┘      ║
║                                                               ║
║  [Fix All Auto-Fixable (2)]                       [Close]     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### Bulk Operations Summary

| Operation | Trigger | Behavior |
|-----------|---------|----------|
| **Bulk Edit** | Select field → select value → apply | Shows preview of changes (grouped by old value). Confirmation required. Saves edit history per record |
| **Bulk Validate** | Click "Validate" | Runs SF picklist validation on selected records. Shows pass/fail results with suggested fixes. "Fix All Auto-Fixable" for simple corrections |
| **Bulk Export** | Export → CSV or Excel | Exports only selected records. Applies SF field name mapping. Validates before export (blocks if errors) |
| **Bulk Delete** | Click "Delete" | Destructive — requires typing "DELETE" to confirm. Records are soft-deleted (flagged, not removed from DB) |

### Component Hierarchy

```
BulkActionsToolbar (floats above grid when rows selected)
├── SelectionCount ("12 selected")
├── BulkEditButton → BulkEditDialog
│   ├── FieldSelector (Select)
│   ├── ValueSelector (Select — dynamic based on field)
│   ├── ChangePreview (grouped by old value)
│   └── ApplyButton (with confirmation)
├── BulkValidateButton → BulkValidateDialog
│   ├── ValidationResultsList
│   │   ├── PassedCount
│   │   └── FailedRecordRow[] (with suggested fixes)
│   └── FixAllButton (auto-fixable only)
├── BulkExportDropdown
│   ├── ExportCSV
│   └── ExportExcel
├── BulkDeleteButton → ConfirmDialog (type "DELETE" to confirm)
└── ClearSelectionButton
```

---

## 9. Component Hierarchy — Full Application

```
App (layout.tsx)
├── DashboardLayout
│   ├── AppShell (sidebar + header)
│   │   ├── Sidebar
│   │   │   ├── WORKSPACE section
│   │   │   │   ├── Dashboard (/)
│   │   │   │   ├── Jobs (/jobs)
│   │   │   │   ├── ACM Register (/acm)
│   │   │   │   ├── Documents (/documents)
│   │   │   │   └── Upload (/upload)  ← NEW
│   │   │   └── CONFIGURE section
│   │   │       ├── Extraction Monitor
│   │   │       └── Settings
│   │   └── TopHeader (breadcrumbs, user menu)
│   │
│   ├── UploadWizardPage (/upload) ← NEW
│   │
│   ├── JobDetailPage (/jobs/[id]) ← EVOLVED
│   │   ├── JobDetailHeader
│   │   ├── TabContainer
│   │   │   ├── OverviewTab (existing)
│   │   │   ├── BuildingsTab ← ENHANCED
│   │   │   │   ├── BuildingListView
│   │   │   │   │   └── BuildingGrid
│   │   │   │   └── BuildingDetailView ← NEW
│   │   │   │       ├── BuildingDetailForm
│   │   │   │       └── BuildingItemsGrid
│   │   │   ├── RecordsTab ← ENHANCED
│   │   │   │   ├── BuildingTabFilter
│   │   │   │   ├── ACMItemGrid ← ENHANCED (SF columns, dependent picklists)
│   │   │   │   ├── BulkActionsToolbar ← NEW
│   │   │   │   └── ValidationMessageBar ← NEW
│   │   │   ├── ContentTab (existing)
│   │   │   ├── RawTablesTab ← ENHANCED
│   │   │   │   └── RawTableGrid (with provider/confidence columns)
│   │   │   └── ExtractionLogTab (existing)
│   │   ├── ChatPanel (existing)
│   │   ├── ProvenanceSheet ← NEW (slide-over)
│   │   └── RecordWizardDialog ← NEW (modal)
│   │
│   └── ExtractionProgressPage (/jobs/[id]/extract) ← ENHANCED
│       ├── ExtractionProgressHeader
│       ├── PipelineStageList
│       └── BuildingCardList
│
├── Providers (existing)
│   ├── QueryProvider
│   ├── ThemeProvider
│   └── CopilotProvider
│
└── UI Primitives (existing + new)
    ├── Wizard (existing)
    ├── DataGrid (existing AG Grid wrapper)
    ├── Sheet (existing Radix slide-over)
    ├── Dialog (existing Radix modal)
    ├── Select, RadioGroup, Tabs, Button, etc.
    ├── DependentPicklistEditor ← NEW (AG Grid cell editor)
    ├── SearchableCombobox ← NEW (for Item_Name 294 values)
    ├── ConfidenceBadge ← NEW
    ├── ValidationBadge ← NEW
    └── PDFPageViewer ← NEW (PDF.js wrapper)
```

---

## 10. State Management Plan

### Zustand Stores

| Store | Purpose | Key State |
|-------|---------|-----------|
| `useUploadStore` | Upload wizard state | `file`, `documentType`, `extractionMode`, `siteConfig`, `isUploading` |
| `useExtractionStreamStore` | SSE extraction progress | `stages[]`, `buildings[]`, `currentStage`, `progress`, `eta`, `isComplete` |
| `useBuildingStore` | Selected building for detail view | `selectedBuildingId`, `buildingFormDirty`, `buildingFormValues` |
| `useBulkSelectionStore` | Multi-select state for bulk ops | `selectedRecordIds: Set<string>`, `isAllSelected`, `selectionCount` |
| `useProvenanceStore` | Provenance panel state | `isOpen`, `selectedRecordId`, `pdfPage`, `bbox` |
| `useRecordWizardStore` | Record wizard state | `isOpen`, `recordId`, `currentStep`, `formValues`, `validationErrors` |

### React Query Keys & Queries

| Query Key | Endpoint | Cache Policy |
|-----------|----------|-------------|
| `['sources', sourceId]` | `GET /api/sources/{id}` | staleTime: 30s |
| `['acm-records', sourceId, buildingId?]` | `GET /api/acm/records?source_id=...&building_id=...` | staleTime: 30s, refetch on SSE signal |
| `['building-records', sourceId]` | `GET /api/acm/buildings?source_id=...` | staleTime: 30s |
| `['building-detail', buildingId]` | `GET /api/acm/buildings/{id}` | staleTime: 60s |
| `['raw-tables', sourceId]` | `GET /api/acm/raw-tables?source_id=...` | staleTime: 60s |
| `['field-schema']` | `GET /api/acm/field-schema` | staleTime: 5min (picklist data rarely changes) |
| `['extraction-progress', commandId]` | `GET /api/acm/extraction-progress/{id}` | refetchInterval: 3s while running |
| `['provenance', recordId]` | `GET /api/acm/records/{id}/provenance` | staleTime: 60s |
| `['acm-stats', sourceId]` | `GET /api/acm/stats?source_id=...` | staleTime: 30s |

### SSE Event Flow

```
SSE Source: /api/acm/extraction-progress/{commandId}/stream

Events:
  → stage_started {stage_id, stage_name}
  → stage_completed {stage_id, duration_ms}
  → building_found {building_id, building_name, page}
  → building_completed {building_id, record_count}
  → record_validated {record_id, building_id, validation_status}
  → extraction_completed {total_buildings, total_records, duration_ms}
  → extraction_failed {error, stage_id}

Frontend handling:
  SSE event → useExtractionStreamStore.update()
            → React Query invalidateQueries(['acm-records', sourceId])
            → AG Grid data refreshes automatically
```

### State Flow Diagram

```
Upload Wizard                Extraction Progress              Job Detail
─────────────               ───────────────────              ──────────

useUploadStore ──submit──→  useExtractionStreamStore ──complete──→ React Query
  file                        SSE connection                       ['acm-records']
  documentType                stages[]                             ['building-records']
  extractionMode              buildings[]                          ['acm-stats']
  siteConfig                  progress %
                              ↓ SSE events
                              invalidateQueries()

                                                              useBuildingStore
                                                                selectedBuildingId
                                                                ↓
                                                              useBulkSelectionStore
                                                                selectedRecordIds
                                                                ↓
                                                              useProvenanceStore
                                                                isOpen, recordId
                                                                ↓
                                                              useRecordWizardStore
                                                                isOpen, recordId, step
```

---

## 11. AG Grid Column Specifications

### Building Grid Column Definitions

```typescript
const buildingColumnDefs: ColDef<BuildingRecord>[] = [
  {
    headerCheckboxSelection: true,
    checkboxSelection: true,
    width: 50,
    pinned: 'left',
    suppressMenu: true,
  },
  {
    field: 'internal_id',
    headerName: 'Bldg ID',
    width: 100,
    pinned: 'left',
    sort: 'asc',
  },
  {
    field: 'building_name',
    headerName: 'Asset Name',
    minWidth: 180,
    flex: 1,
  },
  {
    field: 'building_address',
    headerName: 'Address',
    minWidth: 200,
    flex: 1,
  },
  {
    field: 'building_type',
    headerName: 'Asset Type',
    width: 150,
    cellEditor: 'agSelectCellEditor',
    cellEditorParams: { values: [] }, // loaded from field_schema
  },
  {
    field: 'building_category',
    headerName: 'Category',
    width: 180,
    cellEditor: 'dependentPicklistEditor', // CUSTOM
    cellEditorParams: {
      dependsOn: 'building_type',
      schemaField: 'Building_Category__c',
    },
  },
  {
    field: 'suburb',
    headerName: 'Suburb',
    width: 130,
  },
  {
    field: 'postcode',
    headerName: 'Postcode',
    width: 90,
  },
  {
    field: 'construction_type',
    headerName: 'Construction',
    width: 130,
  },
  {
    field: 'estimated_year_built',
    headerName: 'Year Built',
    width: 100,
  },
  {
    field: 'number_of_levels',
    headerName: 'Levels',
    width: 80,
  },
  {
    headerName: '# Records',
    valueGetter: (params) => params.data?.acm_record_count ?? 0,
    width: 95,
  },
  {
    headerName: '⚠',
    field: 'validation_issue_count',
    width: 60,
    cellRenderer: 'validationBadgeRenderer',
  },
  {
    field: 'extraction_confidence',
    headerName: 'Confidence',
    width: 100,
    cellRenderer: 'confidenceBadgeRenderer',
  },
];
```

### ACM Item Grid Column Definitions

```typescript
const itemColumnDefs: ColDef<ACMRecord>[] = [
  // Selection
  {
    headerCheckboxSelection: true,
    checkboxSelection: true,
    width: 50,
    pinned: 'left',
  },
  // Row number
  {
    headerName: '#',
    valueGetter: 'node.rowIndex + 1',
    width: 55,
    pinned: 'left',
  },
  // Building (filterable, not editable in grid)
  {
    field: 'building_name',
    headerName: 'Building',
    width: 130,
    pinned: 'left',
    filter: 'agTextColumnFilter',
  },
  // Location fields
  {
    field: 'level',
    headerName: 'Level',
    width: 80,
    editable: true,
  },
  {
    field: 'room_or_area',
    headerName: 'Room/Area',
    width: 130,
    editable: true,
  },
  {
    field: 'internal_external',
    headerName: 'Int/Ext',
    width: 100,
    cellEditor: 'agSelectCellEditor',
    cellEditorParams: {
      values: ['Internal', 'External', 'External & Internal'],
    },
  },
  // Classification fields (dependent picklist chain)
  {
    field: 'friability_of_material',
    headerName: 'Friability',
    width: 110,
    cellEditor: 'agSelectCellEditor',
    cellEditorParams: {
      values: ['Non-friable', 'Friable'],
    },
    // On value change → triggers Product Group filter update
  },
  {
    field: 'acm_classification',
    headerName: 'Product Group',
    width: 180,
    cellEditor: 'dependentPicklistEditor',
    cellEditorParams: {
      dependsOn: 'friability_of_material',
      schemaField: 'ACM_Classification__c',
    },
  },
  {
    field: 'acm_sub_classification',
    headerName: 'Product Type',
    width: 220,
    cellEditor: 'dependentPicklistEditor',
    cellEditorParams: {
      dependsOn: 'acm_classification',
      schemaField: 'ACM_Sub_Classification__c',
    },
  },
  {
    field: 'item_name',
    headerName: 'Item Name',
    width: 180,
    cellEditor: 'searchableComboboxEditor',
    cellEditorParams: {
      schemaField: 'Item_Name__c',
      maxValues: 294,
    },
  },
  // Assessment fields
  {
    field: 'condition',
    headerName: 'Condition',
    width: 130,
    cellEditor: 'agSelectCellEditor',
    cellEditorParams: {
      values: ['Poor', 'Fair', 'Stable', 'Unknown',
               'N/A (negative)', 'N/A (assumed negative)'],
    },
    cellClassRules: {
      'bg-red-50 dark:bg-red-950': (params) => params.value === 'Poor',
      'bg-yellow-50 dark:bg-yellow-950': (params) => params.value === 'Fair',
    },
  },
  {
    field: 'disturbance_potential',
    headerName: 'Disturbance',
    width: 120,
    cellEditor: 'agSelectCellEditor',
    cellEditorParams: {
      values: ['Low', 'Moderate', 'High', 'N/A (negative)',
               'Unknown', 'N/A (assumed negative)'],
    },
  },
  {
    field: 'sample_result',
    headerName: 'Sample Result',
    width: 150,
    cellEditor: 'agSelectCellEditor',
    cellEditorParams: {
      values: ['Positive', 'Assumed Positive', 'Negative',
               'Assumed Negative', 'Negative - Treated as Positive'],
    },
  },
  // Quantity
  {
    field: 'quantity',
    headerName: 'Qty',
    width: 70,
    editable: true,
    type: 'numericColumn',
  },
  {
    field: 'units_of_measure',
    headerName: 'Unit',
    width: 60,
    editable: false, // auto-populated
  },
  // Metadata
  {
    field: 'assessor',
    headerName: 'Assessor',
    width: 150,
    editable: true,
  },
  {
    field: 'survey_date',
    headerName: 'Survey Date',
    width: 110,
    cellEditor: 'agDateCellEditor',
  },
  // Status columns
  {
    headerName: '⚠',
    field: 'validation_status',
    width: 50,
    cellRenderer: 'validationBadgeRenderer',
    // 🔴 red: invalid SF value
    // 🟠 orange: dependency chain mismatch
    // 🟡 yellow: contested consensus value
    // (empty): valid
  },
  {
    headerName: '📎',
    width: 50,
    cellRenderer: 'provenanceButtonRenderer',
    // Click → opens Provenance Sheet for this record
  },
  // Hidden by default (can be shown via column visibility)
  {
    field: 'page_number',
    headerName: 'Page',
    width: 60,
    hide: true,
  },
  {
    field: 'extraction_confidence',
    headerName: 'AI Confidence',
    width: 110,
    hide: true,
    cellRenderer: 'confidenceBadgeRenderer',
  },
  {
    field: 'consensus_tier',
    headerName: 'Consensus',
    width: 100,
    hide: true,
  },
  {
    field: 'hygienist_recommendations',
    headerName: 'Recommendations',
    width: 200,
    hide: true,
    editable: true,
  },
  {
    field: 'additional_comments',
    headerName: 'Comments',
    width: 200,
    hide: true,
    editable: true,
  },
];
```

---

## 12. Dependent Picklist Interaction Diagrams

### Chain 1: Building Type → Category

```
Building_Type__c (114 values)          Building_Category__c (13 values)
┌────────────────────┐                ┌───────────────────────────────┐
│ School             │ ──────────────→│ Educational and training      │
│ TAFE               │ ──────────────→│ Educational and training      │
│ Classroom          │ ──────────────→│ Educational and training      │
│ Education centre   │ ──────────────→│ Educational and training      │
│                    │                │                               │
│ Hospital           │ ──────────────→│ Health services               │
│ Health centre      │ ──────────────→│ Health services               │
│ Dental clinic      │ ──────────────→│ Health services               │
│                    │                │                               │
│ Prison             │ ──────────────→│ Correctional and justice      │
│ Court              │ ──────────────→│ Correctional and justice      │
│                    │                │                               │
│ Office             │ ──────────────→│ Offices and professional      │
│ Head office        │ ──────────────→│ Offices and professional      │
│                    │                │                               │
│ Factory            │ ──────────────→│ Factories, warehouses, shops  │
│ Warehouse          │ ──────────────→│ Factories, warehouses, shops  │
│ ...                │                │ ...                           │
└────────────────────┘                └───────────────────────────────┘

NOTE: No Sub_Category chain. Confirmed absent from SF schema (Q1 resolved).
```

### Chain 2: Friability → Product Group → Product Type

```
Friability (2 values)
┌──────────────┐
│ Non-friable  │ ────→ Shows groups WITHOUT (f) suffix:
│              │       "Cement products", "Vinyl products",
│              │       "Bitumen products", "Coatings", ...
│              │
│ Friable      │ ────→ Shows groups WITH (f) suffix:
│              │       "Cement products (f)", "Vinyl products (f)",
│              │       "Insulation products (f)", "Textiles (f)", ...
└──────────────┘

ACM_Classification (18 values: 9 non-friable + 9 friable)
┌──────────────────────┐
│ Cement products      │ ────→ Shows types:
│                      │       "Compressed flat sheeting",
│                      │       "Corrugated roof sheeting",
│                      │       "Cement pipe", "Cement flue",
│                      │       "Flat sheeting", "Moulded cement...",
│                      │       "Ridge capping", ...
│                      │
│ Vinyl products       │ ────→ Shows types:
│                      │       "Vinyl sheet", "Vinyl tiles",
│                      │       "Vinyl tiles and adhesive",
│                      │       "Hessian backed vinyl sheet", ...
│                      │
│ Insulation products  │ ────→ Shows types:
│ (f)                  │       "Sprayed insulation",
│                      │       "Sprayed insulation (Limpet)",
│                      │       "Loose fill insulation",
│                      │       "Boiler insulation",
│                      │       "Foam insulation", ...
└──────────────────────┘

ACM_Sub_Classification (233 unique values across all groups)
  → Filtered by selected ACM_Classification
```

### Chain Behavior in AG Grid

```
User edits Friability cell:
  1. Cell value changes to "Friable"
  2. AG Grid fires onCellValueChanged
  3. Event handler checks: is this cell a controller?
     → Yes: Friability controls ACM_Classification
  4. Fetch valid values for ACM_Classification where friability = "Friable"
     → API: GET /api/acm/field-schema/picklist-values?
             field=ACM_Classification__c&
             controller_value=Friable
  5. If current ACM_Classification value is NOT in valid set:
     → Clear ACM_Classification cell (set to null)
     → Clear ACM_Sub_Classification cell (cascade)
     → Show yellow warning: "Product Group cleared — please re-select"
  6. If current value IS valid:
     → Keep value, but re-validate Sub_Classification
```

### Custom Cell Editor: `DependentPicklistEditor`

```typescript
interface DependentPicklistEditorParams {
  dependsOn: string;          // field name of controller
  schemaField: string;        // SF API field name for lookup
  allowClear?: boolean;       // show "Clear" option
  searchable?: boolean;       // enable type-to-search (for large lists)
}

// Editor renders:
// 1. Reads controller cell value from same row
// 2. Queries field_schema for valid values given controller
// 3. Renders <Select> or <Combobox> with filtered values
// 4. On selection, updates cell and triggers cascade check
```

---

## 13. Accessibility & Responsive Design

### Accessibility Requirements (WCAG 2.1 AA)

| Component | ARIA | Keyboard |
|-----------|------|----------|
| **Wizard** | `role="progressbar"`, `aria-valuenow`, `aria-valuemax` | Enter = Next, Escape = Previous (existing) |
| **AG Grid** | Built-in AG Grid accessibility (WAI-ARIA grid role) | Tab/Shift+Tab between cells, Enter to edit, Escape to cancel |
| **Provenance Sheet** | `role="dialog"`, `aria-modal="true"`, `aria-label="Provenance viewer"` | Escape to close, Tab cycles within panel |
| **Record Wizard** | `role="dialog"`, `aria-label="Edit ACM Record"` | Standard dialog focus trap |
| **Validation badges** | `aria-label="Validation error: Condition is not a valid SF value"` | Focusable, screen reader announces issue |
| **Confidence badges** | `aria-label="Consensus confidence: HIGH"` | Color-independent (icon + text) |
| **Bulk toolbar** | `role="toolbar"`, `aria-label="Bulk actions for 12 selected records"` | Arrow keys between buttons |
| **PDF viewer** | `aria-label="PDF page 12 of 48"` | Page navigation via arrow keys |

### Color-Independent Design

All status indicators use **icon + text + color**, never color alone:

| Status | Icon | Text | Color |
|--------|------|------|-------|
| Valid | ✅ | "Valid" | Green |
| Warning | ⚠ | "Warning" | Orange |
| Error | 🔴 | "Error" | Red |
| Contested | ⚡ | "Contested" | Yellow |
| HIGH confidence | ● | "HIGH" | Green |
| MEDIUM confidence | ◐ | "MEDIUM" | Yellow |
| LOW confidence | ○ | "LOW" | Red |

### Responsive Breakpoints

| Breakpoint | Layout Changes |
|------------|----------------|
| **Desktop (≥1280px)** | Full two-column layout: grid + chat panel. Provenance Sheet 480px |
| **Laptop (1024-1279px)** | Grid takes full width. Chat collapsed to icon. Provenance Sheet 380px |
| **Tablet (768-1023px)** | Building detail form stacks vertically. Wizard steps show icons only (no labels). Provenance opens as full-width overlay |
| **Mobile (<768px)** | Not primary target. Grid shows 4-5 columns with horizontal scroll. Wizard is full-screen. Provenance is full-screen sheet |

---

## 14. Loading & Error States

### Loading States

| Component | Loading State |
|-----------|--------------|
| **Building Grid** | Skeleton rows (5 rows, all columns shimmer) |
| **Item Grid** | Skeleton rows (10 rows, all columns shimmer) |
| **Building Detail Form** | Skeleton fields (12 shimmer blocks in form layout) |
| **Provenance PDF** | "Loading PDF..." with spinner in PDF area, skeleton for lineage section |
| **Record Wizard** | Spinner on "Next" button during validation. Steps remain visible |
| **Upload** | File drop area shows upload progress bar. "Uploading..." text |
| **Extraction Progress** | Animated progress bar. Building cards appear incrementally |
| **Bulk Operations** | "Applying changes..." progress dialog with percentage |

### Error States

| Scenario | Error Display |
|----------|---------------|
| **Upload fails** | Toast: "Upload failed: [reason]". File drop area resets. Retry available |
| **Extraction fails** | Extraction Progress page shows red stage + error message. "Retry" button |
| **API timeout** | Toast: "Request timed out. Please try again." |
| **Validation error (inline)** | Red badge in grid cell. Hover tooltip shows specific error. Fix link available |
| **PDF load failure** | Provenance PDF area shows "Unable to load PDF. [Download link]" |
| **SSE connection lost** | Yellow banner: "Connection lost. Reconnecting..." Auto-retry with backoff |
| **Save fails** | Toast: "Failed to save record. [error details]". Form retains entered values |
| **Bulk operation partial failure** | Dialog: "8 of 12 records updated. 4 failed: [details]" |
| **Empty state (no records)** | Illustrated empty state: "No ACM records found. Upload a document to get started." with CTA |

### Toast Notification Patterns

```
Success: ✅ "12 records updated successfully"
Warning: ⚠ "Record saved with 2 validation warnings"
Error:   🔴 "Failed to save — Condition 'Good' is not valid"
Info:    ℹ "Building BLD#002 extraction complete — 8 records"
```

---

## Appendix A: New Component Inventory

| Component | Type | Priority | Story |
|-----------|------|----------|-------|
| `UploadWizardPage` | Page | P0 | E33-S1 |
| `DocumentTypeSelector` | Form | P0 | E33-S1 |
| `ExtractionModeSelector` | Form | P0 | E33-S1 |
| `ExtractionProgressPage` (enhanced) | Page | P0 | E33-S1 |
| `PipelineStageList` | Display | P0 | E33-S1 |
| `BuildingCardList` | Display | P0 | E33-S1 |
| `BuildingDetailView` | Page section | P0 | E33-S2 |
| `BuildingDetailForm` | Form | P0 | E33-S2 |
| `DependentPicklistEditor` | AG Grid editor | P0 | E33-S3 |
| `SearchableComboboxEditor` | AG Grid editor | P0 | E33-S3 |
| `DependentPicklistPair` | Form | P0 | E33-S3 |
| `ValidationBadgeRenderer` | AG Grid renderer | P0 | E33-S4 |
| `RecordWizardDialog` | Modal | P1 | E33-S4 |
| `ClassificationStep` | Wizard step | P1 | E33-S4 |
| `LocationStep` | Wizard step | P1 | E33-S4 |
| `AssessmentStep` | Wizard step | P1 | E33-S4 |
| `DetailsStep` | Wizard step | P1 | E33-S4 |
| `ReviewStep` | Wizard step | P1 | E33-S4 |
| `RawTableGrid` (enhanced) | AG Grid | P1 | E33-S5 |
| `RawTableToolbar` | Toolbar | P1 | E33-S5 |
| `ConfidenceBadgeRenderer` | AG Grid renderer | P1 | E33-S5 |
| `ProvenanceSheet` | Sheet/panel | P1 | E33-S6 |
| `PDFPageViewer` | Display | P1 | E33-S6 |
| `BboxOverlay` | Display | P1 | E33-S6 |
| `EditHistoryTimeline` | Display | P1 | E33-S6 |
| `BulkActionsToolbar` | Toolbar | P1 | E34-S3 |
| `BulkEditDialog` | Modal | P1 | E34-S3 |
| `BulkValidateDialog` | Modal | P1 | E34-S3 |

---

## Appendix B: Design Tokens Reference

Existing design tokens from the codebase (`globals.css` + Tailwind config):

| Token | Usage in V3 |
|-------|-------------|
| `--primary` | Wizard progress, active tab, primary buttons |
| `--destructive` | Delete buttons, error badges |
| `--muted` | Disabled steps, inactive tabs |
| `--card` | Grid containers, form containers |
| `--border` | Grid borders, form field borders |
| `--accent` | Hover states, selected rows |
| `bg-red-50 / dark:bg-red-950` | Error row highlight |
| `bg-yellow-50 / dark:bg-yellow-950` | Warning row highlight |
| `bg-green-50 / dark:bg-green-950` | Valid/HIGH confidence highlight |
| `bg-orange-50 / dark:bg-orange-950` | Contested value highlight |

---

*Generated 2026-03-03 by Sally (UX Designer) — BMAD Agent*
*6 flows · 26+ new components · Full state management plan · AG Grid specs for 2 grids*
*Next step: Architecture document (05-create-architecture) → Epic/Story creation → Sprint planning*
