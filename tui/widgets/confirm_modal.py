"""Reusable confirmation modal for destructive actions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmScreen(ModalScreen[bool]):
    """Modal dialog that asks the user to confirm or cancel a destructive action.

    Usage:
        def callback(confirmed: bool | None) -> None:
            if confirmed:
                self.run_worker(self._do_thing, thread=True)
        self.app.push_screen(ConfirmScreen("Kill PID 1234?"), callback)
    """

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #confirm-dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }
    #confirm-question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }
    #confirm {
        width: 100%;
    }
    #cancel {
        width: 100%;
    }
    """

    def __init__(self, message: str, title: str = "Confirm") -> None:
        super().__init__()
        self._message = message
        self._title = title

    def compose(self) -> ComposeResult:
        with Grid(id="confirm-dialog"):
            yield Label(self._message, id="confirm-question")
            yield Button("Confirm", id="confirm", variant="error")
            yield Button("Cancel", id="cancel", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")
