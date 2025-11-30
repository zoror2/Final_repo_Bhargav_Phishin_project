@echo off
REM Run extraction overnight with auto-restart if needed
REM This script will keep restarting the extraction until you stop it manually

echo ====================================================================
echo   OVERNIGHT EXTRACTION - AUTO-RESTART MODE
echo   This will run continuously and restart automatically if needed
echo ====================================================================
echo.
echo Press Ctrl+C to stop completely
echo.
timeout /t 3

:LOOP
echo.
echo ====================================================================
echo   Starting/Resuming Extraction...
echo   Time: %date% %time%
echo ====================================================================
echo.

REM Run the extraction
python majestic_million_extractor.py

REM Check if it exited normally or with error
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================================================
    echo   Extraction completed successfully!
    echo ====================================================================
    goto END
) else (
    echo.
    echo ====================================================================
    echo   Extraction stopped - Restarting in 30 seconds...
    echo   Time: %date% %time%
    echo ====================================================================
    timeout /t 30
    goto LOOP
)

:END
echo.
echo All done! Check final_million_dataset.csv
pause
