# MCP Database — AI 记忆系统与角色人设平台

本项目是一个完整的 AI 记忆系统与角色人设平台，基于 MCP (Model Context Protocol) 架构构建。系统提供智能记忆存储、语义检索、上下文聚合和角色人设管理等核心功能，让 AI 拥有"记忆"用户信息的能力。

## 🧠 核心功能

### 📚 **智能记忆系统**
- **🔢 向量化存储**: 使用 BAAI/bge-large-zh-v1.5 模型生成 1024 维语义向量
- **🏷️ 标签化索引**: 多维度标签分类，支持快速精确过滤
- **🧠 LLM 记忆提取**: 自动从对话中提取重要信息并评估重要性
- **🔒 用户数据隔离**: 基于 metadata 的完全数据隔离，支持多用户
- **🎯 上下文聚合**: 智能构建包含记忆的增强提示

### 👥 **角色人设管理**
- **仓桥卯月 (Uozumi)**: 温柔细腻的角色人设
- **络络 (Luoluo)**: 友善活泼的 AI 助手
- **🛡️ 安全规范**: 内置安全指南和内容过滤
- **🌍 世界观设定**: 丰富的角色背景和世界书

### 🔄 **记忆生命周期**
```
👤 用户对话 → 🧠 记忆提取 → 🔢 向量化存储 → 🔍 智能检索 → 🎯 上下文聚合 → 💬 增强对话
```

## 📁 项目架构

### 🎯 **记忆系统核心**
```
memory_processor.py          — 记忆提取和处理核心
context_aggregator_mcp.py    — 上下文聚合 MCP 服务
knowledge_base_service.py    — 知识库 HTTP 服务 (FastAPI)
knowledge_base_mcp.py        — 知识库 MCP 包装器
```

### 👥 **角色人设服务**
```
mcp-persona-uozumi/
├── src/server.ts            — Uozumi & Luoluo MCP 服务器
├── dist/server.js           — 编译后入口
├── personas_uozumi.md       — Uozumi 人设
├── personas_luoluo.md       — Luoluo 人设
├── personas_safety.md       — 安全规则
└── data/
    ├── uozumi_worldbook.zh.json — Uozumi 世界书
    └── luoluo_worldbook.zh.json — Luoluo 世界书
```

### 🔧 **配置与部署**
```
configs/
├── mcp_config.json          — MCP 服务配置
├── mcp_config.dev.json      — 开发环境配置
deploy_memory_system.py      — 自动化部署脚本
start_memory_system.bat      — Windows 快速启动脚本
.env                         — 环境变量配置
```

### 📚 **文档与测试**
```
docs/
├── MEMORY_FLOW_GUIDE.md     — 记忆流程详解
├── MCP_TOOLS_LIST.md        — MCP 工具列表
├── DEPLOYMENT.md            — 部署指南
└── MCP_ARCHITECTURE.md      — 系统架构文档

tests/
├── test_integration.py      — 集成测试
├── demo_memory_system.py    — 端到端演示
└── test_*.py               — 各模块测试
```

## ⚙️ 环境配置

### 先决条件
- **Node.js 18+** + npm/pnpm (角色人设服务)
- **Python 3.8+** (记忆系统和知识库)
- **向量嵌入 API** (推荐硅基流动 SiliconFlow)

### 环境变量配置

在项目根目录创建 `.env` 文件：

```properties
# 向量嵌入 API 配置 (硅基流动)
EMBEDDING_API_KEY=your_embedding_api_key
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_API_URL=https://api.siliconflow.cn/v1/embeddings

# 知识库服务配置
KB_PORT=8001
KB_HOST=localhost

# LLM API 配置 (可选，用于自动记忆提取)
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo

# 记忆处理配置
MEMORY_IMPORTANCE_THRESHOLD=3.0
MAX_MEMORY_CONTEXT=5

# 调试配置
DEBUG=true
LOG_LEVEL=INFO
```

## 🚀 快速部署

### 方式一：自动化部署 (推荐)

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 构建角色人设服务
cd mcp-persona-uozumi
npm install
npm run build
cd ..

# 3. 一键部署所有服务
python deploy_memory_system.py deploy

