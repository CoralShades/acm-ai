#!/bin/bash
# Pre-Commit Gate — blocks commits unless verification passes
# Hook event: PreToolUse (matcher: Bash)
# Exit 2 = block commit | Exit 0 = allow
#
# Only active when .ralph/@fix_plan.md exists (Ralph loop running)

if [ ! -f ".ralph/@fix_plan.md" ]; then
    exit 0
fi

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | grep -o '"command":"[^"]*"' | head -1 | cut -d'"' -f4)

# Only intercept git commit commands
if ! echo "$COMMAND" | grep -qE '^\s*git\s+commit'; then
    exit 0
fi

# Allow safety checkpoint and WIP commits
if echo "$COMMAND" | grep -qE 'chore\(ralph\): safety checkpoint|wip:'; then
    exit 0
fi

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
    echo "Pre-commit gate: Cannot commit. ${ERRORS}Fix issues first." >&2
    exit 2
fi

exit 0
