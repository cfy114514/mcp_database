# MCP Database — AI 编码速用指南

目标：本仓库实现“纯嵌入长期记忆”。核心是一个 FastAPI 向量/记忆服务（FAISS + bge-large-zh）+ MCP 工具进行上下文聚合；严格按用户隔离与标签检索工作。

## 架构与数据流（Big Picture）
- 服务/端口（同代码，不同用途）：`knowledge_base_service.py`
  - 8001：记忆实例（供聚合器/生产对话）
  - 8100：向量库实例（测试/批量导入/验证）
- MCP（stdio）：`knowledge_base_mcp.py`、`context_aggregator_mcp.py`、`embedding_context_aggregator_mcp.py`
  - 聚合器固定从 `http://localhost:8001` 取数据；`build_prompt_with_context(include_persona_prompt=False)` 默认不拼接 persona
- 可选 Persona（Node）：`mcp-persona-*`；Karlach 物料在 `configs/personas/karlach/`
- 数据流：用户输入 → 嵌入 → FAISS 检索 → 语义聚合 → 增强回复

## 存储一致性与模型约定
- 数据在 `data/`：`documents.json` 与 `vectors.npy` 一一对应；顺序由 `document_ids` 维护
- Pydantic v2：写入用别名字段 `doc_id`，读取看到标准 `id`
- 用户隔离：写入/检索必须带 `metadata.user_id`；检索用 `metadata_filter: {"user_id": ...}`
- 标签：AND 用 `tags_all`（兼容历史 `tags`），OR 用 `tags_any`，可叠加 `priority_tags`
- 自修复：启动发现文档/向量不等，自动触发“全量重建向量”；请勿手改数据文件

## HTTP 契约与结果格式（KB）
- 主要接口：`POST /add`、`/batch_add`、`/search`、`/rebuild_index`、`/rebuild_all_vectors`、`/save`；`GET /health`、`/stats`
- `/search` 返回嵌套：`[{"document": <Document>, "score": <float>}]`
  - MCP `knowledge_base_mcp.py` 会扁平化为包含 `content/tags/metadata/id/score` 的字典（参考该文件中 results→formatted 处理）
- 示例检索（带用户隔离）：
  ```json
  {"query":"卡菈克 模板","top_k":5,"tags_all":["memory"],"metadata_filter":{"user_id":"dev-local"}}
  ```

## 嵌入/依赖与配置
- 模型：`BAAI/bge-large-zh-v1.5`（1024 维）；FAISS `IndexFlatL2`
- 外部 API：SiliconFlow；`.env` 需 `EMBEDDING_API_KEY`
- API URL 当前固定 `https://api.siliconflow.cn/v1/embeddings`（忽略 `.env` 的自定义 URL）

## 聚合器与 Persona 集成
- 聚合器统一解包 KB 搜索并输出扁平字段；`include_persona_prompt` 可开关拼接基础 persona
- Karlach 相关：`configs/personas/karlach/{persona.md, levels.v1.json, buckets.v1.json, freeplay_templates.v1.json, karlach_worldbook.zh.json}`
- 模板/人设检索示例：`query="karlach templates"` + `metadata_filter.doc_type="dialogue_template"`；`query="karlach persona"` + `doc_type="persona_description"`

## 开发者工作流（Windows PowerShell）
- 一键部署/启动：`python deploy_all_tools.py deploy|start` 或双击 `start_all_tools.bat`
- 健康与索引：访问 `/:8001|8100/health`、`/stats`；必要时 `POST /rebuild_index` 或 `/rebuild_all_vectors`
- 导入：`python import_docs.py --dir origin --pattern "*"`（脚本尾部会保存并重建索引）；法律文本用 `import_docs_legal.py`
- 测试/示例：`tools/test_8100_example.py`、`tools/kb_add_and_search.py`、`interactive_search.py`、`tools/test_agg_e2e.py`、`tools/seed_karlach_templates.py`
- 日志：`logs/*.log`；PowerShell JSON 转义易错，尽量用随仓脚本（requests）写入

## 代码与并发实践
- 保持“文档顺序 = 向量顺序”：同进程集中 add → `_save_data()` → `rebuild_index()`；批量优先 `/batch_add`
- 并发写入：当前无写锁，避免多进程/多实例同时写 `data/`；需并发请单写者+队列或加文件锁
- 端口角色固定：8001（聚合器/记忆）、8100（实验/导入）；如变更，需同步脚本/配置常量（含 `.vscode/mcp.json`）

有待澄清/补充：
- 如需自定义 SiliconFlow API URL，建议在哪个模块暴露配置；
- Karlach persona 是否始终以 KB 优先、Node 服务为回退？是否需要强制 pinned 策略的统一规范。
