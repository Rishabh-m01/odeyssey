@echo off
echo ===================================================
echo   ODEYSSEY -- Running Automated Test Suite
echo ===================================================
echo.
cd /d "%~dp0"
if exist ".venv\Scripts\pytest.exe" (
    ".venv\Scripts\pytest.exe" -v
) else (
    pytest -v
)
pause
