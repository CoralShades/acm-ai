"""Ollama management tab — start/stop, models, health, pull."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from tui.services.ollama_check import (
    get_ollama_status,
    pull_model,
    start_ollama,
    stop_ollama,
)


class OllamaScreen(Vertical):
    """Ollama service management and model browser."""

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]Ollama Local AI[/bold]  [dim](R to refresh)[/dim]",
            classes="section-header",
        )
        with Horizontal(id="ollama-top"):
            with Vertical(id="ollama-status-col", classes="column-left"):
                yield Static("[bold]Status[/bold]", classes="section-header")
                yield Static(id="ollama-status", classes="info-panel")
            with Vertical(id="ollama-actions-col", classes="column-right"):
                yield Static("[bold]Actions[/bold]", classes="section-header")
                with Horizontal(classes="button-row"):
                    yield Button("Start (GPU)", id="ollama-start-gpu", variant="success")
                    yield Button("Start (CPU)", id="ollama-start-cpu", variant="primary")
                    yield Button("Stop", id="ollama-stop", variant="error")
                with Horizontal(classes="button-row"):
                    yield Button("Pull qwen3", id="ollama-pull-qwen3", variant="default")
                    yield Button("Pull mxbai-embed", id="ollama-pull-embed", variant="default")
        yield Static("[bold]Installed Models[/bold]", classes="section-header")
        yield DataTable(id="ollama-models")

    def on_mount(self) -> None:
        table = self.query_one("#ollama-models", DataTable)
        table.add_columns("Model", "Size", "Modified")
        table.cursor_type = "row"
        self.refresh_ollama()

    def refresh_ollama(self) -> None:
        self.app.run_worker(self._do_refresh, thread=True)

    async def _do_refresh(self) -> None:
        status = get_ollama_status()
        # Build status text
        if status.running:
            mode_label = status.mode.upper()
            lines = [
                f"  Running:  [green]Yes[/green]",
                f"  Mode:     {mode_label}",
                f"  URL:      {status.url}",
                f"  Models:   {len(status.models)}",
            ]
        else:
            lines = [
                "  Running:  [red]No[/red]",
                "  [dim]Start Ollama to use local AI models[/dim]",
            ]
        status_text = "\n".join(lines)

        self.app.call_from_thread(self._apply_update, status_text, status)

    def _apply_update(self, status_text, status) -> None:
        self.query_one("#ollama-status", Static).update(status_text)
        table = self.query_one("#ollama-models", DataTable)
        table.clear()
        for m in status.models:
            table.add_row(m.name, m.size, m.modified)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn == "ollama-start-gpu":
            self.app.run_worker(lambda: self._start("gpu"), thread=True)
        elif btn == "ollama-start-cpu":
            self.app.run_worker(lambda: self._start("cpu"), thread=True)
        elif btn == "ollama-stop":
            self.app.run_worker(self._stop, thread=True)
        elif btn == "ollama-pull-qwen3":
            self.app.run_worker(lambda: self._pull("qwen3"), thread=True)
        elif btn == "ollama-pull-embed":
            self.app.run_worker(lambda: self._pull("mxbai-embed-large"), thread=True)

    def _start(self, mode: str) -> None:
        self.app.call_from_thread(self.app.notify, f"Starting Ollama ({mode})...")
        ok, msg = start_ollama(mode)
        severity = "information" if ok else "error"
        self.app.call_from_thread(self.app.notify, msg, severity=severity)
        self.app.call_from_thread(self.refresh_ollama)

    def _stop(self) -> None:
        self.app.call_from_thread(self.app.notify, "Stopping Ollama...")
        ok, msg = stop_ollama()
        severity = "information" if ok else "error"
        self.app.call_from_thread(self.app.notify, msg, severity=severity)
        self.app.call_from_thread(self.refresh_ollama)

    def _pull(self, model: str) -> None:
        self.app.call_from_thread(
            self.app.notify, f"Pulling {model} (this may take minutes)..."
        )
        ok, msg = pull_model(model)
        severity = "information" if ok else "error"
        self.app.call_from_thread(self.app.notify, msg, severity=severity)
        self.app.call_from_thread(self.refresh_ollama)
