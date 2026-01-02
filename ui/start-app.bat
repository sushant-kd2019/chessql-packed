@echo off
REM ChessQL Desktop App Startup Script for Windows

echo Starting ChessQL Desktop Application...

REM Check if we're in the right directory
if not exist "package.json" (
    echo Error: Please run this script from the chessql-ui directory
    pause
    exit /b 1
)

REM Check if ChessQL backend exists
if not exist "..\chessql" (
    echo Error: ChessQL backend not found. Please ensure it's in the parent directory.
    pause
    exit /b 1
)

REM Start ChessQL backend in background
echo Starting ChessQL backend...
cd ..\chessql
start /b python3 server.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start Electron app
echo Starting Electron application...
cd ..\chessql-ui
npm start

pause
