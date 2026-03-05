# Hooks

> Claude Code hooks for quality gates, scope protection, and loop control.

## Hook Lifecycle

```
SessionStart → [UserPromptSubmit → PreToolUse → (tool runs) → PostToolUse → ... → Stop]
                 ^── agentic loop repeats ──────────────────────────────────────────┘
```

Additional events: `TaskCompleted`, `SubagentStart`, `SubagentStop`, `TeammateIdle`, `PermissionRequest`, `ConfigChange`, `Notification`.

## Exit Code Contract

| Exit Code | Meaning | Effect |
|-----------|---------|--------|
| `exit 0` | Success | Action proceeds. JSON output parsed from stdout |
| `exit 2` | Blocking error | Action blocked. stderr fed back to Claude as error |
| Other | Non-blocking | stderr shown in verbose mode, execution continues |

**Critical**: `exit 2` is the ONLY way to block tool calls. JSON is ignored on exit 2 — only stderr matters.

## Blocking vs Non-Blocking Events

### Can Block (exit 2 prevents action)

| Event | What Gets Blocked |
|-------|-------------------|
| `PreToolUse` | Blocks the tool call |
| `Stop` | Prevents Claude from stopping (continues conversation) |
| `TaskCompleted` | Prevents task from being marked complete |
| `PermissionRequest` | Denies the permission |
| `UserPromptSubmit` | Blocks prompt processing |
| `SubagentStop` | Prevents subagent from stopping |
| `TeammateIdle` | Prevents teammate from going idle |
| `ConfigChange` | Blocks config change |

### Cannot Block (exit 2 only shows stderr)

| Event | Behavior on exit 2 |
|-------|-------------------|
| `PostToolUse` | Shows stderr to Claude (tool already ran) |
| `SessionStart` | Shows stderr to user only |
| `SessionEnd` | Shows stderr to user only |
| `Notification` | Shows stderr to user only |
| `SubagentStart` | Shows stderr to user only |

## Hook Types

### Command Hooks (`type: "command"`)
Run shell scripts. Receive JSON on stdin, return decisions via exit code + stdout JSON.

### Prompt Hooks (`type: "prompt"`)
Single-turn LLM evaluation. Returns `{ "ok": true/false, "reason": "..." }`. Default model: haiku (fast).

### Agent Hooks (`type: "agent"`)
Multi-turn subagent with Read/Grep/Glob tools. Same response format. Up to 50 turns, 60s timeout.

## Matcher Patterns

Matchers are regex strings applied to tool names:
- `"Bash"` — matches Bash tool
- `"Write|Edit"` — matches either
- `"mcp__memory__.*"` — matches all memory MCP tools
- `""` or omitted — matches everything

