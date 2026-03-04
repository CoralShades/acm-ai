"""Extraction/Jobs tab — ACM stats, active jobs, export and re-embed actions."""

from __future__ import annotations

import threading

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from tui.services.extraction_check import (
    cancel_job,
    get_acm_stats,
    list_jobs,
    submit_rebuild_embeddings,
    trigger_export,
    trigger_reembed,
)
from tui.widgets.confirm_modal import ConfirmScreen


class ExtractionScreen(Vertical):
    """ACM extraction job management, stats, and export actions."""

    _refresh_lock = threading.Lock()

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]Extraction & Jobs[/bold]  [dim](R to refresh)[/dim]",
            classes="section-header",
        )
        yield Static("[bold]ACM Statistics[/bold]", classes="section-header")
        yield Static(id="extraction-stats", classes="info-panel")

        yield Static("[bold]Active Jobs[/bold]", classes="section-header")
        yield DataTable(id="jobs-table")

        yield Static("[bold]Actions[/bold]", classes="section-header")
        with Horizontal(classes="action-bar"):
            yield Button("Export CSV", id="ext-export-csv", variant="primary")
            yield Button("Export Excel", id="ext-export-excel", variant="primary")
            yield Button("Re-embed All", id="ext-reembed", variant="warning")
            yield Button(
                "Rebuild Embeddings", id="ext-rebuild", variant="warning"
            )

    def on_mount(self) -> None:
        table = self.query_one("#jobs-table", DataTable)
        table.add_columns("Job ID", "Command", "Status", "Source", "Created")
        table.cursor_type = "row"
        self.query_one("#extraction-stats", Static).update("[dim]Loading...[/dim]")
        self.refresh_extraction()

    def refresh_extraction(self) -> None:
        """Schedule a background refresh."""
        if not self._refresh_lock.acquire(blocking=False):
            return
        self.app.run_worker(self._do_refresh, thread=True)

    async def _do_refresh(self) -> None:
        """Fetch stats and jobs in worker thread."""
        try:
            stats = get_acm_stats()
            jobs = list_jobs()

            # Build stats text
            if stats.error:
                stats_text = f"  [yellow]API unavailable: {stats.error}[/yellow]"
            else:
                stats_text = (
                    f"  Total Records:  {stats.total_records:,}\n"
                    f"  Buildings:      {stats.building_count:,}\n"
                    f"  Rooms:          {stats.room_count:,}\n"
                    f"  Risk: [red]High={stats.high_risk}[/red]  "
                    f"[yellow]Medium={stats.medium_risk}[/yellow]  "
                    f"[green]Low={stats.low_risk}[/green]"
                )

            self.app.call_from_thread(self._apply_update, stats_text, jobs)
        finally:
            self._refresh_lock.release()

    def _apply_update(self, stats_text: str, jobs: list) -> None:
        """Apply data to widgets on UI thread."""
        self.query_one("#extraction-stats", Static).update(stats_text)
        table = self.query_one("#jobs-table", DataTable)
        table.clear()
        for job in jobs:
            # Truncate long IDs for display
            short_id = job.job_id
            if len(short_id) > 12:
                short_id = short_id[:12] + ".."
            status_color = {
                "running": "green",
                "pending": "yellow",
                "completed": "dim",
                "failed": "red",
                "cancelled": "dim",
            }.get(job.status, "white")
            table.add_row(
                short_id,
                job.command,
                f"[{status_color}]{job.status}[/{status_color}]",
                job.source or "-",
                job.created_at[:19] if job.created_at else "-",
                key=job.job_id,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn == "ext-export-csv":
            self.app.run_worker(lambda: self._do_export("csv"), thread=True)
        elif btn == "ext-export-excel":
            self.app.run_worker(lambda: self._do_export("excel"), thread=True)
        elif btn == "ext-reembed":
            self._confirm_action(
                "Re-embed all sources and notes?", self._do_reembed
            )
        elif btn == "ext-rebuild":
            self._confirm_action(
                "Rebuild all embeddings? This may take a while.",
                self._do_rebuild,
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Allow cancelling a job by selecting its row."""
        if event.row_key and event.row_key.value:
            job_id = str(event.row_key.value)
            self._confirm_action(
                f"Cancel job {job_id}?",
                lambda: self._do_cancel(job_id),
            )

    def _confirm_action(self, message: str, action: object) -> None:
        """Show confirm modal, then run action if confirmed."""

        def callback(confirmed: bool | None) -> None:
            if confirmed:
                self.app.run_worker(action, thread=True)

        self.app.push_screen(ConfirmScreen(message), callback)

    def _do_export(self, fmt: str) -> None:
        self.app.call_from_thread(self.app.notify, f"Exporting {fmt.upper()}...")
        ok, msg = trigger_export(fmt)
        severity = "information" if ok else "error"
        self.app.call_from_thread(self.app.notify, msg, severity=severity)

    def _do_reembed(self) -> None:
        self.app.call_from_thread(self.app.notify, "Submitting re-embed job...")
        ok, msg = trigger_reembed()
        severity = "information" if ok else "error"
        self.app.call_from_thread(self.app.notify, msg, severity=severity)
        self.app.call_from_thread(self.refresh_extraction)

    def _do_rebuild(self) -> None:
        self.app.call_from_thread(
            self.app.notify, "Submitting rebuild embeddings job..."
        )
        ok, msg = submit_rebuild_embeddings()
        severity = "information" if ok else "error"
        self.app.call_from_thread(self.app.notify, msg, severity=severity)
        self.app.call_from_thread(self.refresh_extraction)

    def _do_cancel(self, job_id: str) -> None:
        self.app.call_from_thread(self.app.notify, f"Cancelling {job_id}...")
        ok, msg = cancel_job(job_id)
        severity = "information" if ok else "error"
        self.app.call_from_thread(self.app.notify, msg, severity=severity)
        self.app.call_from_thread(self.refresh_extraction)
