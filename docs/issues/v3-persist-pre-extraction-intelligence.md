# V3: Persist Pre-Extraction Intelligence Models

> **Created:** 2026-03-04
> **Status:** IMPLEMENTED (E30-S9, 3 SP, V3-3)
> **Priority:** P1 (enhancement, not blocking current sprint)
> **Branch:** ACMV3
> **GitHub Issue:** https://github.com/CoralShades/acm-ai/issues/85
> **Implemented:** 2026-03-04 — Story E30-S9 in prd.json. All backend + frontend changes complete.

---

## Problem Statement

The 4 pre-extraction analysis models are **transient** — they exist only in the LangGraph state during pipeline execution and are discarded after the pipeline completes:

| Model | What It Contains | Currently Persisted? |
|-------|-----------------|:-------------------:|
| `DocumentMeta` | Consultant, site name, address, date, inspector, methodology | **Partial** — some fields copied to `site_config` via `auto_populate_site_config()` |
| `DocumentStructure` | Document type, TOC sections, total pages, register start page, building IDs | **No** |
| `BuildingInventory` | Per-building: name, year, construction, page ranges, room list, complexity, item estimate | **No** |
| `PageTaggingResult` | Per-page: section label, page type, confidence, content summary | **No** |

### Why This Matters

1. **No pre-AI vs post-AI comparison** — The regex/heuristic-extracted building metadata (year, construction, rooms) feeds the LLM prompt, but the original structural analysis is gone. You can't compare "what the structure analysis found" vs "what the AI extracted" for accuracy auditing.

2. **No frontend access to document intelligence** — The frontend has no way to show the user: "This PDF has 48 pages, 6 buildings, register starts on page 12, TOC found." This data exists during extraction but is thrown away.

3. **No re-extraction context** — If re-running extraction on a source, the pipeline must redo all 4 analysis nodes from scratch. Persisting these would allow skipping Phase 2 on re-runs.

4. **No provenance for building page ranges** — When the user asks "which pages belong to Building B00A?", there's no stored answer. The `building_record` has `page_number` (single int) but not the full `page_start..page_end` range from `BuildingMeta`.

---

## Proposed Solution

### New SurrealDB Table: `source_intelligence`

One record per source, created after Phase 2 completes:

```sql
-- Migration: 41.surrealql
DEFINE TABLE source_intelligence SCHEMAFULL;
DEFINE FIELD source_id ON source_intelligence TYPE record<source>;
DEFINE FIELD document_meta ON source_intelligence TYPE object;        -- Full DocumentMeta JSON
DEFINE FIELD document_structure ON source_intelligence TYPE object;   -- Full DocumentStructure JSON
DEFINE FIELD building_inventory ON source_intelligence TYPE object;   -- Full BuildingInventory JSON
DEFINE FIELD page_tags ON source_intelligence TYPE object;            -- Full PageTaggingResult JSON
DEFINE FIELD total_pages ON source_intelligence TYPE int;             -- Denormalized for quick access
DEFINE FIELD total_buildings ON source_intelligence TYPE int;         -- Denormalized for quick access
DEFINE FIELD document_type ON source_intelligence TYPE string;        -- SAMP, ARA, Division_5
DEFINE FIELD register_page_range ON source_intelligence TYPE object;  -- {start: int, end: int}
DEFINE FIELD created_at ON source_intelligence TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON source_intelligence TYPE datetime DEFAULT time::now();
DEFINE INDEX idx_source_intelligence_source ON source_intelligence FIELDS source_id UNIQUE;
```

### Backend Changes

1. **New save step** in `acm_extraction.py` after `tag_pages` node completes:
   - Serialize all 4 models to JSON and upsert into `source_intelligence`
   - Runs once per extraction, <1ms overhead

2. **New API endpoint**: `GET /api/acm/source-intelligence/{source_id}`
   - Returns the persisted pre-extraction data
   - Used by frontend to show document overview

3. **Skip-on-re-run optimization** (optional, lower priority):
   - If `source_intelligence` exists for this source, load it into graph state instead of re-running Phase 2
   - Add a `force_reanalyze` flag to override

### Frontend Changes

1. **Source overview panel** — After extraction, show:
   - Document type (SAMP/ARA)
   - Total pages, register page range
   - Building count with expandable list (name, year, construction, page range, rooms)
   - TOC sections with page numbers

2. **Pre-AI vs Post-AI comparison** (stretch):
   - Show `BuildingMeta.year` (structural) vs `building_record.Estimated_Year_Build_New__c` (AI) side by side

### Files Changed

| File | Change |
|------|--------|
| `migrations/41.surrealql` | New `source_intelligence` table |
| `open_notebook/database/repository.py` | CRUD for `source_intelligence` |
| `open_notebook/graphs/acm_extraction.py` | Save step after `tag_pages` node |
| `api/routers/acm.py` | New GET endpoint |
| `frontend/src/hooks/useSourceIntelligence.ts` | React Query hook |
| `frontend/src/components/acm/SourceOverview.tsx` | UI component |

---

## Impact on Current Sprint/Epics

### Does NOT disrupt current flow

- **No dependency changes** — This is additive. No existing story depends on this data being persisted.
- **No schema conflicts** — New table, no changes to existing tables.
- **Migration 41** is the next available slot (40 is the latest).
- **No blocking** — Can be implemented at any point without affecting E30-S5 (in progress), E31, E32, or E33.

### Recommended Approach

| Option | Pros | Cons |
|--------|------|------|
| **A: New story in V3-3 or V3-4** | Fits naturally before E31-S1 (MinerU). Having this data persisted makes Docling-vs-MinerU comparison easier. | Adds 2-3 SP to sprint. |
| **B: Fold into E31-S1 (MinerU Integration)** | MinerU story already touches the extraction pipeline. Natural place to add the save step. | Makes E31-S1 slightly larger than its 2 SP estimate. |
| **C: Standalone story after V3-2 completes** | Clean separation. No risk to current sprint. | Delays availability for comparison work. |

**Recommendation: Option A** — Create a new 2 SP story (e.g., `E30-S9` or `E35-S1`) targeting V3-3, unblocked (only needs SCHEMA_FREEZE which is already unlocked). This gives the data to both the MinerU comparison work and the frontend.

---

## Pydantic Model Sizes (for JSON storage estimation)

| Model | Typical JSON size | Fields |
|-------|------------------|--------|
| `DocumentMeta` | ~500 bytes | 15 fields |
| `DocumentStructure` | ~2 KB | sections[], building_ids[], metadata |
| `BuildingInventory` | ~5-20 KB | buildings[] with rooms[], processing_groups[] |
| `PageTaggingResult` | ~5-50 KB | One PageTag per page (48 pages = 48 objects) |
| **Total per source** | **~10-75 KB** | Negligible storage cost |

---

*Issue created 2026-03-04. References: V3/output/architecture-explainer.md §10, 04-architecture.md §14.2.*
