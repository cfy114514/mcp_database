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
    为避免对话应用上下文爆炸，将结果数量限制在1-3条最高分。
    """
    try:
        # Handle backward compatibility for the 'tags' parameter
        if tags and not tags_all:
            tags_all = tags

        # 裁剪 top_k 至 1-3
        effective_top_k = max(1, min((top_k if top_k is not None else 3), 3))

        results = db.search(
            query=query, 
            tags_all=tags_all,
            tags_any=tags_any,
            priority_tags=priority_tags,
            top_k=effective_top_k,
            metadata_filter=metadata_filter
        )

        formatted: List[Dict] = []
        for item in results:
            doc_obj = item
            score = None
            if isinstance(item, dict) and "document" in item:
                doc_obj = item.get("document")
                score = item.get("score")
            # 序列化 Document 或字典（避免直接用 hasattr 触发类型检查器告警）
            if isinstance(doc_obj, Document):
                doc_dict = doc_obj.model_dump()
            elif isinstance(doc_obj, dict):
                doc_dict = dict(doc_obj)
            else:
                continue
            if score is not None:
                try:
                    doc_dict["score"] = float(score)
                except Exception:
                    doc_dict["score"] = score
            formatted.append(doc_dict)

        # 最终再次截断，确保最多返回3条
        formatted = formatted[:effective_top_k]
        return {"success": True, "results": formatted}
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {"success": False, "message": str(e)}

@mcp.tool()
def add_document(content: str, tags: List[str], doc_id: Optional[str] = None, metadata: Optional[Dict] = None) -> dict:
    """Adds a new document to the knowledge base."""
    try:
        import time
        temp_id = doc_id if doc_id else f"temp_{int(time.time() * 1000)}"

        document = Document(
            doc_id=temp_id,
            content=content,
            tags=tags,
            metadata=metadata
        )
        success = db.add_document(document, save=True)
        return {
            "success": success,
            "document_id": document.id,
            "message": "Document added successfully" if success else "Failed to add document"
        }
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        return {"success": False, "message": str(e)}

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

@mcp.tool()
def get_status() -> dict:
    """返回知识库运行状态（就绪、索引、计数与标签）。"""
    try:
        index_ntotal = db.index.ntotal if getattr(db, "index", None) is not None else 0
        status = {
            "ready": (db.index is not None) and (len(db.vectors) == len(db.documents)) and (index_ntotal == len(db.vectors)),
            "documents": len(db.documents),
            "vectors": len(db.vectors),
            "index_ntotal": index_ntotal,
            "mismatch": len(db.vectors) != len(db.documents),
            "tags": list(db.tag_index.keys())
        }
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    # 启动 MCP 服务
    mcp.run(transport="stdio")
