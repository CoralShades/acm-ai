# ACM-AI Ralph Reference

This document is the ACM-AI project-specific reference for Ralph. It absorbs all prior research files and documents the decisions, configuration, and patterns specific to this repository.

---

## ACM-AI Configuration

### Key File Paths

| Purpose | Path |
|---|---|
| Loop script | `.ralph/ralph_loop.sh` |
| Slash commands | `.claude/commands/ralph-*.md` |
| Agent definitions | `.claude/agents/ralph-*.md` |
| Hook scripts | `.claude/hooks/*.sh` |
| Project state | `prd.json` |
| Ralph config | `ralph-config.json` |
| Progress tracker | `docs/sprint-artifacts/v3-sprint-plan.md` |

### prd.json Summary

The V3 `prd.json` contains:
- **33 stories** covering the full V3 implementation sprint
- **4 gates** controlling story eligibility

| Gate | Trigger Condition | Blocks |
|---|---|---|
| `SCHEMA_FREEZE` | All schema migration stories DONE | Extraction stories |
| `EXTRACTION_COMPLETE` | All extraction stories DONE | AI pipeline stories |
| `AI_COMPLETE` | All AI pipeline stories DONE | UI feature stories |
| `UI_COMPLETE` | All UI stories DONE | Final integration |

### ralph-config.json

Current session configuration:

```json
{
  "agents": {
    "backend-specialist": "opus",
    "frontend-specialist": "opus",
    "qa-specialist": "opus",
    "docs-specialist": "sonnet"
  },
  "loop": {
    "max_iterations": 40,
    "completion_promise": "COMPLETE",
    "blocked_signal": "BLOCKED"
  }
}
```

All implementation agents use `opus` (Max plan, better quality for complex domain). Documentation agent uses `sonnet` (adequate for structured writing, lower cost).

### Services

| Service | Port | Start Command |
|---|---|---|
| SurrealDB | 8000 | `docker compose up -d surrealdb` |
| FastAPI | 5055 | `uv run run_api.py` |
| Next.js | 8502 | `cd frontend && npm run dev` |
| Worker | — | `uv run run_worker.py --import-modules commands` |

### Test Commands

| Layer | Command |
|---|---|
| Backend unit | `uv run pytest tests/ -x` |
| Backend with coverage | `uv run pytest --cov=open_notebook` |
| Frontend lint | `cd frontend && npm run lint` |
| Frontend build | `cd frontend && npm run build` |
| Frontend E2E | `npx playwright test` |

### Lint Commands

| Layer | Command | Auto-fix |
|---|---|---|
| Python | `uv run ruff check .` | `uv run ruff check . --fix` |
| Python format | `uv run ruff format .` | (formats in place) |
| Type check | `uv run mypy .` | (manual) |
| Frontend | `cd frontend && npm run lint` | `npm run lint -- --fix` |

---

## Design Decisions

### 1. Direct-to-Main Branch Strategy

All Ralph work commits directly to `main` (or the active sprint branch, currently `ACMV3`). No feature branches are created per story.

**Rationale:**
- Simpler history — each commit is a clear unit of work
- No merge conflicts between parallel story branches
- Safety checkpoints via `git reset --soft HEAD~N` replace branch-based rollback
- Stories are sequential (gated), reducing the need for parallel branches

**Trade-off:** Requires discipline about commit quality. The pre-commit hook enforces lint and build quality before each commit (with `wip:` bypass for checkpoints).

### 2. Opus for All Implementation Agents

`ralph-config.json` sets all implementation agents to `claude-opus-4-6`.

**Rationale:**
- Max plan subscription removes per-token billing anxiety
- ACM domain is specialized — Opus makes fewer architectural mistakes
- Fewer iterations needed per story → lower effective cost despite higher per-call cost
- Complex domain (asbestos compliance, SurrealDB, LangGraph) benefits from deeper reasoning

**Exception:** Docs agent uses Sonnet — documentation writing does not require deep domain reasoning.

### 3. Minimal Agent Teams

Prefer `Task` tool subagents over `TeamCreate` for multi-step work.

**Rationale:**
- `TeamCreate` adds coordination overhead and uses more context
- Sequential subagent calls (via Task tool) are cheaper and easier to debug
- The full sprint team pattern is reserved for stories that genuinely require parallel execution (rare)
- CLAUDE.md rule: "Prefer Task tool subagents over TeamCreate"

