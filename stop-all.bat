@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo   ACM-AI - Stopping All Services
echo ========================================
echo.

cd /d "%~dp0"

echo Current status:
uv run python scripts/service_manager.py status 2>nul
echo.

echo Stopping Frontend...
taskkill /FI "WINDOWTITLE eq ACM-AI - Frontend*" /F >nul 2>&1
REM Kill orphaned node/next processes (Windows)
for /f "tokens=2 delims=," %%a in ('wmic process where "CommandLine like '%%next dev%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do taskkill /F /PID %%a >nul 2>&1

echo Stopping Background Worker...
taskkill /FI "WINDOWTITLE eq ACM-AI - Worker*" /F >nul 2>&1
REM Kill orphaned worker processes (Windows)
for /f "tokens=2 delims=," %%a in ('wmic process where "CommandLine like '%%run_worker.py%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do taskkill /F /PID %%a >nul 2>&1

echo Stopping API Server...
taskkill /FI "WINDOWTITLE eq ACM-AI - API*" /F >nul 2>&1
REM Kill orphaned API processes (Windows)
for /f "tokens=2 delims=," %%a in ('wmic process where "CommandLine like '%%run_api.py%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do taskkill /F /PID %%a >nul 2>&1
REM Kill orphaned uvicorn multiprocessing workers via Python utility
REM (only kills children of dead parent PIDs — safe for other multiprocessing uses)
uv run python -c "from scripts._port_utils import _kill_orphaned_children; _kill_orphaned_children(5055)" >nul 2>&1
REM Kill any Windows process LISTENING on port 5055 (local address only)
for /f "tokens=2,5" %%a in ('netstat -ano 2^>nul ^| findstr "LISTENING"') do (
    echo %%a | findstr /E ":5055" >nul 2>&1 && taskkill /F /PID %%b >nul 2>&1
)

REM Kill WSL2-hosted processes (invisible to Windows taskkill)
echo Killing any WSL2 processes on our ports...
wsl -- pkill -9 -f "run_api" >nul 2>&1
wsl -- pkill -9 -f "uvicorn.*5055" >nul 2>&1
wsl -- pkill -9 -f "run_worker" >nul 2>&1
wsl -- pkill -9 -f "next.*dev" >nul 2>&1
wsl -- fuser -k 5055/tcp >nul 2>&1
wsl -- fuser -k 8502/tcp >nul 2>&1

echo Stopping SurrealDB...
docker compose down >nul 2>&1

echo.
REM Verify port 5055 is free (connect test — fails = port is free)
echo Verifying port 5055 is available...
set "PORT_FREE=0"
for /L %%i in (1,1,15) do (
    if "!PORT_FREE!"=="0" (
        curl -sf http://localhost:5055/health >nul 2>&1
        if errorlevel 1 (
            set "PORT_FREE=1"
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)
if "!PORT_FREE!"=="0" (
    echo [WARN] Port 5055 still responds after 15s. Try: wsl --shutdown
) else (
    echo Port 5055 is free.
)

echo.
echo ========================================
echo   All services stopped!
echo ========================================
echo.

echo Verification:
uv run python scripts/service_manager.py status 2>nul
echo.
echo Running shutdown cleanup...
uv run python scripts\shutdown_cleanup.py
endlocal
