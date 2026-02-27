"""Log file reading, error extraction, and extraction summaries."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from tui.config import LOGS_DIR


@dataclass
class ExtractionSummary:
    timestamp: str
    record_count: int
    duration_seconds: float


@dataclass
class ErrorEntry:
    file: str
    line_number: int
    timestamp: str
    level: str
    message: str


@dataclass
class ErrorGroup:
    file: str
    count: int
    last_occurrence: str
    sample_message: str


def list_log_files() -> list[Path]:
    """Return all .log files in the logs directory, sorted by modification time."""
    if not LOGS_DIR.exists():
        return []
    logs = list(LOGS_DIR.glob("*.log"))
    logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return logs


def read_log_file(path: Path, max_lines: int = 500) -> list[str]:
    """Read last N lines of a log file."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]
    except OSError:
        return []


def get_last_extraction(log_dir: Path | None = None) -> ExtractionSummary | None:
    """Parse logs for the last EXTRACTION COMPLETE line."""
    search_dir = log_dir or LOGS_DIR
    pattern = re.compile(
        r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*EXTRACTION COMPLETE.*?(\d+)\s*records?\s*in\s*([\d.]+)s"
    )

    for log_file in sorted(search_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in reversed(lines):
                m = pattern.search(line)
                if m:
                    return ExtractionSummary(
                        timestamp=m.group(1),
                        record_count=int(m.group(2)),
                        duration_seconds=float(m.group(3)),
                    )
        except OSError:
            continue
    return None


_ERROR_PATTERN = re.compile(r"\b(ERROR|WARNING|CRITICAL|FAIL)\b", re.IGNORECASE)
_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")


def scan_errors(hours: int = 24) -> list[ErrorEntry]:
    """Scan all log files for error-level lines from the last N hours."""
    cutoff = datetime.now() - timedelta(hours=hours)
    entries: list[ErrorEntry] = []

    for log_file in list_log_files():
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for i, line in enumerate(lines, 1):
            m = _ERROR_PATTERN.search(line)
            if not m:
                continue

            level = m.group(1).upper()
            # Try to parse timestamp
            ts_match = _TIMESTAMP_PATTERN.search(line)
            timestamp = ts_match.group(0) if ts_match else ""

            # Filter by time if we have a timestamp
            if timestamp:
                try:
                    line_time = datetime.fromisoformat(timestamp.replace("T", " "))
                    if line_time < cutoff:
                        continue
                except ValueError:
                    pass

            entries.append(
                ErrorEntry(
                    file=log_file.name,
                    line_number=i,
                    timestamp=timestamp,
                    level=level,
                    message=line.strip()[:200],
                )
            )
    return entries


def group_errors(entries: list[ErrorEntry]) -> list[ErrorGroup]:
    """Group error entries by file."""
    groups: dict[str, ErrorGroup] = {}
    for e in entries:
        if e.file not in groups:
            groups[e.file] = ErrorGroup(
                file=e.file,
                count=0,
                last_occurrence=e.timestamp,
                sample_message=e.message,
            )
        g = groups[e.file]
        g.count += 1
        if e.timestamp > g.last_occurrence:
            g.last_occurrence = e.timestamp
            g.sample_message = e.message
    return sorted(groups.values(), key=lambda g: g.count, reverse=True)
