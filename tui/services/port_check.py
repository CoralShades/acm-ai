"""Port conflict detection — delegates to scripts/_port_utils.py."""

from __future__ import annotations

from dataclasses import dataclass

from tui.config import API_PORT, FRONTEND_PORT, SURREAL_PORT
from tui.services.service_control import (
    PortConflict,
    find_port_owner,
    is_port_in_use,
)


@dataclass
class PortStatus:
    port: int
    label: str
    in_use: bool
    conflict: PortConflict | None


def check_project_ports() -> list[PortStatus]:
    """Check all ACM-AI project ports for status and conflicts."""
    ports = [
        (SURREAL_PORT, "SurrealDB"),
        (API_PORT, "API Server"),
        (FRONTEND_PORT, "Frontend"),
    ]
    results = []
    for port, label in ports:
        in_use = is_port_in_use(port)
        conflict = find_port_owner(port) if in_use else None
        results.append(PortStatus(port=port, label=label, in_use=in_use, conflict=conflict))
    return results