## PreToolUse Decision Control

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "Why",
    "updatedInput": { "field": "modified value" },
    "additionalContext": "Extra info for Claude"
  }
}
```

## Ralph Hook Inventory

### 1. Stop Gate (`ralph-stop-gate.sh`)
- **Event**: Stop
- **Purpose**: Prevent premature exit during Ralph loops
- **Behavior**: Checks for unchecked tasks in @fix_plan.md. If tasks remain, exit 2 blocks stop.
- **Guards**: PID file check (only active during loops), `stop_hook_active` check (prevents infinite loop)
- **Signals allowed through**: COMPLETE, BLOCKED, INIT_COMPLETE, INIT_FAILED, REVIEW_PASS, REVIEW_ISSUES

### 2. Scope Guard (`scope-guard.sh`)
- **Event**: PreToolUse (matcher: `Write|Edit`)
- **Purpose**: Block writes to protected paths during loops
- **Behavior**: Regex-matches file path against `PROTECTED_PATTERNS` array
- **Guard**: Only active when `.ralph/@fix_plan.md` exists
- **Protected by default**: `.env`, `docker-compose.yml`, `.github/`, `.claude/settings.json`, `pyproject.toml`

### 3. Pre-Commit Gate (`pre-commit-gate.sh`)
- **Event**: PreToolUse (matcher: `Bash`)
- **Purpose**: Block commits that fail lint/build verification
- **Behavior**: Intercepts `git commit`, runs lint + build, exit 2 if failures
- **Guard**: Only active when `.ralph/@fix_plan.md` exists
- **Bypass**: `chore(ralph): safety checkpoint` and `wip:` commits pass through

### 4. Gate Guard (`ralph-gate-guard.sh`)
- **Event**: PreToolUse (matcher: `Bash`)
- **Purpose**: Block commits for stories with unmet dependencies
- **Behavior**: Extracts story ID from commit message, checks prd.json deps
- **Uses**: python3 for JSON parsing (jq-free)
- **Bypass**: `wip:` and `chore:` commits pass through

### 5. Task Quality Gate (`task-quality-gate.sh`)
- **Event**: TaskCompleted
- **Purpose**: Block task completion unless lint + build pass
- **Behavior**: Runs lint + build checks, exit 2 if failures
- **Input**: Receives `task_subject` and `task_id` from hook JSON

### 6. Ralph Progress (`ralph-progress.sh`)
- **Event**: PostToolUse (matcher: `Write|Edit`)
- **Purpose**: Display progress when prd.json is written
- **Behavior**: Counts stories done/blocked, shows gate status
- **Non-blocking**: Always exit 0 (informational only)

### 7. Story Done Check (`story-done-check.sh`)
- **Event**: PostToolUse (matcher: `Write|Edit`)
- **Purpose**: Auto-commit and create PR when story status changes to done
- **Behavior**: Detects `**Status:** done` in story files, commits, pushes, creates PR via `gh`
- **Guard**: Only on feature branches (not main/master)

### 8. Auto-Commit (`auto-commit.sh`)
- **Event**: Stop
- **Purpose**: Safety net — commit uncommitted work at session end
- **Behavior**: `git add -u && git commit -m "wip: safety checkpoint"`
- **Guard**: Only on feature branches, only if changes exist

### 9. Session Start (`session-start.sh`)
- **Event**: SessionStart (matcher: `startup`)
- **Purpose**: Initialize session with project context
- **Behavior**: WSL path normalization, cloud dep setup, env var persistence, context banner
- **Features**: Detects cloud environments (Codespaces, GitHub Actions, Vercel, CI)

### 10. Pre-Tool-Use (`pre-tool-use.sh`)
- **Event**: PreToolUse
- **Purpose**: Block modifications to protected files
- **Behavior**: Pattern-matches file paths against protected list
- **Protected**: `tests/`, `migrations/`, `pyproject.toml`, `package.json`, `docker-compose`, `.github/`

## Key Patterns

### PID File Gating
Stop gate only activates when `.ralph/.sprint_pid` exists (sprint runner creates this). Interactive sessions are not affected.

### `stop_hook_active` Guard
**Critical**: Always check `stop_hook_active` in Stop hooks:
```bash
if echo "$INPUT" | grep -q '"stop_hook_active":true'; then
    exit 0  # Let it stop — prevents infinite loop
fi
```
Without this guard, a Stop hook that always blocks creates an infinite loop.

### jq-Free JSON Parsing
For environments without jq, use grep/sed:
```bash
LAST_MSG=$(echo "$INPUT" | grep -o '"last_assistant_message":"[^"]*"' | sed 's/^"last_assistant_message":"//;s/"$//')
```

### Environment Variables
- `$CLAUDE_PROJECT_DIR` — project root (use in command paths)
- `$CLAUDE_ENV_FILE` — write `export` statements here in SessionStart to persist env vars
- `$CLAUDE_CODE_REMOTE` — `"true"` in remote/cloud environments

## Hook Configuration

### settings.json Structure
```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/ralph-stop-gate.sh\"",
        "timeout": 10,
        "statusMessage": "Checking Ralph task completion..."
      }]
    }],
    "PreToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{ "type": "command", "command": "..." }]
    }]
  }
}
```

### Configuration Locations

| Location | Scope | Shared |
|----------|-------|--------|
| `~/.claude/settings.json` | All projects | No (local) |
| `.claude/settings.json` | Single project | Yes (committed) |
| `.claude/settings.local.json` | Single project | No (gitignored) |
| Plugin `hooks/hooks.json` | When plugin enabled | Yes |

## Best Practices

1. **Always check `stop_hook_active`** in Stop hooks to prevent infinite loops
2. **Use exit 2 sparingly** — only for genuine blocking conditions
3. **Keep hooks fast** — SessionStart and PostToolUse run frequently
4. **Log to files not stdout** — stdout is parsed as JSON by Claude Code
5. **Use `$CLAUDE_PROJECT_DIR`** for portable script paths
6. **PreToolUse > PostToolUse for blocking** — can't undo a completed tool call
7. **PID file gating** — don't interfere with interactive sessions
8. **Test hooks manually** first: `echo '{"stop_hook_active":false}' | bash hook.sh`

## Templates

See `templates/hooks/` for copy-paste ready hook scripts.
