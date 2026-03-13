# Request Classification Taxonomy

This reference defines the 8 request types, complexity scoring algorithm, plan mode decision tree, and output schema used by the `request-classifier` skill.

---

## Table of Contents

1. [Request Types (8 types)](#request-types)
2. [Complexity Scoring Algorithm](#complexity-scoring-algorithm)
3. [Plan Mode Decision Tree](#plan-mode-decision-tree)
4. [Classification Output Schema](#classification-output-schema)
5. [Domain Signal Glossary](#domain-signal-glossary)

---

## Request Types

### Overview Table

| Type | Primary Keywords | Secondary Signals | Plan Mode Default | Example |
|------|-----------------|-------------------|-------------------|---------|
| `feature` | add, implement, create, new, build, introduce | "I want", "we need", mentions new files | Yes (full plan) | "Add MinerU as a new extraction provider" |
| `bug-fix` | fix, broken, error, failing, crash, not working, wrong | Stack traces, error messages, "should but doesn't" | Yes (debug plan) | "Fix the extraction pipeline timeout error" |
| `research` | investigate, analyze, compare, audit, review, understand, explore | Questions ("why does…"), "look into", "find out" | Yes (research plan) | "Investigate why correction calls are high" |
| `improvement` | optimize, refactor, improve, clean up, modernize, speed up | "too slow", "messy", "technical debt" | Yes (refactor plan) | "Refactor pre-extraction stages to reduce LLM calls" |
| `pipeline` | extraction, graph, node, LangGraph, pipeline, state, edge | References to acm_extraction.py, orchestrator, ExtractionState | Yes (always) | "Add a caching layer to the extraction graph" |
| `frontend` | component, page, UI, React, Next.js, CSS, Tailwind, grid | References to frontend/, tsx files, Zustand stores | Conditional (complex=yes) | "Add SSE streaming to the upload wizard" |
| `quick-task` | rename, move, update, change, simple, just, only | Short request (<20 words), single file mentioned | No | "Rename extract_items to extract_acm_items" |
| `documentation` | document, docs, readme, write up, explain, guide | References to docs/, .md files | No | "Update the README with V3 features" |

---

### Detailed Type Definitions

#### `feature`
A request to add new, previously non-existent functionality to the system.

**Primary keywords:** add, implement, create, new, build, introduce, develop, make, generate, set up, scaffold, wire up

**Secondary signals:**
- Phrases like "I want", "we need", "should have", "it would be great if"
- Mentions of new files that don't currently exist
- References to a capability that doesn't yet exist in the codebase
- "integration with", "support for", "ability to"

**Plan mode default:** YES — full plan (new features almost always require scoping, file impact analysis, and step-by-step sequencing before coding begins)

**Distinguishing from `improvement`:** A feature adds something new; an improvement makes something existing better. "Add dark mode" = feature. "Make the existing theme toggle faster" = improvement.

**Examples:**
- "Add MinerU as a new extraction provider"
- "Implement a bulk-export endpoint for ACM records"
- "Build a notification system for failed extractions"
- "Create a CSV download button on the item grid"

---

#### `bug-fix`
A request to restore correct behavior that is currently broken or producing wrong output.

**Primary keywords:** fix, broken, error, failing, crash, not working, wrong, incorrect, unexpected, bad, issue, problem, bug, broken, regressed, off, missing (when something should be there)

**Secondary signals:**
- Stack traces or error messages included in the request
- "Should do X but does Y" or "used to work" phrasing
- Mentions of specific error codes, HTTP status codes, exceptions
- "Only happens when", "intermittently", "always fails when"
- Test names that are failing

**Plan mode default:** YES — debug plan (bug fixes need root-cause analysis before changes; jumping to code without understanding the cause leads to treating symptoms)

**Distinguishing from `improvement`:** A bug fix restores behavior that should already be correct. An improvement changes behavior intentionally. "The grid doesn't load" = bug-fix. "The grid loads too slowly" = improvement.

**Examples:**
- "Fix the extraction pipeline timeout error"
- "The correction node is being called when it shouldn't be"
- "SurrealDB param binding fails with record ID strings"
- "test_creates_acm_table_section_records is failing with a RecordID type mismatch"

---

#### `research`
A request to investigate, understand, compare, or analyze something — producing knowledge rather than code changes.

**Primary keywords:** investigate, analyze, compare, audit, review, understand, explore, examine, look into, find out, evaluate, assess, study, profile, measure, why, how does, what is

**Secondary signals:**
- Open-ended questions without a clear action outcome
- "Why does…" or "How does…" questions
- Requests to produce a report, findings, or summary
- Benchmarking or performance profiling requests
- Architecture review requests
- "Before we decide", "to inform", "so we can understand"

**Plan mode default:** YES — research plan (research tasks need a defined scope and methodology upfront or they sprawl indefinitely)

**Distinguishing from `bug-fix`:** Research seeks understanding; bug-fix seeks correction. "Investigate why correction calls are high" = research (understanding the cause). "Fix the overcorrection bug" = bug-fix (correcting known behavior).

**Examples:**
- "Investigate why correction calls are high in the pipeline"
- "Compare MinerU vs Docling table extraction quality"
- "Analyze extraction costs across the last 50 runs"
- "Why is the orchestrator making 3 LLM calls when 1 should suffice?"

---

#### `improvement`
A request to make existing, working functionality better — faster, cleaner, more maintainable, or more correct.

**Primary keywords:** optimize, refactor, improve, clean up, modernize, speed up, simplify, reduce, consolidate, streamline, restructure, decouple, extract, reorganize

**Secondary signals:**
- "Too slow", "too verbose", "messy", "hard to read", "technical debt"
- Performance metrics that aren't meeting a target but system works
- "Better", "cleaner", "more efficient", "more maintainable"
- Code quality concerns without broken behavior

**Plan mode default:** YES — refactor plan (improvement tasks benefit from a clear scope of what changes and what stays the same, to avoid inadvertent regressions)

**Examples:**
- "Refactor pre-extraction stages to reduce LLM calls"
- "The row extractor is too slow — optimize it"
- "Clean up the consensus engine, it's hard to follow"
- "Reduce the number of SurrealDB round-trips in building extraction"

---

#### `pipeline`
A request specifically involving the AI extraction pipeline, LangGraph graph structure, nodes, edges, state management, or orchestration layer.

**Primary keywords:** extraction, graph, node, LangGraph, pipeline, state, edge, orchestrator, workflow, chain, agent, tool call, routing, conditional edge, checkpoint, interrupt

**Secondary signals:**
- References to `acm_extraction.py`, `orchestrator.py`, `ExtractionState`
- References to specific graph nodes (preflight_node, correct_node, store_node, etc.)
- Mentions of SSE events, PipelineEventBus, StageId
- LangGraph-specific concepts: thread, checkpointer, invoke, stream
- "The graph", "the pipeline", "the workflow", "the agent"

**Plan mode default:** YES — always (pipeline changes are the highest-risk area; they affect the entire extraction workflow and require careful sequencing)

**Distinguishing from `feature`/`improvement`:** If the request is explicitly about modifying the graph topology (adding nodes, changing edges, modifying state) or the extraction orchestration layer, classify as `pipeline` even if it could also be called a feature or improvement. Pipeline takes precedence.

**Examples:**
- "Add a caching layer to the extraction graph"
- "The correct_node is running when it shouldn't — add a conditional edge to skip it"
- "Refactor ExtractionState to add a confidence_scores field"
- "Wire up the new provider adapter into the extraction pipeline"

---

#### `frontend`
A request specifically involving UI components, pages, or frontend-only changes in Next.js/React.

**Primary keywords:** component, page, UI, React, Next.js, CSS, Tailwind, grid, layout, button, modal, sidebar, form, hook, store, route, navigation, rendering, animation, responsive, SSR

**Secondary signals:**
- References to `frontend/` directory or `.tsx`/`.ts` files in the frontend
- Zustand store mentions (`buildingStore`, `streamingStore`)
- AG Grid references
- React Query hooks (`useBuildings`, `useACMItems`)
- UI/UX behavior descriptions ("when the user clicks", "it should show")

**Plan mode default:** CONDITIONAL — complexity score >= 7 triggers plan mode. Simple component tweaks don't need plans; cross-cutting UI changes (new pages, SSE integration, new grid features) do.

**Distinguishing from `feature`:** A frontend-only request with no backend involvement is `frontend`. A request that adds both a new API endpoint and a new UI for it is `feature` (cross-cutting).

**Examples:**
- "Add SSE streaming to the upload wizard" (complex → plan on)
- "Change the button color in ItemGrid to blue" (simple → plan off)
- "Build the building sidebar component" (medium, plan off)
- "Add a column filter dropdown to the AG Grid" (medium, plan off)

---

#### `quick-task`
A small, clearly scoped, single-action request that can be completed in minutes without planning.

**Primary keywords:** rename, move, update, change, simple, just, only, quickly, swap, replace (one thing), delete, remove (one thing), add (one line/field)

**Secondary signals:**
- Request body is under 20 words
- Only one file or one function is clearly the target
- No architectural decisions required
- Action is fully reversible with one git revert
- No new tests required (existing tests cover it)

**Plan mode default:** NO (planning a rename would take longer than doing it)

**Distinguishing from `feature`:** Quick-tasks are mechanical, zero-ambiguity changes. If the agent needs to decide _how_ to do something, it's not a quick-task.

**Examples:**
- "Rename extract_items to extract_acm_items"
- "Move the config_loader to the parsers/ directory"
- "Update the default Ollama model from llama3.1:7b to llama3.1:8b in .env.example"
- "Delete the deprecated mineru_runner.py script"

---

#### `documentation`
A request to write, update, or reorganize documentation, comments, or explanatory text.

**Primary keywords:** document, docs, readme, write up, explain, guide, comment, annotate, describe, summarize, update docs, add docstring, changelog, migration guide

**Secondary signals:**
- References to `.md` files, `docs/` directory
- "So people know how to", "to explain", "for the team"
- Docstring or inline comment requests
- CHANGELOG or release note requests

**Plan mode default:** NO (documentation can be written directly without scoping; the content itself is the plan)

**Examples:**
- "Update the README with V3 features"
- "Add docstrings to the ConsensusEngine class"
- "Write a migration guide for the new provider adapter pattern"
- "Document the plan mode decision tree in CLAUDE.md"

---

## Complexity Scoring Algorithm

Assign a score from **1–10** using the following rules. Sum contributing factors, then cap at 10.

### Scoring Dimensions

#### Word Count (0–3 points)
- <25 words in the request body → **+0**
- 25–80 words → **+1**
- >80 words → **+3**

#### File Scope (0–3 points)
- 0–1 files mentioned or implied → **+0**
- 2–4 files → **+1**
- 5+ files → **+3**

#### Action Breadth (0–2 points)
- Single, atomic action → **+0**
- Multiple related actions (same layer, same domain) → **+1**
- Cross-cutting actions (backend + frontend, multiple domains) → **+2**

#### Request Type Baseline (0–2 points)
- `quick-task`, `documentation` → **+0**
- `bug-fix`, `improvement`, `frontend` (simple) → **+1**
- `feature`, `research`, `pipeline` → **+2**

#### Complexity Amplifiers (bonus, up to +2 additional)
- Contains "across", "all", "entire", "system-wide" → **+1**
- Cross-backend + cross-frontend in one request → **+1**
- Request mentions 3+ distinct technologies/systems → **+1** (capped at +2 total amplifier)

### Level Bands

| Score | Level | Description |
|-------|-------|-------------|
| 1–3 | Simple | Quick, single-file, single-action work |
| 4–6 | Medium | Multi-step, 2–4 files, one domain |
| 7–10 | Complex | Cross-cutting, architectural, or open-ended |

### Scoring Examples

**"Rename extract_items to extract_acm_items"**
- Word count: <25 → 0
- Files: 1 → 0
- Action breadth: single → 0
- Type baseline: quick-task → 0
- Amplifiers: none → 0
- **Total: 0 → Score 1 (Simple)**

**"Fix the extraction pipeline timeout error when processing large PDFs"**
- Word count: <25 → 0
- Files: 2–3 implied (acm_extractor, orchestrator) → 1
- Action breadth: single action, single domain → 0
- Type baseline: bug-fix → 1
- Amplifiers: none → 0
- **Total: 2 → Score 3 (Simple)**

**"Refactor pre-extraction stages to reduce LLM calls across the orchestrator"**
- Word count: 25–80 → 1
- Files: 3–4 implied → 1
- Action breadth: multiple related → 1
- Type baseline: improvement → 1
- Amplifiers: "across" → 1
- **Total: 5 → Score 5 (Medium)**

**"Investigate why correction calls are high and propose a remediation strategy with benchmarks"**
- Word count: 25–80 → 1
- Files: multiple implied → 1
- Action breadth: multiple actions (investigate + propose + benchmark) → 2
- Type baseline: research → 2
- Amplifiers: cross-system → 1
- **Total: 7 → Score 7 (Complex)**

**"Add SSE streaming to the upload wizard so the frontend shows real-time extraction progress, wiring it through from the PipelineEventBus to a new React hook and updating the Zustand store"**
- Word count: >80 → 3
- Files: 5+ (event bus, router, hook, store, component) → 3
- Action breadth: cross-cutting (backend + frontend) → 2
- Type baseline: feature → 2
- Amplifiers: cross-backend+frontend → 1
- **Total: 11 → Capped at Score 10 (Complex)**

---

## Plan Mode Decision Tree

```
START: Evaluate request

Step 1 — Check for explicit override keywords in the request:
  ├─ Contains "no plan", "skip planning", "just do it", "don't plan", "plan off"
  │   └─ PLAN MODE: OFF (override)
  └─ Contains "with planning", "plan first", "research before", "investigate before",
               "plan this out", "plan mode"
      └─ PLAN MODE: ON (override)

[No override found — proceed to automatic detection]

Step 2 — Check request type:
  ├─ Type is [feature, bug-fix, research, improvement, pipeline]
  │   └─ PLAN MODE: ON
  └─ Type is [frontend, quick-task, documentation]
      └─ Proceed to Step 3

Step 3 — Check complexity score:
  ├─ Complexity score >= 7
  │   └─ PLAN MODE: ON
  └─ Complexity score < 7
      └─ PLAN MODE: OFF

END: Set plan_mode and plan_type
```

### Plan Type Selection

When plan_mode is ON, select the plan type based on request type:

| Request Type | Plan Type |
|-------------|-----------|
| `feature` | `full` |
| `bug-fix` | `debug` |
| `research` | `research` |
| `improvement` | `refactor` |
| `pipeline` | `full` |
| `frontend` (complex) | `full` |
| Any with override "plan mode ON" | match type above, or `full` if no match |

When plan_mode is OFF, set `plan_type` to `null`.

---

## Classification Output Schema

Emit this JSON at the end of classification. Do not omit any field — use `null` for absent optional values.

```json
{
  "request_type": "feature|bug-fix|research|improvement|pipeline|frontend|quick-task|documentation",
  "complexity": {
    "score": 7,
    "level": "simple|medium|complex",
    "reasoning": "Brief explanation of why this score was assigned (1-2 sentences)"
  },
  "plan_mode": true,
  "plan_type": "full|debug|research|refactor|null",
  "keywords_matched": ["add", "new", "provider"],
  "files_mentioned": ["open_notebook/extractors/", "frontend/src/"],
  "domain_signals": ["pipeline", "extraction"],
  "override": "on|off|null"
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `request_type` | string | One of the 8 type identifiers |
| `complexity.score` | int 1–10 | Numeric score (1 = trivially simple, 10 = maximally complex) |
| `complexity.level` | string | "simple" (1–3), "medium" (4–6), "complex" (7–10) |
| `complexity.reasoning` | string | Short explanation of what drove the score |
| `plan_mode` | bool | Whether planning phase should precede coding |
| `plan_type` | string\|null | Plan style to use; null when plan_mode is false |
| `keywords_matched` | string[] | Primary and secondary keywords found in request |
| `files_mentioned` | string[] | File paths, directories, or module names explicitly mentioned |
| `domain_signals` | string[] | Technical domain indicators detected (e.g., "langgraph", "surrealdb", "frontend") |
| `override` | string\|null | "on" or "off" if an explicit plan override was detected; null otherwise |

---

## Domain Signal Glossary

Use these when populating the `domain_signals` field:

| Signal | When to Apply |
|--------|--------------|
| `langgraph` | Mentions of graphs, nodes, edges, ExtractionState, LangGraph |
| `pipeline` | Any extraction pipeline, orchestrator, or workflow reference |
| `surrealdb` | Database queries, schema migrations, record IDs, SurrealDB |
| `frontend` | Next.js, React, components, pages, hooks, stores, AG Grid |
| `fastapi` | Routers, endpoints, services, API layer |
| `extraction` | ACM records, table extraction, MinerU, Docling, parsing |
| `observability` | Langfuse, LangSmith, tracing, spans, logging |
| `testing` | pytest, test files, assertions, mocks, fixtures |
| `configuration` | .env, environment variables, settings, config loading |
| `domain-model` | Pydantic models, domain entities, schemas, validators |
