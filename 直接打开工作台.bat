@echo off
chcp 65001 >nul

REM ===== 直接打开运营工作台（无需本地服务器）=====
REM 原理：用 --disable-web-security 启动独立浏览器实例，临时关闭 CORS 限制，
REM       这样 file:// 协议下也能直接调用大模型接口。
REM 注意：该实例仅供工作台使用，不要用来浏览其他网站。

set "HTML_FILE=%~dp0运营工作台.html"
set "DEV_PROFILE=%TEMP%\ops_workbench_browser_profile"

echo 正在打开运营工作台...
echo.

set "EDGE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
set "CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe"

if exist "%EDGE%" (
  start "" "%EDGE%" --disable-web-security --disable-features=IsolateOrigins --user-data-dir="%DEV_PROFILE%" "file:///%HTML_FILE%"
  echo 已用 Edge 打开工作台，此窗口可关闭。
) else if exist "%CHROME%" (
  start "" "%CHROME%" --disable-web-security --disable-features=IsolateOrigins --user-data-dir="%DEV_PROFILE%" "file:///%HTML_FILE%"
  echo 已用 Chrome 打开工作台，此窗口可关闭。
) else (
  echo 未找到 Edge 或 Chrome 浏览器，请先安装。
  pause
)

timeout /t 2 >nul
