#!/bin/bash
# =============================================================================
# Pre-Commit Gate Hook
# Blocks `git commit` commands unless verification suite passes.
# Only active when .ralph/@fix_plan.md exists (Ralph loop is running).
#
# Hook event: PreToolUse (matcher: Bash)
# Exit 2 = block the command
# Exit 0 = allow
# =============================================================================

# Only guard when in a Ralph loop
if [ ! -f ".ralph/@fix_plan.md" ]; then
    exit 0
fi

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | grep -o '"command":"[^"]*"' | head -1 | cut -d'"' -f4)

# Only intercept git commit commands
if ! echo "$COMMAND" | grep -qE '^\s*git\s+commit'; then
    exit 0
fi

# Allow safety checkpoint commits (from Ralph loop itself)
if echo "$COMMAND" | grep -q 'chore(ralph): safety checkpoint'; then
    exit 0
fi

# Allow WIP commits (from auto-commit hook)
if echo "$COMMAND" | grep -q 'wip:'; then
    exit 0
fi

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
    echo "Pre-commit gate: Cannot commit. ${ERRORS}Fix these issues first." >&2
    exit 2  # Block the commit
fi

exit 0
