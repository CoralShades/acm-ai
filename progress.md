# E29-R2: Match-Gap Remediation — Dev Progress

## Session: 2026-03-02 | Agent: Amelia (Dev)

### Status: PLANNING COMPLETE → IMPLEMENTATION READY

### Reboot Check
1. **Last completed milestone**: R1 implementation complete (Docling fixtures, output-tag, matching normalization, baselines pinned)
2. **Current active task**: R2 planning phase complete — task plan created, findings documented
3. **Blockers**: None — R1 is done, all dependencies met
4. **Last modified files**: `findings.md`, `task_plan.md`, `progress.md` (planning only)
5. **Next planned action**: Execute T1 (RoomMeta typing fix in building_inventory.py)

### Phase: Research Complete → Implementation Next

Read and analyzed:
- `e29-gate2-recovery-spec.md` — R2 scope: 8 ACs, 7 tasks
- `building_inventory.py:448-504` — `_llm_compile_inventory()` + RoomMeta typing gap
- `orchestrator.py` — full extraction pipeline (no changes needed for R2)
- `e29_benchmark_harness.py` — matching engine (PRODUCT_SYNONYMS, 3-tier matching)
- `baseline_results.json` — Alexander 31/43 with 12 unmatched GT records
- `gate2_baseline.json` — pinned reference (immutable)
- `alexander.json` — full 43-record ground truth
- `broadmeadows.json` — full 31-record ground truth
- `test_orchestrator.py` — 61 existing tests (1492 lines)
- `test_strategy_registry.py` — 33 existing tests (no changes needed)
- `sprint-status.yaml` — R2 as `drafted`

### Key Findings
1. **Building name mismatch is the #1 root cause** — GT "Old Alexandra Hospital" vs extracted "Main Hospital Building" (8 of 12 unmatched records)
2. **RoomMeta typing bug** — LLM returns string rooms, Pydantic validation fails, falls back to heuristic
3. **Product synonym gaps** — "heater flue"/"heater", "ceiling"/"porch ceiling", parenthetical stripping
4. **Room name normalization** — "External"/"Exterior", whitespace collapse
5. **Conservative fix set** clears 36/43 Alexander floor easily (building synonyms alone recover 5-8 records)

### Decisions
- Fix matching engine (BUILDING_SYNONYMS, PRODUCT_SYNONYMS expansion, ROOM_SYNONYMS) — NOT the LLM prompts
- Fix RoomMeta typing at the `_llm_compile_inventory` boundary — coerce before validate
- No changes to orchestrator.py extraction logic — out of R2 scope
- No changes to ground truth files — they are the source of truth
