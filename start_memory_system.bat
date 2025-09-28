@echo off
REM [DEPRECATED] 此脚本已合并至统一部署流程，请使用 deploy_all_tools.py 或 start_all_tools.bat

echo ========================================
echo  注意：start_memory_system.bat 已废弃
echo  请使用以下方式之一：
echo    1) python deploy_all_tools.py deploy
echo    2) start_all_tools.bat
echo ========================================

REM 兼容旧用法：直接转发到统一部署
python deploy_all_tools.py deploy
if %errorlevel% neq 0 (
    echo 统一部署失败，请检查 Python 及依赖
    exit /b 1
)

python deploy_all_tools.py status
exit /b 0
