# BMAD v6 Integration

Ralph uses BMAD (Business Model, Architecture, Development) as its planning framework. BMAD produces artifacts in a structured sequence; Ralph consumes those artifacts and executes the implementation.

---

## BMAD Phase → Ralph Phase Mapping

| BMAD Phase | BMAD Agent | Ralph Agent | Ralph Role | Output Artifact |
|---|---|---|---|---|
| Discovery & Research | analyst | ralph-architect | Architecture review, constraints | `_bmad-output/project-planning-artifacts/project-brief.md` |
| Product Requirements | pm | ralph-sm | Sprint breakdown, story sizing | `_bmad-output/project-planning-artifacts/prd.md` |
| System Design | architect | ralph-architect | Tech spec review, feasibility | `_bmad-output/project-planning-artifacts/architecture.md` |
| Sprint Planning | sm | ralph-sm | `ralph-config.json` generation | `docs/sprint-artifacts/<sprint>.md` |
| Implementation | dev | backend-specialist, frontend-specialist | Code implementation | Source files per story |
| Quality Assurance | qa | ralph-qa | Test execution, gate verification | Test results, coverage reports |
| Code Review | reviewer | ralph-reviewer | PR review, standards check | Review comments, approval |
| Documentation | tech-writer | docs-specialist | Docs update, changelog | `docs/` updates |

### BMAD Agents Not Directly Mapped

- **BMAD analyst** → Ralph uses `ralph-architect` for early-stage analysis (no dedicated analyst agent)
- **BMAD pm** → Ralph uses `ralph-sm` for story creation (SM absorbs PM responsibilities in execution)
- **BMAD tech-writer** → Ralph uses `docs-specialist` (scoped, not full doc authoring)

---

## Full Agent Roster

### ralph-architect

| Field | Value |
|---|---|
| File | `.claude/agents/ralph-architect.md` |
| Model | `sonnet` |
| Max turns | 12 |
| Access | Read-only (Read, Grep, Glob, Bash read-only) |
| Responsibility | Architecture decisions, feasibility review, tech spec validation, ADR authoring |
| When spawned | Story E30-S1 type (architecture/design stories), pre-sprint planning |
| Key outputs | Architecture decision records (ADRs), tech spec annotations, constraint lists |

**Spawning example:**
```python
Task(
    description="Review the proposed ACM extraction pipeline architecture and produce an ADR",
    subagent_type="ralph-architect",
    model="sonnet",
    max_turns=12
)
```

### ralph-sm

| Field | Value |
|---|---|
| File | `.claude/agents/ralph-sm.md` |
| Model | `sonnet` |
| Max turns | 20 |
| Access | Read, Write, Glob, Grep, Bash |
| Responsibility | Sprint planning, story creation, `ralph-config.json` generation, BMAD bridge execution |
| When spawned | At sprint start, when running `/ralph-bridge`, when re-planning is needed |
| Key outputs | `ralph-config.json`, `docs/sprint-artifacts/<sprint>.md`, story specs |

**Spawning example:**
```python
Task(
    description="Read the PRD at _bmad-output/project-planning-artifacts/prd.md and generate ralph-config.json for sprint E30",
    subagent_type="ralph-sm",
    model="sonnet",
    max_turns=20
)
```

### backend-specialist

| Field | Value |
|---|---|
| File | `.claude/agents/ralph-backend.md` (if exists) or inline subagent_type |
| Model | `sonnet` (team), `opus` (single agent for complex work) |
| Max turns | 50 |
| Access | All tools |
| Responsibility | Python/FastAPI implementation, SurrealDB migrations, LangGraph workflows, tests |
| When spawned | Any story touching `api/`, `open_notebook/`, `migrations/`, `commands/` |
| Key routing | File patterns: `/api/**`, `/open_notebook/**`, `/migrations/**`, `/commands/**` |

**Spawning example:**
```python
Task(
    description="Implement E30-S2: Add ACM record SF field alignment per docs/sprint-artifacts/e30-s2.md",
    subagent_type="backend-specialist",
    model="sonnet",
    max_turns=50,
    team_name="sprint-team"
)
```

### frontend-specialist

