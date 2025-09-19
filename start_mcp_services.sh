#!/bin/bash

# MCP 记忆系统启动脚本 - 修复版本
# 解决端口配置和启动检测问题

set -e

WORK_DIR="/root/mcp_database"
LOG_DIR="/root/logs"
PID_DIR="/root/pids"
KB_PORT=8001  # 统一使用8001端口

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

print_info "=== MCP 记忆系统启动脚本 ==="

# 检查工作目录
if [ ! -d "$WORK_DIR" ]; then
    print_error "工作目录不存在: $WORK_DIR"
    exit 1
fi

cd "$WORK_DIR"

# 创建必要目录
mkdir -p "$LOG_DIR" "$PID_DIR"

# 检查 Python 环境
print_info "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    print_error "python3 未找到，请先安装 Python 3"
    exit 1
fi

print_info "✓ Python3 版本: $(python3 --version)"

# 检查关键文件
key_files=("knowledge_base_service.py" "embedding_memory_processor.py" "embedding_context_aggregator_mcp.py")
for file in "${key_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "关键文件缺失: $file"
        exit 1
    fi
done

print_info "✓ 关键文件检查通过"

# 检查 Python 依赖
print_info "检查 Python 依赖..."
required_packages=("fastapi" "uvicorn" "numpy" "requests")
for package in "${required_packages[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        print_error "Python包缺失: $package"
        print_info "请运行: pip3 install $package"
        exit 1
    fi
done

print_info "✓ Python 依赖检查通过"

# 停止现有服务
print_info "停止现有服务..."
if [ -f "$PID_DIR/knowledge_base_http.pid" ]; then
    old_pid=$(cat "$PID_DIR/knowledge_base_http.pid")
    if kill -0 "$old_pid" 2>/dev/null; then
        print_info "停止现有服务 (PID: $old_pid)"
        kill "$old_pid"
        sleep 2
    fi
    rm -f "$PID_DIR/knowledge_base_http.pid"
fi

# 清理端口
if netstat -tlnp 2>/dev/null | grep -q ":$KB_PORT "; then
    print_warn "端口 $KB_PORT 被占用，尝试清理..."
    fuser -k $KB_PORT/tcp 2>/dev/null || true
    sleep 2
fi

# 设置环境变量
export KB_PORT=$KB_PORT
export PYTHONPATH="$WORK_DIR"

# 启动知识库 HTTP 服务
print_info "启动知识库 HTTP 服务 (端口: $KB_PORT)..."

log_file="$LOG_DIR/knowledge_base_http.log"
pid_file="$PID_DIR/knowledge_base_http.pid"

# 清空旧日志
> "$log_file"

# 启动服务
nohup python3 knowledge_base_service.py > "$log_file" 2>&1 &
service_pid=$!

echo $service_pid > "$pid_file"
print_info "知识库服务启动中 (PID: $service_pid)"

# 等待服务启动 - 使用正确的端口检查
print_info "等待服务启动..."
max_wait=60  # 增加等待时间
wait_count=0

while [ $wait_count -lt $max_wait ]; do
    # 检查进程是否还活着
    if ! kill -0 "$service_pid" 2>/dev/null; then
        print_error "服务进程意外退出"
        print_info "查看日志内容:"
        if [ -f "$log_file" ]; then
            cat "$log_file"
        fi
        exit 1
    fi
    
    # 检查服务是否响应
    if curl -s "http://localhost:$KB_PORT/docs" > /dev/null 2>&1; then
        print_info "✓ 知识库服务启动成功！"
        break
    fi
    
    # 每5秒显示一次进度
    if [ $((wait_count % 5)) -eq 0 ] && [ $wait_count -gt 0 ]; then
        print_debug "等待中... ($wait_count/$max_wait 秒)"
        # 显示最新的几行日志
        if [ -f "$log_file" ] && [ -s "$log_file" ]; then
            print_debug "最新日志:"
            tail -n 3 "$log_file" | while read line; do
                print_debug "  $line"
            done
        fi
    fi
    
    sleep 1
    ((wait_count++))
done

if [ $wait_count -eq $max_wait ]; then
    print_error "服务启动超时 (${max_wait}秒)"
    print_info "查看完整日志:"
    if [ -f "$log_file" ]; then
        cat "$log_file"
    fi
    
    # 清理失败的进程
    if kill -0 "$service_pid" 2>/dev/null; then
        kill "$service_pid"
    fi
    rm -f "$pid_file"
    exit 1
fi

# 测试服务功能
print_info "测试服务功能..."

# 测试基本API
if curl -s "http://localhost:$KB_PORT/stats" > /dev/null 2>&1; then
    print_info "✓ API 基本功能正常"
else
    print_warn "⚠ API 基本功能测试失败"
fi

# 简单的添加测试
test_result=$(curl -s -X POST "http://localhost:$KB_PORT/add" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "启动测试记忆",
        "tags": ["test", "startup"],
        "metadata": {
            "user_id": "test_startup",
            "test": true,
            "timestamp": "'$(date -Iseconds)'"
        }
    }' 2>/dev/null)

if echo "$test_result" | grep -q "success.*true"; then
    print_info "✓ 记忆存储功能正常"
else
    print_warn "⚠ 记忆存储功能测试异常"
    print_debug "测试结果: $test_result"
fi

print_info "=== 启动完成 ==="
echo ""
print_info "服务信息:"
echo "  - 知识库 HTTP 服务: http://localhost:$KB_PORT"
echo "  - 进程 PID: $service_pid"
echo "  - 日志文件: $log_file"
echo "  - PID 文件: $pid_file"
echo ""
print_info "管理命令:"
echo "  - 查看状态: ./manage_linux_services.sh status"
echo "  - 查看日志: ./manage_linux_services.sh logs"
echo "  - 测试功能: ./manage_linux_services.sh test"
echo "  - 停止服务: ./manage_linux_services.sh stop"
echo ""
print_info "测试命令:"
echo "  curl http://localhost:$KB_PORT/docs"
echo "  curl http://localhost:$KB_PORT/stats"

# 显示最新的几行日志
if [ -f "$log_file" ] && [ -s "$log_file" ]; then
    echo ""
    print_info "服务日志 (最新5行):"
    tail -n 5 "$log_file" | while read line; do
        echo "  $line"
    done
fi
