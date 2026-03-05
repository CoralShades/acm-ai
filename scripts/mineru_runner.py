"""MinerU subprocess bridge — runs inside .venv-mineru, NOT the main venv.

Called from the main project via subprocess:
    .venv-mineru\\Scripts\\python.exe scripts/mineru_runner.py --pdf <path> [--output <json_path>]

Output JSON (stdout or file):
    {"status": "ok", "tables": [{"page": 1, "html": "<table>...</table>", "rows": 10, "cols": 5}]}
    {"status": "error", "error": "...", "tables": []}

IMPORTANT:
- This file must NEVER import from open_notebook or any main-project module.
- It runs in a completely separate venv (.venv-mineru) with its own torch/paddle/magic-pdf.
- All extraction is wrapped in try/except — always returns valid JSON, never raw tracebacks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def extract_tables(pdf_path: Path) -> list[dict]:
    """Extract tables from a PDF using MinerU (magic-pdf).

    Returns a list of table dicts with keys:
        page (int), html (str), rows (int), cols (int)

    TODO (E25-S2): Implement actual magic-pdf 1.3.x API calls here.
    The magic-pdf API for 1.3.x needs to be verified from:
        import magic_pdf
        help(magic_pdf)  # or review magic-pdf 1.3.x docs/changelog
    Expected pattern (to be confirmed):
        from magic_pdf.pipe.UNIPipe import UNIPipe
        from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter
        ...
    """
    # TODO (E25-S2): Replace this stub with actual magic-pdf extraction
    raise NotImplementedError(
        "MinerU extraction not yet implemented — see TODO in extract_tables(). "
        "This will be implemented in E25-S2."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MinerU table extraction bridge (runs in .venv-mineru)"
    )
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path (default: stdout)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)

    try:
        if not pdf_path.exists():
            result = {
                "status": "error",
                "error": f"PDF not found: {pdf_path}",
                "tables": [],
            }
        else:
            tables = extract_tables(pdf_path)
            result = {"status": "ok", "tables": tables}
    except NotImplementedError as e:
        result = {"status": "error", "error": f"Not implemented: {e}", "tables": []}
    except Exception as e:  # noqa: BLE001
        result = {"status": "error", "error": str(e), "tables": []}

    output_json = json.dumps(result, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
    else:
        print(output_json)

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
