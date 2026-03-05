# E34-S3: Performance Optimization — Tech Spec

## Overview

This story adds lightweight performance instrumentation, GPU memory management, and a CI
regression test suite to the V3 extraction pipeline. The goal is to make performance
measurable and protected against regressions — not to redesign the pipeline.

Concretely, the story:

1. Adds wall-clock timing instrumentation to `_run_dual_provider_extraction` in
   `commands/source_commands.py` so that per-stage timings (Docling, MinerU, merge,
   consensus, AI orchestration) are logged and returned in a structured `PipelineTimings`
   object.
2. Adds explicit `torch.cuda.empty_cache()` calls between the Docling and MinerU provider
   runs (CUDA-guarded: only when `torch.cuda.is_available()` is True).
3. Adds `cleanup()` methods to `DoclingAdapter` and `MinerUAdapter` so callers can
   explicitly release model references and trigger Python garbage collection after each
   provider run.
4. Writes `tests/test_v3_performance.py` — a CI-safe performance regression test that
   uses fully mocked extractors. No real PDFs or GPU are required.
5. Creates `docs/benchmarks/v3-performance-report.md` documenting the expected pipeline
   timings for Broadmeadows (20 pages, 1 building) and Alexander (48 pages, 6 buildings)
   based on the existing design, along with the top-3 bottlenecks and future
   optimization opportunities.

AC1 (Broadmeadows < 120 s) and AC2 (Alexander < 300 s) are **measurement and
documentation** criteria only. They are verified by running the real pipeline on
target hardware and recording results in the performance report. No automated test
enforces these wall-clock thresholds in CI because CI environments have no GPU and
no production PDFs.

---

## Background / Context

### What Already Exists

| Component | Location | Status |
|-----------|----------|--------|
| `_run_dual_provider_extraction` | `commands/source_commands.py` | Done — runs Docling then MinerU sequentially |
| `DoclingAdapter` | `open_notebook/extractors/providers/docling_adapter.py` | Done — no cleanup method |
| `MinerUAdapter` | `open_notebook/extractors/providers/mineru_adapter.py` | Done — no cleanup method |
| `NormalizedExtractionResult` | `open_notebook/extractors/providers/base.py` | Done — no timing fields |
| `PipelineLogger` | `open_notebook/extractors/pipeline_events.py` | Done — stage_enter/stage_complete |
| `OrchestratorStats` | `open_notebook/extractors/orchestrator.py` | Done — `total_time_ms` field |
| Existing benchmarks dir | `docs/benchmarks/` | `v3-dual-provider-report.md` exists |

### Sequential Provider Design (Already Correct)

`_run_dual_provider_extraction` already runs Docling first, then MinerU. The comment in
the code explicitly states this is intentional: "Run Docling then (optionally) MinerU
sequentially to prevent VRAM contention." This architecture is correct and must not be
changed. The gap is that no `torch.cuda.empty_cache()` call is made between the two
provider runs, and there is no `cleanup()` method to release model references.

### GPU Memory Concern

Docling uses TableFormer (a PyTorch model). MinerU 2.x also uses a PyTorch-based layout
model. Without an explicit CUDA cache flush between runs, GPU fragmentation can build up
over multiple consecutive document extractions (AC4). The fix is simple: call
`torch.cuda.empty_cache()` after Docling finishes and before MinerU starts, guarded by
`torch.cuda.is_available()`.

### Timing Instrumentation Gap

No structured timing output currently exists. `time.monotonic()` calls are already in
the adapters (`start_ms` / `elapsed_ms`) but the results are only logged at `INFO`
level — they are not returned up the call stack. The orchestrator has `total_time_ms`
but it tracks AI extraction time, not PDF provider time. This story adds a
`PipelineTimings` dataclass and populates it throughout the dual-provider call.

---

## Technical Approach

### AC3 — GPU Memory Management (Sequential Docling → MinerU + cache flush)

**Location**: `commands/source_commands.py`, `_run_dual_provider_extraction`, after the
Docling extract call and before the MinerU extract call.

```python
# After Docling finishes:
await _store_raw_extractions(source_id, docling_result)

# AC3: flush GPU cache between providers (CUDA-safe guard)
try:
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.debug("GPU cache flushed between Docling and MinerU")
except ImportError:
    pass  # torch not installed — skip silently

# Then MinerU runs:
mineru_provider = registry.get_provider("mineru")
mineru_result = mineru_provider.extract(pdf_path)
```

