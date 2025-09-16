#!/usr/bin/env python
from knowledge_base_service import VectorDatabase, Document
import logging
import json
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_result(title: str, result: Dict[str, Any]):
    logger.info(f"\n=== {title} ===")
    if result.get("success", False):
        if "results" in result:
            for i, doc in enumerate(result["results"], 1):
                logger.info(f"\n结果 {i}:")
                logger.info(f"文档ID: {doc['id']}")
                logger.info(f"相关度: 高")
                logger.info(f"标签: {', '.join(doc['tags'])}")
                logger.info(f"内容: {doc['content'][:100]}...")
                if doc.get('metadata'):
                    logger.info(f"元数据: {doc['metadata']}")
        elif "stats" in result:
            logger.info(json.dumps(result["stats"], ensure_ascii=False, indent=2))
    else:
        logger.error(f"查询失败: {result.get('message', '未知错误')}")
    logger.info("="* 50 + "\n")

def run_tests():
    db = VectorDatabase()
    
    # 测试用例1：基本概念查询
    logger.info("测试1：基本概念查询")
    result = db.search(query="物权是什么？")
    print_result("基本概念查询 - 物权", {
        "success": True,
        "results": [doc.model_dump() for doc in result]
    })

    # 测试用例2：带标签过滤的查询
    logger.info("测试2：带标签过滤的查询")
    result = db.search(query="刑罚处理方式", tags=["刑法"])
    print_result("带标签过滤的查询 - 刑法处罚", {
        "success": True,
        "results": [doc.model_dump() for doc in result]
    })

    # 测试用例3：跨领域查询
    logger.info("测试3：跨领域查询")
    result = db.search(query="侵害他人权益的处理方式")
    print_result("跨领域查询 - 权益侵害", {
        "success": True,
        "results": [doc.model_dump() for doc in result]
    })

    # 测试用例4：特定标签组合
    logger.info("测试4：特定标签组合")
    result = db.search(query="基本概念", tags=["民法", "基本概念"])
    print_result("特定标签组合 - 民法基本概念", {
        "success": True,
        "results": [doc.model_dump() for doc in result]
    })

    # 测试用例5：统计信息
    logger.info("测试5：获取统计信息")
    stats = {
        "success": True,
        "stats": {
            "document_count": len(db.documents),
            "vector_count": len(db.vectors),
            "tag_count": len(db.tag_index),
            "tags": list(db.tag_index.keys())
        }
    }
    print_result("数据库统计信息", stats)

if __name__ == "__main__":
    run_tests()
