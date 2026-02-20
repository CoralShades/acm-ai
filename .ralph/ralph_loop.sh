#!/bin/bash
# =============================================================================
# Ralph Loop Runner — ACM-AI
# Autonomous coding loop that runs Claude Code iterations until all tasks in
# @fix_plan.md are complete or a blocker is hit.
#
# Usage:
#   .ralph/ralph_loop.sh [--max N] [--tool TOOL_FLAG]
#
# Examples:
#   .ralph/ralph_loop.sh                    # Default: 40 iterations, claude tool
#   .ralph/ralph_loop.sh --max 20           # Limit to 20 iterations
#   .ralph/ralph_loop.sh --tool "--tool claude"  # Explicit tool flag
#
# Exit codes:
#   0 — All tasks completed successfully
#   1 — Loop blocked (cannot proceed)
#   2 — Max iterations reached without completion
#   3 — Setup error (missing files, bad config)
# =============================================================================

set -uo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────
MAX_ITERATIONS=40
TOOL_FLAG=""
COMPLETION_PROMISE="COMPLETE"
BLOCKED_SIGNAL="BLOCKED"
CHECKPOINT_INTERVAL=10
LOG_DIR=".ralph/logs"
FIX_PLAN=".ralph/@fix_plan.md"
PROMPT_FILE=".ralph/PROMPT.md"
METRICS_FILE=".ralph/logs/metrics.log"

# ─── Parse Arguments ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --max)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --tool)
      TOOL_FLAG="$2"
      shift 2
      ;;
    --help|-h)
      head -20 "$0" | grep -E "^#" | sed 's/^# //' | sed 's/^#//'
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 3
      ;;
  esac
done

# ─── Preflight Checks ──────────────────────────────────────────────────────
preflight_check() {
  local errors=0

  if [ ! -f "$FIX_PLAN" ]; then
    echo "ERROR: $FIX_PLAN not found. Run /ralph-init first."
    errors=$((errors + 1))
  fi

  if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: $PROMPT_FILE not found."
    errors=$((errors + 1))
  fi

  if ! command -v claude &>/dev/null; then
    echo "ERROR: 'claude' CLI not found in PATH."
    errors=$((errors + 1))
  fi

  if [ $errors -gt 0 ]; then
    echo "Preflight check failed with $errors error(s). Aborting."
    exit 3
  fi

  mkdir -p "$LOG_DIR"
}

# ─── Metrics Helpers ────────────────────────────────────────────────────────
log_metric() {
  local iteration="$1"
  local event="$2"
  local detail="${3:-}"
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "$timestamp | iteration=$iteration | event=$event | $detail" >> "$METRICS_FILE"
}

count_tasks() {
  local total checked
  total=$(grep -c '^\- \[' "$FIX_PLAN" 2>/dev/null || echo 0)
  checked=$(grep -c '^\- \[x\]' "$FIX_PLAN" 2>/dev/null || echo 0)
  echo "$checked/$total"
}

