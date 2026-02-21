"""
Ralph Sprint TUI - Live Dashboard
Real-time monitoring of Ralph autonomous sprint progress.

Usage:
    uv run --no-project --with textual --with rich python3 .ralph/ralph-tui.py
    # or shortcut:
    .ralph/ralph-tui.sh
"""
from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from rich.markup import escape
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Label,
    Log,
    ProgressBar,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class StoryProgress:
    story_id: str
    name: str
    done: int = 0
    todo: int = 0
    blocked: bool = False

    @property
    def total(self) -> int:
        return self.done + self.todo

    @property
    def pct(self) -> int:
        return int(self.done * 100 / self.total) if self.total > 0 else 0

    @property
    def status(self) -> str:
        if self.blocked:
            return "BLOCKED"
        if self.todo == 0 and self.done > 0:
            return "DONE"
        if self.done > 0 and self.todo > 0:
            return "IN PROGRESS"
        return "PENDING"


@dataclass
class SprintState:
    phase: str = "unknown"
    model: str = "unknown"
    story_index: int = 0
    completed: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)


@dataclass
class ProcessInfo:
    pid: int
    cpu: str
    mem: str
    uptime: str
    cmd: str


@dataclass
class DashboardData:
    stories: list[StoryProgress] = field(default_factory=list)
    tasks_done: int = 0
    tasks_todo: int = 0
    git_modified: int = 0
    git_untracked: int = 0
    git_diff_summary: str = ""
    new_files: list[str] = field(default_factory=list)
    sprint_state: SprintState = field(default_factory=SprintState)
    processes: list[ProcessInfo] = field(default_factory=list)
    claude_running: bool = False
    sprint_running: bool = False
    log_lines: list[str] = field(default_factory=list)
    remaining_tasks: list[tuple[str, str]] = field(default_factory=list)
    last_updated: str = ""

    @property
    def tasks_total(self) -> int:
        return self.tasks_done + self.tasks_todo


# ---------------------------------------------------------------------------
# Data collection (runs in thread)
# ---------------------------------------------------------------------------

PROJECT = Path(__file__).resolve().parent.parent if "__file__" in dir() else Path.cwd()
FIX_PLAN = PROJECT / ".ralph" / "@fix_plan.md"
LOGS_DIR = PROJECT / ".ralph" / "logs"


def _run(cmd: str, cwd: str | None = None) -> str:
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5,
            cwd=cwd or str(PROJECT),
        )
        return r.stdout.strip()
    except Exception:
        return ""


def parse_fix_plan() -> tuple[list[StoryProgress], list[tuple[str, str]]]:
    if not FIX_PLAN.exists():
        return [], []

    stories: list[StoryProgress] = []
    remaining: list[tuple[str, str]] = []
    current: StoryProgress | None = None
    text = FIX_PLAN.read_text(errors="replace")

    for line in text.splitlines():
        m = re.match(r"^## (E\d+-S\d+):\s+(.+)$", line)
        if m:
            current = StoryProgress(story_id=m.group(1), name=m.group(2))
            stories.append(current)
            # Check blocked in nearby lines
            if "BLOCKED" in line:
                current.blocked = True
            continue

        if current:
            if re.match(r"^- \[x\]", line):
                current.done += 1
            elif re.match(r"^- \[ \]", line):
                current.todo += 1
                task_text = re.sub(r"^- \[ \]\s*", "", line)
                remaining.append((current.story_id, task_text))
            if "BLOCKED" in line and current.todo > 0:
                current.blocked = True

    return stories, remaining


def get_sprint_log_dir() -> Path | None:
    if not LOGS_DIR.exists():
        return None
    dirs = sorted(LOGS_DIR.glob("sprint-*"), key=lambda p: p.name, reverse=True)
    return dirs[0] if dirs else None


def collect_data() -> DashboardData:
    data = DashboardData()
    data.last_updated = time.strftime("%H:%M:%S")

    # Fix plan
    data.stories, data.remaining_tasks = parse_fix_plan()
    data.tasks_done = sum(s.done for s in data.stories)
    data.tasks_todo = sum(s.todo for s in data.stories)

    # Git
    data.git_modified = len(_run("git diff --name-only").splitlines()) if _run("git diff --name-only") else 0
    untracked = _run("git ls-files --others --exclude-standard")
    data.new_files = untracked.splitlines() if untracked else []
    data.git_untracked = len(data.new_files)
    data.git_diff_summary = _run("git diff --stat") or "(no changes)"

    # Sprint state
    log_dir = get_sprint_log_dir()
    if log_dir:
        state_file = log_dir / "state.json"
        if state_file.exists():
            raw = state_file.read_text(errors="replace")
            phase_m = re.search(r'"phase"\s*:\s*"([^"]*)"', raw)
            model_m = re.search(r'"model"\s*:\s*"([^"]*)"', raw)
            idx_m = re.search(r'"story_index"\s*:\s*(\d+)', raw)
            data.sprint_state.phase = phase_m.group(1) if phase_m else "?"
            data.sprint_state.model = model_m.group(1) if model_m else "?"
            data.sprint_state.story_index = int(idx_m.group(1)) if idx_m else 0

        # Log tail
        sprint_log = log_dir / "sprint.log"
        if sprint_log.exists():
            lines = sprint_log.read_text(errors="replace").splitlines()
            data.log_lines = lines[-50:]

    # Processes
    ps_out = _run("ps aux")
    for line in ps_out.splitlines():
        if any(pat in line for pat in ["ralph_sprint", "claude.*-p", "dangerously-skip"]):
            if "grep" in line:
                continue
            parts = line.split(None, 10)
            if len(parts) >= 11:
                data.processes.append(ProcessInfo(
                    pid=int(parts[1]),
                    cpu=parts[2],
                    mem=parts[3],
                    uptime=parts[9],
                    cmd=parts[10][:120],
                ))

    # Status flags
    data.claude_running = bool(_run("pgrep -f 'claude.*dangerously-skip'"))
    data.sprint_running = bool(_run("pgrep -f ralph_sprint"))

    return data


