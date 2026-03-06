#!/usr/bin/env python
"""
Worker wrapper script that configures UTF-8 encoding for Windows compatibility.

This wrapper ensures that the surreal-commands-worker can run on Windows
without Unicode encoding errors when logging emoji characters.

Issue: https://github.com/CoralShades/acm-ai/issues/1
"""

import io
import os
import sys
from pathlib import Path


def _configure_file_logging():
    """Add loguru file sinks for persistent worker logs."""
    from loguru import logger

    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "worker.log",
        rotation="10 MB",
        retention="7 days",
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
        backtrace=True,
        diagnose=False,
    )
    logger.add(
        log_dir / "worker-error.log",
        rotation="10 MB",
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
        backtrace=True,
        diagnose=True,
    )


def main():
    """Configure UTF-8 encoding and start the worker."""
    # Fix Unicode encoding issue on Windows (Issue #1)
    # Windows console uses cp1252 by default which doesn't support emoji
    if sys.platform == "win32":
        # Reconfigure stdout and stderr to use UTF-8 encoding
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )

    # Patch surreal_commands' configure_logging to preserve our file sinks.
    # surreal_commands.core.worker.configure_logging() calls logger.remove()
    # which wipes ALL loguru handlers — including file sinks added earlier.
    # By monkey-patching, we re-add file sinks AFTER the library's own setup.
    from surreal_commands.core import worker as sc_worker

    _original_configure_logging = sc_worker.configure_logging

    def _patched_configure_logging(debug: bool = False):
        _original_configure_logging(debug)
        _configure_file_logging()  # Re-add file sinks after logger.remove()

    sc_worker.configure_logging = _patched_configure_logging

    # Initialize Logfire -> Langfuse OTel bridge (non-fatal, before command imports)
    from open_notebook.observability.logfire_config import init_logfire

    init_logfire()

    # Import and run the worker after encoding is configured
    from surreal_commands.cli.worker import main as worker_main

    worker_main()


if __name__ == "__main__":
    main()
