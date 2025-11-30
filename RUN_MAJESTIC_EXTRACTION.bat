@echo off
REM Majestic Million Feature Extraction - Easy Launcher
REM This script starts the feature extraction process

echo ====================================================================
echo   MAJESTIC MILLION FEATURE EXTRACTION
echo   Crash-Resistant with Auto-Save Progress
echo ====================================================================
echo.

REM Check if Docker Selenium is running
echo Checking Docker Selenium status...
curl -s http://localhost:4444/status > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Docker Selenium is not running!
    echo.
    echo Please start Docker Selenium first:
    echo   docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest
    echo.
    pause
    exit /b 1
)

echo [OK] Docker Selenium is running
echo.

REM Check if input file exists
if not exist "majestic_million.csv" (
    echo [ERROR] Input file not found: majestic_million.csv
    echo.
    echo Please ensure majestic_million.csv is in the current directory.
    echo.
    pause
    exit /b 1
)

echo [OK] Input file found: majestic_million.csv
echo.

REM Check if resuming from previous run
if exist "extraction_progress_million.json" (
    echo [INFO] Previous progress detected - will resume extraction
    echo.
) else (
    echo [INFO] Starting fresh extraction
    echo.
)

echo ====================================================================
echo   Starting Feature Extraction
echo ====================================================================
echo.
echo TIP: Press Ctrl+C to stop safely (progress will be saved)
echo TIP: Run check_million_progress.py in another window to monitor
echo TIP: Watch browser: http://localhost:7900 (password: secret)
echo.
echo ====================================================================
echo.

REM Run the extraction
python majestic_million_extractor.py

echo.
echo ====================================================================
echo   Extraction Process Ended
echo ====================================================================
echo.

if exist "final_million_dataset.csv" (
    echo [SUCCESS] Output file created: final_million_dataset.csv
    echo.
    
    REM Show file size
    for %%A in (final_million_dataset.csv) do (
        set size=%%~zA
        set /a sizeMB=!size! / 1048576
        echo File size: !sizeMB! MB
    )
    echo.
)

if exist "extraction_progress_million.json" (
    echo [INFO] Progress file exists - you can resume if needed
    echo       Run this script again to continue extraction
    echo.
)

echo To check progress: python check_million_progress.py
echo.
pause
