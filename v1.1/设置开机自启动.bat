@echo off
chcp 65001 >nul
echo ============================================
echo    设置开机自启动
echo ============================================
echo.

:: 创建启动脚本
set SCRIPT_PATH=%~dp0启动所有服务.bat
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

:: 创建快捷方式
echo 正在创建开机自启动任务...
schtasks /create /tn "TapTap舆情监控" /tr "\"%SCRIPT_PATH%\"" /sc onstart /rl highest /f

echo.
echo ============================================
echo    设置完成！
echo ============================================
echo.
echo 电脑开机后会自动启动所有服务
echo.
echo 如需取消自启动，请运行：
echo schtasks /delete /tn "TapTap舆情监控" /f
echo.
pause
