@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Open Notebook - Windows Make Equivalent
:: Usage: make.bat <command>
:: Commands: start-all, stop-all, status, database, api, worker, frontend, dev, full, clean-cache

set "PROJECT_DIR=D:\ailocal\open-notebook"
cd /d "%PROJECT_DIR%"

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="start-all" goto start-all
if "%1"=="stop-all" goto stop-all
if "%1"=="status" goto status
if "%1"=="database" goto database
if "%1"=="api" goto api
if "%1"=="worker" goto worker
if "%1"=="worker-start" goto worker
if "%1"=="worker-stop" goto worker-stop
if "%1"=="worker-restart" goto worker-restart
if "%1"=="frontend" goto frontend
if "%1"=="run" goto frontend
if "%1"=="dev" goto dev
if "%1"=="full" goto full
if "%1"=="dev-docker" goto dev-docker
if "%1"=="dev-docker-stop" goto dev-docker-stop
if "%1"=="clean-cache" goto clean-cache
if "%1"=="lint" goto lint
if "%1"=="ruff" goto ruff

echo Unknown command: %1
goto help

:help
echo.
echo ========================================
echo   Open Notebook - Windows Make Commands
echo ========================================
echo.
echo Usage: make.bat ^<command^>
echo.
echo Service Management:
echo   start-all     Start all services (database + API + worker + frontend)
echo   stop-all      Stop all services
echo   status        Show status of all services
echo.
echo Individual Services:
echo   database      Start SurrealDB database
echo   api           Start FastAPI backend
echo   worker        Start background worker
echo   frontend      Start Next.js frontend (alias: run)
echo.
echo Worker Management:
echo   worker-stop     Stop the background worker
echo   worker-restart  Restart the background worker
echo.
echo Docker:
echo   dev           Run development Docker stack (original)
echo   dev-docker    Run development with hot-reload (recommended)
echo   dev-docker-stop  Stop development Docker stack
echo   full          Run full production Docker stack
echo.
echo Development:
echo   lint          Run mypy type checking
echo   ruff          Run ruff code formatting
echo   clean-cache   Clean Python cache directories
echo.
echo Access Points:
echo   Frontend:  http://localhost:8502
echo   API:       http://localhost:5055
echo   API Docs:  http://localhost:5055/docs
echo.
goto end

:database
echo Starting SurrealDB database...
docker ps --filter "name=surrealdb" --format "{{.Names}}" | findstr /i "surrealdb" >nul 2>&1
if %errorlevel% neq 0 (
    docker run -d --name surrealdb -p 8000:8000 -v "%PROJECT_DIR%/surreal_data:/mydata" surrealdb/surrealdb:v2 start --user root --pass root surrealkv://mydata/open_notebook.db
    echo SurrealDB started on port 8000
) else (
    echo SurrealDB is already running
)
goto end

:api
echo Starting API backend on port 5055...
start "Open Notebook - API" cmd /k "cd /d %PROJECT_DIR% && uv run python run_api.py"
goto end

:worker
echo Starting background worker...
start "Open Notebook - Worker" cmd /k "chcp 65001 >nul && cd /d %PROJECT_DIR% && set PYTHONIOENCODING=utf-8 && uv run surreal-commands-worker --import-modules commands"
goto end

:worker-stop
echo Stopping background worker...
taskkill /FI "WINDOWTITLE eq Open Notebook - Worker*" /F >nul 2>&1
echo Worker stopped
goto end

:worker-restart
echo Restarting background worker...
taskkill /FI "WINDOWTITLE eq Open Notebook - Worker*" /F >nul 2>&1
timeout /t 2 /nobreak >nul
start "Open Notebook - Worker" cmd /k "chcp 65001 >nul && cd /d %PROJECT_DIR% && set PYTHONIOENCODING=utf-8 && uv run surreal-commands-worker --import-modules commands"
echo Worker restarted
goto end

:frontend
echo Starting Next.js frontend on port 8502...
start "Open Notebook - Frontend" cmd /k "cd /d %PROJECT_DIR%\frontend && set PORT=8502 && npm run dev -- -p 8502"
goto end

