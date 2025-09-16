# 向量数据库知识检索服务

这是一个基于向量数据库的智能文档检索系统，支持语义搜索和多维度标签过滤。系统使用 FastAPI 构建 RESTful API，并集成了 MCP 协议支持。通过向量 embeddings 实现高效的语义搜索，为文档检索提供智能化支持。

## 🚀 最新更新

### ✨ 领域解耦架构 (v2.0)
- **通用化设计**: 不再局限于法律文档，支持任意领域
- **配置驱动**: 通过JSON配置文件适配不同文档类型
- **向后兼容**: 保留所有法律文档处理功能
- **扩展性强**: 轻松添加新的文档领域

## 功能特点

- 🔍 智能语义搜索
- 🏷️ 多维度标签系统
- ⚡ 自动文档分割与标签提取
- 📦 批量导入支持
- 🔌 MCP协议集成
- 🌐 RESTful API支持
- 💾 持久化存储
- 🎯 自动标准化处理
- 🛠️ 数据管理工具
- 🌍 **多领域支持** (新增)
- ⚙️ **配置化定制** (新增)

## 技术栈

- FastAPI：Web框架
- NumPy：向量运算
- Embedding API (BGE模型)：文本向量化
- MCP Server：协议支持
- Python-dotenv：环境配置
- Pydantic：数据验证

## 目录结构

```
mcp_database/
├── data/                       # 向量数据库文件
│   ├── documents.json         # 文档数据
│   └── vectors.npy            # 向量数据
├── configs/                   # 领域配置文件 (新增)
│   ├── legal_domain.json     # 法律领域配置
│   └── general_domain.json   # 通用领域配置
├── origin/                    # 原始文档文件目录
├── knowledge_base_service.py  # 核心服务实现
├── knowledge_base_mcp.py      # MCP服务接口
├── domain_processor.py        # 领域处理器 (新增)
├── import_docs.py             # 通用导入工具 (重构)
├── import_docs_legal.py       # 法律专用导入工具 (兼容)
├── document_importer.py       # 文档导入器
├── test_queries.py           # 查询测试工具
├── reset_database.py         # 数据库重置工具
└── requirements.txt          # 依赖包列表
├── knowledge_base_mcp.py        # MCP服务接口
├── import_docs.py              # 批量导入工具
├── test_queries.py            # 查询测试工具
└── requirements.txt           # 依赖包列表

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

## 数据管理

### 1. 数据导入

将文本文件放入 `origin` 目录，然后运行：
```bash
python import_docs.py
```

### 2. 数据清除

以下方法可以清除数据库：

1. 直接删除数据：
```bash
rm -rf data/documents.json data/vectors.npy
```

2. 使用Python脚本清除：
```python
from pathlib import Path
import shutil

def clear_database():
    data_dir = Path("data")
    if data_dir.exists():
        shutil.rmtree(data_dir)
        data_dir.mkdir()
        print("数据库已清空")
```

3. 通过API重置：
```python
from knowledge_base_service import VectorDatabase

db = VectorDatabase()
db.reset()  # 清空所有数据
```

### 3. 数据备份

1. 手动备份：
```bash
cp -r data/ data_backup/
```

2. 自动备份（示例脚本）：
```python
import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backups/backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    shutil.copytree("data", backup_dir / "data", dirs_exist_ok=True)
    print(f"数据已备份到: {backup_dir}")
```

## 使用说明

### 1. 导入数据

将法律文本文件放入 `origin` 目录，然后运行：
```bash
python import_docs.py
```

文件要求：
- UTF-8 编码的文本文件
- 建议按主题或类别命名
- 支持任意 .txt 文件

### 2. 启动服务

MCP服务：
```bash
python knowledge_base_mcp.py
```

HTTP API服务：
```bash
python knowledge_base_service.py
```

### 3. 使用示例

搜索文档：
```python
# 简单搜索
result = db.search(query="故意杀人罪的量刑标准", top_k=5)

# 带标签过滤的搜索
result = db.search(
    query="盗窃罪",
    tags=["刑法", "财产犯罪", "有期徒刑"],
    top_k=5
)
```

## 核心组件

### VectorDatabase
- 文档管理
- 向量检索
- 标签索引
- 数据持久化

### MCP工具集
- search_documents：语义搜索
- add_document：添加文档
- get_stats：统计信息

### 导入工具
- 自动文档分割
- 智能标签提取
- 批量处理支持

## 性能优化

- 文档分割：100-800字符
- 保持法律条款完整性
- 向量标准化
- 多维度标签索引
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

## 🎯 快速开始

### 基础用法

1. **法律文档导入** (向后兼容)
```bash
python import_docs.py --domain legal
```

2. **通用文档导入**
```bash
python import_docs.py --domain general
```

3. **自定义领域**
```bash
python import_docs.py --config configs/my_domain.json
```

### 配置文件示例

```json
{
  "domain_config": {
    "name": "技术文档系统",
    "file_type_mapping": {
      "api": "API文档",
      "guide": "使用指南"
    },
    "keyword_mapping": {
      "函数": ["编程", "API"],
      "配置": ["设置", "配置"]
    },
    "base_tags": ["技术文档"]
  }
}
```
