#!/usr/bin/env python3
"""
Startup script for Open Notebook API server.
"""

import os
import sys
from pathlib import Path

import uvicorn

# Add the current directory to Python path so imports work
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    # Default configuration
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "5055"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    print(f"Starting Open Notebook API server on {host}:{port}")
    print(f"Reload mode: {reload}")

    if reload:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=[
                str(current_dir / "api"),
                str(current_dir / "open_notebook"),
                str(current_dir / "commands"),
                str(current_dir / "prompts"),
            ],
            reload_excludes=["*.pyc", "__pycache__"],
        )
    else:
        # On Windows, asyncio.create_server() defaults to reuse_address=False
        # (unlike Unix where it defaults to True). Without SO_REUSEADDR, bind()
        # fails with [Errno 10048] if TIME_WAIT connections linger from a
        # previously killed API process — even though no process is actively
        # listening. Pre-create the socket with SO_REUSEADDR so uvicorn can
        # bind through stale TIME_WAIT state.
        if sys.platform == "win32":
            import socket as socket_mod

            sock = socket_mod.socket(socket_mod.AF_INET, socket_mod.SOCK_STREAM)
            sock.setsockopt(socket_mod.SOL_SOCKET, socket_mod.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError as e:
                print(f"ERROR: Cannot bind to {host}:{port}: {e}")
                sys.exit(1)

            print(f"Pre-bound socket on {host}:{port} (SO_REUSEADDR=1)")
            config = uvicorn.Config("api.main:app", host=host, port=port)
            server = uvicorn.Server(config)
            server.run(sockets=[sock])
        else:
            uvicorn.run("api.main:app", host=host, port=port)
