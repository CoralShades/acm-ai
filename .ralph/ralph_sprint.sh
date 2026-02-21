#!/bin/bash
# =============================================================================
# Ralph Sprint Runner - ACM-AI
# Outer loop that auto-iterates through ready stories with full lifecycle:
#   INIT → DEV → REVIEW → TEST → FIX → COMPLETE → NEXT
#
# Supports resume after rate limit pauses via --resume flag.
#
# Usage:
#   .ralph/ralph_sprint.sh [options]
#
# Options:
#   --max-stories N       Max stories to attempt (default: unlimited)
#   --max-hours N         Stop after N hours (default: unlimited)
#   --model MODEL         Primary Claude model (default: sonnet)
#   --fallback MODEL      Fallback model for rate limits (default: opus)
#   --dev-iters N         Max iterations per dev phase (default: 40)
#   --fix-iters N         Max iterations per fix phase (default: 10)
#   --dry-run             Show which stories would run, don't execute
#   --resume              Resume the most recent sprint run
#   --resume-from DIR     Resume a specific sprint run by log directory
#   --skip-review         Skip the code review phase
#
# Exit codes:
#   0 - Sprint completed (all stories attempted)
#   1 - Sprint interrupted (max-hours or fatal error)
#   2 - No ready stories found
#   3 - Setup error
# =============================================================================

set -euo pipefail

# --- Configuration ---
MAX_STORIES=0          # 0 = unlimited
MAX_HOURS=0            # 0 = unlimited
MODEL="sonnet"
FALLBACK="opus"
DEV_ITERS=40
FIX_ITERS=10
DRY_RUN=false
RESUME=false
RESUME_DIR=""
SKIP_REVIEW=false
TASK_PLAN="task_plan.md"
RALPH_DIR=".ralph"
SPRINT_START_TIME=""

# --- Parse Arguments ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --max-stories)   MAX_STORIES="$2"; shift 2 ;;
        --max-hours)     MAX_HOURS="$2"; shift 2 ;;
        --model)         MODEL="$2"; shift 2 ;;
        --fallback)      FALLBACK="$2"; shift 2 ;;
        --dev-iters)     DEV_ITERS="$2"; shift 2 ;;
        --fix-iters)     FIX_ITERS="$2"; shift 2 ;;
        --dry-run)       DRY_RUN=true; shift ;;
        --resume)        RESUME=true; shift ;;
        --resume-from)   RESUME=true; RESUME_DIR="$2"; shift 2 ;;
        --skip-review)   SKIP_REVIEW=true; shift ;;
        --help|-h)
            head -30 "$0" | grep -E "^#" | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            exit 3
            ;;
    esac
done

# --- Sprint Log Directory ---
if [ "$RESUME" = true ] && [ -n "$RESUME_DIR" ]; then
    SPRINT_LOG_DIR="$RESUME_DIR"
elif [ "$RESUME" = true ]; then
    # Find most recent sprint log directory
    SPRINT_LOG_DIR=$(ls -dt "$RALPH_DIR"/logs/sprint-* 2>/dev/null | head -1)
    if [ -z "$SPRINT_LOG_DIR" ]; then
        echo "ERROR: No previous sprint run found to resume."
        exit 3
    fi
else
    SPRINT_LOG_DIR="$RALPH_DIR/logs/sprint-$(date +%Y%m%d-%H%M%S)"
fi
mkdir -p "$SPRINT_LOG_DIR"

SPRINT_LOG="$SPRINT_LOG_DIR/sprint.log"
STATE_FILE="$SPRINT_LOG_DIR/state.json"
SUMMARY_FILE="$SPRINT_LOG_DIR/summary.json"

# --- Logging ---
sprint_log() {
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local msg="$timestamp $*"
    echo "$msg" | tee -a "$SPRINT_LOG"
}

