"""Post-shutdown verification and cleanup for ACM-AI services.

Checks that ports are freed, processes are stopped, and cleans up
stale PID files and orphaned artifacts.

Exit code 0 = all clean.
Exit code 1 = something still running or cleanup failed.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Service ports to verify
SERVICE_PORTS = {
    5055: "API Server",
    8502: "Frontend",
    8000: "SurrealDB",
}

# Process patterns that indicate ACM-AI services still running
PROCESS_PATTERNS = [
    "run_api.py",
    "run_worker.py",
    "surreal-commands-worker",
]

# PID file directory (Linux/WSL)
PID_DIR = Path("/tmp")

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

RESET = "\033[0m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if platform.system() == "Windows":
        return os.environ.get("TERM") or os.environ.get("WT_SESSION") is not None
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = _supports_color()


def _ok(msg: str) -> str:
    return f"{GREEN}[OK]{RESET} {msg}" if USE_COLOR else f"[OK] {msg}"


def _fail(msg: str) -> str:
    return f"{RED}[!!]{RESET} {msg}" if USE_COLOR else f"[!!] {msg}"


def _info(msg: str) -> str:
    return f"{YELLOW}[--]{RESET} {msg}" if USE_COLOR else f"[--] {msg}"


# ---------------------------------------------------------------------------
# Port checks
# ---------------------------------------------------------------------------


def _is_port_in_use(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def check_ports() -> list[str]:
    """Check that service ports are free. Returns list of issues."""
    issues = []
    for port, name in SERVICE_PORTS.items():
        if _is_port_in_use(port):
            issues.append(f"Port {port} ({name}) is still in use")
    return issues


# ---------------------------------------------------------------------------
# Process checks
# ---------------------------------------------------------------------------


def _find_acm_processes() -> list[str]:
    """Find any ACM-AI processes still running."""
    found = []
    for pattern in PROCESS_PATTERNS:
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    [
                        "wmic",
                        "process",
                        "where",
                        f"CommandLine like '%{pattern}%'",
                        "get",
                        "ProcessId,CommandLine",
                        "/format:csv",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.splitlines():
                    if pattern in line and "wmic" not in line.lower():
                        found.append(f"Process matching '{pattern}' still running")
                        break
            else:
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().splitlines()
                    found.append(
                        f"Process matching '{pattern}' still running"
                        f" (PID: {', '.join(pids)})"
                    )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return found


# ---------------------------------------------------------------------------
# Cleanup actions
# ---------------------------------------------------------------------------


def cleanup_pid_files() -> list[str]:
    """Remove stale PID files. Returns list of cleaned files."""
    cleaned = []
    if platform.system() == "Windows":
        return cleaned  # PID files are Linux/WSL only
    for pid_file in PID_DIR.glob("acm-ai-*.pid"):
        try:
            pid_file.unlink()
            cleaned.append(str(pid_file))
        except OSError:
            pass
    return cleaned


def cleanup_orphaned_torch_distinfo() -> list[str]:
    """Remove orphaned torch-*.dist-info dirs without RECORD."""
    cleaned = []
    venv_dir = PROJECT_ROOT / ".venv"
    site_packages = None

    candidates = [
        venv_dir / "Lib" / "site-packages",  # Windows
        venv_dir / "lib",  # Linux
    ]
    for cand in candidates:
        if cand.is_dir():
            if cand.name == "site-packages":
                site_packages = cand
                break
            for sub in cand.iterdir():
                sp = sub / "site-packages"
                if sp.is_dir():
                    site_packages = sp
                    break
            if site_packages:
                break

    if site_packages is None:
        return cleaned

    for dist in site_packages.glob("torch-*.dist-info"):
        record = dist / "RECORD"
        if not record.exists():
            try:
                shutil.rmtree(dist)
                cleaned.append(dist.name)
            except OSError:
                pass
    return cleaned


def cleanup_pycache() -> int:
    """Remove __pycache__ directories at project root level. Returns count."""
    count = 0
    pycache = PROJECT_ROOT / "__pycache__"
    if pycache.is_dir():
        shutil.rmtree(pycache, ignore_errors=True)
        count += 1
    return count


def cleanup_pytest_cache() -> bool:
    """Remove .pytest_cache if present. Returns True if removed."""
    cache = PROJECT_ROOT / ".pytest_cache"
    if cache.is_dir():
        shutil.rmtree(cache, ignore_errors=True)
        return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("")
    print("=" * 60)
    print("  ACM-AI Shutdown Cleanup")
    print("=" * 60)
    print("")

    has_issues = False

    # 1. Check ports
    print("  Checking ports...")
    port_issues = check_ports()
    if port_issues:
        for issue in port_issues:
            print(f"    {_fail(issue)}")
        has_issues = True
    else:
        print(f"    {_ok('All service ports are free')}")

    # 2. Check processes
    print("  Checking processes...")
    proc_issues = _find_acm_processes()
    if proc_issues:
        for issue in proc_issues:
            print(f"    {_fail(issue)}")
        has_issues = True
    else:
        print(f"    {_ok('No ACM-AI processes found')}")

    # 3. Cleanup
    print("  Running cleanup...")

    pid_cleaned = cleanup_pid_files()
    if pid_cleaned:
        print(f"    {_info(f'Removed {len(pid_cleaned)} PID file(s)')}")

    torch_cleaned = cleanup_orphaned_torch_distinfo()
    if torch_cleaned:
        names = ", ".join(torch_cleaned)
        print(f"    {_info(f'Removed orphaned dist-info: {names}')}")

    pycache_count = cleanup_pycache()
    if pycache_count:
        print(f"    {_info('Removed root __pycache__')}")

    pytest_removed = cleanup_pytest_cache()
    if pytest_removed:
        print(f"    {_info('Removed .pytest_cache')}")

    if not (pid_cleaned or torch_cleaned or pycache_count or pytest_removed):
        print(f"    {_ok('Nothing to clean up')}")

    # Summary
    print("")
    if has_issues:
        print(f"  {_fail('Some services may still be running — check above')}")
    else:
        print(f"  {_ok('Shutdown complete — all clean')}")
    print("")

    return 1 if has_issues else 0


if __name__ == "__main__":
    sys.exit(main())
