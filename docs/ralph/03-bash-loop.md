# Mode 1: Bash Loop

> External bash script spawning fresh Claude Code instances per iteration.

## Overview

The bash loop is the original Ralph pattern. A shell script runs `claude -p` in a loop, checking output for completion/blocked signals after each iteration.

**Key property**: Each iteration gets a completely fresh context window. State persists only via files on disk (prd.json, @fix_plan.md, git history).

## Pattern A: Simple Loop

Minimal ~50-line script from snarktank/ralph. Suitable for single-story implementations.

### Architecture
```
ralph.sh
  └── for i in 1..N:
        claude -p "$(cat PROMPT.md)" --dangerously-skip-permissions --model $MODEL
        grep COMPLETE → exit 0
        grep BLOCKED  → exit 1
```

### Full Script

```bash
#!/bin/bash
# Simple Ralph Loop — spawns fresh Claude Code per iteration
set -euo pipefail

MAX_ITERATIONS="${1:-50}"
MODEL="${2:-sonnet}"
PROMPT_FILE="PROMPT.md"
COMPLETION_PROMISE="<promise>COMPLETE</promise>"
BLOCKED_SIGNAL="<promise>BLOCKED</promise>"

# Force OAuth (remove API key so CLI uses subscription)
unset ANTHROPIC_API_KEY
# Allow spawning child instances
unset CLAUDECODE

cd "$(dirname "$0")/.."

if [ ! -f prd.json ]; then
  echo "ERROR: prd.json not found."
  exit 1
fi

# Branch archiving (optional)
BRANCH=$(jq -r '.branchName // empty' prd.json 2>/dev/null)
if [ -n "$BRANCH" ]; then
  CURRENT=$(git branch --show-current)
  [ "$CURRENT" != "$BRANCH" ] && git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
fi

# Initialize progress file
[ -f progress.txt ] || echo "## Codebase Patterns" > progress.txt

echo "=== Ralph Loop: $MAX_ITERATIONS iterations, model: $MODEL ==="

for i in $(seq 1 "$MAX_ITERATIONS"); do
  echo ""
  echo "=== Iteration $i of $MAX_ITERATIONS ==="

  REMAINING=$(jq '[.stories[] | select(.passes == false)] | length' prd.json 2>/dev/null || echo "0")
  if [ "$REMAINING" -eq 0 ]; then
    echo "All stories complete!"
    exit 0
  fi
  echo "Stories remaining: $REMAINING"

  OUTPUT=$(claude \
    -p "$(cat "$PROMPT_FILE")" \
    --dangerously-skip-permissions \
    --model "$MODEL" \
    2>&1 | tee /dev/stderr) || true

  if echo "$OUTPUT" | grep -qF "$COMPLETION_PROMISE"; then
    echo "=== Ralph completed all stories! ==="
    exit 0
  fi

  if echo "$OUTPUT" | grep -qF "$BLOCKED_SIGNAL"; then
    echo "=== Ralph blocked — needs human intervention ==="
    exit 2
  fi

  sleep 2
done

echo "=== Max iterations ($MAX_ITERATIONS) reached ==="
exit 1
```

### Key Characteristics
- ~50 lines, easy to understand and customize
- `jq` required for prd.json parsing
- Captures output via `tee /dev/stderr` (visible + greppable)
- `unset ANTHROPIC_API_KEY` forces OAuth (subscription-based billing)
- `unset CLAUDECODE` allows spawning child Claude instances
- Branch archiving preserves previous run state

## Pattern B: Full-Featured Loop

Production-grade ~350-line script with circuit breakers, metrics, dashboards, and safety nets.

### Architecture
```
ralph_loop.sh [--max N] [--model M] [--fallback-model M] [--log-dir DIR] [--prompt FILE]
  ├── preflight_check()    # Verify fix plan, prompt, CLI exist
  ├── for i in 1..N:
  │     ├── print_dashboard()       # Iteration N/max, tasks done/total, elapsed
  │     ├── claude -p ... > log     # Run with model flags, log output
  │     ├── log_metric()            # Timestamp, iteration, event, detail
  │     ├── grep COMPLETE → exit 0
  │     ├── grep BLOCKED  → exit 1
  │     ├── check_fatal_errors()    # Credits, auth, rate limit, network
  │     ├── circuit_breaker()       # N consecutive no-progress → exit 1
  │     ├── sleep (30s error / 2s success)
  │     └── safety_checkpoint()     # Every 10 iterations: git commit
  └── exit 2 (max reached)
```

