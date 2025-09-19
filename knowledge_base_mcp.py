#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import sys
import logging
from typing import List, Dict, Optional
import json
import os
from pathlib import Path

# 导入本地模块
from knowledge_base_service import VectorDatabase, Document, SearchRequest

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("KnowledgeBase")

# 创建 MCP 服务器
mcp = FastMCP("KnowledgeBase")

# 创建向量数据库实例
try:
    db = VectorDatabase()
    logger.info("向量数据库初始化成功")
except Exception as e:
    logger.error(f"向量数据库初始化失败: {e}")
    raise

@mcp.tool()
def search_documents(query: str, tags: Optional[List[str]] = None, top_k: Optional[int] = 5, metadata_filter: Optional[Dict] = None) -> dict:
    """搜索文档。
    Args:
        query: 搜索查询文本
        tags: 可选的标签列表进行过滤
        top_k: 返回的最大结果数量
        metadata_filter: 可选的元数据过滤条件

    Returns:
        包含搜索结果的字典
    """
    try:
        results = db.search(
            query=query, 
            tags=tags, 
            top_k=top_k if top_k is not None else 5,
            metadata_filter=metadata_filter
        )
        return {
            "success": True,
            "results": [doc.model_dump() for doc in results]
        }
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def add_document(doc_id: str, content: str, tags: List[str], metadata: Optional[Dict] = None) -> dict:
    """添加新文档到知识库。
    Args:
        doc_id: 文档唯一标识符
        content: 文档内容
        tags: 文档标签列表
        metadata: 可选的元数据字典

    Returns:
        操作结果字典
    """
    try:
        document = Document(
            id=doc_id,
            content=content,
            tags=tags,
            metadata=metadata
        )
        success = db.add_document(document)
        return {
            "success": success,
            "message": "Document added successfully" if success else "Failed to add document"
        }
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def get_stats() -> dict:
    """获取知识库统计信息。
    Returns:
        包含统计信息的字典
    """
    try:
        stats = {
            "document_count": len(db.documents),
            "vector_count": len(db.vectors),
            "tag_count": len(db.tag_index),
            "tags": list(db.tag_index.keys())
        }
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

if __name__ == "__main__":
    # 启动 MCP 服务
    mcp.run(transport="stdio")
