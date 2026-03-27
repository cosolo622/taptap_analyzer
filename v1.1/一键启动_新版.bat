@echo off

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"

set "PY_CMD=py -3"
where py >nul 2>nul
if errorlevel 1 (
  set "PY_CMD=python"
)

echo ============================================
echo TapTap Analyzer v1.1 - One Click Start
echo ============================================
echo.
echo [1/3] Starting backend on :8000 ...
start "TapTap-Backend-8000" cmd /k "cd /d ""%BACKEND_DIR%"" && %PY_CMD% -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 2 >nul

echo [2/3] Starting frontend on :46635 ...
start "TapTap-Frontend-46635" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev -- --host 127.0.0.1 --port 46635"
timeout /t 2 >nul

echo [3/3] Starting scheduler ...
start "TapTap-Scheduler" cmd /k "cd /d ""%BACKEND_DIR%"" && %PY_CMD% scheduler.py"

echo.
echo Done. Open: http://127.0.0.1:46635
echo.
exit /b 0
