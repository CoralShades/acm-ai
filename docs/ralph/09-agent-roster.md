# Agent Roster Reference

All Ralph agents are defined as markdown files with YAML frontmatter in `.claude/agents/`. This document is the authoritative reference for agent capabilities, turn limits, tool access, and team patterns.

---

## Agent Anatomy

Each agent file follows this structure:

```markdown
---
name: ralph-architect
description: >
  Architecture review agent. Read-only access. Reviews tech specs,
  produces ADRs, validates feasibility. Use for design stories and
  pre-sprint architecture sessions.
tools:
  - Read
  - Grep
  - Glob
  - Bash
model: sonnet
maxTurns: 12
---

# System prompt content follows here.
# This is the agent's behavioral instructions.
```

### Frontmatter Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Agent identifier; matches `subagent_type` in Task tool calls |
| `description` | string | Yes | One-paragraph description used by orchestrators to select correct agent |
| `tools` | list | Yes | Explicit list of tools this agent may use; unlisted tools are not available |
| `model` | string | Yes | Default model: `haiku`, `sonnet`, or `opus` |
| `maxTurns` | int | Yes | Maximum conversation turns before agent must return; prevents runaway loops |

### Tool Names

Valid tool names for the `tools` field:

```
Read        - Read files from filesystem
Write       - Write/create files
Edit        - Edit existing files (preferred over Write for modifications)
Glob        - File pattern search
Grep        - Content search (ripgrep)
Bash        - Execute shell commands
WebFetch    - Fetch URLs
WebSearch   - Search the web
Task        - Spawn sub-agents (orchestrators only)
```

---

## Agent Roster Table

| Agent | File | Model | Max Turns | Tools | Primary Role |
|---|---|---|---|---|---|
| ralph-architect | `.claude/agents/ralph-architect.md` | sonnet | 12 | Read, Grep, Glob, Bash (read) | Architecture review, ADR authoring, feasibility |
| ralph-sm | `.claude/agents/ralph-sm.md` | sonnet | 20 | Read, Write, Glob, Grep, Bash | Sprint planning, ralph-config.json, BMAD bridge |
| ralph-qa | `.claude/agents/ralph-qa.md` | sonnet | 30 | All tools | Test execution, gate verification, browser checks |
| ralph-reviewer | `.claude/agents/ralph-reviewer.md` | sonnet | 15 | Read, Grep, Glob, Bash | Code review, standards, security scan |
| backend-specialist | (subagent_type string) | sonnet/opus | 50 | All tools | Python, FastAPI, SurrealDB, LangGraph |
| frontend-specialist | (subagent_type string) | sonnet/opus | 50 | All tools | Next.js, React, TypeScript, Tailwind |
| docs-specialist | (subagent_type string) | haiku | 10 | Read, Write | Docs updates, changelog, sprint completion records |

---

## Agent Detail Sheets

### ralph-architect

```yaml
name: ralph-architect
model: sonnet
maxTurns: 12
tools: [Read, Grep, Glob, Bash]
```

**Scope:** Read-only. This agent never writes production code. It reads existing code, architecture docs, and BMAD artifacts to produce decision documents and annotations.

**Outputs:**
- Architecture Decision Records (ADRs) in `docs/decisions/`
- Tech spec review annotations
- Constraint and risk lists
- Feasibility assessments

**Invoked by:** Sprint SM at start of architecture stories; orchestrator for pre-sprint design pass.

**Do not use for:** Implementation, file creation in `api/` or `frontend/`, test execution.

**Turn budget allocation:**
- Turns 1-4: Read existing code, architecture docs, BMAD artifacts
- Turns 5-9: Draft ADR or review document
- Turns 10-12: Finalize and write output doc

---

### ralph-sm

```yaml
name: ralph-sm
model: sonnet
maxTurns: 20
tools: [Read, Write, Glob, Grep, Bash]
```

**Scope:** Sprint management. Reads BMAD artifacts, writes Ralph config and sprint artifacts. Orchestrates story sequencing and dependency ordering.

**Outputs:**
- `ralph-config.json` (generated or updated)
- `docs/sprint-artifacts/<sprint>.md` files
- Story status updates
- Sprint retrospective notes

**Invoked by:** Human via `/ralph-bridge`; orchestrator at sprint start.

