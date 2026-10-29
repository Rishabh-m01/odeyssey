@echo off
echo ===================================================
echo   ODEYSSEY -- Minimalist Smart Trip Planner
echo   Starting local development server...
echo ===================================================
echo.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)
pause
