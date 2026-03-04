#!/bin/bash
# Task Quality Gate — blocks task completion unless checks pass
# Hook event: TaskCompleted
# Exit 2 = block task completion | Exit 0 = allow

INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | grep -o '"task_subject":"[^"]*"' | cut -d'"' -f4)
TASK_SUBJECT="${TASK_SUBJECT:-unknown}"

ERRORS=""

# Customize these commands for your project:
# Lint check
if ! {{LINT_COMMAND}} 2>/dev/null; then
    ERRORS="${ERRORS}Lint failures. "
fi

# Build check
if ! {{BUILD_COMMAND}} 2>/dev/null; then
    ERRORS="${ERRORS}Build failures. "
fi

if [ -n "$ERRORS" ]; then
    echo "Cannot complete task '${TASK_SUBJECT}': ${ERRORS}Fix before marking complete." >&2
    exit 2
fi

exit 0
