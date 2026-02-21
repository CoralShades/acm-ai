#!/bin/bash
# Ralph Sprint TUI Launcher
# Runs the Textual-based dashboard without touching project venv
cd "$(dirname "$0")/.." || exit 1
exec uv run --no-project --with textual --with rich python3 .ralph/ralph-tui.py "$@"
