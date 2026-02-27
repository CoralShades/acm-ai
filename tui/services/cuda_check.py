"""GPU and CUDA diagnostics via nvidia-smi and torch.cuda."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field


@dataclass
class GpuInfo:
    name: str = "N/A"
    driver_version: str = "N/A"
    memory_used_mb: str = "N/A"
    memory_total_mb: str = "N/A"
    temperature_c: str = "N/A"
    power_draw_w: str = "N/A"
    power_limit_w: str = "N/A"
    utilization_pct: str = "N/A"
    available: bool = False


@dataclass
class CudaInfo:
    torch_version: str = "N/A"
    cuda_available: bool = False
    cuda_version: str = "N/A"
    device_name: str = "N/A"
    device_count: int = 0
    cudnn_version: str = "N/A"
    available: bool = False


def get_gpu_info() -> GpuInfo:
    """Query nvidia-smi for GPU hardware information."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.used,memory.total,"
                "temperature.gpu,power.draw,power.limit,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return GpuInfo()

        line = result.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 8:
            return GpuInfo(
                name=parts[0],
                driver_version=parts[1],
                memory_used_mb=parts[2],
                memory_total_mb=parts[3],
                temperature_c=parts[4],
                power_draw_w=parts[5],
                power_limit_w=parts[6],
                utilization_pct=parts[7],
                available=True,
            )
    except (FileNotFoundError, subprocess.TimeoutExpired, IndexError):
        pass
    return GpuInfo()


def get_cuda_info() -> CudaInfo:
    """Query PyTorch for CUDA runtime information."""
    info = CudaInfo()
    try:
        import torch

        info.torch_version = torch.__version__
        info.cuda_available = torch.cuda.is_available()
        info.available = True

        if info.cuda_available:
            info.cuda_version = torch.version.cuda or "N/A"
            info.device_count = torch.cuda.device_count()
            if info.device_count > 0:
                info.device_name = torch.cuda.get_device_name(0)
            cudnn = torch.backends.cudnn.version()
            if cudnn:
                info.cudnn_version = str(cudnn)
    except ImportError:
        pass
    except Exception:
        info.available = True  # torch imported but something else failed
    return info
