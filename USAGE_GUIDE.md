# 解耦使用指南

## 1. 新的通用架构

### 架构概览
```
mcp_database/
├── configs/                    # 领域配置文件
│   ├── legal_domain.json      # 法律领域配置
│   └── general_domain.json    # 通用领域配置
├── domain_processor.py        # 通用领域处理器
├── import_docs.py             # 通用导入工具（新版）
├── import_docs_legal.py       # 法律专用导入工具（旧版保留）
└── knowledge_base_service.py  # 核心服务（保持通用）
```

## 2. 使用方法

### 2.1 法律文档导入（向后兼容）
```bash
# 使用新的通用工具（推荐）
python import_docs.py --domain legal

# 使用旧的专用工具（向后兼容）
python import_docs_legal.py
```

### 2.2 通用文档导入
```bash
# 使用通用配置
python import_docs.py --domain general

# 或不指定domain（默认通用）
python import_docs.py
```

### 2.3 自定义领域
```bash
# 使用自定义配置文件
python import_docs.py --config configs/my_domain.json
```

## 3. 配置文件说明

### 3.1 创建自定义配置
复制 `configs/general_domain.json` 并修改：

```json
{
  "domain_config": {
    "name": "医学文档系统",
    "description": "医学文献处理配置",
    "file_type_mapping": {
      "diagnosis": "诊断文档",
      "treatment": "治疗文档",
      "research": "研究文档"
    },
    "keyword_mapping": {
      "症状": ["医学", "诊断"],
      "治疗": ["医学", "治疗方案"],
      "药物": ["医学", "药理"]
    },
    "base_tags": ["医学"],
    "chunking_config": {
      "max_length": 400,
      "preserve_structure": true
    }
  }
}
```

### 3.2 配置字段说明
- `file_type_mapping`: 文件名到文档类型的映射
- `keyword_mapping`: 关键词到标签的映射
- `specialized_keywords`: 特定文档类型的专用关键词
- `base_tags`: 所有文档的基础标签
- `chunking_config`: 文档分割配置

## 4. 编程接口

### 4.1 使用领域处理器
```python
from domain_processor import DomainProcessor, LegalDomainProcessor

# 通用处理器
processor = DomainProcessor()
doc_type = processor.extract_document_type("manual.txt")
tags = processor.extract_tags(content, doc_type)

# 法律处理器（专用）
legal_processor = LegalDomainProcessor()
law_type = legal_processor.extract_document_type("xingfa.txt")
```

### 4.2 自定义处理器
```python
# 使用自定义配置
processor = DomainProcessor("configs/medical_domain.json")
```

## 5. 迁移指南

### 5.1 现有代码迁移

#### 旧代码：
```python
from import_docs import extract_law_type, extract_tags

law_type = extract_law_type(filename)
tags = extract_tags(content, law_type)
```

#### 新代码：
```python
from domain_processor import LegalDomainProcessor

processor = LegalDomainProcessor()
doc_type = processor.extract_document_type(filename)
tags = processor.extract_tags(content, doc_type)
```

### 5.2 向后兼容支持
旧的函数接口仍然可用：
```python
# 这些函数仍然可以使用，内部调用新的处理器
from domain_processor import extract_law_type, is_complete_article, extract_tags
```

## 6. 扩展新领域

### 6.1 添加新领域的步骤

1. 创建配置文件：`configs/new_domain.json`
2. 定义文档类型映射和关键词
3. 设置分块策略
4. 测试导入效果

### 6.2 示例：技术文档领域
```json
{
  "domain_config": {
    "name": "技术文档系统",
    "file_type_mapping": {
      "api": "API文档",
      "tutorial": "教程文档",
      "readme": "说明文档"
    },
    "keyword_mapping": {
      "函数": ["编程", "API"],
      "配置": ["设置", "配置"],
      "安装": ["部署", "安装"],
      "错误": ["调试", "故障排查"]
    },
    "base_tags": ["技术文档"],
    "chunking_config": {
      "max_length": 600,
      "preserve_structure": true,
      "structure_indicators": ["##", "###", "```"]
    }
  }
}
```

## 7. 测试验证

### 7.1 功能测试
```bash
# 测试法律文档导入
python import_docs.py --domain legal --dir test_data --pattern "*.txt"

# 测试通用文档导入
python import_docs.py --domain general --dir docs --pattern "*.md"

# 测试自定义配置
python import_docs.py --config configs/tech_domain.json --dir technical_docs
```

### 7.2 验证结果
检查导入后的标签和分类是否符合预期：
```python
from knowledge_base_service import VectorDatabase

db = VectorDatabase()
results = db.search("测试查询")
for doc in results:
    print(f"文档类型: {doc.metadata.get('doc_type')}")
    print(f"标签: {doc.tags}")
    print(f"领域: {doc.metadata.get('domain')}")
```

## 8. 性能优化

### 8.1 分块大小调优
根据不同领域的文档特点调整分块大小：
- 法律文档：300字符（保持条款完整性）
- 技术文档：600字符（代码块可能较长）
- 通用文档：500字符（平衡性能和语义）

### 8.2 批处理优化
```bash
# 大批量导入时使用较小的分块和较长的重试间隔
python import_docs.py --chunk-size 250 --retries 5 --delay 2.0
```

## 9. 故障排除

### 9.1 常见问题

**问题：找不到配置文件**
```
解决：确保配置文件路径正确，或使用绝对路径
```

**问题：标签提取不准确**
```
解决：检查配置文件中的关键词映射，添加更多相关词汇
```

**问题：分块效果不佳**
```
解决：调整chunking_config中的参数，特别是max_length和preserve_structure
```

### 9.2 调试模式
```bash
# 启用详细日志
python import_docs.py --domain legal -v

# 只处理单个文件进行调试
python import_docs.py --pattern "test.txt" --domain legal
```

## 10. 总结

通过这次解耦改造：

1. **提高了灵活性**：可以轻松适配新的文档领域
2. **保持了兼容性**：现有的法律文档处理功能完全保留
3. **增强了可维护性**：领域逻辑与核心逻辑分离
4. **简化了扩展**：添加新领域只需要配置文件
5. **改进了测试**：可以针对不同领域进行独立测试

建议在实际使用中逐步迁移到新的通用架构，享受更好的可扩展性和维护性。
