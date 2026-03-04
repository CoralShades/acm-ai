# E25: Table Extraction Research Spike — Environment Setup Plan

**Date**: 2026-02-27
**Epic**: E25 — Table Extraction Comparative Analysis
**Depends on**: E24 (complete — TableFormer activated, MinerU removed, 17/31 regression documented)
**Goal**: Get Docling Direct API working locally, verify PyMuPDF baseline, optionally set up MinerU, then run controlled comparison on Broadmeadows PDF.

---

## 1. EXECUTIVE SUMMARY

E24 proved that content-core's markdown serializer destroys TableFormer's table output (17/31 regression from 28/31). The **key insight** for E25 is that Docling's Direct Python API (`table.export_to_dataframe()`) **bypasses content-core entirely**, giving native Pandas DataFrames with perfect row/column structure.

This plan covers **Steps 1–3 only**: problem understanding, approach definition, and environment setup. The actual research spike execution (Step 4+) happens in the next session.

### What Changed Since E24

| Item | E24 State | E25 State |
|------|-----------|-----------|
| MinerU code | Existed (dead) | **Deleted** in E24-S3 (commit `6e0e2e8`, 2,298 lines removed) |
| `magic-pdf` in pyproject.toml | Present (`>=0.7.0`) | **May still be listed** — needs audit |
| `mineru_table_extractor.py` | 557 lines | **Deleted** |
| TableFormer flag | Created (E24-S1) | Exists: `DOCLING_TABLE_STRUCTURE=false` (default) |
| Docling Direct API | Never tested | **Target of this spike** |
| PyMuPDF baseline | 28-29/31 | Unchanged — still production engine |

---

## 2. THE REAL PROBLEM (Why E24 Failed)

TableFormer **did NOT fail at table detection**. The E24 validation report (`docs/reviews/e24-validation-results.md`) reveals:

- TableFormer correctly identified cell boundaries, merged cells, and table structure
- **content-core's markdown serializer** fragmented table rows into individual cell values on separate lines
- "Same as" references and "Not Sampled" rows became isolated lines without context
- All 9 "As Per" rows and all 6 "Not Sampled" rows were lost (0/9 and 0/6)

**The fix is NOT "better TableFormer config"** — it's **bypassing content-core's serialization** and using Docling's Direct Python API:

```python
# INSTEAD OF: content-core → markdown (broken)
# USE: DocumentConverter → table.export_to_dataframe() → DataFrame (correct)

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

result = converter.convert("path/to/pdf")
for table in result.document.tables:
    df = table.export_to_dataframe(doc=result.document)  # ← Perfect DataFrame
    html = table.export_to_html()                         # ← HTML with colspan/rowspan
    md = df.to_markdown(index=False)                      # ← Clean row-coherent markdown
```

---

## 3. THREE APPROACHES TO COMPARE

### Approach A: Hybrid PyMuPDF + Docling Direct API (RECOMMENDED)

```
PDF ──→ PyMuPDF ──→ source.full_text (proven 28-29/31 with page markers)
  │
  └──→ Docling Direct API ──→ DataFrames per table
                                  ├── df.to_markdown() → clean table markdown
                                  ├── df.to_html() → HTML with structure
                                  └── Store in acm_table_section
```

**Why favorite**: PyMuPDF gives proven reading-order text with page markers. Docling Direct API gives structured tables bypassing the content-core bug. No new dependencies.

### Approach B: Hybrid PyMuPDF + MinerU HTML Tables

```
PDF ──→ PyMuPDF ──→ source.full_text (proven)
  │
  └──→ MinerU (magic-pdf) ──→ HTML tables with colspan/rowspan
```

**Key blocker**: Needs `paddlepaddle-gpu` installed. MinerU code was deleted in E24-S3. Would need re-installation and new spike-only extractor code.

### Approach C: Pure Docling Direct API (Replace content-core entirely)

```
PDF ──→ Docling DocumentConverter (with TableFormer)
         ├── .tables → DataFrames
         ├── .export_to_markdown() → full text
         └── page-level provenance
```

**Risk**: Must handle page markers ourselves. The markdown export was E24's failure point — but with DataFrames extracted separately, markdown only needs non-table text.

---

## 4. ENVIRONMENT SETUP — STEP-BY-STEP

### Runtime Context

