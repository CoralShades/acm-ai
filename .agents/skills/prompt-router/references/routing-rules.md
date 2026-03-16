# Routing Rules Reference

Complete routing matrix, domain skill selection logic, Context7 directive templates, and PromptPlan output schema for the `prompt-router` skill.

---

## Primary Routing Matrix

Each row maps a `(type, complexity_band)` pair to a recommended skill set, agent strategy, Context7 requirement, and output format.

**Complexity bands:**
- Simple: 1-3
- Medium: 4-6
- Complex: 7-10

| Type + Complexity | Skills to Load | Agent Strategy | Context7? | Output Format |
|---|---|---|---|---|
| `feature` + complex (7-10) | `/planning-with-files`, `/dispatching-parallel-agents`, `/verification-before-completion`, + domain skills | Tmux agent team | Yes | Prompt-pack .md |
| `feature` + medium (4-6) | `/planning-with-files`, `/subagent-driven-development`, + domain skills | Subagent dispatch | If new library | Copy-paste prompt |
| `feature` + simple (1-3) | Domain skills only | Solo agent | No | Terminal output |
| `bug-fix` + any | `/systematic-debugging`, `/planning-with-files` (if complex), + domain skills | Solo focused agent | If library-API error | Copy-paste prompt |
| `research` + any | `/planning-with-files`, `/acm-observability` (if pipeline), + domain skills | Parallel subagents | Yes | Prompt-pack .md |
| `improvement` + complex (7-10) | `/planning-with-files`, `/subagent-driven-development`, `/verification-before-completion`, + domain | Subagent dispatch with gates | If refactoring patterns | Prompt-pack .md |
| `improvement` + medium/simple (1-6) | `/verification-before-completion`, + domain skills | Solo agent | No | Copy-paste prompt |
| `pipeline` + any | `/langgraph-fundamentals`, `/acm-observability`, `/planning-with-files`, `/verification-before-completion` | Tmux team | Yes (LangGraph + LangChain) | Prompt-pack .md |
| `frontend` + complex (7-10) | `/dispatching-parallel-agents`, `/react-best-practices`, `/next-best-practices`, + frontend skills | Tmux team | If new React patterns | Prompt-pack .md |
| `frontend` + medium/simple (1-6) | `/react-best-practices`, `/next-best-practices`, + frontend skills | Solo agent | No | Copy-paste prompt |
| `quick-task` | Minimal (0-1 skills) | Solo agent | No | Terminal output |
| `documentation` | None specific | Solo agent | No | Terminal output |

---

## Domain Skill Selection Logic

After matching the primary routing row, check `domain_signals` from the `RequestClassification` and append additional skills. Apply all matching rules; deduplicate the final list.

### Signal-to-Skill Map

| Domain Signal(s) | Additional Skills to Add |
|---|---|
| `"extraction"`, `"pipeline"`, `"graph"`, `"node"` | `/langgraph-fundamentals`, `/acm-observability` |
| `"agent"`, `"tool"`, `"chain"` | `/langchain-fundamentals` |
| `"model"`, `"schema"`, `"pydantic"`, `"validation"` | `/pydantic-models-py` |
| `"debug"`, `"error"`, `"trace"`, `"failing"`, `"broken"` | `/systematic-debugging`, `/acm-observability` |
| `"component"`, `"page"`, `"UI"`, `"React"`, `"css"`, `"frontend"` | `/react-best-practices`, `/next-best-practices` |
| `"streaming"`, `"SSE"`, `"websocket"`, `"real-time"` | `/sse-streaming` |
| `"test"`, `"coverage"`, `"pytest"`, `"playwright"`, `"e2e"` | `/test-driven-development`, `/verification-before-completion` |
| `"api"`, `"endpoint"`, `"router"`, `"fastapi"` | `/fastapi-router-py` |
| `"python"`, `"uv"`, `"packaging"`, `"dependency"` | `/modern-python` |
| `"database"`, `"surrealdb"`, `"migration"`, `"query"` | No specific skill (use CLAUDE.md surrealdb.md rule) |
| `"security"`, `"auth"`, `"permissions"`, `"vulnerability"` | `/security-best-practices` |
| No matching signal | No additional skills |

### Deduplication Rule

If a skill appears in both the routing matrix row AND the domain signal map, include it only once.

---

## Context7 Directive Templates

Use these templates to build the `context7_directives` array in `PromptPlan`.

Substitute `{topic}` with the specific library feature, API name, or pattern mentioned in the user's request.

### LangGraph

```
resolve-library-id for "langgraph"
→ query-docs for "{topic}"
```

**When to include:** Always for `pipeline` type, for any request mentioning "StateGraph", "nodes", "edges", "Command", "interrupt", "checkpointer", "LangGraph" by name.

**Common topics:**
- "StateGraph nodes and edges"
- "Command pattern for conditional routing"
- "interrupt for human-in-the-loop"
- "checkpointer persistence"
- "streaming graph output"

### LangChain

