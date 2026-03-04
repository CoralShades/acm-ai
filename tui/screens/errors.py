"""Error aggregation tab — scans logs for ERROR/WARNING/CRITICAL/FAIL."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, RichLog, Static

from tui.services.log_parser import group_errors, scan_errors


class ErrorsScreen(Vertical):
    """Error aggregation view with summary table and detail log."""

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]Error Summary[/bold]  [dim](last 24h, R to refresh)[/dim]",
            classes="section-header",
        )
        yield DataTable(id="error-summary-table")
        yield Static("[bold]Error Details[/bold]", classes="section-header")
        yield RichLog(id="error-details", highlight=True, markup=False, wrap=True)

    def on_mount(self) -> None:
        table = self.query_one("#error-summary-table", DataTable)
        table.add_columns("File", "Count", "Last Seen", "Sample")
        table.cursor_type = "row"
        self.refresh_errors()

    def refresh_errors(self) -> None:
        self.app.run_worker(self._do_scan, thread=True)

    async def _do_scan(self) -> None:
        entries = scan_errors(hours=24)
        groups = group_errors(entries)

        # Update summary table
        table = self.query_one("#error-summary-table", DataTable)
        self.app.call_from_thread(table.clear)
        for g in groups:
            self.app.call_from_thread(
                table.add_row,
                g.file,
                str(g.count),
                g.last_occurrence,
                g.sample_message[:80],
            )

        # Update detail log
        detail_log = self.query_one("#error-details", RichLog)
        self.app.call_from_thread(detail_log.clear)
        for e in entries[:200]:  # limit to 200 entries
            self.app.call_from_thread(
                detail_log.write,
                f"[{e.timestamp}] [{e.level}] {e.file}:{e.line_number} — {e.message}",
            )

        if not entries:
            self.app.call_from_thread(detail_log.write, "No errors found in the last 24 hours.")
