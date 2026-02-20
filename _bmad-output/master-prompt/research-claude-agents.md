# Claude Code Agent Systems: Comprehensive Research Documentation

**Research Date:** 2026-02-11  
**Claude Code Version:** Latest (2026)  
**Status:** Agent Teams are Experimental (requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

---

## Table of Contents

1. [Overview](#overview)
2. [Agent Teams (Experimental)](#agent-teams-experimental)
3. [Sub-Agents (Stable)](#sub-agents-stable)
4. [Skills System](#skills-system)
5. [Planning-with-Files Pattern](#planning-with-files-pattern)
6. [Model Selection Guide](#model-selection-guide)
7. [Global Agents Reference](#global-agents-reference)
8. [Best Practices](#best-practices)

---

## Overview

Claude Code offers three complementary systems for delegation and coordination:

| System | Scope | Communication | Best For |
|--------|-------|---------------|----------|
| **Agent Teams** | Multiple sessions | Direct messaging, shared task list | Parallel exploration, research, competing hypotheses |
| **Sub-Agents** | Single session | Report back to parent | Focused tasks, isolation, context preservation |
| **Skills** | Same context | N/A (runs inline) | Reusable workflows, domain knowledge, conventions |

**Key Decision Framework:**
- Use **Agent Teams** when workers need to communicate with each other
- Use **Sub-Agents** when you need isolated context but only the result matters
- Use **Skills** for reusable prompts or domain knowledge that runs inline

---

## Agent Teams (Experimental)

Agent teams coordinate multiple Claude Code instances working together with shared tasks, inter-agent messaging, and centralized management.

### 1. Enabling Agent Teams

**Via settings.json:**
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

**Via environment variable:**
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

### 2. Architecture

```
~/.claude/teams/{team-name}/
├── config.json              # Team metadata + members
└── inboxes/
    ├── team-lead.json       # Leader's inbox
    ├── worker-1.json        # Teammate 1 inbox
    └── worker-2.json        # Teammate 2 inbox

~/.claude/tasks/{team-name}/
├── 1.json                   # Task with id, subject, status, owner, blockedBy
├── 2.json
└── 3.json
```

**Components:**
- **Team Lead**: Main session that creates team, spawns teammates, coordinates work
- **Teammates**: Separate Claude Code instances with independent context windows
- **Task List**: Shared work items with status tracking and dependencies
- **Mailbox**: Messaging system for inter-agent communication

### 3. Creating Teams with TeamCreate

**Natural Language Approach:**
```
Create an agent team with 3 teammates to explore this problem:
- One focused on security
- One on performance
- One playing devil's advocate
```

**Programmatic Approach (TeammateTool):**
```
Teammate({ 
  operation: "spawnTeam", 
  team_name: "my-project" 
})
```

This creates:
- Team directory at `~/.claude/teams/my-project/`
- Leader automatically becomes first member
- Empty task list at `~/.claude/tasks/my-project/`

### 4. Spawning Teammates with Task Tool

**Two Methods:**

#### Method 1: Short-lived Subagent (No team membership)
```
Task({
  subagent_type: "Explore",
  description: "Find authentication files",
  prompt: "Search for auth-related code...",
  model: "haiku",
  run_in_background: false
})
```
Returns result directly; no shared context.

#### Method 2: Persistent Teammate (Team member)
```
Task({
  team_name: "my-project",
  name: "security-reviewer",
  subagent_type: "general-purpose",
  prompt: "Review security vulnerabilities and report findings...",
  model: "sonnet",
  run_in_background: true
})
```

**Parameters:**
- `team_name` (required for teammates): Team to join
- `name` (required for teammates): Unique teammate identifier
- `subagent_type` (required): Agent type (see Built-in Agent Types)
- `prompt` (required): Initial instructions
- `model` (optional): `haiku`, `sonnet`, `opus`, or `inherit` (default: `inherit`)
- `run_in_background` (optional): Async execution (default: `false`)
- `resume` (optional): Continue existing agent by ID

**Environment Variables (Passed to Teammates):**
```bash
CLAUDE_CODE_TEAM_NAME="my-project"
CLAUDE_CODE_AGENT_ID="worker-1@my-project"
CLAUDE_CODE_AGENT_NAME="worker-1"
CLAUDE_CODE_AGENT_TYPE="Explore"
CLAUDE_CODE_AGENT_COLOR="#4A90D9"
CLAUDE_CODE_PLAN_MODE_REQUIRED="false"
CLAUDE_CODE_PARENT_SESSION_ID="session-xyz"
```

### 5. Built-in Agent Types (subagent_type)

| Type | Model | Tools | Best For |
|------|-------|-------|----------|
| `Explore` | Haiku | Read-only (Read, Grep, Glob) | Fast codebase searching, analysis |
| `Plan` | Inherit | Read-only | Architecture planning, read-only research |
| `general-purpose` | Inherit | All tools | Multi-step tasks requiring modification |
| `Bash` | Inherit | Bash only | Git operations, CLI tasks |
| `claude-code-guide` | Haiku | Read, WebFetch, WebSearch | Claude Code questions |

**Custom Agent Types:**
- Located in `~/.claude/agents/` (user-level) or `.claude/agents/` (project-level)
- See [Global Agents Reference](#global-agents-reference) for examples

**Plugin Agent Types:**
Use format `plugin-name:category:agent-name`, e.g.:
```
subagent_type: "compound-engineering:review:security-sentinel"
```

### 6. SendMessage: Inter-Agent Communication

**Message Types:**

#### Regular Message (Direct Communication)
```
Teammate({
  operation: "write",
  target_agent_id: "worker-1",
  value: "Please review the authentication module"
})
```

#### Broadcast (Send to All - Use Sparingly)
```
Teammate({
  operation: "broadcast",
  value: "Team: We're shifting focus to performance"
})
```

**Structured Message Types (JSON in text field):**

1. **shutdown_request** - Leader requests teammate exit
```json
{
  "type": "shutdown_request",
  "requestId": "shutdown-123@worker",
  "from": "team-lead",
  "reason": "Tasks complete"
}
```

2. **shutdown_response** - Teammate approves/rejects
```json
{
  "type": "shutdown_approved",
  "from": "worker-1",
  "requestId": "shutdown-123@worker"
}
```

3. **plan_approval_request** - Teammate submits plan
```json
{
  "type": "plan_approval_request",
  "from": "architect",
  "requestId": "plan-xyz",
  "planContent": "# Implementation Plan..."
}
```

4. **plan_approval_response** - Leader approves/rejects
```json
{
  "type": "plan_approved",
  "from": "team-lead",
  "requestId": "plan-xyz"
}
```

5. **join_request** - New agent requests to join
```json
{
  "type": "join_request",
  "proposedName": "helper",
  "requestId": "join-abc",
  "capabilities": "Code review"
}
```

6. **task_completed** - Worker notifies completion
```json
{
  "type": "task_completed",
  "from": "worker-1",
  "taskId": "2",
  "taskSubject": "Review authentication"
}
```

7. **idle_notification** - Auto-sent when teammate stops
```json
{
  "type": "idle_notification",
  "from": "worker-1",
  "completedTaskId": "2",
  "completedStatus": "completed"
}
```

### 7. Task Management (TaskCreate/Update/List/Get)

#### TaskCreate
```
TaskCreate({
  subject: "Review authentication module",
  description: "Check app/services/auth/ for vulnerabilities",
  activeForm: "Reviewing security..."
})
```

Returns task ID (e.g., "1").

#### TaskList
```
TaskList()
```

Output format:
```
#1 [completed] Research auth patterns (owner: researcher)
#2 [in_progress] Implement auth service (owner: dev-1)
#3 [pending] Write tests (blocked by #2)
```

#### TaskGet
```
TaskGet({ taskId: "2" })
```

Returns full task details including status, owner, dependencies.

#### TaskUpdate

**Claim a task:**
```
TaskUpdate({ 
  taskId: "2", 
  owner: "worker-1" 
})
```

**Start work:**
```
TaskUpdate({ 
  taskId: "2", 
  status: "in_progress" 
})
```

**Complete task:**
```
TaskUpdate({ 
  taskId: "2", 
  status: "completed" 
})
```

**Add dependencies:**
```
TaskUpdate({ 
  taskId: "3", 
  addBlockedBy: ["1", "2"]  # Task 3 waits for 1 and 2
})
```

```
TaskUpdate({ 
  taskId: "1", 
  addBlocks: ["3"]  # Task 1 blocks task 3
})
```

**Task States:**
- `pending`: Not started, may have unresolved dependencies
- `in_progress`: Actively being worked on
- `completed`: Finished
- `deleted`: Removed from active work

**Automatic Unblocking:**
When all blocking tasks complete, dependent tasks automatically unblock.

### 8. Task Dependencies & Workflow Patterns

#### Pattern 1: Pipeline (Sequential)
```
TaskCreate({ subject: "Research API patterns" })      # Task 1
TaskCreate({ subject: "Design API endpoints" })       # Task 2
TaskCreate({ subject: "Implement API" })              # Task 3
TaskCreate({ subject: "Write API tests" })            # Task 4

TaskUpdate({ taskId: "2", addBlockedBy: ["1"] })
TaskUpdate({ taskId: "3", addBlockedBy: ["2"] })
TaskUpdate({ taskId: "4", addBlockedBy: ["3"] })

# Creates: 1 → 2 → 3 → 4 (auto-progression)
```

#### Pattern 2: Parallel with Convergence
```
TaskCreate({ subject: "Frontend implementation" })    # Task 1
TaskCreate({ subject: "Backend API" })                # Task 2
TaskCreate({ subject: "Integration tests" })          # Task 3

TaskUpdate({ taskId: "3", addBlockedBy: ["1", "2"] })

# Creates: [1, 2] → 3 (both must complete before 3 starts)
```

#### Pattern 3: Self-Organizing Swarm
```
# Leader creates many independent tasks
for file in src/**/*.ts:
  TaskCreate({ subject: f"Review {file}" })

# Spawn N workers with this logic:
# 1. TaskList() → find pending, unowned task
# 2. TaskUpdate to claim (set owner)
# 3. Do work
# 4. TaskUpdate to complete
# 5. Send results via SendMessage
# 6. Repeat until no tasks
```

### 9. Team Coordination Patterns

#### Parallel Specialists
```
Teammate({ operation: "spawnTeam", team_name: "code-review" })

Task({
  team_name: "code-review",
  name: "security",
  subagent_type: "security-sentinel",
  prompt: "Review for vulnerabilities. Send findings to team-lead when complete.",
  run_in_background: true
})

Task({
  team_name: "code-review",
  name: "performance",
  subagent_type: "performance-oracle",
  prompt: "Check for bottlenecks. Send findings to team-lead when complete.",
  run_in_background: true
})

# Both run concurrently; leader synthesizes results
```

#### Competing Hypotheses (Adversarial)
```
Spawn 5 agent teammates to investigate different hypotheses for why
the app exits after one message. Have them debate each other to try 
to disprove competing theories. Update findings.md with consensus.
```

Key: Teammates actively challenge each other's findings.

#### Plan Approval Workflow
```
Task({
  team_name: "careful-work",
  name: "architect",
  subagent_type: "Plan",
  prompt: "Design authentication system architecture...",
  mode: "plan",  # Requires approval before implementation
  run_in_background: true
})

# Receive plan_approval_request in leader's inbox
# Review plan content, then:

Teammate({
  operation: "approvePlan",
  target_agent_id: "architect",
  request_id: "plan-xxx"
})

# Or reject with feedback:
Teammate({
  operation: "rejectPlan",
  target_agent_id: "architect",
  request_id: "plan-xxx",
  feedback: "Missing security considerations"
})
```

### 10. Delegate Mode

Restricts leader to coordination-only tools (no code implementation). Prevents leader from doing work instead of delegating.

**Enable:** Press `Shift+Tab` after team creation.

**Tools Available in Delegate Mode:**
- Teammate (spawn, message, shutdown)
- TaskCreate, TaskUpdate, TaskList, TaskGet
- SendMessage
- (No Read, Write, Edit, Bash for implementation)

**Use When:**
- You want leader focused on orchestration only
- Breaking down work, assigning tasks, synthesizing results
- Leader tends to implement instead of waiting for teammates

### 11. Reading Team Config

**Location:** `~/.claude/teams/{team-name}/config.json`

**Structure:**
```json
{
  "name": "my-project",
  "createdAt": "2026-02-11T12:00:00Z",
  "members": [
    {
      "name": "team-lead",
      "agentId": "lead@my-project",
      "agentType": "general-purpose"
    },
    {
      "name": "security-reviewer",
      "agentId": "security@my-project",
      "agentType": "security-sentinel"
    }
  ]
}
```

**Read from code:**
```bash
cat ~/.claude/teams/my-project/config.json | jq '.members[] | {name, agentType}'
```

Teammates can read this file to discover other team members.

### 12. Shutdown & Cleanup

**Graceful Shutdown Sequence:**

1. Request shutdown for each teammate:
```
Teammate({ 
  operation: "requestShutdown", 
  target_agent_id: "worker-1" 
})
```

2. Wait for approval (monitor inbox for `shutdown_approved`)

3. Verify no active members:
```bash
cat ~/.claude/teams/my-project/config.json | jq '.members | length'
```

4. Clean up team:
```
Teammate({ 
  operation: "cleanup" 
})
```

**Important:**
- Always cleanup through leader (not teammates)
- Cleanup fails if any teammates still active
- Removes team directories and task files

### 13. Display Modes

**In-Process (Default for terminals without tmux):**
- All teammates run inside main terminal
- `Shift+Up/Down` to select teammate
- Type to message selected teammate
- `Enter` to view session, `Escape` to interrupt
- `Ctrl+T` to toggle task list

**Split Panes (Auto-enabled in tmux sessions):**
- Each teammate gets own pane
- Click pane to interact directly
- Requires: tmux or iTerm2 with `it2` CLI

**Force mode:**
```bash
claude --teammate-mode in-process
```

**Set default in settings.json:**
```json
{
  "teammateMode": "in-process"  # or "tmux"
}
```

### 14. Limitations & Known Issues

- **No session resumption with in-process teammates**: `/resume` doesn't restore teammates
- **Task status can lag**: Teammates may fail to mark tasks complete
- **Shutdown can be slow**: Teammates finish current action before exiting
- **One team per session**: Must cleanup before starting new team
- **No nested teams**: Teammates cannot spawn their own teams
- **Lead is fixed**: Cannot transfer leadership
- **Permissions set at spawn**: All teammates inherit leader's permissions
- **Split panes require tmux or iTerm2**: Not supported in VS Code terminal, Windows Terminal, Ghostty

---

## Sub-Agents (Stable)

Sub-agents are specialized AI assistants that handle specific tasks within a single session. They run in isolated context and report results back to the main conversation.

### 1. When to Use Sub-Agents vs Agent Teams

| Criteria | Sub-Agents | Agent Teams |
|----------|------------|-------------|
| Context | Own context window | Own context window |
| Communication | Report to parent only | Message each other directly |
| Coordination | Parent manages all work | Shared task list, self-coordination |
| Token Cost | Lower (results summarized) | Higher (each is separate instance) |
| Best For | Focused tasks, only result matters | Complex work requiring discussion |

**Decision Guide:**
- Sub-agents: Quick, focused workers (e.g., "run tests and report failures")
- Agent Teams: Workers need to share findings, challenge each other, coordinate

### 2. Creating Sub-Agents

**Via /agents Command (Interactive):**
```
/agents
→ Create new agent
→ Choose scope: User-level (~/.claude/agents/) or Project-level (.claude/agents/)
→ Generate with Claude or write manually
→ Select tools (e.g., Read-only, All tools)
→ Select model (haiku, sonnet, opus, inherit)
→ Choose color
→ Save
```

**Via File (Manual):**
```markdown
---
name: code-reviewer
description: Expert code reviewer. Use after code changes for quality checks.
tools: Read, Grep, Glob, Bash
model: sonnet
maxTurns: 15
permissionMode: default
---

You are a senior code reviewer. When invoked:

1. Run git diff to see recent changes
2. Focus on modified files
3. Check for:
   - Code clarity and readability
   - Proper error handling
   - Security issues (exposed secrets, input validation)
   - Test coverage
   - Performance considerations

Provide feedback organized by priority:
- **Critical**: Must fix before merge
- **Warnings**: Should fix
- **Suggestions**: Consider improving
```

**Location Priority:**
1. `--agents` CLI flag (highest, session-only)
2. `.claude/agents/` (project-specific)
3. `~/.claude/agents/` (user-level, all projects)
4. Plugin `agents/` directory (lowest, where plugin enabled)

### 3. Sub-Agent Configuration (Frontmatter)

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase, hyphens) |
| `description` | Yes | When Claude should delegate to this sub-agent |
| `tools` | No | Allowlist of tools (inherits all if omitted) |
| `disallowedTools` | No | Denylist of tools |
| `model` | No | `sonnet`, `opus`, `haiku`, `inherit` (default: `inherit`) |
| `permissionMode` | No | `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | No | Max agentic turns before stopping |
| `skills` | No | Skills to preload into context |
| `mcpServers` | No | MCP servers available to sub-agent |
| `hooks` | No | Lifecycle hooks |
| `memory` | No | Persistent memory scope: `user`, `project`, `local` |

### 4. Invoking Sub-Agents

**Automatic Delegation:**
Claude automatically delegates based on task description and sub-agent's `description` field.

**Explicit Invocation:**
```
Use the code-reviewer subagent to review my recent changes
Have the test-runner subagent fix failing tests
```

**Programmatic (Task Tool):**
```
Task({
  subagent_type: "code-reviewer",
  prompt: "Review authentication module for security issues"
})
```

### 5. Foreground vs Background Execution

**Foreground (Default):**
- Blocks main conversation until complete
- Permission prompts passed through to you
- Can ask clarifying questions (AskUserQuestion)

**Background:**
- Runs concurrently with main conversation
- Pre-approval for needed permissions
- Auto-denies unapproved tools
- Cannot ask clarifying questions (call fails)
- MCP tools not available

**Request background:**
```
Run this in the background: use test-runner to fix failing tests
```

Or press `Ctrl+B` to background a running task.

**Disable all background tasks:**
```bash
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1
```

### 6. Resuming Sub-Agents

Each sub-agent invocation creates a new instance by default. To continue existing work:

```
Use the code-reviewer subagent to review authentication module
[Agent completes]

Continue that code review and now analyze authorization logic
[Claude resumes the subagent with full context]
```

**How it works:**
- Each sub-agent transcript saved to `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`
- Resume reloads full conversation history
- Transcripts persist across main conversation compaction
- Auto-cleanup after 30 days (configurable via `cleanupPeriodDays`)

### 7. Sub-Agent Tools Restriction

**Allowlist (tools):**
```yaml
tools: Read, Grep, Glob, Bash
```

**Denylist (disallowedTools):**
```yaml
tools: Read, Write, Edit, Bash
disallowedTools: Write, Edit
```
Result: Only Read, Bash available.

**Restrict Task spawning:**
```yaml
tools: Task(worker, researcher), Read, Bash
```
Sub-agent can only spawn `worker` and `researcher` types.

**Allow any Task spawning:**
```yaml
tools: Task, Read, Bash
```

### 8. Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Standard permission prompts |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Auto-deny all prompts (explicit allows still work) |
| `delegate` | Team lead coordination-only mode |
| `bypassPermissions` | Skip all permission checks (use with caution) |
| `plan` | Plan mode (read-only exploration) |

**Note:** If parent uses `bypassPermissions`, it overrides sub-agent settings.

### 9. Persistent Memory for Sub-Agents

Enable cross-session learning:

```yaml
---
name: code-reviewer
memory: user
---

You are a code reviewer. As you review code, update your agent memory with
patterns, conventions, and recurring issues you discover.
```

**Scopes:**

| Scope | Location | Use When |
|-------|----------|----------|
| `user` | `~/.claude/agent-memory/<name>/` | Knowledge applies across all projects |
| `project` | `.claude/agent-memory/<name>/` | Project-specific, shareable via git |
| `local` | `.claude/agent-memory-local/<name>/` | Project-specific, not in git |

**How it works:**
- System prompt includes instructions for reading/writing memory directory
- First 200 lines of `MEMORY.md` loaded into context
- Read, Write, Edit tools auto-enabled
- Curate `MEMORY.md` if it exceeds 200 lines

**Best Practice:**
```
Review this PR and check your memory for patterns you've seen before.
[After review]
Now save what you learned to your memory.
```

### 10. Preloading Skills into Sub-Agents

```yaml
---
name: api-developer
description: Implement API endpoints following team conventions
skills:
  - api-conventions
  - error-handling-patterns
---

Implement API endpoints. Follow the conventions from the preloaded skills.
```

**How it works:**
- Full skill content injected into sub-agent context at startup
- Sub-agents don't inherit skills from parent
- Must list explicitly

**Inverse Pattern:** See Skills → `context: fork` for comparison.

### 11. Hooks for Sub-Agents

**In Sub-Agent Frontmatter:**
```yaml
---
name: db-reader
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
  Stop:
    - hooks:
        - type: command
          command: "./scripts/cleanup.sh"
---
```

**Project-Level (settings.json):**
```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [
          { "type": "command", "command": "./scripts/setup-db.sh" }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/cleanup-db.sh" }
        ]
      }
    ]
  }
}
```

### 12. Disabling Specific Sub-Agents

**Via settings.json:**
```json
{
  "permissions": {
    "deny": ["Task(Explore)", "Task(my-custom-agent)"]
  }
}
```

**Via CLI:**
```bash
claude --disallowedTools "Task(Explore)"
```

### 13. Sub-Agent Auto-Compaction

Sub-agents support auto-compaction at ~95% context capacity (default).

**Override trigger threshold:**
```bash
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50  # Compact at 50%
```

**Logged in transcript:**
```json
{
  "type": "system",
  "subtype": "compact_boundary",
  "compactMetadata": {
    "trigger": "auto",
    "preTokens": 167189
  }
}
```

---

## Skills System

Skills extend Claude's capabilities through custom instructions, slash commands, and workflows.

### 1. Skills vs Commands vs Sub-Agents

| Feature | Skills | Sub-Agents |
|---------|--------|------------|
| Context | Inline (same context) | Forked (isolated context) |
| Invocation | `/skill-name` or auto | Task tool or auto-delegation |
| Purpose | Reusable workflows, domain knowledge | Task-specific isolation |
| Files | Directory with SKILL.md + supporting files | Single .md file with frontmatter |

**Decision Guide:**
- Skills: Reusable prompts, conventions, inline workflows
- Sub-Agents: Isolated work that returns summarized results

### 2. Skill File Structure

```
my-skill/
├── SKILL.md           # Main instructions (required)
├── template.md        # Template for Claude to fill in
├── examples/
│   └── sample.md      # Example output
└── scripts/
    └── helper.py      # Executable script
```

**SKILL.md Format:**
```markdown
---
name: explain-code
description: Explains code with visual diagrams and analogies
argument-hint: [filename]
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Bash
model: sonnet
context: inline
---

When explaining code, always include:

1. **Analogy**: Compare to something from everyday life
2. **Diagram**: ASCII art showing flow/structure
3. **Walkthrough**: Step-by-step explanation
4. **Gotcha**: Common mistake or misconception
```

### 3. Skill Locations & Priority

| Location | Path | Scope | Priority |
|----------|------|-------|----------|
| Enterprise | Managed settings | Organization | 1 (highest) |
| Personal | `~/.claude/skills/` | All your projects | 2 |
| Project | `.claude/skills/` | Current project | 3 |
| Plugin | `<plugin>/skills/` | Where enabled | 4 (namespaced) |

**Automatic Discovery:**
- Skills in nested `.claude/skills/` directories discovered automatically
- Supports monorepos with per-package skills
- Files from `--add-dir` also loaded (with live change detection)

### 4. Skill Frontmatter Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Display name (defaults to directory name) |
| `description` | Recommended | When to use (Claude decides based on this) |
| `argument-hint` | No | Autocomplete hint, e.g., `[issue-number]` |
| `disable-model-invocation` | No | If `true`, only user can invoke (not Claude) |
| `user-invocable` | No | If `false`, hidden from `/` menu |
| `allowed-tools` | No | Tools Claude can use without asking |
| `model` | No | Model to use when skill active |
| `context` | No | Set to `fork` to run in subagent |
| `agent` | No | Which subagent type for `context: fork` |
| `hooks` | No | Lifecycle hooks scoped to skill |

### 5. String Substitutions in Skills

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed to skill |
| `$ARGUMENTS[N]` | Specific argument by index (0-based) |
| `$N` | Shorthand for `$ARGUMENTS[N]` |
| `${CLAUDE_SESSION_ID}` | Current session ID |

**Example:**
```markdown
---
name: fix-issue
description: Fix a GitHub issue
---

Fix GitHub issue $ARGUMENTS following our standards:

1. Read issue $0 description
2. Implement fix
3. Write tests
4. Create commit
```

**Usage:**
```
/fix-issue 123
```
Result: "Fix GitHub issue 123..."

### 6. Control Who Invokes Skills

| Frontmatter | You Invoke | Claude Invokes | Context Loading |
|-------------|-----------|----------------|-----------------|
| (default) | Yes | Yes | Description always in context |
| `disable-model-invocation: true` | Yes | No | Description NOT in context |
| `user-invocable: false` | No | Yes | Description always in context |

**Use Cases:**
- `disable-model-invocation: true`: Side effects (deploy, commit, send-slack-message)
- `user-invocable: false`: Background knowledge (legacy-system-context)

### 7. Dynamic Context Injection

**Syntax:** `` !`command` ``

Runs shell command before sending to Claude; output replaces placeholder.

**Example:**
```markdown
---
name: pr-summary
context: fork
agent: Explore
---

## Pull Request Context
- Diff: !`gh pr diff`
- Comments: !`gh pr view --comments`
- Files: !`gh pr diff --name-only`

## Task
Summarize this PR...
```

**Flow:**
1. Commands execute immediately
2. Output replaces `` !`command` ``
3. Claude receives fully-rendered prompt with actual data

### 8. Running Skills in Sub-Agents (context: fork)

```markdown
---
name: deep-research
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:

1. Find relevant files using Glob and Grep
2. Read and analyze code
3. Summarize findings with file references
```

**How it works:**
- Skill content becomes the task prompt
- `agent` field determines execution environment
- New isolated context created
- Results returned to main conversation

**Agent Options:**
- Built-in: `Explore`, `Plan`, `general-purpose`
- Custom: Any from `.claude/agents/`
- Default (if omitted): `general-purpose`

**Comparison:**

| Approach | System Prompt | Task | Also Loads |
|----------|---------------|------|------------|
| Skill `context: fork` | From agent type | SKILL.md content | CLAUDE.md |
| Subagent `skills` field | Subagent markdown | Delegation message | Preloaded skills + CLAUDE.md |

### 9. Restricting Claude's Skill Access

**Disable all skills:**
```
/permissions
→ Add to deny: Skill
```

**Allow/deny specific skills:**
```json
{
  "permissions": {
    "allow": ["Skill(commit)", "Skill(review-pr *)"],
    "deny": ["Skill(deploy *)"]
  }
}
```

Syntax: `Skill(name)` for exact match, `Skill(name *)` for prefix match.

**Hide from Claude (frontmatter):**
```yaml
disable-model-invocation: true
```

### 10. Example: Visual Output Skill

Generate interactive HTML codebase explorer:

**Directory Structure:**
```
~/.claude/skills/codebase-visualizer/
├── SKILL.md
└── scripts/
    └── visualize.py
```

**SKILL.md:**
````markdown
---
name: codebase-visualizer
description: Generate interactive tree visualization of codebase
allowed-tools: Bash(python *)
---

Generate an interactive HTML tree view:

```bash
python ~/.claude/skills/codebase-visualizer/scripts/visualize.py .
```

This creates `codebase-map.html` with:
- Collapsible directories
- File sizes
- Color-coded file types
- Directory totals
````

**visualize.py:** (See full script in official docs)
- Scans directory tree
- Generates self-contained HTML with sidebar summary
- Bar chart by file type
- Collapsible tree with color indicators
- Opens in browser automatically

**Usage:**
```
Visualize this codebase
```

Claude runs script, generates HTML, opens in browser.

---

## Planning-with-Files Pattern

Persistent markdown planning for complex, multi-step tasks.

### 1. The 3-File System

| File | Purpose | Content |
|------|---------|---------|
| `task_plan.md` | Decision anchor | Phases, checkpoints, progress checkboxes |
| `findings.md` | Knowledge accumulator | Research, discoveries, key information |
| `progress.md` | Error log | Session log, attempts, test results, errors |

**Core Principle:**
```
Context Window = RAM (volatile, limited)
Filesystem = Disk (persistent, unlimited)
→ Anything important gets written to disk
```

### 2. The 2-Action Rule

**"Save findings after every 2 view/browser operations."**

This prevents context loss by ensuring discoveries don't evaporate when the conversation window resets.

**Pattern:**
1. View/search operation
2. View/search operation
3. **Update findings.md** ← MANDATORY
4. Continue...

### 3. Workflow Steps

1. **Create plan first** (never start without `task_plan.md`)
2. **Update findings** after completing research chunks
3. **Log all errors immediately** to `progress.md`
4. **Re-read the plan** before pivotal decisions
5. **Verify completion** before stopping

### 4. File Formats

**task_plan.md:**
```markdown
# Task Plan: [Task Name]

## Phase 1: Research
- [x] Analyze existing auth system
- [x] Research OAuth best practices
- [ ] Review security requirements

## Phase 2: Implementation
- [ ] Create auth service
- [ ] Add OAuth endpoints
- [ ] Implement token validation

## Phase 3: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Security audit
```

**findings.md:**
```markdown
# Findings: [Task Name]

## Authentication System Analysis
- Current system uses JWT tokens stored in localStorage
- Token expiry: 24 hours
- Location: `src/services/auth.ts`
- Security concern: XSS vulnerability with localStorage

## OAuth Research
- Recommendation: Use Authorization Code flow with PKCE
- Library: `@auth0/auth0-spa-js`
- Storage: httpOnly cookies instead of localStorage
```

**progress.md:**
```markdown
# Progress Log: [Task Name]

## 2026-02-11 - Session 1

### 14:30 - Started research phase
- Analyzed `src/services/auth.ts`
- Found JWT implementation

### 14:45 - Test failed
Error: `TypeError: Cannot read property 'token' of undefined`
Location: `src/services/auth.ts:42`
Cause: Missing null check for expired tokens
Fix: Added null guard

### 15:00 - Phase 1 complete
All research checkboxes marked complete in task_plan.md
```

### 5. When to Deploy

**Use for:**
- Multi-step tasks (3+ steps)
- Research projects
- Building/creating work
- Anything spanning many tool calls

**Skip for:**
- Simple questions
- Single-file edits
- Quick lookups

### 6. Implementation as Skill

```markdown
---
name: plan
description: Start complex multi-step task with persistent planning files
disable-model-invocation: true
---

Create persistent planning files for complex task: $ARGUMENTS

1. Create task_plan.md with phases and checkboxes
2. Create findings.md for research
3. Create progress.md for session log
4. Follow 2-action rule: update findings after every 2 view/browser operations
5. Re-read task_plan.md before major decisions
6. Log all errors immediately to progress.md
```

---

## Model Selection Guide

### 1. Available Models

| Model | Speed | Cost | Context | Best For |
|-------|-------|------|---------|----------|
| `haiku` | Fastest | Lowest | 200K | Search, exploration, read-only tasks |
| `sonnet` | Fast | Medium | 200K | Most tasks, good balance |
| `opus` | Slower | Highest | 200K | Complex reasoning, novel problems |
| `inherit` | - | - | - | Use same model as parent conversation |

### 2. When to Use Each Model

**Haiku:**
- Fast codebase searches
- Read-only exploration
- Simple transformations
- High-volume tasks (many iterations)
- Cost-sensitive operations

**Sonnet (Default Recommendation):**
- Most development tasks
- Well-documented codebase areas
- Standard implementations following patterns
- Code review
- Testing
- Refactoring

**Opus:**
- Complex architectural decisions
- Undocumented/novel problem areas
- Deep reasoning required
- Cross-cutting concerns
- Novel problem-solving
- High-stakes decisions

**Inherit:**
- When consistency with parent matters
- Delegate but maintain same capability level

### 3. Model Selection in Different Contexts

**Sub-Agents:**
```yaml
---
name: code-reviewer
model: sonnet  # Explicit model
---
```

**Task Tool (Teammates):**
```
Task({
  team_name: "my-project",
  name: "researcher",
  subagent_type: "Explore",
  model: "haiku",  # Fast, cheap for search
  prompt: "Find all authentication files..."
})
```

**Skills:**
```yaml
---
name: deep-analysis
model: opus  # Complex reasoning needed
---
```

### 4. Cost Considerations

**Agent Teams:**
Token usage scales with number of teammates. Each teammate is a separate Claude instance with own context window.

**Sub-Agents:**
Lower cost - results summarized back to main context. Only the summary consumes parent tokens.

**Recommendation:**
- Start with `sonnet` for most work
- Use `haiku` for exploration/search-heavy tasks
- Escalate to `opus` when encountering complex/undocumented areas
- Monitor token usage in agent teams (can get expensive fast)

---

## Global Agents Reference

Located in `~/.claude/agents/` on your system. Available across all projects.

### 1. Built-in Global Agents

**architect.md**
```yaml
name: architect
description: Software architecture agent for analysis and design
tools: [Read, Glob, Grep, Bash, WebSearch]
model: sonnet
maxTurns: 25
```
Use for: Architectural decisions, new feature design, system analysis

**researcher.md**
```yaml
name: researcher
description: Deep research for codebases, libraries, APIs, technical questions
tools: [Read, Glob, Grep, WebFetch, WebSearch, Bash, Task]
model: sonnet
maxTurns: 30
```
Use for: Thorough exploration, documentation research, cross-referencing sources

**debugger.md**
```yaml
name: debugger
description: Debugging specialist for errors and test failures
tools: [Read, Edit, Bash, Grep, Glob]
model: inherit
```
Use for: Root cause analysis, fixing bugs, error diagnosis

**docs-writer.md**
```yaml
name: docs-writer
description: Technical documentation writer
tools: [Read, Write, Grep, Glob]
model: inherit
```
Use for: Writing/updating documentation, README files, API docs

**security-reviewer.md**
```yaml
name: security-reviewer
description: Security code review specialist
tools: [Read, Grep, Glob, Bash]
model: sonnet
```
Use for: Security audits, vulnerability scanning, security best practices

**test-writer.md**
```yaml
name: test-writer
description: Test writing specialist
tools: [Read, Write, Edit, Bash, Grep, Glob]
model: inherit
```
Use for: Writing unit tests, integration tests, test coverage

**refactorer.md**
```yaml
name: refactorer
description: Code refactoring specialist
tools: [Read, Edit, Bash, Grep, Glob]
model: inherit
```
Use for: Code cleanup, reducing duplication, improving structure

### 2. BMAD Team Agents (Project-Specific Workflow)

**bmad-architect.md** - System architecture and technical design
**bmad-dev.md** - Implementation and coding
**bmad-qa.md** - Testing and quality assurance
**bmad-pm.md** - Project management and coordination
**bmad-analyst.md** - Requirements analysis
**bmad-sm.md** - Scrum master / agile facilitation
**bmad-tech-writer.md** - Documentation specialist

These are specialized for the BMAD workflow management system in your project.

---

## Best Practices

### 1. Agent Teams Best Practices

**Team Size:**
- 3-5 teammates optimal for most tasks
- Too many = coordination overhead > benefit
- Too few = underutilizing parallelism

**Task Sizing:**
- Self-contained units producing clear deliverable
- Not too small (overhead > work)
- Not too large (too long without check-ins)
- Example: One function, one test file, one review

**Communication:**
- Prefer `write` over `broadcast` (avoid N messages, cost scales)
- Use structured message types (shutdown_request, task_completed) for coordination
- Name teammates descriptively (`security-reviewer` not `worker-1`)

**Monitoring:**
- Check in on teammate progress regularly
- Redirect approaches that aren't working
- Synthesize findings as they come in
- Don't let team run unattended for too long

**File Conflicts:**
- Break work so each teammate owns different files
- Two teammates editing same file = overwrites
- Use task dependencies to serialize same-file work

**Starting Simple:**
- Begin with research/review (clear boundaries, no code conflicts)
- Examples: PR review, library research, bug investigation
- Gain experience before tackling parallel implementation

### 2. Sub-Agent Best Practices

**Isolation Use Cases:**
- High-volume output (tests, logs, documentation fetching)
- Specialized tool restrictions (read-only, bash-only)
- Cost optimization (use haiku for search-heavy tasks)

**Description Field:**
- Write clear, specific descriptions
- Include keywords users naturally say
- Add "use proactively" for automatic delegation

**Tool Restrictions:**
- Grant minimum necessary permissions
- Use hooks for conditional validation (PreToolUse)
- Consider security implications of bypassPermissions

**Memory Management:**
- Use `memory: user` for cross-project learning
- Ask sub-agent to consult memory before work
- Request memory updates after completion
- Builds institutional knowledge over time

**Chaining Sub-Agents:**
- Use for multi-step workflows
- Each returns results to main conversation
- Main conversation passes context to next
- Example: researcher → planner → implementer → tester

### 3. Skills Best Practices

**Skill Types:**
- Reference content: Conventions, patterns, domain knowledge
- Task content: Specific actions (deploy, commit, generate)
- Hybrid: Both knowledge and workflow

**Invocation Control:**
- `disable-model-invocation: true` for side effects
- `user-invocable: false` for background knowledge
- Default: Both you and Claude can invoke

**Supporting Files:**
- Keep SKILL.md under 500 lines
- Move detailed reference to separate files
- Reference from SKILL.md so Claude knows when to load
- Use scripts for heavy lifting (Python, Bash, etc.)

**Context Budget:**
- Skill descriptions loaded into context (2% of window, min 16K chars)
- Too many skills = some excluded
- Check with `/context`
- Override with `SLASH_COMMAND_TOOL_CHAR_BUDGET`

### 4. Planning-with-Files Best Practices

**The 2-Action Rule:**
- Update findings.md after every 2 operations
- Prevents context loss
- Creates permanent knowledge
- Reduces redundant research

**Plan Anchoring:**
- Re-read task_plan.md before major decisions
- Maintains focus on original goals
- Prevents scope creep
- Verifies progress

**Error Logging:**
- Log all errors immediately to progress.md
- Prevents repeated failures
- Guides future approach mutations
- Creates debugging history

**Verification:**
- Check all checkboxes in task_plan.md before stopping
- Confirm all phases complete
- Review findings.md for gaps
- Validate progress.md shows success

### 5. Model Selection Best Practices

**Default Strategy:**
```
haiku → exploration/search
sonnet → most work (default)
opus → complex/novel/undocumented
inherit → maintain consistency with parent
```

**Cost Optimization:**
- Use haiku for exploration-heavy tasks
- Don't use opus unless truly needed
- Monitor agent team token usage (scales with teammates)
- Sub-agents cheaper than agent teams (summarization)

**Performance Optimization:**
- haiku for latency-sensitive operations
- Parallel haiku agents for fast exploration swarms
- opus for quality-critical decisions

**Escalation Pattern:**
```
1. Try sonnet first
2. If stuck/poor results → escalate to opus
3. If simple search → downgrade to haiku
```

### 6. Coordination Patterns

**Parallel Specialists:**
- Multiple experts review simultaneously
- Each has different focus (security, performance, style)
- Leader synthesizes findings
- Best for: Code review, multi-angle analysis

**Pipeline (Sequential):**
- Task dependencies create workflow
- Each stage unblocks next
- Auto-progression via dependency system
- Best for: Research → Design → Implement → Test

**Self-Organizing Swarm:**
- Many independent tasks in pool
- Workers claim tasks, complete, claim next
- No dependencies between tasks
- Best for: Bulk operations (many files to review)

**Competing Hypotheses:**
- Multiple agents investigate different theories
- Actively challenge each other's findings
- Debate/discussion pattern
- Best for: Debugging, root cause analysis

**Plan Approval:**
- Teammate plans in read-only mode
- Leader reviews and approves/rejects
- Teammate implements after approval
- Best for: Risky changes, architectural decisions

### 7. Common Pitfalls

**Agent Teams:**
- Don't let leader implement instead of delegating (use Delegate Mode)
- Don't spawn too many teammates (coordination overhead)
- Don't create tasks too small or too large
- Don't forget to cleanup when done
- Don't let team run unattended too long

**Sub-Agents:**
- Don't use for tasks needing frequent back-and-forth
- Don't nest sub-agents (not supported)
- Don't forget sub-agents can't spawn other sub-agents
- Don't use background mode for tasks needing user input

**Skills:**
- Don't create skills that are too generic
- Don't skip the description field (Claude needs it)
- Don't put side-effect actions in auto-invocable skills
- Don't exceed context budget with too many skills

**Planning:**
- Don't start complex tasks without task_plan.md
- Don't skip the 2-action rule (context loss!)
- Don't forget to re-read plan before decisions
- Don't ignore error logging (repeated failures)

---

## Quick Reference Commands

### Agent Teams
```bash
# Enable agent teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# View team config
cat ~/.claude/teams/{team}/config.json | jq '.members[] | {name, agentType}'

# Monitor inbox
tail -f ~/.claude/teams/{team}/inboxes/team-lead.json

# List tasks
cat ~/.claude/tasks/{team}/*.json | jq '{id, subject, status, owner}'

# Attach to tmux session
tmux attach -t claude-swarm

# Force display mode
claude --teammate-mode in-process
```

### Sub-Agents
```bash
# Interactive agent manager
/agents

# View agent transcripts
ls ~/.claude/projects/{project}/{session}/subagents/

# Disable background tasks
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1

# Adjust compaction threshold
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50
```

### Skills
```bash
# View available skills
ls ~/.claude/skills/
ls .claude/skills/

# Check context budget
/context

# Override skill character budget
export SLASH_COMMAND_TOOL_CHAR_BUDGET=20000
```

---

## Sources

- [Orchestrate teams of Claude Code sessions - Claude Code Docs](https://code.claude.com/docs/en/agent-teams)
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Claude Code Swarm Orchestration Skill - GitHub Gist](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea)
- [Planning-with-Files - GitHub Repository](https://github.com/OthmanAdi/planning-with-files)
- [From Tasks to Swarms: Agent Teams in Claude Code | alexop.dev](https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/)
- [AddyOsmani.com - Claude Code Swarms](https://addyosmani.com/blog/claude-code-agent-teams/)
- [Claude Code Tasks: Complete Guide to AI Agent Workflow | dplooy](https://www.dplooy.com/blog/claude-code-tasks-complete-guide-to-ai-agent-workflow)
- [How to Use Claude Code: Skills, Commands, Agents | ProductTalk](https://www.producttalk.org/how-to-use-claude-code-features/)
- [Claude Code Skills and Slash Commands: Complete Guide | OneAway](https://oneaway.io/blog/claude-code-skills-slash-commands)
- [Claude Code Agent Teams: Setup in 5 Minutes | Serenities AI](https://serenitiesai.com/articles/claude-code-agent-teams-documentation)

---

**Last Updated:** 2026-02-11  
**Document Version:** 1.0  
**Maintained By:** ACM-AI Project / Research Agent
