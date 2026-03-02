---
description: "E25 Research Spike — Final verification of all tools. Run LAST after setup steps. Generates the environment audit report."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# E25 Final Verification + Audit Report

You are Mary (BA) completing the E25 environment verification for ACM-AI.

## MANDATORY PRE-READ

1. `docs/research/e25-environment-audit.md` — Review what preflight and setup steps found
2. `docs/research/e25-environment-setup-plan.md` — Section 5 (Success Criteria)

## STEP 1: Run Full Verification Script

Create and run `scripts/research/e25_verify_tools.py`:

```python
#!/usr/bin/env python3
"""E25 Research Spike: Tool Verification Script."""
import sys
import time

results = {}

def check(name, fn):
    try:
        result = fn()
        results[name] = {"status": "✅", "detail": result}
        print(f"  {name}: ✅ {result}")
        return True
    except Exception as e:
        results[name] = {"status": "❌", "detail": str(e)}
        print(f"  {name}: ❌ {e}")
        return False

print("=" * 60)
print("E25 TOOL VERIFICATION")
print("=" * 60)

# 1. Python version
print("\n[1] Python")
check("Python", lambda: f"{sys.version}")

# 2. GPU
print("\n[2] GPU")
def check_gpu():
    import torch
    assert torch.cuda.is_available(), "CUDA not available"
    name = torch.cuda.get_device_name(0)
    return f"torch={torch.__version__}, CUDA={torch.version.cuda}, GPU={name}"
check("GPU", check_gpu)

# 3. PyMuPDF
print("\n[3] PyMuPDF")
def check_pymupdf():
    import fitz
    doc = fitz.open("docs/samplePDF/Clutch_Broadmeadows.pdf")
    pages = len(doc)
    doc.close()
    return f"v{fitz.version}, Broadmeadows={pages} pages"
check("PyMuPDF", check_pymupdf)

# 4. Docling Direct API
print("\n[4] Docling Direct API")
def check_docling_import():
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    return f"Imports OK, TableFormerMode.ACCURATE={TableFormerMode.ACCURATE}"
check("Docling Imports", check_docling_import)

def check_docling_converter():
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    opts = PdfPipelineOptions(do_table_structure=True)
    opts.table_structure_options.mode = TableFormerMode.ACCURATE
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )
    return "Converter created (model weights cached)"
check("Docling Converter", check_docling_converter)

# 5. Docling Functional Test (THE BIG ONE)
print("\n[5] Docling Functional Test — Broadmeadows PDF")
def check_docling_functional():
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    
    opts = PdfPipelineOptions(do_table_structure=True)
    opts.table_structure_options.mode = TableFormerMode.ACCURATE
    opts.table_structure_options.do_cell_matching = True
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )
    
    start = time.time()
    result = converter.convert("docs/samplePDF/Clutch_Broadmeadows.pdf")
    elapsed = time.time() - start
    
    doc = result.document
    table_count = len(doc.tables)
    
    # Check for ACM data in tables
    acm_indicators = []
    total_rows = 0
    for table in doc.tables:
        try:
            df = table.export_to_dataframe(doc=doc)
            total_rows += len(df)
            flat = df.to_string().lower()
            if "same as" in flat: acm_indicators.append("Same As")
            if "not sampled" in flat: acm_indicators.append("Not Sampled")
            if "34511" in flat: acm_indicators.append("NATA numbers")
            if "negative" in flat: acm_indicators.append("Negative results")
            if "positive" in flat: acm_indicators.append("Positive results")
        except:
            pass
    
    unique_indicators = list(set(acm_indicators))
    return (f"{table_count} tables, {total_rows} total rows, "
            f"{elapsed:.1f}s, ACM data: {unique_indicators}")
check("Docling Functional", check_docling_functional)

# 6. pandas + tabulate
print("\n[6] DataFrame Dependencies")
def check_pandas():
    import pandas as pd
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    md = df.to_markdown(index=False)
    return f"pandas={pd.__version__}, to_markdown()={len(md)} chars"
check("pandas + tabulate", check_pandas)

# 7. MinerU (optional)
print("\n[7] MinerU (optional)")
def check_mineru():
    import magic_pdf
    import paddle
    gpu = paddle.device.is_compiled_with_cuda()
    return f"magic-pdf={magic_pdf.__version__}, paddle={paddle.__version__}, GPU={gpu}"
try:
    check("MinerU", check_mineru)
except:
    results["MinerU"] = {"status": "⏭️", "detail": "Not installed (optional)"}
    print(f"  MinerU: ⏭️ Not installed (optional)")

# Summary
print(f"\n{'=' * 60}")
print("SUMMARY")
print(f"{'=' * 60}")
required = ["GPU", "PyMuPDF", "Docling Imports", "Docling Converter", "Docling Functional", "pandas + tabulate"]
passed = sum(1 for k in required if results.get(k, {}).get("status") == "✅")
total = len(required)
ready = passed == total

for name, r in results.items():
    req = "REQUIRED" if name in required else "optional"
    print(f"  {r['status']} {name} ({req})")

print(f"\n{'✅ READY' if ready else '❌ NOT READY'} for E25 research spike ({passed}/{total} required tools)")

if results.get("MinerU", {}).get("status") == "✅":
    print("  + MinerU available (3-way comparison possible)")
else:
    print("  MinerU not available (2-way comparison: PyMuPDF vs Docling Direct API)")
```

Save to `scripts/research/e25_verify_tools.py` then run:

```bash
mkdir -p scripts/research
python scripts/research/e25_verify_tools.py
```

## STEP 2: Generate Final Audit Report

Based on ALL results from preflight + setup + verification, create/update `docs/research/e25-environment-audit.md`:

The report must include:

1. **System info**: Python version, NVIDIA GPU model, CUDA version, OS
2. **Package versions**: All relevant packages with exact versions
3. **Installation steps taken**: What was installed/upgraded during setup
4. **Conflict resolution**: Any torch/paddle issues and how resolved
5. **Verification results**: Pass/fail for each tool
6. **Docling functional results**: Number of tables found, ACM indicators present, processing time
7. **Model weights status**: TableFormer cached? MinerU models cached?
8. **Ready/not-ready status**: Clear go/no-go for research spike
9. **MinerU decision**: Installed or skipped, with rationale

## STEP 3: Commit Setup Artifacts

```bash
git add scripts/research/e25_verify_tools.py
git add docs/research/e25-environment-audit.md
git add docs/research/e25-environment-setup-plan.md
git commit -m "research(E25): environment setup and verification

Tools verified:
- PyMuPDF: ✅ (production baseline)
- Docling Direct API: ✅/❌ (TableFormer ACCURATE mode)
- MinerU: ✅/⏭️ (optional — paddle status)
- GPU: ✅ (CUDA)

Environment audit: docs/research/e25-environment-audit.md
Verification script: scripts/research/e25_verify_tools.py"
git push
```

## CRITICAL: Report to Demi

After verification, clearly state:

1. **Can we proceed with the research spike?** (Yes/No)
2. **Which approaches are available?**
   - Approach A (PyMuPDF + Docling Direct API): Ready? Yes/No
   - Approach B (PyMuPDF + MinerU): Ready? Yes/No
   - Approach C (Pure Docling): Ready? Yes/No
3. **Did Docling find ACM register tables?** (The breakthrough question)
4. **Any blockers or risks for next session?**
