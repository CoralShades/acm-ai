#!/bin/bash
# =============================================================================
# Ralph Loop Runner - ACM-AI
# Autonomous coding loop that runs Claude Code iterations until all tasks in
# @fix_plan.md are complete or a blocker is hit.
#
# Usage:
#   .ralph/ralph_loop.sh [--max N] [--tool TOOL_FLAG] [--model MODEL]
#                        [--fallback-model MODEL] [--log-dir DIR]
#                        [--prompt FILE]
#
# Examples:
#   .ralph/ralph_loop.sh                    # Default: 40 iterations
#   .ralph/ralph_loop.sh --max 20           # Limit to 20 iterations
#   .ralph/ralph_loop.sh --model sonnet --fallback-model opus
#   .ralph/ralph_loop.sh --log-dir .ralph/logs/sprint-xxx/story-id/phase-dev
#
# Exit codes:
#   0 - All tasks completed successfully (COMPLETE signal)
#   1 - Loop blocked (BLOCKED signal or circuit breaker)
#   2 - Max iterations reached without completion (some progress made)
#   3 - Setup error (missing files, bad config)
#   4 - Infrastructure failure (credits, auth, rate limit, network)
# =============================================================================

set -euo pipefail

# --- Configuration ---
MAX_ITERATIONS=40
TOOL_FLAG=""
MODEL="opus"
FALLBACK_MODEL=""
COMPLETION_PROMISE="<promise>COMPLETE</promise>"
BLOCKED_SIGNAL="<promise>BLOCKED</promise>"
CHECKPOINT_INTERVAL=10
LOG_DIR=".ralph/logs"
FIX_PLAN=".ralph/@fix_plan.md"
PROMPT_FILE=".ralph/PROMPT.md"
METRICS_FILE=""  # Set after LOG_DIR is finalized
LOOP_START_TIME=""
NO_PROGRESS_THRESHOLD=3
consecutive_no_progress=0
last_task_count=""

# --- Parse Arguments ---
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
        --model)
            MODEL="$2"
            shift 2
            ;;
        --fallback-model)
            FALLBACK_MODEL="$2"
            shift 2
            ;;
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --prompt)
            PROMPT_FILE="$2"
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

# Finalize metrics file path after LOG_DIR is set
METRICS_FILE="$LOG_DIR/metrics.log"

