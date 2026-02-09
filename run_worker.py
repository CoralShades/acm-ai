#!/usr/bin/env python
"""
Worker wrapper script that configures UTF-8 encoding for Windows compatibility.

This wrapper ensures that the surreal-commands-worker can run on Windows
without Unicode encoding errors when logging emoji characters.

Issue: https://github.com/CoralShades/acm-ai/issues/1
"""

import io
import sys


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

    # Import and run the worker after encoding is configured
    from surreal_commands.cli.worker import main as worker_main

    worker_main()


if __name__ == "__main__":
    main()
