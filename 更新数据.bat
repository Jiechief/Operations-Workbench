@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM ===== 用后台导出的 Excel 重新生成内置数据 ops-data.js =====
REM 用法一：把导出的 xlsx 拖到这个 bat 上
REM 用法二：双击后按提示粘贴 xlsx 完整路径
REM 生成后再双击「更新到云端.bat」提交，历史数据就永久留在 git 里

if "%~1"=="" (
  set /p SRC=请粘贴后台导出的 xlsx 路径: 
) else (
  set "SRC=%~1"
)

if not defined SRC (
  echo [取消] 没有输入路径
  pause
  exit /b 1
)

echo 正在生成 ops-data.js ...
py "tools\导出工作台数据.py" "%SRC%"
if errorlevel 1 python "tools\导出工作台数据.py" "%SRC%"
if errorlevel 1 (
  echo.
  echo [错误] 生成失败。请确认路径正确、文件已关闭，且已安装 Python 与 openpyxl（pip install openpyxl）
  pause
  exit /b 1
)

echo.
echo [完成] ops-data.js 已更新。刷新工作台页面即可看到新数据。
echo        如需永久留档，再双击「更新到云端.bat」提交到 GitHub。
pause
