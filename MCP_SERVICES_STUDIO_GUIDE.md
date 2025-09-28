# MCP服务 Studio 启动配置指南

本文档详细说明了 MCP 记忆系统中所有服务的 Studio 启动配置方式，包括不同环境（Windows、Linux）和配置文件的完整设置。

## 📋 服务概览

MCP 记忆系统包含以下核心服务：

### 🔧 **MCP 服务**
1. **角色人设服务** (`node`) - 支持 Karlach、Uozumi、Luoluo 角色
2. **知识库 MCP 服务** (`KnowledgeBase`) - 向量文档搜索和存储
3. **上下文聚合器** (`context-aggregator`) - 传统上下文聚合
4. **Embedding 上下文聚合器** (`embedding-context-aggregator`) - 纯 Embedding 记忆聚合

### 🌐 **HTTP 服务**
1. **记忆库 HTTP 服务** (`embedding-memory-http`) - 端口 8001
2. **知识库 HTTP 服务** (`knowledge-base-http`) - 端口 8100

---

## 🚀 Windows 环境配置

### 📄 **主配置文件** (`configs/mcp_config.json`)

```json
{
  "mcpServers": {
    "node": {
      "command": "node",
      "args": ["./mcp-persona-uozumi/dist/server.js"]
    },
    "KnowledgeBase": {
      "command": "python",
      "args": ["knowledge_base_mcp.py"]
    },
    "context-aggregator": {
      "command": "python",
      "args": ["context_aggregator_mcp.py"]
    },
    "embedding-context-aggregator": {
      "command": "python",
      "args": ["embedding_context_aggregator_mcp.py"]
    }
  },
  "httpServices": {
    "embedding-memory-http": {
      "command": "python",
      "args": ["knowledge_base_service.py"],
      "cwd": "c:/Users/Administrator/Documents/mcp_database",
      "env": {
        "PYTHONPATH": "c:/Users/Administrator/Documents/mcp_database",
        "KB_PORT": "8001"
      },
      "description": "记忆库 HTTP 服务，提供嵌入式记忆存储 REST API",
      "port": 8001,
      "healthCheck": {
        "url": "http://localhost:8001/docs",
        "interval": 30000,
        "timeout": 5000
      },
      "restart": true,
      "restartDelay": 5000
    },
    "knowledge-base-http": {
      "command": "python",
      "args": ["knowledge_base_service.py"],
      "cwd": "c:/Users/Administrator/Documents/mcp_database",
      "env": {
        "PYTHONPATH": "c:/Users/Administrator/Documents/mcp_database",
        "KB_PORT": "8100"
      },
      "description": "知识库 HTTP 服务，提供向量数据库 REST API",
      "port": 8100,
      "healthCheck": {
        "url": "http://localhost:8100/docs",
        "interval": 30000,
        "timeout": 5000
      },
      "restart": true,
      "restartDelay": 5000
    }
  }
}
```

### 🔧 **开发环境配置** (`configs/mcp_config.dev.json`)

```json
{
  "mcpServers": {
    "persona-uozumi": {
      "command": "node",
      "args": ["./mcp-persona-uozumi/dist/server.js"]
    },
    "knowledge-base": {
      "command": "python",
      "args": ["knowledge_base_mcp.py"]
    },
    "context-aggregator": {
      "command": "python",
      "args": ["context_aggregator_mcp.py"]
    }
  },
  "globalConfig": {
    "logLevel": "debug",
    "timeout": 60000,
    "retryAttempts": 1,
    "maxConcurrentConnections": 5
  },
  "development": {
    "hotReload": true,
    "debugMode": true,
    "verboseLogging": true,
    "testDataEnabled": true
  }
}
```

---

## 🐧 Linux 服务器配置

### 📄 **Linux 配置文件** (`configs/mcp_config.linux.json`)

```json
{
  "mcpServers": {
    "persona-uozumi": {
      "command": "node",
      "args": ["./mcp-persona-uozumi/dist/server.js"]
    },
    "knowledge-base": {
      "command": "python3",
      "args": ["knowledge_base_mcp.py"]
    },
    "context-aggregator": {
      "command": "python3",
      "args": ["embedding_context_aggregator_mcp.py"]
    }
  },
  "httpServices": {
    "knowledge-base-http": {
      "command": "python3",
      "args": ["knowledge_base_service.py"],
      "cwd": "/root/mcp_database",
      "env": {
        "PYTHONPATH": "/root/mcp_database",
        "KB_PORT": "8100"
      },
      "description": "知识库 HTTP 服务，提供向量数据库 REST API",
      "port": 8100,
      "healthCheck": {
        "url": "http://localhost:8100/docs",
        "interval": 30000,
        "timeout": 5000
      },
      "restart": true,
      "restartDelay": 5000
    },
    "embedding-memory-http": {
      "command": "python3",
      "args": ["knowledge_base_service.py"],
      "cwd": "/root/mcp_database",
      "env": {
        "PYTHONPATH": "/root/mcp_database",
        "KB_PORT": "8001"
      },
      "description": "记忆库 HTTP 服务，提供嵌入式记忆存储 REST API",
      "port": 8001,
      "healthCheck": {
        "url": "http://localhost:8001/docs",
        "interval": 30000,
        "timeout": 5000
      },
      "restart": true,
      "restartDelay": 5000
    }
  },
  "globalConfig": {
    "logLevel": "info",
    "timeout": 30000,
    "retryAttempts": 3,
    "maxConcurrentConnections": 10,
    "enableHealthChecks": true,
    "gracefulShutdownTimeout": 10000
  }
}
```