This is a 6-line addition with zero behavioral change when CUDA is unavailable (the
common CI case). `torch` is already a transitive dependency via Docling/MinerU so the
import will not fail in production; the `try/except ImportError` guard handles the edge
case of a stripped-down test environment.

**Adapter cleanup calls** are made after each extract in `_run_dual_provider_extraction`:

```python
docling_result = docling_provider.extract(pdf_path, pipeline_logger=pipeline_logger)
docling_provider.cleanup()   # release model refs, call gc.collect()
```

```python
mineru_result = mineru_provider.extract(pdf_path)
mineru_provider.cleanup()    # release model refs, call gc.collect()
```

### AC4 — Memory Leak Prevention (cleanup() methods on adapters)

Add a `cleanup()` method to both `DoclingAdapter` and `MinerUAdapter`. The method:
1. Deletes any cached model/converter reference (if the adapter ever stored one).
2. Calls `gc.collect()` to trigger Python's garbage collector.
3. Calls `torch.cuda.empty_cache()` if CUDA is available.

**DoclingAdapter** — currently creates a `DocumentConverter` inside `_run_extraction()`
on every call (no persistent state). The `cleanup()` method is therefore a no-op GC
nudge, but it establishes the protocol for future caching:

```python
def cleanup(self) -> None:
    """Release resources after extraction. Safe to call multiple times."""
    import gc
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
```

**MinerUAdapter** — same pattern. `MinerUDocumentConverter` is instantiated inside
`_run_extraction()` with no persistent state, so cleanup is a GC + cache flush:

```python
def cleanup(self) -> None:
    """Release resources after extraction. Safe to call multiple times."""
    import gc
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
```

If either adapter is ever refactored to cache its converter for reuse (a future
performance optimization), the `cleanup()` contract allows callers to explicitly
invalidate that cache.

### AC5 — Profiling Report (wall-clock timing instrumentation)

**Step 1: Add `PipelineTimings` dataclass** to `open_notebook/extractors/providers/base.py`:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PipelineTimings:
    """Wall-clock timings (milliseconds) for each stage of the extraction pipeline."""
    docling_ms: int = 0
    gpu_flush_ms: int = 0
    mineru_ms: int = 0
    merge_ms: int = 0
    consensus_ms: int = 0
    total_provider_ms: int = 0
```

**Step 2: Populate `PipelineTimings` in `_run_dual_provider_extraction`** and return it
alongside the merged tables. The function signature changes from:

```python
async def _run_dual_provider_extraction(
    source_id: str,
    pdf_path: str,
    pipeline_logger: Optional[PipelineLogger] = None,
) -> List[Dict[str, Any]]:
```

to:

```python
async def _run_dual_provider_extraction(
    source_id: str,
    pdf_path: str,
    pipeline_logger: Optional[PipelineLogger] = None,
) -> tuple[List[Dict[str, Any]], PipelineTimings]:
```

The return type change is backward-compatible because the single call site in
`source_commands.py` (line ~613) is `merged_tables = await _run_dual_provider_extraction(...)`.
That call site must be updated to unpack both values:
`merged_tables, timings = await _run_dual_provider_extraction(...)`.

Timing pattern inside the function:

```python
import time

t0 = time.perf_counter()
docling_result = docling_provider.extract(pdf_path, pipeline_logger=pipeline_logger)
docling_provider.cleanup()
timings.docling_ms = int((time.perf_counter() - t0) * 1000)

t1 = time.perf_counter()
# GPU flush here
timings.gpu_flush_ms = int((time.perf_counter() - t1) * 1000)

t2 = time.perf_counter()
mineru_result = mineru_provider.extract(pdf_path)
mineru_provider.cleanup()
timings.mineru_ms = int((time.perf_counter() - t2) * 1000)

t3 = time.perf_counter()
merged = _merge_provider_tables(docling_result, mineru_result)
timings.merge_ms = int((time.perf_counter() - t3) * 1000)

