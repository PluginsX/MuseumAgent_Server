@echo off
chcp 65001 >nul
echo ========================================
echo Unity WebGL 核心文件提取脚本
echo ========================================
echo.

set SOURCE_DIR=E:\Project\Python\MuseumAgent_Server\client\web\Unity\build
set TARGET_DIR=E:\Project\Python\MuseumAgent_Server\client\web\MuseumAgent_Client\unity

echo [1/3] 检查源目录...
if not exist "%SOURCE_DIR%" (
    echo [错误] 源目录不存在: %SOURCE_DIR%
    pause
    exit /b 1
)

echo [2/3] 创建目标目录...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
if not exist "%TARGET_DIR%\Build" mkdir "%TARGET_DIR%\Build"
if not exist "%TARGET_DIR%\StreamingAssets" mkdir "%TARGET_DIR%\StreamingAssets"
if not exist "%TARGET_DIR%\ServerData" mkdir "%TARGET_DIR%\ServerData"

echo [3/3] 复制核心文件...
echo   - Build/ 目录（游戏代码和资源，包含加载器）
if exist "%SOURCE_DIR%\Build" (
    xcopy "%SOURCE_DIR%\Build" "%TARGET_DIR%\Build\" /E /I /Y /Q
) else (
    echo   [警告] Build 目录不存在
)

echo   - StreamingAssets/ 目录（流媒体资源）
if exist "%SOURCE_DIR%\StreamingAssets" (
    xcopy "%SOURCE_DIR%\StreamingAssets" "%TARGET_DIR%\StreamingAssets\" /E /I /Y /Q
) else (
    echo   [警告] StreamingAssets 目录不存在
)

echo   - ServerData/ 目录（服务器数据）
if exist "%SOURCE_DIR%\ServerData" (
    xcopy "%SOURCE_DIR%\ServerData" "%TARGET_DIR%\ServerData\" /E /I /Y /Q
) else (
    echo   [警告] ServerData 目录不存在
)

echo.
echo ========================================
echo 提取完成！
echo 目标目录: %TARGET_DIR%
echo 已提取核心文件（使用Unity自带minimal模板）
echo ========================================