# --- State Management (for resume) ---
save_state() {
    local story_index="$1"
    local phase="$2"
    local completed_json="$3"
    local blocked_json="$4"
    local skipped_json="$5"
    cat > "$STATE_FILE" <<EOF
{
  "story_index": $story_index,
  "phase": "$phase",
  "model": "$MODEL",
  "fallback": "$FALLBACK",
  "dev_iters": $DEV_ITERS,
  "fix_iters": $FIX_ITERS,
  "skip_review": $SKIP_REVIEW,
  "completed": $completed_json,
  "blocked": $blocked_json,
  "skipped": $skipped_json,
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
}

load_state() {
    if [ -f "$STATE_FILE" ]; then
        echo "Resuming from saved state..."
        # Parse with grep/sed since jq may not be available
        RESUME_INDEX=$(grep '"story_index"' "$STATE_FILE" | grep -oP '\d+')
        RESUME_PHASE=$(grep '"phase"' "$STATE_FILE" | grep -oP ':\s*"\K[^"]+')
        sprint_log "[SPRINT] Resuming from story index=$RESUME_INDEX phase=$RESUME_PHASE"
        return 0
    fi
    return 1
}

# --- Story Parsing ---
# Extracts ready stories from task_plan.md P0 and P1 tables
# Writes one "STORY_ID|Title" per line to a temp file, returns the path
parse_ready_stories() {
    local tmpfile
    tmpfile=$(mktemp)
    # Parse table rows — Format: | # | Story | Title | Size | Notes |
    while IFS= read -r line; do
        local story_id
        story_id=$(echo "$line" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/, "", $3); print $3}')
        local title
        title=$(echo "$line" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/, "", $4); print $4}')
        if [ -n "$story_id" ] && [[ "$story_id" =~ ^E[0-9]+-S[0-9]+$ ]]; then
            echo "${story_id}|${title}" >> "$tmpfile"
        fi
    done < <(grep -E '^\|[[:space:]]*[0-9]+' "$TASK_PLAN" 2>/dev/null)
    echo "$tmpfile"
}

# Map story ID to its tech spec filename
find_spec_file() {
    local story_id="$1"
    # Convert E16-S2 → e16-s2, look for files matching the pattern
    local lower_id
    lower_id=$(echo "$story_id" | tr '[:upper:]' '[:lower:]')
    # Try common naming patterns
    local spec=""
    for pattern in \
        "docs/sprint-artifacts/${lower_id}-"*.md \
        "docs/sprint-artifacts/${lower_id}."*.md \
        "docs/sprint-artifacts/"*"${lower_id}"*.md; do
        local match
        match=$(ls $pattern 2>/dev/null | head -1)
        if [ -n "$match" ]; then
            spec="$match"
            break
        fi
    done
    echo "$spec"
}

# Convert story ID to branch-safe slug
story_to_branch() {
    local story_id="$1"
    local title="$2"
    # E16-S2 + "ACM Record Detail Panel" → feature/story-e16-s2-acm-record-detail-panel
    local lower_id
    lower_id=$(echo "$story_id" | tr '[:upper:]' '[:lower:]')
    local slug
    slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 40)
    echo "feature/story-${lower_id}-${slug}"
}

# --- Phase Functions ---

