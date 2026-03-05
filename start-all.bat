@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo   ACM-AI - Starting All Services
echo ========================================
echo.

set "ACM_DIR=%~dp0"
cd /d "%ACM_DIR%"

REM Create logs directory
if not exist "%ACM_DIR%logs" mkdir "%ACM_DIR%logs"

echo [0/7] Syncing Python dependencies...
set UV_LINK_MODE=copy
uv sync --quiet
echo Dependencies synced.
echo.

echo [1/7] Running preflight checks...
uv run python scripts/preflight_checks.py
if %errorlevel% neq 0 (
    echo.
    echo PREFLIGHT FAILED — fix issues above before starting.
    echo.
    pause
    exit /b 1
)
echo.

echo [2/7] Clearing ports and killing stale processes...
REM Kill any leftover ACM-AI service windows from previous runs
taskkill /FI "WINDOWTITLE eq ACM-AI - Frontend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ACM-AI - Worker*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ACM-AI - API*" /F >nul 2>&1
REM Kill orphaned Windows processes by command line pattern
for /f "tokens=2 delims=," %%a in ('wmic process where "CommandLine like '%%run_api.py%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=2 delims=," %%a in ('wmic process where "CommandLine like '%%run_worker.py%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=2 delims=," %%a in ('wmic process where "CommandLine like '%%next dev%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do taskkill /F /PID %%a >nul 2>&1
REM Kill orphaned uvicorn multiprocessing workers via Python utility
REM (only kills children of dead parent PIDs — safe for other multiprocessing uses)
uv run python -c "from scripts._port_utils import _kill_orphaned_children; _kill_orphaned_children(5055)" >nul 2>&1
REM Kill any Windows process LISTENING on our ports (local address only)
for /f "tokens=2,5" %%a in ('netstat -ano 2^>nul ^| findstr "LISTENING"') do (
    echo %%a | findstr /E ":5055" >nul 2>&1 && taskkill /F /PID %%b >nul 2>&1
    echo %%a | findstr /E ":8502" >nul 2>&1 && taskkill /F /PID %%b >nul 2>&1
)
REM Kill WSL2-hosted processes (invisible to Windows taskkill)
wsl -- pkill -9 -f "run_api" >nul 2>&1
wsl -- pkill -9 -f "uvicorn.*5055" >nul 2>&1
wsl -- pkill -9 -f "run_worker" >nul 2>&1
wsl -- pkill -9 -f "next.*dev" >nul 2>&1
wsl -- fuser -k 5055/tcp >nul 2>&1
wsl -- fuser -k 8502/tcp >nul 2>&1
uv run python scripts/service_manager.py fix --auto-fix 2>nul
echo.

echo [3/7] Checking SurrealDB...
docker compose ps surrealdb 2>nul | findstr /i "running" >nul
if %errorlevel% neq 0 (
    echo Starting SurrealDB via Docker Compose...
    docker compose up -d surrealdb
    timeout /t 5 /nobreak >nul
) else (
    echo SurrealDB is already running.
)
REM Save SurrealDB startup logs
docker compose logs --no-color --tail 200 surrealdb > "%ACM_DIR%logs\surrealdb.log" 2>&1
echo.

REM Verify port 5055 is free before starting API (connect test)
echo Verifying port 5055 is free before starting API...
set "PORT_RETRIES=0"
:check_port_5055
curl -sf http://localhost:5055/health >nul 2>&1
if errorlevel 1 goto port_5055_free
set /a PORT_RETRIES+=1
if !PORT_RETRIES! GEQ 15 (
    echo ERROR: Port 5055 still responding after 15s. Cannot start API.
    echo Try running: wsl --shutdown
    echo Then re-run this script.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto check_port_5055
:port_5055_free
echo Port 5055 is free.
echo.

echo [4/7] Starting API Server (port 5055)...
start "ACM-AI - API" cmd /k "chcp 65001 >nul && cd /d %ACM_DIR% && set API_RELOAD=false && uv run python run_api.py"
echo Waiting for API to be ready...
:wait_api
timeout /t 2 /nobreak >nul
curl -sf http://localhost:5055/health >nul 2>&1
if %errorlevel% neq 0 goto wait_api
echo API Server is ready!
echo.

echo [5/7] Starting Background Worker...
start "ACM-AI - Worker" cmd /k "chcp 65001 >nul && cd /d %ACM_DIR% && set PYTHONIOENCODING=utf-8 && uv run python run_worker.py --import-modules commands"
timeout /t 2 /nobreak >nul
echo.

echo [6/7] Starting Frontend (port 8502)...
start "ACM-AI - Frontend" powershell -NoProfile -Command "cd '%ACM_DIR%frontend'; $env:PORT='8502'; npm run dev -- -p 8502 2>&1 | Tee-Object -FilePath '%ACM_DIR%logs\frontend.log'"
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
echo.
echo   Logs (persistent):
echo     API:       logs\api.log  (+ logs\api-error.log)
echo     Worker:    logs\worker.log  (+ logs\worker-error.log)
echo     SurrealDB: logs\surrealdb.log  (or: docker compose logs surrealdb)
echo     Frontend:  logs\frontend.log
echo ========================================
echo.

echo [7/7] Verifying service health...
timeout /t 5 /nobreak >nul
uv run python scripts/service_manager.py status 2>nul
endlocal
