# MCP Database - AI 编码指南

## 项目概述
这是一个用于 AI 对话的 MCP（Model Context Protocol）嵌入记忆系统。它使用纯嵌入技术与 BAAI/bge-large-zh-v1.5 模型和 FAISS 索引提供长期记忆和上下文增强。

## 架构要点
- **三套工具系统**：记忆库（端口 8001）、向量数据库（端口 8100）、角色人设服务（Node.js MCP）
- **MCP 服务器**：`knowledge_base_mcp.py`、`context_aggregator_mcp.py`、`embedding_context_aggregator_mcp.py` - 通过 stdio 通信
- **HTTP 服务**：`knowledge_base_service.py` 在端口 8001/8100 - REST API 用于向量存储/检索
- **数据流**：用户输入 → 嵌入分析 → FAISS 向量存储 → 语义搜索 → 上下文聚合 → 增强响应
- **隔离**：所有数据操作需要 `user_id` 参数，通过 `metadata.user_id` 实现多用户安全
- **配置**：使用 `configs/mcp_config.json` 进行环境特定设置

## 关键工作流
- **部署**：`python deploy_all_tools.py deploy` - 完整设置（检查/安装/配置/启动/测试）
- **启动服务**：`python deploy_all_tools.py start` - 启动所有 MCP 和 HTTP 服务
- **测试**：`python test_embedding_memory.py all` - 运行集成测试；使用 `env/api/storage/filter/integration` 进行特定测试
- **调试**：检查 `logs/` 目录中的日志；服务异步运行并进行健康检查

## 关键模式与约定
- **记忆分类**：使用类型 `personal/preference/event/knowledge/emotional`（见 `embedding_memory_processor.py`）
- **重要性评分**：基于关键词和内容类型评分 1-10（见 `calculate_importance` 方法）
- **模型**：所有数据结构使用 Pydantic（见 `knowledge_base_service.py`）
- **异步**：所有 I/O 操作使用 `asyncio` 和 `anyio` 异步处理
- **环境**：设置 `KB_SERVICE_URL` 为 HTTP 服务端点（例如 "http://localhost:8100"）
- **错误处理**：服务使用 try/except 和特定错误类型；检查 `logs/*.log` 了解详情
- **导入**：包内使用相对导入；跨包使用绝对导入

## 集成点
- **外部 API**：SiliconFlow 用于嵌入（需要在 `.env` 中提供 API 密钥）
- **向量数据库**：FAISS 与 numpy 数组在 `data/vectors.npy` 和 `data/documents.json`
- **VS Code**：在 `.vscode/settings.json` 中配置 MCP 服务器以集成 Copilot
- **跨服务**：MCP 服务器通过配置的 URL 调用 HTTP 服务
- **角色工具**：Karlach 集成 9 个 MCP 工具（等级、情绪桶、世界书、模板）

## 示例
```python
# 记忆分类（来自 embedding_memory_processor.py）
memory_type = classify_memory_type("用户喜欢科幻电影")  # 返回 "preference"

# 添加记忆并实现用户隔离
response = requests.post(f"{KB_SERVICE_URL}/add_memory",
    json={"user_id": user_id, "content": content, "memory_type": "event"})

# MCP 工具定义（来自 knowledge_base_mcp.py）
@mcp.tool()
async def search_similar(user_id: str, query: str, limit: int = 5):
    # 使用 FAISS 进行向量相似度搜索
```

参考：`README.md`、`MCP_MEMORY_ARCHITECTURE.md`、`configs/mcp_config.json`
