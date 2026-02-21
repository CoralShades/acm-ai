# ACM-AI Workflow Guide

How to use the Ralph Loop + Agent Teams to implement stories autonomously.

---

## Daily Workflow

### Option A: Local Ralph Loop (recommended for focused story work)

```bash
# 1. Initialize Ralph for a story
/ralph-init e1-s13-fix-page-reference-tracking.md

# 2. Run the loop
.ralph/ralph_loop.sh

# 3. When done, verify and finalize
/story-complete
```

### Option B: Interactive Session (for exploration, debugging, multi-story work)

```bash
# Start Claude Code normally
claude

# Check sprint status
/sprint-status

# Work interactively — the orchestrator and specialists are available
# via the Task tool for delegation
```

### Option C: Remote Web Session

Use Claude Code on the web for cloud-based development. The session-start hook auto-installs dependencies and starts SurrealDB.

---

## How /ralph-init Works

When you run `/ralph-init [story-file]`:

1. **Reads the story** from `_bmad-output/implementation-artifacts/`
2. **Parses acceptance criteria** into a task checklist
3. **Generates `.ralph/@fix_plan.md`** with:
   - Story title and source path
   - Checkbox list of all ACs as tasks
   - Completion criteria (all checked + tests passing)
4. **Creates a feature branch**: `feature/story-{id}-{slug}`
5. **Reports** initialization summary with next steps

If no argument is given, it picks the top story from `task_plan.md`.

---

## Orchestrator Routing

The orchestrator reads each story's file changes and routes to the right specialist:

### Routing Examples (ACM-AI specific)

| Story touches... | Routed to | Example |
|-------------------|-----------|---------|
| `api/routers/acm.py` | backend-specialist | New ACM endpoint |
| `open_notebook/extractors/` | backend-specialist | Extraction pipeline change |
| `open_notebook/graphs/` | backend-specialist | LangGraph workflow update |
| `migrations/*.surrealql` | backend-specialist | Schema migration |
| `commands/acm_commands.py` | backend-specialist | Background job change |
| `frontend/src/components/acm/` | frontend-specialist | ACM Grid UI update |
| `frontend/src/app/(dashboard)/` | frontend-specialist | New page or layout |
| `frontend/src/stores/` | frontend-specialist | State management |
| `tests/test_acm_*.py` | qa-specialist | Test coverage verification |
| `docs/`, `README.md` | docs-specialist | Documentation update |

### Mixed stories (backend + frontend)
The orchestrator delegates sequentially: backend first (API changes), then frontend (consumes the API). This prevents frontend work from depending on unimplemented endpoints.

---

## Handling a BLOCKED Loop

When the Ralph loop outputs `BLOCKED`, it means the agent hit an issue it cannot resolve autonomously.

### Diagnosis

```bash
# Check the last iteration log
cat .ralph/logs/iteration-N.md

# Check the metrics log
cat .ralph/logs/metrics.log

# Look for the BLOCKED reason
grep "BLOCKED" .ralph/logs/iteration-*.md
```

### Common Blockers and Fixes

| Blocker | Fix |
|---------|-----|
| Missing dependency | `uv add <package>` or `cd frontend && npm install <package>` |
| Ambiguous AC | Clarify the acceptance criterion in the story file, re-run |
| Test infrastructure missing | Add test fixtures to `tests/conftest.py` |
| Schema migration conflict | Resolve in `migrations/`, re-run |
| External API unavailable | Mock the dependency or skip that AC |

### Resuming After Fix

```bash
# Fix the blocker manually, then restart the loop
.ralph/ralph_loop.sh
```

The loop reads `@fix_plan.md` each iteration, so it picks up where it left off (skips checked tasks).

---

## Running Parallel Stories

For independent stories that don't touch the same files:

```bash
# Terminal 1: Backend story
/ralph-init e1-s13-fix-page-reference-tracking.md
.ralph/ralph_loop.sh

# Terminal 2: Frontend story (in a separate worktree or session)
git worktree add ../acm-ai-lane-b feature/story-e8-s11-grid-polish
cd ../acm-ai-lane-b
/ralph-init e8-s11-acm-register-grid-ui-polish.md
.ralph/ralph_loop.sh
```

Merge back to main when both complete.

---

## Sprint Ceremonies

### Picking the Next Story

```bash
# See what's available
/sprint-status

# Initialize the top priority story
/ralph-init   # No argument = picks from task_plan.md
```

### Updating Status

Sprint status is automatically updated by:
- `/sprint-status` — regenerates the board from story files
- `/story-complete` — marks the current story as done
- The orchestrator — updates `progress.md` after each delegation

### Merging Completed Branches

```bash
# After /story-complete passes
git checkout main
git merge --no-ff feature/story-e1-s13-fix-page-reference-tracking
git push origin main

# Or create a PR
gh pr create --title "E1-S13: Fix Page Reference Tracking" --body "All ACs verified."
```

---

## Code Review Flow

Use a second Claude session to review a feature branch:

```bash
# Session 1: Implementation
/ralph-init e1-s13-fix-page-reference-tracking.md
.ralph/ralph_loop.sh

# Session 2: Review (after loop completes)
git checkout feature/story-e1-s13-fix-page-reference-tracking
# Use /bmad:bmm:workflows:code-review for adversarial review
```

The code review workflow checks architecture compliance, test coverage, security, and performance.
