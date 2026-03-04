Run multiple eligible stories in sequence or prepare parallel session commands.

## Arguments
- `$ARGUMENTS` — `<mode> [options]`
  - Modes: `sequential`, `parallel`, `sprint <sprint-id>`

---

## `sequential` — Run N Stories Back-to-Back

```
/ralph-batch sequential [--count N] [--max-sp N] [--sprint V3-1]
```

Options:
- `--count N` — Run up to N stories (default: 3)
- `--max-sp N` — Only pick stories with SP <= N (default: no limit)
- `--sprint V3-1` — Only pick stories from this sprint

**Behavior**: Runs `/ralph-run` for each eligible story in sequence. After each story completes, checks if the next story is still eligible (deps may have changed). Stops after N stories or when no eligible stories remain.

### Steps
1. Read `prd.json`
2. Find all eligible stories (same logic as `/ralph-run` auto-select)
3. Apply filters (--max-sp, --sprint)
4. Take first N stories
5. Show plan:
```
Ralph Batch: Sequential Mode
Stories to run (up to {N}):
1. E30-S1 — SF Schema Config Loader (5 SP)
2. E30-S8 — Ollama Local Provider Config (2 SP)
3. E30-S3 — SF Field Aliases in Domain Models (3 SP)

Total: ~10 SP
Estimated phases: 3 stories × 7 phases = 21 agent spawns

Proceed? [y/n]
```
6. Use AskUserQuestion to confirm
7. Run each story through the full `/ralph-run` cycle
8. After each story, report progress and check for next eligible

---

## `parallel` — Generate Parallel Session Commands

```
/ralph-batch parallel [--sprint V3-1]
```

Identifies stories that can run in parallel (no mutual dependencies) and generates commands for separate Claude Code sessions.

**This command does NOT run stories** — it outputs commands for the user to run in parallel terminals.

### Steps
1. Read `prd.json`
2. Find all eligible stories
3. Group into parallelizable sets (stories with no deps on each other)
4. Output:
```
Ralph Batch: Parallel Opportunities
═══════════════════════════════════

Parallel Set 1 (after E30-S1 completes):
  Terminal 1: claude -p "Run /ralph-run E30-S2"
  Terminal 2: claude -p "Run /ralph-run E30-S3"
  Terminal 3: claude -p "Run /ralph-run E30-S4"
  Terminal 4: claude -p "Run /ralph-run E30-S8"

Parallel Set 2 (after E30-S2, S3 complete):
  Terminal 1: claude -p "Run /ralph-run E30-S5"
  Terminal 2: claude -p "Run /ralph-run E30-S6"

Note: Each terminal needs its own Claude Code session.
Use /ralph-status to verify completion before starting next set.
```

---

## `sprint` — Run All Stories in a Sprint

```
/ralph-batch sprint V3-1
```

Convenience wrapper: runs all stories in the specified sprint in dependency order.

### Steps
1. Read `prd.json`
2. Filter stories by sprint
3. Topological sort by dependencies
4. Show plan with dependency order
5. Run each story sequentially via `/ralph-run`
6. Report sprint completion when done

```
Ralph Batch: Sprint V3-1
Stories (dependency order):
1. E30-S1 — SF Schema Config Loader (5 SP) [no deps]
2. E30-S2 — Building Record Model (5 SP) [after S1]
3. E30-S3 — SF Field Aliases (3 SP) [after S1]
4. E30-S4 — Dependent Picklist Engine (5 SP) [after S1]
5. E30-S8 — Ollama Config (2 SP) [after S1]
6. E30-S5 — Additive Migration Framework (3 SP) [after S2, S3]
7. E30-S6 — BAR->SF Vocabulary (2 SP) [after S3]

Note: S2, S3, S4, S8 can run in parallel after S1.
Sequential mode will run them one at a time.

Total: 25 SP across 7 stories
Proceed? [y/n]
```
