# V3 Performance Report

Story: E34-S3 Performance Optimization

## 1. Document Classes

| Document | Pages | Buildings | Provider Mode |
|----------|-------|-----------|---------------|
| Broadmeadows | 20 | 1 | Docling-only (single-provider default) |
| Alexander | 48 | 6 | Docling-only (single-provider default) |
| Alexander (dual) | 48 | 6 | Docling + MinerU (V3_DUAL_PROVIDER=true) |

## 2. Stage Breakdown (Estimated)

| Stage | Broadmeadows | Alexander |
|-------|-------------|-----------|
| Docling PDF extraction | ~15-25 s | ~35-60 s |
| MinerU extraction (dual mode only) | ~20-40 s | ~50-90 s |
| GPU cache flush | <1 s | <1 s |
| Consensus merge | <1 s | <2 s |
| AI building extraction (per building x N) | ~20-40 s | ~60-120 s |
| AI item extraction (per building x N) | ~15-30 s | ~50-90 s |
| DB persistence | ~1-3 s | ~3-8 s |
| **Total (single-provider)** | **~50-100 s** | **~150-280 s** |
| **Total (dual-provider)** | **~90-160 s** | **~250-370 s** |

These are design-time estimates based on:

- TableFormer ACCURATE mode: ~0.8-1.5 s/page on consumer GPU
- MinerU 2.x layout model: ~1.0-2.0 s/page
- AI extraction: ~3-8 s/building per LLM call at typical provider latency

## 3. Top-3 Bottlenecks

### 1. AI LLM calls per building

The dominant cost for multi-building documents. Each building triggers at least
one (and up to three with correction loops) LLM calls. For Alexander (6
buildings), this accounts for approximately 50-70% of total runtime.

**Optimization opportunities:**

- Batch building context across fewer calls
- Reduce correction retries by improving system prompt quality
- Use faster LLM providers or smaller models for validation passes

### 2. Docling TableFormer (ACCURATE mode)

Runs a full ML inference pass per table per page. For a 48-page document with
20 tables, this is the second largest contributor.

**Optimization opportunities:**

- Switch to `TableFormerMode.FAST` for documents where table complexity is low
- Add a document complexity pre-check to select the mode automatically
- Consider caching the DocumentConverter instance across calls (with cleanup)

### 3. MinerU layout model (dual-provider mode only)

Adds 50-90 s on top of Docling for Alexander. Only runs when
`V3_DUAL_PROVIDER=true` and `MINERU_ENABLED=true`.

**Optimization opportunities:**

- Only enable dual-provider mode when Docling confidence is below threshold
  (e.g., no tables found on more than 2 pages)
- Add a consensus confidence gate to skip MinerU when Docling results are
  high-confidence
- Consider running MinerU only on pages where Docling found no tables

## 4. Profiling Instructions

### Running a single-document benchmark

Requires a real PDF, running SurrealDB, and appropriate API keys:

```bash
# Single document benchmark (requires real PDF + running DB)
RUN_E2E_LLM=true uv run pytest tests/benchmarks/test_v3_dual_provider.py -v -s
```

### Reading structured timing logs

The pipeline emits structured timing logs at INFO level in the API/worker stdout.
Look for lines matching this pattern:

```
Provider timings | docling=...ms mineru=...ms merge=...ms total=...ms
```

### Running the CI regression test

The CI regression test verifies instrumentation wiring without requiring GPU or
real PDFs:

```bash
uv run pytest tests/test_v3_performance.py -v
```

### Manual GPU memory profiling

For VRAM leak investigation on GPU hardware:

```bash
# Monitor GPU memory during extraction
watch -n 1 nvidia-smi

# Run extraction in a separate terminal
uv run python -c "
import asyncio
from commands.source_commands import _run_dual_provider_extraction
asyncio.run(_run_dual_provider_extraction('source:test', '/path/to/doc.pdf'))
"
```

## 5. Regression Threshold

The CI regression test (`tests/test_v3_performance.py`) does not enforce
wall-clock thresholds. A 5% increase in production timing between releases
should trigger a manual review using the benchmark instructions above.

### Acceptance Criteria Targets

| AC | Target | Verification |
|----|--------|-------------|
| AC1 | Broadmeadows < 120 s | Manual measurement on GPU hardware |
| AC2 | Alexander < 300 s | Manual measurement on GPU hardware |
| AC3 | Sequential + GPU flush | Automated test: `TestGpuCacheFlush` |
| AC4 | No memory leaks | Automated test: `TestMemoryLeakGuard` + `TestCleanupCalled` |
| AC5 | Top-3 bottlenecks documented | This report (sections 2-3) |
| AC6 | CI regression test | `tests/test_v3_performance.py` (13 tests) |