| Field | Value |
|---|---|
| File | `.claude/agents/ralph-frontend.md` (if exists) or inline subagent_type |
| Model | `sonnet` (team), `opus` (single agent for complex work) |
| Max turns | 50 |
| Access | All tools |
| Responsibility | Next.js, React, TypeScript, Tailwind, Zustand, React Query implementation |
| When spawned | Any story touching `frontend/` |
| Key routing | File patterns: `/frontend/**` |

**Spawning example:**
```python
Task(
    description="Implement E30-S2 frontend: ACM record display alignment per docs/sprint-artifacts/e30-s2.md",
    subagent_type="frontend-specialist",
    model="sonnet",
    max_turns=50,
    team_name="sprint-team"
)
```

### ralph-qa

| Field | Value |
|---|---|
| File | `.claude/agents/ralph-qa.md` |
| Model | `sonnet` |
| Max turns | 30 |
| Access | All tools (needs Bash for test execution) |
| Responsibility | Test execution, gate verification, coverage checks, browser verification for UI stories |
| When spawned | After backend-specialist and/or frontend-specialist complete; before reviewer |
| Key outputs | Test results, gate pass/fail, coverage report, browser screenshots |

**Spawning example:**
```python
Task(
    description="Run QA gate for E30-S2: execute pytest, frontend lint+build, verify UI in browser",
    subagent_type="ralph-qa",
    model="sonnet",
    max_turns=30,
    team_name="sprint-team"
)
```

### ralph-reviewer

| Field | Value |
|---|---|
| File | `.claude/agents/ralph-reviewer.md` |
| Model | `sonnet` |
| Max turns | 15 |
| Access | Read, Grep, Glob, Bash (read-only) |
| Responsibility | Code review, standards compliance, pattern adherence, security scan |
| When spawned | After QA passes; before docs-specialist |
| Key outputs | Review checklist, LGTM/request-changes decision |

**Spawning example:**
```python
Task(
    description="Review implementation of E30-S2 for code standards, security, and pattern compliance",
    subagent_type="ralph-reviewer",
    model="sonnet",
    max_turns=15,
    team_name="sprint-team"
)
```

### docs-specialist

| Field | Value |
|---|---|
| File | `.claude/agents/ralph-docs.md` (if exists) or inline |
| Model | `haiku` |
| Max turns | 10 |
| Access | Read, Write |
| Responsibility | Update docs/, CHANGELOG, sprint artifact completion records |
| When spawned | After reviewer approves; story completion step |
| Key outputs | Updated `docs/` files, sprint artifact marked complete |

**Spawning example:**
```python
Task(
    description="Update docs for E30-S2 completion: mark story done in sprint artifact, update relevant docs",
    subagent_type="docs-specialist",
    model="haiku",
    max_turns=10,
    team_name="sprint-team"
)
```

---

## Agent Spawning API

All agent spawning uses the `Task` tool. The parameters are:

```python
Task(
    description="<what to do — full context, story ID, file paths>",
    subagent_type="<agent name from .claude/agents/ or built-in type>",
    model="sonnet" | "haiku" | "opus",   # see model strategy
    max_turns=N,                          # optional override
    team_name="<team-name>",              # required for Wiggum/team mode
    name="<instance-name>",              # optional, for identifying in logs
)
```

### Parameter Rules

| Parameter | Rule |
|---|---|
| `model` | `sonnet` for team members always; `opus` only for single-agent calls; `haiku` for docs/simple |
| `max_turns` | Match agent roster defaults; do not set higher than roster max without justification |
| `team_name` | Must match across all agents in the same sprint team; omit for single-agent calls |
| `name` | Useful for parallel agents of the same type (e.g., `name="backend-dev-1"`) |
| `description` | Must include story ID, relevant file paths, and what "done" means |

---

## BMAD Artifact Paths

### Planning Artifacts (BMAD Output)

```
_bmad-output/
  project-planning-artifacts/
    project-brief.md         # Discovery output
    prd.md                   # Product requirements
    architecture.md          # System design
    epic-list.md             # Epic breakdown
    stories/
      <epic>-<story>.md      # Individual story specs (pre-bridge)
```

