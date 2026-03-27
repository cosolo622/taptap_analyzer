@echo off
set "TITLE1=TapTap-Backend-8000"
set "TITLE2=TapTap-Frontend-46635"
set "TITLE3=TapTap-Scheduler"

echo ============================================
echo TapTap Analyzer v1.1 - One Click Stop
echo ============================================
echo.

taskkill /F /FI "WINDOWTITLE eq %TITLE1%" /T >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq %TITLE2%" /T >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq %TITLE3%" /T >nul 2>nul

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :46635 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>nul

echo Done.
echo.
exit /b 0
