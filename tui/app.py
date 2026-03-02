"""Main Textual App — tab routing, keybindings, service control actions.

Start/Stop mirrors the logic in start-all.bat / stop-all.bat:
  - Preflight checks before start
  - Port cleanup before start
  - Dependency-aware ordered startup with wait-for-ready
  - Ordered shutdown with cleanup
"""

from __future__ import annotations

import subprocess
import time
import urllib.request
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from tui.config import API_PORT, PROJECT_ROOT
from tui.screens.dashboard import DashboardScreen
from tui.screens.database import DatabaseScreen
from tui.screens.errors import ErrorsScreen
from tui.screens.extraction import ExtractionScreen
from tui.screens.gpu import GpuScreen
from tui.screens.logs import LogsScreen
from tui.screens.ollama import OllamaScreen
from tui.screens.packages import PackagesScreen

CSS_PATH = Path(__file__).parent / "tui.tcss"


class AcmMonitorApp(App):
    """ACM-AI unified monitoring and service control dashboard."""

    TITLE = "ACM-AI Monitor"
    CSS_PATH = CSS_PATH

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("s", "start_all", "Start All", show=True),
        Binding("x", "stop_all", "Stop All", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("t", "toggle_tail", "Tail", show=True),
        Binding("f", "toggle_filter", "Filter", show=True),
        Binding("c", "cleanup_ports", "Cleanup", show=True),
        Binding("d", "tab_database", "Database", show=False),
        Binding("e", "tab_extraction", "Extraction", show=False),
        Binding("1", "tab_1", "Dashboard", show=False),
        Binding("2", "tab_2", "GPU", show=False),
        Binding("3", "tab_3", "Packages", show=False),
        Binding("4", "tab_4", "Database", show=False),
        Binding("5", "tab_5", "Extraction", show=False),
        Binding("6", "tab_6", "Logs", show=False),
        Binding("7", "tab_7", "Errors", show=False),
        Binding("8", "tab_8", "Ollama", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("Dashboard", id="tab-dashboard"):
                yield DashboardScreen()
            with TabPane("GPU / CUDA", id="tab-gpu"):
                yield GpuScreen()
            with TabPane("Packages", id="tab-packages"):
                yield PackagesScreen()
            with TabPane("Database", id="tab-database"):
                yield DatabaseScreen()
            with TabPane("Extraction", id="tab-extraction"):
                yield ExtractionScreen()
            with TabPane("Logs", id="tab-logs"):
                yield LogsScreen()
            with TabPane("Errors", id="tab-errors"):
                yield ErrorsScreen()
            with TabPane("Ollama", id="tab-ollama"):
                yield OllamaScreen()
        yield Footer()

    # --- Actions ---

    def action_start_all(self) -> None:
        self.run_worker(self._start_all_services, thread=True)

    def action_stop_all(self) -> None:
        self.run_worker(self._stop_all_services, thread=True)

    def action_cleanup_ports(self) -> None:
        self.run_worker(self._cleanup_ports, thread=True)

    def action_refresh(self) -> None:
        """Refresh the currently active tab."""
        tabs = self.query_one("#tabs", TabbedContent)
        active = tabs.active
        if active == "tab-dashboard":
            self.query_one(DashboardScreen).refresh_all()
        elif active == "tab-gpu":
            self.query_one(GpuScreen).refresh_info()
        elif active == "tab-packages":
            self.query_one(PackagesScreen).refresh_packages()
        elif active == "tab-database":
            self.query_one(DatabaseScreen).refresh_database()
        elif active == "tab-extraction":
            self.query_one(ExtractionScreen).refresh_extraction()
        elif active == "tab-logs":
            self.query_one(LogsScreen).refresh_logs()
        elif active == "tab-errors":
            self.query_one(ErrorsScreen).refresh_errors()
        elif active == "tab-ollama":
            self.query_one(OllamaScreen).refresh_ollama()

    def action_toggle_tail(self) -> None:
        try:
            self.query_one(LogsScreen).toggle_tail()
        except Exception:
            pass

    def action_toggle_filter(self) -> None:
        try:
            self.query_one(LogsScreen).toggle_filter()
        except Exception:
            pass

    def action_tab_1(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-dashboard"

    def action_tab_2(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-gpu"

    def action_tab_3(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-packages"

    def action_tab_4(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-database"

    def action_tab_5(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-extraction"

    def action_tab_6(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-logs"

    def action_tab_7(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-errors"

    def action_tab_8(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-ollama"

    def action_tab_database(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-database"

    def action_tab_extraction(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-extraction"

    # --- Service control workers (all run in thread) ---

    async def _start_all_services(self) -> None:
        """Mirrors start-all.bat: preflight → cleanup → ordered start → health wait."""
        from tui.services.service_control import (
            STARTUP_ORDER,
            get_services,
            is_port_in_use,
            is_service_running,
            start_service_background,
        )

        services = get_services()

        # Step 1: Preflight checks
        self.call_from_thread(self.notify, "[1/4] Running preflight checks...")
        preflight_ok, preflight_msg = _run_preflight()
        if not preflight_ok:
            self.call_from_thread(
                self.notify,
                f"Preflight FAILED: {preflight_msg}",
                severity="error",
            )
            return

        # Step 2: Port cleanup
        self.call_from_thread(self.notify, "[2/4] Clearing ports...")
        for name in STARTUP_ORDER:
            svc = services.get(name)
            if svc and svc.port and is_port_in_use(svc.port):
                if not is_service_running(svc):
                    # Port occupied by something else — skip aggressive kill from TUI
                    self.call_from_thread(
                        self.notify,
                        f"Port {svc.port} in use by another process",
                        severity="warning",
                    )

        # Step 3: Ordered startup with dependency waits
        self.call_from_thread(self.notify, "[3/4] Starting services...")
        for name in STARTUP_ORDER:
            svc = services.get(name)
            if not svc:
                continue

            # Skip if already running
            if is_service_running(svc):
                self.call_from_thread(
                    self.notify, f"{svc.display_name} already running"
                )
                continue

            self.call_from_thread(
                self.notify, f"Starting {svc.display_name}..."
            )
            ok = start_service_background(svc)
            if not ok:
                self.call_from_thread(
                    self.notify,
                    f"Failed to start {svc.display_name}",
                    severity="error",
                )
                continue

            # Wait for readiness (like start-all.bat wait loops)
            if svc.health_url:
                _wait_for_health(svc.health_url, timeout=svc.health_timeout + 15)
            else:
                time.sleep(svc.startup_delay)

        # Step 4: Final status
        self.call_from_thread(
            self.notify, "[4/4] All services started!", severity="information"
        )
        self.call_from_thread(self.query_one(DashboardScreen).refresh_all)

    async def _stop_all_services(self) -> None:
        """Mirrors stop-all.bat: ordered shutdown."""
        from tui.services.service_control import (
            SHUTDOWN_ORDER,
            get_services,
            is_service_running,
            stop_service,
        )

        services = get_services()
        self.call_from_thread(self.notify, "Stopping services...")

        for name in SHUTDOWN_ORDER:
            svc = services.get(name)
            if not svc:
                continue
            if not is_service_running(svc):
                continue
            self.call_from_thread(
                self.notify, f"Stopping {svc.display_name}..."
            )
            stop_service(svc)

        self.call_from_thread(
            self.notify, "All services stopped.", severity="information"
        )
        self.call_from_thread(self.query_one(DashboardScreen).refresh_all)

    async def _cleanup_ports(self) -> None:
        """Kill stale processes on project ports (like start-all.bat step 2)."""
        from tui.config import FRONTEND_PORT, SURREAL_PORT
        from tui.services.service_control import is_port_in_use

        ports = [
            (API_PORT, "API"),
            (FRONTEND_PORT, "Frontend"),
            (SURREAL_PORT, "SurrealDB"),
        ]
        cleaned = 0
        for port, label in ports:
            if is_port_in_use(port):
                self.call_from_thread(
                    self.notify, f"Port {port} ({label}) is in use", severity="warning"
                )
                cleaned += 1
        # Run the service_manager fix command
        try:
            subprocess.run(
                ["uv", "run", "python", "scripts/service_manager.py", "fix", "--auto-fix"],
                capture_output=True,
                cwd=PROJECT_ROOT,
                timeout=15,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        msg = f"Port cleanup done ({cleaned} port(s) checked)"
        self.call_from_thread(self.notify, msg, severity="information")
        self.call_from_thread(self.query_one(DashboardScreen).refresh_all)


def _run_preflight() -> tuple[bool, str]:
    """Run preflight_checks.py. Returns (passed, message)."""
    preflight_script = PROJECT_ROOT / "scripts" / "preflight_checks.py"
    if not preflight_script.exists():
        return True, "No preflight script found, skipping"
    try:
        result = subprocess.run(
            ["uv", "run", "python", str(preflight_script)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30,
        )
        if result.returncode == 0:
            return True, "Preflight passed"
        # Return last non-empty line as error message
        lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
        msg = lines[-1] if lines else "Preflight failed"
        return False, msg
    except FileNotFoundError:
        return True, "uv not found, skipping preflight"
    except subprocess.TimeoutExpired:
        return False, "Preflight timed out"


def _wait_for_health(url: str, timeout: int = 30) -> bool:
    """Poll a health URL until it responds 200 or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status < 400:
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False
