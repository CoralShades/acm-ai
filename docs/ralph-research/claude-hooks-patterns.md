# Claude Code Hooks Patterns for Ralph Loops

Compiled 2026-02-22 from https://code.claude.com/docs/en/hooks

## Hook Lifecycle in Agentic Loop

```
SessionStart → [UserPromptSubmit → PreToolUse → (tool runs) → PostToolUse → ... → Stop] → SessionEnd
                 ^── agentic loop repeats ──────────────────────────────────────────┘
```

## Exit Code Strategy

| Exit Code | Meaning | Effect |
|-----------|---------|--------|
| `exit 0` | Success | Action proceeds. JSON output parsed from stdout |
| `exit 2` | Blocking error | Action blocked. stderr fed back to Claude as error message |
| Other | Non-blocking error | stderr shown in verbose mode, execution continues |

**Critical**: `exit 2` is the ONLY way to block tool calls. JSON is ignored on exit 2 — only stderr matters.

## Hook Types

### Command Hooks (`type: "command"`)
Run shell scripts. Receive JSON on stdin, return decisions via exit code + stdout JSON.

### Prompt Hooks (`type: "prompt"`)
Single-turn LLM evaluation. Returns `{ "ok": true/false, "reason": "..." }`.
- Use `$ARGUMENTS` placeholder for hook input JSON in prompt text
- Default model: fast (Haiku)

### Agent Hooks (`type: "agent"`)
Multi-turn subagent with Read/Grep/Glob tools. Same response format as prompt hooks.
- Up to 50 turns per evaluation
- Default timeout: 60s (vs 30s for prompt)
- Use for complex verification requiring file inspection

## Events That Can Block (exit 2)

| Event | What Gets Blocked |
|-------|-------------------|
| `PreToolUse` | Blocks the tool call |
| `PermissionRequest` | Denies the permission |
| `UserPromptSubmit` | Blocks prompt processing, erases prompt |
| `Stop` | **Prevents Claude from stopping** (continues conversation) |
| `SubagentStop` | Prevents subagent from stopping |
| `TeammateIdle` | Prevents teammate from going idle |
| `TaskCompleted` | Prevents task from being marked complete |
| `ConfigChange` | Blocks config change (except policy_settings) |

## Events That Cannot Block

| Event | What Happens on exit 2 |
|-------|------------------------|
| `PostToolUse` | Shows stderr to Claude (tool already ran) |
| `PostToolUseFailure` | Shows stderr to Claude |
| `Notification` | Shows stderr to user only |
| `SubagentStart` | Shows stderr to user only |
| `SessionStart` | Shows stderr to user only |
| `SessionEnd` | Shows stderr to user only |

## PreToolUse Decision Control (JSON Output)

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

- `"allow"`: bypass permission system
- `"deny"`: block tool call, reason shown to Claude
- `"ask"`: prompt user to confirm

## Stop Hook for Ralph Loops

**Critical Pattern**: Use Stop hooks to prevent Claude from finishing prematurely.

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/ralph-stop-gate.sh"
      }]
    }]
  }
}
```

The stop gate script checks if all tasks are done:
```bash
#!/bin/bash
INPUT=$(cat)
LAST_MSG=$(echo "$INPUT" | jq -r '.last_assistant_message')
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')

# Prevent infinite loop: if stop hook already active, let it stop
if [ "$STOP_ACTIVE" = "true" ]; then
  exit 0
fi

# Check if COMPLETE signal present
if echo "$LAST_MSG" | grep -qF '<promise>COMPLETE</promise>'; then
  exit 0  # Allow stop
fi

if echo "$LAST_MSG" | grep -qF '<promise>BLOCKED</promise>'; then
  exit 0  # Allow stop on block
fi

# Check if fix plan has unchecked tasks
FIX_PLAN=".ralph/@fix_plan.md"
if [ -f "$FIX_PLAN" ]; then
  UNCHECKED=$(grep -c '^\- \[ \]' "$FIX_PLAN" 2>/dev/null || echo "0")
  if [ "$UNCHECKED" -gt 0 ]; then
    echo "Still $UNCHECKED unchecked tasks in @fix_plan.md. Continue working." >&2
    exit 2  # Block stop — Claude continues
  fi
fi

exit 0
```

**Key Guard**: Always check `stop_hook_active` to prevent infinite loops!

## TaskCompleted Hook for Quality Gates

```bash
#!/bin/bash
INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject')

# Run verification suite
ERRORS=""

# Backend lint
if ! ruff check . 2>&1 >/dev/null; then
  ERRORS="${ERRORS}Ruff lint failures. "
fi

# Backend tests
if ! pytest tests/ -x --tb=no -q 2>&1 >/dev/null; then
  ERRORS="${ERRORS}Pytest failures. "
fi

# Frontend
if [ -d "frontend" ]; then
  if ! (cd frontend && npm run build) 2>&1 >/dev/null; then
    ERRORS="${ERRORS}Frontend build failures. "
  fi
fi

if [ -n "$ERRORS" ]; then
  echo "Cannot complete task '$TASK_SUBJECT': $ERRORS" >&2
  exit 2  # Block task completion
fi

exit 0
```

## TeammateIdle Hook for Agent Teams

Prevents teammates from going idle without completing work:

```bash
#!/bin/bash
INPUT=$(cat)
TEAMMATE=$(echo "$INPUT" | jq -r '.teammate_name')
TEAM=$(echo "$INPUT" | jq -r '.team_name')

# Check if teammate has in-progress tasks
# (Would need to inspect task list file)

exit 0  # Allow idle by default
```

## SubagentStart Hook for Context Injection

Inject project context into every subagent:

```json
{
  "hooks": {
    "SubagentStart": [{
      "hooks": [{
        "type": "command",
        "command": "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"SubagentStart\",\"additionalContext\":\"Follow CLAUDE.md conventions. Run tests after changes.\"}}'"
      }]
    }]
  }
}
```

## Hook Configuration Locations

| Location | Scope | Shareable |
|----------|-------|-----------|
| `~/.claude/settings.json` | All projects | No (local) |
| `.claude/settings.json` | Single project | Yes (committed) |
| `.claude/settings.local.json` | Single project | No (gitignored) |
| Plugin `hooks/hooks.json` | When plugin enabled | Yes |
| Skill/agent frontmatter | While component active | Yes |

## Environment Variables in Hooks

- `$CLAUDE_PROJECT_DIR`: project root (use in command paths)
- `$CLAUDE_ENV_FILE`: write `export` statements here in SessionStart hooks to persist env vars
- `$CLAUDE_CODE_REMOTE`: `"true"` in remote web environments

## Matcher Patterns

Matchers are regex strings:
- `"Bash"` — matches Bash tool
- `"Edit|Write"` — matches either
- `"mcp__memory__.*"` — matches all memory MCP tools
- `""` or omitted — matches everything

## Best Practices for Ralph Loops

1. **Always check `stop_hook_active`** in Stop hooks to prevent infinite loops
2. **Use exit 2 sparingly** — only for genuine blocking conditions
3. **Keep hooks fast** — SessionStart and PostToolUse hooks run frequently
4. **Use async hooks** for slow operations (test suites) that shouldn't block the agent
5. **Log to files** not stdout — stdout is parsed as JSON
6. **Use `$CLAUDE_PROJECT_DIR`** for portable script paths
7. **PreToolUse > PostToolUse** for blocking — you can't undo a completed tool call
8. **Agent hooks for complex checks** — when you need to read files to verify conditions
