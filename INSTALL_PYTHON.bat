@echo off
title Install Python for ScamiFy
echo.
echo ===============================================
echo           Python Installation Helper
echo ===============================================
echo.
echo This script will help you install Python if needed.
echo.

REM Check if Python is already installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python is already installed!
    python --version
    echo.
    echo You can now run SETUP.ps1 or START_SERVER.bat
    goto :end
)

echo ❌ Python is not installed or not in PATH
echo.
echo To install Python:
echo 1. Go to: https://python.org/downloads/
echo 2. Click "Download Python" (yellow button)
echo 3. Run the installer
echo 4. ⚠️  IMPORTANT: Check "Add Python to PATH" 
echo 5. Click "Install Now"
echo 6. Restart this script after installation
echo.
echo Opening Python download page in your browser...

REM Try to open the Python downloads page
start https://python.org/downloads/

:end
echo.
echo Press any key to exit...
pause >nul