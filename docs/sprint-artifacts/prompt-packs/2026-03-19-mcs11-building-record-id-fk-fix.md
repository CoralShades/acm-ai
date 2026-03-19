# MCS11-Gap4: Fix building_record_id FK — Remove NULL Workaround
# Generated from MCS7 validation audit — 2026-03-19

**SP: 3 | Priority: P1 | Dependencies: MCS8 (ghost save fix)**
**Audit ref: Pipeline Persistence Timing Audit — Gap 4 (building_record_id always NULL)**
**Related commits: fa1ff9a4 (validation), 881f04f1 (format profile registry)**

## Skills to Load

/systematic-debugging — trace FK value through pipeline
/langgraph-fundamentals — understand state passing between nodes
/planning-with-files — persistent markdown plan
/test-driven-development — write failing test for FK population
/e2e-test — verify FK works end-to-end in frontend
/acm-observability — verify provenance chain in traces
/verification-before-completion — verify FKs populated

---

## Problem Statement

At `acm_extraction.py:2761`, there's a workaround:
```python
acm_record.building_record_id = None
acm_record.parent_table_id = None
```

This nulls out the FK linking `acm_record` to `building_record` before save. It was added during MCS7 because the SurrealDB Python client tried to parse `"building_record:xxx"` strings as RecordIDs, causing save failures.

### Impact
- ACM records have no FK to their building — the relationship is broken at DB level
- Frontend can't filter items by building using the FK
- `useACMItems` hook relies on building_record_id for per-building queries
- Provenance chain is broken: ACMRecord → BuildingRecord → Source

### Root Cause Chain
1. `extract_building_node` saves BuildingRecord, gets `record.id` (via query-back)
2. `extract_items_node` populates `building_record_id` on ACMExtractionRecords (lines 1174-1179)
3. `save_records` nulls it out before save → FK always NULL in DB

### After MCS8 Fix
Once MCS8 fixes the ghost save and SurrealDB record-link handling, the workaround can be removed. The `building_record_id` should be passed through correctly as a `record<building_record>` type value.

---

## Key Files

**Read:**
- `open_notebook/graphs/acm_extraction.py` — line 2761 (workaround), lines 1174-1179 (FK population), lines 1001-1026 (code_to_id_map lookup)
- `open_notebook/domain/acm.py` — `ACMRecord.building_record_id` field definition (line 117)
- `migrations/40.surrealql` — `building_record_id TYPE option<record<building_record>>`
- `frontend/src/lib/hooks/useACMItems.ts` — how frontend queries items by building

**Modify:**
- `open_notebook/graphs/acm_extraction.py` — remove lines 2761-2762 (null workaround)
- Ensure `code_to_id_map` at line 1004 produces valid record link strings

**Test:**
- `tests/test_acm_fk_population.py` (create) — verify building_record_id is populated after extraction

---

## Plan

### Phase 1: Verify MCS8 Prerequisite
- [ ] Confirm `base.py:save()` no longer has early-return guard
- [ ] Confirm `repo_create` returns proper dicts
- [ ] Confirm building records save with valid IDs (no query-back needed)

### Phase 2: Remove Workaround
- [ ] Remove lines 2761-2762 (`building_record_id = None`, `parent_table_id = None`)
- [ ] Verify `code_to_id_map` at line 1004 contains valid `building_record:xxx` strings
- [ ] Verify `section_map` at line 2690 contains valid `acm_table_section:xxx` strings

### Phase 3: Test FK Population
- [ ] Run extraction on Broadmeadows
- [ ] Query: `SELECT building_record_id FROM acm_record WHERE source_id = 'source:...'`
- [ ] Verify ALL records have non-NULL `building_record_id`
- [ ] Verify FK values match actual `building_record` IDs

### Phase 4: Frontend Verification
- [ ] Verify `useACMItems` hook can filter by building_record_id
- [ ] Verify building detail view shows correct items
- [ ] Run /e2e-test for building → items drill-down

---

## Agent Strategy: Agent Team (Opus)

Create team `mcs11-fk-fix` with 3 agents:

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `backend-fixer` | Remove workaround, verify FK flow | opus | Phase 1-3 |
| `frontend-verifier` | Verify FK queries work in hooks + UI | opus | Phase 4 |
| `test-writer` | Write integration tests for FK population | opus | Phase 3 |

---

## Verification Checklist

- [ ] `acm_record.building_record_id` is NOT NULL for all extracted records
- [ ] `acm_record.parent_table_id` is NOT NULL (links to acm_table_section)
- [ ] FK values match actual building_record IDs in DB
- [ ] Frontend items grid filters by building correctly
- [ ] Provenance chain works: ACMRecord → BuildingRecord → Source
- [ ] `/e2e-test` passes for building → items navigation
- [ ] No workaround code remains in `acm_extraction.py`

---

## Commit Template

```
fix(extraction): restore building_record_id FK — remove MCS7 NULL workaround

- Remove building_record_id=None and parent_table_id=None workaround
- building_record_id now populated correctly as record<building_record>
- parent_table_id populated as record<acm_table_section>
- Provenance chain restored: ACMRecord → BuildingRecord → Source
- MCS11 — Pipeline Persistence Timing Audit Gap 4

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
