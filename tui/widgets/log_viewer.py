"""RichLog-based log viewer widget with filtering."""

from __future__ import annotations

import re
from pathlib import Path

from textual.widgets import RichLog

from tui.services.log_parser import read_log_file


class LogViewer(RichLog):
    """Scrollable log viewer with optional regex filtering."""

    def __init__(self, **kwargs) -> None:
        super().__init__(highlight=True, markup=False, wrap=True, **kwargs)
        self._current_path: Path | None = None
        self._filter_pattern: str = ""
        self._all_lines: list[str] = []

    def load_file(self, path: Path) -> None:
        """Load a log file into the viewer."""
        self._current_path = path
        self._all_lines = read_log_file(path, max_lines=1000)
        self._apply_filter()

    def set_filter(self, pattern: str) -> None:
        """Apply a regex filter to displayed lines."""
        self._filter_pattern = pattern
        self._apply_filter()

    def _apply_filter(self) -> None:
        self.clear()
        lines = self._all_lines
        if self._filter_pattern:
            try:
                rx = re.compile(self._filter_pattern, re.IGNORECASE)
                lines = [ln for ln in lines if rx.search(ln)]
            except re.error:
                lines = [ln for ln in lines if self._filter_pattern.lower() in ln.lower()]

        for line in lines:
            self.write(line)

    def tail_refresh(self) -> None:
        """Re-read the current file and scroll to bottom."""
        if self._current_path and self._current_path.exists():
            self._all_lines = read_log_file(self._current_path, max_lines=1000)
            self._apply_filter()
            self.scroll_end(animate=False)
