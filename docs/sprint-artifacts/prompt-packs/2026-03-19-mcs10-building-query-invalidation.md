# MCS10-Gap2+3: Fix Building Query Invalidation + Items Query Timing
# Generated from MCS7 validation audit — 2026-03-19

**SP: 3 | Priority: P1 | Dependencies: MCS9 (SSE save events)**
**Audit ref: Pipeline Persistence Timing Audit — Gap 2 (buildings query) + Gap 3 (items query premature)**
**Related commits: 5d560d06 (Live extraction UX), 80267917 (HITL UI)**

## Skills to Load

/frontend-design — React Query invalidation patterns
/ui-ux-pro-max — real-time building list updates, extraction progress per building
/uncodixfy — prevent generic loading spinners, use contextual progress
/react-best-practices — React Query staleTime, invalidation, optimistic updates
/planning-with-files — persistent markdown plan
/e2e-test — browser verification of building list updates
/verification-before-completion — verify timing is correct

---

## Problem Statement

### Gap 2: Buildings Query Invalidated Too Late
`useV3BuildingStream` invalidates `['buildings', 'v3', sourceId]` only on `ai.validation_complete`. But buildings are saved to DB in `extract_building` node — much earlier. The frontend can't show the building list until the entire extraction finishes, even though buildings exist in DB within the first 2-3 minutes.

### Gap 3: Items Query Invalidated Too Early
`useV3BuildingStream` invalidates `['acm', 'items', sourceId]` on `ai.building_extracted`. But at that point, items haven't been extracted yet. The refetch returns empty results.

### Correct Timing

```
extract_building ── ai.building_extracted ── buildings IN DB ✓
                    → SHOULD invalidate buildings query HERE ✓
                    → SHOULD NOT invalidate items query ✗

extract_items ── ai.items_extracted ── items NOT in DB yet
                    → items query invalidation is USELESS here

save ── ai.save_complete (from MCS9) ── items NOW in DB ✓
                    → SHOULD invalidate items query HERE ✓
```

---

## Key Files

**Read:**
- `frontend/src/lib/hooks/useV3BuildingStream.ts` — the event handler (lines 37-68)
- `frontend/src/lib/hooks/useBuildings.ts` — buildings query hook
- `frontend/src/lib/hooks/useACMItems.ts` — items query hook
- `frontend/src/components/acm/BuildingGrid.tsx` — building list component
- `frontend/src/components/acm/ACMGrid.tsx` — items grid component
- `frontend/src/lib/stores/buildingStore.ts` — Zustand building state

**Modify:**
- `frontend/src/lib/hooks/useV3BuildingStream.ts` — fix invalidation targets per event
- `frontend/src/components/acm/BuildingGrid.tsx` — show buildings as they appear
- `frontend/src/components/acm/` — add per-building extraction status indicator

---

## Plan

### Phase 1: Fix Buildings Query Invalidation
- [ ] In `useV3BuildingStream`, on `ai.building_extracted`:
  - ADD invalidation of `['buildings', 'v3', sourceId]` (buildings ARE in DB now)
  - REMOVE invalidation of `['acm', 'items', sourceId]` (items don't exist yet)
- [ ] Reduce `staleTime` on `useBuildings` from 30s to 5s during active extraction
- [ ] Show building in grid immediately with "Extracting..." status badge

### Phase 2: Fix Items Query Invalidation
- [ ] On `ai.items_extracted`: update building status to "Validating" but DON'T invalidate items query
- [ ] On `ai.save_complete` (from MCS9): invalidate `['acm', 'items', sourceId]` — items NOW exist
- [ ] Add building-specific invalidation: `['acm', 'items', sourceId, buildingId]`

### Phase 3: Per-Building Status UI
- [ ] Show building card with status: "Detected" → "Extracting" → "Validating" → "Saved"
- [ ] Show item count badge per building as extraction progresses
- [ ] Use SSE events to transition states: `ai.building_extracted` → `ai.items_extracted` → `ai.save_complete`
- [ ] Apply /ui-ux-pro-max and /uncodixfy rules — no generic spinners, show contextual info

### Phase 4: Verification
- [ ] Upload PDF, verify buildings appear in grid within 30s of extraction start
- [ ] Verify items appear ONLY after save_complete event
- [ ] Verify building status transitions correctly
- [ ] Run /e2e-test for building list during extraction
- [ ] Screenshot evidence at each stage

---

## Agent Strategy: Agent Team (Opus)

Create team `mcs10-building-timing` with 3 agents:

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `hook-fixer` | Fix useV3BuildingStream invalidation logic | opus | Phase 1-2 |
| `ui-builder` | Per-building status UI with /ui-ux-pro-max + /uncodixfy | opus | Phase 3 |
| `e2e-tester` | Browser verification with /e2e-test | opus | Phase 4 |

---

## Verification Checklist

- [ ] Buildings appear in grid as `ai.building_extracted` events arrive (not waiting for validation)
- [ ] Items grid shows "Waiting for extraction..." until `ai.save_complete`
- [ ] Items appear in grid after `ai.save_complete` fires
- [ ] Per-building status badge shows correct state transitions
- [ ] No empty/stale data from premature query invalidation
- [ ] `/e2e-test` passes for real-time building list updates
- [ ] No `/uncodixfy` violations (no generic spinners or loading placeholders)

---

## Commit Template

```
fix(ux): correct building and items query invalidation timing for real-time extraction display

- Invalidate buildings query on ai.building_extracted (buildings ARE in DB)
- Defer items query invalidation to ai.save_complete (items only exist after save)
- Add per-building status indicator: Detected → Extracting → Validating → Saved
- Remove premature items invalidation from ai.building_extracted handler
- MCS10 — Pipeline Persistence Timing Audit Gap 2 + Gap 3

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
