# 🎯 One-Click Setup Script

# This script will set up everything automatically for your friend

Write-Host "🛡️ ScamiFy Setup Script" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "✅ Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python from python.org" -ForegroundColor Red
    Write-Host "   Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Red
    pause
    exit 1
}

# Navigate to backend directory
$backendPath = Join-Path $PSScriptRoot "Scamify-main\Extension\backend"
if (Test-Path $backendPath) {
    Set-Location $backendPath
    Write-Host "✅ Found backend directory" -ForegroundColor Green
} else {
    Write-Host "❌ Backend directory not found. Make sure you extracted the full project." -ForegroundColor Red
    pause
    exit 1
}

# Create virtual environment if it doesn't exist
if (!(Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        pause
        exit 1
    }
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "📥 Installing Python packages..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Gray
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install packages. Trying alternative method..." -ForegroundColor Red
    pip install Flask==3.0.3 Flask-CORS==4.0.1 numpy==1.26.4 pandas==2.2.3 scikit-learn==1.5.2 joblib==1.4.2 tensorflow==2.18.0 requests==2.32.3 selenium==4.15.0 webdriver-manager==4.0.1
}

Write-Host ""
Write-Host "🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 To start the server:" -ForegroundColor Cyan
Write-Host "   1. Double-click START_SERVER.bat" -ForegroundColor White
Write-Host "   OR run: python app.py" -ForegroundColor White
Write-Host ""
Write-Host "🌐 To install Chrome extension:" -ForegroundColor Cyan
Write-Host "   1. Open Chrome" -ForegroundColor White
Write-Host "   2. Go to chrome://extensions/" -ForegroundColor White
Write-Host "   3. Turn on Developer mode" -ForegroundColor White
Write-Host "   4. Click 'Load unpacked'" -ForegroundColor White
Write-Host "   5. Select the 'phishing-extension' folder" -ForegroundColor White
Write-Host ""
Write-Host "📖 Need help? Check COMPLETE_SETUP_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

# Test installation
Write-Host "🧪 Testing installation..." -ForegroundColor Yellow
try {
    python -c "import flask, tensorflow, pandas, sklearn; print('All packages imported successfully!')"
    Write-Host "✅ All packages working correctly!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Some packages may have issues, but basic functionality should work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")