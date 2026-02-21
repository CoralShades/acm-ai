# Agent Teams Patterns for Ralph Loops

Compiled 2026-02-22 from Claude Code docs and ralph-playbook patterns.

## Agent Teams Overview

Agent Teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) enable multi-agent coordination:
- **TeamCreate** creates team + shared task list
- **Task tool** with `team_name` spawns teammates
- **TaskCreate/TaskUpdate/TaskList** for shared task tracking
- **SendMessage** for inter-agent communication
- Teammates auto-go-idle between turns (normal behavior)

## Minimal Team Architecture for Ralph

### Option A: Single-Agent Loop (No Teams)

For simple stories, the Ralph loop itself (bash script spawning `claude -p`) is sufficient.
No teams needed. Each iteration gets fresh context, reads `@fix_plan.md`, implements next task.

**When to use**: Stories that touch one layer (backend-only or frontend-only).

### Option B: Lead + Specialist Team (Recommended for Mixed Stories)

```
Team Lead (orchestrator)
  ├── Task: "Implement backend changes" → backend-specialist agent
  ├── Task: "Implement frontend changes" → frontend-specialist agent
  └── Task: "Verify all acceptance criteria" → qa-specialist agent
```

**When to use**: Stories touching both backend and frontend, or requiring parallel work.

### Option C: Full Sprint Team (For Multi-Story Loops)

```
Sprint Lead (orchestrator, coordinates story lifecycle)
  ├── Per-Story Team (created/dissolved per story):
  │   ├── Developer (backend-specialist or frontend-specialist)
  │   ├── QA (qa-specialist — validates ACs)
  │   └── Documenter (docs-specialist — updates story files)
  └── Handover: sprint lead picks next story when team finishes
```

**When to use**: Ralph sprint runner processing multiple stories.

## Team Lead Responsibilities

1. **Story selection**: Read sprint-status.yaml, pick highest-priority ready-for-dev story
2. **Context setup**: Read story tech spec, understand scope (backend/frontend/both)
3. **Task creation**: Break story into tasks, create TaskCreate entries
4. **Delegation**: Assign tasks to specialists based on file paths
5. **Quality gate**: After all tasks complete, run verification suite
6. **Story finalization**: Update story file, sprint-status.yaml, commit
7. **Handover**: Pick next story and repeat

## Communication Patterns

### Direct Messages (Preferred)
```
SendMessage(type="message", recipient="backend-dev", content="...", summary="...")
```

### Broadcast (Expensive — Avoid)
```
SendMessage(type="broadcast", content="Critical: stop work, blocking issue found")
```

### Shutdown Request (End of Sprint)
```
SendMessage(type="shutdown_request", recipient="backend-dev", content="Sprint complete")
```

## Task Dependencies

```
TaskCreate(subject="Create API endpoint", description="...")  # task-1
TaskCreate(subject="Build UI component", description="...")    # task-2
TaskUpdate(taskId="task-2", addBlockedBy=["task-1"])           # frontend waits for backend
```

## Hook Integration with Teams

### TeammateIdle Hook
Fires when teammate finishes a turn. Use to enforce quality:
```bash
#!/bin/bash
# Prevent idle if tests failing
if ! npm test --silent 2>/dev/null; then
  echo "Tests failing. Fix before going idle." >&2
  exit 2
fi
exit 0
```

### TaskCompleted Hook
Fires when any agent marks a task complete. Use as quality gate:
```bash
#!/bin/bash
INPUT=$(cat)
TASK=$(echo "$INPUT" | jq -r '.task_subject')
# Run lint + test before allowing task completion
if ! ruff check . 2>&1 >/dev/null; then
  echo "Lint fails for task: $TASK" >&2
  exit 2
fi
exit 0
```

### SubagentStart Hook
Inject context into spawned agents:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "You are working on story E9-S3. Follow CLAUDE.md conventions."
  }
}
```

## Minimizing Agent Cost

### The Problem
Each agent in a team consumes API tokens independently. N agents = N parallel streams.

### Cost Control Strategies

1. **Sequential, not parallel**: For most stories, run backend then frontend sequentially (one agent at a time)
2. **Single-agent with subagent delegation**: Lead agent delegates specific file changes to short-lived subagents via Task tool
3. **Minimize team size**: 2-3 agents max for typical stories
4. **Haiku for simple tasks**: Use `model: "haiku"` for test runners, linters, doc updates
5. **Short-lived specialists**: Spawn specialist, get result, shut down. Don't keep idle agents.

### The Sweet Spot for ACM-AI

For most stories:
```
Lead Agent (orchestrator, opus or sonnet)
  └── Delegates via Task tool to:
      - backend-specialist (short-lived, per-task)
      - frontend-specialist (short-lived, per-task)
      - qa-specialist (short-lived, validation only)
```

This is NOT a persistent team — it's one lead agent spawning sub-agents as needed.
The Task tool handles this without TeamCreate overhead.

## Agent Discovery

Teammates read team config to find each other:
```
~/.claude/teams/{team-name}/config.json
```

Contains `members` array with `name`, `agentId`, `agentType`.
Always refer to teammates by NAME, not by UUID.

## Best Practices

1. **Prefer Task tool over TeamCreate** for simple delegation (less overhead)
2. **Use TeamCreate only** when agents need ongoing coordination across multiple tasks
3. **Don't over-parallelize** — sequential is often more reliable and debuggable
4. **Backend before frontend** — prevents frontend from depending on unbuilt APIs
5. **Single-responsibility tasks** — each agent gets one clear job
6. **Check TaskList after completing** — find newly unblocked work
7. **Prefer lowest ID first** — earlier tasks set up context for later ones
