#!/bin/bash
# =============================================================================
# Ralph Stop Gate Hook
# Prevents Claude from stopping prematurely during a Ralph loop.
# Checks @fix_plan.md for unchecked tasks and respects COMPLETE/BLOCKED signals.
#
# Hook event: Stop
# Exit 2 = block stop (Claude continues working)
# Exit 0 = allow stop
#
# IMPORTANT: Only active when ralph_sprint.sh is running (checks for PID file)
# =============================================================================

# Only activate during Ralph sprint runs (not interactive sessions)
RALPH_PID_FILE=".ralph/.sprint_pid"
if [ ! -f "$RALPH_PID_FILE" ]; then
    exit 0
fi

# Read stdin — parse without jq using grep/sed
INPUT=$(cat)

# Extract last_assistant_message using grep (rough but jq-free)
LAST_MSG=$(echo "$INPUT" | grep -o '"last_assistant_message":"[^"]*"' | sed 's/^"last_assistant_message":"//;s/"$//' || echo "")

# Check stop_hook_active to prevent infinite loop
if echo "$INPUT" | grep -q '"stop_hook_active":true'; then
    exit 0
fi

# Allow stop on explicit signals
for SIGNAL in '<promise>COMPLETE</promise>' '<promise>BLOCKED</promise>' 'INIT_COMPLETE' 'INIT_FAILED' 'REVIEW_PASS' 'REVIEW_ISSUES'; do
    if echo "$LAST_MSG" | grep -qF "$SIGNAL"; then
        exit 0
    fi
done

# Check if fix plan exists
FIX_PLAN=".ralph/@fix_plan.md"
if [ ! -f "$FIX_PLAN" ]; then
    exit 0
fi

# Count unchecked tasks
UNCHECKED=$(grep -c '^\- \[ \]' "$FIX_PLAN" 2>/dev/null || echo "0")
TOTAL=$(grep -c '^\- \[' "$FIX_PLAN" 2>/dev/null || echo "0")
CHECKED=$(grep -c '^\- \[x\]' "$FIX_PLAN" 2>/dev/null || echo "0")

if [ "$UNCHECKED" -gt 0 ]; then
    echo "Ralph: $UNCHECKED/$TOTAL tasks remaining ($CHECKED done). Continue implementing the next unchecked task in .ralph/@fix_plan.md" >&2
    exit 2
fi

exit 0