**When to use TeamCreate:** Only when a story has clearly parallel work streams that cannot be serialized without losing significant time (e.g., backend and frontend implementation of the same feature simultaneously).

### 4. OAuth-Only Authentication

Ralph is configured to run with OAuth (Claude Max subscription) rather than API key billing.

```bash
# The ralph_loop.sh runner uses:
env -u ANTHROPIC_API_KEY claude --model claude-opus-4-6 [args]
```

**Rationale:**
- Max plan has higher rate limits — avoids 429 errors during long loops
- No per-token billing — budget is predictable (monthly subscription)
- API key (`ANTHROPIC_API_KEY`) overrides OAuth; removing it forces OAuth

### 5. Full Protection Hooks

All four hook types are configured:

| Hook | Script | Purpose |
|---|---|---|
| PreToolUse (Bash) | `ralph-gate-guard.sh` | Scope protection — blocks writes outside allowed paths |
| PostToolUse (Bash) | `ralph-progress.sh` | Progress tracking — logs tool use to `@fix_plan.md` |
| PreToolUse (Write) | `ralph-gate-guard.sh` | Same scope protection for file writes |
| Stop | `ralph-progress.sh` | Stop gate — checks COMPLETE/BLOCKED signal, updates prd.json |

### 6. Story Priority

When multiple stories are eligible (deps met, gate open), the sprint runner selects in this order:

1. Frontend-only stories (highest completion probability — no DB migrations, no schema risk)
2. Backend stories with complete specs (low ambiguity)
3. Integration stories (require both backend and frontend — highest risk, run last)

**Rationale:** Small frontend-only stories have the highest probability of clean single-session completion. Running them first builds momentum and reduces the risk of the first story being a blocker.

---

## Absorbed Research

### Variants Comparison

*Source: `docs/ralph-research/ralph-variants-comparison.md` (superseded)*

Five Ralph implementations were compared during design:

| Feature | snarktank | frankbria | playbook | vercel-labs | bmalph |
|---|---|---|---|---|---|
| Dual exit gate | No | Yes | No | No | No |
| API limit handling | Basic retry | Three-layer | Basic | `costIs()` guard | Basic |
| Session resume | No | Yes (state.json) | No | No | No |
| BMAD integration | No | No | No | No | Yes |
| Subagent strategy | None | Task tool | Detailed routing | None | None |
| LLM-as-judge | No | No | Yes | Yes (verify) | No |

**Key takeaways:**
- `frankbria` is the closest reference implementation to ACM-AI's Ralph — dual exit gate and session resume are both implemented
- `playbook` subagent routing table is adopted for the ACM-AI routing rules (see CLAUDE.md)
- `vercel-labs` `costIs()` pattern is not adopted — Max plan removes billing pressure
- `bmalph` BMAD integration is extended — ACM-AI has deeper BMAD integration than the original

### Quality Gates and Backpressure

*Source: `docs/ralph-research/quality-gates-and-backpressure.md` (superseded)*

Three-level gate hierarchy:

**Level 1: Hard Gates** — must pass before commit is allowed
- Python lint: `ruff check .`
- Python format: `ruff format .`
- Type check: `mypy .` (advisory — not blocking in pre-commit)
- Frontend lint: `npm run lint`
- Frontend build: `npm run build`
- Backend tests: `pytest tests/ -x`

**Level 2: Soft Gates** — advisory, tracked but not blocking
- Test coverage threshold (80% target)
- Frontend bundle size (advisory warning if >500KB increase)
- API response time (monitored, not enforced in CI)

**Level 3: LLM-as-Judge** — subjective quality review
- Code review: `PROMPT_REVIEW.md` instructs agent to self-review before marking COMPLETE
- UX verification: Browser snapshot checked against acceptance criteria
- Architectural alignment: Agent checks new code against `docs/development/architecture.md`

**Commit gate pattern:**
```
implement → ruff fix → pytest → npm build → check off story task → commit
```

The pre-commit hook enforces Level 1. Levels 2 and 3 are enforced by the agent's PROMPT instructions.

### Agent Teams Patterns

*Source: `docs/ralph-research/agent-teams-patterns.md` (superseded)*

Three team configurations evaluated:

**Option A: Single-Agent (No Teams)**
- One Claude session handles all work
- Lowest cost, simplest debugging
- Context window is the only limit
- Best for: stories under ~500 LOC of change