# ---------------------------------------------------------------------------
# Custom widgets
# ---------------------------------------------------------------------------

class StatsBar(Static):
    """Top stats bar showing key metrics."""

    def update_data(self, d: DashboardData) -> None:
        pct = int(d.tasks_done * 100 / d.tasks_total) if d.tasks_total > 0 else 0

        # Status indicator
        if d.claude_running:
            status = "[bold green]● LIVE[/]"
        elif d.sprint_running:
            status = "[bold yellow]◌ WAITING[/]"
        else:
            status = "[bold red]■ STOPPED[/]"

        # Phase color
        phase_colors = {
            "init": "cyan", "dev": "green", "review": "yellow",
            "fix": "dark_orange", "test": "magenta", "complete": "bright_green",
        }
        pc = phase_colors.get(d.sprint_state.phase, "white")

        bar_filled = int(pct * 40 / 100)
        bar_empty = 40 - bar_filled
        if pct >= 75:
            bar_color = "green"
        elif pct >= 50:
            bar_color = "yellow"
        elif pct >= 25:
            bar_color = "dark_orange"
        else:
            bar_color = "red"

        bar = f"[{bar_color}]{'█' * bar_filled}[/][dim]{'░' * bar_empty}[/]"

        self.update(
            f" {status}  {bar} [bold]{pct}%[/]  "
            f"[dim]Tasks:[/] [bold]{d.tasks_done}[/]/{d.tasks_total}  "
            f"[dim]Left:[/] [bold yellow]{d.tasks_todo}[/]  "
            f"[dim]Phase:[/] [bold {pc}]{d.sprint_state.phase}[/]  "
            f"[dim]Model:[/] [bold]{d.sprint_state.model}[/]  "
            f"[dim]Git:[/] [yellow]{d.git_modified}[/]M+[green]{d.git_untracked}[/]N  "
            f"[dim]{d.last_updated}[/]"
        )


class StoryTable(Static):
    """Stories progress display."""

    def update_data(self, stories: list[StoryProgress]) -> None:
        lines: list[str] = []
        for s in stories:
            # Status badge
            if s.status == "DONE":
                badge = "[black on green] DONE [/]"
            elif s.status == "IN PROGRESS":
                badge = "[black on yellow] WIP  [/]"
            elif s.status == "BLOCKED":
                badge = "[white on red] BLOCK[/]"
            else:
                badge = "[white on #444] PEND [/]"

            # Mini progress bar
            if s.total > 0:
                bar_w = 20
                filled = int(s.done * bar_w / s.total)
                empty = bar_w - filled
                if s.pct >= 75:
                    bc = "green"
                elif s.pct >= 50:
                    bc = "yellow"
                else:
                    bc = "red"
                bar = f"[{bc}]{'█' * filled}[/][dim]{'·' * empty}[/]"
                nums = f"[bold]{s.done}[/]/{s.total}"
            else:
                bar = "[dim]{'·' * 20}[/]"
                nums = "[dim]—[/]"

            name = s.name[:45] + ".." if len(s.name) > 45 else s.name
            lines.append(
                f" {badge} [bold cyan]{s.story_id:<8}[/] {bar} {nums:>8}  [dim]{name}[/]"
            )

        self.update("\n".join(lines) if lines else "[dim]No stories found[/]")


class SprintLog(RichLog):
    """Color-coded sprint log viewer."""

    def add_lines(self, lines: list[str]) -> None:
        self.clear()
        for line in lines:
            if "ERROR" in line or "FAIL" in line or "blocked" in line:
                self.write(Text(line, style="bold red"))
            elif "PASS" in line or "COMPLETE" in line or "completed" in line:
                self.write(Text(line, style="bold green"))
            elif "SPRINT" in line:
                self.write(Text(line, style="cyan"))
            elif "STORY" in line:
                self.write(Text(line, style="yellow"))
            else:
                self.write(Text(line, style="dim"))


