"""Log viewer tab — file browser + log content + tail mode + filtering."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Label, ListItem, ListView, Static

from tui.services.log_parser import list_log_files
from tui.widgets.log_viewer import LogViewer


class LogsScreen(Vertical):
    """Log file viewer with sidebar, tail mode, and filtering."""

    _tailing: bool = False
    _tail_timer = None

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]Logs[/bold]  [dim]T=tail  F=filter  R=refresh[/dim]",
            classes="section-header",
        )
        with Horizontal(id="logs-columns"):
            with Vertical(id="logs-sidebar"):
                yield ListView(id="log-file-list")
            with Vertical(id="logs-content"):
                yield Input(placeholder="Filter regex...", id="log-filter", classes="hidden")
                yield LogViewer(id="log-viewer")

    def on_mount(self) -> None:
        self._populate_file_list()

    def _populate_file_list(self) -> None:
        file_list = self.query_one("#log-file-list", ListView)
        file_list.clear()
        for log_path in list_log_files():
            item = ListItem(Label(log_path.name), name=str(log_path))
            file_list.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        path_str = event.item.name
        if path_str:
            viewer = self.query_one("#log-viewer", LogViewer)
            viewer.load_file(Path(path_str))

    def toggle_tail(self) -> None:
        self._tailing = not self._tailing
        if self._tailing:
            self._tail_timer = self.set_interval(2.0, self._tail_tick)
        elif self._tail_timer:
            self._tail_timer.stop()
            self._tail_timer = None

    def _tail_tick(self) -> None:
        viewer = self.query_one("#log-viewer", LogViewer)
        viewer.tail_refresh()

    def toggle_filter(self) -> None:
        filter_input = self.query_one("#log-filter", Input)
        if "hidden" in filter_input.classes:
            filter_input.remove_class("hidden")
            filter_input.focus()
        else:
            filter_input.add_class("hidden")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "log-filter":
            viewer = self.query_one("#log-viewer", LogViewer)
            viewer.set_filter(event.value)

    def refresh_logs(self) -> None:
        self._populate_file_list()
