@echo off
REM MCP 三工具统一启动脚本 - Windows版本（更新端口与健康检查）
REM 包含记忆库工具、向量数据库工具、角色人设服务

setlocal enabledelayedexpansion

set KB_PORT=%KB_PORT%
if "%KB_PORT%"=="" set KB_PORT=8100

echo ========================================
echo     MCP 三工具统一启动器
echo ========================================
echo.
echo 🧠 记忆库工具 (端口 8001)
echo 📚 向量数据库工具 (端口 %KB_PORT%)  
echo 👤 角色人设服务 (Node.js MCP)
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

REM 检查主要文件
echo 检查关键文件...
if not exist "deploy_all_tools.py" (
    echo ❌ 错误: 缺少 deploy_all_tools.py
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

REM 健康检查（使用 curl 检查 8001 与 %KB_PORT%）
echo.
echo 健康检查 8001 与 %KB_PORT% 端口:

REM 8001 检查
set PORT_TO_CHECK=8001
echo [!PORT_TO_CHECK!] /docs:
curl -s -o NUL -w "HTTP %%{http_code}\n" http://127.0.0.1:!PORT_TO_CHECK!/docs

echo [!PORT_TO_CHECK!] /stats:
curl -s -o NUL -w "HTTP %%{http_code}\n" http://127.0.0.1:!PORT_TO_CHECK!/stats

echo [!PORT_TO_CHECK!] /rebuild_index (POST):
curl -s -X POST -H "Content-Type: application/json" -d "{}" -o NUL -w "HTTP %%{http_code}\n" http://127.0.0.1:!PORT_TO_CHECK!/rebuild_index

echo.
REM %KB_PORT% 检查
echo [%KB_PORT%] /docs:
curl -s -o NUL -w "HTTP %%{http_code}\n" http://127.0.0.1:%KB_PORT%/docs

echo [%KB_PORT%] /stats:
curl -s -o NUL -w "HTTP %%{http_code}\n" http://127.0.0.1:%KB_PORT%/stats

echo [%KB_PORT%] /rebuild_index (POST):
curl -s -X POST -H "Content-Type: application/json" -d "{}" -o NUL -w "HTTP %%{http_code}\n" http://127.0.0.1:%KB_PORT%/rebuild_index


echo.
echo ========================================
echo 🎯 快速操作命令:
echo - 重建索引(记忆库 8001): curl -X POST http://127.0.0.1:8001/rebuild_index -H "Content-Type: application/json" -d {}
echo - 重建索引(向量库 %KB_PORT%): curl -X POST http://127.0.0.1:%KB_PORT%/rebuild_index -H "Content-Type: application/json" -d {}
echo - 查看文档(8001): http://127.0.0.1:8001/docs
echo - 查看文档(%KB_PORT%): http://127.0.0.1:%KB_PORT%/docs

echo.
echo 完成。
