"""Service definitions and configuration for the ACM-AI service manager."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PID_DIR = Path("/tmp")


@dataclass
class ServiceDef:
    """Definition for a single managed service."""

    name: str
    display_name: str
    port: int | None
    health_url: str | None
    start_command: list[str]
    stop_patterns: list[str]
    pid_file: str | None
    log_file: str | None
    working_dir: Path
    depends_on: list[str] = field(default_factory=list)
    is_docker: bool = False
    startup_delay: int = 3
    health_timeout: int = 10


def get_services() -> dict[str, ServiceDef]:
    """Return service definitions, reading ports from environment variables."""
    surreal_port = int(os.environ.get("SURREAL_PORT", "8000"))
    api_port = int(os.environ.get("API_PORT", "5055"))
    frontend_port = int(os.environ.get("FRONTEND_PORT", "8502"))

    return {
        "surrealdb": ServiceDef(
            name="surrealdb",
            display_name="SurrealDB",
            port=surreal_port,
            health_url=None,  # checked via docker inspect
            start_command=["docker", "compose", "up", "-d", "surrealdb"],
            stop_patterns=[],
            pid_file=None,
            log_file=None,
            working_dir=PROJECT_ROOT,
            is_docker=True,
            startup_delay=5,
            health_timeout=15,
        ),
        "api": ServiceDef(
            name="api",
            display_name="API Server",
            port=api_port,
            health_url=f"http://localhost:{api_port}/health",
            start_command=["uv", "run", "python", "run_api.py"],
            stop_patterns=["run_api.py", "uvicorn api.main:app"],
            pid_file=str(PID_DIR / "acm-ai-api.pid"),
            log_file=str(PID_DIR / "acm-ai-api.log"),
            working_dir=PROJECT_ROOT,
            depends_on=["surrealdb"],
            startup_delay=3,
            health_timeout=10,
        ),
        "worker": ServiceDef(
            name="worker",
            display_name="Background Worker",
            port=None,
            health_url=None,  # checked via process detection
            start_command=[
                "uv",
                "run",
                "surreal-commands-worker",
                "--import-modules",
                "commands",
            ],
            stop_patterns=["surreal-commands-worker"],
            pid_file=str(PID_DIR / "acm-ai-worker.pid"),
            log_file=str(PID_DIR / "acm-ai-worker.log"),
            working_dir=PROJECT_ROOT,
            depends_on=["surrealdb"],
            startup_delay=2,
        ),
        "frontend": ServiceDef(
            name="frontend",
            display_name="Frontend",
            port=frontend_port,
            health_url=f"http://localhost:{frontend_port}",
            start_command=["npm", "run", "dev", "--", "-p", str(frontend_port)],
            stop_patterns=["npm run dev.*8502", "next dev"],
            pid_file=str(PID_DIR / "acm-ai-frontend.pid"),
            log_file=str(PID_DIR / "acm-ai-frontend.log"),
            working_dir=PROJECT_ROOT / "frontend",
            depends_on=["api"],
            startup_delay=3,
        ),
    }


STARTUP_ORDER = ["surrealdb", "api", "worker", "frontend"]
SHUTDOWN_ORDER = list(reversed(STARTUP_ORDER))
