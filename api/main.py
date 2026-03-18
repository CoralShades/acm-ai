# Load environment variables
from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# --- Loguru file logging ---
_log_dir = Path(__file__).resolve().parent.parent / "logs"
_log_dir.mkdir(exist_ok=True)
logger.add(
    _log_dir / "api.log",
    rotation="10 MB",
    retention="7 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
    backtrace=True,
    diagnose=False,
)
logger.add(
    _log_dir / "api-error.log",
    rotation="10 MB",
    retention="30 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
    backtrace=True,
    diagnose=True,
)

from api.auth import PasswordAuthMiddleware
from api.model_provisioning import run_model_provisioning
from open_notebook.observability.logfire_config import init_logfire

# Initialize Logfire -> Langfuse OTel bridge (non-fatal, before graph imports)
init_logfire()
from api.routers import (
    a2a,
    acm,
    agui_extraction,
    auth,
    chat,
    config,
    context,
    embedding,
    embedding_rebuild,
    episode_profiles,
    extraction_events,
    graph,
    insights,
    job_lifecycle,
    models,
    notebooks,
    notes,
    podcasts,
    search,
    settings,
    source_bulk,
    source_chat,
    sources,
    speaker_profiles,
    transformations,
    v3_streaming,
)
from api.routers import commands as commands_router
from api.sf_schema_provisioning import run_sf_schema_provisioning
from open_notebook.database.async_migrate import AsyncMigrationManager
from open_notebook.database.repository import repo_query

# Import commands to register them in the API process
try:
    logger.info("Commands imported in API process")
