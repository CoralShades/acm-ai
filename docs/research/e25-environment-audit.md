# E25 Environment Audit

**Date**: 2026-02-27 (final verification)
**OS**: Windows 11 Home 10.0.26200
**Python (venv)**: 3.12.9 (`.venv/Scripts/python.exe` — used by `uv run`)
**GPU**: NVIDIA GeForce RTX 4090, 24564 MiB VRAM, Driver 581.29, CUDA 13.0
**Agent**: Mary (BA)

## Package Status

| Package | Status | Version | Notes |
|---------|--------|---------|-------|
| torch | OK | 2.10.0+cu126 | CUDA=True, cuda_version=12.6, GPU=RTX 4090 |
| torchvision | OK | 0.25.0+cu126 | |
| PyMuPDF | OK | 1.26.6 | Broadmeadows: 19 pages |
| Docling Direct API | OK | 2.75.0 | `DocumentConverter` + `PipelineOptions` import OK |
| TableFormerMode | OK | N/A | `TableFormerMode.ACCURATE` available |
| docling-core | OK | 2.66.0 | |
| docling-ibm-models | OK | 3.11.0 | |
| docling-parse | OK | 5.4.0 | |
| content-core | OK | 1.8.0 | E24 showed its markdown serializer destroys TableFormer output — bypassed by Direct API |
| pandas | OK | 2.3.3 | Needed for `table.export_to_dataframe()` |
| tabulate | OK | 0.9.0 | Needed for `df.to_markdown()` |
| magic-pdf | Skipped | 1.3.12 (in .venv-mineru) | Available but not used — MinerU skipped for E25 |
| paddlepaddle | Skipped | N/A | Not needed — MinerU skipped |

## GPU Details

```
NVIDIA-SMI 581.29    Driver Version: 581.29    CUDA Version: 13.0
GPU: NVIDIA GeForce RTX 4090 (WDDM)
Memory: 24564 MiB total
```

GPU accessible from venv: `torch.cuda.is_available()=True`, `torch.cuda.get_device_name(0)='NVIDIA GeForce RTX 4090'`.

## Broadmeadows PDF

- **Path**: `docs/samplePDF/Clutch_Broadmeadows.pdf` (exists)
- **Pages**: 19
- **Ground truth**: `docs/samplePDF/Clutch_Broadmeadows.csv` (31 records)

## Docling Functional Test Results

**Test**: `converter.convert('docs/samplePDF/Clutch_Broadmeadows.pdf')` with `TableFormerMode.ACCURATE`

| Metric | Result |
|--------|--------|
| Conversion time | 14.9s (GPU-accelerated, RTX 4090) |
| Tables extracted | 8 |
| Total rows across all tables | 67 |
| ACM register tables | 3 (pages 5, 6, 7 — 10 rows x 18-19 cols each) |
| Sample analysis tables | 2 (pages 11, 12) |
| Row coherence | Preserved — each row contains all fields |
| ACM indicators found | `same as`, `34511`, `negative`, `positive` |

### Key Tables

| Table | Page | Size | Content | ACM Data |
|-------|------|------|---------|----------|
| 0 | 2 | 10x3 | Table of contents | No |
| 1 | 4 | 5x2 | Priority risk key | No |
| **2** | **5** | **10x18** | **Ground floor ACM register** | **34511-039-001 to -005, Negative/Positive/Assumed positive** |
| **3** | **6** | **10x18** | **First floor ACM register** | **34511-039-006 to -008, Same as references** |
| **4** | **7** | **10x19** | **External ACM register** | **Same as 34511-039-007, 34511-039-012 to -017** |
| 5 | 11 | 12x6 | NATA sample analysis | Sample numbers |
| 6 | 12 | 5x7 | NATA sample analysis | Sample numbers |
| 7 | 13 | 5x4 | Site information | No |

### Approach A Viability: CONFIRMED

The Direct API bypasses content-core entirely. Row-major structure is preserved: each row contains `Room`, `Feature`, `Item Description`, `Hazard Status`, `Sample Number`, and all other fields together. This is fundamentally different from E24's content-core cell fragmentation.

### Remaining Challenges (for E25-S2 spike work)

1. **Multi-level headers**: Merged column headers produce compound names (e.g. `'Site Address: Broadmeadows Police Station.Sample Number'`). Parser must normalize.
2. **Split sample numbers**: Line breaks within cells produce `'34511-039- 001'` — needs string join.
3. **Date cell duplication**: Some merged date/reinspect cells produce a Series object instead of a scalar — needs `iloc[0]` or similar extraction.
4. **`export_to_html()` deprecation**: Must pass `doc=doc` argument (warning only, does not affect DataFrame export).

## MinerU Decision

**Skipped** — Docling Direct API functional test results are strong enough for a 2-way comparison (PyMuPDF vs Docling Direct API). MinerU requires paddlepaddle-gpu, potential torch conflicts, and fresh spike code since E24-S3 deleted all MinerU production code. A `.venv-mineru` exists with magic-pdf 1.3.12 from prior setup but will not be used in E25.

## Installation Steps Taken

No new installations required. All tools were already present from prior session:

1. `docling>=2.75.0` — added to `pyproject.toml` in prior session
2. `torch>=2.10.0` + `torchvision>=0.25.0` — added to `pyproject.toml` with CUDA index
3. `pandas` 2.3.3 and `tabulate` 0.9.0 — transitive dependencies, already installed
4. `magic-pdf` removed from `pyproject.toml` (dead dependency cleanup from E24-S3)
5. Orphaned `torch-2.10.0.dist-info` deleted in prior session (fixed `uv run` overhead)

## Verification Script

Full verification script at `scripts/research/e25_verify_tools.py`:
- Checks 7 required tools + 1 optional (MinerU)
- Runs Docling functional test on Broadmeadows PDF
- Reports ACM indicator detection
- Exit code 0 = ready, 1 = not ready

## Ready Status

- [x] PyMuPDF: functional (1.26.6, 19 pages from Broadmeadows)
- [x] Docling Direct API: importable (2.75.0)
- [x] TableFormer mode: available (`ACCURATE`)
- [x] TableFormer weights: cached (loads in <1s, conversion in ~15s)
- [x] GPU: CUDA available — torch 2.10.0+cu126 on RTX 4090
- [x] pandas + tabulate: installed (2.3.3 / 0.9.0)
- [x] Functional test: 8 tables from Broadmeadows in 14.9s, ACM register data confirmed
- [x] MinerU: skipped (available in .venv-mineru but not needed)

---

**Overall: READY for E25-S2 (Research Spike Execution)**

All 7 required checks passed. Approach A (PyMuPDF + Docling Direct API) is confirmed viable. The Direct API returns row-coherent DataFrames with ACM register data intact, bypassing content-core's broken serialization.
