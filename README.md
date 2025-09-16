# 向量数据库知识检索服务

基于向量数据库的知识检索系统，支持语义相似度搜索和标签过滤。该服务使用 FastAPI 构建 RESTful API，通过向量embeddings实现高效的语义搜索。

## 功能特点

- 语义相似度搜索
- 标签过滤支持
- 向量embedding生成
- 持久化存储
- RESTful API接口
- 多维度文档元数据

## 技术栈

- FastAPI
- NumPy
- Embedding API (BGE模型)
- Uvicorn
- Python-dotenv

## 安装

1. 安装依赖：
```bash
pip install fastapi uvicorn numpy requests python-dotenv pydantic
```

2. 配置环境变量：
创建 `.env` 文件并设置：
```env
EMBEDDING_API_KEY=你的API密钥
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
KB_PORT=8000
```

## API 接口

### 搜索接口

```http
POST /search
```

请求体示例：
```json
{
    "query": "搜索查询文本",
    "tags": ["标签1", "标签2"],  // 可选
    "top_k": 5  // 可选，默认为5
}
```

响应示例：
```json
{
    "success": true,
    "results": [
        {
            "id": "doc1",
            "content": "文档内容",
            "tags": ["标签1", "标签2"],
            "metadata": {
                "source": "来源",
                "date": "2025-09-15"
            }
        }
    ]
}
```

## 数据存储

服务会自动在 `data` 目录下创建并维护两个文件：
- `vectors.npy`: 存储文档向量
- `documents.json`: 存储文档元数据

## 启动服务

```bash
python knowledge_base_service.py
```

服务将在配置的端口（默认8000）上启动。

## 核心类说明

### VectorDatabase

负责向量数据库的核心功能：
- 文档添加
- 向量检索
- 数据持久化
- 标签索引

### EmbeddingAPI

处理文本向量化：
- 调用外部Embedding API
- 向量生成和转换
- 错误处理

## 使用示例

1. 添加文档：
```python
document = Document(
    id="doc1",
    content="文档内容",
    tags=["标签1", "标签2"],
    metadata={"source": "示例"}
)
db.add_document(document)
```

2. 搜索文档：
```python
results = db.search(
    query="搜索查询",
    tags=["标签1"],
    top_k=5
)
```

## 待清理的无关文件

以下文件与知识库服务无关，可以删除：

1. ❌ `calculator.py` - 计算器服务
2. ❌ `mcp_config.json` - 旧的MCP配置文件
3. ❌ `mcp_pipe.py` - 旧的管道文件
4. ❌ 旧的 README.md（关于计算器的）

## 注意事项

1. 确保有足够的磁盘空间用于存储向量数据
2. 建议定期备份 `data` 目录
3. 正确配置 API 密钥和模型参数
4. 注意请求频率限制

## 性能优化

- 使用了向量标准化提高相似度计算效率
- 实现了基于标签的预过滤
- 支持批量处理文档
- 异步处理API请求
