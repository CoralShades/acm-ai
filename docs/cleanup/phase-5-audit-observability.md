# Phase 5 Audit — Observability Domain

**Agent:** OBSERVABILITY (Phase 5 post-code audit)
**Date:** 2026-04-11
**Branch:** `feat/sf-reconciliation-20260411`
**Scope:** Static review of observability wiring affected by or adjacent to Phase 2a
(commit `5dc3ef30`). No live trace queries. No code changes.

---

## Scope

Six-tool observability stack reviewed:
- Langfuse (self-hosted) — `open_notebook/observability/langfuse_config.py`
- Logfire → OTel bridge — `open_notebook/observability/logfire_config.py`
- LangGraph PipelineLogger bridge — `open_notebook/observability/langfuse_bridge.py`
- Graph wiring — `open_notebook/graphs/acm_extraction.py` (lines 1705-1836, 3090-3160)
- Commands entry point — `commands/acm_commands.py`

Phase 2a changed one file: `open_notebook/graphs/acm_extraction.py` lines 1803-1813
(the `correct_records` node). All five questions enumerated in the audit brief are
answered below.

---

## Findings

### Q1 — Did the Phase 2a `correct_records` rewrite break any Langfuse span emission?

**Verdict: No regression.**

The removed line (`logger.info("[PIPELINE] Prompt template: acm/correction")`) was a
**Loguru log statement**, not a PipelineEventBus event or a Langfuse span. The `pl`
guard (`if pl:`) conditionalized a plain stdout/file log — it emitted nothing to
Langfuse, nothing to the LangChain callback chain, and nothing to the OTel exporter.

The two stage-boundary events for the CORRECT stage are fully preserved:

| Event | Line | Status |
|---|---|---|
| `pl.stage_enter(StageId.CORRECT, ...)` | 1720 | Intact |
| `pl.stage_complete(StageId.CORRECT, ...)` | 1818–1824 | Intact |

The `stage_complete` still reports `auto_corrected`, `llm_corrected`, and `failed`
counts. `llm_corrected` will now always be 0 — this is semantically correct and
accurately reflects the disabled LLM correction path.

**Minor documentation drift:** The `correct_records` docstring (line 1708) still
says "Layer 2 (slow, LLM-based): Call LLM with correction prompt for remaining issues".
This is stale. Should be updated when E38-S2 deletes `_llm_correct_records()`.

### Q2 — `logfire_config.py` `instrument_pydantic()` safety

**Verdict: Guardrail intact. Tests pass.**

Static analysis of `logfire_config.py`:

- `instrument_pydantic()` is **not called** in the module body. It appears only inside
  a comment block (lines 60-82) as documentation of the safe call pattern.
- The comment explicitly records the 48K-span regression risk and the safe `include` set
  (`ACMExtractionRecord`, `BuildingRoomContext`, `ACMItemRecord`, `ACMExtractionResult`,
  `ACMItemExtractionResult`).
- Guarding rule is also enforced in `.claude/rules/observability-ops.md` §2.

Smoke test results:

```
tests/test_observability_config_smoke.py::test_langfuse_config_module_imports  PASSED
tests/test_observability_config_smoke.py::test_langfuse_tracing_is_context_manager  PASSED
tests/test_observability_config_smoke.py::test_logfire_config_module_imports  PASSED
tests/test_observability_config_smoke.py::test_no_blanket_instrument_pydantic_call  PASSED
tests/test_observability_config_smoke.py::test_langfuse_bridge_imports_cleanly  PASSED
5 passed in 16.45s
```

The `test_no_blanket_instrument_pydantic_call` test strips docstrings and comments
before scanning for `instrument_pydantic(` calls, so the guidance text does not
produce a false positive.

### Q3 — Callback placement: did Phase 2a introduce any in-node callback setup?

**Verdict: Phase 2a is clean. One pre-existing violation exists but is protected.**

The diff for commit `5dc3ef30` modifies only lines 1803-1813 of `correct_records()`.
Those 10 lines contain zero callback, handler, or Langfuse references. Phase 2a
introduced no new callback placement violations.

**Pre-existing exception (not introduced by this sprint):**
`acm_extraction.py:1253` — `langfuse_handler = get_langfuse_handler()` is called
inside the item extraction node. This violates the `.claude/rules/observability-ops.md`
§4 rule ("Callbacks belong at the invocation site, NEVER inside graph node functions").
However:
1. The handler at line 1253 is passed to `extract_all_rows()` as a tracing context
   argument, not injected into the LangGraph `config["callbacks"]`. It is a function
   parameter, not a graph-level callback registration.