```
resolve-library-id for "langchain"
→ query-docs for "{topic}"
```

**When to include:** For any request mentioning "chains", "agents", "tools", "LangChain", "ChatModel", "PromptTemplate", "Runnable".

**Common topics:**
- "create_react_agent"
- "tool calling with structured output"
- "RunnablePassthrough and LCEL"
- "ChatOpenAI configuration"

### Pydantic

```
resolve-library-id for "pydantic"
→ query-docs for "{topic}"
```

**When to include:** For any request involving Pydantic model definitions, validators, serialization, or schema generation.

**Common topics:**
- "model_validator pre and post"
- "field_validator with mode=before"
- "model_dump with mode=json"
- "discriminated unions"
- "BaseModel inheritance patterns"

### Next.js

```
resolve-library-id for "nextjs"
→ query-docs for "{topic}"
```

**When to include:** For any request involving Next.js App Router, RSC, Server Actions, routing, or Next.js-specific patterns.

**Common topics:**
- "App Router layout and page files"
- "Server Components vs Client Components"
- "dynamic route segments"
- "Server Actions for form handling"
- "next/dynamic for lazy loading"

### React

```
resolve-library-id for "react"
→ query-docs for "{topic}"
```

**When to include:** For `frontend` + complex requests introducing new React patterns (hooks, context, refs, concurrent features).

**Common topics:**
- "useCallback and useMemo optimization"
- "useRef imperative handle"
- "Suspense and lazy"
- "Context API with useReducer"

### AG Grid (community)

```
resolve-library-id for "ag-grid"
→ query-docs for "{topic}"
```

**When to include:** For requests involving the ACM item grid, building grid, column definitions, or row grouping.

**Common topics:**
- "columnDefs rowGroup"
- "getRowId and selection"
- "cell renderers"
- "bulk edit with applyTransaction"

---

## Conditional Context7 Rules

| Condition | Include Context7? |
|---|---|
| `pipeline` type (always) | Yes — LangGraph + LangChain |
| `research` type (always) | Yes — libraries mentioned in request |
| `feature` with explicit library version in request | Yes — that library |
| `bug-fix` with "library API" or "method not found" error | Yes — offending library |
| `feature` + medium complexity with no library mention | No |
| `improvement` + refactoring across 3+ files | No (unless graph patterns change) |
| `improvement` refactoring LangGraph graph nodes | Yes — LangGraph |
| `frontend` + simple/medium, no new library | No |
| `quick-task` or `documentation` | Never |

---

## PromptPlan Output Schema

The router outputs a single `PromptPlan` JSON object. This is the contract between the router and the `/prompt-generator` skill.

```json
{
  "classification": {
    "type": "feature|bug-fix|research|improvement|pipeline|frontend|quick-task|documentation",
    "complexity": 5,
    "plan_mode": true,
    "domain_signals": ["extraction", "graph"],
    "scope": "single-file|multi-file|cross-cutting",
    "estimated_files": 4
  },
  "selected_skills": [
    "/planning-with-files",
    "/langgraph-fundamentals",
    "/acm-observability"
  ],
  "agent_strategy": "tmux-team|subagent-dispatch|solo",
  "agent_config": {
    "panes": [
      {
        "id": "implementation",
        "role": "Implementation agent",
        "skills": ["/langgraph-fundamentals"],
        "task": "Implement the graph node changes"
      },
      {
        "id": "testing",
        "role": "Test agent",
        "skills": ["/verification-before-completion"],
        "task": "Write and run tests for graph changes"
      },
      {
        "id": "research",
        "role": "Research agent",
        "skills": [],
        "task": "Query Context7 for LangGraph patterns"
      }
    ],
    "subagents": [
      {
        "id": "subagent-a",
        "task": "Implement backend changes",
        "skills": [],
        "parallel": true
      },
      {
        "id": "subagent-b",
        "task": "Implement frontend changes",
        "skills": [],
        "parallel": true
      }
    ],
    "solo": false
  },
  "context7_directives": [
    "resolve-library-id for \"langgraph\" → query-docs for \"StateGraph nodes and edges\"",
    "resolve-library-id for \"langchain\" → query-docs for \"tool calling\""
  ],
  "output_format": "prompt-pack|copy-paste|terminal",
  "output_path": "docs/sprint-artifacts/prompt-packs/",
  "plan_mode": true,
  "plan_type": "full|debug|research|refactor|none",
  "verification_items": [
    "uv run ruff check .",
    "uv run pytest tests/",
    "cd frontend && npm run build"
  ]
}
```

### Field Reference