run_phase_init() {
    local story_id="$1"
    local title="$2"
    local spec_file="$3"
    local story_log_dir="$4"

    mkdir -p "$story_log_dir"
    local phase_log="$story_log_dir/phase-init.log"

    sprint_log "[STORY:$story_id] Phase INIT — $title"

    # Find the spec file
    if [ -z "$spec_file" ]; then
        sprint_log "[STORY:$story_id] Phase INIT — FAILED: no tech spec found"
        echo "NO_SPEC" > "$story_log_dir/.init_result"
        return 1
    fi

    sprint_log "[STORY:$story_id] Phase INIT — Spec: $spec_file"

    # Create feature branch
    local branch
    branch=$(story_to_branch "$story_id" "$title")
    sprint_log "[STORY:$story_id] Phase INIT — Branch: $branch"

    # Check if branch already exists (resume case)
    if git show-ref --verify --quiet "refs/heads/$branch" 2>/dev/null; then
        sprint_log "[STORY:$story_id] Phase INIT — Branch exists, checking out"
        git checkout "$branch" 2>&1 | tee -a "$phase_log"
    else
        git checkout -b "$branch" 2>&1 | tee -a "$phase_log"
    fi

    # Generate the init prompt with spec file substituted
    local init_prompt
    init_prompt=$(cat "$RALPH_DIR/PROMPT_INIT.md" | sed "s|SPEC_FILE_PLACEHOLDER|$(basename "$spec_file")|g")

    # Run Claude to generate the fix plan
    local claude_args=(-p "$init_prompt" --model "$MODEL")
    if [ -n "$FALLBACK" ]; then
        claude_args+=(--fallback-model "$FALLBACK")
    fi

    sprint_log "[STORY:$story_id] Phase INIT — Generating fix plan..."
    claude "${claude_args[@]}" > "$phase_log" 2>&1 || true

    # Verify fix plan was created
    if [ -f "$RALPH_DIR/@fix_plan.md" ]; then
        local task_count
        task_count=$(grep -c '^\- \[' "$RALPH_DIR/@fix_plan.md" 2>/dev/null) || task_count=0
        sprint_log "[STORY:$story_id] Phase INIT — Fix plan: $task_count tasks"
        if [ "$task_count" -eq 0 ]; then
            sprint_log "[STORY:$story_id] Phase INIT — FAILED: fix plan has 0 tasks"
            return 1
        fi
    else
        sprint_log "[STORY:$story_id] Phase INIT — FAILED: @fix_plan.md not created"
        return 1
    fi

    # Check for INIT_COMPLETE signal
    if grep -qF "INIT_COMPLETE" "$phase_log" 2>/dev/null; then
        sprint_log "[STORY:$story_id] Phase INIT — COMPLETE"
        return 0
    fi

    # Even if no explicit signal, if fix plan exists with tasks, proceed
    sprint_log "[STORY:$story_id] Phase INIT — Proceeding (fix plan generated)"
    return 0
}

run_phase_dev() {
    local story_id="$1"
    local story_log_dir="$2"

    local dev_log_dir="$story_log_dir/phase-dev"
    mkdir -p "$dev_log_dir"

    sprint_log "[STORY:$story_id] Phase DEV — Starting (max $DEV_ITERS iterations)"

    # Run the inner loop with model and log-dir passthrough
    local loop_args=(--max "$DEV_ITERS" --log-dir "$dev_log_dir" --model "$MODEL")
    if [ -n "$FALLBACK" ]; then
        loop_args+=(--fallback-model "$FALLBACK")
    fi

    "$RALPH_DIR/ralph_loop.sh" "${loop_args[@]}"
    local exit_code=$?

    case $exit_code in
        0)
            sprint_log "[STORY:$story_id] Phase DEV — COMPLETE"
            return 0
            ;;
        1)
            sprint_log "[STORY:$story_id] Phase DEV — BLOCKED"
            return 1
            ;;
        2)
            sprint_log "[STORY:$story_id] Phase DEV — Max iterations reached"
            # Not necessarily a failure — review and test will tell
            return 0
            ;;
        *)
            sprint_log "[STORY:$story_id] Phase DEV — ERROR (exit code $exit_code)"
            return 1
            ;;
    esac
}

run_phase_review() {
    local story_id="$1"
    local story_log_dir="$2"

    local phase_log="$story_log_dir/phase-review.log"

    if [ "$SKIP_REVIEW" = true ]; then
        sprint_log "[STORY:$story_id] Phase REVIEW — Skipped (--skip-review)"
        return 0
    fi

    sprint_log "[STORY:$story_id] Phase REVIEW — Starting code review"

    # Clean up previous review issues
    rm -f "$RALPH_DIR/@review_issues.md"

    local review_prompt
    review_prompt=$(cat "$RALPH_DIR/PROMPT_REVIEW.md")

    local claude_args=(-p "$review_prompt" --model "$MODEL")
    if [ -n "$FALLBACK" ]; then
        claude_args+=(--fallback-model "$FALLBACK")
    fi

    claude "${claude_args[@]}" > "$phase_log" 2>&1 || true

    # Check review result
    if grep -qF "REVIEW_PASS" "$phase_log" 2>/dev/null; then
        sprint_log "[STORY:$story_id] Phase REVIEW — PASS"
        return 0
    elif grep -qF "REVIEW_ISSUES" "$phase_log" 2>/dev/null; then
        local issue_count=0
        if [ -f "$RALPH_DIR/@review_issues.md" ]; then
            issue_count=$(grep -c '^## Issue' "$RALPH_DIR/@review_issues.md" 2>/dev/null) || issue_count=0
        fi
        sprint_log "[STORY:$story_id] Phase REVIEW — Found $issue_count issues"
        return 1
    else
        # Ambiguous — check if review issues file was created
        if [ -f "$RALPH_DIR/@review_issues.md" ] && [ -s "$RALPH_DIR/@review_issues.md" ]; then
            sprint_log "[STORY:$story_id] Phase REVIEW — Issues file found (no explicit signal)"
            return 1
        fi
        sprint_log "[STORY:$story_id] Phase REVIEW — No clear signal, assuming PASS"
        return 0
    fi
}

