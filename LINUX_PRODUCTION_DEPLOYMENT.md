# Linux生产环境部署指南

## 🚀 快速部署步骤

### 1. 上传文件到Linux服务器

将整个 `mcp_database` 目录上传到Linux服务器的 `/root/` 目录:

```bash
# 使用scp上传（从Windows到Linux）
scp -r mcp_database root@your-server:/root/

# 或使用rsync（推荐）
rsync -avz mcp_database/ root@your-server:/root/mcp_database/
```

### 2. 登录服务器并设置权限

```bash
# SSH登录服务器
ssh root@your-server

# 进入工作目录
cd /root/mcp_database

# 设置脚本执行权限
chmod +x *.sh
chmod +x scripts/*.sh
```

### 3. 一键部署

```bash
# 运行一键部署脚本
./deploy.sh
```

或者分步骤执行：

```bash
# 步骤1: 检查环境
./check_linux_env.sh

# 步骤2: 修复环境（如果有问题）
./auto_fix.sh

# 步骤3: 启动服务
./manage_linux_services.sh start

# 步骤4: 测试功能
./manage_linux_services.sh test
```

## 📋 详细部署流程

### 环境要求

- Ubuntu 18.04+ / CentOS 7+ / Debian 9+
- Python 3.7+
- 至少 2GB 内存
- 至少 5GB 磁盘空间
- 网络连接（访问embedding API）

### 手动部署步骤

#### 1. 系统环境准备

```bash
# Ubuntu/Debian
apt-get update
apt-get install -y python3 python3-pip curl net-tools git

# CentOS/RHEL
yum update
yum install -y python3 python3-pip curl net-tools git
```

#### 2. Python依赖安装

```bash
cd /root/mcp_database

# 安装Python包
pip3 install -r requirements.txt

# 或手动安装核心包
pip3 install fastapi uvicorn numpy requests python-multipart
```

#### 3. 配置文件验证

```bash
# 检查配置文件
cat configs/mcp_config.linux.json

# 验证端口配置（应该是8001）
grep -n "8001" configs/mcp_config.linux.json
```

#### 4. 服务启动

```bash
# 启动知识库服务
python3 knowledge_base_service.py &

# 或使用管理脚本
./manage_linux_services.sh start
```

#### 5. 服务验证

```bash
# 检查服务状态
./manage_linux_services.sh status

# 测试API
curl http://localhost:8001/docs

# 测试记忆功能
./manage_linux_services.sh test
```

## 🔧 故障排除

### 常见问题及解决方案

#### 1. "spawn python ENOENT" 错误

**原因**: 系统中没有 `python` 命令，只有 `python3`

**解决方案**:
```bash
# 创建python符号链接
ln -s /usr/bin/python3 /usr/bin/python

# 或确保配置文件使用python3
grep -r "python3" configs/
```

#### 2. 端口8001连接被拒绝

**原因**: 知识库服务未启动或端口配置错误

**解决方案**:
```bash
# 检查端口占用
netstat -tlnp | grep 8001

# 重启服务
./manage_linux_services.sh restart

# 查看服务日志
./manage_linux_services.sh logs
```

#### 3. 权限被拒绝错误

**原因**: 脚本没有执行权限

**解决方案**:
```bash
# 设置执行权限
chmod +x *.sh
chmod +x scripts/*.sh

# 检查文件权限
ls -la *.sh
```

#### 4. Python包导入错误

**原因**: 缺少依赖包

**解决方案**:
```bash
# 安装缺少的包
pip3 install fastapi uvicorn numpy requests

# 测试导入
python3 -c "import fastapi, uvicorn, numpy, requests"
```

#### 5. 内存不足错误

**原因**: 服务器内存不足

**解决方案**:
```bash
# 检查内存使用
free -h

# 优化配置（减少并发数）
# 编辑 knowledge_base_service.py
# 修改 uvicorn.run() 的 workers 参数
```

### 日志文件位置

- 知识库服务日志: `/root/logs/knowledge_base_http.log`
- 进程PID文件: `/root/pids/knowledge_base_http.pid`
- 系统日志: `/var/log/syslog` 或 `/var/log/messages`

### 性能监控

```bash
# 检查CPU和内存使用
top -p $(cat /root/pids/knowledge_base_http.pid)

# 检查磁盘使用
df -h

# 检查网络连接
netstat -tlnp | grep 8001
```

## 🔄 服务管理

### 启动/停止/重启服务

```bash
# 启动所有服务
./manage_linux_services.sh start

# 停止所有服务
./manage_linux_services.sh stop

# 重启所有服务
./manage_linux_services.sh restart

# 检查服务状态
./manage_linux_services.sh status
```

### 查看日志

```bash
# 查看知识库服务日志
./manage_linux_services.sh logs

# 实时监控日志
tail -f /root/logs/knowledge_base_http.log
```

### 测试功能

```bash
# 运行完整测试
./manage_linux_services.sh test

# 手动测试API
curl -X GET http://localhost:8001/stats
curl -X GET http://localhost:8001/docs
```

## 🛡️ 安全配置

### 防火墙设置

```bash
# Ubuntu UFW
ufw allow 8001
ufw enable

# CentOS firewalld
firewall-cmd --permanent --add-port=8001/tcp
firewall-cmd --reload

# 或使用iptables
iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
```

### 服务安全

1. **限制访问**: 只允许本地访问（localhost:8001）
2. **用户隔离**: 通过user_id进行数据隔离
3. **输入验证**: API层面的输入验证和清理
4. **日志记录**: 详细的操作日志记录

## 🚀 生产环境优化

### 性能优化

1. **使用进程管理器**: 推荐使用 supervisor 或 systemd
2. **负载均衡**: 如果需要，可以配置Nginx反向代理
3. **数据库优化**: 定期清理和优化向量数据库
4. **缓存策略**: 实现内存缓存减少API调用

### 监控告警

1. **服务监控**: 监控服务运行状态
2. **性能监控**: 监控CPU、内存、磁盘使用
3. **日志监控**: 监控错误日志和异常
4. **告警通知**: 配置服务异常告警

### 数据备份

```bash
# 备份向量数据库
cp -r data/ backup/data_$(date +%Y%m%d_%H%M%S)/

# 备份配置文件
cp configs/mcp_config.linux.json backup/config_$(date +%Y%m%d_%H%M%S).json
```

## 📞 支持联系

如果在部署过程中遇到问题，请：

1. 检查日志文件: `/root/logs/knowledge_base_http.log`
2. 运行诊断脚本: `./check_linux_env.sh`
3. 查看服务状态: `./manage_linux_services.sh status`
4. 提供错误信息和环境详情

---

**部署成功标志**: 
- ✅ 服务状态显示运行正常
- ✅ API文档可访问 (http://localhost:8001/docs)
- ✅ 测试功能返回成功结果
- ✅ MCP工具可以正常连接和存储记忆
