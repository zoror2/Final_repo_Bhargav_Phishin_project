@echo off
echo ============================================================
echo STOPPING CURRENT EXTRACTION
echo ============================================================

:: Kill any running Python extraction processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *majestic*" 2>nul
timeout /t 3 >nul

:: Stop Docker containers
echo Stopping Docker containers...
docker stop $(docker ps -q) 2>nul
timeout /t 5 >nul

echo.
echo ============================================================
echo STARTING AUTO-RECOVERING EXTRACTOR
echo ============================================================
echo This will run until all 1 million URLs are extracted
echo Safe to leave running overnight
echo Press Ctrl+C to stop (it will handle gracefully)
echo ============================================================
echo.

:: Start the auto-recovering extractor
python auto_majestic_extractor.py

pause
