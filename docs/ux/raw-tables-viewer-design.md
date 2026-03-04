# UX Design: Raw Tables Viewer — Job Detail Page

| Field            | Value                                                    |
|------------------|----------------------------------------------------------|
| **Epic**         | E24 — Activate Docling TableFormer                       |
| **Author**       | Sally (UX Designer)                                      |
| **Date**         | 2026-02-27                                               |
| **Status**       | Draft                                                    |
| **Stakeholder**  | Demi (Product Owner)                                     |

---

## Table of Contents

1. [User Story & Problem](#1-user-story--problem)
2. [Design Decisions Summary](#2-design-decisions-summary)
3. [Tab Placement & Labeling](#3-tab-placement--labeling)
4. [Table Viewer Component](#4-table-viewer-component)
5. [Confidence Indicators](#5-confidence-indicators)
6. [Role-Based Views](#6-role-based-views)
7. [Empty & Edge States](#7-empty--edge-states)
8. [Mobile & Responsive Design](#8-mobile--responsive-design)
9. [Wireframes](#9-wireframes)
10. [Component Specification](#10-component-specification)
11. [Interaction Patterns](#11-interaction-patterns)
12. [Accessibility](#12-accessibility)
13. [Implementation Notes](#13-implementation-notes)
14. [Pipeline Context: Where Source Tables Fits](#14-pipeline-context-where-source-tables-fits)

---

## 1. User Story & Problem

### The Persona: "Confidence Checkpoint Claire"

Claire is a compliance officer at a Victorian council. She's just uploaded a 47-page
Broadmeadows asbestos survey PDF. The system extracts 31 ACM records — but Claire
doesn't trust black boxes. She needs to *see* what the AI saw before it processed
the data. She needs a confidence checkpoint.

**Today's pain:** Claire sees final ACM records but has no way to verify what the AI
was working with. If a record looks wrong, she can't tell whether the error was in
the PDF extraction (bad table parsing) or the AI interpretation (misread values).

**Tomorrow's experience:** Claire clicks "Source Tables" and immediately sees the
7 structured tables the AI extracted from her PDF. She can visually verify: "Yes,
these tables look right — all the columns are there, no broken rows." She feels
confident approving the records, or she spots a mangled table and knows to
re-extract with different settings.

### Core Design Principle

> **Transparency builds trust.** The Raw Tables viewer exists to make the AI's
> input visible, not to replace the ACM Records grid. It's a diagnostic tool
> that answers one question: "Did the system read my PDF correctly?"

---

## 2. Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tab label | **"Source Tables"** | Clear, non-technical. Avoids "raw" (sounds unfinished) and "PDF Tables" (not all sources are PDFs). |
| Tab position | Between "Content" and "Extraction Log" | Groups source data tabs together; follows the data flow narrative. |
| Count badge | **Yes — "Source Tables (7)"** | Gives immediate signal of extraction yield without clicking. |
| Table rendering | **HTML iframe** (Phase 1), **AG Grid** (Phase 2) | Matches existing `RawTableViewer` pattern. AG Grid upgrade comes with Phase 2 structured JSON. |
| Collapsibility | **Collapsible cards**, first 3 expanded | Prevents scroll fatigue on multi-table documents. |
| Side-by-side view | **Phase 2 only** | Requires record-to-table lineage mapping not available in Phase 1. |
| Empty state | **Contextual message** with re-extract CTA | Never hide the tab — always show it with helpful guidance. |
| Mobile | **Horizontal scroll** inside cards | Tables are inherently wide; card-based stacking is unusable for tabular data. |

---

## 3. Tab Placement & Labeling

### Tab Order (Updated)

```
┌──────────┬────────────┬─────────────┬─────────┬──────────────────┬────────────────┐
│ Overview │ Buildings  │ ACM Records │ Content │ Source Tables (7) │ Extraction Log │
└──────────┴────────────┴─────────────┴─────────┴──────────────────┴────────────────┘
```

### Design Rationale

The tab order tells a **data flow story**:

1. **Overview** — "What is this job?"
2. **Buildings** — "What buildings were detected?"
3. **ACM Records** — "What did the AI produce?" (the main output)
4. **Content** — "What raw text did the system extract?"
5. **Source Tables** — "What structured tables did the system find?" *(NEW)*
6. **Extraction Log** — "What happened during processing?"

Source Tables sits after Content because it's a *refined view* of the same source
data — Content shows the full markdown, Source Tables shows just the structured
tables extracted from it. This creates a natural "zoom in" progression.

### Tab Label: "Source Tables"

**Rejected alternatives:**

| Label | Why Rejected |
|-------|-------------|
| "Raw Tables" | "Raw" sounds unfinished/broken to compliance officers. |
| "PDF Tables" | Not all sources are PDFs (future: XLSX, HTML). |
| "Extracted Tables" | Confusion with "Extraction" (the AI step). |
| "Table Preview" | Implies temporary/draft status. |

**"Source Tables"** communicates: "These are the tables from your source document."
Non-technical users understand this immediately.

### Count Badge

The tab shows a count badge when tables are available:

```
Source Tables (7)      ← tables found
Source Tables          ← loading or no tables yet
Source Tables (0)      ← processing complete, no tables found
```

**Implementation:** The badge count comes from the `useQuery` result for
`/api/acm/jobs/{source_id}/raw-tables`. Show the count only after the query
resolves (not during loading).

---

## 4. Table Viewer Component

### 4A. Overall Layout

Each extracted table is rendered as a **collapsible card** containing:

```
┌─────────────────────────────────────────────────────────────────────┐
│ ▼ Table 1 — Page 3                   [Register Table] [No merges]  │
│   Building: B009 - Main Building                                   │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Building │ Room        │ Product              │ Result          │ │
│ ├──────────┼─────────────┼──────────────────────┼─────────────────┤ │
│ │ B009     │ R0001 Store │ Vinyl floor tiles    │ Positive        │ │
│ │ B009     │ R0001 Switch│ Auto Battery Charger │ Not Sampled     │ │
│ │ B009     │ R0002       │ Ceiling tiles        │ Positive        │ │
│ │ ...      │             │                      │                 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ 12 rows × 4 columns                                 [Expand ↕]    │
└─────────────────────────────────────────────────────────────────────┘
```

### 4B. Card Header

Each table card header displays:

| Element | Description | Position |
|---------|-------------|----------|
| **Collapse toggle** | Chevron icon (▼/▶) | Left |
| **Table number + page** | "Table 1 — Page 3" or "Table 2 — Pages 5-7" | Left, after toggle |
| **Table type badge** | Color-coded: Register (green), Metadata (blue), Lab Report (amber), Docling Markdown (slate) | Right |
| **Merged cell indicator** | "Merged cells detected" (orange) or "No merged cells" (slate) | Right |
| **Building name** | Subtitle: "Building: B009 - Main Building" | Below title, muted |

**Badge color scheme** (matches existing `RawTableViewer.tsx`):

| Type | Border | Background | Text |
|------|--------|------------|------|
| Register Table | `emerald-200` | `emerald-50` | `emerald-700` |
| Metadata Table | `blue-200` | `blue-50` | `blue-700` |
| Lab Report | `amber-200` | `amber-50` | `amber-700` |
| Docling Markdown | `slate-200` | `slate-50` | `slate-700` |
| TableFormer *(Phase 2)* | `violet-200` | `violet-50` | `violet-700` |

### 4C. Table Rendering Strategy

**Phase 1 (current sprint):** Continue using the existing `iframe + srcDoc` pattern
from `RawTableViewer.tsx` for HTML tables, and `<pre>` blocks for markdown tables.
This is battle-tested and works with the current API response shape.

**Phase 2 (future — Story S6):** When `structured_json` data is available from
TableFormer DataFrames, render in AG Grid for sorting, filtering, and column
resizing. The structured JSON maps directly to AG Grid `rowData` and `columnDefs`.

| Phase | Data Source | Rendering | Interaction |
|-------|-------------|-----------|-------------|
| Phase 1 | `raw_html` or `raw_text` | iframe / `<pre>` | View-only, scroll |
| Phase 2 | `structured_json` | AG Grid | Sort, filter, resize, search |

### 4D. Collapsible Behavior

- **First 3 tables:** Expanded by default on page load.
- **Tables 4+:** Collapsed by default.
- **"Expand All" / "Collapse All"** toggle in the summary bar.
- Collapse state is **per-session only** (not persisted).

**Rationale:** Most SAMP PDFs have 3-7 tables per building. Showing the first 3
gives immediate value without overwhelming. The compliance officer can expand more
if needed.

### 4E. Table Size Handling

| Table Size | Behavior |
|------------|----------|
| **< 20 rows** | Full table visible, no internal scroll |
| **20-100 rows** | `max-height: 400px` with internal scroll, "Expand" button |
| **> 100 rows** | `max-height: 400px` with internal scroll, row count shown prominently |

The "Expand ↕" button in the footer toggles the card between constrained
(`max-height: 400px`) and full height, allowing deep inspection of large tables.

---

## 5. Confidence Indicators

### 5A. Summary Bar

At the top of the Source Tables tab content, above the table cards:

```
┌─────────────────────────────────────────────────────────────────────┐
│ 7 tables found across 12 pages                                     │
│                                                                     │
│ [Register: 5] [Metadata: 1] [Lab: 1]  [Merged cells: 2]          │
│                                                                     │
│ Extraction method: Docling + TableFormer (accurate)                │
│                                            [Expand All] [Collapse] │
└─────────────────────────────────────────────────────────────────────┘
```

### 5B. Summary Badge Set

| Badge | Value | Color | Purpose |
|-------|-------|-------|---------|
| **Total tables** | "7 tables found across 12 pages" | — (text) | Overview of extraction yield |
| **Register count** | "Register: 5" | `emerald` | How many data tables vs metadata |
| **Metadata count** | "Metadata: 1" | `blue` | Non-ACM tables (cover pages, legends) |
| **Lab count** | "Lab: 1" | `amber` | Lab result tables |
| **Merged cells** | "Merged cells: 2" | `orange` | Tables with complex structure (risk indicator) |
| **Extraction method** | "Docling + TableFormer (accurate)" | `violet` | What engine produced these tables |

### 5C. Extraction Method Badge

Displayed in the summary bar and optionally on each table card (for admin users):

| Method | Display | Badge Color |
|--------|---------|-------------|
| TableFormer accurate | "Docling + TableFormer (accurate)" | `violet` |
| TableFormer fast | "Docling + TableFormer (fast)" | `violet` (lighter) |
| Docling basic | "Docling (basic)" | `slate` |
| MinerU *(legacy)* | "MinerU" | `cyan` |

**Phase 1 note:** The extraction method is not yet stored per-table in the API
response. For Phase 1, determine the method from the `table_type` field:
- `table_type` contains "mineru" → MinerU
- `table_type` contains "docling" → Docling
- Otherwise → infer from environment variable `DOCLING_TABLE_STRUCTURE`

**Phase 2:** Add `extraction_method` field to `RawTableResponse` for precise
per-table attribution.

### 5D. Per-Table Confidence Indicators

Each table card footer shows structural metadata:

```
12 rows × 4 columns  ·  No merged cells  ·  Page 3          [Expand ↕]
```

For admin users, additional metrics are shown (see Section 6).

---

## 6. Role-Based Views

### 6A. Standard User (Compliance Officer)

The default view — clean, focused, non-technical:

**Sees:**
- Summary bar with table counts and type badges
- Collapsible table cards with type badges and page numbers
- Table content (HTML or markdown)
- Row × column counts in footer
- Building name labels

**Does NOT see:**
- Extraction method badge (irrelevant to their workflow)
- Processing time metrics
- Bounding box coordinates
- Table structure JSON

### 6B. Admin User (Developer / Data Engineer)

Toggle via a **"Show Details"** switch in the summary bar:

```
┌─────────────────────────────────────────────────────────────────────┐
│ 7 tables found across 12 pages              [Show Details ◉]      │
│                                                                     │
│ [Register: 5] [Metadata: 1] [Lab: 1] [Merged: 2]                 │
│                                                                     │
│ Method: Docling + TableFormer (accurate) · Processed in 23.4s     │
│ Source: Broadmeadows-Survey-2024.pdf · 31 pages                    │
│                                            [Expand All] [Collapse] │
└─────────────────────────────────────────────────────────────────────┘
```

**Additional per-table details** (when "Show Details" is on):

```
┌─────────────────────────────────────────────────────────────────────┐
│ ▼ Table 1 — Page 3      [Register Table] [Merged cells] [TF/acc]  │
│   Building: B009 · Bbox: (72, 144, 540, 720) · Confidence: 0.94   │
├─────────────────────────────────────────────────────────────────────┤
│  ... table content ...                                              │
├─────────────────────────────────────────────────────────────────────┤
│ 12×4 · Merged: 0 · Method: tableformer_accurate · 1.2s   [Expand] │
└─────────────────────────────────────────────────────────────────────┘
```

**Admin-only fields:**

| Field | Source | Display |
|-------|--------|---------|
| Extraction method per table | `table_type` / `extraction_method` (Phase 2) | Badge: "TF/acc" |
| Bounding box | Phase 2: `structured_json` metadata | "Bbox: (72, 144, 540, 720)" |
| Confidence score | Phase 2: TableFormer model output | "Confidence: 0.94" |
| Processing time | Phase 2: timing metadata | "1.2s" |

### 6C. Implementation Approach

**Phase 1:** No role check needed. The "Show Details" toggle is available to all
users but only reveals `table_type` information (already in the API response).
True admin-only fields (bbox, confidence, processing time) are Phase 2 features
that require API changes.

**Phase 2:** Use a `useUserRole()` hook or feature flag to control whether the
"Show Details" toggle is visible at all.

---

## 7. Empty & Edge States

### 7A. No Tables Available (Processing Not Complete)

When `source.full_text` is not yet populated (extraction still running):

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│              ┌────────────────────────┐                             │
│              │   ⏳ (hourglass icon)  │                             │
│              └────────────────────────┘                             │
│                                                                     │
│           Tables are being extracted from your document...          │
│           This usually takes 20-35 seconds.                        │
│                                                                     │
│                  [View Extraction Log →]                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7B. No Structured Tables Found

When extraction completed but no pipe-delimited tables were found:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│              ┌────────────────────────┐                             │
│              │   📄 (document icon)   │                             │
│              └────────────────────────┘                             │
│                                                                     │
│           No structured tables were found in this document.         │
│                                                                     │
│           This PDF may not contain tabular data, or the tables      │
│           may be image-based and couldn't be parsed.                │
│                                                                     │
│           You can check the Content tab to see the full             │
│           extracted text, or re-extract with different settings.    │
│                                                                     │
│                [View Content →]  [Re-Extract]                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7C. Extraction Error

When the raw-tables API returns an error:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   ⚠️  Failed to load source tables                                 │
│                                                                     │
│   There was an error retrieving the table data.                    │
│   Error: [error message]                                            │
│                                                                     │
│                      [Retry]                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7D. Single Table

When only one table is found, skip the collapsible pattern — show it expanded
with no collapse toggle. The summary bar simplifies to:

```
1 table found on page 3  ·  [Register Table]
```

### 7E. Many Tables (>10)

When more than 10 tables are found:

- Show a **building filter** dropdown (reuse `BuildingTabFilter` component)
  to filter tables by building name
- Paginate tables: show 10 per page with "Show More" button
- Summary bar shows: "23 tables found across 47 pages (showing 1-10)"

---

## 8. Mobile & Responsive Design

### 8A. Breakpoint Strategy

| Breakpoint | Layout Change |
|------------|---------------|
| **Desktop (≥1024px)** | Full layout as designed; summary bar horizontal |
| **Tablet (768-1023px)** | Summary badges wrap to 2 rows; table cards full-width |
| **Mobile (<768px)** | Tab bar scrolls horizontally; cards stack; tables scroll horizontally inside cards |

### 8B. Tab Navigation on Small Screens

The existing `TabsList` already has `overflow-x-auto` (line 174 of `page.tsx`).
With 6 tabs, the horizontal scroll activates on screens < ~640px.

**Enhancement:** Add a subtle scroll indicator (gradient fade) on the right edge
when tabs overflow:

```
┌─────────────────────────────────────────────┐
│ Overview │ Buildings │ ACM Records │ Cont...▸│
└─────────────────────────────────────────────┘
```

### 8C. Tables on Mobile

Tables are inherently wide — **horizontal scroll is the correct pattern** for
mobile. Never try to reformat tabular data into cards; it destroys the
row/column relationships that compliance officers need to verify.

```
Mobile (375px width):
┌─────────────────────────────────────────┐
│ Table 1 — Page 3        [Register] [▾] │
│ Building: B009                          │
├─────────────────────────────────────────┤
│ ◀──────── scroll ────────────────────▶ │
│ ┌──────┬──────┬──────────┬──────────┐  │
│ │Build │Room  │Product   │Result    │  │
│ ├──────┼──────┼──────────┼──────────┤  │
│ │B009  │R0001 │Vinyl     │Positive  │  │
│ │B009  │R0001 │Charger   │Not Samp  │  │
│ └──────┴──────┴──────────┴──────────┘  │
│                                         │
│ 12 rows × 4 cols            [Expand ↕] │
└─────────────────────────────────────────┘
```

### 8D. Summary Bar on Mobile

Badges wrap naturally using `flex-wrap`. On very small screens, the badges stack
into 2-3 rows:

```
Mobile summary:
┌─────────────────────────────────────────┐
│ 7 tables · 12 pages                    │
│ [Register: 5] [Metadata: 1] [Lab: 1]  │
│ [Merged: 2]                            │
│                 [Expand All] [Collapse] │
└─────────────────────────────────────────┘
```

---

## 9. Wireframes

### 9A. Full Desktop View — Source Tables Tab

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  ← Jobs    Broadmeadows Survey 2024.pdf          [Re-Extract] [Export CSV] [Export XLSX] │
│  ● Reviewed · 31 records · 3 buildings · Uploaded Feb 24, 2026                           │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐    │
│  │ Overview │ Buildings │ ACM Records │ Content │ Source Tables (7) │ Extraction Log│    │
│  ├──────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │  7 tables found across 12 pages                                         │    │    │
│  │  │                                                                         │    │    │
│  │  │  [Register: 5]  [Metadata: 1]  [Lab: 1]  [Merged cells: 2]            │    │    │
│  │  │                                                                         │    │    │
│  │  │  Extraction: Docling + TableFormer (accurate)                          │    │    │
│  │  │                                       [Expand All]  [Collapse All]     │    │    │
│  │  └──────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │ ▼ Table 1 — Page 3                   [Register Table] [No merged cells] │    │    │
│  │  │   Building: B009 - Main Building                                        │    │    │
│  │  ├──────────────────────────────────────────────────────────────────────────┤    │    │
│  │  │ ┌─────────┬───────────────────────┬─────────────────────┬─────────────┐ │    │    │
│  │  │ │Building │ Room / Area           │ ACM Product         │ Result      │ │    │    │
│  │  │ ├─────────┼───────────────────────┼─────────────────────┼─────────────┤ │    │    │
│  │  │ │ B009    │ R0001 General Store   │ Vinyl floor tiles   │ Positive    │ │    │    │
│  │  │ │ B009    │ R0001 Switch Room     │ Battery Charger     │ Not Sampled │ │    │    │
│  │  │ │ B009    │ R0002 Office          │ Ceiling tiles       │ Positive    │ │    │    │
│  │  │ │ B009    │ R0003 Kitchen         │ Pipe insulation     │ Positive    │ │    │    │
│  │  │ │ B009    │ R0004 Bathroom        │ Wall sheeting       │ Not Sampled │ │    │    │
│  │  │ └─────────┴───────────────────────┴─────────────────────┴─────────────┘ │    │    │
│  │  │                                                                         │    │    │
│  │  │ 12 rows × 4 columns                                       [Expand ↕]  │    │    │
│  │  └──────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │ ▼ Table 2 — Pages 5-7               [Register Table] [Merged cells ⚠]  │    │    │
│  │  │   Building: B010 - Annex                                                │    │    │
│  │  ├──────────────────────────────────────────────────────────────────────────┤    │    │
│  │  │  ... table content (iframe or pre block) ...                            │    │    │
│  │  │                                                                         │    │    │
│  │  │ 24 rows × 6 columns · Merged cells detected                [Expand ↕] │    │    │
│  │  └──────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │ ▶ Table 3 — Page 8                 [Metadata Table] [No merged cells]   │    │    │
│  │  │   Building: B009 - Main Building                                        │    │    │
│  │  └──────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │ ▶ Table 4 — Page 9                 [Register Table] [No merged cells]   │    │    │
│  │  └──────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                                  │    │
│  │              ... (Tables 5-7 collapsed) ...                                 │    │    │
│  │                                                                                  │    │
│  └──────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
├───────────────────────────────────────────┬──────────────────────────────────────────────┤
│          (main content area)              │  CRUD Chat                            [▶]   │
│                                           │  (collapsible right panel)                   │
└───────────────────────────────────────────┴──────────────────────────────────────────────┘
```

### 9B. Empty State — No Tables Found

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Overview │ Buildings │ ACM Records │ Content │ Source Tables │ Extraction Log│
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                                                                              │
│                          ┌──────────────┐                                   │
│                          │              │                                   │
│                          │   📄         │                                   │
│                          │              │                                   │
│                          └──────────────┘                                   │
│                                                                              │
│             No structured tables were found in this document.                │
│                                                                              │
│             This PDF may not contain tabular data, or the tables             │
│             may be image-based and couldn't be parsed.                       │
│                                                                              │
│             You can check the Content tab to see the full                    │
│             extracted text, or re-extract with different settings.           │
│                                                                              │
│                   [View Content →]    [Re-Extract]                           │
│                                                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 9C. Admin "Show Details" View

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  7 tables found across 12 pages                        [Show Details ◉]    │
│                                                                              │
│  [Register: 5]  [Metadata: 1]  [Lab: 1]  [Merged: 2]                      │
│                                                                              │
│  Method: Docling + TableFormer (accurate) · 23.4s total · Source: 31 pages │
│                                             [Expand All] [Collapse All]     │
├──────────────────────────────────────────────────────────────────────────────┤
│ ▼ Table 1 — Page 3   [Register] [No merges] [TF/accurate] [Conf: 0.94]    │
│   Building: B009 · Bbox: (72, 144, 540, 720) · Processed: 1.2s            │
├──────────────────────────────────────────────────────────────────────────────┤
│  ... table content ...                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│ 12×4 · Merged: 0 · Method: tableformer_accurate · 1.2s          [Expand]  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Component Specification

### 10A. Component Tree

```
SourceTablesTab (new wrapper)
├── SourceTablesSummaryBar
│   ├── Table count text
│   ├── Type count badges (Register, Metadata, Lab)
│   ├── Merged cells badge
│   ├── Extraction method badge
│   ├── Show Details toggle (admin)
│   └── Expand All / Collapse All buttons
├── BuildingTabFilter (reused, for >10 tables)
└── SourceTableCard[] (one per table)
    ├── CollapsibleCardHeader
    │   ├── Chevron toggle
    │   ├── Table title (number + page range)
    │   ├── Type badge
    │   ├── Merged cell badge
    │   └── Building name subtitle
    ├── CollapsibleCardContent
    │   ├── iframe (for raw_html)
    │   └── pre (for raw_text / markdown)
    └── CardFooter
        ├── Row × column count
        ├── Admin details (conditional)
        └── Expand height toggle
```

### 10B. New Components

| Component | File | Purpose |
|-----------|------|---------|
| `SourceTablesSummaryBar` | `components/acm/SourceTablesSummaryBar.tsx` | Summary statistics and controls |
| `SourceTableCard` | `components/acm/SourceTableCard.tsx` | Individual collapsible table card |

### 10C. Reused Components

| Component | Source | Usage |
|-----------|--------|-------|
| `RawTableViewer` | `components/acm/RawTableViewer.tsx` | **Enhance** — add collapsible cards, summary bar. The current component becomes the inner rendering logic. |
| `BuildingTabFilter` | `components/acm/BuildingTabFilter.tsx` | Reuse for filtering tables by building (>10 tables) |
| `Badge` | `components/ui/badge` | All status/type badges |
| `Card`, `CardContent`, `CardHeader` | `components/ui/card` | Table card wrappers |
| `Collapsible` | `components/ui/collapsible` | Card expand/collapse (use Radix Collapsible) |

### 10D. Props Interface

```typescript
// SourceTablesSummaryBar
interface SourceTablesSummaryBarProps {
  tables: ACMRawTable[]
  showDetails: boolean
  onToggleDetails: () => void
  allExpanded: boolean
  onExpandAll: () => void
  onCollapseAll: () => void
}

// SourceTableCard
interface SourceTableCardProps {
  table: ACMRawTable
  index: number
  isExpanded: boolean
  onToggleExpand: () => void
  showDetails: boolean  // admin detail view
}
```

---

## 11. Interaction Patterns

### 11A. Collapse/Expand

| Action | Result |
|--------|--------|
| Click card header | Toggle that card's collapsed state |
| Click "Expand All" | Expand all cards |
| Click "Collapse All" | Collapse all cards |
| Keyboard: Enter/Space on header | Toggle collapse (a11y) |

### 11B. Height Toggle ("Expand ↕")

| Action | Result |
|--------|--------|
| Click "Expand ↕" | Toggle between `max-height: 400px` and full height |
| Only shown when | Table content exceeds 400px |

### 11C. Empty State Actions

| Action | Result |
|--------|--------|
| Click "View Content →" | Switch to Content tab (`setActiveTab('content')`) |
| Click "Re-Extract" | Trigger `handleReExtract()` |
| Click "Retry" (error state) | Re-fetch raw tables query |
| Click "View Extraction Log →" | Switch to log tab (`setActiveTab('log')`) |

### 11D. Navigation from Tab Badge

Clicking the "Source Tables (7)" tab scrolls to the top of the tab content
(standard Radix Tabs behavior — no custom scroll logic needed).

---

## 12. Accessibility

| Requirement | Implementation |
|-------------|----------------|
| **Tab navigation** | Radix Tabs handles arrow key navigation between tabs |
| **Collapsible cards** | Use `role="button"`, `aria-expanded`, `aria-controls` |
| **Table content** | iframe has `title` attribute; `<pre>` blocks have `aria-label` |
| **Screen readers** | Summary bar has `aria-live="polite"` for count updates |
| **Color contrast** | All badge colors meet WCAG AA contrast ratios (inherited from existing badge system) |
| **Focus management** | Expand/Collapse All buttons receive focus ring |
| **Keyboard** | All interactive elements reachable via Tab; toggles via Enter/Space |

---

## 13. Implementation Notes

### 13A. Phase 1 Changes (This Sprint — E24)

**Minimal changes to existing components. The current `RawTableViewer.tsx` already
does 80% of what we need.** Phase 1 enhancements:

1. **Tab label change:** Rename "Raw Tables" → "Source Tables" and add count badge
   in `jobs/[id]/page.tsx` (line 179)

2. **Add summary bar:** New `SourceTablesSummaryBar` component above the table list

3. **Add collapsibility:** Wrap each table `Card` in a Radix `Collapsible`, with
   first 3 expanded by default

4. **Improve empty states:** Replace the single-line empty message with the
   contextual empty state designs from Section 7

5. **Add height toggle:** For tables with content > 400px, add "Expand ↕" button

### 13B. Phase 2 Changes (Future — Story S6)

1. **AG Grid rendering** for `structured_json` data
2. **Side-by-side view:** Raw table left, matched ACM records right
3. **Row highlighting:** Click a raw table row to highlight the corresponding
   ACM record in the Records tab
4. **Extraction method per-table** from API response
5. **Admin toggle** with bbox, confidence, processing time

### 13C. API Dependencies

| Feature | API Field | Available |
|---------|-----------|-----------|
| Table count badge | `raw-tables` endpoint length | **Now** |
| Table type badges | `table_type` field | **Now** |
| Building name | `building_name` field | **Now** |
| Merged cell detection | Parse `raw_html` for colspan/rowspan | **Now** |
| Extraction method | *Not in response* | **Phase 2** — add `extraction_method` field |
| Confidence score | *Not in response* | **Phase 2** — add from TableFormer output |
| Bounding box | *Not in response* | **Phase 2** — add from Docling metadata |
| Processing time | *Not in response* | **Phase 2** — add timing metadata |

### 13D. File Changes for Phase 1

| File | Change | Lines |
|------|--------|-------|
| `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` | Rename tab label, add count badge | ~5 |
| `frontend/src/components/acm/RawTableViewer.tsx` | Add collapsibility, summary bar, empty states, height toggle | ~80-120 |
| `frontend/src/components/acm/SourceTablesSummaryBar.tsx` | **New** — summary statistics component | ~60 |
| `frontend/src/components/acm/SourceTableCard.tsx` | **New** — collapsible table card | ~80 |

**Total estimated effort: ~2-3 hours frontend work.**

---

## 14. Pipeline Context: Where Source Tables Fits

> **Added after review of `docs/architecture/pipeline-structured-output-assessment.md`**

### 14A. Two Different Extraction Stages

The Source Tables viewer shows data from **Stage A** of the pipeline. Users must
not confuse this with **Stage B** (the AI interpretation step). The UX must make
this boundary clear without being technical.

```
Stage A: PDF → Structured Tables        ← SOURCE TABLES TAB SHOWS THIS
         (Docling + TableFormer)
              │
              ▼
Stage B: Structured Tables → ACM Records ← ACM RECORDS TAB SHOWS THIS
         (LLM extraction with JSON parsing)
```

The pipeline assessment confirms that Stage B currently has systemic structured
output failures (all 4 LLM stages fall back to heuristic or JSON parsing). This
does NOT affect Stage A or the Source Tables viewer — but it has a critical UX
implication for the relationship BETWEEN tabs.

### 14B. The "Missing Records" Gap — Why This Viewer Matters Even More

The pipeline assessment documents that 3 of 31 Broadmeadows records are
**present in the source tables** but **missing from ACM Records**. These are
"Not Sampled" brief inline entries that the LLM does not extract.

This is precisely the scenario that makes the Source Tables viewer a vital
confidence checkpoint. Claire's workflow becomes:

1. Check **Source Tables**: "I see 12 rows in Table 1, all columns look correct"
2. Check **ACM Records**: "Only 10 records from this table? Where did 2 go?"
3. Insight: "The table data is correct — the AI missed 2 entries"

Without the Source Tables viewer, Claire would have no way to distinguish between:
- **Bad table parsing** (the system misread the PDF) → re-extract with TableFormer
- **AI interpretation gap** (the LLM missed records) → manually add missing records

This reinforces two design decisions:

| Decision | Impact |
|----------|--------|
| **Phase 2 side-by-side view** | Even more valuable. The row-to-record mapping would let Claire instantly see which source rows have no matching ACM record. |
| **Row count in card footer** | Critical. "12 rows" in Source Tables vs "10 records" in ACM Records immediately signals a gap. |

### 14C. What NOT to Show in Source Tables

The pipeline assessment documents ~43s wasted latency from dead
`with_structured_output()` calls. This is an Extraction Log concern, not a
Source Tables concern. The Source Tables viewer must NOT surface:

- LLM extraction method (structured output vs. JSON fallback)
- LLM retry/fallback status
- Provider routing information (OpenRouter, Anthropic)

These belong exclusively in the **Extraction Log** tab. The Source Tables tab
is about PDF parsing quality, not LLM performance.

### 14D. No Design Changes Required

The pipeline structured output assessment does not require changes to:

- Visual design, wireframes, or component specs
- Tab placement, labeling, or count badge logic
- Confidence indicators (which track PDF extraction quality, not LLM quality)
- Empty states, mobile layout, or accessibility requirements

It **reinforces** the value of:

- The Phase 2 side-by-side comparison feature (Section 13B, item 2)
- The row count display in card footers (Section 5D)
- The clear separation between "Source Tables" and "ACM Records" tabs

---

## References

- Technical Design: `docs/architecture/tableformer-technical-design.md` (Section 5)
- Pipeline Assessment: `docs/architecture/pipeline-structured-output-assessment.md`
- Sprint Stories: `docs/sprint-artifacts/e24-s1-activate-tableformer.md`
- Existing Component: `frontend/src/components/acm/RawTableViewer.tsx`
- Job Detail Page: `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`
- API Endpoint: `api/routers/acm.py` (line 1401, `list_raw_tables_for_job`)
