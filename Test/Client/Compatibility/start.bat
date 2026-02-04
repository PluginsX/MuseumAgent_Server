@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo 博物馆智能体测试客户端 - 高级启动脚本
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境
    echo 请确保Python已正确安装并添加到PATH环境变量中
    goto error_exit
)

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "PORT=10086"

echo 当前工作目录: %SCRIPT_DIR%
echo.

REM 检查必要文件
if not exist "%SCRIPT_DIR%index.html" (
    echo 错误: 未找到index.html文件
    goto error_exit
)

if not exist "%SCRIPT_DIR%assets\js\main.js" (
    echo 警告: 未找到main.js文件
)

if not exist "%SCRIPT_DIR%assets\css\style.css" (
    echo 警告: 未找到style.css文件
)

echo.
echo 选择启动选项:
echo 1. 启动Web服务器 (本地访问 - localhost)
echo 2. 启动Web服务器 (局域网访问 - 0.0.0.0)
echo 3. 退出
echo.

choice /c 123 /m "请选择选项"
if %errorlevel% equ 1 goto start_localhost
if %errorlevel% equ 2 goto start_lan
if %errorlevel% equ 3 goto exit_script

:start_localhost
echo.
echo 正在启动Web服务器 (本地访问)...
echo 访问地址: http://localhost:%PORT%
echo 按 Ctrl+C 停止服务器
echo.
cd /d "%SCRIPT_DIR%"
python -m http.server %PORT%
goto end

:start_lan
echo.
echo 正在启动Web服务器 (局域网访问)...
echo 本机访问地址: http://localhost:%PORT%
echo 局域网访问地址: http://[本机IP地址]:%PORT%
echo 按 Ctrl+C 停止服务器
echo.
cd /d "%SCRIPT_DIR%"
python -m http.server %PORT% --bind 0.0.0.0
goto end

:error_exit
echo.
echo 按任意键退出...
pause >nul
exit /b 1

:exit_script
echo 再见!
exit /b 0

:end
echo.
echo 脚本执行完毕
pause