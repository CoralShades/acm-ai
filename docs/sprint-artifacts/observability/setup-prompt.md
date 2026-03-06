# ACM-AI Observability Stack Setup — Session Prompt

**Copy everything below this line and paste as your first message in a new Claude Code session.**

---

## Task: Set Up Full Observability Stack (Langfuse + LangSmith + LangGraph Studio)

You are continuing work from a prior research session. All findings, comparisons, and task plans are already written. Your job is to:

1. **PLAN FIRST** — Use `/planning-with-files` to read prior research, analyze existing code and architecture, then produce a detailed implementation plan using `/writing-plans`
2. **RESEARCH** — Use Context7 MCP (`resolve-library-id` then `query-docs`) to fetch current documentation for Langfuse, LangSmith, and LangGraph Studio
3. **IMPLEMENT** — Use `/subagent-driven-development` or `/dispatching-parallel-agents` to execute the plan: install dependencies, create configs, wire callbacks, verify each tool
4. **VERIFY** — Use `agent-browser` (the skill at `.claude/skills/agent-browser/SKILL.md`) to visit each UI and confirm traces, graphs, and dashboards are live
5. **COMPLETE** — Use `/verification-before-completion` before claiming anything is done

### Required Skills (Invoke These)

You MUST invoke these skills via the `Skill` tool at the appropriate phase:

| Phase | Skill | Why |
|-------|-------|-----|
| Start | `/planning-with-files` | Read progress.md reboot check, recover context |
| Planning | `/writing-plans` | Create bite-sized task plan in `docs/plans/` |
| Execution | `/subagent-driven-development` | Fresh subagent per task with two-stage review |
| Parallel research | `/dispatching-parallel-agents` | 3 Context7 research agents in parallel |
| Bug investigation | `/systematic-debugging` | If anything breaks during setup |
| Browser verification | `agent-browser` skill (`.claude/skills/agent-browser/SKILL.md`) | Visit localhost UIs to verify each tool |
| Completion | `/verification-before-completion` | Evidence before claims |

**Subagent capabilities:** When dispatching subagents, they have FULL tool access — Read, Write, Edit, Bash, Glob, Grep, Agent, MCP tools (including Context7 and chrome-devtools). Do NOT restrict subagent tools. Let them use whatever they need.

### Prior Research (Read These First)

Read these three files before doing ANYTHING (use `/planning-with-files` to check progress.md reboot check):
- `docs/sprint-artifacts/observability/findings.md` — Full head-to-head comparison of all 3 tools, capability matrix, issue-to-tool mapping for 13 open GitHub issues
- `docs/sprint-artifacts/observability/task_plan.md` — 4-phase rollout plan (Phase 2 is your focus)
- `docs/sprint-artifacts/observability/progress.md` — Session recovery journal with reboot check

### Current Environment State (As of Session Start)

