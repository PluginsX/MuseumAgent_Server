@echo off
chcp 65001 >nul
echo ========================================
echo MuseumAgent SDK - 更新到 MuseumAgent_Client
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

echo [2/3] 正在复制到 MuseumAgent_Client...
copy /Y dist\museum-agent-sdk.min.js ..\web\MuseumAgent_Client\lib\museum-agent-sdk.min.js >nul
copy /Y dist\museum-agent-sdk.min.js.map ..\web\MuseumAgent_Client\lib\museum-agent-sdk.min.js.map >nul
copy /Y src\managers\vad-processor.js ..\web\MuseumAgent_Client\lib\vad-processor.js >nul
echo ✓ 复制成功
echo.

echo [3/3] 检查文件...
if exist ..\web\MuseumAgent_Client\lib\museum-agent-sdk.min.js (
    if exist ..\web\MuseumAgent_Client\lib\vad-processor.js (
        echo ✓ SDK 已成功更新到 MuseumAgent_Client ！
        echo.
        echo 文件位置：
        echo   - ..\web\MuseumAgent_Client\lib\museum-agent-sdk.min.js
        echo   - ..\web\MuseumAgent_Client\lib\museum-agent-sdk.min.js.map
        echo   - ..\web\MuseumAgent_Client\lib\vad-processor.js
    ) else (
        echo ✗ AudioWorklet 处理器文件复制失败！
    )
) else (
    echo ✗ 更新失败！
)

echo.
echo ========================================

