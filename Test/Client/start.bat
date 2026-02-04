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
set "PORT=8000"

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
echo 1. 启动Web服务器 (端口 8000)
echo 2. 启动Web服务器 (自定义端口)
echo 3. 仅打开浏览器 (假设服务器已在运行)
echo 4. 启动服务器并自动打开浏览器
echo 5. 退出
echo.

choice /c 12345 /m "请选择选项"
if %errorlevel% equ 1 goto start_server_default
if %errorlevel% equ 2 goto start_server_custom
if %errorlevel% equ 3 goto open_browser_only
if %errorlevel% equ 4 goto start_and_open
if %errorlevel% equ 5 goto exit_script

:start_server_default
echo.
echo 正在启动Web服务器 (端口 %PORT%)...
echo 访问地址: http://localhost:%PORT%
echo 按 Ctrl+C 停止服务器
echo.
cd /d "%SCRIPT_DIR%"
python -m http.server %PORT%
goto end

:start_server_custom
echo.
set /p CUSTOM_PORT=请输入端口号 (默认8000): 
if "%CUSTOM_PORT%"=="" set CUSTOM_PORT=8000
echo.
echo 正在启动Web服务器 (端口 %CUSTOM_PORT%)...
echo 访问地址: http://localhost:%CUSTOM_PORT%
echo 按 Ctrl+C 停止服务器
echo.
cd /d "%SCRIPT_DIR%"
python -m http.server %CUSTOM_PORT%
goto end

:open_browser_only
echo.
echo 正在打开浏览器...
start http://localhost:8000
echo 浏览器已打开，请确保Web服务器正在运行
goto end

:start_and_open
echo.
echo 正在启动Web服务器并打开浏览器...
echo 访问地址: http://localhost:%PORT%
echo 按 Ctrl+C 停止服务器
echo.

REM 启动服务器并在新窗口中打开浏览器
cd /d "%SCRIPT_DIR%"
start "" cmd /c "python -m http.server %PORT% & pause"
timeout /t 2 /nobreak >nul
start http://localhost:%PORT%
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