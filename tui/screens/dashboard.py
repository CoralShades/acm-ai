"""Dashboard tab — interactive service controls, ports, docker, URLs.

Performance: ALL subprocess/network calls happen in a worker thread.
A refresh guard prevents overlapping workers from piling up.
The UI thread only receives pre-fetched data and updates widgets.
"""

from __future__ import annotations

import subprocess
import threading

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from tui.config import (
    API_PORT,
    DASHBOARD_REFRESH_SECONDS,
    FRONTEND_PORT,
    PROJECT_ROOT,
)
from tui.services.docker_check import get_container_health, is_docker_desktop_running
from tui.services.log_parser import get_last_extraction
from tui.services.port_check import PortStatus, check_project_ports
from tui.services.service_control import (
    ServiceDef,
    ServiceStatus,
    get_services,
    is_service_running,
    kill_port_owner,
    poll_all_health,
    start_service_background,
    stop_service,
)
from tui.widgets.confirm_modal import ConfirmScreen
from tui.widgets.extraction_summary import ExtractionSummaryWidget

STATUS_STYLES = {
    ServiceStatus.HEALTHY: ("OK", "green"),
    ServiceStatus.UNHEALTHY: ("FAIL", "red"),
    ServiceStatus.STARTING: ("..", "yellow"),
    ServiceStatus.STOPPED: ("--", "dim"),
}


def _build_svc_row(
    name: str, svc: ServiceDef, status: ServiceStatus
) -> Horizontal:
    """Build a service row with status label and action buttons."""
    label, color = STATUS_STYLES.get(status, ("??", "white"))
    port_str = f":{svc.port}" if svc.port else ""

    children = [
        Static(
            f"  {svc.display_name}  [{color}]{label}[/{color}]  {port_str}",
            classes="svc-label",
        )
    ]
    if status in (
        ServiceStatus.HEALTHY,
        ServiceStatus.STARTING,
        ServiceStatus.UNHEALTHY,
    ):
        children.append(Button("Stop", id=f"svc-{name}-stop", variant="error"))
        children.append(
            Button("Restart", id=f"svc-{name}-restart", variant="warning")
        )
    else:
        children.append(
            Button("Start", id=f"svc-{name}-start", variant="success")
        )
    return Horizontal(*children, classes="svc-row")


def _build_port_row(ps: PortStatus) -> Horizontal:
    """Build a port status row with optional Kill button."""
    children = []
    if ps.in_use:
        owner = ""
        if ps.conflict and ps.conflict.process_name:
            owner = f" ({ps.conflict.process_name}, PID {ps.conflict.pid})"
        children.append(
            Static(
                f"  [green]:{ps.port}[/green] {ps.label} — in use{owner}",
                classes="svc-label",
            )
        )
        children.append(
            Button("Kill", id=f"port-kill-{ps.port}", variant="error")
        )
    else:
        children.append(
            Static(
                f"  [dim]:{ps.port}[/dim] {ps.label} — free",
                classes="svc-label",
            )
        )
    return Horizontal(*children, classes="port-row")


def _build_docker_row(container_info) -> Horizontal:
    """Build a Docker container row with Restart button."""
    color = "green" if container_info.state == "running" else "red"
    docker_svc = container_info.name.replace("acm-ai-", "")
    return Horizontal(
        Static(
            f"  [{color}]{container_info.name}[/{color}]: {container_info.status}",
            classes="svc-label",
        ),
        Button("Restart", id=f"docker-restart-{docker_svc}", variant="warning"),
        classes="svc-row",
    )


