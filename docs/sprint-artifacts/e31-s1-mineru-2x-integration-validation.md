# E31-S1: MinerU 2.x Integration + Validation

| Field | Value |
|-------|-------|
| Story ID | E31-S1 |
| Epic | E31 — Multi-Provider Extraction |
| Sprint | V3-3 |
| Story Points | 2 |
| Risk | MEDIUM |
| Type | backend |

## Objective

Validate that MinerU 2.x can be installed directly into the main `.venv/` alongside Docling and PyTorch, run it against both test PDFs, and document extraction quality, VRAM usage, and processing speed to inform whether to promote MinerU 2.x as a first-class extraction backend.

## Background

MinerU 1.x (`magic-pdf`) required `paddlepaddle-gpu` which conflicted with PyTorch in the main venv. This forced an isolated `.venv-mineru/` venv with a subprocess bridge (`scripts/mineru_runner.py`). MinerU 2.x has replaced PaddlePaddle with `paddleocr2torch` — a PyTorch-native OCR backend — eliminating the venv conflict entirely.

Key MinerU 2.x changes:
- Install target: `mineru[all]` (replaces `magic-pdf`)
- Import: `from mineru import MinerUDocumentConverter` (new API)
- Default backend: hybrid pipeline + VLM auto-routing (since v2.7.0)
- Cross-page table stitching: built-in
- VRAM requirement: ~6–10 GB (RTX 4090 has 24 GB — ample)
- Processing speed: ~10–14s for a 20-page PDF (estimated)
- No subprocess bridge required — direct import from main venv

The old two-venv pattern is OBSOLETE if MinerU 2.x installs cleanly. This story validates that assumption and measures quality on the project's canonical test PDFs before committing to a full adapter implementation in subsequent stories.

## Acceptance Criteria Mapping

| AC | Description | Implementation Approach |
|----|-------------|------------------------|
| AC1 | `pip install mineru[all]` in main `.venv/` — no dependency conflicts | Add `mineru[all]` to `pyproject.toml` dependencies; run `uv sync`; verify no torch/torchvision/langchain conflicts |
| AC2 | Verify hybrid backend (pipeline + VLM auto-routing) is default | Import `MinerUDocumentConverter`; check default config; assert backend mode in validation script output |
| AC3 | Verify CUDA 12.6 compatibility | Validation script checks `torch.cuda.is_available()` and reports CUDA version; run `paddleocr2torch` on a small sample |
| AC4 | Run MinerU on Broadmeadows PDF — capture HTML output, compare to Docling DataFrames | Validation script converts `docs/samplePDF/Clutch_Broadmeadows.pdf`; outputs HTML tables and row counts; side-by-side comparison with Docling |
| AC5 | Run MinerU on Alexander PDF — capture output, note cross-page stitching | Validation script converts `docs/samplePDF/Clucth_Alexander_District_Hospital.pdf`; cross-page tables noted in output |
| AC6 | Docling regression check: existing Docling extraction still works after MinerU install | Validation script re-runs `check_docling_functional()` from `e25_verify_tools.py` pattern; asserts same table counts |
| AC7 | Document chosen backend, VRAM usage, processing speed per document | Validation script captures wall-clock time and `torch.cuda.memory_allocated()` delta per conversion; writes summary JSON |
| AC8 | Fallback plan documented if torch constraint is hard | Section in tech spec and validation script output if install fails |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Modified | Add `mineru[all]` to `[project.dependencies]` |
| `scripts/research/validate_mineru_v2.py` | New | Validation script — primary deliverable of this story |
| `CLAUDE.md` | Modified | Update Two-Venv Pattern section to reflect MinerU 2.x in main venv |

## Implementation Steps

1. **Check for dependency conflicts (offline analysis)**
   - Review MinerU 2.x PyPI metadata for `paddleocr2torch`, `torch`, `torchvision` version requirements
   - Confirm no conflict with `torch>=2.10.0` (cu126) and `docling>=2.75.0` already in `pyproject.toml`
   - If conflict detected → document and go to AC8 fallback path