- **OS**: Windows (PowerShell primary, WSL2 available)
- **Python**: Runs directly on Windows (not in Docker)
- **Docker**: Ollama + SurrealDB containers
- **GPU**: NVIDIA (local, available to Windows Python and Docker)
- **Package manager**: `uv` (primary), `pip` (fallback)

### Step 3A: Pre-Flight Checks

Run these FIRST to establish baseline:

```powershell
# PowerShell — Check GPU and CUDA
nvidia-smi

# Check Python version (must be 3.10-3.12)
python --version

# Check torch + CUDA
python -c "import torch; print(f'torch={torch.__version__}, cuda={torch.cuda.is_available()}, version={torch.version.cuda}')"

# Check PyMuPDF (should work — production engine)
python -c "import fitz; print(f'PyMuPDF={fitz.version}')"

# Check if Docling Direct API is importable (bypassing content-core)
python -c "from docling.document_converter import DocumentConverter; print('Docling Direct API: OK')" 2>&1

# Check magic-pdf status (may be importable even though code was deleted)
python -c "import magic_pdf; print(f'magic-pdf={magic_pdf.__version__}')" 2>&1

# Check paddle status (expected: NOT installed)
python -c "import paddle; print(f'paddle={paddle.__version__}')" 2>&1

# List relevant installed packages
uv pip list | Select-String -Pattern "torch|docling|magic|paddle|fitz|pymupdf|content-core"
```