# --- Preflight Checks ---
preflight_check() {
    local errors=0

    if [ ! -f "$FIX_PLAN" ]; then
        echo "ERROR: $FIX_PLAN not found. Run /ralph-init first."
        errors=$((errors + 1))
    else
        local task_count=0
        task_count=$(grep -c '^\- \[' "$FIX_PLAN" 2>/dev/null) || task_count=0
        if [ "$task_count" -eq 0 ]; then
            echo "ERROR: $FIX_PLAN has no tasks. Run /ralph-init first to populate it."
            errors=$((errors + 1))
        fi
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

# --- Metrics Helpers ---
log_metric() {
    local iteration="$1"
    local event="$2"
    local detail="${3:-}"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$timestamp | iteration=$iteration | event=$event | $detail" >> "$METRICS_FILE"
}

count_tasks() {
    local total=0
    local checked=0
    if [ -f "$FIX_PLAN" ]; then
        total=$(grep -c '^\- \[' "$FIX_PLAN" 2>/dev/null) || total=0
        checked=$(grep -c '^\- \[x\]' "$FIX_PLAN" 2>/dev/null) || checked=0
    fi
    printf "%d/%d" "$checked" "$total"
}

# --- Fatal Error Detection ---
# Scans iteration log for infrastructure errors (credits, auth, rate limits, network)
# Returns 0 (match found) with the matching pattern on stdout, or 1 (no match)
check_fatal_errors() {
    local log="$1"
    local patterns=(
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
    for p in "${patterns[@]}"; do
        if grep -qi "$p" "$log" 2>/dev/null; then
            echo "$p"
            return 0
        fi
    done
    return 1
}

# --- Dashboard Output ---
print_dashboard() {
    local iteration="$1"
    local tasks
    tasks=$(count_tasks)
    local done_count="${tasks%/*}"
    local total_count="${tasks#*/}"
    local pct=0
    if [ "$total_count" -gt 0 ] 2>/dev/null; then
        pct=$(( (done_count * 100) / total_count ))
    fi
    local elapsed=0
    if [ -n "$LOOP_START_TIME" ]; then
        elapsed=$(( $(date +%s) - LOOP_START_TIME ))
    fi

    echo ""
    echo "=============================================="
    echo "  Ralph Loop - Iteration $iteration / $MAX_ITERATIONS"
    echo "  Tasks: $tasks done ($pct%)"
    echo "  Elapsed: ${elapsed}s"
    echo "  Log: $LOG_DIR/iteration-$iteration.md"
    echo "=============================================="
    echo ""
}

# --- Safety Checkpoint ---
safety_checkpoint() {
    local iteration="$1"
    echo "Safety checkpoint at iteration $iteration..."
    # Stage only tracked files — avoid staging secrets or untracked artifacts
    git add -u 2>/dev/null || true
    git diff --cached --quiet 2>/dev/null || \
        git commit -m "chore(ralph): safety checkpoint iteration $iteration" 2>/dev/null || true
    log_metric "$iteration" "checkpoint" "auto-commit safety checkpoint"
}

# --- Main Loop ---
main() {
    preflight_check

    LOOP_START_TIME=$(date +%s)

    echo "============================================="
    echo "  Ralph Loop Starting"
    echo "  Max iterations: $MAX_ITERATIONS"
    echo "  Fix plan: $FIX_PLAN"
    echo "  Prompt: $PROMPT_FILE"
    echo "============================================="

    log_metric 0 "start" "max_iterations=$MAX_ITERATIONS tasks=$(count_tasks)"

    for i in $(seq 1 "$MAX_ITERATIONS"); do
        local iteration_log="$LOG_DIR/iteration-$i.md"
        local start_time
        start_time=$(date +%s)

        print_dashboard "$i"
        log_metric "$i" "iteration_start" "tasks=$(count_tasks)"

        # Build Claude command with model flags
        local claude_args=(-p "$(cat "$PROMPT_FILE")" --dangerously-skip-permissions)
        if [ -n "$MODEL" ]; then
            claude_args+=(--model "$MODEL")
        fi
        if [ -n "$FALLBACK_MODEL" ]; then
            claude_args+=(--fallback-model "$FALLBACK_MODEL")
        fi
        if [ -n "$TOOL_FLAG" ]; then
            claude_args+=($TOOL_FLAG)
        fi

        # Run Claude Code (env -u strips ANTHROPIC_API_KEY so CLI uses OAuth)
        local exit_code=0
        env -u ANTHROPIC_API_KEY claude "${claude_args[@]}" > "$iteration_log" 2>&1 || exit_code=$?

        local end_time
        end_time=$(date +%s)
        local duration=$(( end_time - start_time ))
        local total_elapsed=$(( end_time - LOOP_START_TIME ))
        log_metric "$i" "iteration_end" "exit_code=$exit_code duration=${duration}s total_elapsed=${total_elapsed}s tasks=$(count_tasks)"

        # Append iteration summary to the log
        {
            echo ""
            echo "---"
            echo "# Iteration $i Summary"
            echo "- Duration: ${duration}s"
            echo "- Total elapsed: ${total_elapsed}s"
            echo "- Exit code: $exit_code"
            echo "- Tasks: $(count_tasks)"
            echo "- Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
            echo "---"
        } >> "$iteration_log"

        # Check for Claude CLI errors
        if [ "$exit_code" -ne 0 ]; then
            echo "WARNING: Claude CLI exited with code $exit_code"
            log_metric "$i" "cli_error" "exit_code=$exit_code"
        fi

        # Check if complete (uses XML promise wrapper to avoid false positives)
        if grep -qF "$COMPLETION_PROMISE" "$iteration_log" 2>/dev/null; then
            log_metric "$i" "complete" "tasks=$(count_tasks) total_elapsed=${total_elapsed}s"
            echo ""
            echo "============================================="
            echo "  Ralph completed all tasks in $i iterations"
            echo "  Final tasks: $(count_tasks)"
            echo "  Total time: ${total_elapsed}s"
            echo "============================================="
            exit 0
        fi

        # Check if blocked (uses XML promise wrapper to avoid false positives)
        if grep -qF "$BLOCKED_SIGNAL" "$iteration_log" 2>/dev/null; then
            local reason
            reason=$(grep -oP "<promise>BLOCKED</promise>:?\s*\K.*" "$iteration_log" 2>/dev/null | head -1 || echo "Unknown reason")
            log_metric "$i" "blocked" "reason=$reason total_elapsed=${total_elapsed}s"
            echo ""
            echo "============================================="
            echo "  Ralph is BLOCKED at iteration $i"
            echo "  Reason: $reason"
            echo "  Check: $iteration_log"
            echo "============================================="
            exit 1
        fi

        # Check for infrastructure errors (credits, auth, rate limits, network)
        local fatal_msg=""
        if fatal_msg=$(check_fatal_errors "$iteration_log"); then
            log_metric "$i" "fatal_error" "pattern=$fatal_msg"
            echo ""
            echo "============================================="
            echo "  FATAL: Infrastructure error at iteration $i"
            echo "  Error: $fatal_msg"
            echo "  Check: $iteration_log"
            echo "============================================="
            exit 4
        fi

        # No-progress circuit breaker
        local current_tasks
        current_tasks=$(count_tasks)
        if [ "$current_tasks" = "$last_task_count" ]; then
            consecutive_no_progress=$((consecutive_no_progress + 1))
            if [ "$consecutive_no_progress" -ge "$NO_PROGRESS_THRESHOLD" ]; then
                log_metric "$i" "circuit_breaker" "no progress for $NO_PROGRESS_THRESHOLD consecutive iterations"
                echo ""
                echo "============================================="
                echo "  Circuit breaker: $NO_PROGRESS_THRESHOLD iterations with no progress"
                echo "  Tasks stuck at: $current_tasks"
                echo "  Check logs in: $LOG_DIR/"
                echo "============================================="
                exit 1
            fi
        else
            consecutive_no_progress=0
        fi
        last_task_count="$current_tasks"

        # Inter-iteration delay (backoff on errors, brief pause on success)
        if [ "$exit_code" -ne 0 ]; then
            sleep 30
        else
            sleep 2
        fi

        # Safety checkpoint every N iterations
        if [ $(( i % CHECKPOINT_INTERVAL )) -eq 0 ]; then
            safety_checkpoint "$i"
        fi
    done

    local final_elapsed=$(( $(date +%s) - LOOP_START_TIME ))
    log_metric "$MAX_ITERATIONS" "max_reached" "tasks=$(count_tasks) total_elapsed=${final_elapsed}s"
    echo ""
    echo "============================================="
    echo "  Ralph hit max iterations ($MAX_ITERATIONS)"
    echo "  Final tasks: $(count_tasks)"
    echo "  Total time: ${final_elapsed}s"
    echo "  Review logs in $LOG_DIR/"
    echo "============================================="
    exit 2
}

main "$@"