run_phase_test() {
    local story_id="$1"
    local story_log_dir="$2"

    local phase_log="$story_log_dir/phase-test.log"
    local test_pass=true
    local failures=""

    sprint_log "[STORY:$story_id] Phase TEST — Running test suite"

    # Python lint
    sprint_log "[STORY:$story_id] Phase TEST — ruff check"
    if ruff check . >> "$phase_log" 2>&1; then
        sprint_log "[STORY:$story_id] Phase TEST — ruff: PASS"
    else
        sprint_log "[STORY:$story_id] Phase TEST — ruff: FAIL"
        test_pass=false
        failures="${failures}ruff lint failures\n"
    fi

    # Backend tests
    sprint_log "[STORY:$story_id] Phase TEST — pytest"
    if pytest tests/ -x >> "$phase_log" 2>&1; then
        sprint_log "[STORY:$story_id] Phase TEST — pytest: PASS"
    else
        sprint_log "[STORY:$story_id] Phase TEST — pytest: FAIL"
        test_pass=false
        failures="${failures}pytest failures\n"
    fi

    # Frontend lint + build
    if [ -d "frontend" ]; then
        sprint_log "[STORY:$story_id] Phase TEST — frontend lint"
        if (cd frontend && npm run lint) >> "$phase_log" 2>&1; then
            sprint_log "[STORY:$story_id] Phase TEST — frontend lint: PASS"
        else
            sprint_log "[STORY:$story_id] Phase TEST — frontend lint: FAIL"
            test_pass=false
            failures="${failures}frontend lint failures\n"
        fi

        sprint_log "[STORY:$story_id] Phase TEST — frontend build"
        if (cd frontend && npm run build) >> "$phase_log" 2>&1; then
            sprint_log "[STORY:$story_id] Phase TEST — frontend build: PASS"
        else
            sprint_log "[STORY:$story_id] Phase TEST — frontend build: FAIL"
            test_pass=false
            failures="${failures}frontend build failures\n"
        fi
    fi

    if [ "$test_pass" = true ]; then
        sprint_log "[STORY:$story_id] Phase TEST — ALL PASS"
        return 0
    else
        # Write failures for the fix phase
        printf "%b" "$failures" > "$RALPH_DIR/@test_failures.md"
        {
            echo "# Test Failures"
            echo ""
            echo "Detected during Phase TEST of story $story_id"
            echo ""
            printf "%b" "$failures"
            echo ""
            echo "## Full log"
            echo "See: $phase_log"
        } > "$RALPH_DIR/@test_failures.md"
        sprint_log "[STORY:$story_id] Phase TEST — FAIL (see $phase_log)"
        return 1
    fi
}

run_phase_fix() {
    local story_id="$1"
    local story_log_dir="$2"

    local fix_log_dir="$story_log_dir/phase-fix"
    mkdir -p "$fix_log_dir"

    sprint_log "[STORY:$story_id] Phase FIX — Starting (max $FIX_ITERS iterations)"

    # The fix phase reuses the inner loop with the fix prompt
    local loop_args=(--max "$FIX_ITERS" --log-dir "$fix_log_dir" --model "$MODEL")
    loop_args+=(--prompt "$RALPH_DIR/PROMPT_FIX.md")
    if [ -n "$FALLBACK" ]; then
        loop_args+=(--fallback-model "$FALLBACK")
    fi

    "$RALPH_DIR/ralph_loop.sh" "${loop_args[@]}"
    local exit_code=$?

    case $exit_code in
        0)
            sprint_log "[STORY:$story_id] Phase FIX — COMPLETE"
            return 0
            ;;
        1)
            sprint_log "[STORY:$story_id] Phase FIX — BLOCKED"
            return 1
            ;;
        2)
            sprint_log "[STORY:$story_id] Phase FIX — Max iterations reached"
            return 1
            ;;
        *)
            sprint_log "[STORY:$story_id] Phase FIX — ERROR (exit code $exit_code)"
            return 1
            ;;
    esac
}

