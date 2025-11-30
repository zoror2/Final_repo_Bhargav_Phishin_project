# Stop Current Extraction and Start Auto-Recovery Mode

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "STOPPING CURRENT EXTRACTION" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

# Kill any running Python extraction
Write-Host "Stopping Python processes..." -ForegroundColor White
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*majestic*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# Stop Docker containers
Write-Host "Stopping Docker containers..." -ForegroundColor White
$containers = docker ps -q
if ($containers) {
    docker stop $containers 2>$null
}
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "STARTING AUTO-RECOVERING EXTRACTOR" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "This will run until all 1 million URLs are extracted" -ForegroundColor White
Write-Host "Safe to leave running overnight - auto-restarts on failures" -ForegroundColor White
Write-Host "Press Ctrl+C to stop (it will save progress gracefully)" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the auto-recovering extractor
python auto_majestic_extractor.py

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
