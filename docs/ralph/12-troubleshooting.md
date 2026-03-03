# Ralph Troubleshooting Guide

This guide covers common failure modes grouped by category. Each entry lists the symptom, root cause, and fix.

---

## Windows / WSL Issues

### `lib64` Symlink Blocking `uv run` (Exit Code 2)

**Symptom:** `uv run` fails with "Access is denied" or exit code 2 after running `uv sync` inside WSL.

**Root cause:** WSL creates a Linux-style `lib64` symlink inside `.venv/` that Windows cannot follow. The symlink points to `/usr/lib/x86_64-linux-gnu` which does not exist from the Windows side.

**Fix:**
```bash
# From Windows (PowerShell or Git Bash):
rm -rf .venv/lib64
rm -rf .venv/bin

# Then re-run uv sync from Windows:
uv sync
```

**Prevention:** Always run `uv sync` from the Windows side (PowerShell or Git Bash), not from inside WSL. If you must sync from WSL, delete the symlinks immediately after.

---

### 9P Filesystem Overhead (Slow API / Worker)

**Symptom:** API startup takes 30+ seconds. Worker is sluggish. File watchers miss changes or cause high CPU.

**Root cause:** WSL2 accesses Windows filesystem (`/mnt/d/...`) through the 9P protocol, which has high latency for many small file operations. Uvicorn's StatReload scans files continuously, amplifying the overhead.

**Fix:**
```bash
# In .env — disable reload:
API_RELOAD=false

# Use Docker named volumes instead of bind mounts for SurrealDB:
# (Already configured in docker-compose.yml as acm-ai-surreal-data)

# Move project files to WSL native filesystem for pure WSL development:
# /home/user/projects/acm-ai  (much faster than /mnt/d/...)
```

**Reference:** SurrealDB volume is `acm-ai-surreal-data` (named volume, not bind mount). Do not change this to a bind mount targeting `/mnt/d/...`.

---

### Unicode Encoding Error in `surreal-commands-worker`

**Symptom:** Worker crashes immediately on Windows with `UnicodeEncodeError` or garbled output.

**Root cause:** The `surreal-commands-worker` binary writes Unicode characters (arrows, checkmarks) to stdout. Windows console defaults to CP1252, not UTF-8.

**Fix:** Use the Python wrapper instead of calling the worker binary directly:
```bash
# Wrong (Windows):
surreal-commands-worker

# Correct (Windows):
uv run run_worker.py --import-modules commands
```

The `run_worker.py` wrapper sets `PYTHONIOENCODING=utf-8` and routes output correctly.

---

### `CLAUDE_PROJECT_DIR` Empty on Windows

**Symptom:** Scripts using `$CLAUDE_PROJECT_DIR` fail silently or use wrong paths. Ralph loop can't find prd.json.

**Root cause:** The `CLAUDE_PROJECT_DIR` environment variable is set by the Claude Code session hook, but on Windows the hook may not fire correctly, or the variable is not exported to child processes.

**Fix:** In any script or bash command, use a fallback:
```bash
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-D:/ailocal/acm-ai}"
cd "$PROJECT_DIR"
```

Or use forward-slash Windows paths directly (Git Bash accepts them):
```bash
cd "D:/ailocal/acm-ai"
```

**Do not use:**
- `cd /d/ailocal/acm-ai` — Git Bash drive-letter syntax, unreliable
- `cd D:\ailocal\acm-ai` — Windows backslash, fails in bash
- `cd /mnt/d/ailocal/acm-ai` — WSL path, only works inside WSL

---

### Path Conversion Between Environments

**Symptom:** A path that works in one shell fails in another. Scripts break when switching between Git Bash, WSL, and Windows CMD.

**Path format reference:**

| Context | Format | Example |
|---|---|---|
| Windows CMD / PowerShell | Backslash | `D:\ailocal\acm-ai` |
| Git Bash | Forward slash | `D:/ailocal/acm-ai` |
| WSL (accessing Windows) | `/mnt/` prefix | `/mnt/d/ailocal/acm-ai` |
| WSL (native) | Unix path | `/home/user/projects/acm-ai` |

**Fix:** The session-start hook normalizes paths automatically when Ralph starts. If running scripts manually outside a Claude session, always use the Git Bash forward-slash format (`D:/ailocal/acm-ai`).

---

### macOS: `sed` Differences

**Symptom:** Scripts using `sed -i` work on Linux but fail on macOS with "extra characters at the end of h command".

**Root cause:** BSD sed (macOS) requires an explicit extension argument to `-i`. GNU sed (Linux) does not.

