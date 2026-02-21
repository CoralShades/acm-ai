# Quality Gates and Backpressure Patterns

Compiled 2026-02-22 from ClaytonFarr/ralph-playbook and frankbria/ralph-claude-code.

## Backpressure Hierarchy

Backpressure = mechanisms that reject bad work and force correction before proceeding.

### Level 1: Hard Gates (Automated, Blocking)
These MUST pass before any commit:
- **Type checking**: `ruff check .` (Python), `npx tsc --noEmit` (TypeScript)
- **Linting**: `ruff check .`, `cd frontend && npm run lint`
- **Build**: `cd frontend && npm run build`
- **Unit tests**: `pytest tests/ -x`

### Level 2: Soft Gates (Automated, Advisory)
These inform but don't block:
- **Coverage reports**: Did coverage decrease?
- **Bundle size**: Did the frontend bundle grow unexpectedly?
- **Performance**: Did any benchmark regress?

### Level 3: LLM-as-Judge Gates
For subjective criteria that can't be automated:
- **Code review**: Use adversarial review prompt (PROMPT_REVIEW.md)
- **UX verification**: Use browser tools to verify visual changes
- **Architecture compliance**: Check patterns match CLAUDE.md conventions

## Implementation in Ralph Loop

### Per-Task Gate (After Each Task in @fix_plan.md)
```bash
# Run after implementing each task
ruff check .                        # Python lint
pytest tests/ -x                    # Backend tests
cd frontend && npm run lint         # Frontend lint
cd frontend && npm run build        # Frontend build
```
Only check off task AND commit if ALL pass.

### Per-Story Gate (After All Tasks Complete)
```bash
# Full suite before marking story done
ruff check .
pytest tests/ -x --cov=open_notebook
cd frontend && npm run lint
cd frontend && npm run build
# Optional: npx playwright test (E2E)
```

### Sprint-Level Gate (Between Stories)
- Verify main branch is clean
- Verify no regressions from previous story
- Check sprint-status.yaml is consistent

## Circuit Breaker Patterns

### No-Progress Detection
```
Track task count each iteration.
If same count for N consecutive iterations → BLOCKED.
Default N = 3.
```

### Infrastructure Error Detection
Scan logs for:
- "Credit balance is too low"
- "rate limit" / "rate_limit_error"
- "insufficient_quota"
- "Authentication failed" / "invalid_api_key"
- "Connection refused"
- "overloaded_error"

2 consecutive infra failures → sprint abort.

### Max Iteration Guard
Absolute cap prevents infinite loops:
- Per-task: 40 iterations
- Per-fix-phase: 10 iterations
- Per-story: 40 + 10 = 50 max iterations

### Safety Checkpoints
Every 10 iterations:
```bash
git add -u
git commit -m "chore(ralph): safety checkpoint iteration N"
```
Creates rollback points even during long-running tasks.

## Hook-Based Quality Gates

### TaskCompleted Hook (Claude Code)
```json
{
  "hooks": {
    "TaskCompleted": [{
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/task-quality-gate.sh"
      }]
    }]
  }
}
```

Exit 2 prevents task from being marked complete if tests fail.

### Stop Hook (Prevent Premature Exit)
```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/ralph-stop-gate.sh"
      }]
    }]
  }
}
```

Exit 2 forces Claude to continue if unchecked tasks remain.

### PreToolUse Hook (Scope Protection)
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/scope-guard.sh"
      }]
    }]
  }
}
```

Blocks writes to files outside story scope (protected paths).

## The Commit Gate Pattern

**Only commit when ALL gates pass:**

```
Task Implementation
    ↓
Run lint → FAIL? → Fix → Retry (max 3)
    ↓ PASS
Run tests → FAIL? → Fix → Retry (max 3)
    ↓ PASS
Run build → FAIL? → Fix → Retry (max 3)
    ↓ PASS
Check off task in @fix_plan.md
    ↓
git add -u && git commit -m "feat(story-id): task description"
    ↓
Next task
```

3 failed retries on same task → `<promise>BLOCKED</promise>: [reason]`

## Single Source of Truth Enforcement

From ralph-playbook:
- No migrations or adapters for test compatibility
- If unrelated tests fail, FIX them (don't skip)
- The codebase after your commit must be strictly better than before

## Plan Staleness Detection

Regenerate `@fix_plan.md` when:
- Ralph duplicates work already done
- Tasks reference files that don't exist
- Multiple iterations make no progress
- Story requirements changed since plan was generated

Cost: one planning iteration. Benefits: prevents cascading errors.
