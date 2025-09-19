# 记忆库 MCP 工具列表

## 📚 服务概览

记忆库提供以下 MCP 服务和工具，实现智能记忆存储、检索和上下文聚合功能。

---

## 🛠️ MCP 工具详细列表

### 1. **context_aggregator_mcp.py** - 上下文聚合服务

这是记忆库的核心 MCP 服务，提供以下 4 个工具：

#### 🎯 `build_prompt_with_context`
**功能**: 动态构建包含长期记忆和角色人设的系统提示
```json
{
  "tool": "build_prompt_with_context",
  "description": "为指定角色和用户构建增强的系统提示",
  "parameters": {
    "persona_name": "角色名称 (uozumi/luoluo)",
    "user_id": "用户唯一标识符",
    "user_query": "用户当前查询（可选）",
    "memory_top_k": "检索记忆数量（默认3）",
    "user_name": "用户名称（默认'用户'）",
    "char_name": "角色名称（可选）"
  },
  "returns": "包含记忆上下文的完整系统提示字符串"
}
```

**使用示例**:
```python
# 为用户构建络络角色的上下文提示
result = build_prompt_with_context(
    persona_name="luoluo",
    user_id="user001", 
    user_query="推荐咖啡店",
    memory_top_k=5
)
```

#### 💾 `store_conversation_memory`
**功能**: 从对话历史中提取并存储记忆
```json
{
  "tool": "store_conversation_memory", 
  "description": "智能提取对话中的重要信息并存储为长期记忆",
  "parameters": {
    "user_id": "用户唯一标识符",
    "conversation_history": "对话历史文本",
    "force_save": "是否强制保存（默认false）"
  },
  "returns": {
    "success": "操作是否成功",
    "message": "操作结果描述",
    "memory_saved": "是否已保存记忆",
    "memory_content": "提取的记忆内容",
    "importance": "重要性评分(1-10)",
    "memory_type": "记忆类型"
  }
}
```

**使用示例**:
```python
# 存储对话记忆
result = store_conversation_memory(
    user_id="user001",
    conversation_history="用户: 我喜欢喝拿铁\n络络: 好的，我记住了你喜欢拿铁咖啡",
    force_save=False
)
```

#### 🔍 `get_user_memories`
**功能**: 获取用户的历史记忆
```json
{
  "tool": "get_user_memories",
  "description": "检索用户的历史记忆信息",
  "parameters": {
    "user_id": "用户唯一标识符", 
    "query": "搜索查询（可选）",
    "top_k": "返回记忆数量（默认10）",
    "memory_type": "记忆类型过滤（可选）"
  },
  "returns": {
    "success": "操作是否成功",
    "user_id": "用户ID",
    "total_memories": "记忆总数",
    "memories": "记忆列表"
  }
}
```

**使用示例**:
```python
# 获取用户关于咖啡的记忆
result = get_user_memories(
    user_id="user001",
    query="咖啡",
    top_k=5,
    memory_type="preference"
)
```

#### ⚡ `get_service_status`
**功能**: 获取聚合服务的状态信息
```json
{
  "tool": "get_service_status",
  "description": "检查记忆服务的运行状态",
  "parameters": {},
  "returns": {
    "service": "服务名称",
    "status": "运行状态",
    "components": {
      "knowledge_base": "知识库连接状态",
      "memory_processor": "记忆处理器状态", 
      "persona_services": "角色服务列表"
    }
  }
}
```

---

## 🔧 底层支持服务

### 2. **knowledge_base_service.py** - 知识库 HTTP 服务

提供 REST API 接口，支持记忆存储和检索：

#### 📝 POST `/add` - 添加记忆
```json
{
  "endpoint": "/add",
  "method": "POST",
  "description": "向知识库添加新的记忆文档",
  "payload": {
    "content": "记忆内容",
    "tags": ["标签列表"],
    "metadata": {
      "user_id": "用户ID",
      "importance": "重要性评分",
      "memory_type": "记忆类型"
    }
  }
}
```

#### 🔍 POST `/search` - 搜索记忆
```json
{
  "endpoint": "/search", 
  "method": "POST",
  "description": "基于向量相似度和标签搜索记忆",
  "payload": {
    "query": "搜索查询",
    "tags": ["标签过滤"],
    "metadata_filter": {"user_id": "用户隔离"},
    "top_k": "返回数量"
  }
}
```

#### 📊 GET `/stats` - 服务统计
```json
{
  "endpoint": "/stats",
  "method": "GET", 
  "description": "获取知识库统计信息",
  "returns": {
    "document_count": "文档数量",
    "vector_count": "向量数量"
  }
}
```

### 3. **memory_processor.py** - 记忆处理核心

提供记忆提取和处理的核心功能：

#### 🧠 `MemoryProcessor` 类
- `extract_and_rate_memory()`: LLM 智能记忆提取
- `save_memory()`: 记忆保存到知识库
- `_call_llm()`: LLM API 调用
- `_parse_llm_response()`: 响应解析

---

## 🚀 部署配置

### MCP 配置示例

在 `mcp_config.json` 中配置记忆库服务：

```json
{
  "mcpServers": {
    "context-aggregator": {
      "command": "python",
      "args": ["context_aggregator_mcp.py"],
      "cwd": "/path/to/mcp_database"
    }
  }
}
```

### 环境变量配置

在 `.env` 文件中配置：

```properties
# 向量嵌入 API
EMBEDDING_API_KEY=your_embedding_key
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# 知识库服务
KB_PORT=8001
KB_HOST=localhost

# LLM API（可选，用于自动记忆提取）
LLM_API_KEY=your_llm_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo
```

---

## 📋 使用场景

### 1. **AI 对话增强**
```python
# 在每次对话前构建增强提示
enhanced_prompt = build_prompt_with_context(
    persona_name="luoluo",
    user_id="user001", 
    user_query=current_user_input
)
```

### 2. **记忆自动存储**
```python
# 对话结束后自动存储记忆
memory_result = store_conversation_memory(
    user_id="user001",
    conversation_history=full_conversation
)
```

### 3. **记忆回顾**
```python
# 查看用户历史记忆
memories = get_user_memories(
    user_id="user001",
    query="咖啡 喜好",
    top_k=10
)
```

### 4. **系统监控**
```python
# 检查服务状态
status = get_service_status()
```

---

## 🎯 核心特性

### ✅ **智能特性**
- 🧠 **语义理解**: 基于 1024 维向量的语义搜索
- 🏷️ **标签索引**: 快速精确的标签过滤
- 📊 **重要性评分**: LLM 智能评估记忆重要性
- 🔒 **用户隔离**: 基于 metadata 的多用户数据隔离

### ✅ **技术特性**
- 🚀 **高性能**: 向量化搜索 + 索引优化
- 🔄 **实时性**: 即时记忆存储和检索
- 🛡️ **安全性**: 用户数据完全隔离
- 📈 **可扩展**: 支持大规模用户和记忆存储

### ✅ **集成特性**
- 🔌 **MCP 标准**: 完全兼容 MCP 协议
- 🌐 **REST API**: HTTP 接口支持
- 🐍 **Python 生态**: 丰富的库支持
- ⚙️ **配置灵活**: 环境变量配置

---

## 📞 联系与支持

- **项目地址**: mcp_database
- **配置文件**: `.env`, `mcp_config.json`
- **日志级别**: 可通过 `LOG_LEVEL` 环境变量调整
- **调试模式**: 设置 `DEBUG=true` 启用详细日志

---

*📝 最后更新: 2025年9月19日*
