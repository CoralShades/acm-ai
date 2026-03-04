"""E25 Preflight environment checks for ACM-AI services.

Validates Python/venv, GPU/CUDA, core package imports, benchmark files,
and stale dependency warnings before starting services.

Exit code 0 = all critical checks pass (warnings are OK).
Exit code 1 = at least one critical check failed.
"""

from __future__ import annotations

import importlib
import os
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Check result types
# ---------------------------------------------------------------------------

PASS = "pass"
WARN = "warn"
FAIL = "fail"

SYMBOLS = {PASS: "OK", WARN: "!!", FAIL: "XX"}
COLORS = {PASS: "\033[32m", WARN: "\033[33m", FAIL: "\033[31m"}
RESET = "\033[0m"


def _supports_color() -> bool:
    """Return True if the terminal likely supports ANSI colours."""
    if os.environ.get("NO_COLOR"):
        return False
    if platform.system() == "Windows":
        return os.environ.get("TERM") or os.environ.get("WT_SESSION") is not None
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = _supports_color()


def _sym(status: str) -> str:
    if USE_COLOR:
        return f"{COLORS[status]}[{SYMBOLS[status]}]{RESET}"
    return f"[{SYMBOLS[status]}]"


# ---------------------------------------------------------------------------
# Individual checks — each returns (status, label, detail)
# ---------------------------------------------------------------------------


def check_python_version() -> tuple[str, str, str]:
    v = sys.version_info
    label = "Python version"
    if v >= (3, 11):
        return PASS, label, f"{v.major}.{v.minor}.{v.micro}"
    return FAIL, label, f"{v.major}.{v.minor}.{v.micro} — need >= 3.11"


def check_venv() -> tuple[str, str, str]:
    label = "Virtual environment"
    venv_dir = PROJECT_ROOT / ".venv"
    if not venv_dir.is_dir():
        return FAIL, label, ".venv directory not found"
    # Check for python executable inside venv
    if (venv_dir / "Scripts" / "python.exe").exists():
        return PASS, label, ".venv/Scripts/python.exe"
    if (venv_dir / "bin" / "python").exists():
        return PASS, label, ".venv/bin/python"
    return FAIL, label, ".venv exists but no python executable found"


def check_gpu() -> tuple[str, str, str]:
    label = "GPU / CUDA"
    # Check nvidia-smi first
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return WARN, label, "nvidia-smi failed — no GPU detected"
        gpu_info = result.stdout.strip().splitlines()[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, IndexError):
        return WARN, label, "nvidia-smi not found — no GPU detected"

    # Check torch CUDA
    try:
        import torch

        if torch.cuda.is_available():
            cuda_ver = torch.version.cuda or "unknown"
            return PASS, label, f"{gpu_info} | CUDA {cuda_ver}"
        return WARN, label, f"{gpu_info} | torch.cuda not available"
    except ImportError:
        return WARN, label, f"{gpu_info} | torch not installed (checked separately)"


def check_core_imports() -> list[tuple[str, str, str]]:
    """Check critical ML/extraction imports."""
    results = []

    # torch
    try:
        import torch  # noqa: F811

        results.append((PASS, "Import: torch", f"v{torch.__version__}"))
    except ImportError as e:
        results.append((FAIL, "Import: torch", str(e)))

    # PyMuPDF (fitz)
    try:
        import fitz

        results.append((PASS, "Import: fitz (PyMuPDF)", f"v{fitz.version[0]}"))
    except ImportError as e:
        results.append((FAIL, "Import: fitz (PyMuPDF)", str(e)))

    # docling DocumentConverter
    try:
        importlib.import_module("docling.document_converter")
        results.append((PASS, "Import: docling.DocumentConverter", "OK"))
    except ImportError as e:
        results.append((FAIL, "Import: docling.DocumentConverter", str(e)))

    # docling TableFormerMode
    try:
        importlib.import_module("docling.datamodel.pipeline_options")
        results.append((PASS, "Import: docling.TableFormerMode", "OK"))
    except ImportError as e:
        results.append((FAIL, "Import: docling.TableFormerMode", str(e)))

    return results


def check_data_imports() -> list[tuple[str, str, str]]:
    """Check data-processing imports."""
    results = []
    for mod_name, display in [("pandas", "pandas"), ("tabulate", "tabulate")]:
        try:
            mod = importlib.import_module(mod_name)
            ver = getattr(mod, "__version__", "OK")
            results.append((PASS, f"Import: {display}", f"v{ver}"))
        except ImportError as e:
            results.append((WARN, f"Import: {display}", str(e)))
    return results


