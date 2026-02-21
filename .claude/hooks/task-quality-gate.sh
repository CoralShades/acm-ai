#!/bin/bash
# =============================================================================
# Task Quality Gate Hook
# Blocks task completion unless lint + tests + build pass.
#
# Hook event: TaskCompleted
# Exit 2 = block task completion (feedback sent to agent)
# Exit 0 = allow task completion
# =============================================================================

INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject // "unknown"')
TASK_ID=$(echo "$INPUT" | jq -r '.task_id // "unknown"')

ERRORS=""

# Backend lint check
if command -v ruff &>/dev/null; then
    if ! ruff check . --quiet 2>/dev/null; then
        ERRORS="${ERRORS}Ruff lint failures. "
    fi
fi

# Backend tests (quick check — fail fast)
if [ -d "tests" ]; then
    if ! pytest tests/ -x --tb=no -q 2>/dev/null; then
        ERRORS="${ERRORS}Pytest failures. "
    fi
fi

# Frontend checks
if [ -d "frontend" ]; then
    if ! (cd frontend && npm run lint --silent) 2>/dev/null; then
        ERRORS="${ERRORS}Frontend lint failures. "
    fi
    if ! (cd frontend && npm run build --silent) 2>/dev/null; then
        ERRORS="${ERRORS}Frontend build failures. "
    fi
fi

if [ -n "$ERRORS" ]; then
    echo "Cannot complete task '${TASK_SUBJECT}' (${TASK_ID}): ${ERRORS}Fix these issues before marking the task complete." >&2
    exit 2  # Block task completion
fi

exit 0
