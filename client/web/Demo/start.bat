@echo off
chcp 65001 >nul
echo ========================================
echo   MuseumAgent Web Demo
echo ========================================
echo.
echo Starting HTTP server...
echo Server address: http://localhost:12302

cd /d "%~dp0"

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using Python server...
    start http://localhost:12302/index.html
    python -m http.server 12302 --bind 0.0.0.0
) else (
    REM Check if Node.js is installed
    where node >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo Using Node.js server...
        start http://localhost:12302/index.html
        npx http-server -p 12302 -a 0.0.0.0
    ) else (
        echo Error: Python or Node.js not found
        echo Please install Python 3 or Node.js and try again
        pause
    )
)