2. **Add `mineru[all]` to `pyproject.toml`**
   - Add to `[project.dependencies]` list: `"mineru[all]>=2.7.0"`
   - Run `uv sync` to resolve and install
   - If `uv sync` fails with a version conflict, attempt `mineru>=2.7.0` (without `[all]`) and note which optional extras were excluded

3. **Create validation script `scripts/research/validate_mineru_v2.py`**
   - Follow the same check-function pattern as `scripts/research/e25_verify_tools.py`
   - Include these checks (in order):
     1. `check_python()` — Python version
     2. `check_gpu()` — torch + CUDA version + device name
     3. `check_mineru_import()` — `from mineru import MinerUDocumentConverter`; print version
     4. `check_mineru_backend()` — confirm hybrid backend is default (pipeline + VLM)
     5. `check_cuda_compat()` — run a small paddleocr2torch op; assert no CUDA errors
     6. `check_broadmeadows()` — convert Broadmeadows PDF; capture tables as HTML; compare row counts to Docling baseline; log VRAM delta and wall-clock time
     7. `check_alexander()` — convert Alexander PDF; capture tables; note cross-page stitching (table count pre/post stitching); log VRAM delta and wall-clock time
     8. `check_docling_regression()` — run Docling on Broadmeadows; assert table count matches pre-install baseline (31 ACM records expected)
   - Write summary JSON to `scripts/research/e31_s1_validation_results.json`
   - Exit code 0 = all required checks pass; exit code 1 = any required check failed

4. **Run the validation script**
   ```bash
   uv run python scripts/research/validate_mineru_v2.py
   ```
   - Capture console output and summary JSON as evidence

5. **Update `CLAUDE.md`**
   - Replace the "Two-Venv Pattern (MinerU)" section to reflect that MinerU 2.x installs in the main venv
   - Mark `.venv-mineru/` and `scripts/mineru_runner.py` as legacy/deprecated
   - Update the Venv Summary table and Interpreter Paths table

6. **Document findings in the Dev Agent Record**
   - Chosen backend (hybrid vs pipeline-only vs VLM-only)
   - VRAM usage: baseline, peak during Broadmeadows, peak during Alexander
   - Processing speed: seconds per document for each PDF
   - Cross-page stitching: confirmed or not, table count before/after
   - Any noted quality differences vs Docling output

## Verification

| AC | Verification Command / Check |
|----|------------------------------|
| AC1 | `uv sync` exits 0; `uv run python -c "import mineru; print(mineru.__version__)"` prints a 2.x version |
| AC2 | Validation script `check_mineru_backend()` prints `PASS` with backend mode reported |
| AC3 | Validation script `check_cuda_compat()` prints `PASS`; no CUDA version errors in output |
| AC4 | Validation script `check_broadmeadows()` prints `PASS`; `e31_s1_validation_results.json` contains Broadmeadows table HTML and row counts |
| AC5 | Validation script `check_alexander()` prints `PASS`; results JSON contains Alexander cross-page stitching note |
| AC6 | Validation script `check_docling_regression()` prints `PASS`; Docling still returns expected table counts |
| AC7 | Results JSON contains `vram_mb`, `elapsed_s`, `backend` fields for each document |
| AC8 | If install fails: fallback section in validation script output + updated notes in this spec under Risks |

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `mineru[all]` conflicts with `torch>=2.10.0+cu126` | Low | High | Try `mineru>=2.7.0` without `[all]` extras; or pin `paddleocr2torch` to a compatible version; or keep isolated venv pattern |
| MinerU 2.x API differs from research docs (import path changed) | Medium | Low | Check `mineru` PyPI page and changelog at install time; adapt import in validation script |
| VRAM exhaustion during parallel Docling + MinerU on same run | Low | Medium | Run MinerU and Docling sequentially in validation script; clear CUDA cache between runs with `torch.cuda.empty_cache()` |
| MinerU model weights download on first run (slow) | Medium | Low | Validation script notes first-run vs cached-run time; acceptable for a spike |
| Cross-page stitching not working on Alexander PDF | Medium | Medium | Note in results; does not block story completion — this is a spike/observation |

