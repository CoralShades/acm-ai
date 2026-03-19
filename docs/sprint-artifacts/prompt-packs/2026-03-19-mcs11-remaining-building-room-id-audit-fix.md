# MCS11-CodeGen: Building Code + Room ID Generation Fix
# Generated from live DB audit — 2026-03-19

**SP: 5 | Priority: P0 | Dependencies: MCS8 (ghost save fix), MCS11-Gap4 (FK fix)**
**Audit ref: Live DB query confirmed building_code contains names not codes for ARA-format PDFs**
**Blocks: MCS11 Frontend Phases (per-building filtering depends on stable building_code)**

## Skills to Load

/systematic-debugging — trace building_code assignment from inventory → BuildingRecord
/test-driven-development — write tests before fixing
/langgraph-fundamentals — understand BuildingInventory → extract_building_node flow
/planning-with-files — persistent markdown plan
/verification-before-completion — verify DB state after fix

---

## Problem Statement

### Problem 1: building_code = building name for ARA-format PDFs

When a PDF does not contain DET-style coded building headers (e.g., `B001`, `D02`), the `_heuristic_fallback()` function in `building_inventory.py` falls through to ARA format detection. In that path (line 542), each `BuildingMeta` is created with:

```python
BuildingMeta(
    building_id=name,   # ← the full building name string, e.g. "Nurses Accommodation"
    name=name,
    ...
)
```

This `building_id` then flows directly into `acm_extraction.py` where:

```python
building_code=building_meta_entry.building_id  # line 696, 738
```

Result: `BuildingRecord.building_code = "Nurses Accommodation"` instead of a generated code like `B007`.

**Confirmed in live DB (2026-03-19):**
```
building_code="Mortuary Buildings"   → should be B004 or similar
building_code="Nurses Accommodation" → should be B007 or similar
building_code="VMO Accommodations"   → should be B006 or similar
building_code="Pathology Department" → should be B005 or similar

building_code="B00A"  ← DET format — correct
building_code="B00E"  ← DET format — correct
```

### Problem 2: room_id is always NULL

`ACMRecord.room_id` (maps to `Room_ID__c` in Salesforce) is `null` for every record in DB. The pipeline never assigns room IDs. Neither the LLM prompt nor any post-processing step generates room codes. Rooms are referenced only by `room_name` (free text). This makes Salesforce integration impossible for the Room_ID__c required field.

### Why This Matters

- `code_to_id_map` in `extract_items_node` keyed on `building_code` — if building_code is a name, the map lookup fails if the name contains special chars or whitespace differences
- Frontend building filter tabs key on `building_code` — a name-as-code breaks sorting, deduplication, and cross-source comparisons
- Salesforce `Building_Code__c` field expects short codes like `B001`, not full names
- `room_id` (`Room_ID__c`) is a Salesforce required field — always NULL breaks SF sync

---

## Root Cause Chain

```
PDF (ARA format, no B### headers)
  └─► _heuristic_fallback() in building_inventory.py line 542
        └─► BuildingMeta(building_id=name, name=name)   ← name used as ID
              └─► extract_building_node: building_code=building_meta_entry.building_id
                    └─► BuildingRecord.building_code = "Nurses Accommodation"
                          └─► code_to_id_map["Nurses Accommodation"] → FK lookup key
                                └─► ACMRecord.building_code = "Nurses Accommodation"
```

For room IDs — there is no generation path at all. The field exists on the model but nothing populates it.

---

## Key Files

**Read (understand before fixing):**
- `open_notebook/extractors/building_inventory.py` — `_heuristic_fallback()` lines 515-549 (ARA path), `_detect_ara_buildings()` — where name-as-id is set
- `open_notebook/graphs/acm_extraction.py` — lines 630-760 (`extract_building_node`), lines 1025-1040 (`code_to_id_map` build), lines 1080-1200 (`_extract_items_for_building`)
- `open_notebook/domain/acm.py` — `BuildingRecord.building_code` field (line 700), `ACMRecord.room_id` field (line 124), `ACMRecord.building_id` field (line 80)
- `open_notebook/extractors/acm_schemas_v3.py` — `BuildingExtractionResult` model — note it has NO `building_code` field; code comes from `BuildingMeta.building_id`

**Modify:**
- `open_notebook/extractors/building_inventory.py` — ARA path: generate sequential B-codes instead of using name as ID; store name separately in `BuildingMeta.name`
- `open_notebook/graphs/acm_extraction.py` — `extract_items_node`: add room_id generation (sequential R001, R002 per building) after per-row extraction; set `record.room_id` before save
- `open_notebook/domain/acm.py` — verify `room_id` field validator is tolerant of generated codes

**Test:**
- `tests/test_building_inventory.py` — test ARA-format input produces B-coded building_ids
- `tests/test_building_record.py` — test building_code is never a long name string
- `tests/test_room_id_generation.py` (create) — test room_id assigned sequentially per building

---

## Audit Results (do not re-audit, use these findings)

### Live DB state (queried 2026-03-19):
- 14 building_record rows total
- 4 rows have building_code = a full name string (ARA-format source)
- 10 rows have building_code = B00x code (DET-format source, correct)
- ALL acm_record rows have room_id = null (20 sampled, all null)

