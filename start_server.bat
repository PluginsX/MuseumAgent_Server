@echo off
chcp 65001 > nul
echo.
echo ================================
echo 博物馆智能体服务器 - 启动脚本
echo ================================
echo.

REM 设置Python虚拟环境路径
set VENV_PATH=E:\Project\Python\MuseumAgent_Server\venv\Scripts\python.exe

REM 检查虚拟环境是否存在
if not exist "%VENV_PATH%" (
    echo 错误: 未找到虚拟环境，请确认路径是否正确
    echo 路径: %VENV_PATH%
    pause
    exit /b 1
)

echo 使用虚拟环境: %VENV_PATH%
echo.

REM 启动服务器
echo 启动博物馆智能体服务器...
"%VENV_PATH%" main.py

pause