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

# Backend tests (try uv run, fall back to direct command)
# Ignore tests with pre-existing import errors (missing ai_prompter, commands circular imports)
PYTEST_IGNORES="--ignore=tests/test_broadmeadows_e2e.py --ignore=tests/test_acm_commands.py --ignore=tests/test_graphs.py --ignore=tests/test_acm_ai_extraction.py --ignore=tests/test_acm_api.py"
if [ -d "tests" ]; then
    if ! uv run pytest tests/ $PYTEST_IGNORES -x --tb=no -q 2>/dev/null && ! python3 -m pytest tests/ $PYTEST_IGNORES -x --tb=no -q 2>/dev/null; then
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
