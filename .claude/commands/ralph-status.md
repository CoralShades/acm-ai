Show the current Ralph V3 progress status.

This is a read-only command that parses `prd.json` and displays progress.

## Steps

### 1. Read prd.json
Read `prd.json` from the project root. If it doesn't exist, report: "No prd.json found. Run `/ralph-bridge` first to generate it."

**IMPORTANT — Python encoding on Windows**: Always open prd.json with `encoding='utf-8'` to avoid cp1252 UnicodeDecodeError. Likewise when writing output, use `errors='replace'` or ensure UTF-8 stdout.

**Data types in prd.json**:
- `sprints` is an **integer** (sprint count), not a dict
- `gates` is a **list** of gate objects (each with `id`, `unlocked`, `triggerStory`, `blocksEpics`), not a dict — iterate with `for gate in gates`, not `gates.items()`

### 2. Calculate Progress

Count:
- **Done**: stories where `passes === true`
- **In Progress**: stories where `notes` contains "IN_PROGRESS"
- **Blocked**: stories where all deps are NOT satisfied (dep story `passes=false` or gate `unlocked=false`)
- **Eligible**: stories where `passes === false`, not blocked, no "BLOCKED" in notes

### 3. Gate Status

For each gate:
- Show locked/unlocked status
- Show trigger story and whether it's done
- Show how many stories are waiting on this gate

### 4. Sprint Progress

Group stories by their `sprint` field (V3-1 through V3-N, where N = `sprints` integer from prd.json):
- Show done/total per sprint
- Show SP completed/total per sprint

### 5. Next Eligible Story

Find the next story to work on using priority rules:
1. Sprint order (V3-1 first, then V3-2, etc.)
2. Within a sprint: P0 first, then P1, then P2; within same priority: story points ascending
3. All dependencies satisfied (story deps + gate deps)
4. Stories with unsatisfied `dependencies` (where dep story `passes=false`) are blocked

### 6. Display Report

```
╔══════════════════════════════════════════════╗
║         Ralph V3 Progress Report             ║
╠══════════════════════════════════════════════╣
║ Stories: {done}/{total} done ({pct}%)        ║
║ Story Points: {sp_done}/{sp_total} completed ║
║ Current Sprint: V3-{N}                       ║
╠══════════════════════════════════════════════╣
║ GATES                                        ║
║  (iterate gates list — show each gate's      ║
║   id, unlocked status, and triggerStory)     ║
╠══════════════════════════════════════════════╣
║ SPRINTS                                      ║
║  (iterate all sprints found in stories)      ║
║  V3-N: {done}/{total} ({sp} SP)              ║
╠══════════════════════════════════════════════╣
║ NEXT: {story_id} — {title} ({sp} SP)         ║
║ Blocked: {N} stories waiting on deps         ║
╚══════════════════════════════════════════════╝
```

### 7. Blocked Stories (if any)

List stories that are blocked and what they're waiting on:
```
Blocked Stories:
- E31-S1 — waiting on GATE:SCHEMA_FREEZE (trigger: E30-S6)
- E33-S2 — waiting on GATE:SCHEMA_FREEZE + E30-S2
```
