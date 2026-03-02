"""GPU information display widget."""

from __future__ import annotations

from textual.widgets import Static

from tui.services.cuda_check import CudaInfo, GpuInfo


class GpuPanel(Static):
    """Displays GPU hardware and CUDA runtime info as rich text."""

    def update_info(self, gpu: GpuInfo, cuda: CudaInfo) -> None:
        lines: list[str] = []

        # GPU hardware section
        lines.append("[bold underline]GPU Hardware[/bold underline]")
        if gpu.available:
            lines.append(f"  Name:         {gpu.name}")
            lines.append(f"  Driver:       {gpu.driver_version}")
            lines.append(f"  VRAM:         {gpu.memory_used_mb} / {gpu.memory_total_mb} MB")
            lines.append(f"  Temperature:  {gpu.temperature_c} C")
            lines.append(f"  Power:        {gpu.power_draw_w} / {gpu.power_limit_w} W")
            lines.append(f"  Utilization:  {gpu.utilization_pct}%")
        else:
            lines.append("  [dim]nvidia-smi not available[/dim]")

        lines.append("")
        lines.append("[bold underline]PyTorch CUDA[/bold underline]")
        if cuda.available:
            lines.append(f"  Torch:        {cuda.torch_version}")
            lines.append(f"  CUDA:         {'Yes' if cuda.cuda_available else 'No'}")
            if cuda.cuda_available:
                lines.append(f"  CUDA Version: {cuda.cuda_version}")
                lines.append(f"  Device:       {cuda.device_name}")
                lines.append(f"  Devices:      {cuda.device_count}")
                lines.append(f"  cuDNN:        {cuda.cudnn_version}")
        else:
            lines.append("  [dim]torch not installed[/dim]")

        self.update("\n".join(lines))