**Expected results:**
- ✅ torch 2.10.0 with CUDA
- ✅ PyMuPDF working
- ⚠️ Docling: may or may not import directly (depends on content-core's installation)
- ⚠️ magic-pdf: may still be installed even though code was deleted
- ❌ paddle: NOT installed

### Step 3B: Tool 1 — PyMuPDF (Already Working)

No setup needed. Just verify:

```powershell
python -c "
import fitz
print(f'PyMuPDF version: {fitz.version}')
print(f'PyMuPDF VersionBind: {fitz.VersionBind}')

# Quick functional test on Broadmeadows
doc = fitz.open('docs/samplePDF/Clutch_Broadmeadows.pdf')
print(f'Pages: {len(doc)}')
text = doc[0].get_text('text')
print(f'Page 1 chars: {len(text)}')
doc.close()
print('✅ PyMuPDF functional')
"
```

### Step 3C: Tool 2 — Docling Direct API

This is the **critical setup step**. We need Docling's `DocumentConverter` importable directly, NOT through content-core.

**Test 1: Check if already importable**

```powershell
python -c "
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import PdfFormatOption
print('✅ All Docling Direct API imports successful')
print(f'   InputFormat.PDF = {InputFormat.PDF}')
print(f'   TableFormerMode.ACCURATE = {TableFormerMode.ACCURATE}')
"
```

**If imports fail — install Docling directly:**

```powershell
# Preferred: Add alongside existing deps
uv pip install docling pandas tabulate --break-system-packages

# Or if uv has issues:
pip install docling pandas tabulate
```

**Test 2: Pre-download TableFormer model weights (~500MB)**

```powershell
python -c "
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
pipeline_options.table_structure_options.do_cell_matching = True

# This triggers model download on first run
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
print('✅ TableFormer model weights downloaded and cached')
print(f'   Cache location: ~/.cache/docling/models/')
"
```

**Test 3: Quick functional test on Broadmeadows (THE KEY TEST)**

```powershell
python -c "
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
pipeline_options.table_structure_options.do_cell_matching = True

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

result = converter.convert('docs/samplePDF/Clutch_Broadmeadows.pdf')
doc = result.document

print(f'Tables found: {len(doc.tables)}')
for i, table in enumerate(doc.tables):
    try:
        df = table.export_to_dataframe(doc=doc)
        page = table.prov[0].page_no if table.prov else -1
        print(f'  Table {i}: Page {page}, {len(df)} rows × {len(df.columns)} cols')
        print(f'    Columns: {list(df.columns)[:5]}...')
        if len(df) > 0:
            print(f'    First row: {df.iloc[0].to_dict()}')
    except Exception as e:
        print(f'  Table {i}: ERROR — {e}')

print('✅ Docling Direct API functional — DataFrames extracted')
"
```

### Step 3D: Tool 3 — MinerU (OPTIONAL — Requires Decision)

> **Decision point for Demi**: MinerU code was deleted in E24-S3. Re-enabling it requires:
> 1. Installing `paddlepaddle-gpu` from Paddle's custom index (~1-2GB download)
> 2. Upgrading `magic-pdf` to >=1.3.0
> 3. Writing a NEW spike-only extraction script (old code is gone)
> 4. Potential torch/paddle CUDA conflicts

**If YES — proceed with MinerU setup:**

```powershell
# Step 1: Determine CUDA version
nvidia-smi  # Look for "CUDA Version: 12.x"

# Step 2: Install paddlepaddle-gpu
# For CUDA 12.x (most common with recent drivers):
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# Step 3: Verify paddle
python -c "
import paddle
print(f'PaddlePaddle: {paddle.__version__}')
paddle.utils.run_check()
print(f'CUDA: {paddle.device.is_compiled_with_cuda()}')
"

# Step 4: Upgrade magic-pdf
uv pip install 'magic-pdf[full]>=1.3.0' --break-system-packages

# Step 5: Verify MinerU
python -c "
import magic_pdf
print(f'MinerU/magic-pdf: {magic_pdf.__version__}')
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
print('✅ MinerU imports successful')
"

# Step 6: Verify torch still works after paddle install
python -c "
import torch
t = torch.randn(3,3).cuda()
print(f'torch GPU: OK ({t.sum().item():.2f})')
import paddle
print(f'paddle: OK')
print('✅ Both torch and paddle coexist')
"
```

**If torch/paddle conflict:**
- Option A: `pip install paddlepaddle==3.2.0` (CPU-only paddle)
- Option B: Separate venv: `python -m venv .venv-mineru && .venv-mineru\Scripts\activate`
- Option C: Skip MinerU — focus on Docling Direct API

**If NO — skip MinerU:**

Document the decision and focus on Approach A (PyMuPDF + Docling Direct API) and Approach C (Pure Docling). MinerU can always be revisited in a future spike.

### Step 3E: Dependency Conflict Resolution

**Known risks:**
- `nvidia-cudnn-cu12` version mismatch between torch and paddle
- `nvidia-nccl-cu12` version mismatch

**Resolution test (run after all installs):**

```powershell
python -c "
import sys
print(f'Python: {sys.version}')

# GPU baseline
import torch
print(f'torch: {torch.__version__}, CUDA: {torch.cuda.is_available()}, device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')

# PyMuPDF
import fitz
print(f'PyMuPDF: {fitz.version}')

# Docling Direct API
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import TableFormerMode
print(f'Docling Direct API: OK')

# Paddle (if installed)
try:
    import paddle
    print(f'PaddlePaddle: {paddle.__version__}, GPU: {paddle.device.is_compiled_with_cuda()}')
except ImportError:
    print('PaddlePaddle: NOT INSTALLED (MinerU unavailable)')

# MinerU (if installed)
try:
    import magic_pdf
    print(f'magic-pdf: {magic_pdf.__version__}')
except ImportError:
    print('magic-pdf: NOT INSTALLED')

print('\\n✅ All available tools verified')
"
```

### Step 3F: Docker Setup (Optional — For Isolated MinerU Testing)

Only needed if torch/paddle conflict on host, or if Demi wants containerized spike:

```dockerfile
# File: Dockerfile.e25-research
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PyMuPDF
RUN pip install PyMuPDF

# Docling with TableFormer
RUN pip install docling pandas tabulate

# torch GPU
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126

# PaddlePaddle GPU (optional — comment out to skip MinerU)
# RUN pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# MinerU (optional — comment out to skip)
# RUN pip install "magic-pdf[full]>=1.3.0"

# Pre-download Docling TableFormer weights
RUN python -c "from docling.document_converter import DocumentConverter; \
    from docling.datamodel.base_models import InputFormat; \
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode; \
    from docling.document_converter import PdfFormatOption; \
    opts = PdfPipelineOptions(do_table_structure=True); \
    opts.table_structure_options.mode = TableFormerMode.ACCURATE; \
    DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})"

COPY scripts/research/ /app/scripts/research/
```

```yaml
# docker-compose.e25-research.yml
services:
  e25-research:
    build:
      context: .
      dockerfile: Dockerfile.e25-research
    volumes:
      - ./docs/samplePDF:/data/pdfs:ro
      - ./research-output:/data/output
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: python scripts/research/e25_table_comparison.py /data/pdfs/Clutch_Broadmeadows.pdf /data/output
```

---

## 5. SUCCESS CRITERIA

After environment setup is complete, this verification script must pass:

```powershell
python -c "
results = {}

# Tool 1: PyMuPDF
try:
    import fitz
    fitz.open('docs/samplePDF/Clutch_Broadmeadows.pdf').close()
    results['PyMuPDF'] = True
    print('PyMuPDF ✅')
except Exception as e:
    results['PyMuPDF'] = False
    print(f'PyMuPDF ❌ {e}')

# Tool 2: Docling Direct API
try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    opts = PdfPipelineOptions(do_table_structure=True)
    opts.table_structure_options.mode = TableFormerMode.ACCURATE
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    results['Docling Direct API'] = True
    print('Docling Direct API ✅')
except Exception as e:
    results['Docling Direct API'] = False
    print(f'Docling Direct API ❌ {e}')

# Tool 3: GPU
try:
    import torch
    assert torch.cuda.is_available()
    results['GPU'] = True
    print(f'GPU ✅ ({torch.cuda.get_device_name(0)})')
except Exception as e:
    results['GPU'] = False
    print(f'GPU ❌ {e}')

# Tool 4: MinerU (optional)
try:
    import magic_pdf, paddle
    results['MinerU'] = True
    print(f'MinerU ✅ (magic-pdf {magic_pdf.__version__}, paddle {paddle.__version__})')
except ImportError:
    results['MinerU'] = None
    print('MinerU ⏭️  (skipped — optional)')

required = ['PyMuPDF', 'Docling Direct API', 'GPU']
ready = all(results.get(k) for k in required)
print(f'\\n{\"✅ READY\" if ready else \"❌ NOT READY\"} for research spike ({sum(1 for v in results.values() if v)}/{len(results)} tools)')
"
```

**Minimum required for spike**: PyMuPDF ✅ + Docling Direct API ✅ + GPU ✅
**Optional bonus**: MinerU ✅ (enables 3-way comparison instead of 2-way)

---

## 6. CLAUDE CODE SESSION WORKFLOW

### Session 1: Environment Setup (THIS SESSION)

```
/e25-preflight          → Run pre-flight checks, capture baseline
/e25-setup-docling      → Install/verify Docling Direct API + TableFormer weights
/e25-setup-mineru       → (Optional) Install paddle + upgrade magic-pdf
/e25-verify-all         → Run full verification, generate audit report
```

### Session 2: Research Spike Execution (NEXT SESSION)

```
/e25-run-spike          → Execute 3-way comparison on Broadmeadows PDF
/e25-analyze            → Analyze results, generate comparison report
```

### Session 3: Architecture Decision (AFTER SPIKE)

```
/e25-adr-update         → Update ADR-001 with D5 decision
/e25-tech-design        → Create E26 technical design document
```

---

## 7. KEY FILES REFERENCE

| File | Purpose |
|------|---------|
| `docs/samplePDF/Clutch_Broadmeadows.pdf` | Benchmark PDF (31 ground truth records) |
| `docs/samplePDF/Clutch_Broadmeadows.csv` | Ground truth CSV |
| `docs/reviews/e24-validation-results.md` | Why E24 failed (content-core serialization) |
| `docs/reviews/e23-validation-results.md` | E23 baseline (28/31 with PyMuPDF) |
| `docs/architecture/adr-tableformer-integration.md` | Current ADR (needs D5 update after spike) |
| `docs/architecture/tableformer-technical-design.md` | Current tech design (needs E26 update) |
| `open_notebook/graphs/source.py` | Source processing (TableFormer flag lives here) |
| `pyproject.toml` | Dependencies to audit |

---

## 8. RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Docling Direct API not importable separately from content-core | Medium | High | Install `docling` package directly alongside content-core |
| TableFormer model download fails / slow | Low | Medium | Pre-download in setup step; models cached in `~/.cache/docling/models/` |
| torch/paddle CUDA conflict | Medium | Medium | CPU-only paddle fallback; separate venv; skip MinerU |
| Docling API changes between versions | Low | Medium | Pin docling version; check API against installed version |
| Broadmeadows PDF path wrong | Very Low | Low | Verified: `docs/samplePDF/Clutch_Broadmeadows.pdf` |
| Windows-specific path issues | Low | Low | Use forward slashes or `pathlib.Path` |
