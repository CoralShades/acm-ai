# Windows Developer Setup

This guide covers one-time configuration for Windows developers to prevent line-ending conflicts and take advantage of auto-commit automation.

## Line Ending Setup (Required — do this once)

Windows git defaults often introduce CRLF line endings into files, causing noisy diffs and merge conflicts — especially in `package-lock.json`. Run these commands once in PowerShell or Git Bash:

```bash
git config --global core.autocrlf false
git config --global core.eol lf
```

### VSCode Setting

In VSCode settings (`Ctrl+,`), add or update:

```json
"files.eol": "\n"
```

Or via the UI: search for "End of Line" and set to `\n` (LF).

### Why This Works

The repository's `.gitattributes` enforces LF for all text files (including `package-lock.json`, `uv.lock`, all `.ts`/`.tsx`/`.py`/`.yml` files). With `core.autocrlf false`, git will not convert line endings on checkout, so your local files stay LF.

After pulling the latest `.gitattributes` changes, run once to re-normalize any existing checked-out files:

```bash
git add --renormalize .
git commit -m "fix: normalize line endings to LF"
```

---

## Auto-Commit Behavior

This repository has Claude Code hooks that automatically commit work in progress so you never lose changes between sessions.

### How It Works

**Layer 1 — Stop Hook (session end safety net)**

When you close a Claude Code session, `.claude/hooks/auto-commit.sh` runs automatically. If there are any uncommitted tracked changes on a non-main branch, it commits them with a `wip: safety checkpoint` message and pushes to the remote.

- Uses `git add -u` (tracked files only — never commits `.env`, secrets, or build artifacts)
- Skips if already on `main`/`master`
- Skips if nothing is uncommitted

**Layer 2 — PostToolUse Hook (real-time story completion)**

When Claude Code writes or edits a story file (matching `docs/sprint-artifacts/e*.md`) and the story's Status changes to `done`, `.claude/hooks/story-done-check.sh` fires automatically. It:

1. Stages all tracked changes + the story file
2. Commits with `feat(story-id): story-title`
3. Pushes to the current branch
4. Creates a PR via `gh` CLI (if available)

**Layer 3 — BMAD dev-story Workflow Step 10**

When running the BMAD `dev-story` workflow, Step 10 explicitly commits, pushes, and creates a PR after the story is marked complete. This is the most context-aware trigger.

### Requirements for Auto-PR Creation

Install the GitHub CLI:

```bash
winget install --id GitHub.cli
gh auth login
```

### Disabling Auto-Commit

If you need to disable the Stop hook temporarily, comment out the `Stop` block in `.claude/settings.json`. Do not delete the hook files.

---

## Recommended Git Workflow

1. Work on a feature branch (not `main`): `git checkout -b feat/e16-s1-dashboard`
2. Let Claude Code + BMAD handle commits when stories complete
3. Review auto-generated PRs on GitHub and merge when ready
4. Pull `main` after merging: `git checkout main && git pull`
