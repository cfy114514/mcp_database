#!/bin/bash

# Linux 服务器环境检查和修复脚本
# 用于解决 MCP 服务连接问题

echo "=== MCP 服务器环境检查和修复 ==="

# 1. 检查 Python 环境
echo "1. 检查 Python 环境..."

if command -v python3 &> /dev/null; then
    echo "✓ python3 已安装: $(python3 --version)"
else
    echo "✗ python3 未找到，请安装 Python 3"
    exit 1
fi

if command -v python &> /dev/null; then
    echo "✓ python 命令存在: $(python --version)"
else
    echo "⚠ python 命令不存在，创建软链接..."
    # 检查是否有权限创建软链接
    if [ -w "/usr/local/bin" ]; then
        sudo ln -sf $(which python3) /usr/local/bin/python
        echo "✓ 已创建 python -> python3 软链接"
    else
        echo "ℹ 建议手动创建软链接: sudo ln -sf $(which python3) /usr/local/bin/python"
    fi
fi

# 2. 检查 Node.js 环境
echo -e "\n2. 检查 Node.js 环境..."

if command -v node &> /dev/null; then
    echo "✓ Node.js 已安装: $(node --version)"
else
    echo "✗ Node.js 未找到，请安装 Node.js"
fi

if command -v npm &> /dev/null; then
    echo "✓ npm 已安装: $(npm --version)"
else
    echo "⚠ npm 未找到"
fi

# 3. 检查工作目录
echo -e "\n3. 检查工作目录..."

WORK_DIR="/root/mcp_database"
if [ -d "$WORK_DIR" ]; then
    echo "✓ 工作目录存在: $WORK_DIR"
else
    echo "✗ 工作目录不存在: $WORK_DIR"
    echo "ℹ 请确保项目已正确上传到服务器"
fi

# 4. 检查 Python 依赖
echo -e "\n4. 检查 Python 依赖..."

cd "$WORK_DIR" 2>/dev/null || {
    echo "✗ 无法进入工作目录"
    exit 1
}

if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt 存在"
    echo "检查关键依赖..."
    
    if python3 -c "import mcp" 2>/dev/null; then
        echo "✓ mcp 模块已安装"
    else
        echo "✗ mcp 模块未安装，正在安装..."
        pip3 install -r requirements.txt
    fi
    
    if python3 -c "import fastapi" 2>/dev/null; then
        echo "✓ fastapi 模块已安装"
    else
        echo "✗ fastapi 模块未安装"
    fi
else
    echo "✗ requirements.txt 不存在"
fi

# 5. 检查文件权限
echo -e "\n5. 检查文件权限..."

for file in "context_aggregator_mcp.py" "knowledge_base_mcp.py" "knowledge_base_service.py"; do
    if [ -f "$file" ]; then
        if [ -x "$file" ]; then
            echo "✓ $file 有执行权限"
        else
            echo "⚠ $file 缺少执行权限，正在修复..."
            chmod +x "$file"
            echo "✓ 已为 $file 添加执行权限"
        fi
    else
        echo "✗ $file 文件不存在"
    fi
done

# 6. 创建日志目录
echo -e "\n6. 创建日志目录..."

LOG_DIR="/root/logs"
if [ -d "$LOG_DIR" ]; then
    echo "✓ 日志目录存在: $LOG_DIR"
else
    echo "⚠ 创建日志目录: $LOG_DIR"
    mkdir -p "$LOG_DIR"
    echo "✓ 日志目录创建完成"
fi

# 7. 测试 Python 模块导入
echo -e "\n7. 测试 Python 模块导入..."

cd "$WORK_DIR"

echo "测试 context_aggregator_mcp.py..."
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from context_aggregator_mcp import mcp
    print('✓ context_aggregator_mcp 模块导入成功')
except ImportError as e:
    print(f'✗ context_aggregator_mcp 模块导入失败: {e}')
except Exception as e:
    print(f'⚠ 其他错误: {e}')
"; then
    echo "模块测试完成"
fi

# 8. 生成启动脚本
echo -e "\n8. 生成启动脚本..."

cat > start_mcp_services.sh << 'EOF'
#!/bin/bash

# MCP 服务启动脚本
WORK_DIR="/root/mcp_database"
LOG_DIR="/root/logs"

cd "$WORK_DIR" || exit 1

echo "启动 MCP 服务..."

# 启动知识库 HTTP 服务
echo "启动知识库 HTTP 服务..."
nohup python3 knowledge_base_service.py > "$LOG_DIR/knowledge_base_http.log" 2>&1 &
KNOWLEDGE_BASE_PID=$!
echo "知识库 HTTP 服务 PID: $KNOWLEDGE_BASE_PID"

# 等待知识库服务启动
sleep 5

# 测试知识库服务
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✓ 知识库服务启动成功"
else
    echo "✗ 知识库服务启动失败"
fi

echo "MCP 服务启动完成"
echo "日志目录: $LOG_DIR"
echo ""
echo "要停止服务，运行:"
echo "pkill -f knowledge_base_service.py"
EOF

chmod +x start_mcp_services.sh
echo "✓ 启动脚本创建完成: start_mcp_services.sh"

echo -e "\n=== 环境检查完成 ==="
echo ""
echo "下一步操作建议:"
echo "1. 如果有缺失的依赖，请运行: pip3 install -r requirements.txt"
echo "2. 确保所有文件上传到服务器的 /root/mcp_database 目录"
echo "3. 使用 Linux 配置文件: configs/mcp_config.linux.json"
echo "4. 测试启动服务: ./start_mcp_services.sh"
echo ""
