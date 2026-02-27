"""Package audit tab — checks installed packages and their status."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from tui.services.package_audit import audit_packages

STATUS_COLORS = {
    "OK": "green",
    "WARN": "yellow",
    "MISSING": "red",
    "ERROR": "red",
}


class PackagesScreen(Vertical):
    """Displays package audit results in a DataTable."""

    def compose(self) -> ComposeResult:
        yield Static("[bold]Package Audit[/bold]  [dim](R to refresh)[/dim]", classes="section-header")
        yield DataTable(id="pkg-table")

    def on_mount(self) -> None:
        table = self.query_one("#pkg-table", DataTable)
        table.add_columns("Package", "Version", "Status", "Notes")
        table.cursor_type = "row"
        self.refresh_packages()

    def refresh_packages(self) -> None:
        self.app.run_worker(self._do_audit, thread=True)

    async def _do_audit(self) -> None:
        results = audit_packages()
        table = self.query_one("#pkg-table", DataTable)
        self.app.call_from_thread(table.clear)
        for r in results:
            color = STATUS_COLORS.get(r.status, "white")
            self.app.call_from_thread(
                table.add_row,
                r.name,
                r.version,
                f"[{color}]{r.status}[/{color}]",
                r.notes,
            )
