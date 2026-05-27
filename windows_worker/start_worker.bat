@echo off
title Windows Agent Worker
cd /d "%~dp0\.."
echo Checking configuration...

if not exist "windows_worker\.env.windows" (
    echo .env.windows not found, copying from .env.windows.example...
    copy "windows_worker\.env.windows.example" "windows_worker\.env.windows"
)

REM Read host and port from config if possible
set HOST=127.0.0.1
set PORT=9100

for /f "tokens=1,2 delims==" %%i in (windows_worker\.env.windows) do (
    if "%%i"=="WINDOWS_WORKER_HOST" set HOST=%%j
    if "%%i"=="WINDOWS_WORKER_PORT" set PORT=%%j
)

echo Starting Windows Agent Worker on http://%HOST%:%PORT%...
python -m uvicorn windows_worker.worker:app --host %HOST% --port %PORT% --reload
pause