# ─── Dashboard Output ───────────────────────────────────────────────────────
print_dashboard() {
  local iteration="$1"
  local tasks
  tasks=$(count_tasks)
  local done="${tasks%/*}"
  local total="${tasks#*/}"
  local pct=0
  if [ "$total" -gt 0 ]; then
    pct=$(( (done * 100) / total ))
  fi

  printf "\n╔══════════════════════════════════════════════╗\n"
  printf "║  Ralph Loop — Iteration %3d / %-3d            ║\n" "$iteration" "$MAX_ITERATIONS"
  printf "║  Tasks: %s done (%d%%)%*s║\n" "$tasks" "$pct" $((25 - ${#tasks} - ${#pct})) ""
  printf "║  Log: %s/iteration-%d.md%*s║\n" "$LOG_DIR" "$iteration" $((22 - ${#LOG_DIR} - ${#iteration})) ""
  printf "╚══════════════════════════════════════════════╝\n\n"
}

# ─── Safety Checkpoint ──────────────────────────────────────────────────────
safety_checkpoint() {
  local iteration="$1"
  echo "Safety checkpoint at iteration $iteration..."
  git add -A 2>/dev/null
  git commit -m "chore(ralph): safety checkpoint iteration $iteration" --allow-empty 2>/dev/null || true
  log_metric "$iteration" "checkpoint" "auto-commit safety checkpoint"
}

# ─── Main Loop ──────────────────────────────────────────────────────────────
main() {
  preflight_check

  echo "============================================="
  echo "  Ralph Loop Starting"
  echo "  Max iterations: $MAX_ITERATIONS"
  echo "  Fix plan: $FIX_PLAN"
  echo "  Prompt: $PROMPT_FILE"
  echo "============================================="

  log_metric 0 "start" "max_iterations=$MAX_ITERATIONS"

  for i in $(seq 1 "$MAX_ITERATIONS"); do
    local iteration_log="$LOG_DIR/iteration-$i.md"
    local start_time
    start_time=$(date +%s)

    print_dashboard "$i"
    log_metric "$i" "iteration_start" "tasks=$(count_tasks)"

    # Run Claude Code with the prompt
    claude --print --prompt-file "$PROMPT_FILE" $TOOL_FLAG > "$iteration_log" 2>&1
    local exit_code=$?

    local end_time
    end_time=$(date +%s)
    local duration=$(( end_time - start_time ))
    log_metric "$i" "iteration_end" "exit_code=$exit_code duration=${duration}s tasks=$(count_tasks)"

    # Write iteration summary header
    {
      echo "---"
      echo "# Iteration $i Summary"
      echo "- Duration: ${duration}s"
      echo "- Exit code: $exit_code"
      echo "- Tasks: $(count_tasks)"
      echo "- Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
      echo "---"
      echo ""
    } >> "$iteration_log"

    # Check for Claude CLI errors
    if [ $exit_code -ne 0 ]; then
      echo "WARNING: Claude CLI exited with code $exit_code"
      log_metric "$i" "cli_error" "exit_code=$exit_code"
    fi

    # Check if complete
    if grep -q "$COMPLETION_PROMISE" "$iteration_log" 2>/dev/null; then
      log_metric "$i" "complete" "tasks=$(count_tasks) total_duration=$(( end_time - $(date -d "$(head -1 "$METRICS_FILE" 2>/dev/null | cut -d'|' -f1)" +%s 2>/dev/null || echo "$start_time") ))s"
      echo ""
      echo "============================================="
      echo "  Ralph completed all tasks in $i iterations"
      echo "  Final tasks: $(count_tasks)"
      echo "============================================="
      exit 0
    fi

    # Check if blocked
    if grep -q "$BLOCKED_SIGNAL" "$iteration_log" 2>/dev/null; then
      local reason
      reason=$(grep -oP "BLOCKED:?\s*\K.*" "$iteration_log" 2>/dev/null | head -1 || echo "Unknown reason")
      log_metric "$i" "blocked" "reason=$reason"
      echo ""
      echo "============================================="
      echo "  Ralph is BLOCKED at iteration $i"
      echo "  Reason: $reason"
      echo "  Check: $iteration_log"
      echo "============================================="
      exit 1
    fi

    # Safety checkpoint every N iterations
    if [ $(( i % CHECKPOINT_INTERVAL )) -eq 0 ]; then
      safety_checkpoint "$i"
    fi
  done

  log_metric "$MAX_ITERATIONS" "max_reached" "tasks=$(count_tasks)"
  echo ""
  echo "============================================="
  echo "  Ralph hit max iterations ($MAX_ITERATIONS)"
  echo "  Final tasks: $(count_tasks)"
  echo "  Review logs in $LOG_DIR/"
  echo "============================================="
  exit 2
}

main "$@"
