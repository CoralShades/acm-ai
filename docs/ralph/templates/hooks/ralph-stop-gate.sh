#!/bin/bash
# Ralph Stop Gate — prevents Claude from stopping prematurely
# Hook event: Stop
# Exit 2 = block stop (Claude continues working)
# Exit 0 = allow stop
#
# Only active when a Ralph loop PID file exists.
# ALWAYS check stop_hook_active to prevent infinite loops.

RALPH_PID_FILE=".ralph/.sprint_pid"
if [ ! -f "$RALPH_PID_FILE" ]; then
    exit 0
fi

INPUT=$(cat)

# Prevent infinite loop: if stop hook already active, let it stop
if echo "$INPUT" | grep -q '"stop_hook_active":true'; then
    exit 0
fi

# Extract last message (jq-free parsing)
LAST_MSG=$(echo "$INPUT" | grep -o '"last_assistant_message":"[^"]*"' | sed 's/^"last_assistant_message":"//;s/"$//' || echo "")

# Allow stop on explicit completion/blocked signals
for SIGNAL in '<promise>COMPLETE</promise>' '<promise>BLOCKED</promise>' 'INIT_COMPLETE' 'INIT_FAILED' 'REVIEW_PASS' 'REVIEW_ISSUES'; do
    if echo "$LAST_MSG" | grep -qF "$SIGNAL"; then
        exit 0
    fi
done

# Check fix plan for unchecked tasks
FIX_PLAN=".ralph/@fix_plan.md"
if [ -f "$FIX_PLAN" ]; then
    UNCHECKED=$(grep -c '^\- \[ \]' "$FIX_PLAN" 2>/dev/null || echo "0")
    TOTAL=$(grep -c '^\- \[' "$FIX_PLAN" 2>/dev/null || echo "0")
    CHECKED=$(grep -c '^\- \[x\]' "$FIX_PLAN" 2>/dev/null || echo "0")

    if [ "$UNCHECKED" -gt 0 ]; then
        echo "Ralph: $UNCHECKED/$TOTAL tasks remaining ($CHECKED done). Continue working." >&2
        exit 2
    fi
fi

exit 0
