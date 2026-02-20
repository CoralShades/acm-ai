"""Process management utilities for starting/stopping services."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

from _service_config import PID_DIR, ServiceDef


def is_docker_available() -> bool:
    """Check if Docker is available and the daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_tmux_available() -> bool:
    """Check if tmux is installed."""
    return shutil.which("tmux") is not None


def is_uv_available() -> bool:
    """Check if uv is installed."""
    return shutil.which("uv") is not None


def is_node_available() -> bool:
    """Check if node/npm is installed."""
    return shutil.which("npm") is not None


def read_pid_file(pid_file: str) -> int | None:
    """Read a PID from a PID file, returning None if invalid."""
    try:
        pid = int(Path(pid_file).read_text().strip())
        # Check if process exists
        if platform.system() == "Windows":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if str(pid) in result.stdout:
                return pid
        else:
            os.kill(pid, 0)  # Signal 0 = check existence
            return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        pass
    return None


def is_service_running(service: ServiceDef) -> bool:
    """Check if a service is currently running."""
    if service.is_docker:
        return _is_docker_service_running(service.name)

    # Check PID file first
    if service.pid_file:
        pid = read_pid_file(service.pid_file)
        if pid is not None:
            return True

    # Check by process pattern
    for pattern in service.stop_patterns:
        if _find_process_by_pattern(pattern):
            return True

    return False


def _is_docker_service_running(service_name: str) -> bool:
    """Check if a Docker Compose service is running."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", service_name, "--format", "{{.State}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "running" in result.stdout.lower()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _find_process_by_pattern(pattern: str) -> int | None:
    """Find a process PID by command-line pattern."""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["wmic", "process", "get", "ProcessId,CommandLine", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                if pattern in line:
                    parts = line.strip().split(",")
                    return int(parts[-1])
        else:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().splitlines()[0])
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


def start_service_background(service: ServiceDef) -> bool:
    """Start a service in the background. Returns True on success."""
    if service.is_docker:
        try:
            result = subprocess.run(
                service.start_command,
                cwd=service.working_dir,
                capture_output=True,
                timeout=30,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    # Non-docker services: launch as background process
    log_file = open(service.log_file, "w") if service.log_file else subprocess.DEVNULL
    env = os.environ.copy()
    if service.name == "frontend":
        env["PORT"] = str(service.port)
    if service.name == "api":
        # Disable Uvicorn reload in background mode - StatReload blocks the event
        # loop on slow filesystems (WSL2 /mnt/* uses 9P protocol).
        env["API_RELOAD"] = "false"

    try:
        proc = subprocess.Popen(
            service.start_command,
            cwd=service.working_dir,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        if service.pid_file:
            Path(service.pid_file).write_text(str(proc.pid))
        return True
    except (FileNotFoundError, OSError):
        return False
    finally:
        if hasattr(log_file, "close") and log_file is not subprocess.DEVNULL:
            log_file.close()


def stop_service(service: ServiceDef) -> bool:
    """Stop a service. Returns True if stopped successfully."""
    if service.is_docker:
        try:
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=service.working_dir,
                capture_output=True,
                timeout=30,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    stopped = False

    # Try PID file first
    if service.pid_file:
        pid = read_pid_file(service.pid_file)
        if pid is not None:
            try:
                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        capture_output=True,
                        timeout=5,
                    )
                else:
                    os.kill(pid, 15)  # SIGTERM
                stopped = True
            except (ProcessLookupError, PermissionError):
                pass
        # Clean up PID file
        try:
            Path(service.pid_file).unlink(missing_ok=True)
        except OSError:
            pass

    # Also kill by pattern to catch orphaned processes
    for pattern in service.stop_patterns:
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/FI", f"WINDOWTITLE eq *{pattern}*"],
                    capture_output=True,
                    timeout=5,
                )
            else:
                subprocess.run(
                    ["pkill", "-f", pattern],
                    capture_output=True,
                    timeout=5,
                )
            stopped = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    time.sleep(1)
    return stopped or not is_service_running(service)


def cleanup_pid_files() -> list[str]:
    """Remove stale PID files. Returns list of cleaned files."""
    cleaned = []
    for pid_file in PID_DIR.glob("acm-ai-*.pid"):
        pid = read_pid_file(str(pid_file))
        if pid is None:
            pid_file.unlink(missing_ok=True)
            cleaned.append(str(pid_file))
    return cleaned