### AC8 Fallback Plan

If `mineru[all]` cannot coexist in the main venv due to a hard torch constraint:

1. **Option A**: Keep `.venv-mineru/` isolated venv but upgrade it to MinerU 2.x (`pip install mineru[all]` in `.venv-mineru/`). Update `scripts/mineru_runner.py` to use the new MinerU 2.x API. Subprocess bridge remains the integration pattern.

2. **Option B**: Use MinerU 2.x in a Docker sidecar service — expose as an HTTP endpoint. Main backend calls the sidecar. Eliminates venv conflict entirely.

3. **Option C**: Defer MinerU 2.x — continue with Docling as the sole extraction backend. Document the conflict for future resolution.

Document the chosen fallback option in the Dev Agent Record if reached.

## Dependencies

- GATE:SCHEMA_FREEZE (unlocked)
- PyTorch cu126 already installed via `pyproject.toml` — MinerU 2.x must be compatible
- Test PDFs present at:
  - `docs/samplePDF/Clutch_Broadmeadows.pdf` (Broadmeadows — 31 ACM records)
  - `docs/samplePDF/Clucth_Alexander_District_Hospital.pdf` (Alexander — cross-page table test)

## Dev Agent Notes

### This is a SPIKE story

The primary deliverable is `scripts/research/validate_mineru_v2.py` and its output. Do NOT implement a production MinerU adapter or modify `open_notebook/extractors/`. That is future work gated on AC1–AC7 passing.

### Script structure

Model the validation script on `scripts/research/e25_verify_tools.py`:
- Each check is a separate function returning `(status, label, detail, required)`
- Status values: `PASS`, `WARN`, `FAIL`, `SKIP`
- Print a formatted summary table at the end
- Exit 0 if all required checks pass

### PDF paths

Use absolute paths resolved from `PROJECT_ROOT`:
```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BROADMEADOWS_PDF = PROJECT_ROOT / "docs" / "samplePDF" / "Clutch_Broadmeadows.pdf"
ALEXANDER_PDF = PROJECT_ROOT / "docs" / "samplePDF" / "Clucth_Alexander_District_Hospital.pdf"
```

Note the typo in the Alexander filename (`Clucth` not `Clutch`) — this is the actual filename on disk.

### VRAM measurement pattern

```python
import torch

torch.cuda.reset_peak_memory_stats()
torch.cuda.empty_cache()
before = torch.cuda.memory_allocated()

# ... run conversion ...

after = torch.cuda.memory_allocated()
peak = torch.cuda.max_memory_allocated()
vram_delta_mb = (peak - before) / 1024 / 1024
```

### MinerU 2.x import to attempt

```python
from mineru import MinerUDocumentConverter
```

If this import fails, also try:
```python
from mineru.document_converter import MinerUDocumentConverter
```

Log the exact import path that works in the results JSON under `mineru_import_path`.

### CLAUDE.md update scope

Update only the "Two-Venv Pattern (MinerU)" section and the Venv Summary/Interpreter Paths tables. Do not change any other sections. Mark `.venv-mineru/` as "(deprecated if MinerU 2.x confirmed in main venv)" and `scripts/mineru_runner.py` as "(legacy bridge — deprecated)".

### Output JSON schema

```json
{
  "mineru_version": "2.x.x",
  "mineru_import_path": "mineru.MinerUDocumentConverter",
  "backend_mode": "hybrid",
  "cuda_version": "12.6",
  "torch_version": "2.10.0+cu126",
  "documents": {
    "broadmeadows": {
      "elapsed_s": 12.3,
      "vram_peak_mb": 7200,
      "table_count_mineru": 5,
      "table_count_docling_baseline": 5,
      "row_count_total": 45
    },
    "alexander": {
      "elapsed_s": 15.1,
      "vram_peak_mb": 8100,
      "table_count_before_stitch": 8,
      "table_count_after_stitch": 4,
      "cross_page_stitching_confirmed": true
    }
  },
  "docling_regression": {
    "table_count_post_install": 5,
    "regression_detected": false
  },
  "overall_status": "PASS"
}
```
