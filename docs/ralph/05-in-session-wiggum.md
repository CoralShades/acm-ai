# Mode 3: In-Session Loop (Wiggum)

> Claude Code Stop hook as re-entrant loop mechanism. No external bash script needed.

## Overview

The Wiggum pattern runs a Ralph loop entirely inside a single Claude Code session by using a Stop hook to intercept exit attempts. When Claude tries to stop, the hook checks if work remains and feeds the same prompt back, creating an iterative loop without leaving the session.

**Named after**: Ralph Wiggum — the original technique by Geoffrey Huntley.

**Key property**: Accumulating context (unlike bash loop's fresh context). Each iteration builds on the previous one within the same conversation.

## Architecture

```
User runs /ralph-loop "task" --max-iterations 50 --completion-promise "COMPLETE"
  │
  ├── setup-ralph-loop.sh creates .claude/ralph-loop.local.md (state file)
  │
  └── Claude works on task → tries to stop
        │
        ├── Stop hook fires (stop-hook.sh)
        │   ├── Reads state file (iteration count, max, promise)
        │   ├── Reads transcript (JSONL) for last assistant message
        │   ├── Checks for <promise>COMPLETE</promise> in output
        │   │   ├── Found → rm state file, exit 0 (allow stop)
        │   │   └── Not found → output JSON blocking stop with same prompt
        │   └── Max iterations? → rm state file, exit 0
        │
        └── Claude receives prompt again → continues working
```

## State File Schema

File: `.claude/ralph-loop.local.md`

```markdown
---
iteration: 1
max_iterations: 50
completion_promise: "COMPLETE"
---
Your task prompt goes here.

Continue working on: build a REST API for todos.
Requirements: CRUD operations, input validation, tests.
Output <promise>COMPLETE</promise> when done.
```

### Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `iteration` | number | Current iteration count (auto-incremented by hook) |
| `max_iterations` | number | Stop after this many iterations (0 = infinite) |
| `completion_promise` | string | Text to detect in `<promise>` tags (null = no auto-detection) |

### Prompt Section
Everything after the closing `---` is the prompt text. Fed back to Claude on each loop iteration via the Stop hook's JSON output.

## Commands

### `/ralph-loop` — Start Loop
```
/ralph-loop "Build a REST API for todos. Output <promise>COMPLETE</promise> when done." --max-iterations 50 --completion-promise "COMPLETE"
```

Creates the state file and begins working. The Stop hook takes over from there.

### `/cancel-ralph` — Cancel Loop
Checks for and removes `.claude/ralph-loop.local.md`, reporting the final iteration count.

## Stop Hook Mechanics

### Transcript Parsing
The hook reads the JSONL transcript file to extract the last assistant message:

```bash
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')
LAST_LINE=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -1)
LAST_OUTPUT=$(echo "$LAST_LINE" | jq -r '
  .message.content |
  map(select(.type == "text")) |
  map(.text) |
  join("\n")
')
```

### Completion Detection
Uses Perl for robust `<promise>` tag extraction:
```bash
PROMISE_TEXT=$(echo "$LAST_OUTPUT" | perl -0777 -pe \
  's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g')

if [[ "$PROMISE_TEXT" = "$COMPLETION_PROMISE" ]]; then
    rm "$RALPH_STATE_FILE"
    exit 0  # Allow stop
fi
```

### Blocking Output
When work remains, the hook outputs JSON to block the stop:
```bash
jq -n \
  --arg prompt "$PROMPT_TEXT" \
  --arg msg "Ralph iteration $NEXT_ITERATION | To stop: output <promise>$COMPLETION_PROMISE</promise>" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $msg
  }'
```

### Iteration Counter
The hook atomically updates the iteration count in the state file:
```bash
NEXT_ITERATION=$((ITERATION + 1))
sed "s/^iteration: .*/iteration: $NEXT_ITERATION/" "$RALPH_STATE_FILE" > "${RALPH_STATE_FILE}.tmp.$$"
mv "${RALPH_STATE_FILE}.tmp.$$" "$RALPH_STATE_FILE"
```

## Differences from Bash Loop

| Aspect | Bash Loop | Wiggum (In-Session) |
|--------|-----------|---------------------|
| Context | Fresh each iteration | Accumulating (same session) |
| State mechanism | Files only (prd.json, @fix_plan.md) | Files + conversation history |
| Process model | External script spawns `claude -p` | Stop hook blocks exit |
| Dependencies | bash, jq, claude CLI | claude CLI + Stop hook |
| Memory usage | Low (fresh process each time) | Grows with iterations |
| Best for | Long multi-story sprints | Single-task focused loops |
| Context pollution | None (fresh start) | Possible (context grows) |
| Speed | Slower (process startup per iteration) | Faster (no process overhead) |
| Observable | Yes (separate log files per iteration) | Harder (one continuous session) |
| Recovery | Resume from any iteration | Must restart from beginning |

## When to Use Wiggum

**Good for**:
- Single focused tasks ("build this feature", "fix this bug")
- Tasks where context accumulation is beneficial
- Quick iterations where process startup overhead matters
- Environments where bash scripting is limited

**Not good for**:
- Multi-story sprints (context grows too large)
- Tasks requiring more than ~20 iterations (context window fills)
- Situations needing per-iteration logs
- Production autonomous loops (bash loop is more robust)

## Plugin Structure

```
.claude/plugins/ralph-wiggum/
├── .claude-plugin/plugin.json    # Plugin metadata
├── commands/
│   ├── ralph-loop.md             # Start command
│   ├── cancel-ralph.md           # Cancel command
│   └── help.md                   # Help text
├── hooks/
│   ├── hooks.json                # Hook registration (Stop event)
│   └── stop-hook.sh              # Core loop logic
├── scripts/
│   └── setup-ralph-loop.sh       # State file creator
└── README.md
```

## Error Handling

The stop hook handles these error cases:
- **Corrupted state file**: Non-numeric iteration/max_iterations → cleanup and stop
- **Missing transcript**: File not found → cleanup and stop
- **No assistant messages**: Empty transcript → cleanup and stop
- **JSON parse failure**: jq error → cleanup and stop
- **Empty prompt**: No text after frontmatter → cleanup and stop

All errors: remove state file (stops the loop) and output warning to stderr.

## Combining with Bash Loop

Wiggum can bootstrap then hand off:
1. Run `/ralph-loop` to do initial exploration/planning
2. Wiggum accumulates context about the codebase
3. Save findings to `progress.txt` or `@fix_plan.md`
4. Cancel the Wiggum loop
5. Switch to bash loop for production implementation (fresh context, better observability)