timings.total_provider_ms = timings.docling_ms + timings.gpu_flush_ms + timings.mineru_ms + timings.merge_ms
```

**Step 3: Log the timing summary** at `INFO` level after the function returns:

```python
logger.info(
    f"Provider timings | "
    f"docling={timings.docling_ms}ms "
    f"mineru={timings.mineru_ms}ms "
    f"merge={timings.merge_ms}ms "
    f"total={timings.total_provider_ms}ms"
)
```

**Step 4: Create `docs/benchmarks/v3-performance-report.md`** (see File Changes Table).
This document records:
- The top-3 pipeline bottlenecks (AI LLM calls, Docling TableFormer, MinerU layout model)
- Baseline timing estimates per document class
- Optimization opportunities (token budget tuning, Docling model size selection, MinerU
  disable fallback for CPU environments)
- Instructions for re-running benchmark measurements

### AC6 — Performance Regression Test (CI-safe, fully mocked)

`tests/test_v3_performance.py` must not require a GPU, real PDF, or running SurrealDB.
It verifies three things:

1. **Timing instrumentation is wired**: `_run_dual_provider_extraction` returns a
   `PipelineTimings` object with non-negative integer fields.
2. **Cleanup is called**: `DoclingAdapter.cleanup()` and `MinerUAdapter.cleanup()` are
   called after their respective `extract()` calls (verified via mock call count).
3. **GPU flush is attempted**: When a mock `torch.cuda.is_available()` returns `True`,
   `torch.cuda.empty_cache()` is called exactly once between Docling and MinerU.

The test stubs out:
- Both provider adapters (`MagicMock` with `extract` returning a minimal
  `NormalizedExtractionResult`)
- `_store_raw_extractions` (`AsyncMock`)
- `get_provider_registry` (returns the mock registry)
- `torch.cuda` (mocked module so CI Python environments without CUDA still run the test)

Example test class structure:

```python
class TestProviderTimingInstrumentation:
    """AC6: timing fields are populated and non-negative."""

    @pytest.mark.asyncio
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_timing_fields_populated(self, mock_registry, mock_store):
        ...
        merged_tables, timings = await _run_dual_provider_extraction(
            "source:perf_test", "/tmp/fake.pdf"
        )
        assert timings.docling_ms >= 0
        assert timings.total_provider_ms >= 0

class TestCleanupCalled:
    """AC4/AC6: cleanup() invoked after each provider."""

    @pytest.mark.asyncio
    async def test_docling_cleanup_called(self, ...):
        ...
        docling_mock.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_mineru_cleanup_called_in_dual_mode(self, ...):
        ...
        mineru_mock.cleanup.assert_called_once()

