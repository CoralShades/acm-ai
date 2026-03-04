"""Last extraction results display widget."""

from __future__ import annotations

from textual.widgets import Static

from tui.services.log_parser import ExtractionSummary


class ExtractionSummaryWidget(Static):
    """Displays the last ACM extraction result."""

    def update_summary(self, summary: ExtractionSummary | None) -> None:
        if summary is None:
            self.update("[dim]No extraction results found in logs.[/dim]")
            return

        lines = [
            "[bold underline]Last Extraction[/bold underline]",
            f"  Time:     {summary.timestamp}",
            f"  Records:  {summary.record_count}",
            f"  Duration: {summary.duration_seconds:.1f}s",
        ]
        self.update("\n".join(lines))
