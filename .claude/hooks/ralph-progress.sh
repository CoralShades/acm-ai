#!/bin/bash
# Ralph progress hook — shows story progress when prd.json is written
# Trigger: PostToolUse on Write|Edit (when prd.json is the target)
# Exit: Always 0 (informational only)

# Get the file being written from the tool input
TOOL_INPUT="${TOOL_INPUT:-}"
PRD_FILE="${CLAUDE_PROJECT_DIR:-/mnt/d/ailocal/acm-ai}/prd.json"

# Only fire when prd.json is being written
if [[ "$TOOL_INPUT" != *"prd.json"* ]]; then
  exit 0
fi

# Check prd.json exists
if [[ ! -f "$PRD_FILE" ]]; then
  exit 0
fi

# Count stories done (passes: true)
DONE=$(grep -c '"passes": true' "$PRD_FILE" 2>/dev/null || echo 0)
TOTAL=33

# Count blocked (notes contains BLOCKED)
BLOCKED=$(grep -c '"notes": "BLOCKED' "$PRD_FILE" 2>/dev/null || echo 0)

# Gate status
SCHEMA=$(grep -A1 'SCHEMA_FREEZE' "$PRD_FILE" | grep -c '"unlocked": true' 2>/dev/null || echo 0)
EXTRACT=$(grep -A1 'EXTRACTION_COMPLETE' "$PRD_FILE" | grep -c '"unlocked": true' 2>/dev/null || echo 0)
AI=$(grep -A1 'AI_COMPLETE' "$PRD_FILE" | grep -c '"unlocked": true' 2>/dev/null || echo 0)
UI=$(grep -A1 'UI_COMPLETE' "$PRD_FILE" | grep -c '"unlocked": true' 2>/dev/null || echo 0)

gate_icon() { [[ "$1" -gt 0 ]] && echo "OPEN" || echo "LOCKED"; }

echo "[Ralph] Stories: ${DONE}/${TOTAL} done, ${BLOCKED} blocked | Gates: Schema=$(gate_icon $SCHEMA) Extract=$(gate_icon $EXTRACT) AI=$(gate_icon $AI) UI=$(gate_icon $UI)"

exit 0