### Features

| Feature | Description |
|---------|-------------|
| **Arg parsing** | `--max`, `--model`, `--fallback-model`, `--log-dir`, `--prompt` |
| **Exit codes** | 0=complete, 1=blocked, 2=max reached, 3=setup error, 4=infra failure |
| **Preflight** | Verifies fix plan has tasks, prompt file exists, `claude` CLI in PATH |
| **Metrics** | `timestamp \| iteration=N \| event=X \| detail` to `metrics.log` |
| **Dashboard** | Per-iteration: iteration count, task progress, elapsed time, log path |
| **Fatal errors** | Detects: credit balance, rate limit, auth failure, connection refused |
| **Circuit breaker** | Stops after N iterations with no task progress change |
| **Safety checkpoints** | `git add -u && git commit` every N iterations |
| **Backoff** | 30s sleep after errors, 2s after success |
| **Fallback model** | `--fallback-model` flag for automatic model downgrade |

### Fatal Error Patterns

The loop scans each iteration's log for these infrastructure errors:

```bash
PATTERNS=(
    "Credit balance is too low"
    "rate limit"
    "rate_limit_error"
    "insufficient_quota"
    "Authentication failed"
    "invalid_api_key"
    "Could not connect"
    "Connection refused"
    "overloaded_error"
)
```

Any match triggers exit code 4 (infrastructure failure).

### Circuit Breaker Logic

```
Track: count_tasks() returns "checked/total" each iteration
If same count for N consecutive iterations:
  → "No progress for N iterations" → exit 1
Else:
  → Reset counter
Default threshold: 3 consecutive no-progress iterations
```

### Metrics Log Format

```
2026-01-15T10:30:00Z | iteration=1 | event=iteration_start | tasks=0/12
2026-01-15T10:32:45Z | iteration=1 | event=iteration_end | exit_code=0 duration=165s total_elapsed=165s tasks=2/12
2026-01-15T10:32:46Z | iteration=2 | event=iteration_start | tasks=2/12
```

### Safety Checkpoint Pattern

```bash
safety_checkpoint() {
    git add -u 2>/dev/null || true
    git diff --cached --quiet 2>/dev/null || \
        git commit -m "chore(ralph): safety checkpoint iteration $i" 2>/dev/null || true
}
```

- Only stages tracked files (`-u`), never untracked (avoids secrets)
- Silent failure if nothing to commit
- Default: every 10 iterations (configurable via `CHECKPOINT_INTERVAL`)

## Sprint Runner

The sprint runner wraps the loop in a multi-story lifecycle:

### 6-Phase Story Lifecycle
```
1. INIT    → claude -p PROMPT_INIT.md → generates @fix_plan.md
2. DEV     → ralph_loop.sh → iterative implementation
3. REVIEW  → claude -p PROMPT_REVIEW.md → adversarial review
4. TEST    → bash: ruff, pytest, npm lint, npm build
5. FIX     → ralph_loop.sh --prompt PROMPT_FIX.md (if review found issues)
6. COMPLETE → commit, push, update sprint-status
```

### Story Selection
Sprint runner reads `prd.json`, picks next eligible story using selection algorithm (see `07-prd-and-gates.md`), processes it through all 6 phases.

### Resume
Sprint runner persists state in `state.json`:
```json
{
  "currentStory": "E2-S8",
  "currentPhase": "dev",
  "iteration": 15,
  "startedAt": "2026-02-22T07:51:48Z"
}
```

Restarting the script resumes from the saved phase/iteration.

### Dry Run
`--dry-run` flag walks through story selection and phase sequence without executing.

## OAuth vs API Key

| Method | How | Billing |
|--------|-----|---------|
| OAuth (recommended) | `env -u ANTHROPIC_API_KEY claude` | Claude Max/Pro subscription |
| API Key | `ANTHROPIC_API_KEY=sk-... claude` | Per-token billing |

OAuth is preferred for loops: unlimited usage on Max plan, no credit balance concerns.

## Template

See `templates/ralph_loop.sh.template` (simple) and `templates/ralph_loop_full.sh.template` (full-featured).
