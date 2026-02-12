"""Health monitoring and TUI display for ACM-AI services."""

from __future__ import annotations

import sys
import time
import urllib.request
from enum import Enum

from _port_utils import PortConflict, check_all_ports, is_port_in_use
from _process_utils import is_service_running
from _service_config import ServiceDef

# Try to import rich for TUI display
try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class ServiceStatus(Enum):
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    STARTING = "STARTING"
    STOPPED = "STOPPED"


def check_health(service: ServiceDef) -> ServiceStatus:
    """Check health of a single service."""
    if service.is_docker:
        if is_service_running(service):
            # Also check port if available
            if service.port and is_port_in_use(service.port):
                return ServiceStatus.HEALTHY
            elif service.port:
                return ServiceStatus.STARTING
            return ServiceStatus.HEALTHY
        return ServiceStatus.STOPPED

    if not is_service_running(service):
        return ServiceStatus.STOPPED

    # For services with health URLs, do an HTTP check
    if service.health_url:
        try:
            req = urllib.request.Request(service.health_url, method="GET")
            with urllib.request.urlopen(req, timeout=service.health_timeout) as resp:
                if resp.status < 400:
                    return ServiceStatus.HEALTHY
                return ServiceStatus.UNHEALTHY
        except Exception:
            # Process exists but HTTP not ready yet
            return ServiceStatus.STARTING

    # No health URL but process is running (e.g., worker)
    return ServiceStatus.HEALTHY


def poll_all_health(
    services: dict[str, ServiceDef],
) -> dict[str, ServiceStatus]:
    """Check health of all services."""
    return {name: check_health(svc) for name, svc in services.items()}


# --- Rich TUI display ---


def _status_color(status: ServiceStatus) -> str:
    colors = {
        ServiceStatus.HEALTHY: "green",
        ServiceStatus.UNHEALTHY: "red",
        ServiceStatus.STARTING: "yellow",
        ServiceStatus.STOPPED: "dim",
    }
    return colors.get(status, "white")


def _status_icon(status: ServiceStatus) -> str:
    icons = {
        ServiceStatus.HEALTHY: "[green]OK[/green]",
        ServiceStatus.UNHEALTHY: "[red]!![/red]",
        ServiceStatus.STARTING: "[yellow]..[/yellow]",
        ServiceStatus.STOPPED: "[dim]--[/dim]",
    }
    return icons.get(status, "??")


def _build_status_table(
    services: dict[str, ServiceDef],
    statuses: dict[str, ServiceStatus],
    conflicts: dict[str, PortConflict | None] | None = None,
) -> Table:
    """Build a rich Table showing service status."""
    table = Table(title="ACM-AI Service Status", show_lines=True)
    table.add_column("Service", style="bold", min_width=18)
    table.add_column("Status", min_width=10, justify="center")
    table.add_column("Port", min_width=6, justify="center")
    table.add_column("Info", min_width=20)

    for name, svc in services.items():
        status = statuses.get(name, ServiceStatus.STOPPED)
        color = _status_color(status)
        port_str = str(svc.port) if svc.port else "-"
        info = ""

        if svc.health_url:
            info = svc.health_url
        elif svc.is_docker:
            info = "(docker)"
        else:
            info = "(process check)"

        conflict = (conflicts or {}).get(name)
        if conflict and status == ServiceStatus.STOPPED:
            info = f"[red]PORT CONFLICT: PID {conflict.pid} ({conflict.process_name})[/red]"

        table.add_row(
            svc.display_name,
            f"[{color}]{status.value}[/{color}]",
            port_str,
            info,
        )

    return table


def display_status_table(
    services: dict[str, ServiceDef],
    statuses: dict[str, ServiceStatus],
    conflicts: dict[str, PortConflict | None] | None = None,
) -> None:
    """Display service status using rich or ANSI fallback."""
    if HAS_RICH:
        console = Console()
        table = _build_status_table(services, statuses, conflicts)
        console.print(table)
        console.print()

        # Print access URLs
        for name, svc in services.items():
            if svc.port and statuses.get(name) in (
                ServiceStatus.HEALTHY,
                ServiceStatus.STARTING,
            ):
                if name == "frontend":
                    console.print(f"  Frontend:  http://localhost:{svc.port}")
                elif name == "api":
                    console.print(f"  API:       http://localhost:{svc.port}")
                    console.print(f"  API Docs:  http://localhost:{svc.port}/docs")
        console.print()
    else:
        _display_ansi_fallback(services, statuses, conflicts)


def _display_ansi_fallback(
    services: dict[str, ServiceDef],
    statuses: dict[str, ServiceStatus],
    conflicts: dict[str, PortConflict | None] | None = None,
) -> None:
    """ANSI color fallback when rich is not available."""
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    ansi_colors = {
        ServiceStatus.HEALTHY: GREEN,
        ServiceStatus.UNHEALTHY: RED,
        ServiceStatus.STARTING: YELLOW,
        ServiceStatus.STOPPED: DIM,
    }

    ansi_icons = {
        ServiceStatus.HEALTHY: "OK",
        ServiceStatus.UNHEALTHY: "!!",
        ServiceStatus.STARTING: "..",
        ServiceStatus.STOPPED: "--",
    }

    print("=" * 50)
    print(f"  {BOLD}ACM-AI Service Status{RESET}")
    print("=" * 50)

    for name, svc in services.items():
        status = statuses.get(name, ServiceStatus.STOPPED)
        color = ansi_colors.get(status, "")
        icon = ansi_icons.get(status, "??")
        port_str = str(svc.port) if svc.port else "-"

        conflict = (conflicts or {}).get(name)
        extra = ""
        if conflict and status == ServiceStatus.STOPPED:
            extra = f" {RED}PORT CONFLICT: PID {conflict.pid}{RESET}"

        print(
            f"  {svc.display_name:<20} [{color}{icon}{RESET}] {color}{status.value:<10}{RESET} {port_str}{extra}"
        )

    print("=" * 50)
    print()


def live_health_dashboard(services: dict[str, ServiceDef]) -> None:
    """Live-updating health dashboard using rich.Live."""
    if not HAS_RICH:
        print("Live dashboard requires 'rich' library.")
        print("Install with: uv add rich --group dev")
        print()
        print("Falling back to periodic status display (Ctrl+C to exit)...")
        print()
        try:
            while True:
                statuses = poll_all_health(services)
                conflicts = check_all_ports(services)
                _display_ansi_fallback(services, statuses, conflicts)
                time.sleep(3)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")
        return

    console = Console()
    console.print("[bold]ACM-AI Health Dashboard[/bold] (Ctrl+C to exit)\n")

    try:
        with Live(
            _build_status_table(services, poll_all_health(services)),
            console=console,
            refresh_per_second=0.5,
        ) as live:
            while True:
                statuses = poll_all_health(services)
                conflicts = check_all_ports(services)
                live.update(_build_status_table(services, statuses, conflicts))
                time.sleep(2)
    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard stopped.[/dim]")
