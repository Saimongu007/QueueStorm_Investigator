@echo off
REM QueueStorm Investigator - Development Startup Script (Windows)
REM This script starts both backend and frontend in development mode

echo ========================================
echo    QueueStorm Investigator Full Stack
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found, copying from .env.example
    copy .env.example .env
    echo [WARNING] Please edit .env file and add your GROQ_API_KEY
)

REM Install backend dependencies
echo [INFO] Installing backend dependencies...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)
echo [OK] Backend dependencies installed

REM Install frontend dependencies
echo [INFO] Installing frontend dependencies...
cd frontend
call npm install >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies
    cd ..
    pause
    exit /b 1
)
cd ..
echo [OK] Frontend dependencies installed

REM Create logs directory
if not exist logs mkdir logs

echo.
echo [INFO] Starting services...
echo.

REM Start backend in new window
echo [INFO] Starting backend on http://localhost:8000
start "QueueStorm Backend" /MIN cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs\backend.log 2>&1"

REM Wait for backend to be ready
echo [INFO] Waiting for backend to be ready...
timeout /t 5 /nobreak >nul

:CHECK_BACKEND
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto CHECK_BACKEND
)
echo [OK] Backend is ready!

REM Start frontend in new window
echo [INFO] Starting frontend on http://localhost:3000
start "QueueStorm Frontend" /MIN cmd /c "cd frontend && npm run dev > ..\logs\frontend.log 2>&1"

echo.
echo ========================================
echo    Services Started Successfully!
echo ========================================
echo.
echo Frontend:  http://localhost:3000
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Check logs\ directory for service logs
echo.
echo Press any key to stop all services...
pause >nul

REM Stop services
echo.
echo [INFO] Stopping services...
taskkill /F /FI "WINDOWTITLE eq QueueStorm Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq QueueStorm Frontend*" >nul 2>&1
echo [OK] Services stopped
echo.
echo Goodbye!
pause