except Exception as e:
    logger.error(f"Failed to import commands in API process: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    Runs database migrations automatically on startup.
    """
    # Startup: Run database migrations
    logger.info("Starting API initialization...")

    try:
        migration_manager = AsyncMigrationManager()
        current_version = await migration_manager.get_current_version()
        logger.info(f"Current database version: {current_version}")

        if await migration_manager.needs_migration():
            logger.warning("Database migrations are pending. Running migrations...")
            await migration_manager.run_migration_up()
            new_version = await migration_manager.get_current_version()
            logger.success(
                f"Migrations completed successfully. Database is now at version {new_version}"
            )
        else:
            logger.info(
                "Database is already at the latest version. No migrations needed."
            )
    except Exception as e:
        logger.error(f"CRITICAL: Database migration failed: {str(e)}")
        logger.exception(e)
        # Fail fast - don't start the API with an outdated database schema
        raise RuntimeError(f"Failed to run database migrations: {str(e)}") from e

    # Auto-provision models from environment variables
    try:
        await run_model_provisioning()
    except Exception as e:
        logger.warning(f"Model provisioning failed (non-fatal): {e}")
        # Don't fail startup - models can be configured via UI

    # Load Salesforce field schema into DB (V3 Foundation)
    try:
        await run_sf_schema_provisioning()
    except Exception as e:
        logger.warning(f"SF schema provisioning failed (non-fatal): {e}")

    logger.success("API initialization completed successfully")

    # Yield control to the application
    yield

    # Shutdown: cleanup if needed
    logger.info("API shutdown complete")


app = FastAPI(
    title="ACM-AI API",
    description="API for ACM-AI - Asbestos Containing Material Register Analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# Add password authentication middleware first
# Exclude /api/auth/status and /api/config from authentication
app.add_middleware(
    PasswordAuthMiddleware,
    excluded_paths=[
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/auth/status",
        "/api/config",
        "/api/agui/chat",
        "/api/agui/crud-chat",
        "/.well-known/agent.json",
    ],
)

# Add CORS middleware last (so it processes first)
_cors_env = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
_cors_origins: list[str] = (
    [o.strip() for o in _cors_env.split(",") if o.strip()]
    if _cors_env != "*"
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(notebooks.router, prefix="/api", tags=["notebooks"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(transformations.router, prefix="/api", tags=["transformations"])
app.include_router(notes.router, prefix="/api", tags=["notes"])
app.include_router(embedding.router, prefix="/api", tags=["embedding"])
app.include_router(
    embedding_rebuild.router, prefix="/api/embeddings", tags=["embeddings"]
)
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(context.router, prefix="/api", tags=["context"])
app.include_router(sources.router, prefix="/api", tags=["sources"])
app.include_router(insights.router, prefix="/api", tags=["insights"])
app.include_router(commands_router.router, prefix="/api", tags=["commands"])
app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])
app.include_router(episode_profiles.router, prefix="/api", tags=["episode-profiles"])
app.include_router(speaker_profiles.router, prefix="/api", tags=["speaker-profiles"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(source_chat.router, prefix="/api", tags=["source-chat"])
app.include_router(acm.router, prefix="/api/acm", tags=["acm"])
app.include_router(extraction_events.router, prefix="/api", tags=["extraction-events"])
app.include_router(a2a.router, prefix="/api", tags=["a2a"])
app.include_router(agui_extraction.router, prefix="/api", tags=["agui-extraction"])
app.include_router(source_bulk.router, prefix="/api", tags=["source-bulk"])
app.include_router(v3_streaming.router, prefix="/api", tags=["v3-streaming"])
app.include_router(graph.router, prefix="/api", tags=["graph"])
app.include_router(job_lifecycle.router, prefix="/api", tags=["job-lifecycle"])

# Mount static files for A2A agent card (.well-known)
from pathlib import Path as _Path

from fastapi.staticfiles import StaticFiles

_static_dir = _Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount(
        "/.well-known",
        StaticFiles(directory=str(_static_dir / ".well-known")),
        name="well-known",
    )

# Register AG-UI endpoint for CopilotKit integration
try:
    from api.routers.agui_chat import register_agui_endpoints

    register_agui_endpoints(app)
except Exception as e:
    logger.warning(f"AG-UI endpoint registration failed (non-fatal): {e}")

# Register AG-UI CRUD chat endpoint (E19-S8)
try:
    from api.routers.agui_chat import register_crud_agui_endpoint

    register_crud_agui_endpoint(app)
except Exception as e:
    logger.warning(f"AG-UI CRUD endpoint registration failed (non-fatal): {e}")


@app.get("/")
async def root():
    return {"message": "ACM-AI API is running"}


@app.get("/health")
async def health():
    """Basic liveness check - returns 200 if API is up."""
    return {"status": "healthy"}


@app.get("/health/ready")
async def health_ready():
    """Readiness check - verifies SurrealDB connectivity.

    Returns:
        200 OK if database is reachable
        503 Service Unavailable if database is down
    """
    try:
        # 2-second timeout for database health check
        result = await asyncio.wait_for(repo_query("RETURN 1"), timeout=2.0)
        if result:
            return {"status": "ready", "database": "connected"}
        return {"status": "not_ready", "database": "offline", "error": "Empty result"}
    except asyncio.TimeoutError:
        logger.warning("Database health check timed out after 2 seconds")
        return {"status": "not_ready", "database": "offline", "error": "Timeout"}
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return {"status": "not_ready", "database": "offline", "error": str(e)}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with all component status.

    Returns component health for:
    - SurrealDB connectivity
    - Worker process status
    - Last extraction timestamp
    - API uptime
    - Memory usage
    """
    # Track API start time for uptime calculation
    if not hasattr(health_detailed, "_start_time"):
        health_detailed._start_time = time.time()

    uptime_seconds = int(time.time() - health_detailed._start_time)

    # Check database connectivity
    db_status = "connected"
    db_error = None
    try:
        result = await asyncio.wait_for(repo_query("RETURN 1"), timeout=2.0)
        if not result:
            db_status = "disconnected"
            db_error = "Empty result"
    except asyncio.TimeoutError:
        db_status = "disconnected"
        db_error = "Timeout after 2s"
    except Exception as e:
        db_status = "disconnected"
        db_error = str(e)

    # Check worker process via PID file
    worker_status = "unknown"
    worker_pid = None
    pid_file = os.environ.get("WORKER_PID_FILE", ".pids/worker.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file) as f:
                worker_pid = int(f.read().strip())
            # Check if process is running
            try:
                os.kill(worker_pid, 0)  # Signal 0 = check if process exists
                worker_status = "running"
            except ProcessLookupError:
                worker_status = "stopped"
                worker_pid = None
        except Exception:
            worker_status = "stopped"

    # Get last extraction time from database
    last_extraction = None
    try:
        result = await asyncio.wait_for(
            repo_query(
                """
                SELECT created_at FROM extraction_progress
                ORDER BY created_at DESC LIMIT 1
                """
            ),
            timeout=2.0,
        )
        if result and len(result) > 0:
            last_extraction = result[0].get("created_at")
    except Exception:
        pass

    # Get memory usage (basic - using stdlib only)
    try:
        import resource

        memory_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in KB; on macOS, it's in bytes
        if os.uname().sysname == "Darwin":
            memory_mb = memory_kb / 1024 / 1024
        else:
            memory_mb = memory_kb / 1024
    except Exception:
        memory_mb = 0  # Fallback if resource module unavailable

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": {
                "status": db_status,
                "error": db_error,
            },
            "worker": {
                "status": worker_status,
                "pid": worker_pid,
            },
            "api": {
                "uptime_seconds": uptime_seconds,
                "memory_mb": round(memory_mb, 2),
            },
        },
        "last_extraction": last_extraction,
    }
