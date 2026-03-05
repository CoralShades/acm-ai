#!/bin/bash
# Ralph Gate Guard — blocks commits for stories with unmet dependencies
# Hook event: PreToolUse (matcher: Bash)
# Exit 2 = block commit | Exit 0 = allow

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | grep -o '"command":"[^"]*"' | head -1 | cut -d'"' -f4)

# Only check git commit commands
if ! echo "$COMMAND" | grep -qE '^\s*git\s+commit'; then
    exit 0
fi

# WIP and chore commits always pass
if echo "$COMMAND" | grep -qE 'wip:|chore:'; then
    exit 0
fi

# Extract story ID from commit message (pattern: feat(e1-s1): or fix(e2-s3):)
STORY_ID=$(echo "$COMMAND" | grep -oiE '[eE][0-9]+-[sS][0-9]+' | head -1 | tr '[:lower:]' '[:upper:]')

# Non-story commits pass through
if [ -z "$STORY_ID" ]; then
    exit 0
fi

# Check prd.json for dependency satisfaction
PRD_FILE="prd.json"
if [ ! -f "$PRD_FILE" ]; then
    exit 0
fi

CHECK_RESULT=$(python3 -c "
import json, sys
try:
    with open('$PRD_FILE') as f:
        prd = json.load(f)
except:
    sys.exit(0)

story_id = '$STORY_ID'
stories = {s['id']: s for s in prd.get('stories', [])}
gates = {g['id']: g for g in prd.get('gates', [])}

story = stories.get(story_id)
if not story:
    print('OK')
    sys.exit(0)

unmet = []
for dep in story.get('dependencies', []):
    if dep.startswith('GATE:'):
        gate = gates.get(dep)
        if gate and not gate.get('unlocked', False):
            unmet.append(f'{dep} (LOCKED)')
    else:
        dep_story = stories.get(dep)
        if dep_story and not dep_story.get('passes', False):
            unmet.append(f'{dep} (not done)')

if unmet:
    print('BLOCKED:' + ', '.join(unmet))
else:
    print('OK')
" 2>/dev/null)

if [ "${CHECK_RESULT}" = "${CHECK_RESULT#BLOCKED:}" ]; then
    exit 0
fi

DEPS="${CHECK_RESULT#BLOCKED:}"
echo "[Gate Guard] BLOCKED: ${STORY_ID} has unmet dependencies: ${DEPS}" >&2
echo "Complete dependency stories first, or use 'wip:' prefix." >&2
exit 2
