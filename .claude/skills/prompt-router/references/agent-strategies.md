# Agent Strategy Templates

Three reusable strategy templates for the `prompt-router` skill. Each template uses `{placeholder}` variables that the downstream `/prompt-generator` skill fills in.

---

## Template A: Solo Agent

**When to use:**
- `feature` + simple (complexity 1-3)
- `bug-fix` + any complexity
- `improvement` + medium/simple
- `frontend` + medium/simple
- `quick-task`
- `documentation`

**Characteristics:**
- Single Claude Code session
- Skills loaded via `/skill-name` in the prompt header
- Linear execution: load context → implement → verify
- No inter-agent coordination needed

---

### Template A Body

```
## Agent Strategy: Solo Agent

Load skills at the start of your session:
{skill_list}

### Session Flow

1. **Load context** — Read CLAUDE.md, review `{primary_file_or_area}`, understand current state
2. **Implement** — {task_description}
3. **Verify** — Run verification checklist before marking complete

### Verification Checklist

{verification_items}

### Constraints

- Stay focused on `{scope}` — do not touch unrelated files
- Commit only when all verification items pass
- If unexpected complexity discovered, stop and surface it rather than expanding scope
```

**Placeholder reference:**

| Placeholder | Description | Example |
|---|---|---|
| `{skill_list}` | Newline list of `/skill-name` | `/systematic-debugging\n/acm-observability` |
| `{primary_file_or_area}` | File or module to start from | `open_notebook/graphs/acm_extraction.py` |
| `{task_description}` | 1-2 sentence goal | "Fix the timeout in the building extraction loop" |
| `{verification_items}` | Checklist items | `- [ ] uv run ruff check .\n- [ ] uv run pytest tests/` |
| `{scope}` | What NOT to touch | `open_notebook/extractors/` |

---

## Template B: Subagent Dispatch

**When to use:**
- `feature` + medium (complexity 4-6)
- `improvement` + complex (complexity 7-10) with gates
- `research` + any complexity (parallel research panes)
- `feature` + complex when tmux is unavailable

**Characteristics:**
- Main agent orchestrates; spawns independent subagents via `/dispatching-parallel-agents`
- Subagents run concurrently for independent tasks; sequentially for dependent ones
- Main agent integrates results and runs final verification
- Each subagent gets its own skill set

---

### Template B Body

```
## Agent Strategy: Subagent Dispatch

Load skills at the start of your session:
/dispatching-parallel-agents
{skill_list}

### Subagent Tasks

Dispatch the following subagents {parallel_or_sequential}:

#### Subagent A — {subagent_a_role}
Skills: {subagent_a_skills}
Task:
{subagent_a_task}
Expected output: {subagent_a_output}

#### Subagent B — {subagent_b_role}
Skills: {subagent_b_skills}
Task:
{subagent_b_task}
Expected output: {subagent_b_output}

{subagent_c_block}

### Integration Step (Main Agent)

After all subagents complete:
1. Review outputs from each subagent
2. {integration_task}
3. Resolve any conflicts between subagent outputs
4. Run full verification checklist

### Verification Checklist

{verification_items}

### Gates (if applicable)

{gate_conditions}
```

**Placeholder reference:**

| Placeholder | Description | Example |
|---|---|---|
| `{skill_list}` | Additional skills for main agent | `/pydantic-models-py` |
| `{parallel_or_sequential}` | "in parallel" or "in sequence" | "in parallel" |
| `{subagent_a_role}` | Short role label | "Backend implementation" |
| `{subagent_a_skills}` | Comma-separated skill list | `/langgraph-fundamentals, /pydantic-models-py` |
| `{subagent_a_task}` | Multi-line task description | "Implement the new graph node in..." |
| `{subagent_a_output}` | What the subagent should produce | "Modified `acm_extraction.py` with new node" |
| `{subagent_b_role}` | Second subagent role | "Test implementation" |
| `{subagent_c_block}` | Optional third subagent (empty string if not needed) | "#### Subagent C — Research\n..." |
| `{integration_task}` | What main agent does after | "Merge backend and frontend changes, check imports" |
| `{gate_conditions}` | Conditions to check before next phase | "All tests must pass before merging" |
| `{verification_items}` | Final checklist items | See verification table in routing-rules.md |

### Parallel vs Sequential Decision

Use **parallel** dispatch when:
- Subagent A and B work in different parts of the codebase with no shared files
- Both tasks can be fully specified upfront
- Example: backend API changes (A) and frontend hook changes (B)

Use **sequential** dispatch when:
- Subagent B's input depends on Subagent A's output
- Example: A writes the schema, B writes tests for it
- Example: A implements the feature, B reviews and fixes issues A introduced

### Gate Pattern (for `improvement` + complex)

A "gate" is a checkpoint the main agent checks before dispatching the next subagent:

```
GATE 1: After Subagent A completes
  ✓ Run: uv run ruff check .
  ✓ Run: uv run pytest tests/test_affected_module.py
  → If FAIL: Fix before dispatching Subagent B
  → If PASS: Dispatch Subagent B
```

---

## Template C: Tmux Agent Team

**When to use:**
- `feature` + complex (complexity 7-10)
- `pipeline` + any complexity
- `frontend` + complex (complexity 7-10)
- Any request where simultaneous implementation + testing + research gives a quality advantage

