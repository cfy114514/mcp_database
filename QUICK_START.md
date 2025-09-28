# MCP 三工具统一部署使用说明

## 🚀 快速开始

### 一键启动 (推荐)

#### Windows用户
```cmd
start_all_tools.bat
```

#### Linux用户  
```bash
chmod +x start_all_tools.sh
./start_all_tools.sh
```

#### 手动一键部署
```bash
python deploy_all_tools.py deploy
```

## 📋 三套工具介绍

| 工具名称 | 端口 | 功能描述 | 主要文件 |
|---------|------|----------|----------|
| 🧠 **记忆库工具** | 8001 | 基于Embedding的纯语义记忆系统（HTTP服务实例） | `knowledge_base_service.py`（服务） + `embedding_memory_processor.py`（客户端） |
| 📚 **向量数据库工具** | 8100 | 通用文档向量存储和检索系统（HTTP服务实例） | `knowledge_base_service.py` | 
| 👤 **角色人设服务** | 3000 | TypeScript MCP角色人设服务 | `mcp-persona-uozumi/` |

## 🎯 核心命令

### 系统管理
```bash
python deploy_all_tools.py check      # 环境检查
python deploy_all_tools.py install    # 安装依赖
python deploy_all_tools.py config     # 配置系统
python deploy_all_tools.py start      # 启动所有服务
python deploy_all_tools.py stop       # 停止所有服务
python deploy_all_tools.py status     # 查看服务状态
python deploy_all_tools.py test       # 运行功能测试
python deploy_all_tools.py deploy     # 一键部署
```

### 测试验证
```bash
python test_embedding_memory.py all           # 完整测试
python test_embedding_memory.py env           # 环境测试
python test_embedding_memory.py api           # API测试
python test_embedding_memory.py storage       # 存储测试
python test_embedding_memory.py filter        # 过滤测试  
python test_embedding_memory.py integration   # 集成测试
```

## 🔧 必要配置

### 1. 环境变量 (.env)
```env
EMBEDDING_API_KEY=your_siliconflow_api_key
EMBEDDING_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
# KB_PORT 无需在 .env 中固定设置；部署脚本会分别以 8001/8100 启动服务实例
# 如需手动运行 knowledge_base_service.py，可临时设置：KB_PORT=8100（默认值）或 KB_PORT=8001
```

### 2. 依赖安装
```bash
# Python依赖 (必需)
pip install fastapi uvicorn numpy requests python-dotenv pydantic

# Node.js依赖 (可选，角色人设服务)
cd mcp-persona-uozumi
npm install && npm run build
```

## 🌐 服务访问

启动成功后访问：
- **向量数据库工具API**: http://localhost:8100/docs
- **记忆库工具API**: http://localhost:8001/docs
- 注：二者为同一实现的HTTP API，按端口区分用途；部署脚本会分别拉起两个实例
- **角色人设服务**: Node.js MCP服务 (无HTTP接口)

## ⚡ 使用示例

### 记忆库工具使用
```python
from embedding_memory_processor import EmbeddingMemoryProcessor

# 连接记忆库工具 (端口8001)
processor = EmbeddingMemoryProcessor(kb_service_url="http://localhost:8001")

# 处理对话记忆
result = processor.process_and_save_conversation(
    conversation="用户说：我喜欢看科幻电影",
    user_id="user123"
)

# 搜索记忆
memories = processor.search_memories(
    user_id="user123",
    query="电影偏好",
    top_k=5
)
```

### 向量数据库工具使用
```python
import requests

# 连接向量数据库工具 (端口8100)
base_url = "http://localhost:8100"

# 添加文档
response = requests.post(f"{base_url}/add", json={
    "id": "doc_001",
    "content": "人工智能技术发展...",
    "tags": ["AI", "技术"],
    "metadata": {"category": "technology"}
})

# 搜索文档
response = requests.post(f"{base_url}/search", json={
    "query": "人工智能",
    "top_k": 5
})
```

## 🚨 故障排除

### 常见问题
1. **端口被占用**: 检查 `netstat -ano | findstr :8001` 或 `netstat -ano | findstr :8100`
2. **API密钥未配置**: 检查 `.env` 文件
3. **服务启动失败**: 查看 `logs/` 目录下的日志文件
4. **依赖包缺失**: 运行 `python deploy_all_tools.py install`

### 完全重置
```bash
python deploy_all_tools.py stop           # 停止服务
python reset_database.py --no-backup      # 重置数据
python deploy_all_tools.py deploy         # 重新部署
```

## 📊 检查工具

### 端口冲突检查
```bash
python check_port_conflicts.py
```

### MCP工具状态检查  
```bash
python check_mcp_tools.py
```

---

**快速参考**: 如有问题，请运行 `python deploy_all_tools.py check` 进行系统诊断。
