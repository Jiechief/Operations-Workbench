@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 检查 8000 端口是否已被占用（说明服务器已在运行）
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo 检测到本地服务器已在运行，直接打开页面...
  start "" "http://localhost:8000/运营工作台.html"
  timeout /t 1 >nul
  exit /b 0
)

echo 正在启动本地服务器...
echo   1. 保持此窗口开着（不要关闭），工作台需要它
echo   2. 浏览器会自动打开工作台页面
echo   3. 用完后关闭此窗口即可停止服务器
echo.

start "" "http://localhost:8000/运营工作台.html"
py server.py 8000
if errorlevel 1 python server.py 8000
pause
