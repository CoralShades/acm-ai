#!/bin/bash
# =============================================================================
# Task Quality Gate Hook
# Blocks task completion unless lint + build pass.
# Pytest is advisory in WSL (many pre-existing failures from missing deps).
#
# Hook event: TaskCompleted
# Exit 2 = block task completion (feedback sent to agent)
# Exit 0 = allow task completion
# =============================================================================

INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | grep -o '"task_subject":"[^"]*"' | cut -d'"' -f4)
TASK_SUBJECT="${TASK_SUBJECT:-unknown}"
TASK_ID=$(echo "$INPUT" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
TASK_ID="${TASK_ID:-unknown}"

ERRORS=""

# Backend lint check (try uv run, fall back to direct command)
if [ -d "tests" ] || [ -f "pyproject.toml" ]; then
    if ! uv run ruff check . --quiet 2>/dev/null && ! ruff check . --quiet 2>/dev/null; then
        ERRORS="${ERRORS}Ruff lint failures. "
    fi
fi

# Backend tests — advisory only in WSL environment
# Many pre-existing failures from missing dependencies (ai_prompter, httpx_sse, etc.)
# Tests should be run with `uv run pytest` in proper venv for full validation
# Skipping pytest gate to avoid blocking on environment issues

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