# 4. Windows 用户可直接双击
start_memory_system.bat
```

### 方式二：手动部署

#### 步骤 1：启动知识库 HTTP 服务
```bash
python knowledge_base_service.py
# 服务将在 http://localhost:8001 启动
```

#### 步骤 2：启动记忆系统 MCP 服务
```bash
# 上下文聚合服务 (核心记忆功能)
python context_aggregator_mcp.py

# 知识库 MCP 包装器
python knowledge_base_mcp.py
```

#### 步骤 3：启动角色人设服务
```bash
cd mcp-persona-uozumi
node dist/server.js
```

### 服务管理命令
```bash
# 检查所有服务状态
python deploy_memory_system.py status

# 停止所有服务
python deploy_memory_system.py stop

# 重启服务
python deploy_memory_system.py restart

# 查看服务日志
python deploy_memory_system.py logs [service_name]

# 运行集成测试
python test_integration.py

# 查看记忆系统演示
python demo_memory_system.py
```

## 🔧 MCP 客户端配置

### 配置示例 (mcp_config.json)
```json
{
  "mcpServers": {
    "context-aggregator": {
      "command": "python",
      "args": ["context_aggregator_mcp.py"],
      "cwd": "/path/to/mcp_database",
      "description": "AI记忆系统核心服务"
    },
    "persona-uozumi": {
      "command": "node", 
      "args": ["./mcp-persona-uozumi/dist/server.js"],
      "cwd": "/path/to/mcp_database",
      "description": "角色人设服务"
    }
  }
}
```

### Claude Desktop 配置
在 `%APPDATA%\Claude\claude_desktop_config.json` 中添加：
```json
{
  "mcpServers": {
    "memory-system": {
      "command": "python",
      "args": ["C:/path/to/mcp_database/context_aggregator_mcp.py"]
    }
  }
}
```

- 说明：FastAPI 服务负责管理 Document、生成 embeddings（通过外部 Embedding API）并做向量检索，持久化在 data/ 下。
- 安装依赖：
  pip install -r requirements_kb.txt
- 配置：在仓库根或 mcp-calculator 目录下创建 `.env`（参见上文）。
- 启动：
  python knowledge_base_service.py
- 默认端口：KB_PORT（.env 中配置，缺省 8000）

测试服务：可运行 test_search.py 或 test_xingfa.py 来验证检索与导入功能。

2) 向量知识库的 MCP 包装（vector_mcp / vector_db.py）——（使知识库成为 MCP 工具）

- 说明：将 HTTP /search 接口封装为 MCP 工具（search_documents/add_document/get_stats），供其他 MCP persona 服务或模型以工具方式调用。
- 安装依赖：
  pip install -r requirements_mcp.txt
- 配置：确保环境变量 KB_HOST 指向 knowledge_base_service（如 http://localhost:8000）。
- 启动：
  python vector_db.py
- 示例调用（从 MCP 客户端或其他 MCP 服务）：
  - search_documents(query, tags=None, top_k=5)
  - add_document(doc_id, content, tags, metadata)
  - get_stats()

3) Persona MCP 服务（Uozumi 与 Luoluo）

- 设计：工具化设计（tools-only），每个角色提供：
  - get_*_persona
  - get_*_system_prompt
  - get_*_safety_guidelines
  - list_*_worldbook_entries
  - get_*_worldbook_entry
  - search_*_worldbook

- 两种部署方式可选：
  A) 单服务多角色（推荐）：把 Luoluo 合并到 Uozumi 服务中，面板只配置一次 node 启动 dist/server.js。
  B) 单角色单服务：分别为每个角色启动不同 node 进程（需面板支持多服务）。

- 构建与启动：
  cd mcp-persona-uozumi
  npm install 或 pnpm install
  npm run build 或 pnpm build
  node dist/server.js

- 面板示例（单接入点，cwd 设为仓库根）：
  {
    "type": "stdio",
    "command": "node",
    "args": ["./mcp-persona-uozumi/dist/server.js"],
    "cwd": "."
  }

- 使用建议：
  - 会话开始时调用 get_*_system_prompt（user/char 参数），把返回内容写入会话的 system 消消息。
  - 若需背景设定/人设片段，用 search_*_worldbook → get_*_worldbook_entry 获取并精炼后插入回复上下文（参见“无感检索”节）。

无感调用向量库（检索注入）

- 目标：模型在需要时自动、静默地调用 search_documents 来获取设定/事实支持，并将精炼摘要注入生成上下文，用户无感知调用过程。
- 推荐做法（服务端或模型侧任选其一）：
  1. 实现 summarize_search 工具：内部调用 db.search -> 重排 -> 返回精炼 summary 与命中文档 id 列表。
  2. 系统提示里要求：若问题涉及设定/事实/专有名词/时间线，先静默调用 summarize_search(query, tags, top_k)，并只将 summary 注入到上下文。
  3. 注入控制：每次注入控制在 200~800 tokens，且对敏感信息做 redact。
  4. 若用户明确要求显示原文/来源，再提供全文并记录日志与授权。

文档导入与批处理

- 导入工具：import_tool.py / import_docs.py / universal_import.py，支持 txt/json 文件导入、智能分块与标签提取。
- 使用示例：
  python import_tool.py  # 脚本默认导入 example 或指定文件
  或
  python import_docs.py --dir origin --domain legal
- 批量导入流程：
  1. 把待导入文件放到 origin/ 或指定目录。
  2. 运行导入脚本，脚本会分割、提取标签并调用 Embedding API 生成向量并持久化。
  3. 检查 data/documents.json 与 data/vectors.npy 确认插入成功。

常用运维脚本说明

- deploy.sh：将项目复制到部署目录并创建日志目录，示例用于 Linux 环境。
- reset_database.py：备份并清空 data/ 目录（带交互与备份选项）。
- add_test_data.py / test_search.py：用于向数据库添加测试文档并验证检索质量。

mcp_pipe 与多服务集成

- mcp_pipe.py 提供 stdio <-> WebSocket 或本地脚本的桥接逻辑，并支持从 mcp_config.json 或环境变量加载服务定义。
- 若你的管理面板不能同时启动多个 node/python 进程，建议：
  - 将多个角色合并为同一进程（已为 uozumi 合并 luoluo）；或
  - 使用 mcp_pipe 将本地脚本包装并通过单一代理连接管理面板。

studio.json 示例（用于本地 supervisor / studio）：
- 包含 knowledge-base 与 vector-mcp 两个服务定义，示例已在仓库 root 的 studio.json 文件中。

配置文件与依赖

- requirements_kb.txt：knowledge_base_service 所需依赖（fastapi, uvicorn, numpy, pydantic 等）。
- requirements_mcp.txt：MCP 包装器所需依赖（fastmcp, requests 等）。
- mcp-persona-uozumi/package.json 与 tsconfig.json：persona TypeScript 项目配置。

## 🔧 故障排查

### 常见问题解决

#### 服务连接问题
```bash
# 检查服务状态
python deploy_memory_system.py status

