from knowledge_base_service import VectorDatabase, Document
import logging
import time
import random
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("XingfaTest")

def load_xingfa_content():
    """加载行法文件内容"""
    try:
        with open('./xingfa.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"读取行法文件失败: {e}")
        return None

def is_complete_article(text):
    """检查是否是完整的法律条款"""
    return text.strip().startswith('第') and ('条' in text[:15])

def get_article_number(text):
    """提取条款号"""
    try:
        start = text.find('第') + 1
        end = text.find('条')
        if start > 0 and end > start:
            return int(''.join(filter(str.isdigit, text[start:end])))
    except:
        pass
    return None

def split_text_to_chunks(text, min_length=100, max_length=800):
    """将文本分割成适当大小的块，保持法律条款的完整性"""
    # 首先按条进行分割
    chunks = []
    current_chunk = []
    current_length = 0
    
    # 预处理：规范化换行和空格
    text = text.replace('\n', '。').replace('　', '')
    sentences = text.split('。')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    for sentence in sentences:
        # 检查是否是新条款的开始
        if is_complete_article(sentence):
            # 如果已有内容，保存当前块
            if current_chunk:
                chunks.append('。'.join(current_chunk) + '。')
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            # 如果当前块加上新句子超过最大长度，并且不是同一条款的一部分
            if current_length + len(sentence) > max_length and not any(s.endswith('：') for s in current_chunk[-2:]):
                if current_chunk:
                    chunks.append('。'.join(current_chunk) + '。')
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)
    
    # 处理最后一个块
    if current_chunk:
        chunks.append('。'.join(current_chunk) + '。')
    
    # 后处理：合并过短的块
    merged_chunks = []
    temp_chunk = []
    temp_length = 0
    
    for chunk in chunks:
        if temp_length + len(chunk) <= max_length:
            temp_chunk.append(chunk)
            temp_length += len(chunk)
        else:
            if temp_chunk:
                merged_chunks.append(''.join(temp_chunk))
            temp_chunk = [chunk]
            temp_length = len(chunk)
    
    if temp_chunk:
        merged_chunks.append(''.join(temp_chunk))
    
    # 确保每个块都满足最小长度要求，同时保持条款完整性
    final_chunks = []
    for chunk in merged_chunks:
        if len(chunk) >= min_length:
            final_chunks.append(chunk)
        else:
            # 对于过短的块，尝试与相邻块合并
            if final_chunks:
                final_chunks[-1] = final_chunks[-1] + chunk
            else:
                final_chunks.append(chunk)
    
    return final_chunks

def import_xingfa(db: VectorDatabase):
    """导入行法文本到数据库"""
    content = load_xingfa_content()
    if not content:
        return False

    chunks = split_text_to_chunks(content)
    logger.info(f"文本已分割为 {len(chunks)} 个片段")

    success_count = 0
    for i, chunk in enumerate(chunks, 1):
        doc = Document(
            id=f"xingfa_{i:03d}",
            content=chunk,
            tags=["行法", "法律"]
        )
        if db.add_document(doc):
            success_count += 1
            logger.info(f"成功导入第 {i} 个文档片段（{len(chunk)} 字符）")
        else:
            logger.error(f"导入第 {i} 个文档片段失败")

    logger.info(f"总共成功导入 {success_count}/{len(chunks)} 个文档片段")
    return success_count > 0

def generate_test_queries(doc):
    """从文档中生成多样化的测试查询"""
    queries = []
    content = doc.content
    
    # 提取条款号和主题
    article_number = get_article_number(content)
    if article_number:
        queries.append({
            "query": f"第{article_number}条",
            "type": "条款号查询",
            "source_doc": doc
        })
    
    # 提取关键短语（基于标点符号分割）
    parts = content.split('】')
    if len(parts) > 1:
        # 提取罪名或主题
        topic = parts[0].split('【')[-1]
        if topic:
            queries.append({
                "query": topic,
                "type": "主题查询",
                "source_doc": doc
            })
    
    # 选择一个较长的内容片段
    if len(content) > 50:
        start = random.randint(0, len(content) - 50)
        length = random.randint(30, 50)
        queries.append({
            "query": content[start:start + length],
            "type": "内容片段查询",
            "source_doc": doc
        })
    
    return queries

