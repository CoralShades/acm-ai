# Windows Developer Setup

This guide covers prerequisites and one-time configuration for Windows developers to prevent line-ending conflicts and take advantage of auto-commit automation.

---

## Prerequisites

There are two supported setups depending on your environment. Choose the one that matches you.

---

### Option A: Native Windows (PowerShell + Git for Windows)

> **This is Sanju's setup.** No WSL2 required. Uses Git Bash (bundled with Git for Windows) to execute the hook scripts.

#### A1. Install Claude Code

```powershell
npm install -g @anthropic-ai/claude-code
```

Update to latest:
```powershell
npm update -g @anthropic-ai/claude-code
```

Verify:
```powershell
claude --version
# 2.1.x (Claude Code)
```

#### A2. Install Git for Windows (includes bash)

Download and install from [git-scm.com](https://git-scm.com/download/win). During install, select:
- **"Git from the command line and also from 3rd-party software"** (adds git + bash to PATH)
- **"Use bundled OpenSSH"** (default)

Verify bash is on PATH after install:
```powershell
bash --version
# GNU bash, version 5.x.x (includes git bash)
```

> **Why bash?** The hook scripts (`.sh` files) are bash scripts. The hooks are registered in `settings.json` with `bash "..."` as the command, so Git Bash executes them automatically — no WSL2 needed.

#### A3. Install GitHub CLI (`gh`) — for Auto-PR Creation

```powershell
winget install --id GitHub.cli
```

Authenticate:
```powershell
gh auth login
# Choose: GitHub.com → HTTPS → Login with a web browser
```

Verify:
```powershell
gh auth status
```

If `gh` is not installed, the hooks skip PR creation gracefully and just commit + push.

#### A4. Verify Python 3

The `story-done-check.sh` hook uses `python3` to parse JSON input.

```powershell
python3 --version
# Python 3.x.x
```

Git Bash ships with a minimal Python. If `python3` is missing in bash context, install Python from [python.org](https://www.python.org/downloads/windows/) and ensure it's on your PATH.

#### A5. Verify Hooks Are Registered

Open Claude Code from PowerShell in the project directory:
```powershell
cd D:\ailocal\acm-ai
claude
```

Then type `/hooks` in the Claude Code prompt. You should see:
- `[Project] Stop` → `bash ".../auto-commit.sh"`
- `[Project] PostToolUse (Write|Edit)` → `bash ".../story-done-check.sh"`
- `[Project] SessionStart (startup)` → `session-start.sh`

---

### Option B: WSL2 or Linux (your setup + hosted environments)

> **This is the main dev setup (WSL2 on Windows, or Linux servers).** Everything runs natively in bash.

#### B1. Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Update:
```bash
npm update -g @anthropic-ai/claude-code
```

#### B2. Install GitHub CLI (`gh`)

```bash
# Ubuntu/Debian
sudo apt install gh
# or
curl -sS https://webi.sh/gh | sh

gh auth login
```

#### B3. Ensure Python 3 is available

```bash
python3 --version
# Python 3.x.x — pre-installed on most Ubuntu/WSL2 distros
```

If missing: `sudo apt install python3`

#### B4. Ensure Hook Scripts Are Executable

```bash
ls -la .claude/hooks/
# Should show -rwxr-xr-x for auto-commit.sh and story-done-check.sh
```

If not:
```bash
chmod +x .claude/hooks/auto-commit.sh .claude/hooks/story-done-check.sh
```

#### B5. Launch Claude Code from WSL2 Terminal

```bash
cd /mnt/d/ailocal/acm-ai    # WSL2 path to project
claude
```

Type `/hooks` to verify all three hooks appear.

---

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
