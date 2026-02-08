@echo off
chcp 65001 >nul

:: 文件夹复制脚本 - 基础覆盖版本
:: 设置源文件夹路径
set SOURCE_FOLDER=E:\Project\Python\MuseumAgent_Server\Test\Client\MuseumAgent_Client_Unity
:: 设置目标文件夹路径
set DEST_FOLDER=E:\Project\Unity\SpiritBeast\Assets\Script\Component\MuseumAgent_Client_Unity

echo 正在复制文件夹...
echo 源路径: %SOURCE_FOLDER%
echo 目标路径: %DEST_FOLDER%
echo.

:: 使用xcopy进行复制
xcopy "%SOURCE_FOLDER%" "%DEST_FOLDER%" /E /I /Y /H

if errorlevel 1 (
    echo 复制过程中出现错误！
    pause
    exit /b 1
) else (
    echo 文件夹复制完成！
    pause
)