**Do not use for:** Implementation code, test execution, architecture decisions.

**Turn budget allocation:**
- Turns 1-5: Read BMAD artifacts and existing sprint state
- Turns 6-15: Generate or update ralph-config.json and sprint artifacts
- Turns 16-20: Validate output, confirm story dependencies are correct

---

### ralph-qa

```yaml
name: ralph-qa
model: sonnet
maxTurns: 30
tools: [Read, Write, Grep, Glob, Bash, Task]  # Task for spawning browser check sub-agents
```

**Scope:** Quality gate. Runs all verification checks. Has the broadest tool access of the verification agents because it must execute tests, run lint, and optionally trigger browser checks.

**Outputs:**
- Test execution results (`pytest` stdout)
- Lint check results (`ruff check`, `npm run lint`)
- Frontend build status (`npm run build`)
- Browser verification screenshots (UI stories)
- Gate pass/fail decision written to ralph-config.json

**Invoked by:** Orchestrator after implementation specialists complete; bash loop gate script.

**Do not use for:** Implementation, architecture decisions, doc authoring.

**Turn budget allocation:**
- Turns 1-5: Read story spec, identify what to verify
- Turns 6-15: Execute backend tests and lint
- Turns 16-22: Execute frontend lint and build (if applicable)
- Turns 23-27: Browser verification (if UI story)
- Turns 28-30: Write gate result, update ralph-config.json

**Gate commands:**
```bash
# Backend gate
cd "D:/ailocal/acm-ai" && uv run pytest tests/ -x

# Lint
cd "D:/ailocal/acm-ai" && uv run ruff check .

# Frontend gate
cd "D:/ailocal/acm-ai/frontend" && npm run lint && npm run build
```

---

### ralph-reviewer

```yaml
name: ralph-reviewer
model: sonnet
maxTurns: 15
tools: [Read, Grep, Glob, Bash]
```

**Scope:** Code review. Read-only (Bash is used for `git diff`, `git log`, not for running tests). Checks implementation against project standards, patterns, and security requirements.

**Outputs:**
- Review checklist completion
- LGTM decision or request-changes list
- Pattern compliance notes

**Review checklist:**
- [ ] Conventional commit messages
- [ ] Type hints on all Python functions
- [ ] Ruff/lint passes
- [ ] No hardcoded secrets or credentials
- [ ] Repository pattern followed for DB access
- [ ] LangGraph nodes follow null-safe pattern
- [ ] Frontend uses React Query for server state, Zustand for client state
- [ ] No direct `magic_pdf` or `paddle` imports in main code
- [ ] Migration files follow numbering convention
- [ ] Tests cover happy path and at least one error case

**Invoked by:** Orchestrator after ralph-qa passes.

**Turn budget allocation:**
- Turns 1-3: Read story spec and changed files (via `git diff`)
- Turns 4-12: Review each changed file against checklist
- Turns 13-15: Write review summary, LGTM or request-changes

---

### backend-specialist

Not defined as a `.claude/agents/` file; invoked by subagent_type string or custom agent definition.

```yaml
# If defined as agent file:
name: backend-specialist
model: sonnet   # sonnet for teams, opus for single-agent complex work
maxTurns: 50
tools: [Read, Write, Edit, Glob, Grep, Bash, WebFetch]
```

**Scope:** Full Python backend implementation. The primary implementation agent for all backend stories.

**Routing triggers:** Any story with file changes in:
- `api/` — FastAPI routers, services, models
- `open_notebook/` — Domain layer, graphs, extractors, database
- `migrations/` — SurrealDB schema migrations
- `commands/` — Background job handlers

**Turn budget allocation:**
- Turns 1-5: Read story spec, existing code, related tests
- Turns 6-35: Implement code changes
- Turns 36-45: Write or update tests
- Turns 46-50: Self-review, fix any issues found

---

### frontend-specialist

Not defined as a `.claude/agents/` file; invoked by subagent_type string or custom agent definition.

```yaml
# If defined as agent file:
name: frontend-specialist
model: sonnet   # sonnet for teams, opus for single-agent complex work
maxTurns: 50
tools: [Read, Write, Edit, Glob, Grep, Bash, WebFetch]
```

**Scope:** Full Next.js/React frontend implementation.

