# Ralph Execution Modes

Three distinct execution modes exist for Ralph autonomous loops. Each has different trade-offs across context, state, process model, and tooling.

---

## Mode Comparison Table

| Dimension | Bash Loop | Slash Commands | In-Session Wiggum |
|---|---|---|---|
| **Context model** | Fresh process per iteration; no carry-over unless state files used | Inherits current conversation context; all prior turns visible | Inherits full session context; orchestrator state is live |
| **State mechanism** | `ralph-config.json` + file system; state written/read on each tick | `ralph-config.json` read at invocation; partial in-session state | In-memory orchestrator state + `ralph-config.json` for durability |
| **Process model** | Outer shell loop calls `claude` CLI per story; each call is a child process | Single session; `/ralph-run` is a command that reads and drives a story | Wiggum orchestrator spawns sub-agents as Task tool calls inside a team |
| **Dependencies** | `bash`, `jq`, `claude` CLI, `ralph-config.json` | Active Claude Code session, `.claude/commands/ralph-*.md` files | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var, agent definition files in `.claude/agents/` |
| **Memory usage** | Low per iteration (each `claude` call starts fresh); total memory is sum of N child processes | Grows across iterations as conversation context accumulates | Highest: orchestrator + all active sub-agent contexts in memory simultaneously |
| **Best for** | Overnight autonomous runs; CI pipelines; reproducible batch execution; when you do not want context bleed between stories | Interactive development; debugging a single story; ad-hoc re-runs; when prior conversation context is useful | Complex cross-agent coordination; parallel specialist work; when agents need to communicate results back to orchestrator |
| **Observability** | Terminal output per story; `ralph-progress.sh` hook writes to log files; `ralph-config.json` is ground truth | Inline in conversation; visible step-by-step; easy to interrupt | Team-level output plus per-agent output; harder to follow simultaneously; use `ralph-status` command to inspect |
| **Recovery** | High: any story can be re-started independently; `ralph-config.json` tracks Done/Blocked/Skipped; bash loop skips completed stories | Medium: re-invoke slash command on same story; prior conversation context may help or hinder | Low: team state is not persisted across session restarts; must rebuild team from scratch |
| **Iteration speed** | Slower per story (CLI startup overhead ~2-5 seconds); fast across stories (parallelizable with `&`) | Fastest for single story (no process overhead); sequential only | Parallel across specialists simultaneously; overhead is team setup (~10s) amortized across all stories |
| **Setup complexity** | Low: requires only `ralph-config.json` and bash; hook scripts optional | Lowest: just open Claude Code and type `/ralph-run` | Highest: requires agent definition files, team env var, orchestrator agent, and specialist agent files |

---

## ASCII Decision Flowchart

```
START: What are you trying to do?
         |
         v
   +------------------+
   | Running a full   |
   | sprint batch?    |
   +------------------+
         |
    Yes  |  No
         |   \
         v    v
    Bash Loop  +--------------------+
               | Debugging a single |
               | story interactively|
               +--------------------+
                        |
                   Yes  |  No
                        |   \
                        v    v
                  Slash Cmds  +----------------------+
                              | Cross-agent parallel |
                              | coordination needed? |
                              +----------------------+
                                       |
                                  Yes  |  No
                                       |   \
                                       v    v
                                In-Session   Consider
                                Wiggum       Slash Cmds
                                             (simpler)

SECONDARY DECISION: Do you have CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1?
         |
    No   |  Yes
         |   \
         v    v
   Cannot use  All 3 modes
   Wiggum      available

TERTIARY DECISION: Is context bleed between stories acceptable?
         |
    No   |  Yes
         |   \
         v    v
   Bash Loop  Slash Cmds or Wiggum
   (fresh per (carry session context)
    story)
```

---

## Mode 1: Bash Loop

### How It Works

The outer shell loop reads `ralph-config.json`, iterates over stories with status `Ready`, and calls `claude` CLI for each. Each invocation is a completely independent process with no shared memory.

```bash
#!/usr/bin/env bash
# Simplified ralph-batch inner logic

CONFIG="D:/ailocal/acm-ai/ralph-config.json"

while true; do
  STORY=$(jq -r '.stories[] | select(.status == "Ready") | .id' "$CONFIG" | head -1)
  [ -z "$STORY" ] && echo "No more ready stories. Done." && break

  echo "Running story: $STORY"
  claude --dangerously-skip-permissions \
         --max-turns 50 \
         -p "$(cat .claude/commands/ralph-run.md) Story: $STORY" \
         | tee "logs/ralph-$STORY.log"

  # Gate check: ralph-gate.sh validates tests/lint before marking Done
  bash .claude/hooks/ralph-gate-guard.sh "$STORY"
done
```

### State Files

- `ralph-config.json` — authoritative story list with statuses (`Ready`, `In Progress`, `Done`, `Blocked`, `Skipped`)
- `logs/ralph-<story>.log` — per-story output
- `.claude/hooks/ralph-progress.sh` — hook called by gate to update config

