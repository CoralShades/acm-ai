---
description: "E25 Research Spike — Pre-flight environment checks. Run FIRST before any setup."
allowed-tools: Bash, Read, Glob, Grep
---

# E25 Pre-Flight Environment Checks

You are Mary (BA) running the E25 environment audit for ACM-AI.

## MANDATORY PRE-READ

Read these files FIRST (use Read tool):
1. `pyproject.toml` — Check current dependencies (look for content-core, docling, magic-pdf, torch)
2. `uv.lock` — Search for locked versions of torch, docling, paddle
3. `docs/reviews/e24-validation-results.md` — Lines 1-50 (the summary)

## CONTEXT

E24 validation proved content-core's markdown serializer destroys TableFormer table output (17/31 regression). E25 tests the **Docling Direct API** which bypasses content-core entirely, giving native DataFrames.

MinerU code was deleted in E24-S3 (commit `6e0e2e8`). `magic-pdf` may still be in pyproject.toml but paddle was never installed.

## TASKS — Run All Checks

### Task 1: System Environment

```bash
python --version
nvidia-smi | head -8
```

### Task 2: Python Package Audit

```bash
python -c "import torch; print(f'torch={torch.__version__}, cuda_available={torch.cuda.is_available()}, cuda_version={torch.version.cuda}')"
python -c "import fitz; print(f'PyMuPDF={fitz.version}')"
python -c "from docling.document_converter import DocumentConverter; print('Docling Direct API: OK')" 2>&1
python -c "from docling.datamodel.pipeline_options import TableFormerMode; print(f'TableFormerMode.ACCURATE={TableFormerMode.ACCURATE}')" 2>&1
python -c "import magic_pdf; print(f'magic-pdf={magic_pdf.__version__}')" 2>&1
python -c "import paddle; print(f'paddle={paddle.__version__}')" 2>&1
```

### Task 3: Package Versions List

```bash
uv pip list 2>/dev/null | grep -iE "torch|docling|magic|paddle|fitz|pymupdf|content-core|pandas|tabulate"
```

Or on PowerShell:
```powershell
uv pip list | Select-String -Pattern "torch|docling|magic|paddle|fitz|pymupdf|content-core|pandas|tabulate"
```

### Task 4: Broadmeadows PDF Verification

```bash
# Verify benchmark PDF exists
ls -la docs/samplePDF/Clutch_Broadmeadows.pdf 2>/dev/null || dir docs\samplePDF\Clutch_Broadmeadows.pdf
ls -la docs/samplePDF/Clutch_Broadmeadows.csv 2>/dev/null || dir docs\samplePDF\Clutch_Broadmeadows.csv

# Quick PyMuPDF read test
python -c "
import fitz
doc = fitz.open('docs/samplePDF/Clutch_Broadmeadows.pdf')
print(f'Broadmeadows: {len(doc)} pages, {sum(len(p.get_text()) for p in doc)} total chars')
doc.close()
"
```

### Task 5: Check pyproject.toml for stale MinerU dependency

```bash
grep -n "magic-pdf\|mineru\|paddle" pyproject.toml
```

## OUTPUT

Create `docs/research/e25-environment-audit.md` with ALL check results in this format:

```markdown
# E25 Environment Audit

**Date**: [today]
**OS**: Windows [version] + WSL2
**Python**: [version]
**GPU**: [nvidia-smi output summary]

## Package Status

| Package | Status | Version | Notes |
|---------|--------|---------|-------|
| Python | ✅/❌ | x.y.z | |
| torch | ✅/❌ | x.y.z | CUDA: yes/no, version: x.y |
| PyMuPDF | ✅/❌ | x.y.z | |
| Docling Direct API | ✅/❌ | x.y.z | Import test result |
| TableFormerMode | ✅/❌ | N/A | ACCURATE mode available? |
| content-core | ✅/❌ | x.y.z | |
| magic-pdf | ✅/❌/removed | x.y.z | Still in pyproject.toml? |
| paddlepaddle | ❌ expected | N/A | Not installed |
| pandas | ✅/❌ | x.y.z | Needed for DataFrame export |
| tabulate | ✅/❌ | x.y.z | Needed for df.to_markdown() |

## Broadmeadows PDF

- Path: docs/samplePDF/Clutch_Broadmeadows.pdf
- Pages: [N]
- Total chars: [N]
- Ground truth: docs/samplePDF/Clutch_Broadmeadows.csv (31 records)

## Stale Dependencies

[List any magic-pdf/mineru/paddle references still in pyproject.toml]

## Ready Status

- [ ] PyMuPDF: functional
- [ ] Docling Direct API: importable
- [ ] TableFormer mode: available
- [ ] GPU: CUDA available
- [ ] Broadmeadows PDF: accessible
- [ ] pandas + tabulate: installed

**Overall: READY / NOT READY for E25 setup**
```

## IMPORTANT

- This is READ-ONLY audit. Do NOT install anything.
- Do NOT modify any project files.
- Do NOT trigger extraction pipelines or use API budget.
- Capture ALL output — even errors are valuable diagnostic info.
