# E25 Prompt 1 — Mary (BA): Environment Verification & Dependency Setup

> **Paste this entire prompt into Claude Code to run the E25 environment setup.**
> **Estimated time**: 10-20 minutes (includes ~500MB model download)

---

You are Mary, the Business Analyst for ACM-AI. Your task is a complete environment
verification and dependency setup for the E25 research spike.

## MANDATORY PRE-READ (Read these files FIRST)

1. `pyproject.toml` — Current dependencies (look for content-core, docling, magic-pdf, torch)
2. `docs/reviews/e24-validation-results.md` — Why E24 failed (content-core serialization)
3. `docs/research/e25-environment-setup-plan.md` — The setup plan (if it exists in docs/research/)
4. `docs/sprint-artifacts/e24-s3-remove-mineru-dead-code.md` — What MinerU code was deleted

## CONTEXT

E24 validation proved content-core's markdown serializer destroys TableFormer's table
structure (17/31 regression from 28/31 baseline). The key finding: **Docling's Direct
Python API** (`table.export_to_dataframe()`) bypasses content-core entirely, giving
native Pandas DataFrames.

We need to set up extraction tools for a head-to-head comparison:
1. **PyMuPDF** — Already working (28-29/31 baseline)
2. **Docling Direct API** — Bypasses content-core, uses DocumentConverter directly
3. **MinerU** — OPTIONAL (code was deleted in E24-S3, needs paddle)

**Environment**: Windows + PowerShell + NVIDIA GPU. Python runs directly (not Docker).
Docker has Ollama + SurrealDB containers.

## PHASE 1: AUDIT (Read-Only)

### Task 1: System & Package Audit

Run each check and capture ALL output:

```bash
python --version
nvidia-smi | head -8

python -c "import torch; print(f'torch={torch.__version__}, cuda={torch.cuda.is_available()}, cuda_version={torch.version.cuda}')"
python -c "import fitz; print(f'PyMuPDF={fitz.version}')"
python -c "from docling.document_converter import DocumentConverter; print('Docling Direct API: OK')" 2>&1
python -c "from docling.datamodel.pipeline_options import TableFormerMode; print(f'TableFormerMode available: {TableFormerMode.ACCURATE}')" 2>&1
python -c "import magic_pdf; print(f'magic-pdf={magic_pdf.__version__}')" 2>&1
python -c "import paddle; print(f'paddle={paddle.__version__}')" 2>&1
python -c "import pandas; print(f'pandas={pandas.__version__}')" 2>&1
python -c "import tabulate; print(f'tabulate={tabulate.__version__}')" 2>&1
```

```bash
# Package listing
uv pip list 2>/dev/null | grep -iE "torch|docling|magic|paddle|fitz|pymupdf|content-core|pandas|tabulate"
```

```bash
# Check for stale MinerU ref in pyproject.toml
grep -n "magic-pdf\|mineru\|paddle" pyproject.toml
```

```bash
# Verify Broadmeadows PDF exists
python -c "
import fitz
doc = fitz.open('docs/samplePDF/Clutch_Broadmeadows.pdf')
print(f'Broadmeadows: {len(doc)} pages')
doc.close()
"
```

## PHASE 2: INSTALL (Fix What's Missing)

Based on Phase 1 results, install what's needed:

### If Docling Direct API import failed:

```bash
uv pip install docling --break-system-packages
```

### If pandas or tabulate missing:

```bash
uv pip install pandas tabulate --break-system-packages
```

### Re-verify after installs:

```bash
python -c "
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
print('✅ All Docling Direct API imports successful')
"
```

## PHASE 3: DOWNLOAD TABLEFORMER WEIGHTS

This downloads ~500MB on first run. Be patient.

```bash
python -c "
import time
print('Downloading TableFormer model weights (~500MB)...')
start = time.time()

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

opts = PdfPipelineOptions(do_table_structure=True)
opts.table_structure_options.mode = TableFormerMode.ACCURATE
opts.table_structure_options.do_cell_matching = True

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
)

print(f'✅ Done in {time.time() - start:.1f}s — weights cached in ~/.cache/docling/models/')
"
```

## PHASE 4: FUNCTIONAL TEST — THE KEY MOMENT

This runs the Docling Direct API on Broadmeadows. If tables come back as DataFrames
with ACM data, Approach A is viable.