**Fix:** Use `-i ''` on macOS:
```bash
# Linux / GNU sed:
sed -i 's/old/new/' file.txt

# macOS / BSD sed:
sed -i '' 's/old/new/' file.txt

# Portable alternative (works on both):
perl -i -pe 's/old/new/' file.txt
```

---

### macOS: Missing `jq`

**Symptom:** Ralph scripts fail with `jq: command not found`.

**Fix:**
```bash
brew install jq
```

---

### macOS: `perl` Not Available

**Symptom:** Wiggum completion detection script fails with `perl: command not found`.

**Fix:**
```bash
brew install perl
```

---

## Auth Issues

### Credit Balance Too Low

**Symptom:** API calls fail with `402 Payment Required` or "Your credit balance is too low."

**Fix options:**
1. Top up credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)
2. Switch to OAuth (Claude Max subscription) which does not use API credits:
   ```bash
   # Force OAuth by removing API key from environment:
   env -u ANTHROPIC_API_KEY claude --model claude-opus-4-6
   ```

---

### Rate Limits

**Symptom:** `429 Too Many Requests` errors. Ralph loop slows to a crawl or stops.

**Root cause:** API key billing tiers have per-minute token limits. Long-running Ralph loops with parallel subagents can hit these limits quickly.

**Fix:**
1. Switch to Claude Max plan (OAuth) — significantly higher limits
2. Reduce parallelism in Ralph — avoid launching multiple subagents simultaneously
3. Add delays between iterations (not recommended for productivity)

**Check current tier:** [console.anthropic.com/settings/limits](https://console.anthropic.com/settings/limits)

---

### OAuth vs API Key Conflict

**Symptom:** Claude uses API key even though you want OAuth. Or OAuth fails because `ANTHROPIC_API_KEY` is set.

**Root cause:** `ANTHROPIC_API_KEY` environment variable takes precedence over OAuth tokens.

**Fix — Force OAuth:**
```bash
env -u ANTHROPIC_API_KEY claude --model claude-opus-4-6
```

**Fix — Force API key (override OAuth):**
```bash
ANTHROPIC_API_KEY=sk-... claude --model claude-sonnet-4-6
```

**Check which auth is active:**
```bash
claude auth status
```

---

### `invalid_api_key` Error

**Symptom:** All API calls fail with `authentication_error: invalid_api_key`.

**Common causes:**
- Stale or rotated key in `.env`
- `.env` not loaded (wrong working directory)
- Key has trailing whitespace or newline

**Fix:**
```bash
# Check what key is active:
echo $ANTHROPIC_API_KEY | cat -A   # -A shows invisible characters

# Reload .env:
source .env

# Or remove entirely to fall back to OAuth:
unset ANTHROPIC_API_KEY
```

---

### OAuth Session Expiry

**Symptom:** OAuth was working, now fails with `401 Unauthorized` or "Session expired."

**Fix:**
```bash
claude auth login
# Follow the browser flow to re-authenticate
```

---

## Loop Issues

### Circuit Breaker Firing

**Symptom:** Ralph stops after N iterations with "Circuit breaker: no progress detected." Story remains incomplete.

**Root cause:** The circuit breaker fires when 3+ consecutive iterations produce no verifiable progress (no commits, no story status change, no file changes). This usually means:
- The task is too large for a single context window
- The agent is stuck in a reasoning loop
- The story definition is ambiguous

**Fix:**
1. Check `@fix_plan.md` — what was the last completed step?
2. Split the story into smaller sub-tasks
3. Add explicit checkpoints to the story task list
4. Use `/ralph-retry ID` to reset and attempt with fresh context

---

### Max Iterations Reached

**Symptom:** Ralph exits cleanly but story is marked BLOCKED. Log shows "Max iterations (40) reached."

**Root cause:** Story is genuinely too complex for a single Ralph session with 40 iterations.

**Fix options:**
1. Split the story into two smaller stories in prd.json
2. Increase `max_iterations` in `ralph-config.json` (use cautiously — more cost)
3. Pre-implement the complex parts manually, then let Ralph finish the remaining steps

---

### Stop Hook Infinite Loop

**Symptom:** Claude exits but immediately restarts. The loop never terminates even after COMPLETE.

**Root cause:** Stop hook is calling `claude` again without a guard, creating infinite recursion.

**Fix:** Add the `stop_hook_active` guard to the Stop hook:
```bash
# In your Stop hook script:
if [ "${stop_hook_active}" = "1" ]; then
  exit 0
fi
export stop_hook_active=1

# ... rest of hook logic
```

See `docs/ralph/08-hooks.md` for the complete Stop hook pattern.

---

### BLOCKED Signal Stuck

**Symptom:** Story shows BLOCKED in status. `/ralph-status` shows it as ineligible. The blocking condition has been resolved but the flag is not cleared.

**Fix:**
```bash
# Clear block on specific story:
/ralph-retry STORY_ID

# Or manually edit prd.json:
# Find the story, clear the "notes" field:
# "notes": ""   (was: "BLOCKED: ...")
```

---

### Claude Exits Immediately (No Iterations)

**Symptom:** Ralph starts, Claude launches, but exits after less than one second with no output.

**Root cause:** Stop hook not registered, or registered with wrong trigger. Claude sees the Stop hook fire on startup and exits cleanly.

**Fix:** Check `.claude/settings.json`:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/ralph-progress.sh"
          }
        ]
      }
    ]
  }
}
```

Verify the hook command path is correct and the script is executable.

---

### False COMPLETE Detection

**Symptom:** Ralph marks a story complete but the work is unfinished. The detection is matching natural language like "This is now complete" or "the task is complete."

**Root cause:** Grep-based completion detection is too broad. Any text containing "complete" in the response triggers it.

**Fix:** Ensure all completion checks use the XML wrapper protocol:
```bash
# Agent must output exactly:
<promise>COMPLETE</promise>

