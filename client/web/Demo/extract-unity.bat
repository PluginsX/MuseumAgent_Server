@echo off
chcp 65001 >nul
echo ========================================
echo Unity WebGL 文件提取脚本
echo ========================================
echo.

set SOURCE_DIR=E:\Project\Python\MuseumAgent_Server\client\web\Unity\build
set TARGET_DIR=E:\Project\Python\MuseumAgent_Server\client\web\Demo\unity

echo [1/4] 检查源目录...
if not exist "%SOURCE_DIR%" (
    echo [错误] 源目录不存在: %SOURCE_DIR%
    pause
    exit /b 1
)

echo [2/4] 创建目标目录...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [3/4] 复制文件...
echo   - Build/
xcopy "%SOURCE_DIR%\Build" "%TARGET_DIR%\Build\" /E /I /Y /Q
echo   - StreamingAssets/
xcopy "%SOURCE_DIR%\StreamingAssets" "%TARGET_DIR%\StreamingAssets\" /E /I /Y /Q
echo   - TemplateData/
xcopy "%SOURCE_DIR%\TemplateData" "%TARGET_DIR%\TemplateData\" /E /I /Y /Q
echo   - main.js
copy "%SOURCE_DIR%\main.js" "%TARGET_DIR%\main.js" /Y >nul
echo   - ServiceWorker.js
copy "%SOURCE_DIR%\ServiceWorker.js" "%TARGET_DIR%\ServiceWorker.js" /Y >nul
echo   - manifest.webmanifest
copy "%SOURCE_DIR%\manifest.webmanifest" "%TARGET_DIR%\manifest.webmanifest" /Y >nul

echo [4/4] 验证文件...
set ERROR=0
if not exist "%TARGET_DIR%\Build\build.loader.js" (
    echo [错误] build.loader.js 未找到
    set ERROR=1
)
if not exist "%TARGET_DIR%\main.js" (
    echo [错误] main.js 未找到
    set ERROR=1
)

if %ERROR%==0 (
    echo.
    echo ========================================
    echo 提取完成！
    echo 目标目录: %TARGET_DIR%
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 提取失败，请检查错误信息
    echo ========================================
)

pause

