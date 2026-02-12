@echo off
chcp 65001 >nul
echo ========================================
echo   ACM-AI - Starting All Services
echo ========================================
echo.

cd /d "D:\ailocal\acm-ai"

echo [0/5] Running pre-flight checks...
uv run python scripts/service_manager.py check 2>nul
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Some pre-flight checks failed. Continuing anyway...
    timeout /t 2 /nobreak >nul
)
echo.

echo [1/5] Syncing Python dependencies...
set UV_LINK_MODE=copy
uv sync --quiet
echo Dependencies synced.
echo.

echo [2/5] Checking SurrealDB...
docker compose ps surrealdb 2>nul | findstr /i "running" >nul
if %errorlevel% neq 0 (
    echo Starting SurrealDB via Docker Compose...
    docker compose up -d surrealdb
    timeout /t 5 /nobreak >nul
) else (
    echo SurrealDB is already running.
)
echo.

echo [3/5] Starting API Server (port 5055)...
start "ACM-AI - API" cmd /k "chcp 65001 >nul && cd /d D:\ailocal\acm-ai && uv run python run_api.py"
timeout /t 3 /nobreak >nul
echo.

echo [4/5] Starting Background Worker...
start "ACM-AI - Worker" cmd /k "chcp 65001 >nul && cd /d D:\ailocal\acm-ai && set PYTHONIOENCODING=utf-8 && uv run surreal-commands-worker --import-modules commands"
timeout /t 2 /nobreak >nul
echo.

echo [5/5] Starting Frontend (port 8502)...
start "ACM-AI - Frontend" cmd /k "cd /d D:\ailocal\acm-ai\frontend && set PORT=8502 && npm run dev -- -p 8502"
echo.

echo ========================================
echo   All services started!
echo ========================================
echo.
echo   Frontend:  http://localhost:8502
echo   API:       http://localhost:5055
echo   API Docs:  http://localhost:5055/docs
echo.
echo   Each service runs in its own window.
echo   Close the windows to stop services.
echo ========================================
echo.

echo Verifying service health...
timeout /t 5 /nobreak >nul
uv run python scripts/service_manager.py status 2>nul
