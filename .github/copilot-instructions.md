# MCP Database - AI 编码指南

简要目标：本仓库实现面向对话系统的“纯嵌入长期记忆”。核心是一个 FastAPI 向量服务（FAISS + bge-large-zh），配合 MCP 工具聚合上下文。

## 架构总览（Big Picture）
- HTTP 向量/记忆服务：`knowledge_base_service.py` 在 8001/8100 端口运行（相同代码，不同用途）。
  - 端口 8001：记忆实例（被 aggregator 使用）
  - 端口 8100：向量库实例（用于测试/批量导入/验证）
- MCP 工具（stdio）：`knowledge_base_mcp.py`、`context_aggregator_mcp.py`、`embedding_context_aggregator_mcp.py`
  - 聚合器默认从 `http://localhost:8001` 取数据，支持 include_persona_prompt 开关（默认 False）
- Node 人设服务（可选）：`mcp-persona-*` 子目录
- 数据流：用户输入 → 嵌入 → FAISS 相似度检索 → 语义聚合 → 响应增强

## 数据与一致性（必须遵守）
- 存储在 `data/`：`documents.json`（有序列表） 与 `vectors.npy` 一一对应
  - 文档顺序由 `document_ids` 维护；服务启动时若发现数量不等，会自动触发“全量重建向量”自修复
  - 不要手动改写这两个文件；新增/修改请通过 API 或脚本并最终调用保存/重建
- Pydantic v2 模型：`Document` 使用别名字段 `doc_id` → `id`
  - 写入时传 `doc_id`；读取时会见到标准化后的 `id`
- 用户隔离：所有数据写入/检索均应带上 `metadata.user_id`，检索用 `metadata_filter: {"user_id": ...}`
- 标签约定：
  - AND 过滤用 `tags_all`（兼容历史 `tags` 字段）
  - OR 过滤用 `tags_any`，可叠加 `priority_tags` 做加权

## HTTP 接口契约（knowledge_base_service）
- POST `/add` 接收 `{doc_id, content, tags, metadata}`
- POST `/batch_add` 批量同上
- POST `/search` 返回形如 `[{"document": <Document>, "score": <float>}, ...]`
- POST `/rebuild_index`、POST `/rebuild_all_vectors`、POST `/save`
- GET `/health`、GET `/stats`（含 vectors/docs/index_ntotal/mismatch）

## 嵌入与依赖
- 模型：`BAAI/bge-large-zh-v1.5`（向量维度 1024），后端：FAISS `IndexFlatL2`
- 外部 API：SiliconFlow；需在 `.env` 配置 `EMBEDDING_API_KEY`
  - 当前实现固定使用 `https://api.siliconflow.cn/v1/embeddings`（`.env` 的 EMBEDDING_API_URL 未被读取）

## 开发者工作流与常用脚本
- 启动/部署（Windows PowerShell）：
  - 一键部署/启动：`python deploy_all_tools.py deploy|start` 或运行 `start_all_tools.bat`
  - 健康检查：访问 `/:8001|8100/health`、`/stats`，必要时 `POST /rebuild_index` 或 `/rebuild_all_vectors`
- 文档导入：
  - 通用导入：`python import_docs.py --dir origin --pattern "*"`（脚本末尾会自动保存并重建索引）
  - 法律文本：`python import_docs_legal.py --dir origin --pattern "*.txt"`
  - 断点续传与重置：`--reset` 清空 `import_progress.json`
- 快速验证：
  - `tools/test_8100_example.py`：对 8100 做 /add → /rebuild_index → /search（带 user_id 过滤）
  - `tools/kb_add_and_search.py`、`tools/seed_karlach_templates.py`：演示写入与标签检索
  - `interactive_search.py`：交互式本地检索
  - `tools/test_agg_e2e.py`：聚合器端到端（include_persona_prompt=False）

## 代码约定与实现细节
- 保持“文档顺序 = 向量顺序”：写入后使用 `_save_data()` 并 `rebuild_index()`；批量写入同理
- `/search` 结果为嵌套结构（document+score）；上层组件可自行“扁平化”字段
- 兼容历史字段：`SearchRequest.tags` → 若提供则等同于 `tags_all`
- 端口角色固定：8001（聚合器使用的记忆实例）、8100（实验/导入验证）。如变更，请同步相关脚本常量
- 避免 PowerShell JSON 转义问题；优先使用提供的 Python 脚本进行写入与测试

## 关键文件/目录一览
- 核心服务：`knowledge_base_service.py`
- 导入与分块：`document_importer.py`、`import_docs.py`、`import_docs_legal.py`、`origin/`
- 聚合与工具：`embedding_context_aggregator_mcp.py`、`tools/*.py`
- 配置：`.env`、`configs/*.json`
- 数据：`data/documents.json`、`data/vectors.npy`

## Persona 与聚合器集成
- 聚合器：`embedding_context_aggregator_mcp.py`
  - 检索来源固定 `http://localhost:8001`；统一解包 KB `/search` 的嵌套结果为扁平字段（content/tags/metadata/id/score）。
  - `build_prompt_with_context(include_persona_prompt=False)` 默认不拼接基础 persona 文本；按需开启。
- 人设服务：`mcp-persona-*`（Node）提供人设素材与世界书；当前聚合器中 persona 文本为占位实现，可替换为真实服务输出。
- 写入记忆：`embedding_memory_processor.save_memory_segment` 会生成稳定 `doc_id`（含 user_id 前缀），并写 `metadata.user_id` 以便检索隔离。

## 并发与批量导入（实践建议）
- 单进程导入：`DocumentImporter` 会多次调用 `db.add_document(save=False)`；导入流程末尾务必执行 `db._save_data(); db.rebuild_index()`（已在 `import_docs.py` 中处理）。
- 批量写入建议：尽量使用 `/batch_add` 或在同一进程内集中 add 后一次性保存重建，减少重算与索引抖动。
- 并发写入注意：当前未内置写锁；避免多进程/多实例同时写 `data/`。如需并发，采用单写者+队列或添加文件锁。
- 自修复：服务启动时如发现 vectors≠documents，会触发 `rebuild_all_vectors()` 自动对齐；离线也可运行 `tools/offline_rebuild_vectors.py`。

## Windows/PowerShell 常见问题
- JSON 转义：避免在 PowerShell 直接构造复杂 JSON 调 /add；优先使用仓库脚本（requests）。
- 端口占用：若 8001/8100 无法启动，先查 `check_port_conflicts.py` 或任务管理器结束旧进程。
- 编码与日志：确保 UTF-8 环境；日志在 `logs/*.log`。嵌入 API 错误（401/403/超时）会记录在日志里。
- 422 错误：多为缺少 `doc_id` 或字段名不符；注意 `doc_id` 别名与 `metadata.user_id` 必填实践。

## 环境变量与配置
- 必填：`.env` 的 `EMBEDDING_API_KEY`。模型默认 `BAAI/bge-large-zh-v1.5`。
- API URL：代码中固定使用 `https://api.siliconflow.cn/v1/embeddings`，当前忽略 `EMBEDDING_API_URL`；若需自定义，请修改 `EmbeddingAPI.api_url` 并提交。
- KB 端口：`.env` 中 `KB_PORT` 仅供脚本使用；实际服务端口取决于运行方式（部署脚本/命令行参数）。

示例（检索带用户隔离）：
```json
POST /search
{
  "query": "卡菈克 模板",
  "top_k": 5,
  "tags_all": ["memory"],
  "metadata_filter": {"user_id": "dev-local"}
}
```

如有不清楚或缺漏的部分（例如真实 persona 服务接入、并发写入策略细节），请提出以便进一步完善。
