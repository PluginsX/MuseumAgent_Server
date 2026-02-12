@echo off
REM MuseumAgent Server Startup Script

echo Starting MuseumAgent Server...
echo Using virtual environment: %~dp0venv
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Expected location: %~dp0venv\Scripts\python.exe
    pause
    exit /b 1
)

REM Start server using fixed server script with proper configuration loading
"%~dp0venv\Scripts\python.exe" "%~dp0fixed_server.py"

REM Keep window open after server stops
echo.
echo Server stopped
pause