# Detection command:
grep -q '<promise>COMPLETE</promise>' response.txt
```

Do not rely on natural language detection for completion signals. Update `PROMPT.md` to instruct the agent to use the XML wrapper.

---

## Hook Issues

### Hook Timeout

**Symptom:** Hook fires but times out before completing. Error: "Hook timed out after Ns."

**Root cause:** Default hook timeout is 10-30 seconds. Build steps, lint, or network calls in hooks can exceed this.

**Fix:** Increase timeout in `settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/scope-guard.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

---

### Scope Guard Blocking Legitimate Writes

**Symptom:** Agent cannot write to a file that should be allowed. Hook returns non-zero exit code with "BLOCKED: outside allowed scope."

**Root cause:** `PROTECTED_PATTERNS` in `scope-guard.sh` is too restrictive, or the file path doesn't match the expected pattern.

**Fix:** Edit `.claude/hooks/ralph-gate-guard.sh` (or `scope-guard.sh`) and add an exception:
```bash
# Add to ALLOWED_PATTERNS array:
ALLOWED_PATTERNS=(
  "^open_notebook/"
  "^api/"
  "^frontend/src/"
  "^your/new/path/"   # Add this
)
```

Then re-run the failing operation.

---

### Pre-Commit Gate Blocking

**Symptom:** `git commit` fails because the pre-commit hook exits non-zero. Lint or build errors are reported.

**Root cause:** Code quality gate is working correctly — there are real issues in the code.

**Fix (preferred):** Fix the lint/build errors before committing:
```bash
uv run ruff check . --fix
uv run ruff format .
cd frontend && npm run lint -- --fix
```

**Fix (emergency bypass):** Use `wip:` prefix in commit message to bypass the gate:
```bash
git commit -m "wip: checkpoint before refactor"
```

The pre-commit hook checks for `wip:` prefix and skips quality gates for work-in-progress commits.

---

### Hook Not Firing

**Symptom:** Expected hook behavior does not occur. No errors, but hook actions are not executed.

**Checklist:**
1. Verify hook is registered in `.claude/settings.json` under correct event (`PreToolUse`, `PostToolUse`, `Stop`, etc.)
2. Verify `matcher` regex matches the tool name (e.g., `"Bash"` not `"bash"`)
3. Verify script is executable: `chmod +x .claude/hooks/myhook.sh`
4. Verify script path is relative to project root (not absolute)
5. Check hook script for syntax errors: `bash -n .claude/hooks/myhook.sh`

---

## prd.json Issues

### Corruption (Invalid JSON)

**Symptom:** Ralph fails to start with "SyntaxError: Unexpected token" or jq parse error against prd.json.

**Root cause:** Partial write during a crash left prd.json in an invalid state.

**Fix:**
```bash
# Validate JSON:
jq . prd.json > /dev/null

# If invalid, restore from git:
git checkout HEAD -- prd.json

# Or regenerate from scratch:
/ralph-bridge
```

**Prevention:** Ralph writes prd.json atomically (write to temp file, then rename). Manual edits should be validated with `jq . prd.json` before saving.

