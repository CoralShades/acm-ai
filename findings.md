# Findings — Extraction Audit + Bug Fixes (2026-03-17)

## 1. Building Inventory Audit — ROOT CAUSE FOUND
- **File**: `open_notebook/extractors/building_inventory.py:681-699`
- **Root cause**: Cross-validation merge has false-negative deduplication. LLM returned `B001/Main Building`, heuristic returned `B00A/Broadmeadows Police Station`. Since neither ID nor name matched (AND condition), both kept.
- **Why non-deterministic**: LLM (temperature=0.1) returned different building IDs across runs. First run produced `B00A` (matching heuristic), second run produced `B001` (no match → 2 buildings).
- **Impact**: HIGH — phantom building B001 gets extraction attempted, which then fails due to quantity parse error, wasting compute.
- **Fix**: NOT applied this session — requires careful redesign of merge logic (fuzzy name matching or single-building document detection).

## 2. B001 Quantity Parse Failure — FIXED
- **File**: `open_notebook/extractors/acm_schemas_v3.py:79`
- **Root cause**: `ACMItemRecord.quantity: Optional[float]` rejects LLM strings like "2m 2", "10 lm". Pydantic validation failure discards the ENTIRE building's records, not just the 2 bad rows.
- **Fix**: Changed to `Optional[str]` to match every other layer (domain model, legacy schemas, downstream conversion). All other layers already use `str` for quantity.
- **Also fixed**: `orchestrator.py:531-534` — removed unnecessary `float→str` conversion, now passes through directly.

## 3. Job Detail Page Crash — FIXED
- **File**: `frontend/src/components/jobs/JobOverviewTab.tsx:161`
- **Root cause**: `buildingInventory.buildings.length` crashes when `buildings` is `null`/`undefined` inside a truthy `buildingInventory` object.
- **Fix**: Added optional chaining — `buildingInventory?.buildings?.length ?? 0` and `(buildingInventory?.buildings ?? []).map()`.
- **Build**: PASSED (`npm run build` clean).

## 4. Remaining: Building Inventory Merge (P2)
- The merge dedup at `building_inventory.py:681-699` uses ID+name AND match which fails when LLM invents generic names. Needs fuzzy matching or single-building document detection.
- Deferring to a future story.