2. The file is explicitly protected by CLAUDE.md: "Do NOT modify Langfuse wiring in
   `open_notebook/graphs/acm_extraction.py`".
3. This pre-dates the current sprint.

This pre-existing pattern should be reviewed and potentially refactored in E38-S2 or
a dedicated observability cleanup story.

### Q4 — PipelineEventBus stage progress: correct stage still emitted after the fix?

**Verdict: Stage events intact. `stage_complete` correctly reflects new behaviour.**

The `correct_records()` function:
1. Calls `pl.stage_enter(StageId.CORRECT, ...)` at line 1720 — unchanged.
2. Runs Layer 1 normalization — unchanged.
3. For records still needing correction, now increments `correction_stats["failed"]`
   directly instead of calling `_llm_correct_records()` — changed.
4. Calls `pl.stage_complete(StageId.CORRECT, ...)` at line 1818 with full stats —
   unchanged.

No PipelineEventBus event was removed. The `stage_complete` payload now accurately
shows `llm_corrected=0` for every run. Any dashboard or Langfuse trace that previously
showed non-zero `llm_corrected` counts will show 0 going forward — this is the
intended behaviour change, not a regression.

The `agui.emit_step_finished("correct", ...)` call at line 1826 is also unchanged.

### Q5 — `langfuse_tracing()` safety when `LANGFUSE_ENABLED=false`

**Verdict: Fully safe. No exceptions, no side effects.**

Code path when `LANGFUSE_ENABLED=false`:

```
langfuse_tracing(...)
  → get_langfuse_handler()
      → is_langfuse_enabled() → False
      → return None                              # handler = None

  → append_langfuse_callback([], None) → []      # callbacks = []
  → _try_inject_otel_trace_context(...) skipped  # otel_token = None
  → yield ([], metadata)                         # graph runs normally

  finally:
    → _try_detach_otel_context(None)  → no-op
    → flush_langfuse_handler(None)    → no-op
```

The caller pattern:
```python
with langfuse_tracing(...) as (cb, meta):
    config = merge_langfuse_into_config(base_config, cb, meta)
    # cb = [] → merge_langfuse_into_config returns base_config unchanged
```

`merge_langfuse_into_config` guards on `if not callbacks: return config`, so no
callbacks key is injected and the graph config is unmodified. The full happy path runs
without any Langfuse imports being exercised.

---

## Recommendations

| Priority | Finding | Action |
|---|---|---|
| LOW | `correct_records` docstring still says "Layer 2 LLM-based" | Update docstring in E38-S2 when `_llm_correct_records()` is deleted |
| LOW | `_llm_correct_records()` at line 1853 is dead code | Delete in E38-S2 (already planned in SCP §4) |
| MEDIUM | Pre-existing `get_langfuse_handler()` call inside item-extraction node (line 1253) technically violates callback-placement rule | Evaluate in E38 observability cleanup. Currently protected by CLAUDE.md "do NOT modify" directive. Not introduced by this sprint. |
| INFO | `test_observability_config_smoke.py` has no test for `langfuse_tracing()` under disabled mode | Consider adding `test_langfuse_tracing_noop_when_disabled()` to hardness the Q5 finding |

No critical or high-priority findings. All observability invariants are intact
after the Phase 2a change.

---

## References

- `open_notebook/observability/langfuse_config.py` — `langfuse_tracing()`, `get_langfuse_handler()`
- `open_notebook/observability/logfire_config.py` — `init_logfire()`, `instrument_pydantic()` guard
- `open_notebook/observability/langfuse_bridge.py` — `emit_pipeline_event()`
- `open_notebook/graphs/acm_extraction.py:1705-1836` — `correct_records()` node
- `open_notebook/graphs/acm_extraction.py:3090-3160` — `extract_acm_from_source()` entry point
- `open_notebook/graphs/acm_extraction.py:1253` — pre-existing in-node handler (pre-sprint)
- `.claude/rules/observability-ops.md` — callback placement + instrument_pydantic rules
- `tests/test_observability_config_smoke.py` — 5/5 passed
- `git show 5dc3ef30` — Phase 2a diff (22 changed lines, correct_records only)
