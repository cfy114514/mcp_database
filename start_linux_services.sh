#!/bin/bash

# MCP 服务启动脚本 - Linux 版本
# 解决 "spawn python ENOENT" 问题

set -e  # 遇到错误立即退出

WORK_DIR="/root/mcp_database"
LOG_DIR="/root/logs"
CONFIG_FILE="configs/mcp_config.linux.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== MCP 服务启动脚本 (Linux) ===${NC}"

# 检查工作目录
if [ ! -d "$WORK_DIR" ]; then
    echo -e "${RED}错误: 工作目录不存在: $WORK_DIR${NC}"
    exit 1
fi

cd "$WORK_DIR"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查 Python 环境
echo "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: python3 未找到${NC}"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo -e "${YELLOW}警告: python 命令不存在，使用 python3${NC}"
    # 创建临时别名
    alias python=python3
fi

# 检查 Node.js (如果需要 persona 服务)
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓ Node.js 可用: $(node --version)${NC}"
else
    echo -e "${YELLOW}⚠ Node.js 不可用，persona 服务将无法启动${NC}"
fi

# 测试 Python 环境
echo "测试 Python 环境..."
python3 test_linux_env.py
if [ $? -ne 0 ]; then
    echo -e "${RED}环境测试失败，请检查依赖${NC}"
    exit 1
fi

# 停止现有服务
echo "停止现有服务..."
pkill -f "knowledge_base_service.py" || true
pkill -f "context_aggregator_mcp.py" || true
pkill -f "knowledge_base_mcp.py" || true

sleep 2

# 启动知识库 HTTP 服务
echo -e "${GREEN}启动知识库 HTTP 服务...${NC}"
nohup python3 knowledge_base_service.py > "$LOG_DIR/knowledge_base_http.log" 2>&1 &
KB_HTTP_PID=$!
echo "知识库 HTTP 服务 PID: $KB_HTTP_PID"

# 等待服务启动
echo "等待知识库服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 知识库服务启动成功${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ 知识库服务启动超时${NC}"
        exit 1
    fi
    sleep 1
done

# 保存 PID 文件
echo $KB_HTTP_PID > "$LOG_DIR/knowledge_base_http.pid"

echo -e "${GREEN}=== MCP 服务启动完成 ===${NC}"
echo ""
echo "服务状态:"
echo "- 知识库 HTTP 服务: http://localhost:8000"
echo "- 日志目录: $LOG_DIR"
echo "- PID 文件: $LOG_DIR/knowledge_base_http.pid"
echo ""
echo "测试命令:"
echo "curl http://localhost:8000/docs"
echo ""
echo "停止服务:"
echo "pkill -f knowledge_base_service.py"
echo ""
echo "查看日志:"
echo "tail -f $LOG_DIR/knowledge_base_http.log"
