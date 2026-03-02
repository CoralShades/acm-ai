---
description: "E25 Research Spike — Install and verify Docling Direct API + TableFormer weights. Run AFTER /e25-preflight."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# E25 Setup: Docling Direct API + TableFormer

You are Mary (BA) continuing the E25 environment setup for ACM-AI.

## MANDATORY PRE-READ

1. `docs/research/e25-environment-audit.md` — The preflight audit (confirms what's missing)
2. `docs/reviews/e24-validation-results.md` — Lines 80-130 (Root Cause Analysis — why content-core breaks tables)

## CONTEXT

The **key insight** of E25: Docling's Direct Python API (`table.export_to_dataframe()`) bypasses content-core's broken markdown serialization entirely. E24 proved content-core fragments table rows into isolated cells (17/31 regression). The Direct API gives native Pandas DataFrames with perfect row/column structure.

## STEP 1: Install Missing Dependencies (if needed)

Based on preflight results, install what's missing:

### If Docling Direct API import failed:

```bash
uv pip install docling --break-system-packages
```

### If pandas or tabulate missing:

```bash
uv pip install pandas tabulate --break-system-packages
```

### If Docling is old (< 2.75.0):

```bash
uv pip install "docling>=2.75.0" --break-system-packages
```

**IMPORTANT**: Do NOT uninstall or modify content-core. Docling can be installed alongside it.

## STEP 2: Verify Docling Direct API Imports

```bash
python -c "
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    TableStructureOptions,
)
print('✅ All Docling Direct API imports successful')
print(f'   InputFormat.PDF = {InputFormat.PDF}')
print(f'   TableFormerMode.ACCURATE = {TableFormerMode.ACCURATE}')
"
```

## STEP 3: Pre-Download TableFormer Model Weights

This downloads ~500MB of model weights. They cache in `~/.cache/docling/models/`.

```bash
python -c "
import time
print('Downloading TableFormer model weights (~500MB)...')
print('This may take 2-5 minutes on first run.')
start = time.time()

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
pipeline_options.table_structure_options.do_cell_matching = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

elapsed = time.time() - start
print(f'✅ TableFormer model weights downloaded and cached ({elapsed:.1f}s)')
print(f'   Cache location: ~/.cache/docling/models/')
"
```

## STEP 4: Functional Test — Extract Tables from Broadmeadows PDF

**THIS IS THE CRITICAL TEST.** If this works, E25 Approach A is viable.

```bash
python -c "
import time
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

# Configure for ACCURATE mode with cell matching
pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
pipeline_options.table_structure_options.do_cell_matching = True

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

print('Converting Broadmeadows PDF with Docling Direct API...')
start = time.time()
result = converter.convert('docs/samplePDF/Clutch_Broadmeadows.pdf')
doc = result.document
elapsed = time.time() - start
print(f'Conversion complete in {elapsed:.1f}s')

print(f'\nTables found: {len(doc.tables)}')
print('=' * 70)

for i, table in enumerate(doc.tables):
    try:
        df = table.export_to_dataframe(doc=doc)
        html = table.export_to_html()
        page = table.prov[0].page_no if table.prov else -1
        has_merged = 'colspan' in html or 'rowspan' in html
        
        print(f'\nTable {i}: Page {page}, {len(df)} rows × {len(df.columns)} cols, merged={has_merged}')
        print(f'  Columns: {list(df.columns)}')
        
        # Show first 3 rows as preview
        if len(df) > 0:
            print(f'  Preview (first 3 rows):')
            for row_idx in range(min(3, len(df))):
                row = df.iloc[row_idx]
                print(f'    Row {row_idx}: {dict(row)}')
        
        # Check for key ACM indicators
        flat = df.to_string().lower()
        indicators = {
            'same as': 'same as' in flat,
            'not sampled': 'not sampled' in flat,
            'no access': 'no access' in flat,
            'negative': 'negative' in flat,
            'positive': 'positive' in flat,
            '34511': '34511' in flat,  # NATA sample number prefix
        }
        found = [k for k, v in indicators.items() if v]
        if found:
            print(f'  ACM indicators found: {found}')
            
    except Exception as e:
        print(f'\nTable {i}: ERROR — {e}')

print(f'\n{\"=\" * 70}')
print(f'SUMMARY: {len(doc.tables)} tables extracted in {elapsed:.1f}s')
print('✅ Docling Direct API functional test COMPLETE')
"
```

## STEP 5: Update Audit Report

Update `docs/research/e25-environment-audit.md` with:
- Docling Direct API: ✅ (version, import test, functional test)
- TableFormer weights: ✅ (downloaded, cached)
- Tables found in Broadmeadows: N tables
- Key finding: [which tables contain ACM register data]
- Any ACM indicators found (Same As, Not Sampled, NATA numbers)

## CRITICAL CHECKPOINTS

After this command completes, these must be true:

1. ✅ `from docling.document_converter import DocumentConverter` succeeds
2. ✅ `TableFormerMode.ACCURATE` is accessible
3. ✅ Model weights are cached in `~/.cache/docling/models/`
4. ✅ `converter.convert('docs/samplePDF/Clutch_Broadmeadows.pdf')` produces tables
5. ✅ `table.export_to_dataframe(doc=doc)` returns a Pandas DataFrame
6. ✅ At least one table contains ACM register data (NATA numbers, room names)

If checkpoint 4-6 succeed, **Approach A is viable** and the research spike can proceed.

## DO NOT

- Do NOT modify `source.py` or any production code
- Do NOT trigger the extraction pipeline
- Do NOT use API budget (no LLM calls)
- Do NOT modify content-core's installation
