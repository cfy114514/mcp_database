# 法律耦合分析报告与解耦建议

## 1. 法律相关函数和规则清单

### 文件：import_docs.py
#### 法律耦合函数：
1. `extract_law_type(filename: str) -> str`
   - 硬编码法律类型映射：{'xingfa': '刑法', 'minfa': '民法', 'xingsu': '刑事诉讼法', ...}
   - 返回默认值 '其他法律'

2. `is_complete_article(text: str) -> bool`
   - 检查法律条款格式（以"第"开头，包含"条"）

3. `split_text_to_chunks(text: str, min_length: int = 100, max_length: int = 800) -> list`
   - 基于法律条款结构进行文本分割

4. `extract_tags(content: str, law_type: str) -> list`
   - 硬编码法律标签：["总则", "分则"]
   - 硬编码法律关键词映射：
     ```python
     keywords_map = {
         # 刑法相关
         "故意杀人": ["暴力犯罪", "故意杀人罪"],
         "故意伤害": ["暴力犯罪", "故意伤害罪"],
         # ... 大量法律条目
     }
     ```
   - 硬编码刑罚信息：{"死刑": "死刑", "无期徒刑": "无期徒刑", ...}

### 文件：test_xingfa.py
#### 法律耦合函数：
1. `load_xingfa_content()` - 专门加载刑法文件
2. `is_complete_article(text)` - 同上
3. `get_article_number(text)` - 提取法条编号
4. `split_text_to_chunks()` - 法律条款分割
5. `extract_tags(content: str) -> list` - 刑法专用标签提取
6. `import_xingfa(db: VectorDatabase)` - 刑法导入

### 文件：check_database.py
#### 法律耦合函数：
1. `extract_punishment(text: str) -> str` - 提取刑罚信息
2. `summarize_article(text: str) -> str` - 法条摘要生成
3. `format_result()` - 法律条文格式化输出
4. `test_natural_queries()` - 法律查询测试用例

### 文件：test_queries.py
#### 法律耦合测试：
- 硬编码法律查询测试："物权是什么？"、"刑罚处理方式"等

## 2. 核心架构解耦点

### 2.1 配置解耦
当前问题：法律类型、关键词、标签都硬编码在代码中
解决方案：创建配置文件系统

### 2.2 标签系统解耦
当前问题：标签提取逻辑与法律领域强耦合
解决方案：通用标签提取框架

### 2.3 文档分割解耦
当前问题：分割逻辑基于法律条款格式
解决方案：可配置的文档分割策略

### 2.4 测试解耦
当前问题：所有测试都是法律相关
解决方案：通用测试框架

## 3. 解耦实施建议

### 3.1 立即可执行的解耦步骤

#### 步骤1：创建配置文件系统
```json
{
  "domain_config": {
    "name": "法律文档系统",
    "file_type_mapping": {
      "xingfa": "刑法",
      "minfa": "民法"
    },
    "keyword_mapping": {
      "故意杀人": ["暴力犯罪", "故意杀人罪"]
    },
    "punishment_keywords": ["死刑", "无期徒刑"],
    "chapter_keywords": ["总则", "分则"],
    "article_pattern": "^第.+条"
  }
}
```

#### 步骤2：抽象文档处理器
```python
class DocumentProcessor:
    def __init__(self, config_file: str):
        self.config = self.load_config(config_file)
    
    def extract_document_type(self, filename: str) -> str:
        # 基于配置而非硬编码
    
    def is_structured_content(self, text: str) -> bool:
        # 基于配置的pattern检查
    
    def extract_tags(self, content: str, doc_type: str) -> list:
        # 基于配置的标签提取
```

#### 步骤3：通用化核心服务
```python
class VectorDatabase:
    def __init__(self, domain_config: Optional[str] = None):
        self.domain_processor = DocumentProcessor(domain_config) if domain_config else None
```

### 3.2 文件重构优先级

#### 高优先级（立即执行）：
1. **import_docs.py** - 创建通用版本
2. **document_importer.py** - 已经相对通用，需要移除法律特定逻辑
3. **knowledge_base_service.py** - 核心服务，保持通用性

#### 中优先级：
1. **test_queries.py** - 创建通用测试框架
2. **knowledge_base_mcp.py** - MCP接口保持通用

#### 低优先级（可选迁移）：
1. **test_xingfa.py** - 作为法律领域示例保留
2. **check_database.py** - 作为法律领域工具保留

### 3.3 具体解耦行动

#### 行动1：创建通用导入器
- 重命名 `import_docs.py` 为 `import_docs_legal.py`
- 创建新的 `import_docs.py` 使用配置驱动

#### 行动2：创建领域配置
- 创建 `configs/legal_domain.json`
- 创建 `configs/general_domain.json`

#### 行动3：重构DocumentImporter
- 移除硬编码的法律逻辑
- 添加可配置的处理策略

## 4. 保持向后兼容性

### 4.1 迁移策略
1. 保留现有法律相关文件作为示例
2. 创建新的通用文件
3. 提供配置模板
4. 逐步迁移功能

### 4.2 法律领域包
可以将所有法律相关代码迁移到独立的包：
```
legal_domain/
├── configs/
│   └── legal_config.json
├── processors/
│   └── legal_document_processor.py
├── tests/
│   └── legal_test_cases.py
└── __init__.py
```

## 5. 解耦后的架构优势

1. **领域独立性**：可以轻松适配其他领域（医学、技术文档等）
2. **可维护性**：领域逻辑与核心逻辑分离
3. **可扩展性**：添加新领域不需要修改核心代码
4. **可测试性**：通用测试框架可以测试任何领域
5. **可配置性**：通过配置而非代码变更适配新需求

## 6. 下一步行动计划

1. 创建配置文件系统
2. 重构 `import_docs.py` 为通用版本
3. 创建领域配置模板
4. 更新文档和README
5. 测试通用性和兼容性
