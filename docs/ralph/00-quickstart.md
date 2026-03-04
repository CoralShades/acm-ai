# Ralph Quickstart

Two paths through this document. Choose based on your goal:

- **Human setting up Ralph for the first time** — follow Path 1 (5 minutes)
- **AI agent needing architectural context** — read Path 2 (terse reference)

---

## Path 1: Human Quickstart (5 Minutes)

### Prerequisites

| Tool | Required | Install |
|---|---|---|
| `claude` CLI | Required | `npm install -g @anthropic-ai/claude-code` |
| `bash` | Required for Mode 1 | Pre-installed on macOS/Linux. Git Bash on Windows. |
| `jq` | Optional (prd.json parsing) | `brew install jq` / `apt install jq` |
| MCP servers | Optional (browser verification) | See `docs/ralph/11-mcp-integration.md` |

---

### Step 1: Copy the Loop Script Template

```bash
mkdir -p .ralph
cp docs/ralph/templates/ralph_loop.sh.template .ralph/ralph_loop.sh
chmod +x .ralph/ralph_loop.sh
```

The loop script is the external bash runner (Mode 1). It launches Claude in a loop, one story per iteration, until all stories are done or it hits the max iteration limit.

---

### Step 2: Copy the Agent Prompt Template

```bash
cp docs/ralph/templates/PROMPT.md.template .ralph/PROMPT.md
```

This is the instruction document that each Claude session reads at the start of every iteration. It tells the agent what project it is working on, how to signal completion, and what quality gates to pass.

---

### Step 3: Fill In the Three Required Variables

Open `.ralph/PROMPT.md` and fill in:

```
PROJECT_NAME: "Your Project Name"
TEST_COMMAND: "uv run pytest tests/ -x"
LINT_COMMAND: "uv run ruff check . && cd frontend && npm run lint"
```

These are the only values that must be customized. All other instructions in PROMPT.md are project-agnostic.

**ACM-AI values (already set if you copied from the ACM-AI repo):**
- `PROJECT_NAME`: ACM-AI
- `TEST_COMMAND`: `uv run pytest tests/ -x`
- `LINT_COMMAND`: `uv run ruff check . && cd frontend && npm run lint && npm run build`

---

### Step 4: Create prd.json

Copy the template and fill in your story data:

```bash
cp docs/ralph/templates/prd.json.template prd.json
```

The minimum required structure for each story:

```json
{
  "stories": [
    {
      "id": "E30-S1",
      "title": "Short story title",
      "status": "PENDING",
      "deps": [],
      "gate": null,
      "notes": "",
      "spec": "docs/sprint-artifacts/your-story-spec.md"
    }
  ],
  "gates": []
}
```

For a project with dependencies and gates, see the full example in `docs/ralph/templates/prd.json.template`.

**Validation after editing:**
```bash
jq . prd.json > /dev/null && echo "Valid" || echo "Invalid JSON"
```

---

### Step 5: Run

```bash
.ralph/ralph_loop.sh
```

The loop will:
1. Find the first eligible story (PENDING, deps met, gate open)
2. Launch a Claude session with PROMPT.md as context
3. Wait for the session to emit `<promise>COMPLETE</promise>` or `<promise>BLOCKED</promise>`
4. Update prd.json with the result
5. Repeat until all stories are DONE or max iterations is reached

**Monitor progress:**
```bash
# In another terminal:
/ralph-status
```

**Stop gracefully:**
```bash
# Create a stop file — loop exits after current story completes:
touch .ralph/stop
```

---

## Path 2: AI Architecture Overview

Terse structured reference for AI agents reading this document as context.

### Execution Modes

| Mode | Mechanism | Best For |
|---|---|---|
| Mode 1: Bash Loop | External shell script (`.ralph/ralph_loop.sh`) | Unattended multi-story sprints |
| Mode 2: Slash Commands | `/ralph-run`, `/ralph-status`, `/ralph-bridge` inside Claude session | Interactive single-story execution |
| Mode 3: Wiggum / In-Session | Claude spawns itself recursively via Task tool | Complex stories requiring subagents |

### Core Files

| File | Purpose | Format |
|---|---|---|
| `prd.json` | Project state — stories, gates, statuses | JSON |
| `@fix_plan.md` | Current task progress within one story | Markdown checklist |
| `ralph-config.json` | Agent model assignments, loop config | JSON |
| `.ralph/PROMPT.md` | Agent instruction prompt (loaded each iteration) | Markdown |
| `.ralph/state.json` | Loop state for crash recovery | JSON |

### Completion Protocol

Agents MUST use XML-wrapped signals. Natural language detection is not used.

```
Success:  <promise>COMPLETE</promise>
Blocked:  <promise>BLOCKED</promise>
```

Signals are detected by the Stop hook scanning Claude's final output. The hook then updates prd.json accordingly.

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Story completed successfully |
| 1 | Story blocked — requires human intervention |
| 2 | Hook error — check `.claude/settings.json` |
| 3 | Circuit breaker fired — no progress after N iterations |
| 4 | Max iterations reached — story incomplete |

### Gates

Gates are dependency checkpoints that block groups of stories until a condition is met.

- Each gate has a `trigger` story (or set of stories)
- When the trigger story reaches `DONE`, the gate unlocks
- Stories with `gate: "GATE_NAME"` are ineligible until that gate is unlocked
- Manual override: `/ralph-gate unlock GATE_NAME`

Gate state is stored in `prd.json` under the `gates` array.

### Hooks

| Hook Event | Script | Action |
|---|---|---|
| `PreToolUse` (Bash, Write) | `ralph-gate-guard.sh` | Scope protection — blocks writes outside allowed paths |
| `PostToolUse` (Bash) | `ralph-progress.sh` | Progress tracking — updates `@fix_plan.md` |
| `Stop` | `ralph-progress.sh` | Stop gate — detects COMPLETE/BLOCKED, updates prd.json |

Hook configuration is in `.claude/settings.json`. Scripts are in `.claude/hooks/`.

### Key Commands

| Command | Description |
|---|---|
| `/ralph-bridge` | Generate or regenerate prd.json from sprint plan |
| `/ralph-run ID` | Execute a specific story by ID |
| `/ralph-status` | Show all story statuses and gate states |
| `/ralph-config` | View or edit ralph-config.json |
| `/ralph-gate unlock NAME` | Manually unlock a gate |
| `/ralph-gate lock NAME` | Re-lock a gate |
| `/ralph-reset ID` | Reset a story to PENDING |
| `/ralph-retry ID` | Clear BLOCKED status and re-run |
| `/ralph-skip ID` | Mark a story as SKIPPED (excluded from completion) |
| `/ralph-batch FILE` | Run a list of story IDs from a file |

### Story Lifecycle

```
PENDING → IN_PROGRESS → DONE
                      → BLOCKED
                      → SKIPPED
```

Stories transition to `IN_PROGRESS` when Ralph starts them, and to `DONE`/`BLOCKED`/`SKIPPED` based on the agent's output signal or a manual command.

### Model Selection Rules

From CLAUDE.md:

- Single-agent Task calls: may use `opus` for complex/undocumented areas
- Team members (TeamCreate or Task tool within a team): `sonnet` or `haiku` only, never `opus`
- Documentation subagents: `sonnet`
- Simple focused tasks: `haiku`

### Subagent Routing

| File Pattern | Agent |
|---|---|
| `/api/**`, `/open_notebook/**`, `/migrations/**`, `/commands/**` | `backend-specialist` |
| `/frontend/**` | `frontend-specialist` |
| `/tests/**`, `/playwright-report/**` | `qa-specialist` |
| Story complete event | `docs-specialist` |
