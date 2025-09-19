# MCP 服务架构文档

## 项目概览
本项目基于 Model Context Protocol (MCP) 构建了多个独立服务，提供 AI 角色人设管理、向量化知识库和文档处理能力。

## 服务架构图
```
mcp_database/
├── 🎭 角色人设服务 (Persona Services)
│   ├── mcp-persona-uozumi/     # Uozumi 角色 MCP 服务
│   └── mcp-persona-luoluo/     # Luoluo 角色 MCP 服务
├── 🗄️ 向量知识库服务 (Knowledge Base)
│   ├── knowledge_base_service.py   # HTTP API 服务
│   ├── knowledge_base_mcp.py       # MCP 包装器
│   └── mcp-calculator/             # 计算器与测试工具
├── 📁 文档处理工具 (Document Processing)
│   ├── import_docs.py              # 通用文档导入
│   ├── domain_processor.py         # 领域处理器
│   └── configs/                    # 领域配置文件
└── 🔧 运维工具 (DevOps Tools)
    ├── scripts/                    # 自动化脚本
    └── deploy.sh                   # 部署脚本
```

## 1. 角色人设服务 (Persona Services)

### 1.1 mcp-persona-uozumi
**路径**: `mcp-persona-uozumi/`
**类型**: Node.js TypeScript MCP stdio 服务
**状态**: ✅ 生产就绪（已合并 Luoluo 工具）

#### 服务信息
- **进程**: `node mcp-persona-uozumi/dist/server.js`
- **协议**: MCP stdio
- **能力**: `{ tools: {} }`

#### 提供的工具
```typescript
// Uozumi 工具
- get_uozumi_persona          // 获取 Uozumi 人设 Markdown
- get_uozumi_system_prompt    // 生成系统提示（含安全规则）
- get_safety_guidelines       // 获取安全指南
- list_worldbook_entries      // 列出世界书条目
- get_worldbook_entry(id)     // 获取指定世界书条目
- search_worldbook(query)     // 搜索世界书

// Luoluo 工具（已合并）
- get_luoluo_persona          // 获取 Luoluo 人设 Markdown
- get_luoluo_system_prompt    // 生成 Luoluo 系统提示
- get_luoluo_safety_guidelines // 获取 Luoluo 安全指南
- list_luoluo_worldbook_entries
- get_luoluo_worldbook_entry(id)
- search_luoluo_worldbook(query)
```

#### 数据文件
```
mcp-persona-uozumi/
├── personas_uozumi.md              # Uozumi 人设
├── personas_safety.md              # 通用安全规则
├── data/uozumi_worldbook.zh.json   # Uozumi 世界书
├── data/worldbook.schema.json      # 世界书 JSON Schema
└── startup_prompt_uozumi.md        # 启动系统提示模板
```

#### 配置示例
```json
{
  "servers": {
    "uozumi-persona": {
      "command": "node",
      "args": ["./mcp-persona-uozumi/dist/server.js"],
      "cwd": "/path/to/mcp_database"
    }
  }
}
```

### 1.2 mcp-persona-luoluo
**路径**: `mcp-persona-luoluo/`
**类型**: Node.js TypeScript MCP stdio 服务
**状态**: ⚠️ 独立服务（已合并进 uozumi，但保留独立版本）

#### 服务信息
- **进程**: `node mcp-persona-luoluo/dist/server.js`
- **协议**: MCP stdio
- **能力**: `{ tools: {} }`

#### 提供的工具
```typescript
- get_luoluo_persona          // 获取 Luoluo 人设
- get_luoluo_system_prompt    // 生成系统提示
- get_luoluo_safety_guidelines // 安全指南
- list_luoluo_worldbook_entries
- get_luoluo_worldbook_entry(id)
- search_luoluo_worldbook(query)
```

#### 数据文件
```
mcp-persona-luoluo/
├── personas_luoluo.md              # Luoluo 人设
├── data/luoluo_worldbook.zh.json   # Luoluo 世界书
└── startup_prompt_luoluo.md        # 启动系统提示模板
```

## 2. 向量知识库服务 (Knowledge Base)

### 2.1 knowledge_base_service.py
**路径**: `knowledge_base_service.py`
**类型**: FastAPI HTTP 服务
**状态**: ✅ 生产就绪

#### 服务信息
- **进程**: `python knowledge_base_service.py`
- **端口**: 8000 (可配置 KB_PORT)
- **协议**: HTTP REST API

#### API 端点
```python
POST /search              # 搜索文档
  - query: str            # 搜索查询
  - tags: List[str]       # 标签过滤
  - top_k: int           # 返回数量

POST /add                 # 添加文档
  - doc_id: str          # 文档ID
  - content: str         # 文档内容
  - tags: List[str]      # 标签
  - metadata: Dict       # 元数据

GET /stats               # 获取统计信息
```

#### 核心组件
```python
class VectorDatabase:     # 向量数据库核心
class EmbeddingAPI:       # 向量化API接口
class Document:           # 文档数据模型
class SearchRequest:      # 搜索请求模型
```

### 2.2 knowledge_base_mcp.py
**路径**: `knowledge_base_mcp.py`
**类型**: FastMCP Python MCP stdio 服务
**状态**: ✅ 生产就绪

