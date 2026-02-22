@echo off
chcp 65001 >nul
echo ========================================
echo   MuseumAgent Web Demo
echo ========================================
echo.

cd /d "%~dp0"

REM Default settings
set SSL_ENABLED=true
set PORT=12302

REM Check for SSL argument
if "%1"=="--ssl" set SSL_ENABLED=true

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found
    echo Please install Python 3 and try again
    pause
    exit /b 1
)

if "%SSL_ENABLED%"=="true" (
    echo Starting HTTPS server...
    echo Server address: https://museum.soulflaw.com:%PORT%
    echo SSL enabled
    start https://museum.soulflaw.com:%PORT%/index.html
    python ssl_server.py --ssl --port %PORT%
) else (
    echo Starting HTTP server...
    echo Server address: http://museum.soulflaw.com:%PORT%
    start http://museum.soulflaw.com:%PORT%/index.html
    python -m http.server %PORT% --bind 0.0.0.0
)
