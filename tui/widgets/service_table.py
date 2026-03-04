"""DataTable widget for service status display."""

from __future__ import annotations

from textual.widgets import DataTable

from tui.services.service_control import ServiceDef, ServiceStatus

STATUS_STYLES = {
    ServiceStatus.HEALTHY: ("OK", "green"),
    ServiceStatus.UNHEALTHY: ("FAIL", "red"),
    ServiceStatus.STARTING: ("..", "yellow"),
    ServiceStatus.STOPPED: ("--", "dim"),
}


class ServiceTable(DataTable):
    """Displays service health status as a table.

    IMPORTANT: Never fetches data itself — always receives pre-fetched
    data via update_from() to avoid blocking the UI thread.
    """

    def on_mount(self) -> None:
        self.add_columns("Service", "Status", "Port", "Info")
        self.cursor_type = "row"

    def update_from(
        self,
        services: dict[str, ServiceDef],
        statuses: dict[str, ServiceStatus],
    ) -> None:
        """Update table from pre-fetched data. Call on UI thread only."""
        self.clear()
        for name, svc in services.items():
            status = statuses.get(name, ServiceStatus.STOPPED)
            label, color = STATUS_STYLES.get(status, ("??", "white"))
            port_str = str(svc.port) if svc.port else "-"

            if status == ServiceStatus.HEALTHY and svc.health_url:
                info = svc.health_url
            elif svc.is_docker:
                info = "(docker)"
            else:
                info = "(process)"

            self.add_row(
                svc.display_name,
                f"[{color}]{label}[/{color}]",
                port_str,
                info,
                key=name,
            )
