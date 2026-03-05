"""Port conflict detection and resolution utilities."""

from __future__ import annotations

import os
import platform
import signal
import socket
import subprocess
import time
from dataclasses import dataclass


@dataclass
class PortConflict:
    """Information about a port conflict."""

    port: int
    pid: int | None
    process_name: str | None


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use via socket connection attempt."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _pid_exists(pid: int) -> bool:
    """Check if a process with the given PID actually exists."""
    if platform.system() == "Windows":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # tasklist returns "INFO: No tasks are running..." when PID not found
        return result.stdout.strip().startswith('"') and "INFO:" not in result.stdout
    else:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False


def _get_process_name(pid: int) -> str | None:
    """Get the process name for a PID. Returns None if not found."""
    if platform.system() == "Windows":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout.strip()
        if output.startswith('"') and "INFO:" not in output:
            return output.split(",")[0].strip('"')
        return None
    else:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "comm="],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or None


def _get_ghost_pids_on_port(port: int) -> set[int]:
    """Find PIDs in netstat LISTENING on a port that don't exist as processes."""
    ghost_pids: set[int] = set()
    if platform.system() != "Windows":
        return ghost_pids
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            local_addr = parts[1]
            if not local_addr.endswith(f":{port}"):
                continue
            if "LISTENING" not in line:
                continue
            try:
                pid = int(parts[-1])
            except (ValueError, IndexError):
                continue
            if pid == 0:
                continue
            if not _pid_exists(pid):
                ghost_pids.add(pid)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return ghost_pids


def find_port_owner(port: int) -> PortConflict | None:
    """Find the process using a given port."""
    if not is_port_in_use(port):
        return None

    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Two-pass: prefer LISTENING on local address, then any state
            for state_filter in ["LISTENING", None]:
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    local_addr = parts[1]
                    # Only match LOCAL address, not foreign address
                    if not local_addr.endswith(f":{port}"):
                        continue
                    if state_filter and state_filter not in line:
                        continue
                    try:
                        pid = int(parts[-1])
                    except (ValueError, IndexError):
                        continue
                    if pid == 0:
                        continue
                    # Skip ghost PIDs (process no longer exists)
                    if not _pid_exists(pid):
                        continue
                    name = _get_process_name(pid)
                    return PortConflict(port=port, pid=pid, process_name=name)
        else:
            # Linux/macOS - try lsof first, fall back to ss
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = int(result.stdout.strip().splitlines()[0])
                name = _get_process_name(pid)
                return PortConflict(port=port, pid=pid, process_name=name)
            # Fallback to ss
            result = subprocess.run(
                ["ss", "-tlnp", f"sport = :{port}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines()[1:]:
                    if f":{port}" in line:
                        if "pid=" in line:
                            pid_str = line.split("pid=")[1].split(",")[0]
                            pid = int(pid_str)
                            name_part = (
                                line.split('(("')[1].split('"')[0]
                                if '(("' in line
                                else None
                            )
                            return PortConflict(
                                port=port, pid=pid, process_name=name_part
                            )
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, IndexError):
        pass

    # Port is in use but no visible process found — likely orphaned multiprocessing
    # children that inherited the socket from a killed parent (ghost parent PID
    # shows in netstat but doesn't exist as a Windows process)
    return PortConflict(port=port, pid=None, process_name="orphaned (ghost parent PID)")


def _kill_orphaned_children(port: int) -> bool:
    """Kill orphaned multiprocessing children that inherited a socket.

    When taskkill /F kills a parent uvicorn process, its child multiprocessing
    workers can survive and inherit the LISTEN socket. The parent PID shows in
    netstat but doesn't exist as a Windows process. The children (visible as
    python.exe with 'spawn_main(parent_pid=<ghost>)') still serve requests.

    This function finds ghost parent PIDs from netstat, then kills their children.
    Only kills children of DEAD parents to avoid killing legitimate workers.
    """
    if platform.system() != "Windows":
        return False

    ghost_pids = _get_ghost_pids_on_port(port)
    if not ghost_pids:
        return False

    killed = False
    for ghost_pid in ghost_pids:
        try:
            result = subprocess.run(
                [
                    "wmic",
                    "process",
                    "where",
                    f"ParentProcessId={ghost_pid}",
                    "get",
                    "ProcessId",
                    "/format:csv",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or "ProcessId" in line or "Node" in line:
                    continue
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if part.isdigit():
                        child_pid = int(part)
                        subprocess.run(
                            ["taskkill", "/F", "/PID", str(child_pid)],
                            capture_output=True,
                            timeout=5,
                        )
                        killed = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return killed


def _try_wsl_kill(port: int) -> bool:
    """Attempt to kill processes inside WSL2 that are using a port.

    On Windows with WSL2, processes running inside the Linux VM can bind to
    ports visible on Windows localhost, but their PIDs are invisible to Windows
    process tools. This function tries to kill them via WSL commands.
    """
    if platform.system() != "Windows":
        return False

    kill_patterns = {
        5055: ["run_api", "uvicorn.*5055"],
        8502: ["next.*dev", "node.*8502"],
    }

    patterns = kill_patterns.get(port, [])
    killed = False

    for pattern in patterns:
        try:
            result = subprocess.run(
                ["wsl", "--", "pkill", "-9", "-f", pattern],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                killed = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    try:
        subprocess.run(
            ["wsl", "--", "fuser", "-k", f"{port}/tcp"],
            capture_output=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return killed


def kill_port_owner(port: int, force: bool = True) -> bool:
    """Kill the process using a port. Returns True if port becomes free.

    Handles three scenarios on Windows:
    1. Normal Windows process — killed via taskkill
    2. Orphaned multiprocessing children — parent PID is dead but children
       inherited the LISTEN socket and still serve requests
    3. WSL2 process — PIDs invisible to Windows, killed via wsl pkill

    Args:
        port: The port number to free.
        force: Always force-kill on Windows (/F flag). On Unix, use SIGKILL vs SIGTERM.
    """
    if not is_port_in_use(port):
        return True

    # Step 1: Try to find and kill a visible Windows process
    conflict = find_port_owner(port)
    if conflict and conflict.pid:
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(conflict.pid)],
                    capture_output=True,
                    timeout=5,
                )
            else:
                sig = signal.SIGKILL if force else signal.SIGTERM
                os.kill(conflict.pid, sig)

            for _ in range(3):
                time.sleep(1)
                if not is_port_in_use(port):
                    return True
        except (ProcessLookupError, PermissionError, subprocess.TimeoutExpired):
            pass

    # Step 2: Kill orphaned multiprocessing children (ghost parent PIDs)
    if platform.system() == "Windows" and is_port_in_use(port):
        _kill_orphaned_children(port)
        for _ in range(5):
            time.sleep(1)
            if not is_port_in_use(port):
                return True

    # Step 3: Try WSL2 kill as last resort
    if platform.system() == "Windows" and is_port_in_use(port):
        _try_wsl_kill(port)
        for _ in range(3):
            time.sleep(1)
            if not is_port_in_use(port):
                return True

    return not is_port_in_use(port)


def check_all_ports(
    services: dict,
) -> dict[str, PortConflict | None]:
    """Check all service ports for conflicts. Returns dict of service_name -> conflict."""
    conflicts = {}
    for name, svc in services.items():
        if svc.port:
            conflict = find_port_owner(svc.port)
            if conflict:
                conflicts[name] = conflict
    return conflicts
