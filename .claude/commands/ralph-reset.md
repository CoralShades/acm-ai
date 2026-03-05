Reset a completed story to re-run it through the Ralph loop.

## Arguments
- `$ARGUMENTS` — `<story-id> [--keep-spec] [--keep-code]`

---

## Steps

### 1. Read State
Read `prd.json` (always use `encoding='utf-8'`). Find the story by ID.

If `passes` is not `true`, abort: "Story {ID} is not complete. Nothing to reset."

### 2. Show Current State
```
Story: {ID} — {TITLE}
Completed: {implementedDate}
Tech Spec: {techSpecFile}
Notes: {notes}
```

### 3. Determine Reset Scope

| Flag | Effect |
|------|--------|
| (no flags) | Full reset: clear passes, date, notes. Keep tech spec. |
| `--keep-spec` | Reset implementation but keep tech spec file path |
| `--keep-code` | Only reset prd.json state (code stays, can re-run QA/Review) |

### 4. Check Downstream Impact

Find all stories that depend on this one (directly or via gates). If any downstream stories have `passes: true`, warn:

```
Warning: Resetting {ID} affects downstream stories:
- E30-S5 (DONE) — depends on {ID}
- E31-S2 (DONE) — depends on E31-S1 which depends on GATE:SCHEMA_FREEZE triggered by E30-S6

Resetting will NOT automatically reset downstream stories.
They may need manual reset if re-implementation changes interfaces.

Proceed? [y/n]
```

If this story is a gate trigger and the gate is unlocked:
```
Warning: {ID} is the trigger for GATE:{gate_name} (currently UNLOCKED).
Resetting this story will NOT automatically re-lock the gate.
Use /ralph-gate lock {gate_name} if needed.
```

Use AskUserQuestion to confirm.

### 5. Apply Reset

Update prd.json:
- Set `passes: false`
- Set `implementedDate: null`
- Set `notes: "RESET: Re-run requested"`
- If NOT `--keep-spec`: set `techSpecFile: null`

### 6. Report
```
Story {ID} reset. Ready for re-run.
Tech spec: {kept|cleared}
Code: {kept|will be re-implemented}

Next: /ralph-run {ID}
```
