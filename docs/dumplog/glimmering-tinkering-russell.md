# Plan: Run E19/E20 Story Loop via BMAD Sub-Agents (No Bash Scripts)

## Context

The user wants to implement all 12 E19/E20 stories (created in today's party mode session) using Claude sub-agents following BMAD workflows — without touching the `.ralph/` bash loop scripts.

The project already has two purpose-built mechanisms for this:
1. **The Orchestrator agent** (`.claude/agents/orchestrator.md`) — a pure Claude coordinator that reads `sprint-status.yaml`, picks stories, and spawns Task tool sub-agents (backend, frontend, qa, docs specialists). Zero bash required.
2. **The BMAD dev-story workflow** (`/bmad-bmm-dev-story`) — a single-agent 10-step story implementation loop per story.

The user's request matches **Option A (Orchestrator)** — a multi-story autonomous loop triggered from this chat.

---

## Prerequisite: Mark Stories Ready-for-Dev

Stories are currently `backlog` in `sprint-status.yaml`. The orchestrator and dev-story both pick stories from the first `ready-for-dev` entry. We need to change **E19-S1 only** to `ready-for-dev` (all others stay `backlog`) — the orchestrator advances them one at a time after each story completes.

**File to edit:** `docs/sprint-artifacts/sprint-status.yaml`

Change this single line:
```yaml
# BEFORE
e19-s1-migration-32-review-status: backlog

# AFTER
e19-s1-migration-32-review-status: ready-for-dev
```

---

## Recommended Approach: Orchestrator Agent (Option A)

### How it works

The orchestrator (`.claude/agents/orchestrator.md`) is already wired for this pattern:
1. Reads `docs/sprint-artifacts/sprint-status.yaml` for the next `ready-for-dev` story
2. Reads the story file (e.g. `e19-s1-migration-32-review-status.md`)
3. Determines file scope — routes to `backend-specialist`, `frontend-specialist`, `qa-specialist`, or `docs-specialist` via the `Task` tool
4. Collects results from specialists
5. Updates `progress.md` and story status
6. Signals `COMPLETE` or `BLOCKED`

After E19-S1 finishes, the orchestrator marks it `done`, then the **next** story must be flipped to `ready-for-dev` for the next run. You can either do this manually or give the orchestrator permission to advance them automatically.

### Trigger (just paste this into the chat)

```
Implement all E19 and E20 stories in sequential order using the orchestrator pattern.

Implementation order:
  E19: S1 → S2 → S3 → S4 → S5 → S6 → S7 (then S8 as P1 only after S7 done)
  E20: S1 → S2 → S3 → S4

Story files: docs/sprint-artifacts/e19-s{N}-*.md and docs/sprint-artifacts/e20-s{N}-*.md
Sprint status: docs/sprint-artifacts/sprint-status.yaml
Implementation prompts: docs/sprint-artifacts/e19-e20-implementation-prompts.md

Rules:
- Run ONE story at a time (sequential, not parallel — E19-S1 must be done before S2)
- For each story: read the story file, delegate to backend-specialist / frontend-specialist / qa-specialist per file scope
- Backend stories (migrations, api/, open_notebook/): delegate to backend-specialist
- Frontend stories (frontend/): delegate to frontend-specialist
- Mixed stories: backend-specialist first, then frontend-specialist
- After each story: run full verification (ruff check . + pytest + cd frontend && npm run lint && npm run build)
- Mark story done in sprint-status.yaml before moving to next
- E20-S4 MUST NOT run a real PDF extraction until E20-S1+S2+S3 unit tests all pass
- Follow cost awareness: no real extractions during unit test development

⚠️ DESTRUCTIVE: E19-S1 (Migration 032) deletes all acm_record rows. Confirm before executing.

Signal <promise>COMPLETE</promise> when all 12 stories are done.
Signal <promise>BLOCKED</promise>: [reason] if stuck.
```

---

## Alternative: BMAD dev-story Per Story (Option B — More Control)

Use this if you want to review each story before the next one starts:

```
# For each story, in a new chat turn:
/bmad-bmm-dev-story docs/sprint-artifacts/e19-s1-migration-32-review-status.md
```

The 10-step BMAD workflow handles implementation, tests, lint, and marks the story `review` when done. After you've reviewed the changes, flip the story to `done` in sprint-status.yaml and mark the next story `ready-for-dev`, then run `/bmad-bmm-dev-story` again.

---

## Step-by-Step Execution Plan

### Step 1 — Edit sprint-status.yaml (1 line change)
**File:** `docs/sprint-artifacts/sprint-status.yaml`
Change `e19-s1-migration-32-review-status: backlog` → `ready-for-dev`

### Step 2 — Trigger orchestrator
Paste the trigger prompt above into this chat (or `/bmad-bmm-dev-story` for per-story mode).

### Step 3 — Monitor and unblock
- Watch for `BLOCKED` signals — usually dependency gaps or ambiguous requirements
- For E19-S5/S6 (wizard steps): the orchestrator will need `building_data-schema.md` and `acm_data-schema.md` — already at `docs/samplePDF/` ✓
- For E20-S4: manually confirm "all E20 unit tests pass" before the orchestrator is permitted to run real PDF extraction

### Step 4 — After each story completes
The orchestrator should update `sprint-status.yaml` itself. If using Option B, manually advance the next story to `ready-for-dev`.

---

## Critical Files

| File | Role |
|------|------|
| `.claude/agents/orchestrator.md` | The orchestrator agent definition — reads stories, spawns Task sub-agents |
| `.claude/agents/backend-specialist.md` | Backend implementation agent (api/, open_notebook/, migrations/) |
| `.claude/agents/frontend-specialist.md` | Frontend implementation agent (frontend/) |
| `.claude/agents/qa-specialist.md` | Test verification agent |
| `docs/sprint-artifacts/sprint-status.yaml` | Shared state — stories transition backlog→ready-for-dev→in-progress→review→done |
| `docs/sprint-artifacts/e19-e20-implementation-prompts.md` | Per-story Claude prompts with cost-awareness injections |
| `docs/samplePDF/building_data-schema.md` | 21-field building schema (E19-S5 needs this) |
| `docs/samplePDF/acm_data-schema.md` | 29-field ACM schema (E19-S6 needs this) |

---

## Verification

Each story is verified before being marked done:
- `uv run ruff check .` — Python lint
- `uv run pytest tests/ -x` — Backend tests
- `cd frontend && npm run lint && npm run build` — Frontend checks
- Story's Acceptance Criteria checklist fully ticked
- E20-S4 only: one real extraction run on Broadmeadows PDF (32/32 target)
