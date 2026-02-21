@echo off
chcp 65001 >nul
echo ========================================
echo MuseumAgent SDK - 更新到 Demo
echo ========================================
echo.

echo [1/3] 正在构建 SDK...
call npm run build
if %errorlevel% neq 0 (
    echo 构建失败！
    pause
    exit /b 1
)
echo ✓ 构建成功
echo.

echo [2/3] 正在复制到 Demo...
copy /Y dist\museum-agent-sdk.min.js ..\web\Demo\lib\museum-agent-sdk.min.js >nul
copy /Y dist\museum-agent-sdk.min.js.map ..\web\Demo\lib\museum-agent-sdk.min.js.map >nul
echo ✓ 复制成功
echo.

echo [3/3] 检查文件...
if exist ..\web\Demo\lib\museum-agent-sdk.min.js (
    echo ✓ SDK 已成功更新到 Demo！
    echo.
    echo 文件位置：
    echo   - ..\web\Demo\lib\museum-agent-sdk.min.js
    echo   - ..\web\Demo\lib\museum-agent-sdk.min.js.map
) else (
    echo ✗ 更新失败！
)

echo.
echo ========================================
pause

