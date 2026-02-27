"""Package version and import verification."""

from __future__ import annotations

import importlib
from dataclasses import dataclass

from tui.config import AUDIT_PACKAGES


@dataclass
class PackageResult:
    name: str
    version: str
    status: str  # "OK", "WARN", "MISSING", "ERROR"
    notes: str


def _check_single(pkg_name: str) -> PackageResult:
    """Check a single package's availability and version."""
    try:
        mod = importlib.import_module(pkg_name)
        version = getattr(mod, "__version__", "unknown")

        # Special checks for specific packages
        if pkg_name == "torch":
            import torch

            if torch.cuda.is_available():
                return PackageResult(
                    pkg_name,
                    version,
                    "OK",
                    f"CUDA {torch.version.cuda}",
                )
            else:
                return PackageResult(pkg_name, version, "WARN", "CPU-only, no CUDA")

        if pkg_name == "pymupdf":
            # PyMuPDF imports as 'fitz'
            import fitz

            return PackageResult("pymupdf", fitz.version[0], "OK", "")

        return PackageResult(pkg_name, str(version), "OK", "")

    except ImportError:
        # Special case: pymupdf imports as fitz
        if pkg_name == "pymupdf":
            try:
                import fitz

                return PackageResult("pymupdf", fitz.version[0], "OK", "import as fitz")
            except ImportError:
                pass
        return PackageResult(pkg_name, "-", "MISSING", "Not installed")
    except Exception as e:
        return PackageResult(pkg_name, "-", "ERROR", str(e)[:60])


def audit_packages(packages: list[str] | None = None) -> list[PackageResult]:
    """Audit all configured packages. Returns list of results."""
    pkg_list = packages or AUDIT_PACKAGES
    return [_check_single(pkg) for pkg in pkg_list]
