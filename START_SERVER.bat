@echo off
title ScamiFy Backend Server
echo.
echo =================================
echo    ScamiFy Backend Server
echo =================================
echo.
echo Starting the AI phishing detection backend...
echo Keep this window open while using the Chrome extension!
echo.

cd /d "%~dp0Scamify-main\Extension\backend"

REM Check if virtual environment exists
if exist venv (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting server on http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.

python app.py

echo.
echo Server stopped. Press any key to exit...
pause >nul