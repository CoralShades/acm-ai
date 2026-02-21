# Ralph Loop Variants Comparison

Compiled 2026-02-22 from 5 Ralph implementations.

## 1. snarktank/ralph (Original)

**URL**: https://github.com/snarktank/ralph

**Architecture**: Bash loop that spawns fresh Claude/Amp instances per iteration.

**Key Patterns**:
- Fresh context per iteration (no memory pollution)
- State persistence via `prd.json` (task status) + `progress.txt` (learnings) + git history
- Story selection: pick highest-priority item where `passes: false`
- Completion signal: `<promise>COMPLETE</promise>` when all stories `passes: true`
- `AGENTS.md` as institutional memory — updated after each iteration with patterns/gotchas

**Quality Gates**: Typecheck + test suites must pass before commit. Broken gates undermine entire approach.

**Story Sizing**: Must fit within one context window. "Add a database column" = good. "Build entire dashboard" = bad.

**Frontend Verification**: UI stories require "Verify in browser using dev-browser skill" in acceptance criteria.

---

## 2. frankbria/ralph-claude-code

**URL**: https://github.com/frankbria/ralph-claude-code

**Architecture**: Adapted Ralph for Claude Code CLI with intelligent exit detection.

**Key Innovations**:
- **Dual-condition exit gate**: Requires BOTH `completion_indicators >= 2` AND `EXIT_SIGNAL: true` in RALPH_STATUS JSON block
- **Three-layer API limit detection**: timeout guard → structural JSON → filtered text
- **Session continuity**: `--resume <session_id>` flag maintains context across iterations
- **Circuit breaker**: OPEN → HALF_OPEN → CLOSED with 30-min cooldown
- **Live monitoring**: `ralph --monitor` for tmux dashboard (iteration count, progress, rate limit countdown)

**Setup Paths**:
- `ralph-enable` (interactive wizard): auto-detects project type, imports tasks
- `ralph-import` (format conversion): transforms existing PRDs into `.ralph/` structure
- `ralph-setup` (blank slate): creates bare project for manual configuration

**Configuration Hierarchy**:
```
PROMPT.md (high-level goals)
  → specs/ (detailed requirements)
  → fix_plan.md (specific tasks)
  → AGENT.md (build/test commands)
```

**Unattended Mode**: On 5-hour API limit timeout (exit code 124), auto-waits rather than exiting.

---

## 3. ClaytonFarr/ralph-playbook

**URL**: https://github.com/ClaytonFarr/ralph-playbook

**Architecture**: Methodology guide focused on production reliability patterns.

**Core Principles**:

### Acceptance-Driven Backpressure
Engineer "reject invalid/unacceptable work" mechanisms:
1. Programmatic checks (tests, linting, type checking, builds) — hard failures
2. LLM-as-judge tests for subjective criteria when automation isn't feasible
3. Force agent to fix issues before committing (no error accumulation)

### Context Window Discipline
~176K usable tokens from 200K budget, only 40-60% in "smart zone".
Strategy: "Run one task per loop iteration with fresh context."

### Two-Mode Operation
- **Planning mode**: Gap analysis only, generates/updates `IMPLEMENTATION_PLAN.md`
- **Building mode**: Executes from plan, validates, commits, pushes

### Subagent Deployment Strategy
- Use parallel subagents (up to 500) for reads/searches across codebase
- Reserve exactly one subagent for build/test execution (prevent race conditions)
- Sonnet for volume work, Opus for architectural reasoning

### Plan Staleness Detection
Regenerate plan when Ralph goes off-track, duplicates work, or plan feels stale. Low cost (one planning iteration) justifies frequent refreshes.

### Sandbox Security
"It's not if it gets popped, it's when—what's the blast radius?"
Run with `--dangerously-skip-permissions`, make sandbox your only security boundary.

### Observability
Start with empty `AGENTS.md`. Watch initial loops, spot failure patterns, add guardrails reactively. "Tune it like a guitar."

---

## 4. vercel-labs/ralph-loop-agent

**URL**: https://github.com/vercel-labs/ralph-loop-agent

**Architecture**: Vercel AI SDK wrapper with nested loop structure.

**Two-Loop Design**:
```
┌─ Ralph Loop (outer) ────────────────┐
│ ┌─ AI SDK Tool Loop (inner) ──────┐ │
│ │ LLM ↔ tools ↔ LLM ↔ tools...  │ │
│ └─────────────────────────────────┘ │
│ ↓                                   │
│ verifyCompletion check              │
│ ↓                                   │
│ No? Inject feedback → iterate       │
│ Yes? Return result                  │
└─────────────────────────────────────┘
```

**Key Innovation — verifyCompletion**:
```typescript
verifyCompletion: async ({ result, iteration, allResults, originalPrompt }) => ({
  complete: boolean,
  reason?: string  // Feedback injected into next iteration
})
```
Return `{ complete: false, reason: "specific feedback" }` to guide next iteration.

**Composable Stop Conditions**:
- `iterationCountIs(n)` — max attempts
- `tokenCountIs(n)` — token budget
- `costIs(maxCost, rates?)` — dollar limits
- Array composition: stop when ANY condition triggers

**Lifecycle Hooks**:
- `onIterationStart` / `onIterationEnd` — logging, monitoring, conditional abort

---

## 5. LarsCowe/bmalph (BMAD + Ralph Unified)

**URL**: https://github.com/LarsCowe/bmalph

**Architecture**: Single tool managing entire SDLC lifecycle.

**Workflow**:
1. `/analyst` → Product brief (Phase 1)
2. `/pm` → PRD (Phase 2)
3. `/architect` → Architecture + stories (Phase 3)
4. `/bmalph-implement` → Auto-generates `@fix_plan.md`, transitions to Ralph (Phase 4)
5. `bash .ralph/ralph_loop.sh` → Autonomous implementation

**Multi-Epic Pattern**:
```
BMAD (Epic 1) → /bmalph-implement → Ralph works on Epic 1
       ↓
BMAD (add Epic 2) → /bmalph-implement → Ralph sees changes + picks up Epic 2
```

Completed stories preserved in fix plan via smart merge.

---

## Cross-Cutting Best Practices

### What ALL Variants Agree On

1. **Fresh context per iteration** — prevents context pollution
2. **State on disk, not in memory** — fix_plan.md/prd.json persists between iterations
3. **Quality gates are non-negotiable** — tests must pass before commit
4. **Explicit completion signals** — `<promise>COMPLETE</promise>` pattern
5. **Circuit breakers** — max iterations, no-progress detection, infrastructure error detection
6. **Git as recovery mechanism** — commits create rollback points
7. **Story sizing matters** — fit within one context window or fail

### Key Differentiators

| Feature | snarktank | frankbria | playbook | vercel-labs | bmalph |
|---------|-----------|-----------|----------|-------------|--------|
| Dual exit gate | No | Yes | No | Via verifyCompletion | No |
| API limit handling | Basic | Three-layer | N/A | costIs() | Basic |
| Session resume | No | Yes | N/A | N/A | No |
| Monitoring dashboard | No | Yes (tmux) | N/A | Lifecycle hooks | No |
| BMAD integration | No | No | No | No | Yes |
| Subagent strategy | No | No | Detailed | Built-in | No |
| LLM-as-judge | No | No | Yes | Via verify | No |