:start-all
echo.
echo ========================================
echo   Open Notebook - Starting All Services
echo ========================================
echo.

echo [1/4] Starting SurrealDB...
docker ps --filter "name=surrealdb" --format "{{.Names}}" | findstr /i "surrealdb" >nul 2>&1
if %errorlevel% neq 0 (
    docker run -d --name surrealdb -p 8000:8000 -v "%PROJECT_DIR%/surreal_data:/mydata" surrealdb/surrealdb:v2 start --user root --pass root surrealkv://mydata/open_notebook.db
    timeout /t 3 /nobreak >nul
) else (
    echo SurrealDB is already running
)

echo [2/4] Starting API backend...
start "Open Notebook - API" cmd /k "cd /d %PROJECT_DIR% && uv run python run_api.py"
timeout /t 3 /nobreak >nul

echo [3/4] Starting background worker...
start "Open Notebook - Worker" cmd /k "chcp 65001 >nul && cd /d %PROJECT_DIR% && set PYTHONIOENCODING=utf-8 && uv run surreal-commands-worker --import-modules commands"
timeout /t 2 /nobreak >nul

echo [4/4] Starting Next.js frontend...
start "Open Notebook - Frontend" cmd /k "cd /d %PROJECT_DIR%\frontend && set PORT=8502 && npm run dev -- -p 8502"

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
echo   Close the windows to stop individual services.
echo   Or run: make.bat stop-all
echo ========================================
goto end

:stop-all
echo.
echo ========================================
echo   Open Notebook - Stopping All Services
echo ========================================
echo.

echo Stopping API Server...
taskkill /FI "WINDOWTITLE eq Open Notebook - API*" /F >nul 2>&1

echo Stopping Background Worker...
taskkill /FI "WINDOWTITLE eq Open Notebook - Worker*" /F >nul 2>&1

echo Stopping Frontend...
taskkill /FI "WINDOWTITLE eq Open Notebook - Frontend*" /F >nul 2>&1

echo Stopping SurrealDB container...
docker stop surrealdb >nul 2>&1
docker rm surrealdb >nul 2>&1

echo.
echo All services stopped!
goto end

:status
echo.
echo ========================================
echo   Open Notebook - Service Status
echo ========================================
echo.

echo Database (SurrealDB):
docker ps --filter "name=surrealdb" --format "  Status: {{.Status}}" 2>nul || echo   Not running

echo.
echo API Backend (port 5055):
curl -s http://localhost:5055/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   Status: Running (healthy)
) else (
    echo   Status: Not running
)

echo.
echo Frontend (port 8502):
curl -s http://localhost:8502 >nul 2>&1
if %errorlevel% equ 0 (
    echo   Status: Running
) else (
    curl -s http://localhost:3000 >nul 2>&1
    if %errorlevel% equ 0 (
        echo   Status: Running on port 3000
    ) else (
        echo   Status: Not running
    )
)

echo.
goto end

:dev
echo Starting development Docker stack...
docker compose -f docker-compose.dev.yml up --build
goto end

:dev-docker
echo.
echo ========================================
echo   Starting Development Docker Stack
echo   (with hot-reloading)
echo ========================================
echo.
echo This may take a few minutes on first run...
echo.
docker compose -f docker-compose.dev-local.yml up --build
goto end

:dev-docker-stop
echo Stopping development Docker stack...
docker compose -f docker-compose.dev-local.yml down
echo Development Docker stack stopped
goto end

:full
echo Starting full production Docker stack...
docker compose -f docker-compose.full.yml up --build
goto end

:lint
echo Running mypy type checking...
uv run python -m mypy .
goto end

:ruff
echo Running ruff code formatting...
uv run ruff check . --fix
goto end

:clean-cache
echo Cleaning cache directories...
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r %%d in (.mypy_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r %%d in (.ruff_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
del /s /q *.pyd 2>nul
echo Cache directories cleaned!
goto end

:end
endlocal
