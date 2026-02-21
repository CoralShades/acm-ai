#!/bin/bash
# PostToolUse hook: detect when a BMAD story is marked done via Write/Edit
# then auto-commit, push, and create a PR

INPUT=$(cat)  # JSON from Claude Code hook system

# Extract the file path from the tool input
FILE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    ti = d.get('tool_input', {})
    print(ti.get('file_path', ti.get('path', '')))
except Exception:
    print('')
" 2>/dev/null)

# Fallback: try jq if python3 unavailable
if [[ -z "$FILE" ]]; then
  FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""' 2>/dev/null)
fi

# Only trigger on story files in docs/sprint-artifacts/
[[ "$FILE" == */docs/sprint-artifacts/e*.md ]] || exit 0
[[ -f "$FILE" ]] || exit 0

# Check if this story is now marked done
grep -qiE '^\*\*Status:\*\*\s*done' "$FILE" || exit 0

# Extract story info
STORY_ID=$(basename "$FILE" .md)
STORY_TITLE=$(grep -m1 "^# Story" "$FILE" | sed 's/^# Story [^:]*: //')
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)

# Don't auto-commit+PR on main/master
[[ "$BRANCH" == "main" || "$BRANCH" == "master" ]] && exit 0

# Check if already committed with this story ID (avoid double commits)
LAST_MSG=$(git log --oneline -1 2>/dev/null)
[[ "$LAST_MSG" == *"$STORY_ID"* ]] && exit 0

# Stage tracked files + story file explicitly
git add -u
git add "$FILE"

# Check there's actually something to commit
git diff --cached --quiet && exit 0

COMMIT_MSG="feat(${STORY_ID}): ${STORY_TITLE}"
if ! git commit -m "$COMMIT_MSG"; then
  echo "[story-done-check] Commit failed for ${STORY_ID}"
  exit 1
fi

git push -u origin "$BRANCH" 2>/dev/null || echo "[story-done-check] Push failed — commit saved locally"

# Auto-create PR (requires gh CLI)
if ! command -v gh &>/dev/null; then
  echo "[story-done-check] gh CLI not found — skipping PR creation. Commit pushed: $COMMIT_MSG"
  exit 0
fi

CHANGED_FILES=$(git diff --stat HEAD~1 2>/dev/null | grep -v "files changed" | awk '{print $1}' | head -5 | sed 's/^/- /' | tr '\n' '\n')
STORY_SUMMARY=$(grep -A3 "## User Story" "$FILE" 2>/dev/null | tail -3 | head -3 || echo "See story file")
BUILD_NOTES=$(grep -A6 "### Build Verification" "$FILE" 2>/dev/null | head -7 || echo "See story file")

PR_BODY="## Story: ${STORY_TITLE}

**Story File:** \`${FILE}\`

## Summary
${STORY_SUMMARY}

## Key Files Changed
${CHANGED_FILES}

## Verification
${BUILD_NOTES}

---
🤖 Auto-committed by Claude Code when story status changed to done"

gh pr create \
  --title "${STORY_ID}: ${STORY_TITLE}" \
  --body "$PR_BODY" \
  --base main \
  --head "$BRANCH" 2>/dev/null \
  && echo "[story-done-check] PR created for ${STORY_ID}" \
  || echo "[story-done-check] Note: PR creation skipped (may already exist or branch not pushed)"
