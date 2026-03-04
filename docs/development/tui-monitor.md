# TUI Monitor — Developer & User Guide

The ACM-AI TUI Monitor is a terminal-based dashboard built with [Textual](https://textual.textualize.io/) that provides unified monitoring, service control, database inspection, and extraction job management for the project — all from one keyboard-driven interface.

This guide covers how to use the TUI, how it's built, and how to adapt the pattern for any multi-service project.

---

## Quick Start

```bash
# Windows
tui.bat

# Linux / macOS / WSL
uv run python -m tui
```

The monitor opens with 8 tabs. Use number keys `1`–`8` or click tabs to switch.

---

## Keyboard Reference

### Global Keys (available on every tab)

| Key | Action | Notes |
|-----|--------|-------|
| `q` | Quit | Exits the TUI |
| `s` | Start All | Preflight checks, port cleanup, ordered startup |
| `x` | Stop All | Ordered shutdown of all services |
| `r` | Refresh | Refreshes the active tab's data |
| `t` | Tail | Toggle log tailing (Logs tab) |
| `f` | Filter | Toggle regex filter (Logs tab) |
| `c` | Cleanup | Scan and report occupied project ports |
| `d` | Database | Jump to Database tab |
| `e` | Extraction | Jump to Extraction tab |

### Tab Navigation

| Key | Tab |
|-----|-----|
| `1` | Dashboard |
| `2` | GPU / CUDA |
| `3` | Packages |
| `4` | Database |
| `5` | Extraction |
| `6` | Logs |
| `7` | Errors |
| `8` | Ollama |

---

## Tab Reference

### 1. Dashboard

The main overview tab with interactive controls for every service, port, and Docker container.

**Services panel** — each service shows its status and provides action buttons:

| Status | Buttons Shown |
|--------|---------------|
| Healthy / Starting / Unhealthy | `[Stop]` `[Restart]` |
| Stopped | `[Start]` |

- **Start** acts immediately (non-destructive)
- **Stop** and **Restart** show a confirmation modal before proceeding

**Ports panel** — shows each project port's status:
- Ports in use display the process name/PID and a `[Kill]` button
- `[Kill]` shows a confirmation modal, then force-terminates the process

**Docker panel** — shows Docker Desktop status and each container:
- Each container has a `[Restart]` button (with confirmation)

**Also shows:** Last extraction summary, access URLs (Frontend, API, API Docs).

Auto-refreshes every 10 seconds.

### 2. GPU / CUDA

Read-only display of GPU hardware information and PyTorch CUDA status. Useful for verifying your ML environment is correctly configured.

### 3. Packages

Audit table of critical Python packages — shows version, installation status, and notes. Covers torch, docling, paddlepaddle, langchain, fastapi, surrealdb, and more.

### 4. Database

SurrealDB status and data inspection. Queries the database **directly** via its HTTP `/sql` endpoint (works even when the API server is down).

**Left column:**
- Connection status (URL, namespace, database, connected/disconnected)
- Migration status (total applied, latest version)
- `[Run Migrations]` button

**Right column:**
- Table record counts — shows row counts for `acm_record`, `source`, `source_embedding`, `note`, `notebook`, `model`, `school`, `building`, `room`, and more

### 5. Extraction

ACM extraction job management. Requires the API server to be running.

**ACM Statistics** — total records, buildings, rooms, risk breakdown (High/Medium/Low)

**Active Jobs** — DataTable of recent command jobs with ID, command, status, source, and created timestamp. Select a row to cancel that job (with confirmation).

**Action buttons:**
- `[Export CSV]` — downloads ACM records to `exports/` directory
- `[Export Excel]` — downloads formatted Excel file to `exports/`
- `[Re-embed All]` — submits a job to re-embed all sources and notes (with confirmation)
- `[Rebuild Embeddings]` — submits a full embeddings rebuild job (with confirmation)

### 6. Logs

File browser + log content viewer with tail mode and regex filtering.

- Left sidebar lists log files from `logs/`
- Click a file to view its contents
- Press `t` to toggle live tail mode (polls every 2s)
- Press `f` to toggle the regex filter input

### 7. Errors

Scans log files for ERROR/WARNING/CRITICAL/FAIL entries from the last 24 hours.

- Summary table grouped by file with count and sample message
- Detail log showing individual error entries

### 8. Ollama

Local AI model management for Ollama containers.

- Start/Stop Ollama in GPU or CPU mode
- Pull models (qwen3, mxbai-embed-large)
- View installed models with size and modification date

---

## Confirmation Modal

All destructive actions show a confirmation dialog before executing:

- Kill port process
- Stop / Restart a service
- Restart a Docker container
- Cancel an extraction job
- Re-embed or rebuild embeddings

The modal presents **Confirm** (red) and **Cancel** (blue) buttons. Pressing Cancel returns to the previous view with no action taken.

---

## Architecture

### Directory Structure

```
tui/
  __init__.py              # Package marker
  __main__.py              # Entry point: uv run python -m tui
  app.py                   # Main App class — tabs, keybindings, global actions
  config.py                # Configuration constants (ports, URLs, auth, paths)
  tui.tcss                 # Textual CSS stylesheet

  screens/                 # One file per tab
    dashboard.py           # Tab 1 — interactive service/port/Docker controls
    gpu.py                 # Tab 2 — GPU/CUDA info
    packages.py            # Tab 3 — package audit
    database.py            # Tab 4 — SurrealDB status & table counts
    extraction.py          # Tab 5 — jobs, stats, export
    logs.py                # Tab 6 — log viewer
    errors.py              # Tab 7 — error aggregation
    ollama.py              # Tab 8 — Ollama management

  widgets/                 # Reusable UI components
    confirm_modal.py       # ConfirmScreen(ModalScreen[bool])
    service_table.py       # DataTable for service status (v1, kept for reference)
    extraction_summary.py  # Last extraction result display
    gpu_panel.py           # GPU information panel
    log_viewer.py          # Log file viewer with filtering

  services/                # Data-fetching modules (no UI code)
    service_control.py     # Re-exports from scripts/ — start, stop, health, ports
    port_check.py          # Port conflict detection
    docker_check.py        # Docker Desktop & container health
    database_check.py      # SurrealDB HTTP queries
    extraction_check.py    # API calls for jobs, stats, export
    cuda_check.py          # GPU/CUDA detection
    package_audit.py       # Package version audit
    log_parser.py          # Log file scanning
    ollama_check.py        # Ollama service management
```

### Key Design Patterns

**1. Worker Thread Pattern**

All subprocess calls, network requests, and database queries run in worker threads. The UI thread never blocks.

```python
# Schedule work in a background thread
self.app.run_worker(self._do_refresh, thread=True)

async def _do_refresh(self) -> None:
    # This runs in a worker thread — safe to do blocking I/O
    data = fetch_data()

    # Update UI from worker thread via call_from_thread
    self.app.call_from_thread(self._apply_update, data)
```

**2. Refresh Guard**

A `threading.Lock` prevents overlapping refresh cycles from piling up:

```python
_refresh_lock = threading.Lock()

def refresh_all(self) -> None:
    if not self._refresh_lock.acquire(blocking=False):
        return  # skip — previous refresh still running
    self.app.run_worker(self._do_refresh, thread=True)

async def _do_refresh(self) -> None:
    try:
        # ... fetch and update ...
    finally:
        self._refresh_lock.release()
```

**3. Confirm Before Destructive Actions**

```python
from tui.widgets.confirm_modal import ConfirmScreen

def _confirm_and_run(self, message: str, action) -> None:
    def callback(confirmed: bool | None) -> None:
        if confirmed:
            self.app.run_worker(action, thread=True)
    self.app.push_screen(ConfirmScreen(message), callback)
```

**4. Service Layer Separation**

`tui/services/` modules handle all data fetching and external calls. Screen files only handle layout and UI updates. This separation makes it easy to test services independently and swap out data sources.

**5. Dynamic Widget Rebuilding**

The Dashboard rebuilds its service/port/Docker rows on each refresh instead of using static tables. This allows buttons to change based on service state:

```python
def _apply_ui_update(self, services, statuses, ...) -> None:
    container = self.query_one("#svc-rows", Vertical)
    container.remove_children()
    for name, svc in services.items():
        row = Horizontal(classes="svc-row")
        row.mount(Static(...))
        if status == HEALTHY:
            row.mount(Button("Stop", id=f"svc-{name}-stop", variant="error"))
        else:
            row.mount(Button("Start", id=f"svc-{name}-start", variant="success"))
        container.mount(row)
```

---

## Adapting for Your Project

The TUI Monitor pattern is generic — it works for any multi-service project. Here's how to adapt it.

### Step 1: Install Textual

Add `textual` to your project dependencies:

```bash
uv add textual
```

### Step 2: Create the Package Structure

```
your-project/
  tui/
    __init__.py
    __main__.py          # Entry point
    app.py               # Main App class
    config.py            # Your project's configuration
    tui.tcss             # Stylesheet
    screens/
      __init__.py
      dashboard.py       # Your main monitoring tab
    widgets/
      __init__.py
      confirm_modal.py   # Copy as-is — fully reusable
    services/
      __init__.py
      # Your data-fetching modules
```

### Step 3: Define Your Configuration

Edit `config.py` with your project's services, ports, and endpoints:

```python
"""Configuration constants for your project's TUI Monitor."""
from __future__ import annotations
import base64, os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Your services and ports
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
API_PORT = int(os.environ.get("API_PORT", "8000"))
WORKER_PORT = int(os.environ.get("WORKER_PORT", "6379"))

# URLs
API_BASE_URL = f"http://localhost:{API_PORT}"

# Refresh interval
DASHBOARD_REFRESH_SECONDS = 10.0
```

### Step 4: Define Your Services

Create a service definition module (equivalent to `scripts/_service_config.py`):

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ServiceDef:
    name: str
    display_name: str
    port: int | None
    health_url: str | None
    start_command: list[str]
    stop_patterns: list[str]
    depends_on: list[str] = field(default_factory=list)
    is_docker: bool = False

def get_services() -> dict[str, ServiceDef]:
    return {
        "postgres": ServiceDef(
            name="postgres",
            display_name="PostgreSQL",
            port=5432,
            health_url=None,
            start_command=["docker", "compose", "up", "-d", "postgres"],
            stop_patterns=[],
            is_docker=True,
        ),
        "api": ServiceDef(
            name="api",
            display_name="API Server",
            port=8000,
            health_url="http://localhost:8000/health",
            start_command=["uv", "run", "uvicorn", "app.main:app"],
            stop_patterns=["uvicorn"],
            depends_on=["postgres"],
        ),
        "worker": ServiceDef(
            name="worker",
            display_name="Celery Worker",
            port=None,
            health_url=None,
            start_command=["uv", "run", "celery", "-A", "app", "worker"],
            stop_patterns=["celery"],
            depends_on=["postgres"],
        ),
    }
```

### Step 5: Create Service Modules

Write data-fetching functions in `tui/services/`. These should be pure functions (no UI dependencies) that return dataclasses:

```python
# tui/services/database_check.py
import urllib.request, json
from dataclasses import dataclass

@dataclass
class DbStatus:
    connected: bool = False
    error: str = ""

def get_db_status() -> DbStatus:
    try:
        # Your database health check
        req = urllib.request.Request("http://localhost:5432/health")
        urllib.request.urlopen(req, timeout=3)
        return DbStatus(connected=True)
    except Exception as e:
        return DbStatus(error=str(e))
```

### Step 6: Create Screen Tabs

Each tab is a Textual `Vertical` widget with `compose()` for layout and worker methods for data:

```python
# tui/screens/dashboard.py
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

class DashboardScreen(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("[bold]Services[/bold]", classes="section-header")
        yield Static(id="status", classes="info-panel")

    def on_mount(self) -> None:
        self.refresh_all()
        self.set_interval(10.0, self.refresh_all)

    def refresh_all(self) -> None:
        self.app.run_worker(self._do_refresh, thread=True)

    async def _do_refresh(self) -> None:
        # Blocking I/O in worker thread
        data = fetch_my_data()
        self.app.call_from_thread(
            self.query_one("#status", Static).update, data
        )
```

### Step 7: Wire Up the App

```python
# tui/app.py
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

class MyMonitorApp(App):
    TITLE = "My Project Monitor"
    CSS_PATH = "tui.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("1", "tab_1", "Dashboard", show=False),
        Binding("2", "tab_2", "Logs", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("Dashboard", id="tab-dashboard"):
                yield DashboardScreen()
            with TabPane("Logs", id="tab-logs"):
                yield LogsScreen()
        yield Footer()
```

### Step 8: Add a Launch Script

```batch
@REM Windows: tui.bat
@echo off
cd /d "%~dp0"
uv run python -m tui %*
```

```bash
# Linux/macOS: tui.sh
#!/bin/bash
cd "$(dirname "$0")"
uv run python -m tui "$@"
```

---

## Common Customization Patterns

### Adding a New Tab

1. Create `tui/services/my_check.py` — data fetching functions
2. Create `tui/screens/my_tab.py` — UI layout + worker refresh
3. Import and add `TabPane` in `app.py`
4. Add keybinding for tab switch
5. Add refresh routing in `action_refresh()`
6. Add CSS for any new widget IDs in `tui.tcss`

### Adding Buttons to Any Tab

Follow the Ollama tab pattern:

```python
def compose(self) -> ComposeResult:
    with Horizontal(classes="button-row"):
        yield Button("Action", id="my-action", variant="primary")

def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "my-action":
        self.app.run_worker(self._do_action, thread=True)

def _do_action(self) -> None:
    self.app.call_from_thread(self.app.notify, "Working...")
    result = do_something()
    self.app.call_from_thread(self.app.notify, result)
```

### Adding a Destructive Action with Confirmation

```python
from tui.widgets.confirm_modal import ConfirmScreen

def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "danger-btn":
        def callback(confirmed: bool | None) -> None:
            if confirmed:
                self.app.run_worker(self._do_dangerous_thing, thread=True)
        self.app.push_screen(
            ConfirmScreen("Are you sure? This cannot be undone."),
            callback,
        )
```

### Direct Database Queries (no API dependency)

The Database tab demonstrates querying a database directly via HTTP, bypassing the application server. This pattern is useful when you want monitoring to work even when the app is down:

```python
import urllib.request, json, base64

def query_db(sql: str) -> list[dict]:
    auth = base64.b64encode(b"user:pass").decode()
    req = urllib.request.Request(
        "http://localhost:8000/sql",
        data=sql.encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))
```

### Dynamic Rows with Per-Item Buttons

The Dashboard builds rows dynamically with buttons that have structured IDs:

```python
# Build rows with identifiable button IDs
for item in items:
    row = Horizontal(classes="item-row")
    row.mount(Static(f"  {item.name}", classes="svc-label"))
    row.mount(Button("Delete", id=f"delete-{item.id}", variant="error"))
    container.mount(row)

# Handle by parsing the button ID
def on_button_pressed(self, event: Button.Pressed) -> None:
    btn_id = event.button.id or ""
    if btn_id.startswith("delete-"):
        item_id = btn_id[7:]  # strip "delete-"
        self._confirm_and_run(f"Delete {item_id}?", ...)
```

---

## Use Cases Beyond ACM-AI

This TUI pattern works for any project with multiple services:

| Project Type | Services to Monitor | Tabs to Add |
|-------------|--------------------|----|
| **AI/ML Pipeline** | Model server, vector DB, embedding worker, API | Model status, training jobs, inference metrics |
| **Microservices** | API gateway, auth, users, billing, queue | Per-service health, request rates, error rates |
| **Data Pipeline** | Airflow, Spark, database, S3 | DAG status, job runs, data quality |
| **DevOps** | Docker, Kubernetes, CI/CD | Container health, pod status, build pipeline |
| **Full-Stack App** | Frontend, API, database, cache, queue | Response times, cache hit rates, queue depth |

### Example: AI Agent Monitoring Dashboard

For an AI agent project, you might create tabs for:

```
Tab 1: Dashboard      — Agent status, model endpoints, vector DB health
Tab 2: Models         — Loaded models, VRAM usage, inference latency
Tab 3: Knowledge Base — Document counts, embedding status, index health
Tab 4: Workflows      — Active LangGraph runs, step progress, errors
Tab 5: Jobs           — Background tasks, queue depth, completion rate
Tab 6: Logs           — Agent conversation logs, API call logs
Tab 7: Errors         — Structured error aggregation
Tab 8: Config         — Runtime configuration, feature flags
```

---

## Troubleshooting

### TUI doesn't start

```bash
# Verify textual is installed
uv run python -c "import textual; print(textual.__version__)"

# Run with verbose errors
uv run python -m tui 2>tui-errors.log
```

### Dashboard shows "Checking..." forever

- The worker thread may have failed silently. Press `r` to force refresh.
- Check that Docker is running if SurrealDB shows as stopped.

### Database tab shows "Disconnected"

- SurrealDB must be running on the configured port (default 8000)
- Check `SURREAL_PORT`, `SURREAL_USER`, `SURREAL_PASSWORD` in `.env`
- The Database tab queries SurrealDB directly — it does not need the API server

### Extraction tab shows "API unavailable"

- The FastAPI server must be running on port 5055
- Start it with `s` (Start All) or manually: `uv run python run_api.py`

### Buttons don't respond

- Buttons that trigger destructive actions show a confirmation modal first
- Check that the Textual app has focus (click inside the terminal window)

---

## Related Documentation

- [Architecture Overview](architecture.md) — System design
- [Windows Setup](windows-setup.md) — Windows development environment
- [API Reference](api-reference.md) — REST API endpoints
- [Contributing Guide](contributing.md) — Development workflow