# 检查端口占用
netstat -an | findstr 8001  # Windows
lsof -i :8001              # Linux/Mac

# 重启知识库服务
python knowledge_base_service.py
```

#### 记忆系统问题
```bash
# 测试向量嵌入 API
python -c "
import requests
headers = {'Authorization': 'Bearer your_key'}
response = requests.post('https://api.siliconflow.cn/v1/embeddings', 
    headers=headers, json={'model': 'BAAI/bge-large-zh-v1.5', 'input': ['测试']})
print(response.status_code, response.json())
"

# 运行渐进式集成测试
python integration_guide.py

# 检查记忆存储
python -c "
import requests
response = requests.get('http://localhost:8001/stats')
print('知识库状态:', response.json())
"
```

#### MCP 工具问题
```bash
# 验证 MCP 服务
python context_aggregator_mcp.py --test

# 检查角色人设服务
cd mcp-persona-uozumi
node dist/server.js --test
```

### 日志分析
```bash
# 查看服务日志
python deploy_memory_system.py logs

# 查看特定服务日志
python deploy_memory_system.py logs knowledge-base

# 启用调试模式
export DEBUG=true  # Linux/Mac
set DEBUG=true     # Windows
```

## 📚 技术架构

### 🏗️ 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  MCP 客户端     │───→│  上下文聚合服务  │───→│  知识库服务     │
│  (Claude等)     │    │ context_aggregator│    │ knowledge_base  │
└─────────────────┘    └─────────┬───────┘    └─────────────────┘
                                 ↓                      ↓
                       ┌─────────────────┐    ┌─────────────────┐
                       │  角色人设服务   │    │  向量嵌入服务   │
                       │  persona-uozumi │    │  SiliconFlow    │
                       └─────────────────┘    └─────────────────┘
```

