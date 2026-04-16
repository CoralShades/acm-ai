# ACM-AI Extraction Pipeline Audit — RTX 5090 Production Readiness

## Context

The extraction pipeline on RunPod RTX 5090 completes fast (45s for 34-page PDF) but produces **only 10/31 records** for Broadmeadows Police Station (expected 31 from ground truth). The full pipeline locally previously took 37min-1hr (pre-OCR fix). We need an end-to-end audit to find where records are lost, remove unnecessary components, and achieve production-quality accuracy.

**Recent fixes already applied (commit 5aefa9a3 on deploy/runpod-5090):**
- `do_ocr=False` on all Docling PdfPipelineOptions (OCR hung on native PDFs)
- `document_engine="simple"` in source.py (content_core Docling path has no PdfPipelineOptions)
- `AcceleratorDevice.AUTO` for GPU table extraction
- `.venv/bin/python` everywhere on RunPod (uv run overwrites cu128 torch)

**LangSmith trace IDs for the 10-record Broadmeadows run (local):**
- `d890fadf-1816-4ca5-9b6a-2a593c7409d9`
- `2c0961fd-6d28-4e6d-8152-77351182e8c2`

**Test documents:**
- Broadmeadows Police Station (31 ground truth records, 18 pages)
- Alexander District Hospital (43 ground truth records, 34 pages)

**Sprint status:** `docs/sprint-artifacts/sprint-status.yaml` section `pipeline-audit-2026-04-16`

---

## Execution Plan

### Phase 0: Skills & Documentation Loading

Before ANY work, invoke these skills to load current documentation and patterns:

```
/acm-observability          — Langfuse/LangSmith query patterns, wiring patterns
/langgraph-fundamentals     — Graph structure, state management, node patterns
/langgraph-persistence      — Checkpointing, state serialization
/langgraph-human-in-the-loop — Interrupt/approval flows
/langchain-fundamentals     — Chain composition, callbacks, tracing
/langchain-rag              — RAG patterns (for extraction prompt context)
/langchain-middleware        — Middleware, interceptors, retry logic
/langchain-dependencies     — Package compatibility, version constraints
/framework-selection         — Provider routing, model selection
/e2e-test                    — End-to-end test patterns
```

Use **context7** MCP server for ALL library documentation lookups (Docling, LangGraph, LangChain, Pydantic, SurrealDB). Do not rely on training data for API details.

---

### Phase 1: Observability Stack Setup (PA-1)

**Goal:** Get Langfuse + LangSmith running locally so we can trace everything.

1. Start Docker Desktop on Windows
2. `docker compose up -d` — check which compose file has Langfuse (search repo for `docker-compose*.yml`)
3. Verify Langfuse health: `curl http://localhost:3000/api/public/health`
4. Verify `.env` has correct `LANGFUSE_ENABLED=true`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
5. Verify `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` are set for LangSmith
6. Start all local services: `start-all.bat` (from PowerShell on Windows)

**Use skill:** `/acm-observability` for Langfuse query patterns and wiring verification.

---

### Phase 2: Trace Investigation — Where Are Records Lost? (PA-2)

**Goal:** Analyze the LangSmith traces to find where 31 records become 10.

**Agent team dispatch:** Spawn a **TeamCreate** team named `pipeline-audit` with these members:

