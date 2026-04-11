# Technical Debt — Full System Audit 2026-04-09

Items identified during the 2026-04-09 full system audit that are deferred for future sprints.
Ordered by impact. Items #1–4 from the same audit were actioned immediately (see fixer Task #5).

---

## MEDIUM Priority

### TD-1: Broad Exception Handling Masks Extraction Failures
**File:** `open_notebook/graphs/acm_extraction.py` lines ~426, ~532, ~1129  
**Pattern:**
```python
except Exception as e:
    logger.warning(f"Combined metadata+structure extraction failed: {e}")
    return {"document_metadata": None, "document_structure": None}
```
**Problem:** Nodes like `metadata_and_structure_node` and `compile_inventory` silently return empty dicts on any failure. Downstream nodes receive `None` context and produce degraded output without any user-visible signal. The pipeline "succeeds" but quality is silently worse.  
**Fix approach:** Replace bare `except Exception` with specific exception types; emit an SSE event on node failure so the UI can indicate degraded mode.  
**Effort:** M (~4h)  
**Found by:** pipeline-inspector (2026-04-09)

---

### TD-2: unified_agent MemorySaver — No Chat Session Persistence
**File:** `open_notebook/graphs/unified_agent.py`  
**Problem:** The `unified_agent` graph uses `MemorySaver` (in-memory checkpointer). All chat session state is lost every time the LangGraph dev server restarts. The comment in `checkpointer.py` notes "upgrade to SqliteSaver planned".  
**Note:** The main `AsyncSqliteSaver` in `checkpointer.py` is used by the unified chat (per fix-chat-pipeline-async-tools-2026-03-23). This affects only the LangGraph **dev server** instance, not production. In production, the unified_agent is invoked via FastAPI, not LangGraph dev server.  
**Fix approach:** Wire `AsyncSqliteSaver` from `checkpointer.py` into the LangGraph dev server config (`.langgraph_api/` config).  
**Effort:** S (~1h)  
**Found by:** pipeline-inspector (2026-04-09)

---

### TD-3: Product Name Normalization + Room-Level Deduplication
**File:** `open_notebook/extractors/normalizers/enums.py`, extraction pipeline  
**Problem:** Extracted product names don't exactly match expected ground truth terminology:
- "Fuses" vs "Fuse cartridge"
- "Flange mastic (grey)" vs "Flange joints"
- "Fibre cement sheet infill panel" vs "Infill panels"

Additionally, room-level deduplication is needed: Fan Room produced 4 records where only 2 are expected (records 39, 40, 41, 43).  
**Fix approach:** (1) Add synonym mapping to normalizer enums for product name variants. (2) Implement deduplication by `(room_name, product, result)` tuple within the same building in the `deduplicate` graph node.  
**Effort:** M (~4h)  
**Found by:** extraction-runner (2026-04-09)

---

## LOW Priority

### TD-4: Ollama Docker Healthcheck False Alarm
**File:** `docker-compose.yml` — ollama service healthcheck  
**Problem:** `acm-ai-ollama` container has been marked Docker `(unhealthy)` for 2+ weeks. The API at `localhost:11434` responds correctly. The healthcheck command likely probes in a way that times out or doesn't match expected output.  
**Fix approach:** Inspect `docker-compose.yml` ollama healthcheck command; adjust to `curl -f http://localhost:11434/api/tags` or similar.  
**Effort:** XS (~15min)  
**Found by:** log-monitor (2026-04-09)

---

### TD-5: Frontend next.config.ts Config Warnings
**File:** `frontend/next.config.ts`  
**Problem:**
1. `experimental.esmExternals: "loose"` — Next.js warns this disrupts module resolution
2. Webpack devtool set in development mode — causes performance regression warning

**Fix approach:** Remove `experimental.esmExternals` from config; check if webpack devtool override is still needed.  
**Effort:** XS (~15min)  
**Found by:** log-monitor (2026-04-09)

---

### TD-6: Langfuse Trace Accumulation (243K traces)
**File:** N/A — operational  
**Problem:** 243,743 traces accumulated since system setup. Langfuse UI may become slow; the `/api/public/traces` endpoint is already returning >4MB responses. The `/trace-cleanup` custom command is available.  
**Fix approach:** Run `/trace-cleanup` to remove old traces (filter by date range, keep last 30 days). Add to maintenance schedule.  
**Effort:** XS (run command)  
**Found by:** pipeline-inspector (2026-04-09)

---

### TD-7: Langfuse Trace Metadata — document_type and extraction_model Always Default
**File:** `open_notebook/graphs/acm_extraction.py` line ~3108–3114, `open_notebook/observability/langfuse_config.py`  
**Problem:** `build_langfuse_metadata()` is called without `document_type` parameter (defaults to "unknown"). The `extraction_model` shows "default" because model_id isn't resolved at trace creation time. This reduces Langfuse filter/search utility.  
**Fix approach:** (1) Pass `document_type` from `DocumentMeta` after structure extraction node completes. (2) Resolve actual model ID from DB before calling `build_langfuse_metadata()`.  
**Effort:** S (~1h)  
**Found by:** pipeline-inspector (2026-04-09)

---

### TD-8: AI-Editor Card Navigation UX
**File:** `frontend/src/app/(dashboard)/ai-editor/page.tsx` or notebook card component  
**Problem:** Clicking the AI-Editor card body opens an Archive/Delete context menu instead of navigating to the detail page. The title link may not be exposed as a standalone clickable element.  
**Fix approach:** Wrap card in a `Link` component; separate the three-dot menu trigger from the card click area. Pattern exists on job cards for reference.  
**Effort:** S (~30min)  
**Found by:** browser-tester (2026-04-09)

---

### TD-9: SurrealDB Startup Credential Warning
**File:** `docker-compose.yml` — surrealdb service command  
**Problem:** `--user root --pass root` args are passed on every restart but root user already exists. Generates cosmetic but noisy warnings on every container restart.  
**Fix approach:** Either remove `--user`/`--pass` from start command (root credentials persist in storage), or suppress the warning if the startup flexibility is needed.  
**Effort:** XS (~10min)  
**Found by:** log-monitor (2026-04-09)

---

## Summary Table

| ID | Description | Priority | Effort | Owner |
|----|-------------|----------|--------|-------|
| TD-1 | Broad exception handling masks extraction failures | MEDIUM | M | — |
| TD-2 | MemorySaver in LangGraph dev server | MEDIUM | S | — |
| TD-3 | Product name normalization + deduplication | MEDIUM | M | — |
| TD-4 | Ollama Docker healthcheck false alarm | LOW | XS | — |
| TD-5 | Frontend next.config.ts config warnings | LOW | XS | — |
| TD-6 | Langfuse trace accumulation (243K) | LOW | XS | — |
| TD-7 | Langfuse trace metadata defaults | LOW | S | — |
| TD-8 | AI-Editor card navigation UX | LOW | S | — |
| TD-9 | SurrealDB startup credential warning | LOW | XS | — |

*Note: Issues #1–6 from the same audit (Assumed Positive regression, cloud fallback, over-extraction, missing fields, validation-summary, status badge) were actioned immediately by the fixer agent (Task #5).*