def test_search(db: VectorDatabase):
    """使用多样化的查询测试搜索功能"""
    all_docs = list(db.documents.values())
    if not all_docs:
        logger.error("数据库中没有文档！")
        return

    # 生成多样化的测试查询
    test_queries = []
    test_docs = random.sample(all_docs, min(5, len(all_docs)))
    
    for doc in test_docs:
        test_queries.extend(generate_test_queries(doc))
    
    # 随机选择不同类型的查询进行测试
    test_queries = random.sample(test_queries, min(6, len(test_queries)))
    
    logger.info("\n开始搜索测试:")
    total_time = 0
    success_count = 0
    success_by_type = {}
    times_by_type = {}
    rank_positions = []

    for i, test in enumerate(test_queries, 1):
        query_type = test.get('type', '普通查询')
        logger.info(f"\n测试查询 {i}:")
        logger.info(f"查询类型: {query_type}")
        logger.info(f"查询内容: {test['query']}")
        logger.info(f"来源文档: ID={test['source_doc'].id}")
        logger.info(f"原文片段: ...{test['source_doc'].content[:50]}...")

        start_time = time.time()
        results = db.search(query=test['query'], top_k=5)
        duration = time.time() - start_time
        total_time += duration

        # 初始化类型统计
        if query_type not in success_by_type:
            success_by_type[query_type] = {'total': 0, 'success': 0}
            times_by_type[query_type] = []
        
        success_by_type[query_type]['total'] += 1
        times_by_type[query_type].append(duration)

        # 检查结果相关性和排名
        found_source = False
        source_rank = None
        if results:
            for j, result in enumerate(results, 1):
                logger.info(f"\n结果 {j}:")
                logger.info(f"文档ID: {result.id}")
                logger.info(f"相关片段: {result.content[:100]}...")
                if result.id == test['source_doc'].id:
                    found_source = True
                    source_rank = j
                    success_by_type[query_type]['success'] += 1
                    rank_positions.append(j)
                    break

        success_count += 1 if found_source else 0
        logger.info(f"\n查询耗时: {duration:.3f}秒")
        logger.info(f"是否找到源文档: {'✓' if found_source else '✗'}")
        if found_source:
            logger.info(f"源文档排名: {source_rank}")

    if test_queries:
        logger.info(f"\n搜索测试详细统计:")
        logger.info(f"总查询数: {len(test_queries)}")
        logger.info(f"平均响应时间: {total_time / len(test_queries):.3f}秒")
        logger.info(f"整体找回率: {success_count / len(test_queries) * 100:.1f}%")
        
        if rank_positions:
            avg_rank = sum(rank_positions) / len(rank_positions)
            logger.info(f"平均排名位置: {avg_rank:.1f}")
        
        logger.info("\n按查询类型统计:")
        for qtype, stats in success_by_type.items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_time = sum(times_by_type[qtype]) / len(times_by_type[qtype])
            logger.info(f"\n{qtype}:")
            logger.info(f"  查询次数: {stats['total']}")
            logger.info(f"  成功次数: {stats['success']}")
            logger.info(f"  成功率: {success_rate:.1f}%")
            logger.info(f"  平均耗时: {avg_time:.3f}秒")

def main():
    # 初始化数据库
    logger.info("初始化向量数据库...")
    db = VectorDatabase()

    # 检查数据库是否为空
    if not db.documents:
        logger.info("数据库为空，开始导入行法文本...")
        if not import_xingfa(db):
            logger.error("导入失败，退出测试")
            return
    else:
        logger.info(f"数据库中已有 {len(db.documents)} 个文档")

    # 运行搜索测试
    test_search(db)

if __name__ == "__main__":
    main()