| Agent | Role | First Task |
|-------|------|-----------|
| `acm-observability-debugger` | Trace detective | Query LangSmith traces `d890fadf...` and `2c0961fd...`. Map the extraction flow: how many tables did Docling find? How many buildings identified? How many rows sent to per-row LLM? How many records returned? Find the exact drop-off point. |
| `acm-extraction-pre` | Pre-extraction analyst | Read `open_notebook/graphs/source.py`, `open_notebook/extractors/schema_inference.py`, page tagging logic. Check if TOC detection / page range tagging drops register pages. Known issue: page 8 has a 2-row table that TableFormer misses. |
| `acm-extraction-core` | Core extraction analyst | Read `open_notebook/graphs/acm_extraction.py`, `open_notebook/extractors/row_extractor.py`, `open_notebook/extractors/row_segmenter.py`. Trace the per-row extraction path. Check if `ACM_ITEM_EXTRACTION_MODE=per_row` is set. Check prompt templates in `prompts/acm/`. |
| `acm-trace-analyst` | Performance profiler | Read worker logs, time each pipeline stage. Document: content extraction time, table extraction time, pre-extraction intelligence time, per-building extraction time, per-row LLM time. Write findings to `docs/sprint-artifacts/observability/pipeline-audit-2026-04-16.md`. |

**Coordinator (you):** Synthesize findings from all 4 agents. The key question is: **at which exact stage do 31 potential records become 10?**

Possible failure points (investigate in order):
1. Docling only finds tables on some pages (page 8 gap known)
2. Page tagging (`tag_pages` node) excludes register pages
3. Building inventory doesn't include all buildings
4. Per-row segmenter drops rows (subheaders, small tables)
5. Per-row LLM extraction fails silently for some rows
6. `acm_extract` command never triggered (only source_process ran)
7. Ollama model on pod misconfigured (check .env `ACM_EXTRACTION_MODEL`)

---

### Phase 3: Local Full Pipeline Run (PA-3)

**Goal:** Run both test PDFs through the full pipeline locally with observability.

1. Upload Broadmeadows PDF via frontend (`http://localhost:8502`)
2. Monitor worker logs: `tail -f logs/worker.log` (or tmux session)
3. After completion, check:
   - `acm_table_section` count in SurrealDB
   - `acm_record` count in SurrealDB
   - `building_record` count in SurrealDB
   - `command` table — did both `process_source` AND `acm_extract` commands complete?
4. Check LangSmith for the new traces — compare with the 10-record traces
5. Repeat with Alexander District Hospital PDF
6. **Use skill:** `/e2e-test` for verification patterns

**SurrealDB queries:**
```sql
SELECT count() FROM acm_table_section WHERE source_id = type::thing('source', '<id>') GROUP ALL;
SELECT count() FROM acm_record WHERE source_id = type::thing('source', '<id>') GROUP ALL;
SELECT count() FROM building_record WHERE source_id = type::thing('source', '<id>') GROUP ALL;
SELECT id, status, name FROM command WHERE status != 'completed' ORDER BY created_at DESC LIMIT 10;
```

---

### Phase 4: Pipeline Component Audit (PA-4 through PA-7)

**Goal:** Audit each pipeline component for correctness and necessity.

**Use context7** for current Docling, LangGraph, and LangChain API docs.

#### 4A: Table Detection (PA-4)
- Known issue: Broadmeadows page 8 has a 2-row table that TableFormer misses
- Read `commands/source_commands.py:_extract_tables_with_docling()` — check gap detection logic
- Read `open_notebook/extractors/providers/docling_adapter.py`
- **Use context7:** Query Docling docs for `TableFormerMode.ACCURATE` vs `FAST` sensitivity settings
- Investigate: Can we lower the minimum row threshold? Is there a confidence score we can use?

#### 4B: TOC / Page Range Logic (PA-5)
- Read `open_notebook/graphs/acm_extraction.py` — find `tag_pages` node
- Read `open_notebook/extractors/schema_inference.py` — how does it identify register pages?
- Check: Does page tagging correctly identify ALL register pages, or does it stop after the gap?
- **Use skill:** `/langgraph-fundamentals` for graph node patterns

