@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo   ACM-AI - Restarting All Services
echo ========================================
echo.

cd /d "%~dp0"

REM Uncomment the next line if you want to pause the Cloudflare tunnel during restart:
REM net stop "Cloudflare Tunnel Agent" >nul 2>&1 && set "CF_WAS_RUNNING=1"

call stop-all.bat
echo.
echo ----------------------------------------
echo.
call start-all.bat

REM Uncomment the next line to restart the Cloudflare tunnel after services are up:
REM if "!CF_WAS_RUNNING!"=="1" net start "Cloudflare Tunnel Agent" >nul 2>&1

endlocal