### When to Use

- Overnight batch runs of an entire sprint
- CI/CD integration (GitHub Actions, local cron)
- When you want clean isolation between stories
- When stories have no runtime dependencies on each other

---

## Mode 2: Slash Commands

### How It Works

Inside an active Claude Code session, you invoke `/ralph-run`, `/ralph-status`, `/ralph-gate`, etc. The command file is read from `.claude/commands/`, interpreted, and executed within the current conversation context.

```
User: /ralph-run E30-S2
Claude: [reads ralph-config.json, loads story spec, executes implementation]
User: /ralph-gate E30-S2
Claude: [runs tests, checks lint, updates ralph-config.json status]
User: /ralph-status
Claude: [displays current sprint dashboard from ralph-config.json]
```

### Available Commands

| Command | Purpose |
|---|---|
| `/ralph-run [story-id]` | Execute a single story |
| `/ralph-status` | Display sprint dashboard |
| `/ralph-gate [story-id]` | Run verification checks |
| `/ralph-skip [story-id]` | Mark story as Skipped |
| `/ralph-retry [story-id]` | Reset Blocked story to Ready |
| `/ralph-config` | Display or edit ralph-config.json |
| `/ralph-reset` | Reset all stories to Ready (destructive) |
| `/ralph-bridge` | Run BMAD → Ralph bridge (generate config from artifacts) |
| `/ralph-batch` | Start bash loop from within session |

### When to Use

- Active development with a developer watching
- Debugging a story that keeps failing
- One-off story execution without setting up bash loop
- When prior conversation context (e.g., an architectural decision made earlier) should be available to the agent

---

## Mode 3: In-Session Wiggum (Agent Teams)

### How It Works

The Wiggum orchestrator agent reads the sprint plan and spawns specialist sub-agents using the `Task` tool. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var.

```
Orchestrator (ralph-sm or ralph-architect):
  → Spawns: backend-specialist (Task tool, team_name="sprint-team")
  → Spawns: frontend-specialist (Task tool, team_name="sprint-team")
  → Waits for results
  → Spawns: ralph-qa (Task tool, team_name="sprint-team")
  → Gate check → Done
```

### Agent Definition Location

`.claude/agents/` — markdown files with YAML frontmatter defining each agent.

### Env Requirement

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Without this, the `Task` tool spawns agents outside a team context (single sub-agent, no team coordination).

### When to Use

- Stories that have clear frontend + backend split (parallel implementation)
- When QA agent should independently verify what dev agents produced
- Complex multi-file refactors where a reviewer agent checks implementation before marking done
- Sprint ceremonies where SM agent coordinates multiple specialist handoffs

---

## Mode Combining Patterns

### Pattern A: Bash Outer + Slash Inner

Use the bash loop to drive stories in batch, but drop into slash commands when a story is Blocked.

```
Bash loop running overnight →
  Story E30-S4 gets Blocked (gate fails) →
  Developer wakes up, opens Claude Code →
  /ralph-status (sees E30-S4 Blocked) →
  /ralph-run E30-S4 (re-runs with interactive context) →
  /ralph-gate E30-S4 (verifies) →
  /ralph-retry E30-S4 if still failing →
  Bash loop picks up from E30-S5 next morning
```

### Pattern B: Wiggum Bootstrap → Bash Handoff

Use Wiggum for the first story (complex architecture decision needing multi-agent coordination), then hand off to bash loop for subsequent implementation stories.

```
Session start:
  /ralph-run E30-S1 (Wiggum team: architect + sm coordinate)
  Team produces: architecture decision records in docs/
  ralph-config.json updated: E30-S1 Done

Night batch:
  ralph-batch.sh picks up E30-S2 through E30-S8
  Each story runs as independent bash loop call
  All implementation stories reference E30-S1 architecture docs
```

### Pattern C: Slash Bootstrap → Wiggum for Parallel Stories

Use slash commands to set up context, then trigger Wiggum for a group of parallelizable stories.

```
/ralph-status (review sprint state)
/ralph-config (adjust story priorities)
/ralph-run E30-S2 (single story, establish patterns)
# E30-S3, E30-S4, E30-S5 are independent parallel stories
# Trigger Wiggum team for parallel execution:
# (within /ralph-run, orchestrator spawns 3 specialists simultaneously)
```

### Anti-Patterns

- **Do not** mix bash loop and Wiggum for the same story — they will conflict on `ralph-config.json` writes
- **Do not** use Wiggum without the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var — Task tool behaves differently
- **Do not** use in-session wiggum for more than 6-8 parallel agents — context and cost explode
- **Do not** rely on slash command session context for overnight runs — sessions expire

---

## Quick Reference

```
Need: Overnight batch        → bash loop (ralph-batch.sh)
Need: Debug one story        → /ralph-run <id>
Need: Parallel specialists   → Wiggum (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1)
Need: Recover blocked story  → /ralph-retry <id> then /ralph-run <id>
Need: CI integration         → bash loop + ralph-gate-guard.sh as gate
```
