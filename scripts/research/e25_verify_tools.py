"""E25-S1 deliverable: Verify all 3 table extraction tools are operational.

Run under the MAIN venv:
    uv run python scripts/research/e25_verify_tools.py

Checks:
    1. PyMuPDF (fitz) — direct import in main venv
    2. Docling Direct API — import + pipeline_options in main venv
    3. MinerU — subprocess bridge via .venv-mineru

Exit code 0 = all checks pass (warnings are OK, e.g. MinerU venv absent).
Exit code 1 = at least one critical check failed.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PASS = "pass"
WARN = "warn"
FAIL = "fail"

SYMBOLS = {PASS: "OK", WARN: "!!", FAIL: "XX"}
COLORS = {PASS: "\033[32m", WARN: "\033[33m", FAIL: "\033[31m"}
RESET = "\033[0m"
USE_COLOR = not os.environ.get("NO_COLOR") and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _sym(status: str) -> str:
    if USE_COLOR:
        return f"{COLORS[status]}[{SYMBOLS[status]}]{RESET}"
    return f"[{SYMBOLS[status]}]"


# ---------------------------------------------------------------------------
# Tool 1: PyMuPDF
# ---------------------------------------------------------------------------


def check_pymupdf() -> tuple[str, str, str]:
    label = "Tool 1: PyMuPDF (fitz)"
    try:
        fitz = importlib.import_module("fitz")
        ver = fitz.version[0]  # type: ignore[attr-defined]
        return PASS, label, f"v{ver} — main venv OK"
    except ImportError as e:
        return FAIL, label, f"import failed: {e}"
    except Exception as e:  # noqa: BLE001
        return FAIL, label, f"unexpected error: {e}"


# ---------------------------------------------------------------------------
# Tool 2: Docling Direct API
# ---------------------------------------------------------------------------


def check_docling() -> list[tuple[str, str, str]]:
    results = []

    # DocumentConverter
    try:
        importlib.import_module("docling.document_converter")
        results.append((PASS, "Tool 2a: docling.DocumentConverter", "main venv OK"))
    except ImportError as e:
        results.append((FAIL, "Tool 2a: docling.DocumentConverter", f"import failed: {e}"))

    # TableFormerMode via pipeline_options
    try:
        mod = importlib.import_module("docling.datamodel.pipeline_options")
        has_tf = hasattr(mod, "TableFormerMode")
        if has_tf:
            results.append((PASS, "Tool 2b: docling.TableFormerMode", "main venv OK"))
        else:
            results.append((WARN, "Tool 2b: docling.TableFormerMode", "attr not found in pipeline_options"))
    except ImportError as e:
        results.append((FAIL, "Tool 2b: docling.TableFormerMode", f"import failed: {e}"))

    return results


# ---------------------------------------------------------------------------
# Tool 3: MinerU (via subprocess bridge)
# ---------------------------------------------------------------------------


def _mineru_python() -> Path:
    venv_path = os.environ.get("MINERU_VENV_PATH", ".venv-mineru")
    base = PROJECT_ROOT / venv_path
    win = base / "Scripts" / "python.exe"
    nix = base / "bin" / "python"
    if win.exists():
        return win
    if nix.exists():
        return nix
    return win  # return win path for error messages even if absent


def check_mineru() -> list[tuple[str, str, str]]:
    results = []
    enabled = os.environ.get("MINERU_ENABLED", "false").lower() == "true"
    python = _mineru_python()

    # Check venv exists
    if not python.exists():
        status = FAIL if enabled else WARN
        suffix = "run /e25-setup-mineru to create" if not enabled else "MINERU_ENABLED=true but venv missing"
        results.append((status, "Tool 3a: MinerU venv (.venv-mineru)", suffix))
        return results

    results.append((PASS, "Tool 3a: MinerU venv (.venv-mineru)", str(python)))

    # Check magic_pdf import inside the venv
    try:
        proc = subprocess.run(
            [
                str(python),
                "-c",
                "import importlib.metadata; v=importlib.metadata.version('magic-pdf'); print(f'v{v}')",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            ver = proc.stdout.strip()
            results.append((PASS, "Tool 3b: magic_pdf import", f"{ver} in .venv-mineru"))
        else:
            results.append((WARN, "Tool 3b: magic_pdf import", f"failed: {proc.stderr.strip()[:120]}"))
    except subprocess.TimeoutExpired:
        results.append((WARN, "Tool 3b: magic_pdf import", "timeout after 30s"))
    except Exception as e:  # noqa: BLE001
        results.append((WARN, "Tool 3b: magic_pdf import", f"error: {e}"))

    # Check paddle import inside the venv
    try:
        proc = subprocess.run(
            [str(python), "-c", "import paddle; print(f'v{paddle.__version__}')"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            ver = proc.stdout.strip()
            results.append((PASS, "Tool 3c: paddle import", f"{ver} in .venv-mineru"))
        else:
            results.append((WARN, "Tool 3c: paddle import", f"failed: {proc.stderr.strip()[:120]}"))
    except subprocess.TimeoutExpired:
        results.append((WARN, "Tool 3c: paddle import", "timeout after 30s"))
    except Exception as e:  # noqa: BLE001
        results.append((WARN, "Tool 3c: paddle import", f"error: {e}"))

    # Test subprocess bridge with a minimal dry-run (no PDF needed — just bridge invocation)
    runner = PROJECT_ROOT / "scripts" / "mineru_runner.py"
    if runner.exists():
        try:
            # Pass a nonexistent PDF — we expect {"status": "error", "tables": []}
            # This confirms the bridge JSON protocol works end-to-end
            proc = subprocess.run(
                [str(python), str(runner), "--pdf", "/nonexistent.pdf"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            try:
                data = json.loads(proc.stdout)
                if "status" in data and "tables" in data:
                    results.append((PASS, "Tool 3d: MinerU bridge protocol", "JSON protocol OK"))
                else:
                    results.append((WARN, "Tool 3d: MinerU bridge protocol", "unexpected JSON schema"))
            except json.JSONDecodeError:
                results.append((WARN, "Tool 3d: MinerU bridge protocol", f"invalid JSON: {proc.stdout[:80]}"))
        except subprocess.TimeoutExpired:
            results.append((WARN, "Tool 3d: MinerU bridge protocol", "timeout after 30s"))
        except Exception as e:  # noqa: BLE001
            results.append((WARN, "Tool 3d: MinerU bridge protocol", f"error: {e}"))
    else:
        results.append((WARN, "Tool 3d: MinerU bridge protocol", "scripts/mineru_runner.py not found"))

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_all_checks() -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    results.append(check_pymupdf())
    results.extend(check_docling())
    results.extend(check_mineru())
    return results


def print_results(results: list[tuple[str, str, str]]) -> bool:
    max_label = max(len(r[1]) for r in results)

    print("")
    print("=" * 65)
    print("  E25 Tool Verification — 3-Way Extraction Spike")
    print("=" * 65)
    print("")

    has_critical_failure = False
    for status, label, detail in results:
        sym = _sym(status)
        print(f"  {sym}  {label:<{max_label}}  {detail}")
        if status == FAIL:
            has_critical_failure = True

    print("")
    if has_critical_failure:
        if USE_COLOR:
            print(f"  {COLORS[FAIL]}RESULT: CRITICAL FAILURES DETECTED{RESET}")
        else:
            print("  RESULT: CRITICAL FAILURES DETECTED")
    else:
        warn_count = sum(1 for s, _, _ in results if s == WARN)
        if warn_count:
            print(f"  RESULT: PASSED ({warn_count} warning{'s' if warn_count > 1 else ''})")
        else:
            if USE_COLOR:
                print(f"  {COLORS[PASS]}RESULT: ALL CHECKS PASSED{RESET}")
            else:
                print("  RESULT: ALL CHECKS PASSED")
    print("")

    return not has_critical_failure


def main() -> int:
    results = run_all_checks()
    passed = print_results(results)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
