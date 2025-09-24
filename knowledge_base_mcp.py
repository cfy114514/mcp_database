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
def search_documents(
    query: str, 
    tags_all: Optional[List[str]] = None, 
    tags_any: Optional[List[str]] = None,
    priority_tags: Optional[List[str]] = None,
    top_k: Optional[int] = 5, 
    metadata_filter: Optional[Dict] = None,
    tags: Optional[List[str]] = None # For backward compatibility
) -> dict:
    """
    Searches documents in the knowledge base with advanced filtering.
    
    Args:
        query: The natural language search query.
        tags_all: A list of tags that must all be present in the results (AND logic).
        tags_any: A list of tags where at least one must be present in the results (OR logic).
        priority_tags: A list of tags to boost the score of, making them more likely to appear first.
        top_k: The maximum number of results to return.
        metadata_filter: Optional dictionary of metadata to filter results.
        tags: Kept for backward compatibility, behaves like tags_all.

    Returns:
        A dictionary containing the search results.
    """
    try:
        # Handle backward compatibility for the 'tags' parameter
        if tags and not tags_all:
            tags_all = tags

        results = db.search(
            query=query, 
            tags_all=tags_all,
            tags_any=tags_any,
            priority_tags=priority_tags,
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
def add_document(content: str, tags: List[str], doc_id: Optional[str] = None, metadata: Optional[Dict] = None) -> dict:
    """
    Adds a new document to the knowledge base.
    
    Args:
        content: The text content of the document.
        tags: A list of tags to associate with the document.
        doc_id: An optional unique ID for the document. If not provided, one will be generated.
        metadata: Optional dictionary of metadata.

    Returns:
        A dictionary with the result of the operation.
    """
    try:
        # If doc_id is not provided, the service will generate one.
        # We need to create a temporary one for the Pydantic model, but the service's will be canonical.
        import time
        temp_id = doc_id if doc_id else f"temp_{int(time.time() * 1000)}"

        document = Document(
            id=temp_id,
            content=content,
            tags=tags,
            metadata=metadata
        )
        
        # The service's add_document now handles ID generation if not provided
        # and returns the final document ID.
        # We need to adapt to this if we want to use the service layer directly.
        # For now, we'll stick to the db layer which has a simpler `add_document`
        success = db.add_document(document)
        
        # If we were using the service endpoint, the logic would be different.
        # This MCP tool directly interacts with the DB layer.
        
        return {
            "success": success,
            "document_id": document.id,
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
