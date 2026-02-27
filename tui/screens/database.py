"""Database tab — SurrealDB connection status, table counts, migrations."""

from __future__ import annotations

import threading

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from tui.services.database_check import (
    get_db_status,
    get_migration_status,
    get_table_counts,
    run_migrations,
)


class DatabaseScreen(Vertical):
    """SurrealDB database status, record counts, and migration management."""

    _refresh_lock = threading.Lock()

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]Database[/bold]  [dim](R to refresh)[/dim]",
            classes="section-header",
        )
        with Horizontal(id="db-columns"):
            with Vertical(classes="column-left"):
                yield Static("[bold]SurrealDB Connection[/bold]", classes="section-header")
                yield Static(id="db-connection", classes="info-panel")
                yield Static("[bold]Migrations[/bold]", classes="section-header")
                yield Static(id="db-migrations", classes="info-panel")
                with Horizontal(classes="button-row"):
                    yield Button("Run Migrations", id="db-run-migrations", variant="primary")
            with Vertical(classes="column-right"):
                yield Static("[bold]Table Record Counts[/bold]", classes="section-header")
                yield DataTable(id="db-counts-table")

    def on_mount(self) -> None:
        table = self.query_one("#db-counts-table", DataTable)
        table.add_columns("Table", "Count")
        table.cursor_type = "row"
        self.query_one("#db-connection", Static).update("[dim]Checking...[/dim]")
        self.query_one("#db-migrations", Static).update("[dim]Checking...[/dim]")
        self.refresh_database()

    def refresh_database(self) -> None:
        """Schedule a background refresh."""
        if not self._refresh_lock.acquire(blocking=False):
            return
        self.app.run_worker(self._do_refresh, thread=True)

    async def _do_refresh(self) -> None:
        """Fetch all DB data in worker thread, then update UI."""
        try:
            status = get_db_status()
            counts = get_table_counts()
            migration = get_migration_status()

            # Build connection text
            if status.connected:
                conn_lines = [
                    f"  URL:        {status.url}",
                    f"  Namespace:  {status.namespace}",
                    f"  Database:   {status.database}",
                    "  Status:     [green]Connected[/green]",
                ]
            else:
                conn_lines = [
                    f"  URL:        {status.url}",
                    "  Status:     [red]Disconnected[/red]",
                    f"  Error:      {status.error}" if status.error else "",
                ]
            conn_text = "\n".join(ln for ln in conn_lines if ln)

            # Build migration text
            if migration.error:
                mig_text = f"  [yellow]{migration.error}[/yellow]"
            else:
                mig_lines = [
                    f"  Applied:    {migration.total_migrations}",
                    f"  Latest:     {migration.current_version}",
                ]
                if migration.applied_at:
                    mig_lines.append(f"  Applied at: {migration.applied_at}")
                mig_text = "\n".join(mig_lines)

            self.app.call_from_thread(
                self._apply_update, conn_text, mig_text, counts
            )
        finally:
            self._refresh_lock.release()

    def _apply_update(
        self, conn_text: str, mig_text: str, counts: list
    ) -> None:
        """Apply data to widgets on UI thread."""
        self.query_one("#db-connection", Static).update(conn_text)
        self.query_one("#db-migrations", Static).update(mig_text)
        table = self.query_one("#db-counts-table", DataTable)
        table.clear()
        for tc in counts:
            table.add_row(tc.name, f"{tc.count:,}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "db-run-migrations":
            self.app.run_worker(self._do_run_migrations, thread=True)

    def _do_run_migrations(self) -> None:
        self.app.call_from_thread(self.app.notify, "Running migrations...")
        ok, msg = run_migrations()
        severity = "information" if ok else "error"
        self.app.call_from_thread(self.app.notify, msg, severity=severity)
        self.app.call_from_thread(self.refresh_database)
