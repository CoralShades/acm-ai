# Observability & Tracing — Findings

## Date: 2026-03-06

---

## 1. Three Tools Head-to-Head — Complete Comparison

### 1A. Core Identity

| Dimension | LangGraph Studio | LangSmith | Langfuse |
|-----------|-----------------|-----------|----------|
| **What it is** | Desktop graph debugger | Cloud tracing + prompt lab | Self-hosted trace archive + analytics |
| **Analogy** | VS Code debugger with breakpoints | Chrome DevTools Network tab + replay | Datadog APM for LLMs |
| **When you use it** | During dev, one run at a time | During + after dev, many runs | After dev, production monitoring |
| **Core question** | "What's happening inside THIS run?" | "What prompt caused THAT output?" | "How are ALL runs performing?" |

### 1B. Capability Matrix

| Capability | Studio | LangSmith | Langfuse |
|------------|--------|-----------|---------|
| Visual DAG topology | **YES** — live graph with edges | Partial — trace shows node order | **NO** — flat span tree |
| Pause + step through nodes | **YES** | NO | NO |
| Inspect LangGraph state at node | **YES** — full state object | NO — only LLM I/O | NO |
| Modify state mid-run | **YES** | NO | NO |
| Re-run from specific node | **YES** | NO | NO |
| Human-in-the-loop injection | **YES** | NO | NO |
| Auto-trace ALL graphs | NO — register in langgraph.json | **YES** — 2 env vars, zero code | NO — wire callbacks per graph |
| Prompt playground (edit + re-run) | NO | **YES** — click any traced call | NO |
| Side-by-side prompt comparison | NO | **YES** | NO |
| Historical trace storage | NO — ephemeral | **YES** — thousands, searchable | **YES** — unlimited if self-hosted |
| Cost/token tracking | NO | YES — per call | **YES** — per model, per provider |
| Evaluation datasets | NO | **YES** — build from traces | **YES** — scoring + datasets |
| Regression monitoring | NO | YES — annotation queues | YES — score trends |
| Self-hostable | **YES** — fully local | **NO** — cloud only | **YES** — Docker Compose |
| Data privacy | **BEST** — nothing leaves machine | **WORST** — all data to cloud | **GOOD** — self-host keeps data local |
| Free tier limit | Unlimited (local) | 5,000 traces/mo (~380 extractions) | 50K obs/mo (cloud) or unlimited (self-hosted) |
| Setup effort | Register graphs + `langgraph dev` | 2 env vars | Docker Compose + env vars + wire callbacks |
| Works offline | YES | NO | YES (self-hosted) |

### 1C. Development vs Production

| Scenario | Studio | LangSmith | Langfuse |
|----------|--------|-----------|---------|
| **Dev: prompt iteration** | Poor — edit file, restart, re-run | **Best** — playground, instant re-run | Poor — view only, no replay |
| **Dev: debug pipeline flow** | **Best** — pause, inspect, modify | Good — trace shows flow | Poor — flat spans |
| **Dev: coverage (all graphs)** | Poor — must register each | **Best** — auto, zero config | Poor — must wire each |
| **Prod: monitoring** | N/A — not a prod tool | Good but cloud-only | **Best** — self-hosted |
| **Prod: cost control** | N/A | Good | **Best** — per-provider breakdown |
| **Prod: data privacy** | N/A | **Fails** — no self-host | **Best** — full control |
| **Prod: alerting/regression** | N/A | Yes | Yes |

---

## 2. Complete Issue Inventory

### 2A. GitHub Issues (Open)