#### 服务信息
- **进程**: `python knowledge_base_mcp.py`
- **协议**: MCP stdio
- **依赖**: knowledge_base_service.VectorDatabase

#### 提供的工具
```python
@mcp.tool()
def search_documents(query, tags, top_k):     # 搜索文档
def add_document(doc_id, content, tags):      # 添加文档
def get_stats():                              # 获取统计信息
```

### 2.3 mcp-calculator (测试模块)
**路径**: `mcp-calculator/`
**类型**: Python 脚本集合
**状态**: 🧪 开发测试用

#### 组件
```
mcp-calculator/
├── calculator.py           # 基础计算器 MCP 服务
├── mcp_pipe.py            # MCP stdio <-> WebSocket 代理
├── test_*.py              # 各种测试脚本
├── import_*.py            # 导入工具脚本
└── example_docs/          # 示例文档
```

## 3. 文档处理工具 (Document Processing)

### 3.1 通用导入系统
**状态**: ✅ 生产就绪（已解耦）

#### 核心文件
```python
# 新架构（推荐）
import_docs.py              # 通用文档导入工具
domain_processor.py         # 可配置领域处理器
universal_import.py         # 批量导入工具

# 向后兼容
import_docs_legal.py        # 法律专用导入工具（保留）
```

#### 配置系统
```
configs/
├── legal_domain.json      # 法律领域配置
├── general_domain.json    # 通用领域配置
└── [custom].json          # 自定义领域配置
```

### 3.2 文档导入器
```python
class DocumentImporter:     # 文档分块导入
class DomainProcessor:      # 通用领域处理器
class LegalDomainProcessor: # 法律专用处理器
```

## 4. 环境配置与依赖

### 4.1 环境变量
```bash
# .env 文件
EMBEDDING_API_KEY=sk-xxxxx        # 向量化API密钥
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # 模型名称
KB_PORT=8000                      # 知识库服务端口
MCP_CONFIG=./mcp_config.json      # MCP 配置文件路径
```

### 4.2 Python 依赖
```txt
# requirements.txt (根据各模块)
fastapi>=0.104.0           # HTTP API 框架
uvicorn>=0.24.0           # ASGI 服务器
numpy>=1.24.0             # 数值计算
scikit-learn>=1.3.0       # 机器学习
requests>=2.31.0          # HTTP 客户端
python-dotenv>=1.0.0      # 环境变量
mcp>=1.0.0                # MCP SDK
```

### 4.3 Node.js 依赖
```json
// package.json (persona 服务)
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.18.0"
  },
  "devDependencies": {
    "typescript": "^5.5.4",
    "@types/node": "^22.5.4",
    "tsx": "^4.16.2"
  }
}
```

## 5. 部署配置

### 5.1 MCP 客户端配置
```json
{
  "mcpServers": {
    "persona-service": {
      "command": "node",
      "args": ["./mcp-persona-uozumi/dist/server.js"],
      "cwd": "/path/to/mcp_database"
    },
    "knowledge-base": {
      "command": "python",
      "args": ["knowledge_base_mcp.py"],
      "cwd": "/path/to/mcp_database"
    }
  }
}
```

### 5.2 Docker 部署（可选）
```dockerfile
# 示例 Dockerfile
FROM node:18-slim
WORKDIR /app
COPY . .
RUN npm install && npm run build
CMD ["node", "dist/server.js"]
```

## 6. 数据流架构

### 6.1 角色交互流程
```
用户消息 -> MCP客户端 -> Persona服务 -> 获取人设/世界书 -> 生成回复
                     |
                     -> 知识库服务 -> 向量检索 -> 补充上下文
```

### 6.2 文档处理流程
```
原始文档 -> DomainProcessor -> 分块处理 -> VectorDatabase -> 向量化存储
```

### 6.3 记忆存储流程（计划中）
```
对话内容 -> 记忆提取 -> 重要性评分 -> VectorDatabase -> 持久化记忆
```

## 7. 监控与维护

### 7.1 日志系统
```python
# 统一日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 7.2 健康检查
```bash
# 服务状态检查
curl http://localhost:8000/stats        # 知识库服务
node mcp-persona-uozumi/dist/server.js  # Persona 服务测试
```

### 7.3 数据备份
```python
# 数据备份工具
reset_database.py --backup              # 创建备份
```

## 8. 扩展规划

### 8.1 已规划功能
- [ ] 向量化记忆存储库
- [ ] 多模态文档支持（图片、PDF）
- [ ] 实时学习与适应
- [ ] 分布式部署支持

### 8.2 性能优化
- [ ] 向量索引优化
- [ ] 缓存层实现
- [ ] 异步处理优化
- [ ] 负载均衡

## 9. 安全与合规

### 9.1 数据安全
- ✅ 敏感信息过滤
- ✅ 用户权限控制
- ✅ 数据隐私保护

### 9.2 内容安全
- ✅ 安全规则集成
- ✅ 违规内容检测
- ✅ 合规性审查

---

**文档版本**: v1.0  
**最后更新**: 2025-09-19  
**维护者**: mcp_database 项目组