### Format detection split:
- DET format (B###): `building_inventory.py` line 476-513 → `building_id` from regex group(1) → CORRECT
- ARA format: `building_inventory.py` line 523-548 → `building_id=name` → BUG
- Generic fallback: line 558-574 → `building_id` from `document_structure.building_ids` → may also be names

---

## Plan

### Phase 1: Fix ARA Building Code Generation (Backend)

- [ ] 1.1 In `_heuristic_fallback()` ARA path (building_inventory.py ~line 523), generate sequential codes:
  - Change `building_id=name` to `building_id=f"B{i+1:03d}"` (B001, B002, ...)
  - Keep `name=name` unchanged
  - Handle the generic fallback path (line 558-574) similarly: generate codes if `bid` from structure is a name not a code
- [ ] 1.2 Add a helper `_is_coded_building_id(bid: str) -> bool` that returns True for pattern `[A-Z]\d+` or `D\d+` (DET codes), False for anything else
- [ ] 1.3 In generic fallback path, use `_is_coded_building_id(bid)` — if False, replace `bid` with sequential code
- [ ] 1.4 Write `tests/test_building_inventory.py` — verify ARA path produces B001, B002 codes not names

### Phase 2: Fix Building Code Propagation (Validation)

- [ ] 2.1 In `extract_building_node` (acm_extraction.py), add assertion/warning if `building_meta_entry.building_id` looks like a long name (len > 10 and not matching `[A-Z]\d+`)
  - This is a defensive guard — after Phase 1 fix, should never trigger
- [ ] 2.2 In `code_to_id_map` build (acm_extraction.py ~line 1030), log a warning if any key has len > 10
- [ ] 2.3 Verify `ACMRecord.building_id` (the field on acm_record, not building_record) is set to the same code as `BuildingRecord.building_code` — trace through `_extract_items_for_building`

### Phase 3: Room ID Generation

- [ ] 3.1 In `_extract_items_for_building` (acm_extraction.py ~line 1080), after per-row extraction produces `records: list[ACMExtractionRecord]`:
  - Build a `room_name → room_code` mapping scoped to the current building
  - Assign `R{n:03d}` codes sequentially by order of first appearance
  - Set `record.room_id = room_name_to_code[record.room_name]` for each record
- [ ] 3.2 For bulk extraction path (where per-row didn't run), apply same room_id generation in the bulk results post-processing
- [ ] 3.3 Room code scope: per-building (R001 resets for each building), NOT global
  - Rationale: Salesforce Room_ID__c is relative to Building_Code__c
- [ ] 3.4 Handle `room_name=None` records: assign `room_id=None` (do not generate a code for nameless rooms)
- [ ] 3.5 Write `tests/test_room_id_generation.py` — verify room_id is populated, resets per building, None for null room_name

### Phase 4: Verify DB State

- [ ] 4.1 Run full extraction on Alexander PDF (has ARA-format buildings)
- [ ] 4.2 Query: `SELECT building_code, building_name FROM building_record WHERE source_id = '...'`
  - Verify all building_codes are B001, B002, ... style (no full names)
- [ ] 4.3 Query: `SELECT room_id, room_name, building_code FROM acm_record LIMIT 50`
  - Verify room_id is populated (R001, R002, ...) for all records with room_name
- [ ] 4.4 Verify `code_to_id_map` lookup works correctly (no FK-miss warnings in logs)
- [ ] 4.5 Verify building deduplication (`_disambiguate_duplicate_names`) still works correctly after code generation change

### Phase 5: Regression Check

- [ ] 5.1 Run extraction on a DET-format PDF (with B### headers)
- [ ] 5.2 Verify DET building_codes are unchanged (still B001, D02, etc. from PDF)
- [ ] 5.3 Verify room_ids also populated for DET-format extraction
- [ ] 5.4 Run existing tests: `uv run pytest tests/test_building_record.py`

---

## Agent Strategy

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `backend-fixer` | Fix ARA building code + room_id generation | sonnet | Phase 1-3 |
| `verifier` | DB state verification + regression tests | sonnet | Phase 4-5 |

**Sequential**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

---

## Verification Checklist

- [ ] No `BuildingRecord.building_code` value has `len > 10` (no full names stored as codes)
- [ ] ARA-format PDFs produce B001, B002, ... style codes
- [ ] DET-format PDFs unchanged (B### from PDF preserved)
- [ ] All `acm_record.room_id` non-null where `room_name` is non-null
- [ ] Room codes reset per building (B001 rooms: R001-R005; B002 rooms: R001-R003 etc.)
- [ ] `code_to_id_map` lookup succeeds for all buildings (no FK-miss warnings in logs)
- [ ] `uv run pytest tests/test_building_inventory.py` passes
- [ ] `uv run pytest tests/test_building_record.py` passes
- [ ] `uv run pytest tests/test_room_id_generation.py` passes

---

## Commit Template

```
fix(extraction): generate sequential building codes and room IDs for ARA-format PDFs

- ARA-format buildings no longer use name as building_code (was "Nurses Accommodation")
- _heuristic_fallback() now generates B001, B002, ... codes for ARA path
- room_id assigned R001, R002, ... per-building based on room_name first appearance
- DET-format building codes (B### from PDF headers) unchanged
- Fixes Salesforce Building_Code__c and Room_ID__c field population
- MCS11 — building/room ID generation audit fix

Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## Execution Order

This pack is **foundational** — it must run before MCS11 frontend phases because the frontend building filter tabs and per-building item queries depend on stable, code-format `building_code` values.

**Recommended sequence:**

1. **This pack (MCS11 Building/Room ID Fix)** — backend, foundational, must run first
2. **MCS12** (`2026-03-19-mcs12-extraction-events-dead-endpoint.md`) — backend SSE events, independent of building codes, can run in parallel with this pack
3. **MCS13** (`2026-03-19-mcs13-schema-inference-documentmeta-fix.md`) — backend schema inference, independent, can also run in parallel
4. **MCS11 Frontend Phases** (`2026-03-19-mcs11-remaining-frontend-phases.md`) — depends on stable building_code (this pack) and MCS11-Gap4 FK fix
5. **MCS11 Verification** (`2026-03-19-mcs11-remaining-verification.md`) — final, depends on all above
