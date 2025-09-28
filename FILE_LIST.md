# MCP 三工具项目文件清单

## 📁 项目结构总览

```
mcp_database/
├── 🚀 部署和启动脚本
├── 🧠 记忆库工具 (端口 8001)
├── 📚 向量数据库工具 (端口 8100)
├── 👤 角色人设服务 (Node.js MCP)
├── 🔧 配置和测试
└── 📝 文档和说明
```

## 🚀 部署和启动脚本

### 统一部署管理
- **`deploy_all_tools.py`** - 三工具统一部署管理脚本 ⭐ 主要入口
- **`start_all_tools.bat`** - Windows一键启动脚本
- **`start_all_tools.sh`** - Linux一键启动脚本
- **`manage_linux_services.sh`** - Linux服务管理（start/stop/status/test/logs）

### 旧版启动脚本 (已整合，保留转发)
- `mcp_memory_manager.py` - 记忆管理器 (保留兼容)
- `[DEPRECATED] start_linux_services.sh` - 已合并到 manage_linux_services.sh
- `[DEPRECATED] start_mcp_services.sh` - 已合并到 manage_linux_services.sh
- `[DEPRECATED] start_memory_system.bat` - 已合并到 deploy_all_tools.py

## 🧠 记忆库工具 (端口 8001)

### 核心文件
- **`embedding_memory_processor.py`** - 基于Embedding的记忆处理器 ⭐ 核心
- **`embedding_context_aggregator_mcp.py`** - 记忆上下文聚合MCP服务 ⭐ 核心
- **`test_embedding_memory.py`** - 统一测试脚本 ⭐ 核心

### 特点
- 🔢 纯Embedding技术，无需LLM
- 💰 成本低，响应快 (< 100ms)
- 🔒 用户数据完全隔离
- 🧠 智能记忆分类和重要性评分

## 📚 向量数据库工具 (端口 8100)

### 核心文件
- **`knowledge_base_service.py`** - 向量数据库HTTP服务 ⭐ 核心
- **`context_aggregator_mcp.py`** - 传统上下文聚合MCP服务
- **`memory_processor.py`** - 传统LLM记忆处理器
- **`knowledge_base_mcp.py`** - 知识库MCP接口（根目录版本为主）

### 文档处理工具
- **`document_importer.py`** - 文档批量导入器
- **`domain_processor.py`** - 领域文档处理器  
- `import_docs.py` - 通用文档导入工具
- `import_docs_legal.py` - 法律文档专用导入
- `[REMOVED] universal_import.py` - 冗余已移除（如需恢复请在 backups/_trash 查找）

### 特点
- 📄 支持大规模文档存储
- 🏷️ 支持标签和元数据过滤
- 🔍 高效向量相似度搜索
- 🌐 RESTful API接口

## 👤 角色人设服务 (Node.js MCP)

### 核心目录
```
mcp-persona-uozumi/
├── src/server.ts              - TypeScript MCP服务器源码
├── dist/server.js             - 编译后的服务器
├── personas_uozumi.md         - 仓桥卯月角色设定
├── personas_luoluo.md         - 络络角色设定
├── package.json               - Node.js项目配置
└── tsconfig.json              - TypeScript配置
```

### 特点
- 🎭 多角色人设支持
- 💬 智能角色对话生成
- 🔄 与记忆系统无缝集成
- 📡 标准MCP协议接口

## 🔧 配置和测试

### 配置文件
```
configs/
├── mcp_config.json            - 主要生产配置 ⭐
├── mcp_config.dev.json        - 开发环境配置
├── mcp_config.linux.json      - Linux服务器配置
└── README.md                  - 配置说明
```

### 测试工具
- **`test_embedding_memory.py`** - 统一测试套件 ⭐ 主要测试
- **`check_port_conflicts.py`** - 端口冲突检查工具
- **`check_mcp_tools.py`** - MCP工具状态检查
- `tests/**` - 其他测试与 examples/

### 数据库管理
- **`reset_database.py`** - 数据库重置工具
- `confirm_metadata_filter.py` - 元数据过滤确认

## 📝 文档和说明

