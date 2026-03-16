#!/usr/bin/env python
"""Historical log splitter — parse monolithic logs into per-run directories.

Reads logs/acm-extraction.log to identify extraction run boundaries,
then slices matching entries from worker.log and api.log into
per-run directories under logs/runs/<timestamp>_<source_suffix>/.

Each directory contains:
  - extraction.log  — [PIPELINE] lines for this run
  - worker.log      — worker log entries from the same time window
  - api.log         — API log entries from the same time window
  - summary.txt     — auto-generated run metadata

Usage:
    uv run python scripts/split_logs.py [--log-dir logs] [--dry-run] [--source-id SOURCE_ID]
"""

import argparse
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Regex for extraction.log timestamps: [YYYY-MM-DD HH:MM:SS]
_EXTRACTION_TS_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")

# Regex for loguru timestamps: YYYY-MM-DD HH:mm:ss.SSS
_LOGURU_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")

# Run boundary markers in extraction.log
_START_RE = re.compile(
    r"\[PIPELINE\] Starting extraction for (source:\S+)"
)
_END_RE = re.compile(
    r"\[PIPELINE\] EXTRACTION (COMPLETE|FAILED)"
)


def _parse_extraction_ts(line: str) -> datetime | None:
    m = _EXTRACTION_TS_RE.match(line)
    if m:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    return None


def _parse_loguru_ts(line: str) -> datetime | None:
    m = _LOGURU_TS_RE.match(line)
    if m:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S.%f").replace(
            tzinfo=timezone.utc
        )
    return None


def _find_runs(extraction_log: Path) -> list[dict]:
    """Parse extraction.log to find run boundaries."""
    runs: list[dict] = []
    current: dict | None = None

    for line in extraction_log.read_text(encoding="utf-8", errors="replace").splitlines():
        ts = _parse_extraction_ts(line)
        if not ts:
            continue

        start_m = _START_RE.search(line)
        if start_m:
            current = {
                "source_id": start_m.group(1),
                "start_ts": ts,
                "end_ts": None,
                "lines": [line],
            }
            continue

        if current:
            current["lines"].append(line)

        end_m = _END_RE.search(line)
        if end_m and current:
            current["end_ts"] = ts
            # Parse record count from COMPLETE line
            count_m = re.search(r"(\d+) records", line)
            current["record_count"] = int(count_m.group(1)) if count_m else 0
            current["status"] = end_m.group(1)
            runs.append(current)
            current = None

    # Handle unclosed runs (pipeline crashed without COMPLETE/FAILED)
    if current:
        current["end_ts"] = current["start_ts"] + timedelta(minutes=30)
        current["status"] = "INCOMPLETE"
        current["record_count"] = 0
        runs.append(current)

    return runs


def _slice_loguru_file(
    log_path: Path,
    start: datetime,
    end: datetime,
    buffer_before: timedelta = timedelta(seconds=30),
    buffer_after: timedelta = timedelta(minutes=5),
) -> list[str]:
    """Extract lines from a loguru-formatted log file within a time window."""
    if not log_path.exists():
        return []

    window_start = start - buffer_before
    window_end = end + buffer_after
    result: list[str] = []

    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        ts = _parse_loguru_ts(line)
        if ts and window_start <= ts <= window_end:
            result.append(line)
        elif not ts and result:
            # Continuation line (traceback, multiline log) — include if we're inside window
            result.append(line)

    return result


def _generate_summary(run: dict, worker_lines: int, api_lines: int) -> str:
    """Generate summary.txt content for a historical run."""
    duration = (run["end_ts"] - run["start_ts"]).total_seconds()
    return "\n".join([
        f"Source ID:    {run['source_id']}",
        f"Run ID:      (historical — unknown)",
        f"Started:     {run['start_ts'].isoformat()}",
        f"Ended:       {run['end_ts'].isoformat()}",
        f"Duration:    {duration:.1f}s",
        f"Status:      {run['status']}",
        f"Records:     {run.get('record_count', 'unknown')}",
        f"",
        f"Log lines:",
        f"  extraction.log: {len(run['lines'])}",
        f"  worker.log:     {worker_lines}",
        f"  api.log:        {api_lines}",
        "",
    ])


