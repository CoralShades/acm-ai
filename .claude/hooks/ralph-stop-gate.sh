#!/bin/bash
# =============================================================================
# Ralph Stop Gate Hook
# Prevents Claude from stopping prematurely during a Ralph loop.
# Checks @fix_plan.md for unchecked tasks and respects COMPLETE/BLOCKED signals.
#
# Hook event: Stop
# Exit 2 = block stop (Claude continues working)
# Exit 0 = allow stop
# =============================================================================

INPUT=$(cat)
LAST_MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // empty')
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# CRITICAL: Prevent infinite loop — if stop hook already active, allow stop
if [ "$STOP_ACTIVE" = "true" ]; then
    exit 0
fi

# Allow stop on explicit COMPLETE signal
if echo "$LAST_MSG" | grep -qF '<promise>COMPLETE</promise>'; then
    exit 0
fi

# Allow stop on explicit BLOCKED signal
if echo "$LAST_MSG" | grep -qF '<promise>BLOCKED</promise>'; then
    exit 0
fi

# Allow stop on INIT_COMPLETE signal (during init phase)
if echo "$LAST_MSG" | grep -qF 'INIT_COMPLETE'; then
    exit 0
fi

# Allow stop on REVIEW_PASS / REVIEW_ISSUES signals (during review phase)
if echo "$LAST_MSG" | grep -qF 'REVIEW_PASS'; then
    exit 0
fi
if echo "$LAST_MSG" | grep -qF 'REVIEW_ISSUES'; then
    exit 0
fi

# Check if we're in a Ralph loop (fix plan exists)
FIX_PLAN=".ralph/@fix_plan.md"
if [ ! -f "$FIX_PLAN" ]; then
    # Not in a Ralph loop — allow normal stop
    exit 0
fi

# Count unchecked tasks
UNCHECKED=$(grep -c '^\- \[ \]' "$FIX_PLAN" 2>/dev/null || echo "0")
TOTAL=$(grep -c '^\- \[' "$FIX_PLAN" 2>/dev/null || echo "0")
CHECKED=$(grep -c '^\- \[x\]' "$FIX_PLAN" 2>/dev/null || echo "0")

if [ "$UNCHECKED" -gt 0 ]; then
    echo "Ralph: $UNCHECKED/$TOTAL tasks remaining ($CHECKED done). Continue implementing the next unchecked task in .ralph/@fix_plan.md" >&2
    exit 2  # Block stop — Claude continues
fi

# All tasks checked — allow stop
exit 0
