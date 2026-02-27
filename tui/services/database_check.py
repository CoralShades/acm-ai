"""SurrealDB queries via direct HTTP /sql endpoint.

Works even when the FastAPI API server is down — only needs SurrealDB running.
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from dataclasses import dataclass, field

from tui.config import (
    DB_TABLES,
    PROJECT_ROOT,
    SURREAL_AUTH,
    SURREAL_DB,
    SURREAL_HTTP_URL,
    SURREAL_NS,
)


@dataclass
class DbStatus:
    connected: bool = False
    url: str = ""
    namespace: str = ""
    database: str = ""
    error: str = ""


@dataclass
class TableCount:
    name: str = ""
    count: int = 0


@dataclass
class MigrationStatus:
    current_version: str = ""
    applied_at: str = ""
    total_migrations: int = 0
    error: str = ""


def _surreal_query(sql: str) -> list[dict]:
    """POST to SurrealDB HTTP /sql endpoint with Basic auth.

    Returns parsed JSON results list. Raises on connection error.
    """
    req = urllib.request.Request(
        f"{SURREAL_HTTP_URL}/sql",
        data=sql.encode("utf-8"),
        headers={
            "Accept": "application/json",
            "NS": SURREAL_NS,
            "DB": SURREAL_DB,
            "Authorization": f"Basic {SURREAL_AUTH}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    # SurrealDB returns a list of result objects
    if isinstance(body, list):
        return body
    return [body]


def get_db_status() -> DbStatus:
    """Ping SurrealDB via INFO FOR DB query."""
    try:
        _surreal_query("INFO FOR DB;")
        return DbStatus(
            connected=True,
            url=SURREAL_HTTP_URL,
            namespace=SURREAL_NS,
            database=SURREAL_DB,
        )
    except Exception as e:
        return DbStatus(
            connected=False,
            url=SURREAL_HTTP_URL,
            namespace=SURREAL_NS,
            database=SURREAL_DB,
            error=str(e),
        )


def get_table_counts() -> list[TableCount]:
    """Query record counts for all configured tables in a single batch."""
    queries = [
        f"SELECT count() as total FROM {table} GROUP ALL;"
        for table in DB_TABLES
    ]
    sql = "\n".join(queries)

    try:
        results = _surreal_query(sql)
    except Exception:
        return [TableCount(name=t, count=0) for t in DB_TABLES]

    counts = []
    for i, table in enumerate(DB_TABLES):
        count = 0
        if i < len(results):
            result = results[i]
            if result.get("status") == "OK" and result.get("result"):
                rows = result["result"]
                if rows and isinstance(rows, list) and len(rows) > 0:
                    count = rows[0].get("total", 0)
        counts.append(TableCount(name=table, count=count))
    return counts


def get_migration_status() -> MigrationStatus:
    """Check migration status from _sbl_migrations table."""
    try:
        results = _surreal_query(
            "SELECT * FROM _sbl_migrations ORDER BY version DESC LIMIT 1;"
        )
        if not results:
            return MigrationStatus(error="No results")

        result = results[0]
        if result.get("status") != "OK" or not result.get("result"):
            return MigrationStatus(error="No migrations table found")

        rows = result["result"]
        if not rows:
            return MigrationStatus(error="No migrations applied")

        latest = rows[0]
        # Count total migrations
        count_results = _surreal_query(
            "SELECT count() as total FROM _sbl_migrations GROUP ALL;"
        )
        total = 0
        if count_results and count_results[0].get("result"):
            cr = count_results[0]["result"]
            if cr and isinstance(cr, list) and len(cr) > 0:
                total = cr[0].get("total", 0)

        return MigrationStatus(
            current_version=str(latest.get("version", "")),
            applied_at=str(latest.get("applied_at", latest.get("created_at", ""))),
            total_migrations=total,
        )
    except Exception as e:
        return MigrationStatus(error=str(e))


def run_migrations() -> tuple[bool, str]:
    """Run database migrations via subprocess."""
    try:
        result = subprocess.run(
            [
                "uv", "run", "python", "-c",
                (
                    "import asyncio; "
                    "from open_notebook.database.async_migrate import AsyncMigrationManager; "
                    "asyncio.run(AsyncMigrationManager().run())"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
        if result.returncode == 0:
            return True, "Migrations completed successfully"
        return False, result.stderr.strip() or result.stdout.strip() or "Migration failed"
    except FileNotFoundError:
        return False, "uv not found"
    except subprocess.TimeoutExpired:
        return False, "Migration timed out (60s)"