**Option B: Lead + Specialist (Mixed Stories)**
- Lead agent delegates subtasks via Task tool
- Specialists are short-lived subagents (one task, then done)
- Moderate cost, good for complex stories
- Best for: stories requiring both DB migration and frontend component

**Option C: Full Sprint Team (Multi-Story)**
- `TeamCreate` with persistent specialist agents
- Highest cost, complex coordination
- Only justified for genuinely parallel work streams
- Best for: accelerating a sprint with 5+ independent stories

**Cost control rules:**
- Sequential > parallel whenever order permits
- Minimize team size — start with Option A, escalate only if needed
- Use `haiku` for simple/focused subagent tasks (test running, lint fixing)
- Use `sonnet` for lead agents and complex implementation tasks (in teams)
- Use `opus` for single-agent sessions only (not team members)

**Sweet spot for ACM-AI:** One lead agent (opus, single-agent Task tool call) + short-lived Task tool sub-agents (sonnet/haiku). `TeamCreate` is avoided except for the largest sprint stories.

### Loop Design

*Source: `docs/ralph-research/acm-ai-loop-design.md` (superseded)*

**6-phase story lifecycle:**

```
INIT → DEV → REVIEW → TEST → FIX → COMPLETE
```

| Phase | Description | Exit Condition |
|---|---|---|
| INIT | Load context, read story spec, plan approach | Plan documented in `@fix_plan.md` |
| DEV | Implement changes, create files, update DB | All task items checked off |
| REVIEW | Self-review against spec, run `PROMPT_REVIEW.md` | No review issues found |
| TEST | Run test suite, fix failures | All tests pass |
| FIX | Address any review or test issues | All issues resolved |
| COMPLETE | Commit, update prd.json, emit `<promise>COMPLETE</promise>` | Signal detected by Stop hook |

**Known issues fixed in ACM-AI loop design:**

| Issue | Root Cause | Fix Applied |
|---|---|---|
| Stale artifact paths | Loop referenced old `docs/ralph-PLAYBOOK.md` | Updated to `docs/ralph/` paths |
| YAML fragility | prd.json was originally YAML | Migrated to JSON (jq-parseable) |
| Branch logic | Loop tried to create feature branches | Removed — direct-to-main strategy |
| Orchestrator conflict | Multiple agents updating prd.json simultaneously | Sequential story execution enforced |

**Existing assets preserved:**

These files exist from prior Ralph sessions and are still active:

| File | Purpose |
|---|---|
| `.ralph/PROMPT.md` | Main agent instruction prompt |
| `.ralph/PROMPT_INIT.md` | First-iteration initialization prompt |
| `.ralph/PROMPT_REVIEW.md` | Self-review instructions |
| `docs/PROJECT_CONTEXT.md` | Project background for agents |

Do not overwrite these files when setting up a new Ralph session — they contain ACM-AI-specific instructions built up over multiple sessions.

---

## Subagent Routing Table

From CLAUDE.md — routes subagents to the appropriate specialist:

| File Pattern | Agent |
|---|---|
| `/api/**`, `/open_notebook/**`, `/migrations/**`, `/commands/**` | `backend-specialist` |
| `/frontend/**` | `frontend-specialist` |
| `/tests/**`, `/playwright-report/**` | `qa-specialist` |
| Story complete event | `docs-specialist` |

---

## Deprecation Notice

The following files are **superseded** by `docs/ralph/`. They are left in place for reference but should not be edited.

| Old File | Absorbed Into |
|---|---|
| `docs/ralph-PLAYBOOK.md` | `00-quickstart.md`, `06-bmad-integration.md`, `10-model-strategy.md`, `13-acm-ai-reference.md` |
| `docs/ralph-research/ralph-variants-comparison.md` | `13-acm-ai-reference.md` (Variants Comparison section) |
| `docs/ralph-research/quality-gates-and-backpressure.md` | `13-acm-ai-reference.md` (Quality Gates section) |
| `docs/ralph-research/agent-teams-patterns.md` | `13-acm-ai-reference.md` (Agent Teams section) |
| `docs/ralph-research/acm-ai-loop-design.md` | `13-acm-ai-reference.md` (Loop Design section) |

**Authoritative reference:** `docs/ralph/` (this directory)

When in doubt, prefer the `docs/ralph/` version. The research files may contain outdated assumptions from before the final ACM-AI loop design was settled.
