# ODEYSSEY -- Minimalist Smart Trip Planner
# Run script for PowerShell
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  ODEYSSEY -- Minimalist Smart Trip Planner" -ForegroundColor Green
Write-Host "  Starting local development server on http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
if (Test-Path $pythonExe) {
    & $pythonExe "app.py"
} else {
    python "app.py"
}
