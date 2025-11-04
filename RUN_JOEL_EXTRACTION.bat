@echo off
title Joel Dataset - Docker Selenium Feature Extraction
echo.
echo =====================================================
echo    Joel Dataset Feature Extraction Setup
echo =====================================================
echo.
echo This will set up Docker Selenium and extract features from 5k URLs
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed or not running
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Docker is available
echo.

REM Setup Docker Selenium
echo 🐳 Setting up Docker Selenium...
python setup_docker_selenium.py

if %errorlevel% neq 0 (
    echo ❌ Docker Selenium setup failed
    pause
    exit /b 1
)

echo.
echo 🎯 Ready to extract features!
echo.
echo Choose an option:
echo 1. Extract features from all 5k URLs (recommended)
echo 2. Test with 10 URLs first
echo 3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Starting feature extraction for 5k URLs...
    echo 📺 You can monitor progress at: http://localhost:7900 (password: secret)
    echo.
    python joel_docker_selenium_extractor.py
) else if "%choice%"=="2" (
    echo.
    echo 🧪 Running test extraction on 10 URLs...
    python test_joel_docker_extractor.py
) else (
    echo.
    echo 👋 Goodbye!
    goto end
)

echo.
echo 🎉 Feature extraction complete!
echo 📁 Check Joel_dataset_features.csv for results
echo.

:end
pause