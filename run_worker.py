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

    # Configure file logging before starting the worker
    _configure_file_logging()

    # Import and run the worker after encoding is configured
    from surreal_commands.cli.worker import main as worker_main

    worker_main()


if __name__ == "__main__":
    main()