def check_benchmark_pdf() -> tuple[str, str, str]:
    label = "Benchmark PDF"
    pdf_path = PROJECT_ROOT / "docs" / "samplePDF" / "Clutch_Broadmeadows.pdf"
    if not pdf_path.exists():
        return WARN, label, "docs/samplePDF/Clutch_Broadmeadows.pdf not found"
    size = pdf_path.stat().st_size
    if size == 0:
        return WARN, label, "Benchmark PDF is empty (0 bytes)"
    return PASS, label, f"{size / 1024:.0f} KB"


def check_ground_truth_csv() -> tuple[str, str, str]:
    label = "Ground truth CSV"
    csv_path = PROJECT_ROOT / "docs" / "samplePDF" / "Clutch_Broadmeadows.csv"
    if not csv_path.exists():
        return WARN, label, "docs/samplePDF/Clutch_Broadmeadows.csv not found"
    return PASS, label, "exists"


def check_stale_deps() -> tuple[str, str, str]:
    label = "Stale deps"
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return WARN, label, "pyproject.toml not found"
    content = pyproject.read_text(encoding="utf-8")
    # magic-pdf intentionally removed from main venv (lives in .venv-mineru)
    if "magic-pdf" in content:
        return (
            WARN,
            label,
            "magic-pdf still listed in pyproject.toml (move to .venv-mineru)",
        )
    return PASS, label, "no stale deps detected"


def check_mineru_venv() -> tuple[str, str, str]:
    label = "MinerU venv (.venv-mineru)"
    venv = PROJECT_ROOT / ".venv-mineru"
    enabled = os.environ.get("MINERU_ENABLED", "false").lower() == "true"
    python_win = venv / "Scripts" / "python.exe"
    python_nix = venv / "bin" / "python"
    exists = python_win.exists() or python_nix.exists()
    if exists:
        return PASS, label, "present and functional"
    if enabled:
        return (
            FAIL,
            label,
            "MINERU_ENABLED=true but .venv-mineru not found — run /e25-setup-mineru",
        )
    return (
        WARN,
        label,
        "not present (MINERU_ENABLED=false — run /e25-setup-mineru to enable)",
    )


def check_torch_distinfo() -> tuple[str, str, str]:
    label = "torch dist-info"
    site_packages = None
    # Find site-packages in venv
    venv_dir = PROJECT_ROOT / ".venv"
    candidates = [
        venv_dir / "Lib" / "site-packages",  # Windows
        venv_dir / "lib",  # Linux — need to check python3.X subdirs
    ]
    for cand in candidates:
        if cand.is_dir():
            if cand.name == "site-packages":
                site_packages = cand
                break
            # Linux: lib/python3.X/site-packages
            for sub in cand.iterdir():
                sp = sub / "site-packages"
                if sp.is_dir():
                    site_packages = sp
                    break
            if site_packages:
                break

    if site_packages is None:
        return PASS, label, "site-packages not found (skipped)"

    orphans = []
    for dist in site_packages.glob("torch-*.dist-info"):
        record = dist / "RECORD"
        if not record.exists():
            orphans.append(dist.name)

    if orphans:
        return WARN, label, f"orphaned: {', '.join(orphans)}"
    return PASS, label, "clean"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_all_checks() -> list[tuple[str, str, str]]:
    """Run all preflight checks and return list of (status, label, detail)."""
    results: list[tuple[str, str, str]] = []

    results.append(check_python_version())
    results.append(check_venv())
    results.append(check_gpu())
    results.extend(check_core_imports())
    results.extend(check_data_imports())
    results.append(check_benchmark_pdf())
    results.append(check_ground_truth_csv())
    results.append(check_stale_deps())
    results.append(check_mineru_venv())
    results.append(check_torch_distinfo())

    return results


def print_results(results: list[tuple[str, str, str]]) -> bool:
    """Print results table. Returns True if all critical checks passed."""
    max_label = max(len(r[1]) for r in results)

    print("")
    print("=" * 60)
    print("  ACM-AI Preflight Checks")
    print("=" * 60)
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
        print("  Fix the [XX] issues above before starting services.")
    else:
        warn_count = sum(1 for s, _, _ in results if s == WARN)
        if warn_count:
            if USE_COLOR:
                print(
                    f"  {COLORS[PASS]}RESULT: PASSED{RESET}"
                    f" ({warn_count} warning{'s' if warn_count > 1 else ''})"
                )
            else:
                print(
                    f"  RESULT: PASSED"
                    f" ({warn_count} warning{'s' if warn_count > 1 else ''})"
                )
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