class TestGpuCacheFlush:
    """AC3/AC6: torch.cuda.empty_cache() called between providers when CUDA available."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    async def test_cuda_cache_flushed_when_available(self, ...):
        # Patch torch inside the source_commands module namespace
        with patch("commands.source_commands.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            ...
            mock_torch.cuda.empty_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_cuda_flush_skipped_when_unavailable(self, ...):
        with patch("commands.source_commands.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            ...
            mock_torch.cuda.empty_cache.assert_not_called()
```

**Note on torch import in `source_commands.py`**: The `torch` import must be a
module-level optional import with a guard, not a top-level unconditional import. The
recommended pattern:

```python
# At module top level (after existing imports):
try:
    import torch as _torch
except ImportError:
    _torch = None  # type: ignore[assignment]
```

Then inside `_run_dual_provider_extraction`:

```python
if _torch is not None and _torch.cuda.is_available():
    _torch.cuda.empty_cache()
```

This avoids the `try/except ImportError` block scattered inside the function body and
makes the `torch` reference patchable via `patch("commands.source_commands._torch")`.

---

## File Changes Table

| File | Change Type | Description |
|------|-------------|-------------|
| `commands/source_commands.py` | modify | Add optional `_torch` import at module top; add GPU cache flush between Docling and MinerU in `_run_dual_provider_extraction`; add `PipelineTimings` population; change return type to `tuple[list, PipelineTimings]`; call `cleanup()` on each adapter after extraction; update the single call site to unpack the tuple |
| `open_notebook/extractors/providers/base.py` | modify | Add `PipelineTimings` dataclass |
| `open_notebook/extractors/providers/docling_adapter.py` | modify | Add `cleanup()` method |
| `open_notebook/extractors/providers/mineru_adapter.py` | modify | Add `cleanup()` method |
| `tests/test_v3_performance.py` | create | CI-safe regression test: timing fields populated, cleanup called, GPU cache flushed |
| `docs/benchmarks/v3-performance-report.md` | create | Human-readable performance report: Broadmeadows/Alexander timings, top-3 bottlenecks, profiling instructions |

---

## Acceptance Criteria Mapping

| AC | Implementation |
|----|----------------|
| AC1: Broadmeadows < 120 s | Documented in `docs/benchmarks/v3-performance-report.md` as a design target. Verified by running pipeline on GPU hardware and recording timings. Not enforced in CI. |
| AC2: Alexander < 300 s | Same as AC1 — documented target verified on GPU hardware. |
| AC3: Sequential Docling → MinerU + `torch.cuda.empty_cache()` | Already sequential; `empty_cache()` call added in `_run_dual_provider_extraction` between providers, CUDA-guarded. Verified by `TestGpuCacheFlush` in `tests/test_v3_performance.py`. |
| AC4: No memory leaks over 10 consecutive extractions | `cleanup()` method on both adapters calls `gc.collect()` + `empty_cache()` after each document. Verified by `TestCleanupCalled` and by the leak-detection test in `tests/test_v3_performance.py`. |
| AC5: Profiling report — top-3 bottlenecks | `docs/benchmarks/v3-performance-report.md` identifies AI LLM calls (per-building), Docling TableFormer inference, and MinerU layout model as the three dominant bottlenecks, with measured or estimated durations. |
| AC6: Performance regression test in CI | `tests/test_v3_performance.py` — fully mocked, passes in CI without GPU or real PDFs. Tests timing instrumentation, cleanup, and GPU flush path. |

---

## Test Plan

### `tests/test_v3_performance.py` (new file)

#### `TestProviderTimingInstrumentation`

1. **`test_timing_fields_populated_single_provider`**
   - Mock: Docling provider only (dual-provider disabled via env)
   - Assert: returned `PipelineTimings` has `docling_ms >= 0`, `total_provider_ms >= 0`,
     `mineru_ms == 0`

2. **`test_timing_fields_populated_dual_provider`**
   - Mock: both Docling and MinerU providers, dual-provider enabled
   - Assert: `docling_ms >= 0`, `mineru_ms >= 0`, `merge_ms >= 0`,
     `total_provider_ms == docling_ms + gpu_flush_ms + mineru_ms + merge_ms`

3. **`test_return_type_is_tuple`**
   - Assert `isinstance(result, tuple)` and `len(result) == 2`
   - Assert first element is a list, second is `PipelineTimings`

#### `TestCleanupCalled`

4. **`test_docling_cleanup_called_single_provider`**
   - Mock Docling provider as `MagicMock` with `cleanup` method
   - Assert `docling_mock.cleanup.call_count == 1`

5. **`test_docling_cleanup_called_dual_provider`**
   - Both providers mocked; dual enabled
   - Assert `docling_mock.cleanup.call_count == 1`

6. **`test_mineru_cleanup_called_dual_provider`**
   - Both providers mocked; dual enabled
   - Assert `mineru_mock.cleanup.call_count == 1`

7. **`test_mineru_cleanup_not_called_single_provider`**
   - Dual disabled
   - Assert `mineru_mock.cleanup.call_count == 0`

8. **`test_cleanup_called_even_on_mineru_failure`**
   - `mineru_mock.extract.side_effect = ProviderError("mineru", "test")`
   - Assert `docling_mock.cleanup.call_count == 1` (cleanup still called after Docling)

#### `TestGpuCacheFlush`

9. **`test_cuda_empty_cache_called_when_cuda_available`**
   - Dual provider enabled; patch `commands.source_commands._torch` with mock
   - `mock_torch.cuda.is_available.return_value = True`
   - Assert `mock_torch.cuda.empty_cache.call_count == 1`

10. **`test_cuda_empty_cache_not_called_when_cuda_unavailable`**
    - `mock_torch.cuda.is_available.return_value = False`
    - Assert `mock_torch.cuda.empty_cache.call_count == 0`

11. **`test_cuda_flush_skipped_when_torch_none`**
    - Patch `commands.source_commands._torch = None`
    - Assert no AttributeError is raised; function completes normally

12. **`test_cuda_flush_not_called_in_single_provider_mode`**
    - Dual disabled (MinerU never runs)
    - Assert `empty_cache` not called (flush is only needed between providers)

#### `TestMemoryLeakGuard`

13. **`test_consecutive_extractions_no_growing_gc_objects`**
    - Run `_run_dual_provider_extraction` 10 times with mocked providers
    - Track `gc.get_count()` before first and after last run
    - Assert: no more than 100 net new objects in generation 0 (a loose but
      meaningful bound that catches obvious leaks)
    - Note: This test is an approximation — it cannot catch CUDA memory leaks in
      a CPU-only test environment, but it catches Python object leaks.

### Existing Tests — No Regressions

The call site change (unpacking tuple instead of plain list) must not break any existing
test that calls `_run_dual_provider_extraction`. Check:

- `tests/test_v3_e2e_pipeline.py` — patches `_run_dual_provider_extraction` indirectly
  via `source_commands`. No direct calls to the function; no change needed.
- `tests/test_raw_extraction_storage.py` — calls `_run_dual_provider_extraction`
  directly. Must be updated to unpack the tuple: `merged, _ = await _run_dual_provider_extraction(...)`.
- `tests/test_dual_provider_pipeline.py` — same update if it calls the function directly.

Run the full test suite to confirm no regressions:

```bash
uv run pytest tests/ -x -q
```

---

## `docs/benchmarks/v3-performance-report.md` Content Outline

The performance report covers:

### 1. Document Classes

| Document | Pages | Buildings | Provider Mode |
|----------|-------|-----------|---------------|
| Broadmeadows | 20 | 1 | Docling-only (single-provider default) |
| Alexander | 48 | 6 | Docling-only (single-provider default) |
| Alexander (dual) | 48 | 6 | Docling + MinerU (V3_DUAL_PROVIDER=true) |

### 2. Stage Breakdown (Estimated)

| Stage | Broadmeadows | Alexander |
|-------|-------------|-----------|
| Docling PDF extraction | ~15–25 s | ~35–60 s |
| MinerU extraction (dual mode only) | ~20–40 s | ~50–90 s |
| GPU cache flush | <1 s | <1 s |
| Consensus merge | <1 s | <2 s |
| AI building extraction (per building × N) | ~20–40 s | ~60–120 s |
| AI item extraction (per building × N) | ~15–30 s | ~50–90 s |
| DB persistence | ~1–3 s | ~3–8 s |
| **Total (single-provider)** | **~50–100 s** | **~150–280 s** |
| **Total (dual-provider)** | **~90–160 s** | **~250–370 s** |

These are design-time estimates based on:
- TableFormer ACCURATE mode: ~0.8–1.5 s/page on consumer GPU
- MinerU 2.x layout model: ~1.0–2.0 s/page
- AI extraction: ~3–8 s/building per LLM call at typical provider latency

### 3. Top-3 Bottlenecks

1. **AI LLM calls per building** — the dominant cost for multi-building documents.
   Each building triggers at least one (and up to three with correction loops) LLM
   calls. For Alexander (6 buildings), this accounts for ~50–70% of total runtime.
   Optimization: batch building context across fewer calls; reduce correction retries
   by improving system prompt quality.

2. **Docling TableFormer (ACCURATE mode)** — runs a full ML inference pass per table
   per page. For a 48-page document with 20 tables, this is the second largest
   contributor. Optimization: switch to `TableFormerMode.FAST` for documents where
   table complexity is low; add a document complexity pre-check to select the mode
   automatically.

3. **MinerU layout model (dual-provider mode only)** — adds 50–90 s on top of
   Docling for Alexander. Optimization: only enable dual-provider mode when Docling
   confidence is below threshold (e.g., no tables found on more than 2 pages);
   add a consensus confidence gate.

### 4. Profiling Instructions

To re-run measurements:

```bash
# Single document benchmark (requires real PDF + running DB)
RUN_E2E_LLM=true uv run pytest tests/benchmarks/test_v3_dual_provider.py -v -s

# Structured timing log — visible in API/worker stdout
# Look for lines: "Provider timings | docling=...ms mineru=...ms ..."
```

### 5. Regression Threshold

The CI regression test (`tests/test_v3_performance.py`) does not enforce wall-clock
thresholds. A 5% increase in production timing between releases should trigger a
manual review using the benchmark instructions above.

---

## Notes / Risks

- **Risk 1 (LOW)**: The `_run_dual_provider_extraction` return type changes from
  `List[Dict]` to `tuple[List[Dict], PipelineTimings]`. This is a breaking change for
  any direct caller. The only production call site is in `source_commands.py` itself.
  Two test files (`test_raw_extraction_storage.py`, `test_dual_provider_pipeline.py`)
  call the function directly and must be updated to unpack the tuple.

- **Risk 2 (LOW)**: `torch` is already a transitive dependency (Docling, MinerU) but is
  not listed in `pyproject.toml` as a direct dependency. The optional import pattern
  (`try: import torch as _torch except ImportError: _torch = None`) handles environments
  where torch is absent.

- **Risk 3 (LOW)**: `DoclingAdapter` and `MinerUAdapter` currently have no persistent
  model state, so `cleanup()` is a GC nudge only. The method is still necessary to
  establish the cleanup contract for future adapter versions that may cache converters.

- **Risk 4 (LOW)**: The `TestMemoryLeakGuard` test using `gc.get_count()` is an
  approximation. It will not catch CUDA VRAM leaks in a CPU-only CI environment.
  Real VRAM leak verification requires manual testing on GPU hardware following the
  profiling instructions in the performance report.

- **Risk 5 (NONE)**: Frontend changes are not required for this story. All changes are
  confined to the Python backend and test/docs layers.
