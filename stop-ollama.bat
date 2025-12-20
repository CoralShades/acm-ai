@echo off
chcp 65001 >nul
echo ========================================
echo   ACM-AI - Stopping Ollama
echo ========================================
echo.

cd /d "D:\ailocal\acm-ai"

echo Stopping Ollama container...
docker stop acm-ai-ollama 2>nul
docker rm acm-ai-ollama 2>nul

echo.
echo Ollama stopped.
echo.
echo Note: Model data is preserved in Docker volume 'acm-ai-ollama-data'
echo To remove models: docker volume rm acm-ai-ollama-data
echo.
pause