---

## 🎯 各服务详细说明

### 1. **角色人设服务** (`node` / `persona-uozumi`)

**功能**: 提供 Karlach、Uozumi、Luoluo 角色的人设和对话功能

**启动配置**:
```json
{
  "command": "node",
  "args": ["./mcp-persona-uozumi/dist/server.js"]
}
```

**可用工具**:
- `get_karlach_persona` - 获取 Karlach 基本信息
- `get_karlach_system_prompt` - 获取系统提示词
- `get_karlach_levels` - 获取26级等级系统
- `get_karlach_buckets` - 获取5种情绪状态
- `get_uozumi_system_prompt` - 获取 Uozumi 角色提示
- `get_luoluo_system_prompt` - 获取 Luoluo 角色提示

### 2. **知识库 MCP 服务** (`KnowledgeBase` / `knowledge-base`)

**功能**: 提供向量文档的搜索和存储功能

**启动配置**:
```json
{
  "command": "python",
  "args": ["knowledge_base_mcp.py"]
}
```

### 3. **上下文聚合器** (`context-aggregator`)

**功能**: 整合角色人设和知识库信息，提供上下文聚合

**启动配置**:
```json
{
  "command": "python",
  "args": ["context_aggregator_mcp.py"]
}
```

**依赖**: `node`, `KnowledgeBase`

### 4. **Embedding 上下文聚合器** (`embedding-context-aggregator`)

**功能**: 基于纯 Embedding 的记忆上下文聚合

**启动配置**:
```json
{
  "command": "python",
  "args": ["embedding_context_aggregator_mcp.py"]
}
```

**依赖**: `node`, `embedding-memory-http`

### 5. **记忆库 HTTP 服务** (`embedding-memory-http`)

**功能**: 提供嵌入式记忆存储的 REST API

**端口**: 8001

**启动配置**:
```json
{
  "command": "python",
  "args": ["knowledge_base_service.py"]
}
```

### 6. **知识库 HTTP 服务** (`knowledge-base-http`)

**功能**: 提供向量数据库的 REST API

**端口**: 8100

**启动配置**:
```json
{
  "command": "python",
  "args": ["knowledge_base_service.py"]
}
```

---

## 🔄 服务依赖关系

```
embedding-memory-http (8001)
    ↓
embedding-context-aggregator
    ↓
node (角色人设)
    ↓
context-aggregator
    ↓
KnowledgeBase
    ↓
knowledge-base-http (8100)
```

**启动顺序建议**:
1. HTTP 服务（embedding-memory-http, knowledge-base-http）
2. 角色人设服务（node）
3. MCP 服务（KnowledgeBase, context-aggregator, embedding-context-aggregator）

---

## ⚙️ Studio 配置使用方法

### 1. **选择配置文件**

根据你的环境选择对应的配置文件：

- **Windows 生产环境**: `configs/mcp_config.json`
- **Windows 开发环境**: `configs/mcp_config.dev.json`
- **Linux 服务器**: `configs/mcp_config.linux.json`

### 2. **在 Studio 中配置**

将选中的配置文件内容复制到 Studio 的 MCP 配置中。

### 3. **启动服务**

确保所有依赖的 HTTP 服务已启动：
```bash
# Windows
python deploy_all_tools.py start

# Linux
./manage_linux_services.sh start
```

### 4. **验证配置**

运行测试验证所有服务正常工作：
```bash
python deploy_all_tools.py test
```

---

## 🔧 故障排除

### 服务启动失败
- 检查 HTTP 服务是否已启动
- 验证端口是否被占用
- 查看日志文件：`logs/*.log`

### 连接超时
- 检查 `KB_SERVICE_URL` 配置是否正确
- 验证 HTTP 服务健康检查：`curl http://localhost:8001/docs`

### 权限问题
- Linux 环境下确保脚本有执行权限：`chmod +x *.sh`
- 检查文件路径是否正确

---

## 📚 相关文档

- [README.md](README.md) - 完整项目文档
- [MCP_MEMORY_ARCHITECTURE.md](MCP_MEMORY_ARCHITECTURE.md) - 系统架构说明
- [configs/](configs/) - 所有配置文件目录

---

## 🌐 HTTP 实现方式

对于远程 MCP 服务，可以使用 HTTP URL 直接连接，无需本地启动：

```json
{
  "mcpServers": {
    "http-server": {
      "url": "https://example.com/mcp"
    }
  }
}
```

这种方式适用于连接已部署的远程 MCP 服务，无需管理本地进程。

---

## 🔗 远程 MCP 服务配置示例

如果您的 MCP 服务部署在远程服务器上，可以使用以下格式直接通过 URL 连接：

### 本地服务器示例
```json
{
  "mcpServers": {
    "local-server": {
      "command": "npx",
      "args": ["-y", "@example/mcp-server"]
    }
  }
}
```

### HTTP 服务器示例
```json
{
  "mcpServers": {
    "http-server": {
      "url": "https://example.com/mcp"
    }
  }
}
```

这些配置可以直接复制到 Studio 的 MCP 设置中，无需额外的本地进程管理。

---

*最后更新: 2025年9月28日*