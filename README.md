# MCP Database — 项目总览与部署指南

本仓库包含多个子模块：角色 persona 的 MCP 接入点（Uozumi 与 Luoluo）、向量知识库（Knowledge Base）HTTP 服务与其 MCP 包装器、文档导入/分割/持久化工具以及若干运维与测试脚本。本 README 为统一首页，包含部署、启动、导入与测试步骤，以及关键脚本的使用说明。

目录概览（重要路径）

- mcp-persona-uozumi/
  - src/server.ts        — Uozumi MCP stdio 服务器（现已合并 Luoluo 工具）
  - dist/server.js       — 编译后入口（用于在面板中启动）
  - personas_uozumi.md   — Uozumi 人设
  - personas_safety.md   — 安全规则
  - data/uozumi_worldbook.zh.json — Uozumi 世界书
- mcp-persona-luoluo/
  - src/server.ts
  - dist/server.js
  - personas_luoluo.md
  - data/luoluo_worldbook.zh.json
- mcp-calculator/ 或 根目录
  - knowledge_base_service.py — FastAPI 知识库 HTTP 服务（/search）
  - vector_db.py             — MCP 工具包装（search_documents/add_document/get_stats）
  - import_tool.py / import_docs.py — 文档导入器
- 脚本与配置
  - deploy.sh
  - reset_database.py
  - add_test_data.py / test_search.py
  - studio.json (示例服务定义)
  - mcp_config.json (旧版/示例)
  - .env（环境变量）

先决条件

- Node.js + npm / pnpm（用于 persona 服务的构建与运行）。
- Python 3.8+（用于知识库与 MCP 包装器）。
- 安装依赖：见各模块下的 requirements_*.txt 与 package.json。
- 配置 EMBEDDING_API_KEY（向量 embedding 服务的 API key）。

配置与环境（建议）

在仓库根创建 `.env`：

EMBEDDING_API_KEY=你的_api_key
EMBEDDING_MODEL=BAAI/bge-m3
KB_PORT=8000

确保主机可访问 embedding 服务并允许 outbound HTTPS（如使用第三方 embedding API）。

模块部署与启动

1) 向量知识库 HTTP 服务（Knowledge Base）——（提供 /search REST API）

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
  - 会话开始时调用 get_*_system_prompt（user/char 参数），把返回内容写入会话的 system 消息。
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

安全与合规

- 所有 persona 的系统提示应合并安全指南（personas_safety.md）；在生成系统提示时由 get_*_system_prompt 将安全规范与人设合并。
- 向量检索注入前执行脱敏（redact_sensitive），禁止自动泄露受版权保护或 PII 的原文。

监控与日志

- 各服务应将 stdout/stderr 重定向到日志文件（示例见 studio.json 与 deploy.sh）。
- 所有检索调用应记录（query, returned_ids, scores, timestamp）以便审计与调优。

故障排查（快速）

- persona 未列出工具：确认 node dist/server.js 是否打印启动日志并处于运行状态；确认面板的 cwd 与 args 设置正确。
- search_documents 报错：检查 KB 服务是否可用（http://localhost:8000/search），并检查 EMBEDDING_API_KEY 是否有效。
- 导入失败或 embedding 超时：检查网络与 embedding API 速率限制，尝试增大学习重试间隔或分批导入。

示例快速启动顺序（推荐）

1) 在一台机器上：启动 HTTP 知识库
   python knowledge_base_service.py

2) 启动向量 MCP 包装器（连接到 step1）
   python vector_db.py

3) 启动 persona MCP（包含 Uozumi 与 Luoluo 工具）
   cd mcp-persona-uozumi
   node dist/server.js

4) 在 AI 客户端面板中配置单 stdio 服务，指向第3步的 node 进程，调用工具：
   - 会话开始：get_*_system_prompt { user: "阿漠", char: "络络" }
   - 运行时检索：模型静默调用 search_documents / summarize_search（如已实现）

附录：常用文件位置与说明

- .env — 环境变量（EMBEDDING_API_KEY 等）
- studio.json — supervisor/studio 服务定义示例（knowledge-base, vector-mcp）
- mcp_config.json — mcp_pipe 的简易 config 示例
- deploy.sh — 部署辅助脚本
- .gitignore — 忽略 node_modules/ 与 dist/ 产物

---
如需我把 README 的这些变更同步提交到 git（git add/commit），或把 persona 的合并构建（npm run build）并本地启动一次进行连通性测试，我可以继续为你执行这些步骤。
