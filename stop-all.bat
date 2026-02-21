@echo off
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

echo Stopping Background Worker...
taskkill /FI "WINDOWTITLE eq ACM-AI - Worker*" /F >nul 2>&1

echo Stopping API Server...
taskkill /FI "WINDOWTITLE eq ACM-AI - API*" /F >nul 2>&1

echo Stopping SurrealDB...
docker compose down >nul 2>&1

echo.
echo ========================================
echo   All services stopped!
echo ========================================
echo.

echo Verification:
uv run python scripts/service_manager.py status 2>nul
