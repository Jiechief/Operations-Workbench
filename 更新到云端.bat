@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === 更新运营工作台到 GitHub ===
echo.

git add -A
if errorlevel 1 (
  echo [错误] git add 失败
  pause
  exit /b 1
)

set /p MSG=请输入本次提交说明（直接回车用默认）: 
if "%MSG%"=="" set MSG=update %date% %time%
git commit -m "%MSG%"
if errorlevel 1 (
  echo [提示] 没有新修改，无需更新
  pause
  exit /b 0
)

echo 正在推送到 GitHub...
git push origin main
if errorlevel 1 (
  echo.
  echo [错误] push 失败，请检查网络后重试
  pause
  exit /b 1
)

echo [完成] 已推送到 https://github.com/Jiechief/Operations-Workbench
echo 若已开启 Pages：https://jiechief.github.io/Operations-Workbench/
pause
