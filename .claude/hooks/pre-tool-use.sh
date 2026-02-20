#!/bin/bash
# Pre-tool-use hook: Block modifications to protected files
# Exit codes: 0 = allow, 1 = deny with message, 2 = hard block

TOOL_NAME="$1"
shift
ARGS=("$@")

# Protected file patterns
PROTECTED_PATTERNS=(
    "tests/"
    "migrations/"
    "pyproject.toml"
    "package.json"
    "docker-compose"
    ".github/workflows/"
    "uv.lock"
    "package-lock.json"
)

# Only check Write and Edit tools
if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
    exit 0
fi

# Extract file path from tool arguments
FILE_PATH=""
for arg in "${ARGS[@]}"; do
    if [[ "$arg" =~ ^file_path=(.+)$ ]]; then
        FILE_PATH="${BASH_REMATCH[1]}"
        break
    fi
done

# If no file path found, allow (shouldn't happen)
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Check against protected patterns
for pattern in "${PROTECTED_PATTERNS[@]}"; do
    if [[ "$FILE_PATH" == *"$pattern"* ]]; then
        echo "🛡️  BLOCKED: Cannot modify protected file: $FILE_PATH"
        echo "   Pattern matched: $pattern"
        echo "   Protected files require explicit user approval."
        echo "   If you need to modify this file, ask the user first."
        exit 2
    fi
done

# Allow all other files
exit 0