run_phase_complete() {
    local story_id="$1"
    local title="$2"
    local story_log_dir="$3"

    local phase_log="$story_log_dir/phase-complete.log"
    local branch
    branch=$(git branch --show-current)

    sprint_log "[STORY:$story_id] Phase COMPLETE — Committing and merging"

    # Stage and commit any remaining changes
    git add -u 2>&1 | tee -a "$phase_log"
    if ! git diff --cached --quiet 2>/dev/null; then
        git commit -m "feat(${story_id}): ${title}" 2>&1 | tee -a "$phase_log"
    fi

    # Push the branch
    sprint_log "[STORY:$story_id] Phase COMPLETE — Pushing $branch"
    git push -u origin "$branch" 2>&1 | tee -a "$phase_log" || true

    # Merge to main
    sprint_log "[STORY:$story_id] Phase COMPLETE — Merging to main"
    git checkout main 2>&1 | tee -a "$phase_log"
    git merge --no-ff "$branch" -m "Merge $branch: $title" 2>&1 | tee -a "$phase_log"

    if [ $? -eq 0 ]; then
        git push origin main 2>&1 | tee -a "$phase_log" || true
        sprint_log "[STORY:$story_id] Phase COMPLETE — Merged to main"

        # Update sprint-status.yaml: mark story as done
        if [ -f "docs/sprint-artifacts/sprint-status.yaml" ]; then
            # Use sed to update the story status
            sed -i "s/\(${story_id}.*status:\s*\)ready-for-dev/\1done/" \
                "docs/sprint-artifacts/sprint-status.yaml" 2>/dev/null || true
            sed -i "s/\(${story_id}.*status:\s*\)in-progress/\1done/" \
                "docs/sprint-artifacts/sprint-status.yaml" 2>/dev/null || true
        fi

        # Clean up the feature branch
        git branch -d "$branch" 2>/dev/null || true
        git push origin --delete "$branch" 2>/dev/null || true

        sprint_log "[STORY:$story_id] DONE"
        return 0
    else
        sprint_log "[STORY:$story_id] Phase COMPLETE — MERGE CONFLICT"
        git merge --abort 2>/dev/null || true
        git checkout "$branch" 2>/dev/null || true
        return 1
    fi
}

# --- Time Check ---
check_time_limit() {
    if [ "$MAX_HOURS" -gt 0 ] 2>/dev/null; then
        local elapsed=$(( $(date +%s) - SPRINT_START_TIME ))
        local max_seconds=$(( MAX_HOURS * 3600 ))
        if [ "$elapsed" -ge "$max_seconds" ]; then
            sprint_log "[SPRINT] Time limit reached (${MAX_HOURS}h)"
            return 1
        fi
    fi
    return 0
}