class ProcessView(Static):
    """Process and git info display."""

    def update_data(self, d: DashboardData) -> None:
        lines: list[str] = []

        lines.append("[bold cyan]── Claude/Ralph Processes ──[/]")
        if d.processes:
            for p in d.processes:
                cmd_short = p.cmd[:90] + "..." if len(p.cmd) > 90 else p.cmd
                lines.append(
                    f" [green]PID {p.pid}[/]  "
                    f"[dim]cpu:[/]{p.cpu}%  [dim]mem:[/]{p.mem}%  [dim]up:[/]{p.uptime}"
                )
                lines.append(f"   [dim]{escape(cmd_short)}[/]")
        else:
            lines.append(" [dim](no ralph processes found)[/]")

        lines.append("")
        lines.append("[bold yellow]── Git Diff Summary ──[/]")
        for gl in d.git_diff_summary.splitlines()[-15:]:
            if "insertion" in gl or "deletion" in gl:
                lines.append(f" [bold]{escape(gl)}[/]")
            elif "+" in gl:
                lines.append(f" [green]{escape(gl)}[/]")
            else:
                lines.append(f" [dim]{escape(gl)}[/]")

        lines.append("")
        lines.append(f"[bold green]── New Files ({d.git_untracked}) ──[/]")
        for f in d.new_files[:20]:
            lines.append(f" [green]+ {escape(f)}[/]")
        if d.git_untracked > 20:
            lines.append(f" [dim]... and {d.git_untracked - 20} more[/]")

        self.update("\n".join(lines))


class RemainingView(Static):
    """Remaining unchecked tasks."""

    def update_data(self, remaining: list[tuple[str, str]]) -> None:
        if not remaining:
            self.update("[bold green]  ✓ ALL TASKS COMPLETE![/]")
            return

        lines: list[str] = []
        lines.append(f"[bold]{len(remaining)} tasks remaining:[/]\n")
        for story_id, task in remaining:
            task_short = task[:70] + ".." if len(task) > 70 else task
            lines.append(f" [red]○[/] [bold yellow]{story_id:<8}[/] {escape(task_short)}")

        self.update("\n".join(lines))


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

REFRESH_INTERVAL = 3

CSS = """
Screen {
    background: $surface;
}

#stats-bar {
    height: 3;
    background: $boost;
    padding: 1 0;
    border-bottom: heavy $primary;
}

#main-tabs {
    height: 1fr;
}

StoryTable, ProcessView, RemainingView {
    padding: 1 2;
    overflow-y: auto;
}

SprintLog {
    padding: 0 1;
}

TabPane {
    padding: 0;
}

Footer {
    background: $boost;
}
"""


class RalphTUI(App):
    TITLE = "Ralph Sprint Dashboard"
    SUB_TITLE = "Live monitoring"
    CSS = CSS

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh Now"),
        Binding("1", "tab_stories", "Stories", show=True),
        Binding("2", "tab_logs", "Logs", show=True),
        Binding("3", "tab_process", "Process", show=True),
        Binding("4", "tab_remaining", "Remaining", show=True),
    ]

    data: reactive[DashboardData | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatsBar(id="stats-bar")
        with TabbedContent(id="main-tabs"):
            with TabPane("Stories", id="tab-stories"):
                yield StoryTable()
            with TabPane("Sprint Log", id="tab-logs"):
                yield SprintLog(max_lines=200)
            with TabPane("Process", id="tab-process"):
                yield ProcessView()
            with TabPane("Remaining", id="tab-remaining"):
                yield RemainingView()
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_data()
        self.set_interval(REFRESH_INTERVAL, self.refresh_data)

    @work(thread=True)
    def refresh_data(self) -> None:
        d = collect_data()
        self.call_from_thread(self._apply_data, d)

    def _apply_data(self, d: DashboardData) -> None:
        self.data = d

        self.query_one(StatsBar).update_data(d)
        self.query_one(StoryTable).update_data(d.stories)

        log_widget = self.query_one(SprintLog)
        log_widget.add_lines(d.log_lines)

        self.query_one(ProcessView).update_data(d)
        self.query_one(RemainingView).update_data(d.remaining_tasks)

        # Update subtitle
        if d.claude_running:
            self.sub_title = f"LIVE | {d.tasks_done}/{d.tasks_total} tasks | {d.last_updated}"
        else:
            self.sub_title = f"Idle | {d.tasks_done}/{d.tasks_total} tasks | {d.last_updated}"

    def action_refresh(self) -> None:
        self.refresh_data()

    def action_tab_stories(self) -> None:
        self.query_one(TabbedContent).active = "tab-stories"

    def action_tab_logs(self) -> None:
        self.query_one(TabbedContent).active = "tab-logs"

    def action_tab_process(self) -> None:
        self.query_one(TabbedContent).active = "tab-process"

    def action_tab_remaining(self) -> None:
        self.query_one(TabbedContent).active = "tab-remaining"


if __name__ == "__main__":
    app = RalphTUI()
    app.run()