### 🔄 数据流
1. **用户输入** → MCP 客户端
2. **上下文构建** → 记忆检索 + 角色人设
3. **AI 响应** → 基于增强提示的个性化回复
4. **记忆存储** → 自动提取重要信息并向量化存储

### 📊 技术栈
- **后端**: Python FastAPI + Node.js TypeScript
- **向量数据库**: 自研向量存储 + 余弦相似度搜索
- **嵌入模型**: BAAI/bge-large-zh-v1.5 (1024维)
- **通信协议**: MCP (Model Context Protocol)
- **部署**: 多服务容器化部署

## 📖 相关文档

- **[记忆流程详解](docs/MEMORY_FLOW_GUIDE.md)** - 详细的记忆处理流程
- **[MCP 工具列表](docs/MCP_TOOLS_LIST.md)** - 所有可用工具的完整说明
- **[部署指南](docs/DEPLOYMENT.md)** - 生产环境部署指南
- **[系统架构](docs/MCP_ARCHITECTURE.md)** - 详细的架构设计文档

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

🎉 **恭喜！你现在拥有了一个完整的 AI 记忆系统！**

让 AI 拥有"记忆"用户信息的能力，打造更加个性化和连续的对话体验。

## 🧠 记忆系统使用指南

### 📋 核心 MCP 工具

| 工具名 | 功能 | 用途 |
|--------|------|------|
| `build_prompt_with_context` | 🎯 构建增强系统提示 | AI对话增强，加载用户记忆 |
| `store_conversation_memory` | 💾 存储对话记忆 | 自动提取重要信息并存储 |
| `get_user_memories` | 🔍 检索用户记忆 | 查询和分析用户历史记忆 |
| `get_service_status` | ⚡ 服务状态监控 | 检查记忆系统运行状态 |

### 📝 使用示例

#### 1. AI 对话增强
```python
# 为用户构建包含记忆的增强提示
enhanced_prompt = build_prompt_with_context(
    persona_name="luoluo",  # 选择角色：luoluo 或 uozumi
    user_id="user001",      # 用户唯一标识
    user_query="今天想喝什么咖啡？"  # 当前查询（可选）
)
```

#### 2. 记忆自动存储
```python
# 对话结束后自动提取并存储重要信息
conversation = """
用户: 我最近爱上了手冲咖啡
络络: 听起来很有趣！你喜欢什么豆子？
用户: 埃塞俄比亚的耶加雪菲，酸度适中
"""

result = store_conversation_memory(
    user_id="user001",
    conversation_history=conversation,
    force_save=False  # 是否强制保存低重要性记忆
)
```

#### 3. 记忆查询分析
```python
# 获取用户的咖啡相关记忆
memories = get_user_memories(
    user_id="user001",
    query="咖啡 喜好 口味",
    top_k=5,
    memory_type="preference"  # 可选：preference/event/knowledge/emotional
)
```

### 🔄 记忆处理流程

```
👤 用户对话 → 🧠 LLM 分析 → 📊 重要性评分 → 🔢 向量化存储 
                  ↓
🏷️ 标签索引 → 🔍 语义检索 → 🎯 上下文聚合 → 💬 增强对话
```

### 📊 记忆类型分类

- **🆔 身份信息** (`identity`): 姓名、职业、基本信息
- **❤️ 偏好习惯** (`preference`): 喜好、习惯、口味偏好
- **📚 知识技能** (`knowledge`): 学习内容、专业技能
- **🏠 生活信息** (`lifestyle`): 居住地、日程安排
- **😊 情感状态** (`emotional`): 心情、情感表达

### 🎯 技术特性

- **🔢 语义向量**: 1024维向量 (BAAI/bge-large-zh-v1.5)
- **🏷️ 标签索引**: 多维度分类和快速过滤
- **🔒 用户隔离**: 基于 metadata 的数据隔离
- **⚡ 实时性**: 毫秒级检索响应
- **🧠 智能评分**: LLM 自动评估记忆重要性
