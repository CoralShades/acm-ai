"""Configuration constants for the ACM-AI TUI Monitor."""

from __future__ import annotations

import base64
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ports (read from environment, same defaults as _service_config.py)
SURREAL_PORT = int(os.environ.get("SURREAL_PORT", "8000"))
API_PORT = int(os.environ.get("API_PORT", "5055"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "8502"))
OLLAMA_PORT = int(os.environ.get("OLLAMA_PORT", "11434"))

# URLs
API_BASE_URL = f"http://localhost:{API_PORT}"
SURREAL_HTTP_URL = f"http://localhost:{SURREAL_PORT}"

# SurrealDB auth (Basic auth for HTTP /sql endpoint)
_surreal_user = os.environ.get("SURREAL_USER", "root")
_surreal_pass = os.environ.get("SURREAL_PASSWORD", "root")
SURREAL_AUTH = base64.b64encode(f"{_surreal_user}:{_surreal_pass}".encode()).decode()
SURREAL_NS = os.environ.get("SURREAL_NAMESPACE", "open_notebook")
SURREAL_DB = os.environ.get("SURREAL_DATABASE", "development")

# Tables to show record counts for in the Database tab
DB_TABLES = [
    "acm_record",
    "source",
    "source_embedding",
    "note",
    "acm_table_section",
    "extraction_progress",
    "notebook",
    "model",
    "school",
    "building",
    "room",
]

# Paths
LOGS_DIR = PROJECT_ROOT / "logs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
EXPORTS_DIR = PROJECT_ROOT / "exports"

# Polling — 10s avoids subprocess pile-up on Windows
DASHBOARD_REFRESH_SECONDS = 10.0

# Ollama
OLLAMA_CONTAINER = "acm-ai-ollama"
OLLAMA_URL = f"http://localhost:{OLLAMA_PORT}"
OLLAMA_DEFAULT_MODELS = ["qwen3", "mxbai-embed-large"]

# Package audit list
AUDIT_PACKAGES = [
    "torch",
    "torchvision",
    "docling",
    "docling_core",
    "docling_ibm_models",
    "paddlepaddle",
    "pymupdf",
    "pandas",
    "tabulate",
    "content_core",
    "langchain",
    "fastapi",
    "surrealdb",
]
