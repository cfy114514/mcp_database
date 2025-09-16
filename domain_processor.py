#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DomainProcessor:
    """通用领域文档处理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化领域处理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用通用配置
        """
        if config_path is None:
            config_path = str(Path(__file__).parent / "configs" / "general_domain.json")
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "domain_config": {
                "name": "默认文档系统",
                "file_type_mapping": {},
                "default_type": "通用文档",
                "keyword_mapping": {},
                "specialized_keywords": {},
                "chapter_keywords": {},
                "base_tags": ["文档"],
                "document_patterns": {
                    "article_start": "^.+",
                    "article_content": "(.+)",
                    "chapter_pattern": "^.+"
                },
                "chunking_config": {
                    "min_length": 100,
                    "max_length": 500,
                    "preserve_structure": False,
                    "structure_indicators": []
                }
            }
        }
    
    def extract_document_type(self, filename: str) -> str:
        """从文件名提取文档类型"""
        filename_lower = filename.lower()
        domain_config = self.config["domain_config"]
        
        for key, value in domain_config["file_type_mapping"].items():
            if key in filename_lower:
                return value
                
        return domain_config["default_type"]
    
    def is_structured_content(self, text: str) -> bool:
        """检查是否是结构化内容"""
        domain_config = self.config["domain_config"]
        pattern = domain_config["document_patterns"]["article_start"]
        
        try:
            return bool(re.match(pattern, text.strip()))
        except re.error:
            logger.warning(f"正则表达式错误: {pattern}")
            return False
    
    def extract_tags(self, content: str, doc_type: str) -> List[str]:
        """从文档内容中提取标签"""
        domain_config = self.config["domain_config"]
        tags = set(domain_config["base_tags"])
        
        # 添加文档类型标签
        tags.add(doc_type)
        
        # 检查章节关键词
        for keyword, tag in domain_config["chapter_keywords"].items():
            if keyword in content:
                tags.add(tag)
        
        # 检查通用关键词
        for keyword, related_tags in domain_config["keyword_mapping"].items():
            if keyword in content:
                tags.update(related_tags)
        
        # 检查专用关键词
        if doc_type in domain_config["specialized_keywords"]:
            specialized = domain_config["specialized_keywords"][doc_type]
            for keyword, tag in specialized.items():
                if keyword in content:
                    tags.add(tag)
        
        return list(tags)
    
    def split_document(self, content: str) -> List[str]:
        """智能分割文档"""
        domain_config = self.config["domain_config"]
        chunking_config = domain_config["chunking_config"]
        
        min_length = chunking_config["min_length"]
        max_length = chunking_config["max_length"]
        preserve_structure = chunking_config["preserve_structure"]
        structure_indicators = chunking_config["structure_indicators"]
        
        if preserve_structure and structure_indicators:
            return self._split_with_structure(content, min_length, max_length, structure_indicators)
        else:
            return self._split_basic(content, min_length, max_length)
    
    def _split_with_structure(self, content: str, min_length: int, max_length: int, 
                            structure_indicators: List[str]) -> List[str]:
        """基于结构化指标分割文档"""
        chunks = []
        current_chunk = ""
        
        # 预处理：规范化换行和空格
        content = content.replace('\n', '。').replace('　', '')
        content = re.sub(r'。+', '。', content)
        
        sentences = content.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            # 检查是否是结构化内容的开始
            is_structure_start = any(
                sentence.strip().startswith(indicator) 
                for indicator in structure_indicators
            )
            
            if is_structure_start and current_chunk and len(current_chunk) >= min_length:
                chunks.append(current_chunk + '。')
                current_chunk = sentence
            elif len(current_chunk) + len(sentence) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk + '。')
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += '。' + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk + '。')
        
        return self._merge_short_chunks(chunks, min_length)
    
    def _split_basic(self, content: str, min_length: int, max_length: int) -> List[str]:
        """基础文档分割"""
        chunks = []
        
        # 按句子分割
        sentences = re.split(r'[。！？\n]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += "。" + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return self._merge_short_chunks(chunks, min_length)
    
    def _merge_short_chunks(self, chunks: List[str], min_length: int) -> List[str]:
        """合并过短的块"""
        if not chunks:
            return chunks
        
        merged_chunks = []
        current_chunk = chunks[0]
        
        for chunk in chunks[1:]:
            if len(current_chunk) < min_length:
                current_chunk += chunk
            else:
                merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        merged_chunks.append(current_chunk)
        return merged_chunks
    
    def get_domain_info(self) -> Dict[str, Any]:
        """获取领域信息"""
        domain_config = self.config["domain_config"]
        return {
            "name": domain_config["name"],
            "description": domain_config.get("description", ""),
            "supported_types": list(domain_config["file_type_mapping"].values()),
            "base_tags": domain_config["base_tags"]
        }


class LegalDomainProcessor(DomainProcessor):
    """法律领域专用处理器（向后兼容）"""
    
    def __init__(self):
        config_path = Path(__file__).parent / "configs" / "legal_domain.json"
        super().__init__(str(config_path))


class GeneralDomainProcessor(DomainProcessor):
    """通用领域处理器"""
    
    def __init__(self):
        config_path = Path(__file__).parent / "configs" / "general_domain.json"
        super().__init__(str(config_path))


# 向后兼容的函数接口
def extract_law_type(filename: str) -> str:
    """向后兼容的法律类型提取函数"""
    processor = LegalDomainProcessor()
    return processor.extract_document_type(filename)


def is_complete_article(text: str) -> bool:
    """向后兼容的法律条款检查函数"""
    processor = LegalDomainProcessor()
    return processor.is_structured_content(text)


def extract_tags(content: str, law_type: str) -> list:
    """向后兼容的标签提取函数"""
    processor = LegalDomainProcessor()
    return processor.extract_tags(content, law_type)
