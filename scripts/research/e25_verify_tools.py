#!/usr/bin/env python3
"""E25-S1 deliverable: Verify all extraction tools are operational.

Run under the MAIN venv:
    uv run python scripts/research/e25_verify_tools.py

Checks:
    1. Python version
    2. GPU (torch + CUDA)
    3. PyMuPDF — import + Broadmeadows PDF access
    4. Docling Direct API — imports + converter creation
    5. Docling Functional — full conversion with ACM indicator detection
    6. pandas + tabulate — DataFrame export dependencies
    7. MinerU (optional) — subprocess bridge via .venv-mineru

Exit code 0 = all required checks pass (warnings OK, e.g. MinerU absent).
Exit code 1 = at least one required check failed.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BROADMEADOWS_PDF = PROJECT_ROOT / "docs" / "samplePDF" / "Clutch_Broadmeadows.pdf"

PASS = "pass"
WARN = "warn"
FAIL = "fail"
SKIP = "skip"

SYMBOLS = {PASS: "OK", WARN: "!!", FAIL: "XX", SKIP: ">>"}
COLORS = {PASS: "\033[32m", WARN: "\033[33m", FAIL: "\033[31m", SKIP: "\033[36m"}
RESET = "\033[0m"
USE_COLOR = (
    not os.environ.get("NO_COLOR")
    and hasattr(sys.stdout, "isatty")
    and sys.stdout.isatty()
)


def _sym(status: str) -> str:
    if USE_COLOR:
        return f"{COLORS[status]}[{SYMBOLS[status]}]{RESET}"
    return f"[{SYMBOLS[status]}]"


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

Results = list[tuple[str, str, str, bool]]  # (status, label, detail, required)


def check_python() -> tuple[str, str, str, bool]:
    return PASS, "Python", f"{sys.version.split()[0]}", True


def check_gpu() -> tuple[str, str, str, bool]:
    label = "GPU (torch + CUDA)"
    try:
        import torch

        if not torch.cuda.is_available():
            return FAIL, label, "CUDA not available", True
        name = torch.cuda.get_device_name(0)
        return (
            PASS,
            label,
            f"torch={torch.__version__}, CUDA={torch.version.cuda}, {name}",
            True,
        )
    except ImportError:
        return FAIL, label, "torch not installed", True
    except Exception as e:
        return FAIL, label, str(e), True


def check_pymupdf() -> tuple[str, str, str, bool]:
    label = "PyMuPDF (fitz)"
    try:
        import fitz

        ver = fitz.version[0]
        if BROADMEADOWS_PDF.exists():
            doc = fitz.open(str(BROADMEADOWS_PDF))
            pages = len(doc)
            doc.close()
            return PASS, label, f"v{ver}, Broadmeadows={pages} pages", True
        return PASS, label, f"v{ver} (PDF not found at expected path)", True
    except ImportError:
        return FAIL, label, "fitz not installed", True
    except Exception as e:
        return FAIL, label, str(e), True


def check_docling_imports() -> tuple[str, str, str, bool]:
    label = "Docling Direct API imports"
    try:
        from docling.datamodel.pipeline_options import TableFormerMode
        from docling.document_converter import DocumentConverter  # noqa: F401

        return (
            PASS,
            label,
            f"DocumentConverter OK, TableFormerMode.ACCURATE={TableFormerMode.ACCURATE}",
            True,
        )
    except ImportError as e:
        return FAIL, label, f"import failed: {e}", True
    except Exception as e:
        return FAIL, label, str(e), True


def check_docling_converter() -> tuple[str, str, str, bool]:
    label = "Docling Converter + weights"
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            TableFormerMode,
        )
        from docling.document_converter import DocumentConverter, PdfFormatOption

        opts = PdfPipelineOptions(do_table_structure=True)
        opts.table_structure_options.mode = TableFormerMode.ACCURATE
        opts.table_structure_options.do_cell_matching = True

        start = time.time()
        DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )
        elapsed = time.time() - start
        return PASS, label, f"created in {elapsed:.1f}s (weights cached)", True
    except Exception as e:
        return FAIL, label, str(e), True


def check_docling_functional() -> tuple[str, str, str, bool]:
    label = "Docling Functional Test"
    if not BROADMEADOWS_PDF.exists():
        return WARN, label, "Broadmeadows PDF not found", True

    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            TableFormerMode,
        )
        from docling.document_converter import DocumentConverter, PdfFormatOption

        opts = PdfPipelineOptions(do_table_structure=True)
        opts.table_structure_options.mode = TableFormerMode.ACCURATE
        opts.table_structure_options.do_cell_matching = True
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )

        start = time.time()
        result = converter.convert(str(BROADMEADOWS_PDF))
        elapsed = time.time() - start
        doc = result.document

        indicators = set()
        total_rows = 0
        for table in doc.tables:
            try:
                df = table.export_to_dataframe(doc=doc)
                total_rows += len(df)
                flat = df.to_string().lower()
                for term in [
                    "same as",
                    "not sampled",
                    "34511",
                    "negative",
                    "positive",
                ]:
                    if term in flat:
                        indicators.add(term)
            except Exception:
                pass

        return (
            PASS,
            label,
            f"{len(doc.tables)} tables, {total_rows} rows, {elapsed:.1f}s, ACM: {sorted(indicators)}",
            True,
        )
    except Exception as e:
        return FAIL, label, str(e), True


def check_pandas_tabulate() -> tuple[str, str, str, bool]:
    label = "pandas + tabulate"
    try:
        import pandas as pd

        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        md = df.to_markdown(index=False)
        return PASS, label, f"pandas={pd.__version__}, to_markdown()={len(md)} chars", True
    except ImportError as e:
        return FAIL, label, f"import failed: {e}", True
    except Exception as e:
        return FAIL, label, str(e), True


def check_mineru() -> tuple[str, str, str, bool]:
    label = "MinerU (optional)"
    venv_path = os.environ.get("MINERU_VENV_PATH", ".venv-mineru")
    base = PROJECT_ROOT / venv_path
    win = base / "Scripts" / "python.exe"
    nix = base / "bin" / "python"
    python = win if win.exists() else nix

    if not python.exists():
        return SKIP, label, "venv not found (skipped — optional)", False

    try:
        proc = subprocess.run(
            [
                str(python),
                "-c",
                (
                    "import importlib.metadata; "
                    "v=importlib.metadata.version('magic-pdf'); "
                    "print(f'magic-pdf={v}')"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            return PASS, label, proc.stdout.strip(), False
        return WARN, label, f"import failed: {proc.stderr.strip()[:80]}", False
    except Exception as e:
        return WARN, label, str(e), False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_all_checks() -> Results:
    checks = [
        check_python,
        check_gpu,
        check_pymupdf,
        check_docling_imports,
        check_docling_converter,
        check_docling_functional,
        check_pandas_tabulate,
        check_mineru,
    ]
    results: Results = []
    for fn in checks:
        print(f"  Checking {fn.__name__.replace('check_', '')}...")
        results.append(fn())
    return results


def print_results(results: Results) -> bool:
    max_label = max(len(r[1]) for r in results)

    print("")
    print("=" * 70)
    print("  E25 Tool Verification — Table Extraction Research Spike")
    print("=" * 70)
    print("")

    has_critical_failure = False
    for status, label, detail, required in results:
        sym = _sym(status)
        req_tag = " [REQUIRED]" if required else " [optional]"
        print(f"  {sym}  {label:<{max_label}}  {detail}{req_tag}")
        if status == FAIL and required:
            has_critical_failure = True

    print("")
    required_checks = [(s, l, d) for s, l, d, r in results if r]
    passed = sum(1 for s, _, _ in required_checks if s == PASS)
    total = len(required_checks)

    if has_critical_failure:
        msg = f"NOT READY — {passed}/{total} required checks passed"
        if USE_COLOR:
            print(f"  {COLORS[FAIL]}{msg}{RESET}")
        else:
            print(f"  {msg}")
    else:
        msg = f"READY for E25 research spike ({passed}/{total} required)"
        if USE_COLOR:
            print(f"  {COLORS[PASS]}{msg}{RESET}")
        else:
            print(f"  {msg}")

    mineru_status = next((s for s, l, _, _ in results if "MinerU" in l), None)
    if mineru_status == PASS:
        print("  + MinerU available (3-way comparison possible)")
    else:
        print("  MinerU not available (2-way comparison: PyMuPDF vs Docling Direct API)")

    print("")
    return not has_critical_failure


def main() -> int:
    os.chdir(PROJECT_ROOT)
    print("\nE25 Tool Verification starting...\n")
    results = run_all_checks()
    passed = print_results(results)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
