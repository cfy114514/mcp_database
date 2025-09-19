# 用户记忆存储位置详解

## 📍 存储架构概览

用户记忆在MCP记忆系统中采用**向量数据库**存储方式，具体分为以下几个层次：

## 🗂️ 具体存储位置

### 1. Windows 环境
```
c:\Users\Administrator\Documents\mcp_database\data\
├── vectors.npy          # 向量数据文件（1024维embedding）
├── documents.json       # 文档元数据文件
└── (自动生成的索引文件)
```

### 2. Linux 服务器环境  
```
/root/mcp_database/data/
├── vectors.npy          # 向量数据文件（1024维embedding）
├── documents.json       # 文档元数据文件
└── (自动生成的索引文件)
```

## 📊 数据文件详解

### vectors.npy
- **类型**: NumPy 数组文件
- **维度**: 1024维向量（BAAI/bge-large-zh-v1.5模型）
- **内容**: 用户记忆的语义向量表示
- **用途**: 支持语义相似性搜索

### documents.json
- **类型**: JSON 格式文件
- **内容**: 记忆文档的完整信息
- **结构**:
```json
{
  "id": "memory_unique_id",
  "content": "用户记忆内容",
  "metadata": {
    "user_id": "用户唯一标识",
    "memory_type": "personal/preference/event/knowledge",
    "importance": 7.5,
    "created_at": "2025-09-19T15:30:00Z",
    "tags": ["coffee", "morning", "habit"]
  },
  "tags": ["memory", "user_habit"]
}
```

## 🔍 用户隔离机制

### metadata 过滤
每个用户的记忆通过 `metadata.user_id` 字段进行隔离：
- 用户A: `"user_id": "user_001"`
- 用户B: `"user_id": "user_002"`

### 搜索时自动过滤
```python
search_params = {
    "query": "咖啡习惯",
    "metadata_filter": {"user_id": "user_001"}  # 只返回该用户的记忆
}
```

## 🔧 数据操作接口

### 通过知识库HTTP服务 (端口8000)
```bash
# 添加记忆
POST http://localhost:8000/add

# 搜索记忆
POST http://localhost:8000/search

# 获取统计
GET http://localhost:8000/stats
```

### 通过MCP工具
```python
# 存储对话记忆
store_conversation_memory(user_id, conversation_history)

# 获取用户记忆
get_user_memories(user_id, query, top_k)

# 构建包含记忆的提示
build_prompt_with_context(persona_name, user_id, user_query)
```

## 💾 数据持久化

### 自动保存机制
- 记忆添加时立即保存到文件
- 向量和文档同步更新
- 支持服务重启后数据恢复

### 备份建议
重要数据文件建议定期备份：
```bash
# 备份数据目录
cp -r /root/mcp_database/data /root/backup/data_$(date +%Y%m%d)

# 或者 Windows
xcopy c:\Users\Administrator\Documents\mcp_database\data c:\backup\data_%date% /E /I
```

## 📈 数据增长预估

### 每条记忆占用空间
- 向量: 1024 × 4字节 = 4KB
- 文档元数据: 约 1-2KB
- **总计**: 约 5-6KB/条记忆

### 存储容量规划
- 1万条记忆 ≈ 50-60MB
- 10万条记忆 ≈ 500-600MB
- 100万条记忆 ≈ 5-6GB

## 🔄 数据迁移

### 从旧系统迁移
如果需要从其他系统迁移用户记忆：

1. **格式转换脚本**:
```python
def migrate_memories(old_data, user_id):
    for memory in old_data:
        # 转换为标准格式
        formatted_memory = {
            "content": memory["text"],
            "metadata": {
                "user_id": user_id,
                "memory_type": "imported",
                "importance": 5.0,
                "created_at": memory.get("timestamp"),
            },
            "tags": ["memory", "imported"]
        }
        # 调用API添加
        add_memory(formatted_memory)
```

2. **批量导入工具**:
```bash
python3 migrate_user_data.py --input old_data.json --user_id user_001
```

## 🚨 注意事项

### 数据安全
- 用户记忆包含敏感信息，确保文件权限正确设置
- 定期备份，防止数据丢失
- 考虑加密存储敏感记忆内容

### 性能优化
- 大量数据时考虑使用专业向量数据库（如Milvus、Pinecone）
- 定期清理过期或低重要性记忆
- 优化向量检索算法

### 扩展性
- 当前方案适合中小规模应用（10万条记忆以内）
- 大规模应用建议迁移到分布式向量数据库
- 支持水平扩展和集群部署

## 📝 查看当前存储状态

运行以下命令查看当前记忆存储情况：

```bash
# 查看数据文件
ls -la /root/mcp_database/data/

# 检查记忆统计
curl http://localhost:8000/stats

# 查看特定用户记忆
python3 -c "
from context_aggregator_mcp import get_user_memories
result = get_user_memories('your_user_id', '', 10)
print(result)
"
```
