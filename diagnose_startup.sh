#!/bin/bash

# MCP服务启动问题诊断脚本
# 用于快速定位和解决启动失败问题

set -e

WORK_DIR="/root/mcp_database"
LOG_FILE="/root/logs/knowledge_base_http.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header "MCP服务启动问题诊断"

cd "$WORK_DIR"

# 1. 检查基础环境
print_header "1. 基础环境检查"

if command -v python3 &> /dev/null; then
    print_success "Python3 可用: $(python3 --version)"
else
    print_error "Python3 未安装"
    echo "解决方案: apt-get install python3 python3-pip"
    exit 1
fi

# 2. 检查Python依赖
print_header "2. Python依赖检查"

required_packages=("fastapi" "uvicorn" "numpy" "requests")
missing_packages=()

for package in "${required_packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        print_success "Python包 $package 可用"
    else
        print_error "Python包 $package 缺失"
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    print_warning "发现缺失的Python包，正在安装..."
    for package in "${missing_packages[@]}"; do
        print_info "安装 $package..."
        pip3 install "$package"
    done
fi

# 3. 检查关键文件
print_header "3. 关键文件检查"

key_files=("knowledge_base_service.py" "embedding_memory_processor.py" "configs/mcp_config.linux.json")
for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "文件存在: $file"
    else
        print_error "文件缺失: $file"
    fi
done

# 4. 检查端口配置
print_header "4. 端口配置检查"

if [ -f "configs/mcp_config.linux.json" ]; then
    port_8001_count=$(grep -c "8001" configs/mcp_config.linux.json || echo "0")
    port_8000_count=$(grep -c "8000" configs/mcp_config.linux.json || echo "0")
    
    print_info "配置文件中端口8001出现次数: $port_8001_count"
    print_info "配置文件中端口8000出现次数: $port_8000_count"
    
    if [ "$port_8001_count" -gt 0 ]; then
        print_success "端口配置使用8001 (正确)"
    else
        print_warning "端口配置可能有问题，检查是否使用8001"
    fi
fi

# 5. 检查端口占用
print_header "5. 端口占用检查"

if netstat -tlnp 2>/dev/null | grep -q ":8001 "; then
    print_warning "端口8001已被占用:"
    netstat -tlnp 2>/dev/null | grep ":8001 "
    print_info "清理占用进程..."
    fuser -k 8001/tcp 2>/dev/null || true
    sleep 2
else
    print_success "端口8001可用"
fi

# 6. 尝试手动启动服务进行诊断
print_header "6. 服务启动诊断"

print_info "清理旧日志..."
mkdir -p /root/logs
> "$LOG_FILE"

print_info "设置环境变量..."
export KB_PORT=8001
export PYTHONPATH="$WORK_DIR"

print_info "尝试启动服务..."
timeout 10s python3 knowledge_base_service.py > "$LOG_FILE" 2>&1 &
service_pid=$!

print_info "服务PID: $service_pid"

# 等待几秒让服务初始化
sleep 5

# 检查进程是否还活着
if kill -0 "$service_pid" 2>/dev/null; then
    print_success "服务进程正在运行"
    
    # 测试连接
    if curl -s "http://localhost:8001/docs" > /dev/null 2>&1; then
        print_success "服务响应正常"
        print_info "服务启动成功！可以使用以下命令管理:"
        echo "  - 停止: kill $service_pid"
        echo "  - 查看状态: ./manage_linux_services.sh status"
        echo "  - 重启: ./manage_linux_services.sh restart"
    else
        print_warning "服务进程运行但无法响应HTTP请求"
        print_info "检查服务日志..."
    fi
else
    print_error "服务进程已退出"
fi

# 7. 显示日志内容
print_header "7. 服务日志分析"

if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
    print_info "服务日志内容:"
    echo "----------------------------------------"
    cat "$LOG_FILE"
    echo "----------------------------------------"
    
    # 分析常见错误
    if grep -q "ModuleNotFoundError" "$LOG_FILE"; then
        print_error "发现模块导入错误"
        print_info "请检查Python包安装: pip3 install -r requirements.txt"
    fi
    
    if grep -q "Permission denied" "$LOG_FILE"; then
        print_error "发现权限错误"
        print_info "请检查文件权限: chmod +x *.py"
    fi
    
    if grep -q "Address already in use" "$LOG_FILE"; then
        print_error "端口被占用"
        print_info "请使用其他端口或清理占用进程"
    fi
    
    if grep -q "No module named" "$LOG_FILE"; then
        module_name=$(grep "No module named" "$LOG_FILE" | sed -n "s/.*No module named '\([^']*\)'.*/\1/p" | head -1)
        print_error "缺少Python模块: $module_name"
        print_info "安装命令: pip3 install $module_name"
    fi
else
    print_warning "没有找到日志文件或日志为空"
fi

# 8. 生成修复建议
print_header "8. 修复建议"

print_info "根据诊断结果，建议执行以下操作:"

echo "1. 安装所有依赖:"
echo "   pip3 install fastapi uvicorn numpy requests python-multipart"
echo ""

echo "2. 使用改进的启动脚本:"
echo "   ./start_mcp_services.sh"
echo ""

echo "3. 或使用完整管理脚本:"
echo "   ./manage_linux_services.sh start"
echo ""

echo "4. 查看实时日志:"
echo "   tail -f $LOG_FILE"
echo ""

echo "5. 测试服务:"
echo "   curl http://localhost:8001/docs"
echo "   curl http://localhost:8001/stats"

# 清理测试进程
if kill -0 "$service_pid" 2>/dev/null; then
    print_info "清理诊断进程..."
    kill "$service_pid" 2>/dev/null || true
fi

print_header "诊断完成"