| Field | Type | Description |
|---|---|---|
| `classification` | object | Full `RequestClassification` from Step 1, passed through unchanged |
| `selected_skills` | string[] | Ordered list of skills to load. Prefix `/` matches Claude Code skill names. |
| `agent_strategy` | enum | One of: `"solo"`, `"subagent-dispatch"`, `"tmux-team"` |
| `agent_config.panes` | array | Used when `agent_strategy = "tmux-team"`. Each entry is a tmux pane. |
| `agent_config.subagents` | array | Used when `agent_strategy = "subagent-dispatch"`. |
| `agent_config.solo` | bool | `true` when `agent_strategy = "solo"` |
| `context7_directives` | string[] | Ordered list of Context7 MCP call sequences. Empty array if not needed. |
| `output_format` | enum | One of: `"prompt-pack"`, `"copy-paste"`, `"terminal"` |
| `output_path` | string | Used when `output_format = "prompt-pack"`. Full directory path. |
| `plan_mode` | bool | Whether to scaffold `task_plan.md` + `findings.md` + `progress.md` |
| `plan_type` | enum | `"full"` (feature/improvement), `"debug"` (bug-fix), `"research"`, `"refactor"`, `"none"` |
| `verification_items` | string[] | Shell commands to run before claiming completion |

---

## Skill Name Reference

These are the skill identifiers as used in `selected_skills`. All are available in both `.claude/skills/` and `.agents/skills/`.

### Workflow Skills

| Skill ID | Purpose |
|---|---|
| `/planning-with-files` | task_plan.md + findings.md + progress.md scaffolding |
| `/dispatching-parallel-agents` | Parallel subagent dispatch for independent tasks |
| `/subagent-driven-development` | Fresh subagent per task pattern with review gate |
| `/verification-before-completion` | Pre-completion verification checklist enforcement |
| `/executing-plans` | Execute a written implementation plan |
| `/writing-plans` | Create implementation plans from specs |

### Debugging Skills

| Skill ID | Purpose |
|---|---|
| `/systematic-debugging` | Root-cause-first debugging protocol |
| `/acm-observability` | Langfuse traces, LangSmith, LangGraph state inspection |
| `/find-bugs` | Static bug hunting |

### Backend Skills

| Skill ID | Purpose |
|---|---|
| `/langgraph-fundamentals` | StateGraph, nodes, edges, Command patterns |
| `/langchain-fundamentals` | Agents, tools, chains, LCEL |
| `/pydantic-models-py` | Pydantic v2 multi-model patterns |
| `/fastapi-router-py` | FastAPI CRUD routers with auth |
| `/modern-python` | uv, ruff, pyproject.toml patterns |
| `/test-driven-development` | TDD with red-green-refactor |

### Frontend Skills

| Skill ID | Purpose |
|---|---|
| `/react-best-practices` | React performance, hooks, patterns |
| `/next-best-practices` | Next.js App Router, RSC, file conventions |
| `/sse-streaming` | Server-Sent Events implementation |
| `/frontend-design` | Visual design and component patterns |
| `/webapp-testing` | Browser interaction testing |

---

## Routing Examples

### Example A — Pipeline Feature (complex)

**Input classification:**
```json
{
  "type": "pipeline",
  "complexity": 8,
  "plan_mode": true,
  "domain_signals": ["extraction", "graph", "node"],
  "scope": "cross-cutting",
  "estimated_files": 6
}
```

**Routing result:**
- Matrix row: `pipeline + any` → tmux-team, Context7=yes
- Domain signals: `"extraction"`, `"graph"` → `/langgraph-fundamentals`, `/acm-observability` already in matrix row
- Context7: LangGraph + LangChain (pipeline type always)
- Output: prompt-pack

**PromptPlan excerpt:**
```json
{
  "selected_skills": ["/langgraph-fundamentals", "/acm-observability", "/planning-with-files", "/verification-before-completion"],
  "agent_strategy": "tmux-team",
  "context7_directives": ["resolve-library-id for \"langgraph\" → query-docs for \"graph nodes\""],
  "output_format": "prompt-pack",
  "plan_type": "full"
}
```

### Example B — Bug Fix (medium)

**Input classification:**
```json
{
  "type": "bug-fix",
  "complexity": 5,
  "plan_mode": true,
  "domain_signals": ["error", "trace", "graph"],
  "scope": "single-file",
  "estimated_files": 2
}
```

**Routing result:**
- Matrix row: `bug-fix + any` → solo focused agent
- Domain signals: `"error"`, `"trace"` → `/systematic-debugging`, `/acm-observability`; `"graph"` → `/langgraph-fundamentals`
- Context7: conditional (error relates to library API? if yes, add LangGraph)
- Output: copy-paste

### Example C — Quick Task (simple)

**Input classification:**
```json
{
  "type": "quick-task",
  "complexity": 1,
  "plan_mode": false,
  "domain_signals": [],
  "scope": "single-file",
  "estimated_files": 1
}
```

**Routing result:**
- Matrix row: `quick-task` → solo, no extra skills
- Context7: no
- Output: terminal

```json
{
  "selected_skills": [],
  "agent_strategy": "solo",
  "agent_config": { "solo": true, "panes": [], "subagents": [] },
  "context7_directives": [],
  "output_format": "terminal",
  "plan_mode": false,
  "plan_type": "none",
  "verification_items": ["uv run ruff check ."]
}
```
