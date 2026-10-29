# ODEYSSEY -- Run Automated Test Suite via PowerShell
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  ODEYSSEY -- Running Automated Test Suite" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$pytestExe = Join-Path $scriptDir ".venv\Scripts\pytest.exe"
if (Test-Path $pytestExe) {
    & $pytestExe -v
} else {
    pytest -v
}
