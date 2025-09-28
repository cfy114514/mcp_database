# MCP记忆系统架构说明

> 端口与实例约定（重要）
> - knowledge_base_service.py 为同一HTTP实现，会按用途启动两个实例：
>   - 8100：向量数据库实例（通用文档向量存储/检索）
>   - 8001：记忆库实例（供 embedding_memory_processor 读写）
> - 部署脚本会分别拉起两个端口；手动运行时可通过临时设置环境变量 KB_PORT 指定端口。

## 🏗️ 为什么需要独立的记忆库服务？

### 架构演进对比

#### 旧方案：文件存储方式
```
MCP 工具 → 直接读写文件 → vectors.npy + documents.json
```
- ✅ 简单直接，无需额外服务
- ❌ 并发访问问题
- ❌ 无法提供API接口
- ❌ 缺乏数据验证和安全控制

#### 新方案：HTTP服务架构
```
MCP 工具 → HTTP API → 记忆库服务 → 数据存储
```
- ✅ 支持并发访问
- ✅ 标准HTTP API接口
- ✅ 数据验证和安全控制
- ✅ 可扩展和监控
- ✅ 支持用户隔离

## 🔄 服务启动流程

### 必要的启动顺序

1. **知识库HTTP服务** (端口8001/8100)
   - 提供记忆存储和检索API（8001 实例）
   - 提供通用向量数据库API（8100 实例）
   - 必须首先启动

2. **MCP工具服务**
   - 通过HTTP调用知识库服务
   - 依赖知识库服务运行

### 为什么必须先启动记忆库？

```mermaid
graph TD
    A[用户使用MCP工具] --> B[MCP工具调用]
    B --> C[HTTP请求到localhost:8001/8100]
    C --> D[知识库服务处理]
    D --> E[存储/检索记忆]
    
    F[如果服务未启动] --> G[连接被拒绝]
    G --> H[MCP工具报错]
```

## 🛠️ 启动脚本说明

### 主要启动脚本（统一入口）

1. deploy_all_tools.py — 统一部署/状态/测试（推荐）
2. manage_linux_services.sh — Linux 服务管理（start/stop/status/test/logs）
3. start_all_tools.sh — Linux 一键启动（可选）

### 推荐使用方式

```bash
# 方式1: 使用统一部署脚本（推荐，跨平台）
python3 deploy_all_tools.py status
python3 deploy_all_tools.py test

# 方式2: 使用 Linux 管理脚本
./manage_linux_services.sh start
./manage_linux_services.sh status

# 方式3: Windows
start_all_tools.bat
```

## 🐛 常见启动问题及解决方案

### 1. "知识库服务启动失败"

**可能原因:**
- 端口配置不一致 (8100 vs 8001)
- Python依赖包缺失
- 权限问题
- 端口被占用

**解决步骤:**
```bash
# 检查端口配置
grep -r "8001\|8100" configs/

# 检查Python依赖
python3 -c "import fastapi, uvicorn, numpy, requests"

# 检查端口占用
netstat -tlnp | grep 8001
netstat -tlnp | grep 8100

# 查看详细错误
tail -f logs/knowledge_base_http.log
```

### 2. "Connection refused localhost:8001/8100"

**原因:** 知识库服务未正确启动

**解决:**
```bash
# 重启服务
./manage_linux_services.sh restart

# 检查服务状态
./manage_linux_services.sh status

# 测试连接（两个实例）
curl http://localhost:8001/docs
curl http://localhost:8100/docs
```

### 3. Python包导入错误

**解决:**
```bash
# 安装依赖
pip3 install fastapi uvicorn numpy requests python-multipart

# 或使用requirements.txt
pip3 install -r requirements.txt
```

## 📊 服务健康检查

### 检查服务是否正常运行

```bash
# 1. 检查进程
ps aux | grep knowledge_base_service

# 2. 检查端口
netstat -tlnp | grep 8001
netstat -tlnp | grep 8100

# 3. 测试API
curl http://localhost:8001/docs
curl http://localhost:8001/stats
curl http://localhost:8100/docs
curl http://localhost:8100/stats

# 4. 使用管理脚本
./manage_linux_services.sh status
./manage_linux_services.sh test
```

### 查看服务日志

```bash
# 实时查看日志
tail -f logs/knowledge_base_http.log

# 查看错误日志
grep -i error logs/knowledge_base_http.log

# 使用管理脚本
./manage_linux_services.sh logs
```

## 🚀 生产环境最佳实践

### 1. 使用进程管理器

**Systemd服务配置** (`/etc/systemd/system/mcp-memory.service`):
```ini
[Unit]
Description=MCP Memory Knowledge Base Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/mcp_database
Environment=KB_PORT=8001
Environment=PYTHONPATH=/root/mcp_database
ExecStart=/usr/bin/python3 knowledge_base_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> 若需部署向量数据库实例，请将 `Environment=KB_PORT=8100` 并相应调整服务名与端口映射。

启用服务:
```bash
systemctl enable mcp-memory
systemctl start mcp-memory
systemctl status mcp-memory
```

### 2. 监控和告警

```bash
# 创建监控脚本
cat > /root/check_mcp_health.sh << 'EOF'
#!/bin/bash
if ! curl -s http://localhost:8001/stats > /dev/null; then
    echo "MCP服务异常" | mail -s "MCP告警" admin@example.com
    systemctl restart mcp-memory
fi
EOF

# 添加到crontab
echo "*/5 * * * * /root/check_mcp_health.sh" | crontab -
```

### 3. 日志轮转

```bash
# 配置logrotate
cat > /etc/logrotate.d/mcp-memory << 'EOF'
/root/logs/knowledge_base_http.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

## 🔧 故障排除清单

当遇到启动问题时，按以下顺序检查：

1. **环境检查**
   ```bash
   ./check_linux_env.sh
   ```

2. **配置验证**
   ```bash
   python3 validate_mcp_config.py
   ```

3. **手动启动测试**
   ```bash
   cd /root/mcp_database
   export KB_PORT=8001
   python3 knowledge_base_service.py
   ```

4. **依赖检查**
   ```bash
   python3 -c "import fastapi, uvicorn, numpy, requests; print('所有依赖正常')"
   ```

5. **端口检查**
   ```bash
   netstat -tlnp | grep 8001
   netstat -tlnp | grep 8100
   ```

6. **日志分析**
   ```bash
   tail -f logs/knowledge_base_http.log
   ```

---

**记住**: 新的embedding记忆系统需要HTTP服务支持，这与之前的文件存储方式不同。服务启动是使用记忆功能的前提条件。
