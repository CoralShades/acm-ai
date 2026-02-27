"""API calls for ACM extraction jobs, stats, and export.

Requires the FastAPI server running on API_PORT.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime

from tui.config import API_BASE_URL, EXPORTS_DIR


@dataclass
class AcmStats:
    total_records: int = 0
    high_risk: int = 0
    medium_risk: int = 0
    low_risk: int = 0
    building_count: int = 0
    room_count: int = 0
    error: str = ""


@dataclass
class JobInfo:
    job_id: str = ""
    command: str = ""
    status: str = ""
    source: str = ""
    created_at: str = ""


def _api_get(path: str, timeout: int = 10) -> dict | list | bytes:
    """GET from FastAPI backend. Returns parsed JSON."""
    req = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        data = resp.read()
        if "json" in content_type:
            return json.loads(data.decode("utf-8"))
        return data


def _api_post(path: str, body: dict | None = None, timeout: int = 30) -> dict:
    """POST to FastAPI backend. Returns parsed JSON."""
    payload = json.dumps(body).encode("utf-8") if body else b""
    req = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _api_delete(path: str, timeout: int = 10) -> dict:
    """DELETE to FastAPI backend. Returns parsed JSON."""
    req = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        headers={"Accept": "application/json"},
        method="DELETE",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_acm_stats() -> AcmStats:
    """GET /api/acm/stats — ACM record statistics."""
    try:
        data = _api_get("/api/acm/stats")
        if isinstance(data, dict):
            return AcmStats(
                total_records=data.get("total_records", 0),
                high_risk=data.get("high_risk_count", 0),
                medium_risk=data.get("medium_risk_count", 0),
                low_risk=data.get("low_risk_count", 0),
                building_count=data.get("building_count", 0),
                room_count=data.get("room_count", 0),
            )
        return AcmStats(error="Unexpected response format")
    except Exception as e:
        return AcmStats(error=str(e))


def list_jobs(limit: int = 20) -> list[JobInfo]:
    """GET /api/commands/jobs — list recent command jobs."""
    try:
        data = _api_get(f"/api/commands/jobs?limit={limit}")
        if not isinstance(data, list):
            return []
        jobs = []
        for item in data:
            jobs.append(
                JobInfo(
                    job_id=str(item.get("id", "")),
                    command=str(item.get("command", "")),
                    status=str(item.get("status", "")),
                    source=str(item.get("input", {}).get("source_id", ""))
                    if isinstance(item.get("input"), dict)
                    else "",
                    created_at=str(item.get("created_at", "")),
                )
            )
        return jobs
    except Exception:
        return []


def cancel_job(job_id: str) -> tuple[bool, str]:
    """DELETE /api/commands/jobs/{job_id} — cancel a running job."""
    try:
        _api_delete(f"/api/commands/jobs/{job_id}")
        return True, f"Job {job_id} cancelled"
    except Exception as e:
        return False, str(e)


def trigger_export(fmt: str, source_id: str = "") -> tuple[bool, str]:
    """GET /api/acm/export/{fmt} — download export file.

    Saves to PROJECT_ROOT/exports/acm_export_{timestamp}.{ext}
    """
    ext = "xlsx" if fmt == "excel" else "csv"
    try:
        # Build query params
        params = f"?source_id={source_id}" if source_id else ""
        req = urllib.request.Request(
            f"{API_BASE_URL}/api/acm/export/{ext}{params}",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()

        # Save to exports directory
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"acm_export_{timestamp}.{ext}"
        filepath = EXPORTS_DIR / filename
        filepath.write_bytes(data)
        return True, f"Exported to {filepath}"
    except Exception as e:
        return False, str(e)


def trigger_reembed() -> tuple[bool, str]:
    """POST /api/commands/jobs — submit re-embed job."""
    try:
        body = {
            "command": "rebuild_embeddings",
            "app": "open_notebook",
            "input": {
                "mode": "all",
                "include_sources": True,
                "include_notes": True,
            },
        }
        result = _api_post("/api/commands/jobs", body)
        job_id = result.get("id", "unknown")
        return True, f"Re-embed job submitted: {job_id}"
    except Exception as e:
        return False, str(e)


def submit_rebuild_embeddings() -> tuple[bool, str]:
    """POST /api/commands/jobs — submit rebuild embeddings job."""
    try:
        body = {
            "command": "rebuild_embeddings",
            "app": "open_notebook",
            "input": {
                "mode": "all",
                "include_sources": True,
                "include_notes": True,
            },
        }
        result = _api_post("/api/commands/jobs", body)
        job_id = result.get("id", "unknown")
        return True, f"Rebuild embeddings job submitted: {job_id}"
    except Exception as e:
        return False, str(e)
