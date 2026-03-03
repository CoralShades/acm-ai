Show the current Ralph V3 progress status.

This is a read-only command that parses `prd.json` and displays progress.

## Steps

### 1. Read prd.json
Read `prd.json` from the project root. If it doesn't exist, report: "No prd.json found. Run `/ralph-bridge` first to generate it."

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

Group stories by sprint (V3-1 through V3-7):
- Show done/total per sprint
- Show SP completed/total per sprint

### 5. Next Eligible Story

Find the next story to work on using priority rules:
1. Sprint order (V3-1 first, then V3-2, etc.)
2. Within a sprint: story points ascending (small wins first)
3. All dependencies satisfied (story deps + gate deps)

### 6. Display Report

```
╔══════════════════════════════════════════╗
║         Ralph V3 Progress Report         ║
╠══════════════════════════════════════════╣
║ Stories: {done}/33 done ({pct}%)         ║
║ Story Points: {sp_done}/97 completed     ║
║ Current Sprint: V3-{N}                   ║
╠══════════════════════════════════════════╣
║ GATES                                    ║
║ ○ SCHEMA_FREEZE    — {status} (E30-S6)   ║
║ ○ EXTRACTION_COMPLETE — {status} (E31-S6)║
║ ○ AI_COMPLETE      — {status} (E32-S5)   ║
║ ○ UI_COMPLETE      — {status} (E33-S8)   ║
╠══════════════════════════════════════════╣
║ SPRINTS                                  ║
║ V3-1: {done}/{total} ({sp} SP)           ║
║ V3-2: {done}/{total} ({sp} SP)           ║
║ ...                                      ║
╠══════════════════════════════════════════╣
║ NEXT: {story_id} — {title} ({sp} SP)     ║
║ Blocked: {N} stories waiting on deps     ║
╚══════════════════════════════════════════╝
```

### 7. Blocked Stories (if any)

List stories that are blocked and what they're waiting on:
```
Blocked Stories:
- E31-S1 — waiting on GATE:SCHEMA_FREEZE (trigger: E30-S6)
- E33-S2 — waiting on GATE:SCHEMA_FREEZE + E30-S2
```
