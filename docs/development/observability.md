# Observability & Tracing Guide

This document covers the six observability tools used in ACM-AI, how they work together, when to use each one, and practical workflows for debugging and optimizing the extraction pipeline.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [The Six Tools](#the-six-tools)
- [Configuration](#configuration)
- [Langfuse (Production Tracing)](#langfuse-production-tracing)
- [LangSmith (Dev Auto-Tracing + Prompt Lab)](#langsmith-dev-auto-tracing--prompt-lab)
- [LangGraph API (Graph State Debugger)](#langgraph-api-graph-state-debugger)
- [Logfire (Pydantic Validation Tracing)](#logfire-pydantic-validation-tracing)
- [erdantic (Model Relationship Diagrams)](#erdantic-model-relationship-diagrams)
- [JSON Crack (Interactive JSON Viewer)](#json-crack-interactive-json-viewer)
- [Head-to-Head Comparison](#head-to-head-comparison)
- [Practical Workflows](#practical-workflows)
- [Issue Debugging Matrix](#issue-debugging-matrix)
- [Wiring Langfuse Into New Graphs](#wiring-langfuse-into-new-graphs)
- [Registering Graphs in LangGraph API](#registering-graphs-in-langgraph-api)
- [Troubleshooting](#troubleshooting)
- [Reference Links](#reference-links)

---

## Architecture Overview

```
                    ┌─────────────────────────────────┐
                    │         Langfuse (:3000)         │
                    │   Self-hosted trace dashboard    │
                    │                                  │
                    │  ┌──────────┐  ┌──────────────┐ │
                    │  │ LangChain│  │  Pydantic     │ │
                    │  │ Callback │  │  Validation   │ │
                    │  │ Traces   │  │  Spans (OTel) │ │
                    │  └────▲─────┘  └──────▲───────┘ │
                    └───────┼───────────────┼─────────┘
                            │               │
              langfuse_tracing()      Logfire SDK
              (8 invocation sites)    (Pydantic auto-instrument)
                            │               │
                    ┌───────┴───────────────┴─────────┐
                    │         FastAPI Backend          │
                    │   Routers → Graphs → Extractors  │
                    │                                  │
                    │   ACMExtractionRecord (Pydantic) │
                    │   BuildingRecord (Pydantic)      │
                    │   ExtractionState (TypedDict)    │
                    └────────┬──────────────┬──────────┘
                             │              │
                    ┌────────▼──────┐  ┌────▼──────────┐
                    │ LangSmith     │  │ LangGraph API │
                    │ (cloud)       │  │ (:2024)       │
                    │ Prompt        │  │ State inspect  │
                    │ playground    │  │ Swagger UI     │
                    └───────────────┘  └───────┬───────┘
                                               │
                                      ┌────────▼───────┐
                                      │ dump_state_json │
                                      │ (helper script) │
                                      └────────┬───────┘
                                               │
                                      ┌────────▼───────┐
                                      │ JSON Crack     │
                                      │ (:8888)        │
                                      │ Interactive    │
                                      │ JSON viewer    │
                                      └────────────────┘

              ┌─────────────────────────────┐
              │  erdantic (dev CLI)         │
              │  generate_model_diagrams.py │
              │  → docs/diagrams/*.svg      │
              └─────────────────────────────┘
```

All tools can run simultaneously without conflicts. Langfuse hooks in via explicit callback injection. LangSmith hooks in via the LangChain runtime (env var). Logfire instruments Pydantic at import time and exports to Langfuse via OTel. JSON Crack and erdantic are standalone dev tools.

---

## The Six Tools

### Quick Identity

| Tool | What It Is | Analogy | Core Question |
|------|-----------|---------|---------------|
| **Langfuse** | Trace archive + analytics | Datadog APM for LLMs | "How are ALL runs performing?" |
| **LangSmith** | Cloud auto-tracing + prompt lab | Chrome DevTools Network tab + replay | "What prompt caused THAT output?" |
| **LangGraph API** | Local graph state debugger | REST debugger with state access | "What's the graph state at this node?" |
| **Logfire** | Pydantic validation tracer | pytest for data validation, but traces | "What did Pydantic do with the LLM output?" |
| **erdantic** | Pydantic model ER diagrams | UML class diagrams, auto-generated | "How do our 60+ models relate?" |
| **JSON Crack** | Interactive JSON tree viewer | JSON visualizer with graph layout | "Let me explore this nested JSON" |

### When to Use Each

| Scenario | Tool |
|----------|------|
| Track costs across providers (Ollama vs Anthropic vs OpenRouter) | **Langfuse** |
| See which LLM calls are slow or expensive | **Langfuse** |
| Score extraction quality and build regression datasets | **Langfuse** |
| Compare runs over days/weeks | **Langfuse** |
| Production monitoring | **Langfuse** (self-hosted only) |
| Edit and test a prompt without re-running the pipeline | **LangSmith** (Playground) |
| Auto-trace all graphs with zero code changes | **LangSmith** |
| Compare prompt outputs across different models | **LangSmith** |
| Build evaluation datasets from traces | **LangSmith** |
| Inspect full graph state for a specific thread | **LangGraph API** |
| Modify thread state and re-invoke a graph | **LangGraph API** |
| Debug provider fallback chain via state manipulation | **LangGraph API** |
| See where Pydantic validation failed or coerced data | **Logfire** |
| Trace `model_validate()` calls with field-level detail | **Logfire** |
| Find parse errors between LLM output and Pydantic model | **Logfire** |
| Visualize relationships between Pydantic models | **erdantic** |
| Generate living documentation of data schemas | **erdantic** |
| Interactively explore nested JSON (graph state, extraction records) | **JSON Crack** |
| Debug LangGraph thread state as an interactive tree | **JSON Crack** |

---

## Configuration

### Environment Variables

Add to `.env` (see `.env.example` for full reference):

```bash
# --- LangSmith (dev only — cloud, auto-traces all graphs) ---
LANGCHAIN_TRACING_V2=true              # Set false to disable
LANGCHAIN_API_KEY=lsv2_pt_xxx          # From smith.langchain.com > Settings > API Keys
LANGSMITH_PROJECT=acm-ai-dev           # Auto-creates if doesn't exist

# --- Langfuse (production — self-hosted or cloud) ---
LANGFUSE_ENABLED=true                  # Set false to disable
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_BASE_URL=http://localhost:3000
# For cloud: LANGFUSE_BASE_URL=https://cloud.langfuse.com

# --- Logfire (Pydantic validation traces → Langfuse via OTel) ---
LOGFIRE_ENABLED=false                  # Set true to enable
# When true, Logfire SDK instruments Pydantic v2 validation and sends spans
# to Langfuse. Requires LANGFUSE_ENABLED=true and Langfuse keys.
# No Logfire cloud account needed — traces go to your self-hosted Langfuse.
```

### Key Notes

- `LANGCHAIN_API_KEY` is the same key as `LANGSMITH_API_KEY` — LangSmith console generates one key that works for both variables
- `LANGSMITH_PROJECT` auto-creates in the cloud if it doesn't exist
- LangSmith should be **disabled in production** (`LANGCHAIN_TRACING_V2=false`) — data goes to cloud servers, which conflicts with government data requirements
- Langfuse can run as self-hosted Docker stack or cloud — self-hosted is required for production
- Logfire is opt-in (`LOGFIRE_ENABLED=false` by default) and reuses existing `LANGFUSE_*` credentials — no new accounts needed
- Logfire uses `send_to_logfire=False` — no data goes to Logfire cloud, only to your Langfuse via OTel

### Docker Services

```bash
# Start the full observability stack (Langfuse v3 + JSON Crack)
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Start only JSON Crack
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d jsoncrack

# Start only Langfuse
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d \
  langfuse-postgres langfuse-clickhouse langfuse-redis langfuse-minio \
  langfuse-minio-init langfuse-worker langfuse-web
```

Port map:

| Service | Port | Purpose |
|---------|------|---------|
| Langfuse Web UI | 3000 | Trace dashboard |
| Langfuse Worker | 3030 (localhost) | Background processing |
| PostgreSQL | 5433 (localhost) | Langfuse user data |
| ClickHouse | 8123 (localhost) | Langfuse trace storage |
| Redis | 6379 (localhost) | Langfuse queue/cache |
| MinIO API | 9090 | S3-compatible storage |
| MinIO Console | 9091 (localhost) | MinIO admin UI |
| JSON Crack | 8888 | Interactive JSON viewer |

### LangGraph API

```bash
uv run langgraph dev --no-browser      # Start local API server
# API: http://127.0.0.1:2024
# Swagger UI: http://127.0.0.1:2024/docs
```

Always use `uv run langgraph dev`, NOT bare `langgraph dev` — the latter uses global Python which lacks project dependencies.

---

## Langfuse (Production Tracing)

### How It Works

Langfuse captures traces via explicit `CallbackHandler` injection into LangChain/LangGraph invocations. The integration is in `open_notebook/observability/langfuse_config.py`.

### Code Architecture

| File | Purpose |
|------|---------|
| `open_notebook/observability/langfuse_config.py` | Core functions: handler creation, metadata, context manager |
| `open_notebook/observability/langfuse_bridge.py` | Custom event bridge: PipelineLogger stages to Langfuse spans |
| `open_notebook/observability/__init__.py` | Public API re-exports |
| `scripts/observability/setup_langfuse_datasets.py` | Evaluation dataset creation |

### Two Wiring Patterns

**Pattern 1: Context Manager (preferred for routers)**

Used in `api/routers/chat.py`, `api/routers/sources.py`, `api/routers/search.py`, `api/routers/transformations.py`, `api/routers/source_chat.py`, `api/routers/notes.py`:

```python
from open_notebook.observability.langfuse_config import (
    langfuse_tracing,
    merge_langfuse_into_config,
)

# In your endpoint:
with langfuse_tracing("chat", source_id="chat", operation_type="chat") as (callbacks, metadata):
    config = merge_langfuse_into_config(base_config, callbacks, metadata)
    result = await graph.ainvoke(input, config=config)
```

The context manager handles handler creation and auto-flushing.

**Pattern 2: Manual (used in extraction pipeline)**

Used in `open_notebook/graphs/acm_extraction.py` (line ~3596) and `commands/source_commands.py` (line ~612):

```python
from open_notebook.observability.langfuse_config import (
    append_langfuse_callback,
    build_langfuse_metadata,
    flush_langfuse_handler,
    get_langfuse_handler,
)

langfuse_handler = get_langfuse_handler()
callbacks = append_langfuse_callback([], langfuse_handler)
metadata = build_langfuse_metadata(
    source_id=source_id_str,
    extraction_model=model_id,
    command_id=command_id,
)

# Pass to graph:
config = {"callbacks": callbacks, "metadata": metadata}
result = await graph.ainvoke(input, config=config)

# Cleanup:
flush_langfuse_handler(langfuse_handler)
```

Use this pattern when you need custom metadata per-run (source_id, model_id, command_id).

### Non-Fatal Guarantee

All Langfuse code is wrapped in try/except. If Langfuse is down, disabled, or misconfigured, the application continues normally. This is a hard requirement — **tracing must never break extraction**.

### What Langfuse Captures

Each graph invocation creates a **trace** with nested **spans**:

```
Trace: "extraction-source:abc123"
 ├── extract_metadata (span)
 ├── structure_analysis (span)
 ├── building_inventory (span)
 ├── tag_pages (span)
 ├── save_intelligence (span)
 ├── extract_building (span)
 │    └── ChatOllama/ChatAnthropic  (LLM span: input/output/tokens/latency)
 ├── extract_items (span)
 │    └── ChatOllama/ChatAnthropic  (LLM span)
 ├── orchestrate (span)
 ├── validate (span)
 ├── correct (span)              <-- may repeat in a loop
 ├── validate (span)             <-- loop iteration 2
 ├── deduplicate (span)
 ├── recover_no_access (span)
 └── save (span)
```

When **Logfire is enabled**, additional Pydantic validation spans appear nested under each node:

```
 ├── extract_items (span)
 │    ├── ChatOllama (LLM span)
 │    ├── ACMExtractionRecord validate_python (Logfire OTel span)
 │    ├── ACMExtractionRecord validate_python (Logfire OTel span)
 │    └── BuildingRoomContext validate_python (Logfire OTel span)
```

The pipeline bridge (`langfuse_bridge.py`) also emits custom `acm.pipeline.stage` events that appear as nested spans, correlating PipelineLogger stages (STRUCTURE, PREFLIGHT, EXTRACT, etc.) with LangChain-level spans.

### Reading Traces in the Langfuse UI

**Find slow nodes:** Open a trace, view the waterfall. Each span shows duration. If `extract_items` takes 45s but `validate` takes 2s, the extraction LLM call is your bottleneck.

**Find the correction loop cost:** Look for repeated `validate` -> `correct` -> `validate` spans. Count iterations. Click each `correct` span to see the prompt and response.

**Track costs by provider:** Dashboard > Cost view > filter by `extraction_model` tag. Compare Ollama ($0.00) vs Anthropic vs OpenRouter for the same document.

**Score extraction quality:** Open a trace > click "Score" > add a manual score (0-1). Over time, build a dataset of "good" vs "bad" extractions. Filter by score to find patterns.

**Find Pydantic parse failures (Logfire spans):** Filter spans by `logfire.pydantic` — see which model, which field, and whether validation succeeded or failed. Cross-reference with the LLM output in the parent span.

### Langfuse Filters

```
Tags: acm-extraction                          # Only extraction traces
Session ID: extraction-source:<id>            # Specific source
Metadata > extraction_model: ollama/llama3.1  # Specific model
Search: "correction failed"                   # Find failures
```

---

## LangSmith (Dev Auto-Tracing + Prompt Lab)

### How It Works

Set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` — LangChain's runtime automatically traces every `ChatModel.invoke()`, `chain.invoke()`, and `graph.invoke()` call. Zero code changes needed.

### What It Traces

All LangGraph graphs are auto-traced:
- `acm_extraction` (13 nodes)
- `supervisor_agent` (ReAct loop)
- `chat`, `source_chat`, `transformation`
- `doc_search_agent`, `crud_agent`, `acm_analyst_agent`
- `source`, `prompt`, `ask`

Each trace shows:
- **Node execution order** and conditional edge decisions
- **Full LLM input/output** for every call
- **Token counts and latency** per call
- **Model name** used

### The Prompt Playground

This is LangSmith's most valuable feature for extraction pipeline work:

1. Go to **smith.langchain.com** > your project
2. Find a trace where extraction produced bad output
3. Click the specific LLM call (e.g., `extract_items`)
4. Click **"Open in Playground"**
5. The **exact rendered prompt** loads with the actual PDF content
6. **Edit the prompt** (e.g., clarify field definitions)
7. Hit **Run** — see the new output immediately, same input
8. Iterate multiple variations in seconds
9. Copy the working prompt back to your Jinja2 template in `prompts/`

**This replaces the old workflow** of: edit template > restart API > re-upload PDF > wait for extraction > check results (15+ minutes per iteration). With the Playground, prompt iteration takes seconds.

### Limitations

- **Cloud-only** — all data goes to LangSmith servers
- **Free tier: 5,000 traces/month** (~380 full extraction runs at 13 nodes each)
- **Not for production** — data privacy concern for government data
- **Cannot inspect LangGraph state** — only sees LLM inputs/outputs, not the full state object between nodes

---

## LangGraph API (Graph State Debugger)

### How It Works

The LangGraph dev server reads `langgraph.json` to discover registered graphs, compiles them, and provides a REST API for state inspection and graph invocation.

> **Note:** LangGraph Studio's visual UI now requires a LangSmith cloud session (no standalone desktop app). This conflicts with our data-privacy requirement for Victorian Government data. We use the local REST API + Swagger UI instead, supplemented by Langfuse trace trees for visualization.

### Starting the API

```bash
uv run langgraph dev --no-browser
# API: http://127.0.0.1:2024
# Swagger UI: http://127.0.0.1:2024/docs
```

### Key Endpoints

```bash
# List registered graphs
curl http://127.0.0.1:2024/assistants

# Create a thread
curl -X POST http://127.0.0.1:2024/threads

# Get thread state (inspect graph state at current node)
curl http://127.0.0.1:2024/threads/{thread_id}/state

# Update thread state (modify values, simulate conditions)
curl -X POST http://127.0.0.1:2024/threads/{thread_id}/state \
  -H "Content-Type: application/json" \
  -d '{"values": {"model_family": "qwen", "is_qwen": true}}'

# Invoke a graph
curl -X POST http://127.0.0.1:2024/runs \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "...", "assistant_id": "acm_extraction", "input": {...}}'
```

### Dump State to JSON Crack

For interactive exploration of large state objects:

```bash
# Fetch thread state and save as JSON
uv run python scripts/dump_state_json.py <thread_id>
# Opens state_dump.json — paste into http://localhost:8888
```

### What You Can Do

**State inspection:**
- After `extract_items`: see all extracted records, check field values
- After `validate`: see which records failed and why (validation_failures)
- After `correct`: see if corrections actually improved things

**State modification:**
- Manually fix a record's `room_name` > re-invoke from `validate` > see if downstream works
- Set `correction_attempts = max` to force exit from the correction loop
- Simulate "Ollama unavailable" to test provider fallback chain

### What We Lose vs Studio Visual UI (and Mitigations)

| Studio Feature | Available? | Mitigation |
|----------------|------------|------------|
| Visual DAG topology | No | Langfuse trace tree shows node execution order |
| Pause + step through nodes | No | Strategic logging + Langfuse trace inspection |
| Inspect full state at node | Partial | `GET /threads/{id}/state` (current state only) |
| Modify state mid-run | Partial | `POST /threads/{id}/state` (between runs) |
| Re-run from specific node | No | Re-invoke full graph with modified input |
| Human-in-the-loop injection | No | Not needed for current issue backlog |

### Configuration

File: `langgraph.json` (project root):

```json
{
  "dependencies": ["."],
  "graphs": {
    "acm_extraction": "./open_notebook/graphs/studio_entry.py:graph",
    "supervisor": "./open_notebook/graphs/studio_entry_supervisor.py:graph"
  },
  "env": ".env"
}
```

---

## Logfire (Pydantic Validation Tracing)

### How It Works

Logfire auto-instruments Pydantic v2 validation. Every `ACMExtractionRecord.model_validate()`, `BuildingRoomContext()` construction, and failed parse shows up as a span. These spans are sent to Langfuse via OpenTelemetry — no Logfire cloud account needed.

This fills the gap between "what the LLM returned" (Langfuse already captures via LangChain callbacks) and "what Pydantic did with it" (previously invisible).

### Architecture

```
Logfire SDK (logfire.instrument_pydantic())
    │
    ▼
Pydantic v2 model_validate() / __init__()
    │
    ▼ (OTel spans via OTLP/HTTP — gRPC is NOT supported by Langfuse)
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = http://localhost:3000/api/public/otel
OTEL_EXPORTER_OTLP_TRACES_HEADERS  = Authorization=Basic base64(pk:sk)
    │  (SDK auto-appends /v1/traces to the base endpoint)
    ▼
Langfuse (:3000) — spans appear alongside LangChain traces
```

### Configuration

| File | Purpose |
|------|---------|
| `open_notebook/observability/logfire_config.py` | OTel bridge: `init_logfire()` |
| `api/main.py` | Calls `init_logfire()` at startup (before graph imports) |
| `run_worker.py` | Calls `init_logfire()` at startup (before command imports) |

### Key Design Decisions

- **`send_to_logfire=False`** — no Logfire cloud account needed, all data routes to Langfuse
- **Reuses `LANGFUSE_*` env vars** — no new credentials required
- **`LOGFIRE_ENABLED=false`** by default — opt-in, non-fatal
- **Initialized before graph imports** — ensures Pydantic instrumentation is active when models are loaded
- **Both API and Worker** have `init_logfire()` — covers REST endpoints AND background extraction commands

### What It Captures

When `LOGFIRE_ENABLED=true`, you'll see spans like:

```
ACMExtractionRecord validate_python    duration: 0.3ms   success
BuildingRoomContext validate_python     duration: 0.1ms   success
ACMItemRecord validate_python           duration: 0.2ms   FAILURE: field 'result' invalid
```

These appear in Langfuse alongside the LangChain callback spans, giving you a complete picture:
1. What the LLM returned (LangChain span)
2. How Pydantic parsed/validated it (Logfire OTel span)
3. Which fields failed and why (Logfire span attributes)

### Per-Model Configuration

You can control recording granularity per-model using Pydantic's `plugin_settings`:

```python
from pydantic import BaseModel

class ACMExtractionRecord(BaseModel, plugin_settings={'logfire': {'record': 'all'}}):
    """Record all validations — useful for debugging extraction quality."""
    ...

class InternalHelper(BaseModel, plugin_settings={'logfire': {'record': 'failure'}}):
    """Only record failures — reduce noise for internal helpers."""
    ...
```

Options: `'all'` (default), `'failure'`, `'metrics'`, `'off'`.

### Verification

```bash
# Quick test (with Langfuse keys in .env):
LOGFIRE_ENABLED=true uv run python -c "
from dotenv import load_dotenv; load_dotenv()
import os; os.environ['LOGFIRE_ENABLED'] = 'true'
from open_notebook.observability.logfire_config import init_logfire
print('init:', init_logfire())
from pydantic import BaseModel
class Test(BaseModel):
    name: str
m = Test(name='hello')
print('OK:', m.name)
"
# Look for: "Pydantic Test validate_python" in console output
# Check Langfuse dashboard for OTel spans
```

---

## erdantic (Model Relationship Diagrams)

### How It Works

erdantic generates SVG entity-relationship diagrams from Pydantic models. It traverses model fields, finds references to other models, and renders the relationships as an ER diagram using Graphviz.

### Prerequisites

```bash
# One-time system install (Graphviz C library)
winget install graphviz        # Windows
brew install graphviz           # macOS
apt install graphviz            # Linux

# One-time Python install (not in pyproject.toml — pygraphviz needs Graphviz headers)
pip install erdantic
```

> **Why not in pyproject.toml?** erdantic depends on pygraphviz, which requires Graphviz C headers to compile. This fails `uv sync` on Windows without a complex setup. It's documented as a manual install instead.

### Usage

```bash
uv run python scripts/generate_model_diagrams.py
# Outputs to docs/diagrams/:
#   extraction_schemas.svg  — ACMExtractionResult + related models
#   v3_schemas.svg          — ACMItemExtractionResult + related
#   domain_acm.svg          — ACMRecord domain model
#   domain_building.svg     — BuildingRecord domain model
#   provider_models.svg     — NormalizedExtractionResult
#   api_acm.svg             — ACMRecordResponse API model
#   api_source.svg          — SourceResponse API model
```

### Limitation

erdantic does NOT support TypedDict (used by LangGraph states like `ExtractionState`). For graph state topology, use the LangGraph API instead:

```bash
curl http://127.0.0.1:2024/assistants | jq
```

### Script Location

`scripts/generate_model_diagrams.py` — handles ImportError gracefully, skips missing models, reports Graphviz installation requirements.

---

## JSON Crack (Interactive JSON Viewer)

### How It Works

JSON Crack renders JSON as an interactive tree/graph. When debugging extraction issues, it provides a far better experience than scrolling through raw JSON in a terminal or Langfuse dashboard.

### Starting

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d jsoncrack
# Open http://localhost:8888
```

### Usage Patterns

**1. Explore LangGraph thread state:**

```bash
# Fetch state from LangGraph API
uv run python scripts/dump_state_json.py <thread_id>
# Open http://localhost:8888 → Import → Upload File → state_dump.json
```

**2. Explore extraction records:**

```python
# In any debugging context:
record = ACMExtractionRecord(...)
print(record.model_dump_json(indent=2))
# Copy-paste into http://localhost:8888
```

**3. Explore API responses:**

```bash
# Fetch and visualize API response
curl -s http://localhost:5055/api/acm/buildings?source_id=source:abc | python -m json.tool > buildings.json
# Upload buildings.json to http://localhost:8888
```

### When to Use

- Debugging nested JSON structures (extraction records with 20+ fields)
- Exploring graph state objects (TypedDicts with nested lists of records)
- Comparing before/after extraction results
- Onboarding: understanding the shape of data flowing through the pipeline

---

## Head-to-Head Comparison

### Capability Matrix

| Capability | LangGraph API | LangSmith | Langfuse | Logfire | erdantic | JSON Crack |
|------------|---------------|-----------|----------|---------|----------|------------|
| Inspect graph state | **YES** (REST) | NO | NO | NO | NO | YES (via dump) |
| Modify state | **YES** (REST) | NO | NO | NO | NO | NO |
| Auto-trace ALL graphs | NO | **YES** (env var) | NO (wire each) | N/A | N/A | N/A |
| Prompt playground | NO | **YES** | NO | NO | NO | NO |
| Historical traces | NO (ephemeral) | **YES** | **YES** | Via Langfuse | NO | NO |
| Cost/token tracking | NO | YES | **YES** | NO | NO | NO |
| Pydantic validation | NO | NO | NO | **YES** | NO | NO |
| Model relationships | NO | NO | NO | NO | **YES** | NO |
| Interactive JSON | NO | NO | NO | NO | NO | **YES** |
| Self-hostable | **YES** | **NO** | **YES** | **YES** (via Langfuse) | **YES** | **YES** |
| Data privacy | **BEST** | **WORST** | **GOOD** | **GOOD** | **BEST** | **BEST** |

### Development vs Production

| Scenario | Recommended Tool(s) |
|----------|---------------------|
| Prompt iteration | **LangSmith** (playground) |
| Debug pipeline flow | **Langfuse** (trace tree) + **LangGraph API** (state) |
| Coverage (all graphs) | **LangSmith** (auto-trace) |
| Pydantic parse debugging | **Logfire** (validation spans in Langfuse) |
| Schema documentation | **erdantic** (SVG diagrams) |
| Data exploration | **JSON Crack** (interactive viewer) |
| Production monitoring | **Langfuse** (self-hosted only) |
| Production cost control | **Langfuse** (per-provider breakdown) |
| Production data privacy | **Langfuse** (self-hosted, data stays local) |

---

## Practical Workflows

### Workflow: Debug a Bad Extraction

**Scenario:** Building 3 came back with `material_type: "unknown"` instead of `"vinyl floor tiles"`.

```
1. Langfuse: Find the extraction trace by source_id
2. Click extract_items span > see the LLM output > confirm wrong value
3. If Logfire enabled: check Pydantic validation span — did coercion happen?
4. LangSmith: Find same trace > click extract_items LLM call > "Open in Playground"
5. Edit the prompt > Run > compare output > iterate
6. Copy working prompt back to Jinja2 template in prompts/
7. Langfuse: Run 5 extractions > score each > verify improvement trend
```

### Workflow: Debug the Correction Loop

**Scenario:** `validate > correct > validate` loops 4 times before succeeding.

```
1. Langfuse: Open trace tree > count validate/correct span pairs (loop iterations)
2. Click each correct span > see prompt + LLM response > identify pattern
3. LangGraph API: GET /threads/{id}/state > inspect validation_failures
4. LangSmith: Open correct iteration 2 in Playground
5. Edit correction prompt > test if stronger instructions fix in 1 pass
6. Langfuse: Compare correction loop counts before/after prompt change
```

### Workflow: Debug Pydantic Parse Failures

**Scenario:** LLM returns valid-looking JSON but records are missing fields.

```
1. Langfuse: Find extraction trace > look for Logfire OTel spans
2. Filter by "validate_python" > find FAILURE spans
3. Click failure span > see which field failed and the error message
4. Cross-reference with parent LLM span > see what the LLM actually returned
5. JSON Crack: copy LLM output JSON > paste into localhost:8888 > explore structure
6. Identify: wrong field name? wrong type? missing required field?
7. Fix prompt or schema accordingly
```

### Workflow: Optimize Provider Selection

**Scenario:** Need to verify Ollama > Anthropic > OpenRouter fallback chain works.

```
1. LangGraph API: invoke extraction with specific provider config
2. GET /threads/{id}/state > see which model was provisioned
3. POST /threads/{id}/state > simulate "Ollama unavailable" > re-invoke
4. Confirm Anthropic Direct is reached
5. Langfuse: Compare cost and quality across providers in dashboard
```

### Workflow: Iterate on Extraction Prompts

**Scenario:** `room_name` field gets material descriptions instead of room names.

```
1. Langfuse: Find Alexander PDF extraction trace
2. Click extract_items span > confirm room_name has materials
3. LangSmith: Find same trace > click extract_items call > "Open in Playground"
4. Edit prompt:
   room_name: The PHYSICAL room or area (e.g., "Shower Room", "Corridor")
   DO NOT put material descriptions here.
5. Hit Run > check output > iterate 3-4 variations
6. Copy working prompt to prompts/ Jinja2 template
7. Langfuse: Run on 5 different PDFs > score each > verify generalization
```

### Workflow: Understand Schema Relationships

**Scenario:** New developer needs to understand how extraction models relate.

```
1. Run: uv run python scripts/generate_model_diagrams.py
2. Open docs/diagrams/extraction_schemas.svg in browser
3. See: ACMExtractionResult → ACMExtractionRecord → BuildingRoomContext
4. Open docs/diagrams/domain_acm.svg
5. See: ACMRecord fields and relationships to BuildingRecord
6. Compare extraction schemas vs domain models — understand the mapping
```

---

## Issue Debugging Matrix

Mapping of known GitHub issues to the observability tools that help debug them:

| Issue | Description | Primary Tool | Debuggable NOW? | CLI/API Workflow |
|-------|-------------|-------------|-----------------|------------------|
| **#100** | room_name field misalignment | **LangSmith** | YES | Trace → Playground → edit field description → re-run |
| **#84** | SF picklist corruption | **All tools** | YES | Langfuse trace tree + LangSmith correction prompt + LangGraph API loop state |
| **#93** | Ollama hardening | **LangSmith** | YES | Playground: test `num_ctx` + `format=json` across models |
| **#101** | OpenRouter 402 fallback | **Langfuse** | YES | Query traces with `provider=openrouter` → analyze 402 frequency |
| **#97** | correction format=json | **LangSmith** + **Logfire** | YES | Trace correction call + Logfire shows Pydantic parse failure |
| **#99** | progress stuck running | **Langfuse** + **LangGraph API** | PARTIAL | Filter traces missing STORE stage_exit + inspect thread state |
| **#94** | Anthropic Direct gap | **Langfuse** | PARTIAL | Metadata tags show which provider was actually used |
| **#96** | backfill 500 | N/A | NO | Simple `source.name` → `source.title` fix |
| **#92** | model defaults | N/A | NO | DB persistence issue |
| **#91** | asyncio.run() error | N/A | NO | Async runtime fix |
| **#90** | SSE polling fallback | N/A | NO | Frontend hook fix |
| **#89** | empty buildings | N/A | NO | Data migration |
| **#98** | test log contamination | N/A | NO | pytest config fix |

---

## Wiring Langfuse Into New Graphs

When adding new graphs or invocation points, follow this pattern.

### For API Routers (Preferred)

Use the context manager pattern:

```python
from open_notebook.observability.langfuse_config import (
    langfuse_tracing,
    merge_langfuse_into_config,
)

@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    base_config = {"configurable": {"thread_id": request.session_id}}

    with langfuse_tracing(
        "my_graph",
        source_id=str(request.source_id),
        operation_type="my_operation",
    ) as (callbacks, metadata):
        config = merge_langfuse_into_config(base_config, callbacks, metadata)
        result = await my_graph.ainvoke(input, config=config)

    return result
```

### For Background Commands

Use the manual pattern when you need per-run metadata:

```python
from open_notebook.observability.langfuse_config import (
    append_langfuse_callback,
    build_langfuse_metadata,
    flush_langfuse_handler,
    get_langfuse_handler,
)

async def my_command(source_id: str, command_id: str):
    handler = get_langfuse_handler()
    callbacks = append_langfuse_callback([], handler)
    metadata = build_langfuse_metadata(
        source_id=source_id,
        extraction_model=model_id,
        command_id=command_id,
    )

    try:
        config = {"callbacks": callbacks, "metadata": metadata}
        result = await graph.ainvoke(input, config=config)
    finally:
        flush_langfuse_handler(handler)
```

### Rules

- **Callbacks go at the invocation site** (in routers or commands), NOT inside graph node functions
- **Never modify** `acm_extraction.py` or `source_commands.py` Langfuse wiring — it's pre-existing and working
- **Always non-fatal** — use the provided functions which handle errors internally
- **Do not add `langfuse` imports** to files that don't invoke graphs

---

## Registering Graphs in LangGraph API

### Current Registration

File: `langgraph.json`

```json
{
  "dependencies": ["."],
  "graphs": {
    "acm_extraction": "./open_notebook/graphs/studio_entry.py:graph",
    "supervisor": "./open_notebook/graphs/studio_entry_supervisor.py:graph"
  },
  "env": ".env"
}
```

### Adding a New Graph

1. If the graph compiles without a checkpointer, register directly:
   ```json
   "my_graph": "./open_notebook/graphs/my_graph.py:graph"
   ```

2. If the graph uses `checkpointer=memory` at compile time, create a studio entry wrapper:
   ```python
   # open_notebook/graphs/studio_entry_my_graph.py
   from dotenv import load_dotenv
   load_dotenv(override=False)
   from open_notebook.graphs.my_graph import build_graph
   graph = build_graph()  # Compile without checkpointer for API
   ```

---

## Troubleshooting

### Langfuse traces not appearing

1. Check `LANGFUSE_ENABLED=true` in `.env`
2. Check `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set
3. Check API logs for: `"LANGFUSE_ENABLED=true but ... missing"`
4. Verify `LANGFUSE_BASE_URL` points to correct host
5. Run a chat or extraction and check the Langfuse dashboard
6. For self-hosted: verify Docker containers are healthy: `docker compose -f docker-compose.yml -f docker-compose.observability.yml ps`

### LangSmith traces not appearing

1. Check `LANGCHAIN_TRACING_V2=true` in `.env`
2. Check `LANGCHAIN_API_KEY` is set (same key as `LANGSMITH_API_KEY`)
3. Verify internet connectivity (LangSmith is cloud-only)
4. Check that `LANGSMITH_PROJECT` matches your project name at smith.langchain.com (auto-creates if new)

### Logfire / Pydantic spans not appearing in Langfuse

1. Check `LOGFIRE_ENABLED=true` in `.env`
2. Check that `LANGFUSE_ENABLED=true` AND Langfuse keys are set (Logfire needs them)
3. Check API startup logs for: `"Logfire initialized -- Pydantic traces -> Langfuse OTel at ..."`
4. If you see `"logfire package not installed"`: run `uv sync --group dev`
5. Langfuse OTel requires v3.x (self-hosted) — verify version at `http://localhost:3000/api/public/health`
6. Logfire only instruments models loaded AFTER `init_logfire()` — check import order in `api/main.py`
7. Only OTLP/HTTP protocol is supported (not gRPC). Logfire uses HTTP by default with `send_to_logfire=False`, so this works out of the box. Do NOT configure a gRPC exporter pointing at Langfuse.

### LangGraph API won't start

1. Use `uv run langgraph dev`, NOT bare `langgraph dev`
2. Check `langgraph.json` syntax and paths
3. Verify the graph module imports cleanly: `uv run python -c "from open_notebook.graphs.studio_entry import graph"`

### JSON Crack not loading

1. Check container is running: `docker ps | grep jsoncrack`
2. Open `http://localhost:8888` — should show the JSON Crack UI
3. If port conflict: change the host port in `docker-compose.observability.yml`

### erdantic fails to install

1. Install Graphviz system library first: `winget install graphviz` (Windows)
2. Install pygraphviz with explicit include/lib paths (Windows):
   ```powershell
   uv pip install pygraphviz --config-settings="--global-option=build_ext" --config-settings="--global-option=-IC:\Program Files\Graphviz\include" --config-settings="--global-option=-LC:\Program Files\Graphviz\lib"
   ```
3. Then: `uv pip install erdantic`
4. **DLL load failure at runtime:** Add Graphviz `bin/` to PATH before running:
   ```bash
   # Bash / Git Bash
   PATH="$PATH:/c/Program Files/Graphviz/bin" uv run python scripts/generate_model_diagrams.py
   # PowerShell
   $env:PATH += ";C:\Program Files\Graphviz\bin"; uv run python scripts/generate_model_diagrams.py
   ```
5. To make permanent, add `C:\Program Files\Graphviz\bin` to your system PATH via Windows Environment Variables

### Both Langfuse and LangSmith enabled — conflicts?

No conflicts. They trace independently:
- LangSmith hooks into the LangChain runtime globally (env var)
- Langfuse hooks in via explicit callbacks per invocation
- Logfire hooks in via OTel to Langfuse (separate protocol)
- All three send trace data in parallel without interference
- Negligible overhead (async HTTP posts)

---

## Reference Links

### Internal Files

| File | Purpose |
|------|---------|
| `open_notebook/observability/langfuse_config.py` | Core Langfuse integration (handler, metadata, context manager) |
| `open_notebook/observability/logfire_config.py` | Logfire → Langfuse OTel bridge (`init_logfire()`) |
| `open_notebook/observability/langfuse_bridge.py` | PipelineLogger stage events to Langfuse spans |
| `open_notebook/observability/__init__.py` | Public API re-exports |
| `scripts/observability/setup_langfuse_datasets.py` | Evaluation dataset creation script |
| `scripts/generate_model_diagrams.py` | erdantic ER diagram generator |
| `scripts/dump_state_json.py` | LangGraph thread state → JSON Crack helper |
| `langgraph.json` | LangGraph API graph registration |
| `open_notebook/graphs/studio_entry.py` | API entry for acm_extraction graph |
| `open_notebook/graphs/studio_entry_supervisor.py` | API entry for supervisor graph |
| `docker-compose.observability.yml` | Langfuse v3 stack + JSON Crack |
| `.env.example` (Observability section) | Environment variable reference |

### Routers with Langfuse Wired

| Router | Graph | Pattern |
|--------|-------|---------|
| `api/routers/chat.py` | `chat` | `langfuse_tracing()` context manager |
| `api/routers/source_chat.py` | `source_chat` | `langfuse_tracing()` context manager |
| `api/routers/sources.py` | `source` | `langfuse_tracing()` context manager |
| `api/routers/transformations.py` | `transformation` | `langfuse_tracing()` context manager |
| `api/routers/search.py` | `doc_search` | `langfuse_tracing()` context manager |
| `api/routers/notes.py` | `notes` | `langfuse_tracing()` context manager |
| `open_notebook/graphs/acm_extraction.py` | `acm_extraction` | Manual (handler + metadata + flush) |
| `commands/source_commands.py` | `acm_extraction` (pre-graph Docling step) | Manual |

### Logfire Integration Points

| File | Purpose |
|------|---------|
| `api/main.py` | `init_logfire()` at startup (API process) |
| `run_worker.py` | `init_logfire()` at startup (Worker process) |

### Sprint Artifacts

| File | Content |
|------|---------|
| `docs/sprint-artifacts/observability/findings.md` | Full tool comparison, issue-to-tool mapping, Phase 3 assessment |
| `docs/sprint-artifacts/observability/task_plan.md` | 5-phase rollout plan |
| `docs/sprint-artifacts/observability/progress.md` | Session recovery journal (4 sessions) |
| `docs/sprint-artifacts/observability/setup-prompt.md` | Setup session prompt for AI agents |

### External Documentation

| Resource | URL |
|----------|-----|
| Langfuse docs | https://langfuse.com/docs |
| Langfuse LangChain integration | https://langfuse.com/docs/integrations/langchain |
| Langfuse self-hosted setup | https://langfuse.com/docs/deployment/self-host |
| Langfuse OTel integration | https://langfuse.com/docs/integrations/native/opentelemetry |
| LangSmith docs | https://docs.smith.langchain.com |
| LangSmith Playground | https://docs.smith.langchain.com/how_to_guides/playground |
| LangGraph CLI | https://langchain-ai.github.io/langgraph/cloud/reference/cli |
| Logfire docs | https://logfire.pydantic.dev/docs |
| Logfire Pydantic integration | https://logfire.pydantic.dev/docs/integrations/pydantic |
| Logfire alternative backends | https://logfire.pydantic.dev/docs/how-to-guides/alternative-backends |
| erdantic docs | https://erdantic.roaminsight.com |
| JSON Crack | https://jsoncrack.com |
