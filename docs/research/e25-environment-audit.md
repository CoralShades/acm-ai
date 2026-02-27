# E25 Environment Audit

**Date**: 2026-02-27 (re-audited)
**OS**: Windows 11 Home 10.0.26200
**Python (system)**: 3.12.10 (`C:\Program Files\Python312\python`)
**Python (venv)**: 3.12.x (`.venv/Scripts/python.exe` — used by `uv run`)
**GPU**: NVIDIA GeForce RTX 4090, 24564 MiB VRAM, Driver 581.29, CUDA 13.0

## Package Status

| Package | Status | Version | Notes |
|---------|--------|---------|-------|
| Python (venv) | ✅ | 3.12.9 | Used by `uv run` |
| torch | ✅ | 2.10.0+cu126 | CUDA=True, cuda_version=12.6, GPU=RTX 4090 |
| torchvision | ✅ | 0.25.0+cu126 | |
| PyMuPDF | ✅ | 1.26.6 | `fitz.version=('1.26.6', '1.26.11', None)` |
| Docling Direct API | ✅ | 2.75.0 | `DocumentConverter` + `PipelineOptions` import OK |
| TableFormerMode | ✅ | N/A | `TableFormerMode.ACCURATE` available |
| docling-core | ✅ | 2.66.0 | |
| docling-ibm-models | ✅ | 3.11.0 | |
| docling-parse | ✅ | 5.4.0 | |
| content-core | ✅ | 1.8.0 | E24 showed its markdown serializer destroys TableFormer output |
| magic-pdf | ⚠️ stale | 1.0.1 | Installed but MinerU code deleted in E24-S3 |
| paddlepaddle | ❌ expected | N/A | Not installed (never was) |
| pandas | ✅ | 2.3.3 | Needed for DataFrame export |
| tabulate | ✅ | 0.9.0 | Needed for `df.to_markdown()` |

## GPU Details

```
NVIDIA-SMI 581.29    Driver Version: 581.29    CUDA Version: 13.0
GPU: NVIDIA GeForce RTX 4090 (WDDM)
Memory: 4210MiB / 24564MiB (17% used)
Temp: 42C, Power: 18W/450W, Util: 2%
```

GPU is accessible from the venv: `torch.cuda.is_available()=True`, `torch.cuda.get_device_name(0)='NVIDIA GeForce RTX 4090'`.

## Broadmeadows PDF

- **Path**: `docs/samplePDF/Clutch_Broadmeadows.pdf` ✅ (1,829,326 bytes)
- **Pages**: 19
- **Total chars**: 34,056 (PyMuPDF text extraction)
- **Ground truth**: `docs/samplePDF/Clutch_Broadmeadows.csv` ✅ (13,240 bytes, 31 records)

## Dependency Changes Made

### pyproject.toml updates

1. **Added `[tool.uv]` CUDA index** — PyTorch cu126 index configured so `uv sync` always installs GPU torch
2. **Added `torch>=2.10.0` as direct dependency** — was previously transitive-only, sources required explicit listing
3. **Added `torchvision>=0.25.0` as direct dependency** — same reason
4. **Added `docling>=2.75.0` as direct dependency** — was previously installed manually, `uv sync` would remove it

### Stale dependency (not yet removed)

| File | Line | Reference | Action Needed |
|------|------|-----------|---------------|
| `pyproject.toml` | 32 | `"magic-pdf>=0.7.0"` | Remove — MinerU code deleted in E24-S3 (commit `6e0e2e8`) |

## Ready Status

- [x] PyMuPDF: functional (1.26.6)
- [x] Docling Direct API: importable (2.75.0)
- [x] TableFormer mode: available (`ACCURATE`)
- [x] TableFormer weights: cached (~/.cache/docling/models/, loads in 6.9s)
- [x] GPU: CUDA available — torch 2.10.0+cu126 on RTX 4090
- [x] Broadmeadows PDF: accessible (19 pages, 34,056 chars)
- [x] pandas + tabulate: installed (2.3.3 / 0.9.0)
- [x] Functional test: 8 tables from Broadmeadows in 25.5s, ACM register data confirmed
- [x] torch dist-info corruption: FIXED (deleted orphaned torch-2.10.0.dist-info)

---

**Overall: READY — Approach A CONFIRMED VIABLE**

All blockers resolved. Docling Direct API functional test passed. `table.export_to_dataframe(doc=doc)`
returns row-coherent DataFrames with ACM register data intact. `uv sync` (and therefore `start-all.bat`)
maintains this state automatically via the `[[tool.uv.index]]` configuration in pyproject.toml.

## Docling Direct API Functional Test Results (2026-02-27)

**Test**: `converter.convert('docs/samplePDF/Clutch_Broadmeadows.pdf')` with `TableFormerMode.ACCURATE`

| Metric | Result |
|--------|--------|
| Conversion time | 25.5s (GPU-accelerated, RTX 4090) |
| Tables extracted | 8 |
| ACM register tables | 3 (pages 5, 6, 7 — 10 rows × 18-19 cols each) |
| Sample analysis tables | 2 (pages 11, 12) |
| Row coherence | ✅ Preserved — each row contains all fields |
| ACM indicators found | `same as`, `negative`, `positive`, `34511` |

### Key Tables

- **Table 2 (page 5)**: Ground floor ACM register — 10 rows × 18 cols. NATA numbers `34511-039-001` through `34511-039-005`. Contains `Asbestos Negative`, `Asbestos Positive`, and `Assumed positive` entries.
- **Table 3 (page 6)**: First floor ACM register — 10 rows × 18 cols. `Same as` references preserved (e.g. `Same as 34511-039-007`).
- **Table 4 (page 7)**: External ACM register — 10 rows × 19 cols. Contains `Same as` references and `Assumed positive` entries.

### Approach A Viability: CONFIRMED ✅

The Direct API bypasses content-core entirely. Row-major structure is preserved: each row contains `Room`, `Feature`, `Item Description`, `Hazard Status`, `Sample Number`, and all other fields together. This is fundamentally different from E24's content-core cell fragmentation.

### Remaining Challenges (for E25 spike work)

1. **Multi-level headers**: Merged column headers produce compound names (e.g. `'Site Address: Broadmeadows Police Station.Sample Number'`). Parser must normalize.
2. **Split sample numbers**: Line breaks within cells produce `'34511-039-\n001'` — needs string join.
3. **Date cell duplication**: Some merged date/reinspect cells produce a Series object instead of a scalar — needs `iloc[0]` or similar extraction.
4. **`export_to_html()` deprecation**: Must pass `doc=doc` argument (warning only, does not affect DataFrame export).

## Known Issues (re-audit 2026-02-27)

1. **torch dist-info corruption** — **FIXED 2026-02-27**: The orphaned `torch-2.10.0.dist-info`
   directory was deleted. `uv run` no longer triggers the 6s reinstall overhead.

2. **System Python vs venv**: Bare `python` resolves to system Python (`C:\Program Files\Python312\python`).
   All project commands must use `uv run python` or activate the venv explicitly.

### Pre-Setup Recommendations

1. ~~Delete orphaned `torch-2.10.0.dist-info`~~ — **Done 2026-02-27**
2. Remove `magic-pdf>=0.7.0` from `pyproject.toml` line 32 (dead dependency)
3. Consider removing `content-core` after E25 confirms Direct API works (not urgent)
