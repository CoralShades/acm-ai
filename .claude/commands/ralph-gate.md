Manually control Ralph dependency gates.

## Arguments
- `$ARGUMENTS` — `<action> <gate-id>`
  - Actions: `show`, `unlock`, `lock`
  - Gate IDs: `SCHEMA_FREEZE`, `EXTRACTION_COMPLETE`, `AI_COMPLETE`, `UI_COMPLETE`

If no arguments, defaults to `show` (all gates).

---

## `show` — Display Gate Status

Read `prd.json` (always use `encoding='utf-8'`; `gates` is a **list** of objects, not a dict). Display all gates:

```
Ralph V3 Gates
══════════════

GATE:SCHEMA_FREEZE
  Status:   LOCKED ○ / UNLOCKED ●
  Trigger:  E30-S6 — BAR->SF Vocabulary Mapping (passes: false)
  Blocks:   E31-S1, E33-S1, E33-S2 (+ 24 downstream)
  Purpose:  All SF schema definitions finalized

GATE:EXTRACTION_COMPLETE
  Status:   LOCKED ○
  Trigger:  E31-S6 — Extraction Pipeline Integration (passes: false)
  Blocks:   (no direct blocks — informational gate)
  Purpose:  Multi-provider extraction pipeline operational

GATE:AI_COMPLETE
  Status:   LOCKED ○
  Trigger:  E32-S5 — AI Pipeline Integration (passes: false)
  Blocks:   E33-S3 (+ downstream)
  Purpose:  AI validation and correction pipeline operational

GATE:UI_COMPLETE
  Status:   LOCKED ○
  Trigger:  E33-S8 — Frontend Dashboard Integration (passes: false)
  Blocks:   E34-S4
  Purpose:  All frontend views operational
```

---

## `unlock` — Manually Unlock a Gate

```
/ralph-gate unlock SCHEMA_FREEZE
```

Updates prd.json:
- Set gate's `unlocked: true`

Before unlocking, show impact:
```
Unlocking GATE:SCHEMA_FREEZE will make eligible:
- E31-S1 — Docling Provider Adapter (if other deps met)
- E33-S1 — Provenance Timeline Component (if other deps met)
- E33-S2 — ACM Register Grid Views (if other deps met)

Warning: The trigger story E30-S6 has NOT been completed.
Unlocking manually bypasses the natural dependency flow.

Proceed? [y/n]
```

Use AskUserQuestion to confirm.

---

## `lock` — Re-lock a Gate

```
/ralph-gate lock SCHEMA_FREEZE
```

Updates prd.json:
- Set gate's `unlocked: false`

Before locking, warn about downstream impact:
```
Locking GATE:SCHEMA_FREEZE will block:
- E31-S1 (currently eligible)
- E33-S1, E33-S2 (currently eligible)

Any in-progress stories depending on this gate should be completed first.

Proceed? [y/n]
```

---

## Gate Dependency Reference

| Gate | Trigger | Stories Directly Blocked |
|------|---------|------------------------|
| SCHEMA_FREEZE | E30-S6 | E31-S1, E33-S1, E33-S2, E30-S7 |
| EXTRACTION_COMPLETE | E31-S6 | (informational) |
| AI_COMPLETE | E32-S5 | E33-S3 |
| UI_COMPLETE | E33-S8 | E34-S4 |