**Characteristics:**
- Multiple Claude Code instances in tmux panes running concurrently
- Each pane has a dedicated role: Implementation, Testing, Research
- Coordination via shared planning files (`task_plan.md`, `progress.md`)
- No direct inter-pane communication — they work from shared files
- One pane (Implementation) is the "lead" that commits and creates the PR

---

### Template C Body

```
## Agent Strategy: Tmux Agent Team

Load `/dispatching-parallel-agents` for full tmux setup instructions.

### Pane Layout

Start a 3-pane (or 2-pane) tmux session:

```bash
# Create session
tmux new-session -s {session_name} -d

# Pane 1: Implementation (lead pane)
tmux send-keys -t {session_name}:0 "claude" Enter

# Pane 2: Testing
tmux split-window -h -t {session_name}
tmux send-keys -t {session_name}:0.1 "claude" Enter

# Pane 3: Research (optional — include when Context7 is needed)
tmux split-window -v -t {session_name}:0.1
tmux send-keys -t {session_name}:0.2 "claude" Enter
```

### Pane Assignments

#### Pane 1 — Implementation (Lead)
Skills: {implementation_skills}
Responsibility:
- Implement {implementation_task}
- Read `task_plan.md` to track progress
- Update `progress.md` after each milestone
- Create the final commit when all panes are done

#### Pane 2 — Testing
Skills: /verification-before-completion, {testing_skills}
Responsibility:
- Write tests for {testing_scope}
- Run `{test_command}` continuously as Implementation pane works
- Report failures to `findings.md` for Implementation pane to see
- Run full verification checklist at the end

#### Pane 3 — Research (include only when Context7 directives exist)
Skills: (none required — uses Context7 MCP directly)
Responsibility:
- Execute Context7 directives:
  {context7_directives}
- Write findings to `findings.md`
- Answer questions from Implementation pane as they arise

### Coordination Protocol

1. **Start**: All panes read `task_plan.md` before beginning
2. **During**: Panes write to `findings.md` for shared discoveries; `progress.md` for completed milestones
3. **Conflict resolution**: If two panes would edit the same file, Implementation pane has priority; Testing pane waits
4. **Completion signal**: Implementation pane writes "COMPLETE" to `progress.md` when all tasks done
5. **Verification**: Testing pane runs final checklist; Implementation pane addresses any failures

### Shared Planning Files

Create these files before starting the agent team:

**`task_plan.md`** — Pre-populate with tasks from this prompt:
```markdown
# Task Plan: {task_title}
## Implementation Tasks (Pane 1)
- [ ] {impl_task_1}
- [ ] {impl_task_2}
## Testing Tasks (Pane 2)
- [ ] {test_task_1}
- [ ] {test_task_2}
## Research Tasks (Pane 3 — if applicable)
- [ ] {research_task_1}
```

**`findings.md`** — Pre-create, empty:
```markdown
# Findings: {task_title}
## Research Results
(Context7 findings go here)
## Implementation Notes
(Discoveries during implementation go here)
## Test Failures
(Failing tests go here for Implementation pane to fix)
```

**`progress.md`** — Pre-create, empty:
```markdown
# Progress: {task_title}
## Completed Milestones
(Panes update this as they complete work)
## Blockers
(Cross-pane blockers go here)
## Status
ACTIVE
```

### Verification Checklist (Pane 2 runs this)

{verification_items}
```

**Placeholder reference:**

| Placeholder | Description | Example |
|---|---|---|
| `{session_name}` | tmux session name | `acm-feature-extraction` |
| `{implementation_skills}` | Skills for Pane 1 | `/langgraph-fundamentals, /pydantic-models-py` |
| `{implementation_task}` | What Pane 1 builds | "the new MinerU v3 adapter in `open_notebook/extractors/providers/`" |
| `{testing_skills}` | Skills for Pane 2 | `/test-driven-development` |
| `{testing_scope}` | What Pane 2 tests | "the new adapter's normalize() method" |
| `{test_command}` | Command Pane 2 runs | `uv run pytest tests/test_mineru_adapter.py -v` |
| `{context7_directives}` | Formatted Context7 queries | See routing-rules.md Context7 section |
| `{task_title}` | Short task name for files | "MinerU v3 Adapter" |
| `{impl_task_1}` etc. | Individual task items | "Create `MinuruV3Adapter` class stub" |
| `{verification_items}` | Final verification checklist | See routing-rules.md |

### 2-Pane vs 3-Pane Decision

**Use 2 panes** (Implementation + Testing) when:
- Context7 is not needed (no new libraries)
- Research phase is minimal (1-2 file reads, no library docs)

**Use 3 panes** (Implementation + Testing + Research) when:
- `context7_directives` array is non-empty
- Library docs need to be fetched and synthesized before Implementation pane proceeds
- The research pane doubles as a "review" pane for complex architectural questions

---

## Strategy Selection Summary

| Agent Strategy | Best For | Overhead | Coordination |
|---|---|---|---|
| Solo Agent | Focused, well-scoped tasks | Low | None |
| Subagent Dispatch | Independent parallel subtasks | Medium | Via orchestrator agent |
| Tmux Agent Team | Complex multi-domain work needing simultaneous progress | High | Via shared markdown files |

When in doubt, prefer **Solo Agent** for anything under complexity 6, and **Subagent Dispatch** over **Tmux Team** unless the task genuinely benefits from simultaneous execution (e.g., implementation + continuous test running + live research).