### Sprint Artifacts (Ralph Input/Output)

```
docs/sprint-artifacts/
  <epic-id>-<sprint-id>-<slug>.md    # Sprint plan (generated by ralph-bridge)
  # Example: e30-s3-acm-record-sf-item-alignment.md
```

### Ralph Config (Authoritative State)

```
ralph-config.json                    # Sprint state: story list, statuses, metadata
```

### Log Files

```
logs/
  ralph-<story-id>.log               # Per-story execution log (bash loop mode)
```

---

## Workflow: Planning → Bridge → Execution

### Phase 1: BMAD Planning (Human + BMAD Agents)

```
1. Run BMAD analyst → project-brief.md
2. Run BMAD pm      → prd.md
3. Run BMAD architect → architecture.md
4. Run BMAD sm      → epic-list.md + stories/*.md
```

BMAD agents are invoked separately in a planning session (not by Ralph). Output lands in `_bmad-output/`.

### Phase 2: Bridge (Ralph SM)

The bridge converts BMAD artifacts into Ralph execution format.

```bash
/ralph-bridge
```

Or spawned as Task:

```python
Task(
    description="Run BMAD bridge: read _bmad-output/project-planning-artifacts/ and generate ralph-config.json and sprint artifacts in docs/sprint-artifacts/",
    subagent_type="ralph-sm",
    model="sonnet",
    max_turns=20
)
```

The bridge:
1. Reads all BMAD artifacts
2. Generates `ralph-config.json` with stories in dependency order
3. Writes `docs/sprint-artifacts/<sprint>.md` for each epic/sprint
4. Sets all stories to status `Ready`

### Phase 3: Execution (Ralph)

```bash
# Option A: Bash loop
bash .claude/hooks/ralph-batch.sh

# Option B: Slash commands
/ralph-run E30-S1
/ralph-gate E30-S1
/ralph-run E30-S2
...

# Option C: Wiggum team (parallel)
# Orchestrator spawns specialists from ralph-config.json
```

### Phase 4: Story Completion Protocol

For each story, the completion sequence is:

```
1. backend-specialist and/or frontend-specialist implement
2. ralph-gate-guard.sh runs: pytest + ruff + frontend lint/build
3. ralph-qa verifies: browser check (UI stories), coverage, edge cases
4. ralph-reviewer checks: code standards, patterns, security
5. docs-specialist updates: sprint artifact, docs/
6. ralph-config.json updated: status → Done
```

If gate fails at step 2, story → `Blocked`. Use `/ralph-retry <id>` to reset.

---

## ralph-config.json Schema Reference

```json
{
  "sprint": {
    "id": "E30",
    "name": "ACM SF Alignment Sprint",
    "started": "2026-03-01",
    "target_complete": "2026-03-15"
  },
  "stories": [
    {
      "id": "E30-S1",
      "title": "SF Schema Config Loader",
      "status": "Done",
      "spec": "docs/sprint-artifacts/e30-s1-sf-schema-config.md",
      "agents": ["backend-specialist"],
      "depends_on": [],
      "model": "sonnet"
    },
    {
      "id": "E30-S2",
      "title": "ACM Record SF Field Alignment",
      "status": "Ready",
      "spec": "docs/sprint-artifacts/e30-s2-acm-sf-alignment.md",
      "agents": ["backend-specialist", "frontend-specialist"],
      "depends_on": ["E30-S1"],
      "model": "sonnet"
    }
  ],
  "config": {
    "max_iterations": 40,
    "gate_required": true,
    "parallel_allowed": false,
    "completion_promise": "COMPLETE",
    "blocked_signal": "BLOCKED"
  }
}
```

### Status Values

| Status | Meaning | Next Action |
|---|---|---|
| `Ready` | Available to run | `/ralph-run <id>` |
| `In Progress` | Currently being executed | Wait or inspect |
| `Done` | Gate passed, complete | None |
| `Blocked` | Gate failed or agent signaled BLOCKED | `/ralph-retry <id>` |
| `Skipped` | Intentionally skipped | `/ralph-skip <id>` |
| `Deferred` | Moved to future sprint | Update sprint plan |