# --- Summary ---
print_sprint_summary() {
    local completed_count="$1"
    local blocked_count="$2"
    local skipped_count="$3"
    local total_elapsed=$(( $(date +%s) - SPRINT_START_TIME ))

    sprint_log "[SPRINT] ============================================="
    sprint_log "[SPRINT] Sprint Complete"
    sprint_log "[SPRINT]   Stories completed: $completed_count"
    sprint_log "[SPRINT]   Stories blocked:   $blocked_count"
    sprint_log "[SPRINT]   Stories skipped:   $skipped_count"
    sprint_log "[SPRINT]   Total time:        ${total_elapsed}s"
    sprint_log "[SPRINT]   Log directory:     $SPRINT_LOG_DIR"
    sprint_log "[SPRINT] ============================================="

    # Write machine-readable summary
    cat > "$SUMMARY_FILE" <<EOF
{
  "completed": $completed_count,
  "blocked": $blocked_count,
  "skipped": $skipped_count,
  "total_elapsed_seconds": $total_elapsed,
  "model": "$MODEL",
  "fallback": "$FALLBACK",
  "log_dir": "$SPRINT_LOG_DIR",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
}

# --- Main ---
main() {
    SPRINT_START_TIME=$(date +%s)

    sprint_log "[SPRINT] ============================================="
    sprint_log "[SPRINT] Ralph Sprint Runner Starting"
    sprint_log "[SPRINT]   Model: $MODEL  Fallback: $FALLBACK"
    sprint_log "[SPRINT]   Dev iterations: $DEV_ITERS  Fix iterations: $FIX_ITERS"
    sprint_log "[SPRINT]   Max stories: ${MAX_STORIES:-unlimited}  Max hours: ${MAX_HOURS:-unlimited}"
    sprint_log "[SPRINT]   Log dir: $SPRINT_LOG_DIR"
    sprint_log "[SPRINT] ============================================="

    # Preflight
    if [ ! -f "$TASK_PLAN" ]; then
        sprint_log "[SPRINT] ERROR: $TASK_PLAN not found"
        exit 3
    fi
    if ! command -v claude &>/dev/null; then
        sprint_log "[SPRINT] ERROR: 'claude' CLI not found in PATH"
        exit 3
    fi

    # Ensure we start from main
    local current_branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ] && [ "$RESUME" != true ]; then
        sprint_log "[SPRINT] Switching to main branch..."
        git checkout main 2>/dev/null || {
            sprint_log "[SPRINT] ERROR: Cannot checkout main. Stash or commit changes first."
            exit 3
        }
    fi

    # Parse stories into a temp file (one "STORY_ID|Title" per line)
    local stories_file
    stories_file=$(parse_ready_stories)
    local story_count
    story_count=$(wc -l < "$stories_file")

    if [ "$story_count" -eq 0 ]; then
        sprint_log "[SPRINT] No ready stories found in $TASK_PLAN"
        rm -f "$stories_file"
        exit 2
    fi

    sprint_log "[SPRINT] Found $story_count stories in task plan"

    # Dry run — just list stories
    if [ "$DRY_RUN" = true ]; then
        sprint_log "[SPRINT] === DRY RUN ==="
        local idx=0
        while IFS='|' read -r sid stitle; do
            idx=$((idx + 1))
            local spec
            spec=$(find_spec_file "$sid")
            local spec_status="FOUND"
            [ -z "$spec" ] && spec_status="MISSING"
            sprint_log "[SPRINT]   $idx. $sid — $stitle (spec: $spec_status)"
        done < "$stories_file"
        sprint_log "[SPRINT] === END DRY RUN ==="
        rm -f "$stories_file"
        exit 0
    fi

    # Resume state
    local start_index=0
    if [ "$RESUME" = true ] && load_state; then
        start_index=${RESUME_INDEX:-0}
        sprint_log "[SPRINT] Resuming from story index $start_index"
    fi

    # Sprint loop
    local completed_count=0
    local blocked_count=0
    local skipped_count=0
    local completed_json="[]"
    local blocked_json="[]"
    local skipped_json="[]"
    local idx=0

    while IFS='|' read -r story_id story_title; do
        # Skip stories before resume point
        if [ "$idx" -lt "$start_index" ]; then
            idx=$((idx + 1))
            continue
        fi

        # Max stories check
        if [ "$MAX_STORIES" -gt 0 ] && [ "$completed_count" -ge "$MAX_STORIES" ]; then
            sprint_log "[SPRINT] Max stories ($MAX_STORIES) reached"
            break
        fi

        # Time limit check
        if ! check_time_limit; then
            break
        fi

        local story_log_dir="$SPRINT_LOG_DIR/$story_id"
        local story_start_time
        story_start_time=$(date +%s)

        sprint_log "[SPRINT] ─────────────────────────────────────────"
        sprint_log "[SPRINT] Story $((idx + 1))/$story_count: $story_id — $story_title"
        sprint_log "[SPRINT] ─────────────────────────────────────────"

        # Save state at story start
        save_state "$idx" "init" "$completed_json" "$blocked_json" "$skipped_json"

        # Find tech spec
        local spec_file
        spec_file=$(find_spec_file "$story_id")

        # === Phase 1: INIT ===
        if ! run_phase_init "$story_id" "$story_title" "$spec_file" "$story_log_dir"; then
            sprint_log "[STORY:$story_id] Skipping — init failed"
            skipped_count=$((skipped_count + 1))
            skipped_json=$(echo "$skipped_json" | sed 's/\]$//' | sed "s/$/\"$story_id\"]/" | sed 's/^\["/["/')
            git checkout main 2>/dev/null || true
            idx=$((idx + 1))
            continue
        fi

        save_state "$idx" "dev" "$completed_json" "$blocked_json" "$skipped_json"

        # === Phase 2: DEV ===
        if ! run_phase_dev "$story_id" "$story_log_dir"; then
            sprint_log "[STORY:$story_id] Blocked during dev phase"
            blocked_count=$((blocked_count + 1))
            blocked_json=$(echo "$blocked_json" | sed 's/\]$//' | sed "s/$/\"$story_id\"]/" | sed 's/^\["/["/')
            git checkout main 2>/dev/null || true
            idx=$((idx + 1))
            continue
        fi

        save_state "$idx" "review" "$completed_json" "$blocked_json" "$skipped_json"

        # === Phase 3: REVIEW ===
        local review_has_issues=false
        if ! run_phase_review "$story_id" "$story_log_dir"; then
            review_has_issues=true
        fi

        save_state "$idx" "test" "$completed_json" "$blocked_json" "$skipped_json"

        # === Phase 4: TEST ===
        local test_failed=false
        if ! run_phase_test "$story_id" "$story_log_dir"; then
            test_failed=true
        fi

        # === Phase 5: FIX (if needed) ===
        if [ "$review_has_issues" = true ] || [ "$test_failed" = true ]; then
            save_state "$idx" "fix" "$completed_json" "$blocked_json" "$skipped_json"

            if ! run_phase_fix "$story_id" "$story_log_dir"; then
                sprint_log "[STORY:$story_id] Fix phase failed"
                blocked_count=$((blocked_count + 1))
                blocked_json=$(echo "$blocked_json" | sed 's/\]$//' | sed "s/$/\"$story_id\"]/" | sed 's/^\["/["/')
                git checkout main 2>/dev/null || true
                idx=$((idx + 1))
                continue
            fi

            # Re-run tests after fix
            sprint_log "[STORY:$story_id] Re-running tests after fix..."
            if ! run_phase_test "$story_id" "$story_log_dir"; then
                sprint_log "[STORY:$story_id] Tests still failing after fix — blocked"
                blocked_count=$((blocked_count + 1))
                blocked_json=$(echo "$blocked_json" | sed 's/\]$//' | sed "s/$/\"$story_id\"]/" | sed 's/^\["/["/')
                git checkout main 2>/dev/null || true
                idx=$((idx + 1))
                continue
            fi
        fi

        save_state "$idx" "complete" "$completed_json" "$blocked_json" "$skipped_json"

        # === Phase 6: COMPLETE ===
        if run_phase_complete "$story_id" "$story_title" "$story_log_dir"; then
            completed_count=$((completed_count + 1))
            completed_json=$(echo "$completed_json" | sed 's/\]$//' | sed "s/$/\"$story_id\"]/" | sed 's/^\["/["/')

            local story_elapsed=$(( $(date +%s) - story_start_time ))
            sprint_log "[STORY:$story_id] DONE — Total: ${story_elapsed}s"
        else
            sprint_log "[STORY:$story_id] Complete phase failed (merge conflict?)"
            blocked_count=$((blocked_count + 1))
            blocked_json=$(echo "$blocked_json" | sed 's/\]$//' | sed "s/$/\"$story_id\"]/" | sed 's/^\["/["/')
            git checkout main 2>/dev/null || true
        fi

        # Ensure we're on main for the next story
        git checkout main 2>/dev/null || true
        idx=$((idx + 1))
    done < "$stories_file"

    rm -f "$stories_file"
    print_sprint_summary "$completed_count" "$blocked_count" "$skipped_count"
    exit 0
}

main "$@"
