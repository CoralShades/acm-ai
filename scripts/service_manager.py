#!/usr/bin/env python3
"""ACM-AI Service Manager - unified CLI for starting, stopping, and monitoring services.

Usage:
    uv run python scripts/service_manager.py <command> [options]

Commands:
    start    Start all services with pre-flight checks
    stop     Stop all services with verification
    restart  Stop then start all services
    status   Show current service status
    health   Live-updating health dashboard (Ctrl+C to exit)
    fix      Fix port conflicts and stale PID files
    check    Pre-flight check (Docker, ports, dependencies)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add scripts dir to path for sibling module imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _health_monitor import (
    HAS_RICH,
    ServiceStatus,
    display_status_table,
    live_health_dashboard,
    poll_all_health,
)
from _port_utils import check_all_ports, is_port_in_use, kill_port_owner
from _process_utils import (
    cleanup_pid_files,
    is_docker_available,
    is_node_available,
    is_tmux_available,
    is_uv_available,
    start_service_background,
    stop_service,
)
from _service_config import SHUTDOWN_ORDER, STARTUP_ORDER, get_services

# Optional rich imports
try:
    from rich.console import Console

    console = Console()

    def _print(msg: str = "", **kwargs) -> None:
        console.print(msg, **kwargs)
except ImportError:

    def _print(msg: str = "", **kwargs) -> None:
        # Strip rich markup for plain output
        import re

        clean = re.sub(r"\[/?[^\]]+\]", "", msg)
        print(clean)


def _wait_for_service(svc: object, timeout: int = 60) -> bool:
    """Wait for a service to become healthy. Returns True if healthy within timeout."""
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        # Try HTTP health check first
        if svc.health_url:
            try:
                req = urllib.request.Request(svc.health_url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status < 400:
                        return True
            except Exception:
                pass
        # Fall back to port check
        elif svc.port:
            if is_port_in_use(svc.port):
                return True
        else:
            time.sleep(svc.startup_delay or 2)
            return True
        time.sleep(2)
    return False


def cmd_check(args: argparse.Namespace) -> int:
    """Pre-flight check: verify all dependencies are available."""
    services = get_services()
    all_ok = True

    _print("[bold]ACM-AI Pre-flight Check[/bold]")
    _print()

    # Docker
    docker_ok = is_docker_available()
    if docker_ok:
        _print("  [green]OK[/green]  Docker is running")
    else:
        _print("  [red]FAIL[/red]  Docker is not running - start Docker Desktop first")
        all_ok = False

    # uv
    if is_uv_available():
        _print("  [green]OK[/green]  uv is installed")
    else:
        _print("  [red]FAIL[/red]  uv is not installed")
        all_ok = False

    # Node/npm
    if is_node_available():
        _print("  [green]OK[/green]  npm is installed")
    else:
        _print("  [red]FAIL[/red]  npm is not installed")
        all_ok = False

    # tmux (optional)
    if is_tmux_available():
        _print("  [green]OK[/green]  tmux is available")
    else:
        _print("  [yellow]WARN[/yellow] tmux not found (optional, for tmux mode)")

    # rich (optional)
    if HAS_RICH:
        _print("  [green]OK[/green]  rich is installed (TUI enabled)")
    else:
        _print(
            "  [yellow]WARN[/yellow] rich not found (install for TUI: uv add rich --group dev)"
        )

    # Ports
    _print()
    _print("[bold]Port Availability[/bold]")
    conflicts = check_all_ports(services)
    for name in STARTUP_ORDER:
        svc = services[name]
        if svc.port is None:
            _print(f"  [green]OK[/green]  {svc.display_name} (no port)")
            continue
        conflict = conflicts.get(name)
        if conflict:
            _print(
                f"  [red]BUSY[/red] Port {svc.port} ({svc.display_name}) - "
                f"PID {conflict.pid} ({conflict.process_name})"
            )
            all_ok = False
        else:
            _print(f"  [green]FREE[/green] Port {svc.port} ({svc.display_name})")

    _print()
    if all_ok:
        _print("[green bold]All checks passed![/green bold]")
    else:
        _print("[red bold]Some checks failed. Fix issues before starting.[/red bold]")

    return 0 if all_ok else 1


def cmd_start(args: argparse.Namespace) -> int:
    """Start all services with pre-flight checks."""
    services = get_services()
    auto_fix = getattr(args, "auto_fix", False)

    _print("[bold]ACM-AI - Starting Services[/bold]")
    _print()

    # Pre-flight
    if not is_docker_available():
        _print("[red]Docker is not running. Start Docker Desktop first.[/red]")
        return 1

    # Check ports
    conflicts = check_all_ports(services)
    if conflicts:
        _print("[yellow]Port conflicts detected:[/yellow]")
        for name, conflict in conflicts.items():
            svc = services[name]
            _print(
                f"  Port {svc.port} ({svc.display_name}): "
                f"PID {conflict.pid} ({conflict.process_name})"
            )

        if auto_fix:
            _print()
            _print("[yellow]Auto-fixing port conflicts...[/yellow]")
            for name, conflict in conflicts.items():
                svc = services[name]
                if kill_port_owner(svc.port):
                    _print(f"  [green]Freed[/green] port {svc.port}")
                else:
                    _print(f"  [red]Failed[/red] to free port {svc.port}")
                    return 1
        else:
            _print()
            _print(
                "Run with --auto-fix to resolve, or stop conflicting processes manually."
            )
            return 1
        _print()

    # Clean stale PID files
    cleaned = cleanup_pid_files()
    if cleaned:
        _print(f"[dim]Cleaned {len(cleaned)} stale PID file(s)[/dim]")

    # Start services in order, waiting for each to be healthy before next
    for name in STARTUP_ORDER:
        svc = services[name]
        target_name = (
            args.service if hasattr(args, "service") and args.service else None
        )
        if target_name and target_name != name:
            continue

        _print(f"  Starting {svc.display_name}...", end="")

        if start_service_background(svc):
            _print(f" [green]launched[/green]")
        else:
            _print(f" [red]failed[/red]")
            return 1

        # Wait for service to be healthy (not just started)
        if svc.health_url or svc.port:
            _print(f"  Waiting for {svc.display_name} to be ready...", end="")
            healthy = _wait_for_service(svc, timeout=120)
            if healthy:
                _print(f" [green]ready[/green]")
            else:
                _print(f" [yellow]timeout (continuing)[/yellow]")
        elif svc.startup_delay:
            time.sleep(svc.startup_delay)

    # Post-startup health check
    _print()
    _print("[bold]Health Check[/bold]")
    statuses = poll_all_health(services)
    display_status_table(services, statuses)

    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    """Stop all services with verification."""
    services = get_services()

    _print("[bold]ACM-AI - Stopping Services[/bold]")
    _print()

    # Show current status
    statuses = poll_all_health(services)
    running = [n for n, s in statuses.items() if s != ServiceStatus.STOPPED]
    if not running:
        _print("[dim]No services are running.[/dim]")
        return 0

    # Stop in reverse order
    for name in SHUTDOWN_ORDER:
        svc = services[name]
        target_name = (
            args.service if hasattr(args, "service") and args.service else None
        )
        if target_name and target_name != name:
            continue

        status = statuses.get(name, ServiceStatus.STOPPED)
        if status == ServiceStatus.STOPPED:
            _print(f"  {svc.display_name}: [dim]already stopped[/dim]")
            continue

        _print(f"  Stopping {svc.display_name}...", end="")
        if stop_service(svc):
            _print(f" [green]stopped[/green]")
        else:
            _print(f" [yellow]may still be running[/yellow]")

    # Kill tmux session if exists
    import subprocess

    subprocess.run(
        ["tmux", "kill-session", "-t", "acm-ai"],
        capture_output=True,
        timeout=5,
    )

    # Clean PID files
    cleanup_pid_files()

    _print()
    _print("[bold]Verification[/bold]")
    statuses = poll_all_health(services)
    display_status_table(services, statuses)

    return 0


def cmd_restart(args: argparse.Namespace) -> int:
    """Restart all services."""
    ret = cmd_stop(args)
    if ret != 0:
        return ret
    _print()
    return cmd_start(args)


def cmd_status(args: argparse.Namespace) -> int:
    """Show current service status with detailed health information."""
    services = get_services()
    statuses = poll_all_health(services)
    conflicts = check_all_ports(services)

    # Try to get detailed health from API
    from _health_monitor import get_detailed_health

    detailed_health = get_detailed_health()

    display_status_table(services, statuses, conflicts, detailed_health)

    # Return non-zero if any service unhealthy
    from _health_monitor import ServiceStatus

    unhealthy = any(
        s in (ServiceStatus.UNHEALTHY, ServiceStatus.STOPPED) for s in statuses.values()
    )
    return 1 if unhealthy else 0


def cmd_health(args: argparse.Namespace) -> int:
    """Live health dashboard with detailed component health.

    Returns non-zero exit code if any component is unhealthy.
    """
    services = get_services()
    return live_health_dashboard(services)


def cmd_fix(args: argparse.Namespace) -> int:
    """Fix port conflicts and stale PID files."""
    services = get_services()
    auto_fix = getattr(args, "auto_fix", False)

    _print("[bold]ACM-AI - Fix Issues[/bold]")
    _print()

    # Stale PID files
    cleaned = cleanup_pid_files()
    if cleaned:
        _print(f"[green]Cleaned {len(cleaned)} stale PID file(s):[/green]")
        for f in cleaned:
            _print(f"  {f}")
    else:
        _print("[dim]No stale PID files found.[/dim]")

    _print()

    # Port conflicts
    conflicts = check_all_ports(services)
    if not conflicts:
        _print("[dim]No port conflicts detected.[/dim]")
        return 0

    _print("[yellow]Port conflicts found:[/yellow]")
    for name, conflict in conflicts.items():
        svc = services[name]
        _print(
            f"  Port {svc.port} ({svc.display_name}): "
            f"PID {conflict.pid} ({conflict.process_name})"
        )

    if auto_fix:
        _print()
        _print("Resolving conflicts...")
        for name, conflict in conflicts.items():
            svc = services[name]
            if kill_port_owner(svc.port):
                _print(f"  [green]Freed[/green] port {svc.port}")
            else:
                _print(f"  [red]Failed[/red] to free port {svc.port}")
    else:
        _print()
        _print("Run with --auto-fix to automatically resolve conflicts.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ACM-AI Service Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically fix port conflicts and other issues",
    )
    parser.add_argument(
        "--service",
        type=str,
        help="Target a specific service (surrealdb, api, worker, frontend)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    sub_start = subparsers.add_parser("start", help="Start all services")
    sub_start.add_argument("--auto-fix", action="store_true")
    sub_start.add_argument("--service", type=str)

    sub_stop = subparsers.add_parser("stop", help="Stop all services")
    sub_stop.add_argument("--service", type=str)

    sub_restart = subparsers.add_parser("restart", help="Restart all services")
    sub_restart.add_argument("--auto-fix", action="store_true")
    sub_restart.add_argument("--service", type=str)

    subparsers.add_parser("status", help="Show service status")
    subparsers.add_parser("health", help="Live health dashboard")

    sub_fix = subparsers.add_parser("fix", help="Fix issues")
    sub_fix.add_argument("--auto-fix", action="store_true")

    subparsers.add_parser("check", help="Pre-flight check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "status": cmd_status,
        "health": cmd_health,
        "fix": cmd_fix,
        "check": cmd_check,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
