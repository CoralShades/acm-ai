#!/bin/bash
# Ralph gate guard — prevents commits for stories with unmet dependencies
# Trigger: PreToolUse on Bash (git commit commands)
# Exit: 2 to block, 0 to allow

TOOL_INPUT="${TOOL_INPUT:-}"
PRD_FILE="${CLAUDE_PROJECT_DIR:-/mnt/d/ailocal/acm-ai}/prd.json"

# Only check git commit commands
if [[ "$TOOL_INPUT" != *"git commit"* ]]; then
  exit 0
fi

# WIP and chore commits always pass through
if [[ "$TOOL_INPUT" == *"wip:"* ]] || [[ "$TOOL_INPUT" == *"chore:"* ]] || [[ "$TOOL_INPUT" == *"wip "* ]]; then
  exit 0
fi

# Extract story ID from commit message (pattern: feat(e30-s1): or fix(e31-s2):)
STORY_ID=$(echo "$TOOL_INPUT" | grep -oiE '[eE][0-9]+-[sS][0-9]+' | head -1 | tr '[:lower:]' '[:upper:]')

# Non-story commits pass through
if [[ -z "$STORY_ID" ]]; then
  exit 0
fi

# If no prd.json, can't check — allow
if [[ ! -f "$PRD_FILE" ]]; then
  exit 0
fi

# Check if story exists and get its dependencies using python for JSON parsing
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

# Check all dependencies are satisfied
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

if [[ "$CHECK_RESULT" == BLOCKED:* ]]; then
  DEPS="${CHECK_RESULT#BLOCKED:}"
  echo "[Ralph Gate Guard] BLOCKED: ${STORY_ID} has unmet dependencies: ${DEPS}"
  echo "Complete dependency stories first, or use 'wip:' prefix for work-in-progress commits."
  exit 2
fi

exit 0
