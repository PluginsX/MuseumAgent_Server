@echo off
chcp 65001 >nul
echo ========================================
echo   MuseumAgent Web Demo - V2.0
echo ========================================
echo.
echo 【重要提示】
echo 如果看不到新功能，请在浏览器中：
echo   1. 按 Ctrl + Shift + R 强制刷新
echo   2. 或按 F12 打开开发者工具
echo   3. 右键点击刷新按钮
echo   4. 选择"清空缓存并硬性重新加载"
echo.
echo ========================================
echo.
echo 正在启动 HTTP 服务器...
echo 服务器地址: http://localhost:18000
echo.

cd /d "%~dp0"

REM 检查 Python 是否安装
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo 使用 Python 启动服务器...
    start http://localhost:18000/index.html
    python -m http.server 18000
) else (
    REM 检查 Node.js 是否安装
    where node >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo 使用 Node.js 启动服务器...
        start http://localhost:18000/index.html
        npx http-server -p 18000
    ) else (
        echo 错误: 未找到 Python 或 Node.js
        echo 请安装 Python 3 或 Node.js 后重试
        pause
    )
)
