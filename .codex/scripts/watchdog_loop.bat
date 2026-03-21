@echo off
setlocal enabledelayedexpansion

if "%INTERVAL_SECONDS%"=="" (
    set INTERVAL_SECONDS=300
)

:loop
codex continue
timeout /t %INTERVAL_SECONDS% /nobreak >nul
goto loop
