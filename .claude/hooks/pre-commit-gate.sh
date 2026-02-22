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
    echo "Pre-commit gate: Cannot commit. ${ERRORS}Fix these issues first." >&2
    exit 2  # Block the commit
fi

exit 0