### 主要文档
- **`README.md`** - 完整项目文档 ⭐ 主要文档
- **`QUICK_START.md`** - 快速开始指南 ⭐ 快速参考
- **`FILE_LIST.md`** - 本文件清单
- `[DEPRECATED] README_NEW.md` - 新版README (已合并，已归档至 backups/_trash)

### 技术文档
- **`port_mcp_check_report.md`** - 端口冲突检查报告（已更新统一端口策略）
- **`MCP_MEMORY_ARCHITECTURE.md`** - MCP记忆系统架构说明（已更新统一入口）

### 环境修复脚本
- `diagnose_startup.sh` - 启动诊断脚本（指向统一入口）
- `fix_linux_env.sh` - Linux环境修复脚本（指向统一入口）

## 📦 依赖配置

### Python依赖
- **`requirements.txt`** - Python包依赖清单
- **`.env`** - 环境变量配置 (需手动创建)

### Node.js依赖
- `mcp-persona-uozumi/package.json` - Node.js包依赖

## 🗂️ 数据目录

### 运行时目录 (自动创建)
```
data/                          - 向量数据存储
logs/                          - 服务运行日志
pids/                          - 进程ID文件
backups/                       - 数据备份
```

## 🎯 文件重要性分级

### ⭐ 核心必需文件 (必须存在)
1. `deploy_all_tools.py` - 统一部署管理
2. `embedding_memory_processor.py` - 记忆处理核心
3. `embedding_context_aggregator_mcp.py` - 记忆MCP服务
4. `knowledge_base_service.py` - 向量数据库服务
5. `test_embedding_memory.py` - 测试套件
6. `configs/mcp_config.json` - MCP配置
7. `README.md` - 项目文档

### 🔧 重要工具文件
- `context_aggregator_mcp.py` - 传统MCP服务
- `memory_processor.py` - 传统记忆处理
- `document_importer.py` - 文档导入器
- `check_port_conflicts.py` - 端口检查
- `reset_database.py` - 数据库管理

### 📚 扩展功能文件
- `mcp-persona-uozumi/` - 角色人设服务
- `domain_processor.py` - 领域处理器
- `import_docs.py` - 文档导入工具

### 📝 文档和辅助文件
- 各种`.md`文档文件
- 环境修复和诊断脚本
- 测试和验证工具

## 🚀 快速启动优先级

### 最小运行需求
1. `deploy_all_tools.py` + `start_all_tools.bat/.sh`
2. 记忆库工具: `embedding_memory_processor.py` + `embedding_context_aggregator_mcp.py`
3. 向量数据库工具: `knowledge_base_service.py`
4. 配置文件: `configs/mcp_config.json`
5. 环境配置: `.env` (手动创建)

### 完整功能需求
- 添加角色人设服务: `mcp-persona-uozumi/`
- 添加测试套件: `test_embedding_memory.py`
- 添加文档导入: `document_importer.py` + `import_docs.py`
- 添加管理工具: 各种检查和重置脚本

---

# 文件清单（精简版）

- 核心服务与工具
  - knowledge_base_service.py — HTTP 服务（8001/8100 双实例）
  - embedding_memory_processor.py — 记忆处理器
  - embedding_context_aggregator_mcp.py — 记忆聚合 MCP
  - context_aggregator_mcp.py — 传统聚合 MCP
  - knowledge_base_mcp.py — 知识库 MCP（根目录版本为主）
  - mcp_memory_manager.py — 统一管理脚本（兼容保留）
  - deploy_all_tools.py — 统一部署/检查/启动

- 启动脚本
  - start_all_tools.bat / start_all_tools.sh — 统一启动
  - manage_linux_services.sh — Linux 管理（start/stop/status/test/logs）
  - [DEPRECATED] start_memory_system.bat / start_linux_services.sh / start_mcp_services.sh — 已合并，保留转发

- 配置
  - configs/mcp_config.json — 主配置（已指向根目录 knowledge_base_mcp.py）
  - configs/** — 角色与域配置

- 测试与示例
  - test_embedding_memory.py — 统一测试脚本
  - tests/** — 其他测试（tag/search 等）与 examples/

- 导入工具
  - import_docs.py / import_docs_legal.py / document_importer.py
  - [REMOVED] universal_import.py — 冗余已移除（如需恢复请在 backups/_trash 查找）

- 历史与备份
  - backups/** — 历史备份与迁移文件
