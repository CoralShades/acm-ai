@echo off
chcp 65001 >nul
echo ========================================
echo   Open Notebook - Starting All Services
echo ========================================
echo.

cd /d "D:\ailocal\open-notebook"

echo [1/4] Checking SurrealDB...
docker ps --filter "name=surrealdb" --format "{{.Names}}" | findstr /i "surrealdb" >nul
if %errorlevel% neq 0 (
    echo Starting SurrealDB...
    docker run -d --name surrealdb -p 8000:8000 -v "D:/ailocal/open-notebook/surreal_data:/mydata" surrealdb/surrealdb:v2 start --user root --pass root surrealkv://mydata/open_notebook.db
    timeout /t 3 /nobreak >nul
) else (
    echo SurrealDB is already running.
)
echo.

echo [2/4] Starting API Server (port 5055)...
start "Open Notebook - API" cmd /k "cd /d D:\ailocal\open-notebook && uv run python run_api.py"
timeout /t 3 /nobreak >nul
echo.

echo [3/4] Starting Background Worker...
start "Open Notebook - Worker" cmd /k "chcp 65001 >nul && cd /d D:\ailocal\open-notebook && set PYTHONIOENCODING=utf-8 && uv run surreal-commands-worker --import-modules commands"
timeout /t 2 /nobreak >nul
echo.

echo [4/4] Starting Frontend (port 8502)...
start "Open Notebook - Frontend" cmd /k "cd /d D:\ailocal\open-notebook\frontend && set PORT=8502 && npm run dev -- -p 8502"
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
