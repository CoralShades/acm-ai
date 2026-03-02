"""Docker Desktop and container health checks."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class ContainerInfo:
    name: str
    state: str
    status: str
    uptime: str


def is_docker_desktop_running() -> bool:
    """Check if Docker Desktop / daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_container_health() -> list[ContainerInfo]:
    """Get health info for all project containers."""
    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "ps",
                "--format",
                "{{.Name}}\t{{.State}}\t{{.Status}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []

        containers = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            name = parts[0] if len(parts) > 0 else "unknown"
            state = parts[1] if len(parts) > 1 else "unknown"
            status = parts[2] if len(parts) > 2 else ""
            # Extract uptime from status like "Up 2 hours (healthy)"
            uptime = status if status else "-"
            containers.append(
                ContainerInfo(name=name, state=state, status=status, uptime=uptime)
            )
        return containers
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