**Routing triggers:** Any story with file changes in `frontend/`.

**Tech stack:** Next.js 15, React 19, TypeScript, Tailwind CSS 4, Zustand, React Query, Radix UI, shadcn/ui patterns.

**Turn budget allocation:** Same as backend-specialist.

---

### docs-specialist

Not defined as a `.claude/agents/` file; invoked by subagent_type string.

```yaml
# If defined as agent file:
name: docs-specialist
model: haiku    # haiku is sufficient for doc updates
maxTurns: 10
tools: [Read, Write]
```

**Scope:** Documentation only. Reads story spec and implementation summary, updates relevant docs.

**Outputs:**
- Sprint artifact marked complete in `docs/sprint-artifacts/`
- `docs/` files updated with new API endpoints, config options, etc.
- CHANGELOG entry (if applicable)

**Turn budget allocation:**
- Turns 1-3: Read story spec and identify which docs to update
- Turns 4-8: Write doc updates
- Turns 9-10: Verify output is correct

---

## Team Patterns

### Option A: Single-Agent (No Teams)

Simplest pattern. One agent handles the full story. No `team_name` parameter.

```python
Task(
    description="Implement E30-S2 backend and frontend, run tests, update docs",
    subagent_type="backend-specialist",
    model="sonnet",
    max_turns=50
    # No team_name
)
```

**Best for:** Stories that are entirely backend or entirely frontend; simple stories under 200 lines of change; when CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 is not set.

**Cost:** 1 agent context.

---

### Option B: Lead + Specialist Team

Orchestrator (SM or QA lead) spawns 2-3 specialists.

```python
# SM orchestrates
Task(
    description="Coordinate E30-S2: spawn backend and frontend specialists, then QA",
    subagent_type="ralph-sm",
    model="sonnet",
    max_turns=20,
    team_name="e30-s2-team"
)

# Within SM's execution:
Task(
    description="Implement E30-S2 backend",
    subagent_type="backend-specialist",
    model="sonnet",
    max_turns=50,
    team_name="e30-s2-team",
    name="backend-dev"
)
Task(
    description="Implement E30-S2 frontend",
    subagent_type="frontend-specialist",
    model="sonnet",
    max_turns=50,
    team_name="e30-s2-team",
    name="frontend-dev"
)
```

**Best for:** Full-stack stories with clear frontend/backend split; when parallel implementation saves time.

**Cost:** 3 agent contexts (SM + 2 specialists).

---

### Option C: Full Sprint Team

Orchestrator spawns full pipeline: architect → dev(s) → QA → reviewer → docs.

```python
# ralph-sm orchestrates full story pipeline
Team: ralph-sm (lead)
  → ralph-architect (if design story)
  → backend-specialist
  → frontend-specialist
  → ralph-qa
  → ralph-reviewer
  → docs-specialist
```

**Best for:** Complex stories requiring architecture review + parallel implementation + full verification; sprint ceremonies.

**Cost:** Up to 7 agent contexts. Use sparingly.

---

## Cost Control Rules

These rules are MANDATORY per CLAUDE.md:

| Rule | Detail |
|---|---|
| `sonnet` for all team members | Never use `opus` in a `team_name` context |
| `opus` only for single agents | Allowed when task is complex, undocumented, or requires deep reasoning |
| `haiku` for simple tasks | Docs updates, lint runs, changelog entries, simple test additions |
| Minimize team size | Prefer Option A over Option B; Option B over Option C |
| Sequential > parallel | Run agents sequentially unless stories are truly independent |
| Respect maxTurns | Do not override maxTurns higher than roster defaults without justification |

### Upgrade Heuristics (sonnet → opus, single agent only)

Use `opus` when:
- Story involves areas with minimal existing code patterns to follow
- Requires cross-cutting architectural reasoning (e.g., new LangGraph workflow design)
- Previous sonnet attempt produced incomplete or incorrect implementation
- Story touches multiple subsystems with complex interactions (e.g., pipeline + SSE + frontend)

### Downgrade Heuristics (sonnet → haiku)

Use `haiku` when:
- Task is documentation only (no code changes)
- Task is a simple test addition following existing test patterns
- Task is a lint/format fix with no logic changes
- Task is reading and summarizing files (no implementation)
