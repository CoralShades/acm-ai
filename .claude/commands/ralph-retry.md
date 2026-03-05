Retry a blocked or failed story in the Ralph loop.

## Arguments
- `$ARGUMENTS` — Story ID (e.g., `E30-S1`). Required.

---

## Steps

### 1. Read State
Read `prd.json` (always use `encoding='utf-8'`). Find the story by ID.

If the story doesn't exist, abort: "Story {ID} not found in prd.json."
If the story already has `passes: true`, abort: "Story {ID} is already complete. Use `/ralph-reset` to re-run it."

### 2. Show Block Reason
Display the current `notes` field for the story:
```
Story: {ID} — {TITLE}
Status: BLOCKED
Reason: {notes}
```

### 3. Clear Block
Update prd.json:
- Set `notes: ""` (clear the block reason)

### 4. Check Dependencies
Verify all dependencies are satisfied:
- Story deps: all must have `passes: true`
- Gate deps: all must have `unlocked: true`

If deps are NOT satisfied, warn:
```
Warning: {ID} has unmet dependencies:
- E30-S1 (not done)
- GATE:SCHEMA_FREEZE (locked)

The story will still be blocked by the dependency graph.
Use /ralph-gate to manually unlock gates if needed.
```

If deps ARE satisfied:
```
Story {ID} unblocked. It is now eligible for /ralph-run.
Run: /ralph-run {ID}
```

### 5. Optional: Re-run Immediately
If the user's arguments include `--run` (e.g., `/ralph-retry E30-S1 --run`):
- After clearing the block, immediately invoke the `/ralph-run` flow for this story
