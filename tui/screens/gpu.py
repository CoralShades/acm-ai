"""GPU / CUDA information tab."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from tui.services.cuda_check import get_cuda_info, get_gpu_info
from tui.widgets.gpu_panel import GpuPanel


class GpuScreen(Vertical):
    """Displays GPU hardware and PyTorch CUDA details."""

    def compose(self) -> ComposeResult:
        yield Static("[bold]GPU & CUDA Information[/bold]  [dim](R to refresh)[/dim]", classes="section-header")
        yield GpuPanel(id="gpu-panel", classes="info-panel")

    def on_mount(self) -> None:
        self.refresh_info()

    def refresh_info(self) -> None:
        self.app.run_worker(self._do_refresh, thread=True)

    async def _do_refresh(self) -> None:
        gpu = get_gpu_info()
        cuda = get_cuda_info()
        panel = self.query_one("#gpu-panel", GpuPanel)
        self.app.call_from_thread(panel.update_info, gpu, cuda)
