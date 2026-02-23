@echo off
chcp 65001 >nul
rem 源目录
set "SOURCE_DIR=E:\Project\Python\MuseumAgent_Server\client\web\AgentClient_Unity"

rem 目标目录
set "DEST_DIR=E:\Project\Unity\Museum\Assets\Script\Component\AgentClient_Unity"

rem 创建目标目录（如果不存在）
mkdir "%DEST_DIR%" 2>nul

rem 复制所有文件和子目录
xcopy "%SOURCE_DIR%" "%DEST_DIR%" /E /I /Y

rem 显示完成信息
echo 复制完成！
echo 源目录: %SOURCE_DIR%
echo 目标目录: %DEST_DIR%

pause