@echo off
chcp 65001 >nul
echo ============================================
echo    TapTap舆情监控 - 启动所有服务
echo ============================================
echo.

:: 启动后端
echo [1/3] 启动后端服务...
start "TapTap后端" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 >nul

:: 启动前端
echo [2/3] 启动前端服务...
start "TapTap前端" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 >nul

:: 启动定时调度
echo [3/3] 启动定时调度服务...
start "TapTap定时调度" cmd /k "cd /d %~dp0backend && python scheduler.py"

echo.
echo ============================================
echo    所有服务已启动！
echo ============================================
echo.
echo 访问地址: http://10.89.128.38:46635
echo.
echo 按任意键退出此窗口（服务会继续运行）
pause >nul
