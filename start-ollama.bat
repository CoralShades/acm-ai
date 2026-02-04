@echo off
chcp 65001 >nul
echo ========================================
echo   ACM-AI - Ollama Local AI Setup
echo ========================================
echo.

cd /d "D:\ailocal\acm-ai"

echo Choose your Ollama configuration:
echo.
echo   [1] CPU-only    (office laptops, VMs, no GPU)
echo   [2] NVIDIA GPU  (developer machines with GPU)
echo   [3] Skip        (use cloud AI providers only)
echo.

set /p choice="Enter choice (1/2/3): "

if "%choice%"=="1" goto cpu
if "%choice%"=="2" goto gpu
if "%choice%"=="3" goto skip
echo Invalid choice. Exiting.
goto end

:cpu
echo.
echo Starting Ollama (CPU-only mode)...
docker compose --profile ollama-cpu up -d
goto setup_models

:gpu
echo.
echo Starting Ollama (GPU mode)...
docker compose --profile ollama-gpu up -d
goto setup_models

:setup_models
echo.
echo Waiting for Ollama to start...
timeout /t 10 /nobreak >nul

echo.
echo Checking Ollama health...
docker exec acm-ai-ollama curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama is still starting, waiting longer...
    timeout /t 15 /nobreak >nul
)

echo.
echo ========================================
echo   Pull AI Models (Optional)
echo ========================================
echo.
echo Do you want to pull recommended models now?
echo   - qwen3 (language model, ~4GB)
echo   - mxbai-embed-large (embeddings, ~670MB)
echo.
set /p pullmodels="Pull models? (y/n): "

if /i "%pullmodels%"=="y" (
    echo.
    echo Pulling qwen3 (this may take a few minutes)...
    docker exec acm-ai-ollama ollama pull qwen3
    echo.
    echo Pulling mxbai-embed-large...
    docker exec acm-ai-ollama ollama pull mxbai-embed-large
    echo.
    echo Models pulled successfully!
)

echo.
echo ========================================
echo   Ollama Setup Complete!
echo ========================================
echo.
echo   Ollama URL: http://localhost:11434
echo.
echo   Add this to your .env file:
echo   OLLAMA_API_BASE=http://ollama:11434
echo.
echo   Then configure models in the app:
echo   - Language Model: qwen3
echo   - Embedding Model: mxbai-embed-large
echo.
goto end

:skip
echo.
echo Skipping Ollama setup.
echo You can use cloud AI providers (OpenAI, Anthropic, etc.)
echo.
goto end

:end
echo.
pause
