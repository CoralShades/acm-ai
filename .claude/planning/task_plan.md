# Task Plan: Ralph Loop Redesign for ACM-AI

## Goal
Redesign the Ralph autonomous coding loop to:
1. Commit directly to main (no feature branches)
2. Use Opus model for all agents (OAuth only, no API key)
3. Implement Claude Code hooks with exit 2 strategies for quality gates
4. Use Agent Teams with sub-agents for story implementation
5. Process all 8 ready-for-dev stories with BMAD workflow integration
6. Sequential commits with full details, pushed after each story

## Tasks

### Phase 1: Hook Scripts
- [ ] Create `.claude/hooks/ralph-stop-gate.sh` — Stop hook that prevents premature exit (checks @fix_plan.md for unchecked tasks, respects COMPLETE/BLOCKED signals)
- [ ] Create `.claude/hooks/task-quality-gate.sh` — TaskCompleted hook that blocks task completion unless lint+tests+build pass
- [ ] Create `.claude/hooks/scope-guard.sh` — PreToolUse hook that blocks Write/Edit to protected paths (migrations/*, .env, package-lock.json, uv.lock, docker-compose*.yml, .github/*)
- [ ] Create `.claude/hooks/pre-commit-gate.sh` — PreToolUse hook for Bash that blocks `git commit` unless verification suite passes

### Phase 2: Update Settings
- [ ] Update `.claude/settings.json` — Add new hooks (Stop, TaskCompleted, PreToolUse scope-guard, PreToolUse pre-commit-gate), add permission for `.ralph/ralph_sprint.sh`

### Phase 3: Update ralph_sprint.sh
- [ ] Remove all feature branch logic (create, checkout, merge, push branch, delete)
- [ ] Add direct-to-main commit strategy (commit per task, push after story)
- [ ] Change default model from sonnet to opus
- [ ] Ensure `env -u ANTHROPIC_API_KEY` on all claude invocations (OAuth only)
- [ ] Fix sprint-status.yaml update to use Claude agent instead of fragile sed
- [ ] Add BMAD story file update in COMPLETE phase (mark status done, fill Dev Agent Record)
- [ ] Reorder story list: small/frontend-first for momentum

### Phase 4: Update ralph_loop.sh
- [ ] Change default model to opus
- [ ] Ensure `env -u ANTHROPIC_API_KEY` on all claude invocations
- [ ] Keep existing: circuit breaker, safety checkpoints, infrastructure error detection

### Phase 5: Update Prompts
- [ ] Update `PROMPT.md` — Add agent team instructions, sub-agent delegation patterns, main-branch commit strategy
- [ ] Update `PROMPT_INIT.md` — Fix path from `_bmad-output/implementation-artifacts/` to `docs/sprint-artifacts/`
- [ ] Update `PROMPT_REVIEW.md` — Review against main HEAD (no branch diff needed)
- [ ] Update `PROMPT_FIX.md` — Minor: ensure it works with main-branch strategy

### Phase 6: Update /ralph-init Command
- [ ] Fix path reference from `_bmad-output/implementation-artifacts/` to `docs/sprint-artifacts/`
- [ ] Remove feature branch creation (direct to main)
- [ ] Add model flag (default opus)

### Phase 7: Update task_plan.md
- [ ] Reorder P0 stories for optimal execution: E2-S8, E10-S1, E16-S3, E2-S11, E1-S23, E9-S3, E5-S3, E16-S1

### Phase 8: Verification
- [ ] Dry run: `.ralph/ralph_sprint.sh --dry-run` to verify story discovery and ordering
- [ ] Verify all hook scripts are executable
- [ ] Verify settings.json is valid JSON
- [ ] Verify all prompt files reference correct paths
