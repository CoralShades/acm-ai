Skip a story or mark it as manually blocked/done in the Ralph loop.

## Arguments
- `$ARGUMENTS` — `<story-id> <action> [reason]`
  - Actions: `block`, `done`, `defer`

---

## Actions

### `block` — Mark Story as Blocked
```
/ralph-skip E30-S4 block "Waiting for SF field mapping confirmation from stakeholder"
```

Updates prd.json:
- Set `notes: "BLOCKED: {reason}"`
- Story will be skipped by `/ralph-run` auto-selection

### `done` — Mark Story as Manually Complete
```
/ralph-skip E30-S6 done "Completed manually outside Ralph loop"
```

Updates prd.json:
- Set `passes: true`
- Set `implementedDate` to today
- Set `notes: "Manual: {reason}"`
- **Gate check**: If this story is a gate trigger, unlock the gate

This is useful when:
- A story was implemented in a previous session without Ralph
- A story is a doc/planning-only task completed outside the loop
- You want to unlock downstream stories by marking a dep as done

### `defer` — Defer to a Later Sprint
```
/ralph-skip E32-S6 defer "Ollama spike — not needed for MVP"
```

Updates prd.json:
- Set `notes: "DEFERRED: {reason}"`
- Story will be skipped by auto-selection but NOT marked as done
- Downstream stories that depend on this remain blocked

---

## Confirmation

Before making any change, show:
```
Action: {action}
Story: {ID} — {TITLE} ({SP} SP)
Reason: {reason}
Impact: {N} downstream stories affected

Proceed? [y/n]
```

Use AskUserQuestion to confirm.

---

## Undo

To undo a skip:
- `block` → Use `/ralph-retry {ID}` to clear the block
- `done` → Use `/ralph-reset {ID}` to un-complete it
- `defer` → Use `/ralph-retry {ID}` to clear the deferral