#### 4C: Per-Row LLM Extraction (PA-6)
- Read `open_notebook/extractors/row_extractor.py` — `extract_single_row()`, `extract_all_rows()`
- Read `open_notebook/extractors/row_segmenter.py` — `segment_docling_table()`
- Read prompt templates: `prompts/acm/row_extraction.jinja`, `prompts/acm/building_extraction.jinja`
- Check: Which Ollama model is being used? What's the `num_ctx`? Is structured output working?
- **Use skill:** `/langchain-fundamentals` for LLM call patterns
- **Use context7:** Query Ollama docs for structured output, `num_ctx` limits

#### 4D: Unnecessary Components (PA-7)
- Map the FULL pipeline: every LangGraph node, every LLM call, every DB write
- Identify: vision models, redundant extraction passes, unnecessary validation loops
- Compare: What runs in 45s on RunPod vs what took 37min-1hr locally
- The old pipeline included: embeddings, transformations, multiple LLM retries — are these still needed?

---

### Phase 5: Worker Queue Audit (PA-8 through PA-10)

**Goal:** Verify worker auto-triggers, timing, and reliability.

- Read `commands/source_commands.py:process_source_command()` — does it trigger `acm_extract`?
- Read `commands/acm_commands.py` — how is `acm_extract` triggered?
- Check: Is there an automatic handoff from `process_source` → `acm_extract`, or is it manual?
- Read `run_worker.py` — LIVE query listener, concurrent task handling
- **Use skill:** `/langgraph-persistence` for state management between commands

---

### Phase 6: Speed Benchmark (PA-11)

**Goal:** Benchmark the updated pipeline locally (with OCR fix).

- Time each stage with the local RTX 4090
- Compare: Old (37min-1hr) vs New (expected <2min based on RunPod results)
- Document bottlenecks
- The RTX 4090 should be slightly slower than RTX 5090 but in the same ballpark

---

### Phase 7: Cloud Observability (PA-12)

**Goal:** Configure Langfuse Cloud + LangSmith for RunPod pod.

- Get Langfuse Cloud free tier keys (or use existing)
- SSH to pod: `ssh -i ~/.runpod/ssh/RunPod-Key-Go root@142.127.93.36 -p 11392`
- Update `.env` on pod with cloud Langfuse keys
- Verify tracing works on next extraction

---

## Agent Team Configuration

Use `TeamCreate` to spawn the audit team. The team lead (you) coordinates and synthesizes.

```
Team: pipeline-audit
Members:
  - acm-observability-debugger (sonnet) — trace analysis, read-only
  - acm-extraction-pre (sonnet) — pre-extraction logic audit
  - acm-extraction-core (sonnet) — core extraction logic audit  
  - acm-trace-analyst (sonnet) — performance profiling
  - backend-specialist (sonnet) — code fixes when ready
```

**Coordination pattern:**
1. Phase 0-1: Lead does skill loading + observability setup (sequential)
2. Phase 2: Dispatch all 4 analysis agents in parallel via SendMessage
3. Phase 3: Lead runs local pipeline while agents analyze (parallel)
4. Phase 4: Dispatch agents to audit specific components based on Phase 2 findings
5. Phase 5-7: Lead + backend-specialist apply fixes

**CRITICAL RULES:**
- GPU extraction is a MUST — never disable AcceleratorDevice.AUTO
- Always use context7 for library docs, never rely on training data
- Never use `uv run` on RunPod — always `.venv/bin/python`
- All findings go to `docs/sprint-artifacts/observability/pipeline-audit-2026-04-16.md`
- Update `docs/sprint-artifacts/sprint-status.yaml` PA items as they complete

---

## Success Criteria

- [ ] Broadmeadows: 31/31 records extracted (100% ground truth match)
- [ ] Alexander District: ≥40/43 records extracted (≥93% ground truth match)
- [ ] Pipeline completes in <120s locally on RTX 4090
- [ ] Pipeline completes in <60s on RunPod RTX 5090
- [ ] All pipeline stages visible in Langfuse/LangSmith traces
- [ ] Worker auto-triggers all stages without manual intervention
- [ ] No unnecessary components (vision models, redundant passes) remain
