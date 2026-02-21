#!/bin/bash
# Auto-commit uncommitted tracked changes at end of Claude Code session (Stop hook)
# Safety net: commits any work-in-progress so nothing is lost between sessions

# Must be in a git repo
git rev-parse --git-dir > /dev/null 2>&1 || exit 0
git symbolic-ref HEAD > /dev/null 2>&1 || exit 0  # Not detached HEAD

# Skip if nothing to commit
git diff --quiet && git diff --cached --quiet && exit 0

BRANCH=$(git symbolic-ref --short HEAD)

# Don't auto-commit on main/master — too risky
[[ "$BRANCH" == "main" || "$BRANCH" == "master" ]] && exit 0

# Find the most recently modified story file for commit message context
STORY_FILE=$(ls -t docs/sprint-artifacts/e*.md 2>/dev/null | head -1)
STORY_CONTEXT=""
if [[ -n "$STORY_FILE" ]]; then
  STORY_CONTEXT=$(grep -m1 "^# Story" "$STORY_FILE" 2>/dev/null | sed 's/^# Story [^:]*: //' | cut -c1-60)
fi

# Stage tracked files only (avoids committing secrets/untracked artifacts)
git add -u

if [[ -n "$STORY_CONTEXT" ]]; then
  MSG="wip: safety checkpoint — ${STORY_CONTEXT}"
else
  CHANGED=$(git diff --cached --name-only 2>/dev/null | head -3 | paste -sd', ')
  MSG="wip: safety checkpoint — ${CHANGED}"
fi

git commit -m "$MSG" && git push -u origin "$BRANCH" 2>/dev/null || true
echo "[auto-commit] Committed: $MSG"
