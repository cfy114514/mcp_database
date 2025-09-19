# MCP 记忆系统部署指南

## 📋 概述

本文档描述了如何部署和管理 MCP 记忆系统，该系统包含多个协同工作的服务，提供 AI 对话记忆存储和上下文聚合功能。

## 🏗️ 系统架构

```
MCP 记忆系统
├── HTTP 服务层
│   └── knowledge-base-http (端口 8000)
│       ├── 向量数据库接口
│       ├── 文档搜索和存储
│       └── 元数据过滤
├── MCP 服务层
│   ├── context-aggregator (MCP)
│   │   ├── 记忆提取和存储
│   │   ├── 上下文聚合
│   │   └── 用户记忆检索
│   └── persona-uozumi (MCP, 可选)
│       └── 人格化服务
└── 核心组件
    ├── memory_processor.py
    ├── 配置管理
    └── 部署脚本
```

## 🔧 部署前准备

### 1. 系统要求

- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.8+ 
- **Node.js**: 16+ (如果使用 persona 服务)
- **内存**: 最低 4GB，推荐 8GB+
- **磁盘**: 最低 1GB 可用空间

### 2. 依赖安装

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 如果使用 Node.js 服务
npm install
```

### 3. 环境变量配置

创建 `.env` 文件或设置系统环境变量：

```bash
# LLM API 配置
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.openai.com/v1

# 向量数据库配置
EMBEDDING_API_URL=https://api.your-embedding-service.com
EMBEDDING_API_KEY=your_embedding_key

# 可选：调试模式
DEBUG=true
LOG_LEVEL=INFO
```

## 🚀 快速启动

### 方法一：使用启动脚本（推荐）

**Windows:**
```cmd
# 双击运行或命令行执行
start_memory_system.bat
```

**Linux/macOS:**
```bash
# 创建 shell 脚本（如果需要）
python deploy_memory_system.py deploy
```

### 方法二：使用部署管理器

```bash
# 生产环境部署
python deploy_memory_system.py deploy

# 开发环境部署
python deploy_memory_system.py deploy --dev

# 仅启动服务
python deploy_memory_system.py start

# 查看状态
python deploy_memory_system.py status

# 健康检查
python deploy_memory_system.py health

# 停止所有服务
python deploy_memory_system.py stop
```

### 方法三：手动启动

```bash
# 1. 启动知识库 HTTP 服务
python knowledge_base_service.py

# 2. 启动上下文聚合 MCP 服务
python context_aggregator_mcp.py

# 3. （可选）启动其他 MCP 服务
```

## 📁 配置文件

### 生产配置 (`configs/mcp_config.json`)

```json
{
  "mcpServers": {
    "context-aggregator": {
      "command": "python",
      "args": ["context_aggregator_mcp.py"],
      "cwd": ".",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  },
  "httpServices": {
    "knowledge-base-http": {
      "command": "python",
      "args": ["knowledge_base_service.py"],
      "cwd": ".",
      "port": 8000,
      "healthCheck": {
        "url": "http://localhost:8000/health"
      }
    }
  },
  "globalConfig": {
    "timeout": 30,
    "retries": 3
  }
}
```

### 开发配置 (`configs/mcp_config.dev.json`)

包含额外的调试设置和详细日志。

## 🔍 服务验证

### 1. 自动健康检查

部署脚本会自动执行健康检查：

- ✅ HTTP 服务响应检查
- ✅ MCP 进程状态检查
- ✅ 依赖项验证

### 2. 手动验证

**知识库服务:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
```

**记忆处理器:**
```bash
python -c "from memory_processor import MemoryProcessor; print('✅ 记忆处理器正常')"
```

**上下文聚合器:**
检查进程是否运行并监听 stdio。

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口使用
   netstat -an | findstr :8000
   # 或使用其他端口
   set PORT=8001 && python knowledge_base_service.py
   ```

2. **Python 包缺失**
   ```bash
   pip install -r requirements.txt
   ```

3. **环境变量未设置**
   ```bash
   # 检查关键环境变量
   echo %LLM_API_KEY%
   ```

4. **权限问题**
   - 确保脚本有执行权限
   - 检查文件访问权限

### 日志查看

- **HTTP 服务日志**: 控制台输出
- **MCP 服务日志**: stderr 输出
- **部署日志**: deploy_memory_system.py 输出

### 调试模式

```bash
# 启用详细日志
python deploy_memory_system.py deploy --dev

# 单独测试组件
python memory_processor.py
python test_memory_integration.py
```

## 📊 监控和维护

### 系统状态检查

```bash
# 定期状态检查
python deploy_memory_system.py status

# 详细健康检查
python deploy_memory_system.py health
```

### 性能监控

- **内存使用**: 监控 Python 进程内存
- **响应时间**: 检查 HTTP 服务响应时间
- **错误率**: 监控日志中的错误信息

### 备份和恢复

- **配置备份**: 定期备份 `configs/` 目录
- **数据备份**: 备份向量数据库文件
- **日志归档**: 定期清理和归档日志文件

## 🔄 更新和升级

### 代码更新

```bash
# 1. 停止服务
python deploy_memory_system.py stop

# 2. 更新代码
git pull

# 3. 更新依赖
pip install -r requirements.txt

# 4. 重新部署
python deploy_memory_system.py deploy
```

### 配置迁移

在更新配置文件时，建议：

1. 备份现有配置
2. 比较配置变更
3. 测试新配置
4. 逐步迁移

## 🛡️ 安全考虑

### API 密钥管理

- 使用环境变量存储敏感信息
- 不要在代码中硬编码密钥
- 定期轮换 API 密钥

### 网络安全

- HTTP 服务默认绑定到 localhost
- 生产环境考虑使用 HTTPS
- 配置防火墙规则

### 访问控制

- 限制文件系统权限
- 考虑用户隔离
- 审计日志访问

## 📞 支持

### 问题报告

如遇到问题，请提供：

1. 错误信息和日志
2. 系统环境信息
3. 配置文件内容
4. 重现步骤

### 文档更新

本文档会随系统更新而更新，请关注最新版本。

---

**部署成功标志:**

- ✅ 所有服务状态检查通过
- ✅ HTTP 健康检查返回 200
- ✅ MCP 服务正常响应
- ✅ 记忆处理功能正常

部署完成后，记忆系统将为 AI 对话提供持久化记忆存储和智能上下文聚合功能。
