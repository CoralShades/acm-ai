#!/bin/bash
# Scope Guard — blocks Write/Edit to protected paths during Ralph loops
# Hook event: PreToolUse (matcher: Write|Edit)
# Exit 2 = block | Exit 0 = allow

if [ ! -f ".ralph/@fix_plan.md" ]; then
    exit 0
fi

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Normalize to relative path
PROJECT_DIR=$(pwd)
REL_PATH="${FILE_PATH#$PROJECT_DIR/}"

# Customize: add paths that should never be modified during loops
PROTECTED_PATTERNS=(
    "^\.env$"
    "^\.env\."
    "^docker-compose\.yml$"
    "^\.github/"
    "^\.claude/settings\.json$"
)

for pattern in "${PROTECTED_PATTERNS[@]}"; do
    if echo "$REL_PATH" | grep -qE "$pattern"; then
        echo "Scope guard: Blocked modification to protected path '$REL_PATH'." >&2
        exit 2
    fi
done

exit 0
