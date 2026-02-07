@echo off
REM Simple startup script for MuseumAgent Server

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please check if env directory exists
    pause
    exit /b 1
)

REM Start server using virtual environment Python
echo Starting MuseumAgent Server...
echo Using virtual environment: %~dp0env
echo.

"%~dp0venv\Scripts\python.exe" "%~dp0main.py"

REM Keep window open after server stops
echo.
echo Server stopped
pause
