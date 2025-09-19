# Linux 服务器部署指南

## 问题诊断

你遇到的错误 `spawn python ENOENT` 表示系统找不到 `python` 命令。这是Linux服务器上的常见问题。

## 解决方案

### 1. 上传文件到服务器

确保所有文件已上传到服务器的 `/root/mcp_database` 目录：

```bash
# 在服务器上检查目录
ls -la /root/mcp_database/
```

### 2. 运行环境检查脚本

```bash
cd /root/mcp_database
chmod +x fix_linux_env.sh
./fix_linux_env.sh
```

这个脚本会：
- 检查 Python 和 Node.js 环境
- 创建必要的软链接 (python -> python3)
- 设置文件权限
- 安装缺失的依赖
- 创建日志目录

### 3. 测试 Python 环境

```bash
python3 test_linux_env.py
```

这会验证所有模块是否正确安装。

### 4. 启动服务

```bash
chmod +x start_linux_services.sh
./start_linux_services.sh
```

### 5. 使用正确的配置文件

MCP 客户端应该使用 `configs/mcp_config.linux.json`，这个配置文件使用了：
- `python3` 而不是 `python`
- Linux 路径格式 (`/root/mcp_database`)
- 正确的环境变量

## 手动排查步骤

如果自动脚本不工作，可以手动检查：

### 检查 Python 命令

```bash
# 检查 python3 是否存在
which python3
python3 --version

# 检查 python 是否存在
which python
# 如果不存在，创建软链接
sudo ln -sf $(which python3) /usr/local/bin/python
```

### 安装依赖

```bash
cd /root/mcp_database
pip3 install -r requirements.txt
```

### 测试模块导入

```bash
python3 -c "
import mcp
from mcp.server.fastmcp import FastMCP
print('MCP 模块导入成功')
"
```

### 设置文件权限

```bash
chmod +x *.py
chmod +x configs/*.json
```

### 手动启动服务

```bash
# 启动知识库服务
python3 knowledge_base_service.py &

# 等待几秒，然后测试
curl http://localhost:8000/docs
```

## 常见问题

### 1. `python: command not found`
**解决**: 创建软链接 `ln -sf $(which python3) /usr/local/bin/python`

### 2. `ModuleNotFoundError: No module named 'mcp'`
**解决**: 安装依赖 `pip3 install -r requirements.txt`

### 3. `Permission denied`
**解决**: 设置执行权限 `chmod +x *.py`

### 4. 端口被占用
**解决**: 
```bash
# 检查端口
netstat -tlnp | grep :8000
# 杀死进程
pkill -f knowledge_base_service.py
```

## 服务管理

### 启动所有服务
```bash
./start_linux_services.sh
```

### 停止所有服务
```bash
pkill -f "knowledge_base_service.py"
pkill -f "context_aggregator_mcp.py"
pkill -f "knowledge_base_mcp.py"
```

### 查看日志
```bash
tail -f /root/logs/knowledge_base_http.log
```

### 检查服务状态
```bash
curl http://localhost:8000/docs
ps aux | grep python3
```

## 下一步

1. 运行环境检查脚本: `./fix_linux_env.sh`
2. 测试环境: `python3 test_linux_env.py`
3. 启动服务: `./start_linux_services.sh`
4. 配置 MCP 客户端使用 `configs/mcp_config.linux.json`

如果仍有问题，请检查日志文件并提供具体的错误信息。
