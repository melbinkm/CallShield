@echo off
REM CallShield — Setup script for Windows
REM Usage: scripts\setup.bat

setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0.."

echo [INFO] Checking dependencies...

REM ── Python check ────────────────────────────────────────────────────────────

where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python not found. Install Python 3.11+ from https://python.org
        exit /b 1
    )
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

%PYTHON% --version 2>&1
echo [INFO] Python found.

REM ── Node check ──────────────────────────────────────────────────────────────

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node 18+ from https://nodejs.org
    exit /b 1
)

node --version
echo [INFO] Node.js found.

REM ── Backend setup ───────────────────────────────────────────────────────────

echo [INFO] Setting up backend...

cd /d "%ROOT_DIR%\backend"

if not exist "venv" (
    echo [INFO] Creating virtual environment...
    %PYTHON% -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q

if not exist ".env" (
    copy .env.example .env
    echo [WARN] .env created — please edit backend\.env and add your MISTRAL_API_KEY
)

REM ── Frontend setup ──────────────────────────────────────────────────────────

echo [INFO] Setting up frontend...

cd /d "%ROOT_DIR%\frontend"
call npm install --silent

if not exist ".env" (
    copy .env.example .env
    echo [INFO] .env created for frontend
)

REM ── Start services ──────────────────────────────────────────────────────────

echo [INFO] Starting backend...
cd /d "%ROOT_DIR%\backend"
call venv\Scripts\activate.bat
start "CallShield Backend" cmd /c "uvicorn main:app --reload --port 8000"

echo [INFO] Starting frontend...
cd /d "%ROOT_DIR%\frontend"
start "CallShield Frontend" cmd /c "npm run dev"

echo.
echo =========================================
echo   CallShield is running!
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API docs: http://localhost:8000/docs
echo =========================================
echo   Close the terminal windows to stop.
echo.

pause