```bash
python -c "
import time
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

opts = PdfPipelineOptions(do_table_structure=True)
opts.table_structure_options.mode = TableFormerMode.ACCURATE
opts.table_structure_options.do_cell_matching = True

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
)

print('Converting Broadmeadows PDF...')
start = time.time()
result = converter.convert('docs/samplePDF/Clutch_Broadmeadows.pdf')
doc = result.document
elapsed = time.time() - start

print(f'Done in {elapsed:.1f}s — {len(doc.tables)} tables found')
print('=' * 70)

for i, table in enumerate(doc.tables):
    try:
        df = table.export_to_dataframe(doc=doc)
        html = table.export_to_html()
        page = table.prov[0].page_no if table.prov else -1
        merged = 'colspan' in html or 'rowspan' in html
        
        print(f'\\nTable {i}: Page {page}, {len(df)}r × {len(df.columns)}c, merged={merged}')
        print(f'  Cols: {list(df.columns)}')
        if len(df) > 0:
            for r in range(min(3, len(df))):
                print(f'  Row {r}: {dict(df.iloc[r])}')
        
        flat = df.to_string().lower()
        acm = [x for x in ['same as','not sampled','no access','34511','negative','positive'] if x in flat]
        if acm: print(f'  ACM indicators: {acm}')
    except Exception as e:
        print(f'\\nTable {i}: ERROR — {e}')

print(f'\\n✅ Functional test complete')
"
```

## PHASE 5: MINERU DECISION POINT

**Ask the user**: Based on the Docling Direct API results above, should we also set up MinerU?

Factors to consider:
- If Docling found register tables with ACM data → MinerU may be unnecessary
- MinerU requires paddlepaddle-gpu (~1-2GB download, potential torch conflicts)
- MinerU code was deleted in E24-S3 — needs fresh spike-only script
- Skipping MinerU = 2-way comparison (faster); including = 3-way (more thorough)

**If user says YES to MinerU:**

```bash
# Check CUDA version first
nvidia-smi | head -3

# Install paddle
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# Verify paddle
python -c "import paddle; print(f'paddle={paddle.__version__}'); paddle.utils.run_check()"

# Upgrade magic-pdf
uv pip install "magic-pdf[full]>=1.3.0" --break-system-packages

# Verify MinerU
python -c "import magic_pdf; print(f'magic-pdf={magic_pdf.__version__}')"

# Check for torch/paddle conflict
python -c "
import torch; t = torch.randn(3,3).cuda(); print(f'torch GPU: OK')
import paddle; print(f'paddle: OK')
print('✅ Coexistence verified')
"
```

**If conflict**: Try `pip install paddlepaddle==3.2.0` (CPU-only) or skip MinerU.

## PHASE 6: GENERATE ARTIFACTS

### Create verification script

Save to `scripts/research/e25_verify_tools.py` — a standalone script that verifies
all tools are ready. (Use the full script from the /e25-verify-all command definition.)

### Create environment audit report

Save to `docs/research/e25-environment-audit.md` with:

```markdown
# E25 Environment Audit

**Date**: 2026-02-27
**OS**: Windows [version]
**Python**: [version]
**GPU**: [model] — CUDA [version]
**Agent**: Mary (BA)

## Package Status

| Package | Status | Version | Notes |
|---------|--------|---------|-------|
| torch | ✅ | [ver] | CUDA: [ver] |
| PyMuPDF | ✅ | [ver] | Broadmeadows: [N] pages |
| Docling Direct API | ✅/❌ | [ver] | [import test result] |
| TableFormerMode | ✅/❌ | N/A | ACCURATE mode: [yes/no] |
| content-core | [ver] | [ver] | [status] |
| pandas | ✅/❌ | [ver] | DataFrame export |
| tabulate | ✅/❌ | [ver] | df.to_markdown() |
| magic-pdf | ✅/⏭️ | [ver] | [installed/skipped] |
| paddlepaddle | ✅/⏭️/❌ | [ver] | [installed/skipped/conflict] |

## Docling Functional Test Results

- Tables found: [N]
- Processing time: [N]s
- ACM indicators found: [list]
- Register tables identified: [which table indices]

## MinerU Decision

[Installed / Skipped — with rationale]

## Installation Steps Taken

1. [what was installed]
2. [what was upgraded]
3. [conflicts resolved]

## Ready Status

- [x/] PyMuPDF: functional
- [x/] Docling Direct API: importable + functional
- [x/] TableFormer weights: cached
- [x/] GPU: CUDA available
- [x/] pandas + tabulate: installed
- [x/] MinerU: [ready/skipped]

**Overall: READY / NOT READY for E25-S2 (Research Spike Execution)**
```

### Commit

```bash
git add scripts/research/e25_verify_tools.py docs/research/e25-environment-audit.md
git commit -m "research(E25-S1): environment setup and verification

Tools verified:
- PyMuPDF: ✅ (production baseline)
- Docling Direct API: [✅/❌] (TableFormer ACCURATE mode)
- MinerU: [✅/⏭️] ([status])
- GPU: ✅ (CUDA [version])

Docling functional test: [N] tables from Broadmeadows, [N]s
ACM indicators: [list]

Audit: docs/research/e25-environment-audit.md"
git push
```

## CRITICAL REMINDERS

1. **Do NOT modify production code** — no changes to source.py, orchestrator.py, etc.
2. **Do NOT trigger extraction pipelines** — no worker, no API calls
3. **Do NOT use API budget** — no LLM calls (this is local-only)
4. **Do NOT add paddle to pyproject.toml** — spike-only install
5. **ASK THE USER** before installing MinerU (Phase 5 decision point)
