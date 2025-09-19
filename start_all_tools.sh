#!/bin/bash

# MCP 三工具统一启动脚本 - Linux版本
# 包含记忆库工具、向量数据库工具、角色人设服务

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================"
echo -e "    MCP 三工具统一启动器"
echo -e "========================================"
echo -e "${NC}"
echo -e "🧠 记忆库工具 (端口 8001)"
echo -e "📚 向量数据库工具 (端口 8000)"  
echo -e "👤 角色人设服务 (Node.js MCP)"
echo -e "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: Python3 未安装${NC}"
    echo "请安装 Python 3.7+ "
    exit 1
fi

# 检查主要文件
if [ ! -f "deploy_all_tools.py" ]; then
    echo -e "${RED}❌ 错误: deploy_all_tools.py 不存在${NC}"
    echo "请确保在正确的项目目录中运行此脚本"
    exit 1
fi

echo -e "${BLUE}🚀 启动 MCP 三工具统一部署系统...${NC}"
echo ""

# 询问运行模式
echo "选择模式:"
echo "  [1] 一键部署 (推荐)"
echo "  [2] 仅启动服务"
echo "  [3] 检查环境"
echo "  [4] 停止所有服务"
echo ""
read -p "请选择 (默认: 1): " mode

if [ -z "$mode" ]; then
    mode=1
fi

case $mode in
    1)
        echo -e "${GREEN}📦 执行一键部署（包含环境检查、依赖安装、配置、启动、测试）${NC}"
        python3 deploy_all_tools.py deploy
        ;;
    2)
        echo -e "${GREEN}🚀 仅启动所有服务${NC}"
        python3 deploy_all_tools.py start
        ;;
    3)
        echo -e "${GREEN}🔍 执行环境检查${NC}"
        python3 deploy_all_tools.py check
        ;;
    4)
        echo -e "${YELLOW}🛑 停止所有服务${NC}"
        python3 deploy_all_tools.py stop
        exit 0
        ;;
    *)
        echo -e "${YELLOW}❌ 无效选择，使用默认一键部署模式${NC}"
        python3 deploy_all_tools.py deploy
        ;;
esac

echo ""
echo -e "${GREEN}========================================"
echo -e "部署完成，显示服务状态..."
echo -e "========================================"
echo -e "${NC}"

# 显示服务状态
python3 deploy_all_tools.py status

echo ""
echo -e "${GREEN}========================================"
echo -e "🎯 快速操作命令:"
echo -e "${NC}"
echo "  python3 deploy_all_tools.py status  - 查看服务状态"
echo "  python3 deploy_all_tools.py test    - 运行测试"
echo "  python3 deploy_all_tools.py stop    - 停止所有服务"
echo ""
echo -e "${BLUE}📋 服务访问地址:"
echo -e "${NC}"
echo "  http://localhost:8001/docs  - 记忆库工具API"
echo "  http://localhost:8000/docs  - 向量数据库工具API"
echo ""

# 如果是交互式终端，等待用户输入
if [ -t 0 ]; then
    read -p "按 Enter 键退出..."
fi
