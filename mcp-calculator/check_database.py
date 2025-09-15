import logging
import re
import os
import sys
from knowledge_base_service import VectorDatabase
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def highlight_keywords(text: str, keywords: List[str]) -> str:
    """高亮关键词"""
    for keyword in keywords:
        pattern = re.compile(f'({keyword})', re.IGNORECASE)
        text = pattern.sub('【\\1】', text)
    return text

def extract_punishment(text: str) -> str:
    """提取处罚信息"""
    punishments = []
    patterns = [
        r"处([^，。；）】]+)有期徒刑",
        r"处([^，。；）】]+)拘役",
        r"并处([^，。；）】]+)罚金",
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            punishments.append(match.group())
    
    return "；".join(punishments) if punishments else "未明确指出处罚"

def summarize_article(text: str) -> str:
    """简要总结条文要点"""
    # 提取罪名
    crime_name = re.search(r"【([^】]+)】", text)
    crime_name = crime_name.group(1) if crime_name else "未知罪名"
    
    # 提取处罚
    punishment = extract_punishment(text)
    
    # 提取构成要件（简化处理）
    elements = text.split("的，")[0] if "的，" in text else text
    elements = elements.split("】")[-1] if "】" in elements else elements
    
    return f"罪名：{crime_name}\n构成要件：{elements}\n处罚：{punishment}"

def format_result(doc: Any, query: str, index: int) -> str:
    """格式化输出结果"""
    # 提取条文号
    article_num = re.search(r"第[一二三四五六七八九十百]+条", doc.content)
    article_num = article_num.group() if article_num else "条文编号未知"
    
    # 获取关键词
    keywords = [word for word in query if len(word) >= 2]
    keywords.extend(["有期徒刑", "拘役", "罚金", "情节严重"])
    
    # 高亮处理
    highlighted_text = highlight_keywords(doc.content, keywords)
    
    # 生成摘要
    summary = summarize_article(doc.content)
    
    return f"\n结果 {index}:\n{article_num}\n{summary}\n\n原文：\n{highlighted_text}"

def search(query):
    """调用搜索接口"""
    url = "http://localhost:8080/search"  # 假设服务运行在本地8080端口
    try:
        response = requests.post(url, json={"query": query})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"搜索请求失败: {e}")
        return []

def test_natural_queries():
    """测试更自然的用户查询方式"""
    # 初始化知识库
    db = VectorDatabase()
    
    # 模拟真实用户的自然语言查询
    queries = [
        "什么情况下算是泄露军事秘密？",
        "偷拍军事设施会判多久？",
        "对俘虏不人道会受什么处罚",
        "非法占用农田的后果",
        "假释期间又犯事怎么办",
        "军事基地周边拍照违法吗",
        "过失泄密和故意泄密有什么区别",
        "在部队服役时无意中说漏嘴会怎样"
    ]
    
    logger.info("开始测试自然语言查询...")
    
    for i, query in enumerate(queries, 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"测试查询 {i}:")
        logger.info(f"用户问题: {query}")
        logger.info(f"{'-'*50}")
        
        # 执行搜索
        try:
            results = db.search(query, top_k=3)
            if results:
                logger.info("\n相关条文:")
                for j, doc in enumerate(results, 1):
                    logger.info(format_result(doc, query, j))
            else:
                logger.info("未找到相关条文")
            logger.info(f"\n{'='*50}")
        except Exception as e:
            logger.error(f"查询出错: {e}")
            
if __name__ == "__main__":
    test_natural_queries()