| # | Title | Type | Severity | System Area |
|---|-------|------|----------|-------------|
| 101 | OpenRouter fallback chain non-functional (HTTP 402) | Bug | CONCERN | Provider fallback |
| 100 | room_name field misalignment (material in room_name) | Bug | CONCERN | Extraction prompts |
| 99 | extraction_progress stuck at "running" | Bug | BLOCKER | Pipeline logger / DB |
| 98 | Test logs contaminate production log files | Bug | CONCERN | Logging infra |
| 97 | Correction stage format=json not applied (100% Ollama failure) | Bug | CONCERN | Correction stage |
| 96 | backfill-buildings HTTP 500 (Source.name AttributeError) | Bug | BLOCKER | API endpoint |
| 94 | Anthropic Direct provider never tested (routing gap) | Gap | P0 | Provider selection |
| 93 | Ollama extraction hardening (format=json, num_ctx, chunking) | Bug | P0 | Extraction / Ollama |
| 92 | Model defaults don't persist to SurrealDB | Bug | P1 | API / DB |
| 91 | Sync upload 500 — asyncio.run() in event loop | Bug | P1 | API / Upload |
| 90 | SSE falls back to polling on completed jobs | Bug | Minor | Frontend / SSE |
| 89 | V3 building register empty for pre-V3 sources | Bug | Data | Migration / DB |
| 84 | SF picklist mismatches in runtime config files (F2-F8) | Bug | HIGH | Validation pipeline |

### 2B. Local Issues (docs/issues/) — Additional Context