class DashboardScreen(Vertical):
    """Main dashboard with per-service controls, port kill, and Docker management."""

    _refresh_lock = threading.Lock()
    _services: dict[str, ServiceDef] = {}
    _statuses: dict[str, ServiceStatus] = {}
    _ports: list[PortStatus] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="dashboard-columns"):
            with Vertical(id="dashboard-left", classes="column-left"):
                yield Static("[bold]Services[/bold]", classes="section-header")
                yield Vertical(id="svc-rows")
                yield Static("[bold]Ports[/bold]", classes="section-header")
                yield Vertical(id="port-rows")
            with Vertical(id="dashboard-right", classes="column-right"):
                yield Static("[bold]Docker[/bold]", classes="section-header")
                yield Vertical(id="docker-rows")
                yield Static(
                    "[bold]Last Extraction[/bold]", classes="section-header"
                )
                yield ExtractionSummaryWidget(
                    id="extraction-summary", classes="info-panel"
                )
                yield Static("[bold]Access URLs[/bold]", classes="section-header")
                yield Static(id="url-info", classes="info-panel")

    def on_mount(self) -> None:
        self.query_one("#url-info", Static).update("[dim]Checking...[/dim]")
        self.refresh_all()
        self.set_interval(DASHBOARD_REFRESH_SECONDS, self.refresh_all)

    def refresh_all(self) -> None:
        """Schedule a background refresh. Skips if one is already running."""
        if not self._refresh_lock.acquire(blocking=False):
            return
        self.app.run_worker(self._do_refresh, thread=True)

    async def _do_refresh(self) -> None:
        """Fetch ALL data in worker thread, then batch-update UI."""
        try:
            services = get_services()
            statuses = poll_all_health(services)
            ports = check_project_ports()
            docker_running = is_docker_desktop_running()
            containers = get_container_health() if docker_running else []
            summary = get_last_extraction()

            # URLs
            api_up = statuses.get("api") in (
                ServiceStatus.HEALTHY,
                ServiceStatus.STARTING,
            )
            fe_up = statuses.get("frontend") in (
                ServiceStatus.HEALTHY,
                ServiceStatus.STARTING,
            )
            url_lines = []
            if fe_up:
                url_lines.append(
                    f"  Frontend:  [link]http://localhost:{FRONTEND_PORT}[/link]"
                )
            if api_up:
                url_lines.append(
                    f"  API:       [link]http://localhost:{API_PORT}[/link]"
                )
                url_lines.append(
                    f"  API Docs:  [link]http://localhost:{API_PORT}/docs[/link]"
                )
            url_text = (
                "\n".join(url_lines)
                if url_lines
                else "[dim]No services running[/dim]"
            )

            self.app.call_from_thread(
                self._apply_ui_update,
                services,
                statuses,
                ports,
                docker_running,
                containers,
                url_text,
                summary,
            )
        finally:
            self._refresh_lock.release()

    def _apply_ui_update(
        self,
        services,
        statuses,
        ports,
        docker_running,
        containers,
        url_text: str,
        summary,
    ) -> None:
        """Rebuild interactive widgets on UI thread."""
        self._services = services
        self._statuses = statuses
        self._ports = ports

        # --- Service rows ---
        svc_container = self.query_one("#svc-rows", Vertical)
        svc_container.remove_children()
        for name, svc in services.items():
            status = statuses.get(name, ServiceStatus.STOPPED)
            svc_container.mount(_build_svc_row(name, svc, status))

        # --- Port rows ---
        port_container = self.query_one("#port-rows", Vertical)
        port_container.remove_children()
        for ps in ports:
            port_container.mount(_build_port_row(ps))

        # --- Docker rows ---
        docker_container = self.query_one("#docker-rows", Vertical)
        docker_container.remove_children()
        desktop_status = (
            "[green]Running[/green]"
            if docker_running
            else "[red]Stopped[/red]"
        )
        docker_container.mount(
            Static(f"  Desktop: {desktop_status}", classes="info-panel")
        )
        for c in containers:
            docker_container.mount(_build_docker_row(c))

        # --- URLs and extraction ---
        self.query_one("#url-info", Static).update(url_text)
        self.query_one(
            "#extraction-summary", ExtractionSummaryWidget
        ).update_summary(summary)

    # --- Button handlers ---

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""

        # Service start/stop/restart
        if btn_id.startswith("svc-") and btn_id.endswith("-start"):
            name = btn_id[4:-6]  # strip "svc-" and "-start"
            svc = self._services.get(name)
            if svc:
                self.app.run_worker(
                    lambda s=svc: self._start_service(s), thread=True
                )

        elif btn_id.startswith("svc-") and btn_id.endswith("-stop"):
            name = btn_id[4:-5]  # strip "svc-" and "-stop"
            svc = self._services.get(name)
            if svc:
                self._confirm_and_run(
                    f"Stop {svc.display_name}?",
                    lambda s=svc: self._stop_service(s),
                )

        elif btn_id.startswith("svc-") and btn_id.endswith("-restart"):
            name = btn_id[4:-8]  # strip "svc-" and "-restart"
            svc = self._services.get(name)
            if svc:
                self._confirm_and_run(
                    f"Restart {svc.display_name}?",
                    lambda s=svc: self._restart_service(s),
                )

        # Port kill
        elif btn_id.startswith("port-kill-"):
            port = int(btn_id[10:])  # strip "port-kill-"
            # Find port info for display
            ps = next((p for p in self._ports if p.port == port), None)
            owner_info = ""
            if ps and ps.conflict and ps.conflict.process_name:
                owner_info = f" ({ps.conflict.process_name}, PID {ps.conflict.pid})"
            self._confirm_and_run(
                f"Kill process on port {port}{owner_info}?",
                lambda p=port: self._kill_port(p),
            )

        # Docker container restart
        elif btn_id.startswith("docker-restart-"):
            docker_svc = btn_id[15:]  # strip "docker-restart-"
            self._confirm_and_run(
                f"Restart Docker container {docker_svc}?",
                lambda ds=docker_svc: self._restart_docker(ds),
            )

    def _confirm_and_run(self, message: str, action: object) -> None:
        """Show confirm modal, then run action in worker thread if confirmed."""

        def callback(confirmed: bool | None) -> None:
            if confirmed:
                self.app.run_worker(action, thread=True)

        self.app.push_screen(ConfirmScreen(message), callback)

    # --- Worker thread actions ---

    def _start_service(self, svc: ServiceDef) -> None:
        self.app.call_from_thread(
            self.app.notify, f"Starting {svc.display_name}..."
        )
        ok = start_service_background(svc)
        if ok:
            self.app.call_from_thread(
                self.app.notify,
                f"{svc.display_name} started",
                severity="information",
            )
        else:
            self.app.call_from_thread(
                self.app.notify,
                f"Failed to start {svc.display_name}",
                severity="error",
            )
        self.app.call_from_thread(self.refresh_all)

    def _stop_service(self, svc: ServiceDef) -> None:
        self.app.call_from_thread(
            self.app.notify, f"Stopping {svc.display_name}..."
        )
        stop_service(svc)
        self.app.call_from_thread(
            self.app.notify,
            f"{svc.display_name} stopped",
            severity="information",
        )
        self.app.call_from_thread(self.refresh_all)

    def _restart_service(self, svc: ServiceDef) -> None:
        self.app.call_from_thread(
            self.app.notify, f"Restarting {svc.display_name}..."
        )
        if is_service_running(svc):
            stop_service(svc)
        start_service_background(svc)
        self.app.call_from_thread(
            self.app.notify,
            f"{svc.display_name} restarted",
            severity="information",
        )
        self.app.call_from_thread(self.refresh_all)

    def _kill_port(self, port: int) -> None:
        self.app.call_from_thread(
            self.app.notify, f"Killing process on port {port}..."
        )
        ok = kill_port_owner(port, force=True)
        if ok:
            self.app.call_from_thread(
                self.app.notify,
                f"Port {port} freed",
                severity="information",
            )
        else:
            self.app.call_from_thread(
                self.app.notify,
                f"Failed to free port {port}",
                severity="error",
            )
        self.app.call_from_thread(self.refresh_all)

    def _restart_docker(self, service_name: str) -> None:
        self.app.call_from_thread(
            self.app.notify, f"Restarting Docker container {service_name}..."
        )
        try:
            result = subprocess.run(
                ["docker", "compose", "restart", service_name],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=30,
            )
            if result.returncode == 0:
                self.app.call_from_thread(
                    self.app.notify,
                    f"Container {service_name} restarted",
                    severity="information",
                )
            else:
                self.app.call_from_thread(
                    self.app.notify,
                    f"Failed to restart {service_name}: {result.stderr.strip()}",
                    severity="error",
                )
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.app.call_from_thread(
                self.app.notify,
                f"Docker error: {e}",
                severity="error",
            )
        self.app.call_from_thread(self.refresh_all)
