# E30-S9 Tech Spec: Persist Pre-Extraction Intelligence

**Story ID:** E30-S9
**Sprint:** V3-3
**Story Points:** 3
**Risk Level:** MEDIUM
**Type:** both (backend + frontend)
**Status:** Implemented (2026-03-04)

---

## Problem Statement

The 4 pre-extraction analysis models (`DocumentMeta`, `DocumentStructure`, `BuildingInventory`, `PageTaggingResult`) are transient — they exist only in LangGraph pipeline state and are discarded when the pipeline ends. This makes them inaccessible to the frontend and prevents comparison, auditing, or re-use.

---

## Acceptance Criteria

- **AC1:** Migration 41 creates `source_intelligence` table (SCHEMAFULL) with unique index on `source_id`
- **AC2:** `save_source_intelligence()` upserts all 4 pre-extraction models into the table
- **AC3:** `get_source_intelligence()` returns persisted data for a `source_id` or `None`
- **AC4:** `save_intelligence` graph node runs between `tag_pages` and `orchestrate` — non-blocking (catches all exceptions)
- **AC5:** `GET /api/acm/source-intelligence/{source_id}` returns 200 with data or 404
- **AC6:** Intelligence tab visible in source detail page with Brain icon
- **AC7:** Document Overview section shows type badge, total pages, buildings count, register page range
- **AC8:** Building Inventory section uses Radix Accordion with per-building details (rooms table)
- **AC9:** Page Analysis section shows scrollable table with confidence badges
- **AC10:** Hook polls every 5s during extraction, stops when done; skeleton + empty states

---

## File Changes

| File | Change |
|------|--------|
| `migrations/41.surrealql` | NEW — source_intelligence table definition |
| `migrations/41_down.surrealql` | NEW — down migration |
| `open_notebook/database/repository.py` | MODIFIED — `save_source_intelligence()`, `get_source_intelligence()` |
| `open_notebook/graphs/acm_extraction.py` | MODIFIED — `save_intelligence_node`, graph wiring |
| `api/models.py` | MODIFIED — `SourceIntelligenceResponse` Pydantic model |
| `api/routers/acm.py` | MODIFIED — `GET /api/acm/source-intelligence/{source_id}` endpoint |
| `frontend/src/lib/types/intelligence.ts` | NEW — TypeScript types |
| `frontend/src/lib/hooks/use-source-intelligence.ts` | NEW — polling hook |
| `frontend/src/components/acm/SourceIntelligencePanel.tsx` | NEW — Intelligence tab component |
| `frontend/src/app/(dashboard)/sources/[id]/page.tsx` | MODIFIED — add Intelligence tab |

---

## Implementation Details

### Database (Migration 41)

```sql
DEFINE TABLE IF NOT EXISTS source_intelligence SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS source_id ON TABLE source_intelligence TYPE record<source>;
DEFINE FIELD IF NOT EXISTS document_meta ON TABLE source_intelligence TYPE option<object>;
DEFINE FIELD IF NOT EXISTS document_structure ON TABLE source_intelligence TYPE option<object>;
DEFINE FIELD IF NOT EXISTS building_inventory ON TABLE source_intelligence TYPE option<object>;
DEFINE FIELD IF NOT EXISTS page_tags ON TABLE source_intelligence TYPE option<object>;
DEFINE FIELD IF NOT EXISTS total_pages ON TABLE source_intelligence TYPE option<int>;
DEFINE FIELD IF NOT EXISTS total_buildings ON TABLE source_intelligence TYPE option<int>;
DEFINE FIELD IF NOT EXISTS document_type ON TABLE source_intelligence TYPE option<string>;
DEFINE FIELD IF NOT EXISTS register_page_range ON TABLE source_intelligence TYPE option<object>;
DEFINE INDEX IF NOT EXISTS idx_source_intelligence_source_id ON TABLE source_intelligence FIELDS source_id UNIQUE;
```

### Backend

- `save_source_intelligence(source_id, data)` — UPSERT into table
- `get_source_intelligence(source_id)` — SELECT with source_id filter
- `save_intelligence_node` — LangGraph node after `tag_pages`, before `orchestrate`; wrapped in try/except (non-blocking)
- `GET /api/acm/source-intelligence/{source_id:path}` — returns `SourceIntelligenceResponse` or 404

### Frontend

- `SourceIntelligence` types mirror the API response
- `useSourceIntelligence(sourceId, isExtracting)` — polls every 5s while extracting, fetches once otherwise
- `SourceIntelligencePanel` — Document Overview, Building Inventory (Accordion), Page Analysis (ScrollArea table)
- Source detail page adds "Intelligence" tab with Brain icon

---

## Test Coverage

- `tests/test_e2e_extraction.py` — integration tests for save/get intelligence
- `tests/test_orchestrator.py` — save_intelligence_node unit tests
