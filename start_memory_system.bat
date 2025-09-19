@echo off
REM MCP 记忆系统快速启动脚本
REM Windows 批处理版本

echo ========================================
echo     MCP 记忆系统启动器
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

REM 检查配置文件
if not exist "configs\mcp_config.json" (
    echo ❌ 错误: 配置文件 configs\mcp_config.json 不存在
    pause
    exit /b 1
)

echo 🚀 启动 MCP 记忆系统...
echo.

REM 选择配置模式
set /p mode="选择模式 [1] 生产环境 [2] 开发环境 (默认: 1): "
if "%mode%"=="" set mode=1
if "%mode%"=="2" (
    set config_flag=--dev
    echo 📝 使用开发配置
) else (
    set config_flag=
    echo 🏭 使用生产配置
)

echo.
echo 正在启动服务...
echo 按 Ctrl+C 停止所有服务
echo.

REM 启动部署管理器
python deploy_memory_system.py deploy %config_flag%

echo.
echo 服务已停止
pause
