from knowledge_base_service import Document, VectorDatabase
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestSearch")

def create_test_documents():
    """创建测试文档"""
    return [
        Document(
            id="doc1",
            content="Python是一种易于学习又功能强大的编程语言。它有高效的高级数据结构，也有简单有效的面向对象编程。",
            tags=["编程语言", "Python", "教程"]
        ),
        Document(
            id="doc2",
            content="机器学习是人工智能的一个分支，主要研究计算机怎样模拟或实现人类的学习行为。",
            tags=["机器学习", "AI", "技术"]
        ),
        Document(
            id="doc3",
            content="深度学习是机器学习的分支，使用多层神经网络进行模式识别和特征学习。",
            tags=["深度学习", "AI", "神经网络"]
        ),
        Document(
            id="doc4",
            content="向量数据库是一种专门用于存储和检索向量数据的数据库系统，广泛应用于机器学习和人工智能领域。",
            tags=["数据库", "向量", "技术"]
        ),
        Document(
            id="doc5",
            content="自然语言处理是计算机科学和人工智能的一个重要分支，致力于让计算机理解和处理人类语言。",
            tags=["NLP", "AI", "技术"]
        )
    ]

def test_add_documents(db: VectorDatabase):
    """测试添加文档"""
    documents = create_test_documents()
    success_count = 0
    
    for doc in documents:
        logger.info(f"添加文档: {doc.id}")
        if db.add_document(doc):
            success_count += 1
    
    logger.info(f"成功添加 {success_count}/{len(documents)} 个文档")
    return success_count == len(documents)

def test_search(db: VectorDatabase):
    """测试搜索功能"""
    test_queries = [
        ("Python编程语言的特点是什么？", None),
        ("什么是机器学习？", None),
        ("深度学习和神经网络", ["AI"]),
        ("向量数据库的应用", ["技术"]),
        ("自然语言处理", ["AI", "技术"])
    ]
    
    for query, tags in test_queries:
        logger.info(f"\n执行搜索 - 查询: '{query}' 标签: {tags if tags else '无'}")
        start_time = time.time()
        
        results = db.search(query=query, tags=tags, top_k=3)
        
        duration = time.time() - start_time
        logger.info(f"搜索耗时: {duration:.2f}秒")
        logger.info(f"找到 {len(results)} 个结果:")
        
        for doc in results:
            logger.info(f"- 文档ID: {doc.id}")
            logger.info(f"  内容: {doc.content}")
            logger.info(f"  标签: {doc.tags}\n")

def main():
    logger.info("初始化向量数据库...")
    db = VectorDatabase()
    
    logger.info("开始添加测试文档...")
    if test_add_documents(db):
        logger.info("文档添加成功，开始测试搜索功能...")
        test_search(db)
    else:
        logger.error("文档添加失败，测试终止")

if __name__ == "__main__":
    main()
