#!/bin/bash

# Linux服务器MCP服务管理脚本
# 用于启动、停止和检查MCP记忆系统服务

set -e

WORK_DIR="/root/mcp_database"
LOG_DIR="/root/logs"
PID_DIR="/root/pids"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 创建必要的目录
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# 切换到工作目录
cd "$WORK_DIR"

# 函数：打印彩色信息
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

# 函数：检查服务状态
check_service() {
    local service_name=$1
    local port=$2
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            if [ -n "$port" ]; then
                if curl -s "http://localhost:$port/docs" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓${NC} $service_name 运行中 (PID: $pid, 端口: $port)"
                else
                    echo -e "${YELLOW}⚠${NC} $service_name 进程存在但服务不可访问 (PID: $pid)"
                fi
            else
                echo -e "${GREEN}✓${NC} $service_name 运行中 (PID: $pid)"
            fi
            return 0
        else
            echo -e "${RED}✗${NC} $service_name 未运行"
            rm -f "$pid_file"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} $service_name 未运行"
        return 1
    fi
}

# 函数：启动知识库HTTP服务
start_knowledge_base() {
    print_info "启动知识库HTTP服务..."
    
    local pid_file="$PID_DIR/knowledge_base_http.pid"
    local log_file="$LOG_DIR/knowledge_base_http.log"
    
    # 检查是否已经运行
    if check_service "knowledge_base_http" "8001" > /dev/null 2>&1; then
        print_warn "知识库HTTP服务已经在运行"
        return 0
    fi
    
    # 设置环境变量并启动服务
    export KB_PORT=8001
    export PYTHONPATH="$WORK_DIR"
    
    nohup python3 knowledge_base_service.py > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    print_info "知识库HTTP服务启动中 (PID: $pid)"
    
    # 等待服务启动
    local max_wait=30
    local count=0
    while [ $count -lt $max_wait ]; do
        if curl -s "http://localhost:8001/docs" > /dev/null 2>&1; then
            print_info "✓ 知识库HTTP服务启动成功 (端口: 8001)"
            return 0
        fi
        sleep 1
        ((count++))
    done
    
    print_error "知识库HTTP服务启动超时"
    return 1
}

# 函数：停止服务
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_info "停止 $service_name (PID: $pid)"
            kill "$pid"
            
            # 等待进程结束
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            # 如果进程仍然存在，强制终止
            if kill -0 "$pid" 2>/dev/null; then
                print_warn "强制终止 $service_name"
                kill -9 "$pid"
            fi
            
            rm -f "$pid_file"
            print_info "✓ $service_name 已停止"
        else
            print_warn "$service_name 进程不存在，清理PID文件"
            rm -f "$pid_file"
        fi
    else
        print_warn "$service_name 未运行"
    fi
}

# 函数：检查所有服务状态
check_all_services() {
    print_info "检查服务状态..."
    echo
    check_service "knowledge_base_http" "8001"
    echo
}

# 函数：查看日志
show_logs() {
    local service_name=${1:-"knowledge_base_http"}
    local log_file="$LOG_DIR/${service_name}.log"
    
    if [ -f "$log_file" ]; then
        print_info "显示 $service_name 日志 (最后50行):"
        echo "----------------------------------------"
        tail -n 50 "$log_file"
    else
        print_warn "$service_name 日志文件不存在"
    fi
}

# 函数：测试记忆功能
test_memory_system() {
    print_info "测试记忆系统功能..."
    
    # 检查知识库服务是否可访问
    if ! curl -s "http://localhost:8001/stats" > /dev/null 2>&1; then
        print_error "知识库服务不可访问，请先启动服务"
        return 1
    fi
    
    # 测试添加记忆
    print_info "测试添加记忆..."
    local test_result=$(curl -s -X POST "http://localhost:8001/add" \
        -H "Content-Type: application/json" \
        -d '{
            "content": "测试记忆：用户喜欢喝咖啡",
            "tags": ["memory", "test", "preference"],
            "metadata": {
                "user_id": "test_user_linux",
                "memory_type": "preference",
                "importance": 7.0,
                "created_at": "'$(date -Iseconds)'"
            }
        }')
    
    if echo "$test_result" | grep -q "success.*true"; then
        print_info "✓ 记忆添加测试成功"
        
        # 测试搜索记忆
        print_info "测试搜索记忆..."
        local search_result=$(curl -s -X POST "http://localhost:8001/search" \
            -H "Content-Type: application/json" \
            -d '{
                "query": "咖啡",
                "tags": ["memory"],
                "top_k": 3,
                "metadata_filter": {"user_id": "test_user_linux"}
            }')
        
        if echo "$search_result" | grep -q "success.*true"; then
            print_info "✓ 记忆搜索测试成功"
            print_info "记忆系统工作正常！"
        else
            print_error "记忆搜索测试失败"
            print_debug "搜索结果: $search_result"
        fi
    else
        print_error "记忆添加测试失败"
        print_debug "添加结果: $test_result"
    fi
}

# 主要功能
case "${1:-help}" in
    "start")
        print_info "启动MCP记忆系统服务..."
        start_knowledge_base
        echo
        check_all_services
        ;;
    
    "stop")
        print_info "停止MCP记忆系统服务..."
        stop_service "knowledge_base_http"
        ;;
    
    "restart")
        print_info "重启MCP记忆系统服务..."
        stop_service "knowledge_base_http"
        sleep 2
        start_knowledge_base
        echo
        check_all_services
        ;;
    
    "status")
        check_all_services
        ;;
    
    "logs")
        show_logs "${2:-knowledge_base_http}"
        ;;
    
    "test")
        test_memory_system
        ;;
    
    "help"|*)
        echo "MCP记忆系统服务管理脚本"
        echo ""
        echo "用法: $0 {start|stop|restart|status|logs|test|help}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动所有服务"
        echo "  stop    - 停止所有服务"
        echo "  restart - 重启所有服务"
        echo "  status  - 检查服务状态"
        echo "  logs    - 查看服务日志"
        echo "  test    - 测试记忆系统功能"
        echo "  help    - 显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  $0 start          # 启动服务"
        echo "  $0 status         # 检查状态"
        echo "  $0 logs           # 查看日志"
        echo "  $0 test           # 测试功能"
        ;;
esac
