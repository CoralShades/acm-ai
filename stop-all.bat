@echo off
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

echo.
echo ========================================
echo   All services stopped!
echo ========================================
