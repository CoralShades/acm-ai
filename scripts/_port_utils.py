"""Port conflict detection and resolution utilities."""

from __future__ import annotations

import os
import platform
import signal
import socket
import subprocess
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
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = int(parts[-1])
                    # Get process name
                    name_result = subprocess.run(
                        [
                            "tasklist",
                            "/FI",
                            f"PID eq {pid}",
                            "/FO",
                            "CSV",
                            "/NH",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    name = name_result.stdout.strip().split(",")[0].strip('"')
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
                # Get process name
                name_result = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "comm="],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                name = name_result.stdout.strip() or None
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
                        # Extract pid from users:(("name",pid=123,fd=4))
                        if "pid=" in line:
                            pid_str = line.split("pid=")[1].split(",")[0]
                            pid = int(pid_str)
                            name_part = line.split('(("')[1].split('"')[0] if '(("' in line else None
                            return PortConflict(
                                port=port, pid=pid, process_name=name_part
                            )
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, IndexError):
        pass

    # Port is in use but we can't identify the owner
    return PortConflict(port=port, pid=None, process_name=None)


def kill_port_owner(port: int, force: bool = False) -> bool:
    """Kill the process using a port. Returns True if successfully killed."""
    conflict = find_port_owner(port)
    if not conflict or not conflict.pid:
        return not is_port_in_use(port)

    try:
        if platform.system() == "Windows":
            flag = "/F" if force else ""
            subprocess.run(
                ["taskkill", flag, "/PID", str(conflict.pid)],
                capture_output=True,
                timeout=5,
            )
        else:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(conflict.pid, sig)

        # Verify port is freed (give it a moment)
        import time

        time.sleep(1)
        return not is_port_in_use(port)
    except (ProcessLookupError, PermissionError, subprocess.TimeoutExpired):
        return False


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