| File | Adds to GH# | Extra Detail |
|------|-------------|--------------|
| pr55-qwen25-extraction-quality-review.md | (no GH#) | 4 critical bugs + 6 high-severity + 2 missing test files from PR #55 review |
| pr55-fix-session-prompt.md | (no GH#) | Fix session template for PR #55 bugs |
| v3-continuation-sf-validation-pipeline.md | Extends #84 | BAR path A runs upstream of SF path B — correction loop permanently corrupts SF-valid data |
| v3-persist-pre-extraction-intelligence.md | #85 | DONE — pre-extraction models now persisted |
| ollama-content-chunking.md | Part of #93 | Fixed in E32-S8 (hard-truncation bug) |
| ollama-extraction-hardening.md | = #93 | Umbrella issue for Ollama fixes |

---

## 3. Issue-by-Issue: How Each Tool Helps

### Legend
- **Observe** = detect the problem exists
- **Validate** = confirm the fix works
- **Fix** = directly aid in implementing the fix

---

### #101 — OpenRouter HTTP 402 Fallback Failure

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | Step through fallback chain → see state when OpenRouter is tried → see 402 not caught | Pause at fallback node → confirm Anthropic Direct is reached before OpenRouter | Modify state to simulate "Ollama down" → test fallback path |
| **LangSmith** | Auto-trace shows the failed OpenRouter call with 402 in trace | Re-run extraction → trace confirms fallback order | Prompt playground N/A (not a prompt issue) |
| **Langfuse** | Historical traces show 402 errors over time, frequency, cost of failed calls | Before/after cost comparison | N/A |
| **Best combo** | **Studio** (debug fallback logic) + **Langfuse** (monitor recurrence) |

---

### #100 — room_name Field Misalignment

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | Pause at `extract_items` → inspect state → see room_name has material text | Step to `validate` → confirm room_name now has actual room names | Inspect the exact markdown chunk fed to LLM |
| **LangSmith** | **BEST** — open `extract_items` LLM call → see rendered prompt → spot that field description is ambiguous | **BEST** — playground: edit prompt to clarify room_name vs product vs location_detail → re-run → compare output | **BEST** — iterate prompt 5x in playground without re-running pipeline |
| **Langfuse** | See that 100% of Alexander extractions have low quality scores | Score before/after traces | N/A |
| **Best combo** | **LangSmith** (prompt iteration) then **Studio** (end-to-end flow validation) |

---

### #99 — extraction_progress Stuck at "running" (BLOCKER)

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | Step to final `save` node → check if pipeline_logger.finalize() is called → inspect state for terminal status | Re-run → confirm status reaches "completed" at END node | Modify state to force different paths → find which path skips finalize |
| **LangSmith** | Auto-trace shows whether the graph reaches END node (trace structure) | Re-run trace confirms graph completes | N/A (DB write issue, not LLM issue) |
| **Langfuse** | Bridge events show stage timings — can see if STORE stage_exit is ever emitted | Before/after: STORE span now appears in all traces | N/A |
| **Best combo** | **Studio** (find which code path misses finalize) + **Langfuse** (monitor fix across many runs) |

---

### #98 — Test Log Contamination

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | N/A — not a graph issue | N/A | N/A |
| **LangSmith** | N/A — not a graph issue | N/A | N/A |
| **Langfuse** | **Partially** — contaminated traces (test runs appearing in prod) are visible, but root cause is logging config | Verify test traces stop appearing in prod Langfuse project | N/A |
| **Best combo** | None needed — this is a pytest config fix, not an observability issue |

---

### #97 — Correction Stage format=json Missing (100% Ollama Failure)

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | **BEST** — pause at `correct` node → see LLM response is conversational text, not JSON → see format=json missing on model config | Step through: extraction (has format=json) vs correction (missing it) — side by side | Inspect model object at correct node — confirm format param |
| **LangSmith** | Trace shows `correct` LLM call output — see "Expecting value: line 1 column 1" repeatedly | Re-run correction call in playground with format=json added | Playground: test if format=json fixes the output |
| **Langfuse** | See 100% correction failure rate across traces — 39 failures per run visible as nested spans | Before/after: correction success rate jumps from 0% to >80% | N/A |
| **Best combo** | **Studio** (pinpoint the missing param) + **LangSmith** (test the fix in playground) |

---

### #96 — backfill-buildings HTTP 500

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| All three | N/A — this is a simple `source.name → source.title` field rename. Not an LLM/graph issue. | N/A | N/A |
| **Best combo** | None — one-line code fix |

---

### #94 — Anthropic Direct Provider Never Tested

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | **BEST** — step through `provision_langchain_model()` → see which provider is selected → modify state to simulate Ollama failure → watch fallback | Confirm Anthropic Direct is reached in fallback chain | Force different provider states to test all paths |
| **LangSmith** | Auto-trace shows which model was actually used (model name in metadata) | Trace confirms anthropic model used when Ollama unavailable | N/A |
| **Langfuse** | Metadata tags show `extraction_model: "anthropic/..."` — verify across runs | Compare traces: Ollama vs Anthropic Direct vs OpenRouter | Cost comparison between providers |
| **Best combo** | **Studio** (debug provider selection) + **Langfuse** (verify in production) |

---

### #93 — Ollama Extraction Hardening (format=json, num_ctx, chunking)

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | Pause at `extract_building`/`extract_items` → inspect ChatOllama model object → verify format=json, num_ctx | Step through chunked extraction — see each chunk processed | Modify num_ctx in state → test effect on chunking |
| **LangSmith** | **BEST** — trace shows every LLM call with input size, model params, output quality | Playground: test different num_ctx values on same input | Compare prompt outputs across different Ollama models |
| **Langfuse** | Token usage per call reveals truncation (input tokens << expected) | Before/after: input token counts stabilize, output quality scores improve | Cost tracking across Ollama models |
| **Best combo** | **LangSmith** (prompt testing across models) + **Studio** (chunking logic debug) |

---

### #92 — Model Defaults Don't Persist

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| All three | N/A — DB persistence issue, not an LLM/graph issue | N/A | N/A |
| **Best combo** | None — SurrealDB migration + API fix |

---

### #91 — Sync Upload asyncio.run() Error

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| All three | N/A — async runtime error, not graph-related | N/A | N/A |
| **Best combo** | None — async/await fix in source_commands.py |

---

### #90 — SSE Falls Back to Polling on Completed Jobs

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| All three | N/A — frontend SSE connection issue | N/A | N/A |
| **Best combo** | None — frontend hook fix |

---

### #89 — V3 Building Register Empty for Pre-V3 Sources

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| All three | N/A — data migration issue | N/A | N/A |
| **Best combo** | None — migration script or re-extraction |

---

### #84 — SF Picklist Mismatches (F2-F8)

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | **BEST** — pause at `validate` → inspect which validator ran → see BAR values overwriting SF-valid data in `correct` | Step through validate → correct loop: watch BAR values fed to LLM via correction.jinja | Modify state at `correct` to inject SF-valid values → test if downstream accepts them |
| **LangSmith** | Trace shows correction prompt with BAR-only valid values — see the corruption happening | **BEST** — playground: test correction.jinja with SF-valid values included | Iterate prompt to include both BAR + SF valid values |
| **Langfuse** | Score traces for "SF compliance" — track how many records have SF-invalid values | Before/after: SF validation pass rate improves | N/A |
| **Best combo** | **Studio** (understand validate→correct loop) + **LangSmith** (iterate correction prompt) + **Langfuse** (track SF compliance over time) |

---

### PR #55 — Qwen 2.5 Critical Bugs (C1-C4, H1-H6)

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | C2: pause at extract_building → check if model_family is defined after provisioning fails. C4: pause → see entire building dropped on parse failure | Step through each fixed path | Force Qwen model in state → test all code paths |
| **LangSmith** | C1: trace shows NO_ACCESS_PHRASES substitution chain. C3: trace shows _early_qwen silently swallowed | Playground: test JSON parsing with Qwen output format | N/A for H1 (Pydantic mutation) — not an LLM issue |
| **Langfuse** | H5: see fallback errors without source_id context in traces | Before/after trace quality improves (richer metadata) | N/A |
| **Best combo** | **Studio** (C2, C4 — state inspection) + **LangSmith** (C1, C3 — trace the substitution/error flow) |

---

### v3-continuation-sf-validation-pipeline (extends #84)

| Tool | Observe | Validate | Fix |
|------|---------|----------|-----|
| **Studio** | **CRITICAL** — the BAR-upstream-of-SF corruption happens in the validate→correct→validate loop. Studio is the ONLY tool that lets you pause at `validate`, see which records are "invalid" per BAR but valid per SF, then step into `correct` and watch the LLM corrupt them | Confirm: SF-valid records now pass validation without triggering correction | Modify state to inject SF-valid "Negative - Treated as Positive" → verify it survives the loop |
| **LangSmith** | Trace shows the correction prompt with only BAR values → see the root cause of corruption | **BEST** for fix — edit correction.jinja in playground to include SF values → verify LLM preserves them | Iterate the unified prompt that handles both BAR + SF |
| **Langfuse** | Track "SF corruption rate" score over time across all extractions | Before/after: corruption rate drops to 0 | N/A |
| **Best combo** | ALL THREE — Studio (understand loop), LangSmith (fix prompt), Langfuse (verify across all docs) |

---

## 4. Summary: Which Issues Benefit Most From Observability

### Issues where observability is ESSENTIAL (can't efficiently fix without it)

| Issue | Primary Tool | Why |
|-------|-------------|-----|
| #100 room_name misalignment | **LangSmith** | Prompt iteration in playground — saves hours |
| #97 correction format=json | **Studio** | See model config at correct node |
| #84/#v3 SF validation pipeline | **All three** | Most complex issue — loop debug + prompt fix + regression tracking |
| #99 progress stuck running | **Studio** | Find which code path misses finalize |
| #94 Anthropic Direct gap | **Studio** | Step through provider selection logic |
| #93 Ollama hardening | **LangSmith** | Test across multiple models in playground |
| PR#55 C1-C4 | **Studio** | State inspection for undefined vars, dropped buildings |

### Issues where observability adds marginal value

| Issue | Why |
|-------|-----|
| #96 backfill 500 | One-line field rename |
| #92 model defaults | DB persistence, not LLM |
| #91 asyncio.run() | Async runtime fix |
| #90 SSE polling | Frontend hook fix |
| #89 empty buildings | Data migration |
| #98 test log contamination | Pytest config fix |

---

## 5. Recommended Setup (Revised — Phase 2B)

### Decision: Drop LangGraph Studio Cloud UI

LangGraph Studio's visual UI now requires a LangSmith cloud session (no standalone desktop app).
This conflicts with our data-privacy requirement for Victorian Government data.

**What we keep instead:**
- **LangGraph Dev Server** (`uv run langgraph dev`) — local API at `http://127.0.0.1:2024`
  - Swagger UI at `/docs` — fully local, no cloud
  - `GET /threads/{id}/state` — inspect graph state
  - `POST /threads/{id}/state` — update state
  - `POST /runs` — invoke graphs with specific input
  - `GET /assistants` — list registered graphs
- **Langfuse self-hosted** — trace visualization replaces Studio's "what happened" view
- **LangSmith cloud** — prompt playground replaces Studio's prompt debugging

### What Studio Features We Lose (and Mitigations)

| Studio Feature | Lost? | Mitigation |
|----------------|-------|------------|
| Visual DAG topology | Yes | Langfuse trace tree shows node execution order |
| Pause + step through nodes | Yes | Add strategic logging + inspect via Langfuse traces |
| Inspect full state at node | Partial | LangGraph API `GET /threads/{id}/state` (current state only, not per-node) |
| Modify state mid-run | Partial | LangGraph API `POST /threads/{id}/state` (between runs, not mid-run) |
| Re-run from specific node | Yes | Re-invoke full graph via API with modified input |
| Human-in-the-loop injection | Yes | Not needed for current issue backlog |

**Impact assessment:** The 7 issues marked "Studio is best tool" in Section 4 can still be debugged:
- **#99, #94, PR#55** — state inspection via LangGraph API + Langfuse traces
- **#97, #84** — LangSmith prompt playground covers the prompt iteration need
- **#100, #93** — LangSmith prompt playground is already the primary tool

### When to Use Which Tool

| Question | Tool | Why |
|----------|------|-----|
| "Why did this extraction produce wrong data?" | **LangSmith** | Trace the LLM call, edit prompt in playground, re-run |
| "How much is this costing across all runs?" | **Langfuse** | Self-hosted, per-provider cost/token dashboards |
| "What's the graph state for thread X?" | **LangGraph API** | `GET /threads/{id}/state` at `:2024` |
| "Is the pipeline healthy across many documents?" | **Langfuse** | Historical traces, score trends, regression detection |
| "Which code path does this graph take?" | **Langfuse** | Trace tree shows every node, timing, I/O |
| "What if I change this prompt?" | **LangSmith** | Prompt playground — edit, re-run, compare side-by-side |
| Production monitoring | **Langfuse only** | Self-hosted, data stays local (government requirement) |

### Development

```bash
# .env additions
LANGCHAIN_TRACING_V2=true              # LangSmith — auto-trace, prompt playground
LANGCHAIN_API_KEY=lsv2_pt_xxx          # from smith.langchain.com
LANGSMITH_PROJECT=acm-ai-dev

LANGFUSE_ENABLED=true                  # Langfuse — cost tracking, trace archive
LANGFUSE_BASE_URL=http://localhost:3000 # self-hosted
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
```

Plus `uv run langgraph dev` for local graph API + Swagger UI debugging.

### Production

```bash
LANGCHAIN_TRACING_V2=false             # OFF — no cloud data
LANGFUSE_ENABLED=true                  # Langfuse self-hosted only
LANGFUSE_BASE_URL=http://langfuse:3000
```

### Completed Code Changes (Phase 2A + 2B)

1. ~~Wire Langfuse into remaining graphs~~ — DONE (all 6 routers via `langfuse_tracing()`)
2. ~~Register supervisor_agent in langgraph.json~~ — DONE (Phase 2A)
3. ~~Add Langfuse self-hosted to docker-compose.observability.yml~~ — DONE (Phase 2A, v3 full stack)
4. Add format=json to correction LLM (#97 — one-line fix) — TODO (Phase 3)
