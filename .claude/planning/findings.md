# Findings: Ralph Loop Redesign Research

## Research Date: 2026-02-22

## Key Findings

### 1. Branch Strategy
- Current system creates feature branches per story, merges to main with --no-ff
- User wants direct-to-main commits for cleaner history
- Ralph playbook confirms this is valid: "eventual consistency through iteration"
- Safety checkpoints (every 10 iterations) provide rollback points

### 2. Hook Exit 2 Strategy
- Exit 2 is the ONLY way to block tool calls in Claude Code hooks
- Stop hooks with exit 2 prevent Claude from finishing prematurely (critical for Ralph loops)
- MUST check `stop_hook_active` to prevent infinite loops
- TaskCompleted hooks can enforce quality gates before marking tasks done
- PreToolUse hooks can block writes to protected files

### 3. Agent Teams vs Sub-Agents
- Agent Teams (TeamCreate) are heavyweight — persistent agents consuming tokens
- Task tool sub-agents are lightweight — spawn, execute, return
- For most stories, a single agent + Task tool delegation is sufficient
- Teams only needed for complex stories requiring ongoing coordination
- User wants minimal agents to conserve resources

### 4. Model Choice
- User's Sonnet usage is capped (Max plan, 100 more hours)
- Opus recommended for all agents in this session
- Hard rule: OAuth only (env -u ANTHROPIC_API_KEY)
- ralph_loop.sh already has the env -u pattern

### 5. Story Priority Reordering
- Current task_plan.md order: E9-S3, E16-S1, E16-S3, E10-S1, E2-S8, E5-S3, E1-S23, E2-S11
- Optimal order (small/frontend-first): E2-S8, E10-S1, E16-S3, E2-S11, E1-S23, E9-S3, E5-S3, E16-S1
- Rationale: build momentum with quick wins, save complex stories for later

### 6. Existing Ralph Infrastructure is Good
- ralph_loop.sh: solid circuit breaker, safety checkpoints, infra error detection
- ralph_sprint.sh: good lifecycle (INIT→DEV→REVIEW→TEST→FIX→COMPLETE)
- PROMPT files: well-structured, just need path fixes and model updates
- Only major change: remove branch logic, add hooks, fix paths

### 7. BMAD Integration Points
- Story files need: Status update to "done", Dev Agent Record filled
- Sprint-status.yaml needs: story status changed to "done"
- docs-specialist agent handles documentation updates
- /story-complete command handles verification + finalization

## Sources
- Full research documented in `docs/ralph-research/`
