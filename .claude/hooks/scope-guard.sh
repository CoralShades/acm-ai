#!/bin/bash
# =============================================================================
# Scope Guard Hook
# Blocks Write/Edit to protected paths during Ralph loops.
# Only active when .ralph/@fix_plan.md exists (Ralph loop is running).
#
# Hook event: PreToolUse (matcher: Write|Edit)
# Exit 2 = block the write/edit
# Exit 0 = allow
# =============================================================================

# Only guard when in a Ralph loop
if [ ! -f ".ralph/@fix_plan.md" ]; then
    exit 0
fi

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# No file path — allow (shouldn't happen but be safe)
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Normalize to relative path from project root
PROJECT_DIR=$(pwd)
REL_PATH="${FILE_PATH#$PROJECT_DIR/}"

# Protected paths — block modifications
PROTECTED_PATTERNS=(
    "^\.env$"
    "^\.env\."
    "^uv\.lock$"
    "^frontend/package-lock\.json$"
    "^docker-compose\.yml$"
    "^docker-compose\.override\.yml$"
    "^docker-compose\.dev-local\.yml$"
    "^\.github/"
    "^\.claude/settings\.json$"
    "^\.claude/settings\.local\.json$"
    "^pyproject\.toml$"
)

for pattern in "${PROTECTED_PATTERNS[@]}"; do
    if echo "$REL_PATH" | grep -qE "$pattern"; then
        echo "Scope guard: Blocked $TOOL_NAME to protected path '$REL_PATH'. This file should not be modified during Ralph loop execution." >&2
        exit 2
    fi
done

# Allow everything else
exit 0
