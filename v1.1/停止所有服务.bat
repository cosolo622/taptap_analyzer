@echo off
chcp 65001 >nul
echo ============================================
echo    TapTap舆情监控 - 停止所有服务
echo ============================================
echo.

echo 正在停止所有服务...

:: 停止Python进程（后端和调度器）
taskkill /F /IM python.exe /FI "WINDOWTITLE eq TapTap*" 2>nul
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq TapTap*" 2>nul

:: 停止Node进程（前端）
taskkill /F /IM node.exe /FI "WINDOWTITLE eq TapTap*" 2>nul

:: 按端口停止（备用方式）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :46635 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul

echo.
echo ============================================
echo    所有服务已停止！
echo ============================================
echo.
pause