---

### Gate Mismatch (Gate Unlocked but Trigger Story Not Done)

**Symptom:** `/ralph-status` shows a gate as unlocked, but the story that was supposed to unlock it is not marked DONE.

**Root cause:** Gate was manually unlocked, or the trigger condition was met by a different story.

**Fix:**
```bash
# Re-lock the gate:
/ralph-gate lock GATE_NAME

# Complete the trigger story:
/ralph-run TRIGGER_STORY_ID

# Then re-unlock after story completes:
# (Gate auto-unlocks when trigger story is DONE)
```

---

### Circular Dependencies

**Symptom:** `/ralph-status` shows a story as ineligible, but its listed dependencies all appear complete. Or validation errors on startup.

**Root cause:** Story A depends on B, B depends on A (directly or transitively).

**Fix:** Edit prd.json manually to break the cycle:
```bash
# Find the cycle:
# Look for stories where depA -> depB -> depA

# Remove the weaker dependency:
# In the story definition, remove one of the circular "deps" entries
jq '.stories[] | {id: .id, deps: .deps}' prd.json
```

---

### Story Not Eligible

**Symptom:** `/ralph-run STORY_ID` says story is not eligible. Status shows it as blocked.

**Checklist:**
1. Check deps: `jq '.stories[] | select(.id == "STORY_ID") | .deps' prd.json`
2. Verify all deps are DONE: `jq '.stories[] | select(.status == "DONE") | .id' prd.json`
3. Check gate: `jq '.gates[] | select(.blocks == "STORY_ID")' prd.json`
4. Check notes field: `jq '.stories[] | select(.id == "STORY_ID") | .notes' prd.json`

If a gate is blocking, use `/ralph-gate unlock GATE_NAME` after the trigger conditions are met.

---

### `notes` Field Stuck with BLOCKED

**Symptom:** Story shows as BLOCKED in status but the blocking issue is resolved.

**Fix:**
```bash
# Clear via command:
/ralph-retry STORY_ID

# Or manually:
# Edit prd.json, find the story, set:
# "notes": ""
```

---

## Recovery Procedures

### Resume After Crash

Ralph uses `state.json` to persist loop state. On restart, it reads this file and resumes from the saved phase.

```bash
# Check current state:
cat .ralph/state.json

# Resume normally:
.ralph/ralph_loop.sh

# Force restart from beginning (discards state):
rm .ralph/state.json
.ralph/ralph_loop.sh
```

---

### Rollback a Bad Iteration

Ralph creates safety checkpoint commits before each iteration. Use these to roll back.

```bash
# View recent checkpoints:
git log --oneline | grep -E "checkpoint|wip"

# Roll back N commits (soft — keeps changes staged):
git reset --soft HEAD~N

# Roll back N commits (hard — discards all changes):
git reset --hard HEAD~N

# Roll back to specific commit:
git reset --hard COMMIT_SHA
```

---

### Manual Checkpoint

If Ralph is paused and you want to create a manual safety checkpoint:
```bash
git add -u
git commit -m "chore(ralph): manual checkpoint before $(date +%Y%m%d-%H%M)"
```

---

### Re-Run a Single Story

To reset and re-run a specific story without affecting others:
```bash
# Reset story status to PENDING:
/ralph-reset STORY_ID

# Then run it:
/ralph-run STORY_ID
```

---

### Clear All Blocks

If multiple stories are stuck with BLOCKED status:
```bash
# View all blocked stories:
jq '.stories[] | select(.notes | test("BLOCKED")) | .id' prd.json

# Clear all at once (use with caution):
jq '.stories[].notes = ""' prd.json > prd.json.tmp && mv prd.json.tmp prd.json

# Validate:
jq . prd.json > /dev/null && echo "Valid JSON"
```

---

## Diagnostic Commands

Quick reference for diagnosing Ralph state:

```bash
# Check story eligibility:
/ralph-status

# View prd.json summary:
jq '{total: (.stories | length), done: (.stories | map(select(.status == "DONE")) | length), blocked: (.stories | map(select(.notes | test("BLOCKED"))) | length)}' prd.json

# Check gate states:
jq '.gates' prd.json

# View recent Ralph activity:
git log --oneline -20 | grep -E "feat|fix|chore|wip"

# Check hook registrations:
jq '.hooks' .claude/settings.json

# Validate all JSON files:
for f in prd.json ralph-config.json .claude/settings.json; do
  echo -n "$f: "
  jq . "$f" > /dev/null && echo "OK" || echo "INVALID"
done
```