**Already configured by the user:** : @.env
- `LANGCHAIN_API_KEY` — set in `.env` (obtained from LangSmith web console)
- `LANGSMITH_API_KEY` — set in `.env` (may be same key as LANGCHAIN_API_KEY — verify this)
- `LANGSMITH_PROJECT=acm-ai-dev` — NOT changed yet. Unclear if this needs to match a cloud project name. **Research this via Context7.**
- A LangSmith cloud project ID has been added (empty project, no traces yet)
- `LANGFUSE_ENABLED` — user set to `true` in `.env`
- Langfuse cloud keys (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`) — set for cloud
- Langfuse self-hosted Docker container — **NOT configured yet.** User wants local Docker config added to the ACM container stack
- The extraction pipeline has NOT been tested with observability enabled yet — no traces exist anywhere

**What needs investigation:**
1. Are `LANGCHAIN_API_KEY` and `LANGSMITH_API_KEY` the same key? (LangSmith console gives one key)
2. Does `LANGSMITH_PROJECT` need to match an existing project in the LangSmith UI, or is it auto-created?
3. Langfuse self-hosted: should it be added to the existing `docker-compose.yml` or a separate overlay file?
4. With `LANGFUSE_ENABLED=true` and cloud keys set, does the extraction pipeline already send traces to Langfuse cloud? Test this.

### What Already Exists (Do NOT Recreate)

**Langfuse (partially built):**
- `open_notebook/observability/langfuse_config.py` — `get_langfuse_handler()`, `append_langfuse_callback()`, `build_langfuse_metadata()`, `flush_langfuse_handler()`
- `open_notebook/observability/langfuse_bridge.py` — `emit_pipeline_event()` for PipelineLogger -> Langfuse span correlation
- `open_notebook/observability/__init__.py` — re-exports all public functions
- `langfuse>=3.14.5` already in `pyproject.toml`
- Wired into `acm_extraction.py` (line ~3596) and `source_commands.py` (line ~612)
- `scripts/observability/setup_langfuse_datasets.py` — dataset creation script
- `.env.example` has `LANGFUSE_ENABLED=false`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL`

**LangSmith (env vars only):**
- `.env.example` has `LANGCHAIN_TRACING_V2=false`, `LANGCHAIN_API_KEY`, `LANGSMITH_PROJECT=acm-ai-dev`
- Zero Python code — LangSmith auto-traces via LangChain runtime when env vars are set
- No dependencies needed (comes with `langchain-core`)

**LangGraph Studio (partially built):**
- `langgraph.json` — registers only `acm_extraction` graph via `studio_entry.py`
- `open_notebook/graphs/studio_entry.py` — loads `.env`, warns if SurrealDB missing, exports compiled graph
- `langgraph-cli` NOT in `pyproject.toml` (install separately)

### What's NOT Wired (Your Work)

**Langfuse callbacks missing from these graphs:**
| Graph | File | Compiled As | Complexity |
|-------|------|-------------|------------|
| chat | `open_notebook/graphs/chat.py` | `graph` (line 85) | Simple (1 node) |
| source_chat | `open_notebook/graphs/source_chat.py` | `source_chat_graph` (line 335) | Simple (1 node) |
| supervisor | `open_notebook/graphs/supervisor_agent.py` | `supervisor_graph` (line 155) | Medium (ReAct loop) |
| transformation | `open_notebook/graphs/transformation.py` | `graph` (line 67) | Simple (1 node) |
| source | `open_notebook/graphs/source.py` | `source_graph` (line 187) | Simple |
| prompt | `open_notebook/graphs/prompt.py` | `graph` (line 42) | Simple |
| ask | `open_notebook/graphs/ask.py` | `graph` (line 146) | Simple |
| doc_search | `open_notebook/graphs/doc_search_agent.py` | `doc_search_graph` (line 120) | Medium |
| crud_agent | `open_notebook/graphs/crud_agent.py` | `crud_graph` (line 121) | Medium |
| acm_analyst | `open_notebook/graphs/acm_analyst_agent.py` | `acm_analyst_graph` (line 126) | Medium |

**LangGraph Studio missing registrations:**
- `supervisor_agent` (most complex after extraction — ReAct loop with tools)
- Optionally: `acm_analyst_agent`, `doc_search_agent`

**No Langfuse self-hosted Docker config exists.**

### Implementation Steps (Phase 2 from task_plan.md)

#### Step 1: Research (Use Context7 + `/dispatching-parallel-agents`)

Spawn 3 parallel research subagents. Each MUST use Context7 MCP tools (`resolve-library-id` then `query-docs`):

1. **Langfuse self-hosted setup** — Use Context7 to resolve `langfuse` library and query for:
   - Docker Compose setup for self-hosted v3 (PostgreSQL + Redis + ClickHouse + Langfuse)
   - Or v2 if v3 is too heavy (PostgreSQL + Langfuse only)
   - Environment variables needed
   - How to create API keys after first launch
   - Whether `LANGCHAIN_API_KEY` and `LANGSMITH_API_KEY` are the same key
   - Whether `LANGSMITH_PROJECT` auto-creates or must exist first

2. **LangGraph Studio CLI** — Use Context7 to resolve `langgraph` library and query for:
   - `langgraph dev` command and options
   - `langgraph.json` schema for registering multiple graphs
   - Requirements (Python version, dependencies)
   - Whether `langgraph-cli` needs to be in pyproject.toml or installed globally

3. **Langfuse LangChain callback** — Use Context7 to resolve `langfuse` and query for:
   - Current `CallbackHandler` API for LangChain integration
   - How to attach callbacks to `graph.invoke()` and `graph.astream()` calls
   - Session grouping and metadata patterns
   - The `@observe()` decorator for non-LangChain code (Docling extractors, MinerU)

#### Step 2: Langfuse Self-Hosted Docker Config

Create `docker-compose.observability.yml` (separate overlay, not modifying the main docker-compose.yml):
- PostgreSQL for Langfuse data
- Redis (if v3 requires it)
- ClickHouse (if v3 requires it, otherwise skip)
- Langfuse web server on port 3000
- Network shared with existing `acm-ai` services
- Volumes for data persistence

Usage: `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d`

#### Step 3: Wire Langfuse Into Remaining Graphs

Follow the EXACT pattern from `acm_extraction.py:3596-3697`:
```python
from open_notebook.observability.langfuse_config import (
    append_langfuse_callback,
    build_langfuse_metadata,
    flush_langfuse_handler,
    get_langfuse_handler,
)

# At invocation point:
langfuse_handler = get_langfuse_handler()
callbacks = append_langfuse_callback([], langfuse_handler)
metadata = build_langfuse_metadata(source_id=..., ...)

# Pass to graph.invoke() or graph.ainvoke():
config = {"callbacks": callbacks, "metadata": metadata}

# After completion:
flush_langfuse_handler(langfuse_handler)
```

**Priority order** (by usage frequency and complexity):
1. `supervisor_agent.py` — most used, has tools
2. `chat.py` — user-facing
3. `source_chat.py` — user-facing
4. `transformation.py` — background processing
5. The rest (source, prompt, ask, doc_search, crud_agent, acm_analyst) — lower priority, wire if time permits

**For each graph**, find where `.invoke()` / `.ainvoke()` / `.astream()` is called and wrap with the callback pattern. The handler is non-fatal by design — if Langfuse is disabled or credentials are missing, `get_langfuse_handler()` returns `None` and the callback list is empty.

#### Step 4: Register Additional Graphs in langgraph.json

Update `langgraph.json` to register additional graphs for Studio debugging:
```json
{
  "dependencies": ["."],
  "graphs": {
    "acm_extraction": "./open_notebook/graphs/studio_entry.py:graph",
    "supervisor": "./open_notebook/graphs/supervisor_agent.py:supervisor_graph",
    "acm_analyst": "./open_notebook/graphs/acm_analyst_agent.py:acm_analyst_graph"
  },
  "env": ".env"
}
```

Note: Only graphs that DON'T require a running checkpointer at import time can be registered. Graphs compiled with `checkpointer=memory` (like chat, source_chat) may need a studio entry wrapper similar to `studio_entry.py`.

#### Step 5: Install LangGraph CLI

```bash
uv tool install langgraph-cli
# OR add to pyproject.toml dev dependencies:
# langgraph-cli>=0.1.0
```

Verify: `langgraph dev` should open browser UI showing the registered graphs.

#### Step 6: Update .env.example

Add documentation for the complete observability config:
```bash
# --- Observability ---
# LangSmith (dev only — cloud, auto-traces all graphs)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGSMITH_PROJECT=acm-ai-dev

# Langfuse (production — self-hosted, requires explicit callback wiring)
LANGFUSE_ENABLED=false
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_BASE_URL=https://cloud.langfuse.com
# For self-hosted: LANGFUSE_BASE_URL=http://localhost:3000

# LangGraph Studio (dev only — needs LANGSMITH_API_KEY for auth)
# Run: langgraph dev
# Config: langgraph.json
```

#### Step 7: Browser Verification (Use `agent-browser`)

After setup, verify EACH tool is working by visiting its UI. Use `agent-browser` (installed at `/c/nvm4w/nodejs/agent-browser`):

**7A. Verify Langfuse Cloud (traces visible):**
```bash
# First: run a short extraction or chat to generate traces
# Then verify Langfuse cloud dashboard shows traces
agent-browser open https://cloud.langfuse.com && agent-browser wait --load networkidle && agent-browser snapshot -i
# Login if needed, navigate to the project, verify traces exist
```

**7B. Verify Langfuse Self-Hosted (Docker running, UI accessible):**
```bash
agent-browser open http://localhost:3000 && agent-browser wait --load networkidle && agent-browser snapshot -i
# Should show Langfuse login/dashboard
agent-browser screenshot "docs/sprint-artifacts/observability/evidence/langfuse-local.png"
```

**7C. Verify LangSmith (traces visible):**
```bash
agent-browser open https://smith.langchain.com && agent-browser wait --load networkidle && agent-browser snapshot -i
# Navigate to acm-ai-dev project, verify traces appear
agent-browser screenshot "docs/sprint-artifacts/observability/evidence/langsmith-traces.png"
```

**7D. Verify ACM-AI Frontend (extraction pipeline works with observability):**
```bash
# Verify the frontend is up and extraction can be triggered
agent-browser open http://localhost:8503 && agent-browser wait --load networkidle && agent-browser snapshot -i
# Navigate to a source, trigger extraction, verify progress tracking works
agent-browser screenshot "docs/sprint-artifacts/observability/evidence/frontend-extraction.png"
```

**7E. Verify LangGraph Studio (if running):**
```bash
# After running `langgraph dev`, Studio opens on a local port
agent-browser open http://localhost:8123 && agent-browser wait --load networkidle && agent-browser snapshot -i
agent-browser screenshot "docs/sprint-artifacts/observability/evidence/studio-graphs.png"
```

Save all screenshots to `docs/sprint-artifacts/observability/evidence/` as proof.

**agent-browser workflow reminder:**
1. `agent-browser open <url>` — navigate
2. `agent-browser wait --load networkidle` — wait for page load
3. `agent-browser snapshot -i` — get interactive elements with refs (@e1, @e2)
4. `agent-browser click @e1` / `agent-browser fill @e2 "text"` — interact using refs
5. `agent-browser screenshot <path>` — capture evidence
6. Re-snapshot after any page navigation or DOM changes

### Constraints

- **NEVER modify `acm_extraction.py` Langfuse wiring** — it already works correctly
- **NEVER put LangSmith env vars in production .env** — dev only, data privacy concern
- **Langfuse callbacks must be non-fatal** — extraction must never break if Langfuse is down
- **Use the existing pattern** — don't invent new observability abstractions
- **Don't add `langfuse` imports to files that don't invoke graphs** — callbacks go at the invocation site, not inside graph node functions
- **Windows/WSL path rules apply** — use `$CLAUDE_PROJECT_DIR` or `D:/ailocal/acm-ai` with forward slashes. Never `cd /d/...` or `cd D:\...`
- **Protected files**: don't modify `tests/`, `migrations/`, `pyproject.toml` dependencies without asking
- **Context7 is mandatory**: When looking up library docs, ALWAYS use Context7 MCP (`resolve-library-id` then `query-docs`). Do NOT rely on training data for Langfuse, LangSmith, or LangGraph API details.

### Issue Context (Why This Matters)

7 of your 13 open GitHub issues benefit directly from having observability enabled:

| Issue | Primary Tool Needed | What It Enables |
|-------|-------------------|-----------------|
| #100 room_name misalignment | LangSmith playground | Iterate extraction prompt without re-running pipeline |
| #97 correction format=json | Studio | Inspect model config at the `correct` node |
| #99 progress stuck running | Studio | Step to END node, find which path skips finalize() |
| #84 SF picklist corruption | All three | Loop debug + prompt fix + regression tracking |
| #94 Anthropic Direct gap | Studio | Step through provider selection logic |
| #93 Ollama hardening | LangSmith playground | Test same prompt across 6 Ollama models |
| PR#55 C1-C4 Qwen bugs | Studio | State inspection for undefined vars, dropped buildings |

### Output Expected

When done, update `docs/sprint-artifacts/observability/progress.md` with:
- What was installed/configured
- Verification results (which tools are working) — include screenshot paths as evidence
- Answers to the investigation questions (API key identity, project naming, Docker strategy)
- Any blockers or decisions that need user input
- Next steps for Phase 3 (using the tools to fix issues)

### Execution Flow Summary

```
1. Invoke /planning-with-files → read progress.md reboot check
2. Read findings.md + task_plan.md → understand scope
3. Invoke /writing-plans → create bite-sized plan in docs/plans/
4. Invoke /dispatching-parallel-agents → 3 Context7 research subagents
5. Invoke /subagent-driven-development → execute plan tasks with review
   - For each task: implement → spec review → code quality review
   - Use /systematic-debugging if anything breaks
6. Use agent-browser to verify each UI (Langfuse, LangSmith, Frontend, Studio)
7. Invoke /verification-before-completion → evidence before claims
8. Update progress.md with results and evidence
```
