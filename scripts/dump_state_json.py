#!/usr/bin/env python3
"""Dump LangGraph thread state as JSON for JSON Crack visualization.

Usage:
  uv run python scripts/dump_state_json.py <thread_id> [output_file]

Then open http://localhost:8888 and paste/upload the JSON file.
"""

import json
import sys
from pathlib import Path


def dump_thread_state(thread_id: str, output: str = "state_dump.json"):
    """Fetch thread state from LangGraph API and save as JSON."""
    try:
        import httpx
    except ImportError:
        print("httpx not installed. Run: uv sync")
        sys.exit(1)

    resp = httpx.get(f"http://127.0.0.1:2024/threads/{thread_id}/state")
    resp.raise_for_status()
    state = resp.json()

    Path(output).write_text(json.dumps(state, indent=2, default=str))
    print(f"State dumped to {output}")
    print(f"Open http://localhost:8888 and use Import -> Upload File -> {output}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: uv run python scripts/dump_state_json.py <thread_id> [output_file]"
        )
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else "state_dump.json"
    dump_thread_state(sys.argv[1], out)
