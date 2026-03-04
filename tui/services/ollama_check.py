"""Ollama service management — start/stop, model listing, health checks."""

from __future__ import annotations

import json
import subprocess
import urllib.request
from dataclasses import dataclass, field

from tui.config import OLLAMA_CONTAINER, OLLAMA_PORT, OLLAMA_URL, PROJECT_ROOT


@dataclass
class OllamaModel:
    name: str
    size: str
    modified: str


@dataclass
class OllamaStatus:
    running: bool = False
    mode: str = "unknown"  # "cpu", "gpu", "unknown"
    models: list[OllamaModel] = field(default_factory=list)
    url: str = OLLAMA_URL
    error: str = ""


def get_ollama_status() -> OllamaStatus:
    """Check Ollama container status, mode, and installed models."""
    status = OllamaStatus()

    # Check if container is running
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "{{.Name}}\t{{.State}}"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=10,
        )
        for line in result.stdout.strip().splitlines():
            if "ollama" in line.lower():
                parts = line.split("\t")
                if len(parts) >= 2 and parts[1].strip().lower() == "running":
                    status.running = True
                    # Detect mode from container name
                    if "gpu" in parts[0].lower():
                        status.mode = "gpu"
                    elif "cpu" in parts[0].lower():
                        status.mode = "cpu"
                    else:
                        status.mode = "gpu"  # default assumption
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fetch models if running
    if status.running:
        status.models = list_models()

    return status


def is_ollama_healthy() -> bool:
    """Quick health check via HTTP."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status < 400
    except Exception:
        return False


def list_models() -> list[OllamaModel]:
    """List installed Ollama models via API."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                size_bytes = m.get("size", 0)
                size_str = f"{size_bytes / (1024**3):.1f}GB" if size_bytes else "?"
                models.append(
                    OllamaModel(
                        name=m.get("name", "?"),
                        size=size_str,
                        modified=m.get("modified_at", "")[:19],
                    )
                )
            return models
    except Exception:
        return []


def start_ollama(mode: str = "gpu") -> tuple[bool, str]:
    """Start Ollama via docker compose profile. Returns (success, message)."""
    profile = f"ollama-{mode}"
    try:
        result = subprocess.run(
            ["docker", "compose", "--profile", profile, "up", "-d"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
        if result.returncode == 0:
            return True, f"Ollama started ({mode} mode)"
        return False, result.stderr.strip()[:200]
    except FileNotFoundError:
        return False, "docker not found"
    except subprocess.TimeoutExpired:
        return False, "Timed out starting Ollama"


def stop_ollama() -> tuple[bool, str]:
    """Stop the Ollama container."""
    try:
        result = subprocess.run(
            ["docker", "compose", "--profile", "ollama-gpu", "--profile", "ollama-cpu", "down"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30,
        )
        # Also try stopping the specific container directly
        subprocess.run(
            ["docker", "stop", OLLAMA_CONTAINER],
            capture_output=True,
            timeout=10,
        )
        return True, "Ollama stopped"
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def pull_model(model_name: str) -> tuple[bool, str]:
    """Pull a model inside the Ollama container."""
    try:
        result = subprocess.run(
            ["docker", "exec", OLLAMA_CONTAINER, "ollama", "pull", model_name],
            capture_output=True,
            text=True,
            timeout=600,  # models can be large
        )
        if result.returncode == 0:
            return True, f"Pulled {model_name}"
        return False, result.stderr.strip()[:200]
    except FileNotFoundError:
        return False, "docker not found"
    except subprocess.TimeoutExpired:
        return False, "Timed out pulling model"
