#!/bin/bash

# Linux环境配置验证和修复脚本
# 确保MCP记忆系统能够正常运行

set -e

WORK_DIR="/root/mcp_database"
CONFIG_FILE="$WORK_DIR/configs/mcp_config.linux.json"

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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查函数
check_requirement() {
    local name=$1
    local command=$2
    local fix_hint=$3
    
    echo -n "检查 $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        if [ -n "$fix_hint" ]; then
            print_warn "修复建议: $fix_hint"
        fi
        return 1
    fi
}

# 主要检查流程
print_step "1. 检查基础环境"

# 检查Python3
check_requirement "Python3" "python3 --version" "安装Python3: apt-get install python3"

# 检查pip3
check_requirement "pip3" "pip3 --version" "安装pip3: apt-get install python3-pip"

# 检查curl
check_requirement "curl" "curl --version" "安装curl: apt-get install curl"

echo

print_step "2. 检查Python包依赖"

# 检查Python包
required_packages=("fastapi" "uvicorn" "numpy" "requests" "logging")
for package in "${required_packages[@]}"; do
    check_requirement "Python包: $package" "python3 -c 'import $package'" "安装: pip3 install $package"
done

echo

print_step "3. 检查工作目录和文件"

# 检查工作目录
check_requirement "工作目录" "[ -d '$WORK_DIR' ]" "创建目录: mkdir -p $WORK_DIR"

# 检查关键文件
key_files=(
    "knowledge_base_service.py"
    "embedding_memory_processor.py"
    "embedding_context_aggregator_mcp.py"
    "configs/mcp_config.linux.json"
)

for file in "${key_files[@]}"; do
    check_requirement "文件: $file" "[ -f '$WORK_DIR/$file' ]" "确保文件存在并正确配置"
done

echo

print_step "4. 检查配置文件"

if [ -f "$CONFIG_FILE" ]; then
    print_info "验证MCP配置文件..."
    
    # 检查端口配置
    if grep -q '"KB_PORT": "8001"' "$CONFIG_FILE"; then
        echo -e "端口配置: ${GREEN}✓${NC} (8001)"
    else
        echo -e "端口配置: ${RED}✗${NC} (需要8001)"
        print_warn "请确保配置文件中KB_PORT设置为8001"
    fi
    
    # 检查Python命令
    if grep -q '"command": "python3"' "$CONFIG_FILE"; then
        echo -e "Python命令: ${GREEN}✓${NC} (python3)"
    else
        echo -e "Python命令: ${RED}✗${NC} (需要python3)"
        print_warn "请确保配置文件中使用python3命令"
    fi
    
    # 检查路径配置
    if grep -q '"/root/mcp_database"' "$CONFIG_FILE"; then
        echo -e "路径配置: ${GREEN}✓${NC} (/root/mcp_database)"
    else
        echo -e "路径配置: ${YELLOW}⚠${NC} (检查路径设置)"
    fi
    
else
    print_error "MCP配置文件不存在: $CONFIG_FILE"
fi

echo

print_step "5. 检查网络和端口"

# 检查端口是否被占用
if netstat -tlnp 2>/dev/null | grep -q ":8001 "; then
    print_warn "端口8001已被占用"
    print_info "查看占用进程:"
    netstat -tlnp 2>/dev/null | grep ":8001 " || true
else
    echo -e "端口8001: ${GREEN}可用${NC}"
fi

echo

print_step "6. 自动修复建议"

# 创建自动修复脚本
cat > "$WORK_DIR/auto_fix.sh" << 'EOF'
#!/bin/bash

# 自动修复脚本
echo "开始自动修复环境..."

# 更新系统包
apt-get update

# 安装必要的系统包
apt-get install -y python3 python3-pip curl net-tools

# 安装Python包
pip3 install fastapi uvicorn numpy requests

# 创建日志和PID目录
mkdir -p /root/logs /root/pids

# 设置文件权限
chmod +x /root/mcp_database/*.sh

echo "自动修复完成！"
EOF

chmod +x "$WORK_DIR/auto_fix.sh"

print_info "自动修复脚本已创建: $WORK_DIR/auto_fix.sh"
print_info "运行修复: cd $WORK_DIR && ./auto_fix.sh"

echo

print_step "7. 测试建议"

echo "环境检查完成！"
echo ""
echo "下一步操作建议:"
echo "1. 如有错误，运行自动修复: ./auto_fix.sh"
echo "2. 启动服务: ./manage_linux_services.sh start"
echo "3. 检查状态: ./manage_linux_services.sh status"
echo "4. 测试功能: ./manage_linux_services.sh test"
echo ""

# 创建快速部署脚本
cat > "$WORK_DIR/deploy.sh" << 'EOF'
#!/bin/bash

# 快速部署脚本
echo "开始快速部署MCP记忆系统..."

# 1. 运行环境检查
./check_linux_env.sh

# 2. 自动修复（如果需要）
if [ -f "./auto_fix.sh" ]; then
    echo "运行自动修复..."
    ./auto_fix.sh
fi

# 3. 启动服务
echo "启动服务..."
./manage_linux_services.sh start

# 4. 测试功能
echo "测试功能..."
sleep 5
./manage_linux_services.sh test

echo "部署完成！"
EOF

chmod +x "$WORK_DIR/deploy.sh"

print_info "快速部署脚本已创建: $WORK_DIR/deploy.sh"
print_info "一键部署: cd $WORK_DIR && ./deploy.sh"