# Source IDs that are test fixtures — skip by default
_TEST_SOURCES = {"source:test", "source:empty", "source:123", "source:test/fail"}


def _is_test_source(source_id: str) -> bool:
    """Check if source_id is a test fixture."""
    return (
        source_id in _TEST_SOURCES
        or source_id.startswith("source:test_")
        or source_id == "source:broadmeadows_e2e_test"
    )


def main():
    parser = argparse.ArgumentParser(description="Split monolithic logs into per-run directories")
    parser.add_argument("--log-dir", default="logs", help="Log directory (default: logs)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    parser.add_argument("--source-id", help="Filter to a specific source ID")
    parser.add_argument("--include-tests", action="store_true", help="Include test fixture runs")
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    extraction_log = log_dir / "acm-extraction.log"

    if not extraction_log.exists():
        print(f"No extraction log found at {extraction_log}")
        return

    runs = _find_runs(extraction_log)
    if args.source_id:
        runs = [r for r in runs if args.source_id in r["source_id"]]
    if not args.include_tests:
        before = len(runs)
        runs = [r for r in runs if not _is_test_source(r["source_id"])]
        skipped_tests = before - len(runs)
        if skipped_tests:
            print(f"Skipped {skipped_tests} test fixture run(s) (use --include-tests to include)")

    print(f"Found {len(runs)} extraction run(s) in {extraction_log}")

    runs_dir = log_dir / "runs"
    created = 0
    skipped = 0
    _seen_dirs: set[str] = set()

    for run in runs:
        ts_str = run["start_ts"].strftime("%Y-%m-%dT%H-%M-%S")
        suffix = run["source_id"].replace("source:", "")[-12:]
        base_name = f"{ts_str}_{suffix}"

        # Handle timestamp collisions by appending a counter
        dir_name = base_name
        counter = 1
        while dir_name in _seen_dirs or (runs_dir / dir_name).exists():
            counter += 1
            dir_name = f"{base_name}_{counter}"
        _seen_dirs.add(dir_name)
        run_dir = runs_dir / dir_name

        if run_dir.exists():
            skipped += 1
            continue

        if args.dry_run:
            print(f"  [DRY RUN] Would create: {run_dir}/")
            print(f"            Source: {run['source_id']}, Status: {run['status']}, "
                  f"Records: {run.get('record_count', '?')}")
            created += 1
            continue

        run_dir.mkdir(parents=True, exist_ok=True)

        # Write extraction.log
        (run_dir / "extraction.log").write_text(
            f"# Historical extraction run (split from monolithic log)\n"
            f"# Source: {run['source_id']}\n"
            f"# Period: {run['start_ts'].isoformat()} to {run['end_ts'].isoformat()}\n\n"
            + "\n".join(run["lines"]) + "\n",
            encoding="utf-8",
        )

        # Slice worker.log
        worker_lines = _slice_loguru_file(
            log_dir / "worker.log", run["start_ts"], run["end_ts"]
        )
        if worker_lines:
            (run_dir / "worker.log").write_text(
                "\n".join(worker_lines) + "\n", encoding="utf-8"
            )

        # Slice api.log
        api_lines = _slice_loguru_file(
            log_dir / "api.log", run["start_ts"], run["end_ts"]
        )
        if api_lines:
            (run_dir / "api.log").write_text(
                "\n".join(api_lines) + "\n", encoding="utf-8"
            )

        # Generate summary.txt
        (run_dir / "summary.txt").write_text(
            _generate_summary(run, len(worker_lines), len(api_lines)),
            encoding="utf-8",
        )

        created += 1
        print(f"  Created: {run_dir.name} ({run['status']}, {run.get('record_count', '?')} records)")

    print(f"\nDone: {created} created, {skipped} skipped (already exist)")


if __name__ == "__main__":
    main()
