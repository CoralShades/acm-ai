# Ralph Concepts & Vocabulary

> Audience: AI agents. Terse reference. Read this before any other Ralph doc.

## Glossary

| Term | Definition |
|------|-----------|
| **Ralph Loop** | Bash loop spawning fresh AI agent instances per iteration until all tasks complete or blocked |
| **prd.json** | Machine-readable project state: stories array, dependency graph, gates, progress tracking |
| **@fix_plan.md** | Per-iteration task checklist derived from story acceptance criteria. Checkbox format: `- [ ]` / `- [x]` |
| **progress.txt** | Institutional memory file updated across iterations with patterns, gotchas, codebase learnings |
| **AGENTS.md** | Alternative name for progress.txt in some Ralph variants |
| **Completion Promise** | Signal `<promise>COMPLETE</promise>` — agent outputs when ALL tasks verified done |
| **Blocked Signal** | Signal `<promise>BLOCKED</promise>: [reason]` — agent outputs when human intervention needed |
| **Gate** | Dependency checkpoint blocking downstream stories until a trigger story completes and unlocks it |
| **Circuit Breaker** | Safety mechanism: halts loop after N consecutive iterations with no task progress |
| **Backpressure** | Mechanisms rejecting bad work, forcing correction before proceeding (tests, lint, build gates) |
| **Safety Checkpoint** | Periodic `git add -u && git commit` during long loops creating rollback points |
| **Story Sizing** | Constraint: each story must fit within one context window (~60-80K usable tokens) |
| **Fresh Context** | Each iteration starts empty. State persists ONLY via files on disk and git history |
| **Stop Hook** | Claude Code hook blocking session exit, enabling in-session loops (Wiggum pattern) |
| **Quality Gate** | Automated check (lint, test, build) that must pass before task completion or commit |
| **Sprint Runner** | Orchestration script processing multiple stories sequentially through the full BMAD cycle |

## Completion Protocol

### Signal Strings
```
<promise>COMPLETE</promise>           # All tasks done, verified
<promise>BLOCKED</promise>: reason    # Cannot proceed, needs human
```

### Rules
- XML wrapper `<promise>` prevents false positives from natural language
- Agent outputs COMPLETE only after ALL acceptance criteria pass verification
- Agent outputs BLOCKED with specific reason when stuck after max retries
- Both signals are detected via `grep -qF` on iteration output logs
- NEVER output a false COMPLETE to escape the loop

### Detection
```bash
# In bash loop:
if grep -qF '<promise>COMPLETE</promise>' "$iteration_log"; then exit 0; fi
if grep -qF '<promise>BLOCKED</promise>' "$iteration_log"; then exit 1; fi
```

## State-on-Disk

### Why
Fresh context per iteration means no in-memory state survives between iterations. ALL persistent state lives in files.

### Core State Files

| File | Purpose | Updated By |
|------|---------|------------|
| `@fix_plan.md` | Task progress — checkbox list | Agent (checks off tasks) |
| `prd.json` | Project state — stories, deps, gates | Agent + slash commands |
| `metrics.log` | Timing, events, iteration tracking | Bash loop script |
| `progress.txt` | Cross-iteration learnings, patterns | Agent (appends insights) |

### Recovery
- Git history serves as recovery mechanism and audit trail
- Safety checkpoints create rollback points every N iterations
- `git log --oneline` shows iteration-by-iteration progress

## Exit Code Contract

| Code | Name | Meaning | Triggered By |
|------|------|---------|-------------|
| 0 | Success | COMPLETE signal detected | All tasks done |
| 1 | Blocked | BLOCKED signal or circuit breaker | Stuck or no-progress |
| 2 | Max iterations | Loop exhausted without completion | Hit iteration limit |
| 3 | Setup error | Missing files or bad configuration | Preflight check failure |
| 4 | Infrastructure | Credits, auth, rate limit, network | Fatal error detection |

## Cross-Variant Consensus

Seven principles ALL Ralph implementations agree on:

1. **Fresh context per iteration** — prevents context pollution, each iteration reads state from disk
2. **State on disk, not in memory** — @fix_plan.md / prd.json persists between iterations
3. **Quality gates are non-negotiable** — tests must pass before any commit
4. **Explicit completion signals** — `<promise>COMPLETE</promise>` pattern avoids false detection
5. **Circuit breakers** — max iterations + no-progress detection + infrastructure error detection
6. **Git as recovery mechanism** — commits create rollback points for safe experimentation
7. **Story sizing matters** — story must fit within one context window or it will fail

## Key Variants

| Variant | Key Innovation |
|---------|---------------|
| snarktank/ralph | Original pattern. Fresh context, prd.json state, branch archiving |
| frankbria/ralph-claude-code | Dual exit gate, three-layer API limit detection, session resume |
| ClaytonFarr/ralph-playbook | Acceptance-driven backpressure, LLM-as-judge, plan staleness |
| vercel-labs/ralph-loop-agent | TypeScript SDK wrapper, composable stop conditions, verifyCompletion |
| LarsCowe/bmalph | Unified BMAD + Ralph, planning-to-implementation transition |
