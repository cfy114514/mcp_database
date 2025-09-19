@echo off
REM MCP 三工具统一启动脚本 - Windows版本
REM 包含记忆库工具、向量数据库工具、角色人设服务

title MCP 三工具统一启动器

echo ========================================
echo     MCP 三工具统一启动器
echo ========================================
echo.
echo 🧠 记忆库工具 (端口 8001)
echo 📚 向量数据库工具 (端口 8000)  
echo 👤 角色人设服务 (Node.js MCP)
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Python 未安装或不在 PATH 中
    echo 请安装 Python 3.7+ 并确保添加到 PATH
    pause
    exit /b 1
)

REM 检查主要文件
if not exist "deploy_all_tools.py" (
    echo ❌ 错误: deploy_all_tools.py 不存在
    echo 请确保在正确的项目目录中运行此脚本
    pause
    exit /b 1
)

echo 🚀 启动 MCP 三工具统一部署系统...
echo.

REM 询问运行模式
set /p mode="选择模式 [1] 一键部署 [2] 仅启动服务 [3] 检查环境 (默认: 1): "
if "%mode%"=="" set mode=1

if "%mode%"=="1" (
    echo 📦 执行一键部署（包含环境检查、依赖安装、配置、启动、测试）
    python deploy_all_tools.py deploy
) else if "%mode%"=="2" (
    echo 🚀 仅启动所有服务
    python deploy_all_tools.py start
) else if "%mode%"=="3" (
    echo 🔍 执行环境检查
    python deploy_all_tools.py check
) else (
    echo ❌ 无效选择，使用默认一键部署模式
    python deploy_all_tools.py deploy
)

echo.
echo ========================================
echo 部署完成，按任意键查看服务状态...
pause >nul

echo.
echo 📊 服务状态:
python deploy_all_tools.py status

echo.
echo ========================================
echo 🎯 快速操作命令:
echo   python deploy_all_tools.py status  - 查看服务状态
echo   python deploy_all_tools.py test    - 运行测试
echo   python deploy_all_tools.py stop    - 停止所有服务
echo.
echo 📋 服务访问地址:
echo   http://localhost:8001/docs  - 记忆库工具API
echo   http://localhost:8000/docs  - 向量数据库工具API
echo.
echo 按任意键退出...
pause >nul
