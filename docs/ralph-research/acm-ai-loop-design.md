# ACM-AI Ralph Loop Design Decisions

Compiled 2026-02-22 during Ralph loop redesign.

## Design Decisions

### 1. Direct-to-Main Branch Strategy
**Decision**: Eliminate feature branches. All commits go directly to main.
**Rationale**:
- Cleaner git history with sequential conventional commits
- No merge conflicts from parallel branches
- Each task gets its own atomic commit
- Push to remote after each completed story (not after every commit)
- Safety checkpoints still create recovery points

### 2. Opus for All Agents (Session-Specific)
**Decision**: Use Opus model for all agent team members.
**Rationale**:
- Sonnet usage capped on Max plan
- Better quality for complex stories
- Fewer iterations needed = potentially lower total cost
- Hard rule: use Claude OAuth token, NOT Anthropic API key
- Implementation: `env -u ANTHROPIC_API_KEY claude --model opus`

### 3. Minimal Agent Teams
**Decision**: Keep agent teams to minimum. Use Task tool sub-agents sparingly.
**Rationale**:
- Each parallel agent consumes API tokens
- Sequential execution is more debuggable
- Most stories can be handled by a single agent with sub-agent delegation
- Use teams only for stories requiring true parallel backend+frontend work

### 4. All 8 Stories in One Run
**Decision**: Process all 8 ready-for-dev stories in priority order.
**Rationale**:
- Stories are independent (no cross-dependencies in ready-for-dev batch)
- Stop on 2 consecutive blocks (infra failure detection)
- Natural batching via sprint runner

### 5. Full Protection Hooks
**Decision**: Implement all hook guards:
- Block destructive git ops
- Block modifications outside story scope
- Block commits without passing tests
- Block task completion without AC verification

### 6. Story Priority Order
From task_plan.md P0 table + sprint-status.yaml analysis:

| Order | Story | Scope | Size | Why This Order |
|-------|-------|-------|------|----------------|
| 1 | E2-S8 | Frontend | S | Smallest, no deps, quick win |
| 2 | E10-S1 | Frontend | S | Small, no deps, quick UX improvement |
| 3 | E16-S3 | Frontend | S | Small, no deps, reusable EmptyState component |
| 4 | E2-S11 | Both | M | Strengthens data quality globally |
| 5 | E1-S23 | Backend | M | Critical extraction accuracy |
| 6 | E9-S3 | Both | M | Bulk operations (backend-heavy) |
| 7 | E5-S3 | Both | M | BAR template mgmt (blocks E5-S4) |
| 8 | E16-S1 | Both | L | Largest, dashboard + stats endpoint |

**Reordered from task_plan.md** to put small/frontend-only stories first (highest probability of clean completion, builds momentum).

## Known Issues to Fix

### 1. `/ralph-init` Stale Path
Current: reads from `_bmad-output/implementation-artifacts/`
Fix: read from `docs/sprint-artifacts/` (canonical location since commit e1d375f)

### 2. Sprint Status Update Fragility
Current: `sed -i` single-line regex on YAML
Fix: Use Claude agent to update YAML properly (or Python script)

### 3. Feature Branch Logic in ralph_sprint.sh
Current: creates branches, merges, pushes, deletes
Fix: remove all branch logic, commit directly to main

### 4. Orchestrator vs Sprint Runner Conflict
Current: two separate systems that don't coordinate
Fix: remove orchestrator-style story picking from ralph_sprint.sh, use Claude agent as orchestrator within the loop

### 5. Inner Loop Passes Full Prompt Every Iteration
This is correct by design (fresh context). No fix needed.

## Existing Assets to Preserve

- `PROMPT.md` — implementation rules (good, minor update needed)
- `PROMPT_INIT.md` — fix plan generation (good)
- `PROMPT_REVIEW.md` — adversarial review (good)
- `PROMPT_FIX.md` — fix phase (good)
- `PROJECT_CONTEXT.md` — project context (good)
- Circuit breaker logic in `ralph_loop.sh`
- Infrastructure error detection
- Safety checkpoint pattern

## Architecture: New vs Old

### Old Architecture
```
ralph_sprint.sh (bash)
  └── ralph_loop.sh (bash)
        └── claude -p "$(cat PROMPT.md)" (headless, no permissions)
```

### New Architecture
```
ralph_sprint.sh (bash) — orchestrates story lifecycle
  ├── Phase INIT: claude -p PROMPT_INIT.md → generates @fix_plan.md
  ├── Phase DEV: ralph_loop.sh → iterative implementation
  │     └── claude -p PROMPT.md (with agent teams when needed)
  ├── Phase REVIEW: claude -p PROMPT_REVIEW.md
  ├── Phase TEST: direct bash (ruff, pytest, npm lint, npm build)
  ├── Phase FIX: ralph_loop.sh --prompt PROMPT_FIX.md
  └── Phase COMPLETE: commit to main, push, update sprint-status.yaml
```

### Key Changes
1. No feature branches (direct to main)
2. Opus model throughout
3. OAuth-only (env -u ANTHROPIC_API_KEY)
4. Hook-based quality gates (exit 2 strategies)
5. Proper BMAD story file updates in COMPLETE phase
6. Sub-agent delegation via Task tool (not persistent teams)
