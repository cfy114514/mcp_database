#!/usr/bin/env python3
from knowledge_base_service import VectorDatabase, Document
from document_importer import DocumentImporter
from pathlib import Path
import logging
import re
import sys
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DocImporter")

def extract_law_type(filename: str) -> str:
    """从文件名推断法律类型"""
    filename = filename.lower()
    law_types = {
        'xingfa': '刑法',
        'minfa': '民法',
        'xingsu': '刑事诉讼法',
        'minsu': '民事诉讼法',
        'xingzheng': '行政法',
        'laodong': '劳动法',
        'huanping': '环评法',
        'zhishi': '知识产权法',
    }
    
    for key, value in law_types.items():
        if key in filename:
            return value
    return '其他法律'

def is_complete_article(text: str) -> bool:
    """检查是否是完整的法律条款"""
    return text.strip().startswith('第') and ('条' in text[:15])

def split_text_to_chunks(text: str, min_length: int = 100, max_length: int = 800) -> list:
    """将文本分割成适当大小的块，保持法律条款的完整性"""
    # 预处理：规范化换行和空格
    text = text.replace('\n', '。').replace('　', '')
    text = re.sub(r'。+', '。', text)  # 合并多个句号
    sentences = text.split('。')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        # 检查是否是新条款的开始
        if is_complete_article(sentence):
            if current_chunk:
                chunks.append('。'.join(current_chunk) + '。')
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            if current_length + len(sentence) > max_length:
                chunks.append('。'.join(current_chunk) + '。')
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)
    
    if current_chunk:
        chunks.append('。'.join(current_chunk) + '。')
    
    # 合并过短的块
    final_chunks = []
    for chunk in chunks:
        if len(chunk) >= min_length:
            final_chunks.append(chunk)
        elif final_chunks:
            final_chunks[-1] = final_chunks[-1] + chunk
        else:
            final_chunks.append(chunk)
    
    return final_chunks

def extract_tags(content: str, law_type: str) -> list:
    """从文档内容中提取标签"""
    tags = [law_type, "法律"]  # 基础标签
    
    # 提取章节信息
    if "第一章" in content or "总则" in content:
        tags.append("总则")
    elif "分则" in content:
        tags.append("分则")
    
    # 提取具体罪名和相关概念
    keywords_map = {
        # 刑法相关
        "故意杀人": ["暴力犯罪", "故意杀人罪"],
        "故意伤害": ["暴力犯罪", "故意伤害罪"],
        "强奸": ["性犯罪", "强奸罪"],
        "盗窃": ["财产犯罪", "盗窃罪"],
        "诈骗": ["财产犯罪", "诈骗罪"],
        "贪污": ["职务犯罪", "贪污罪"],
        "渎职": ["职务犯罪", "渎职罪"],
        "受贿": ["职务犯罪", "受贿罪"],
        
        # 民法相关
        "合同": ["合同法", "合同纠纷"],
        "物权": ["物权法", "财产权"],
        "侵权": ["侵权法", "侵权责任"],
        "继承": ["继承法", "继承权"],
        "婚姻": ["婚姻法", "婚姻家庭"],
        
        # 行政法相关
        "行政许可": ["行政法", "行政许可"],
        "行政处罚": ["行政法", "行政处罚"],
        "行政复议": ["行政法", "行政复议"],
        
        # 诉讼法相关
        "起诉": ["诉讼程序", "诉权"],
        "上诉": ["诉讼程序", "上诉权"],
        "管辖": ["诉讼程序", "管辖权"],
        "证据": ["诉讼程序", "证据规则"],
    }
    
    # 根据法律类型添加特定关键词
    if law_type == "刑法":
        # 提取刑罚信息
        punishments = {
            "死刑": "死刑",
            "无期徒刑": "无期徒刑",
            "有期徒刑": "有期徒刑",
            "拘役": "拘役",
            "管制": "管制",
            "罚金": "罚金",
        }
        for keyword, tag in punishments.items():
            if keyword in content:
                tags.append(tag)
    
    # 从内容中提取关键词对应的标签
    for keyword, related_tags in keywords_map.items():
        if keyword in content:
            tags.extend(related_tags)
    
    # 去重
    return list(set(tags))

def process_file(file_path: Path, db: VectorDatabase, importer: DocumentImporter) -> bool:
    """处理单个文件"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"文件 {file_path.name} 为空")
            return False
        
        # 获取法律类型
        law_type = extract_law_type(file_path.name)
        logger.info(f"处理文件: {file_path.name} (类型: {law_type})")
        
        # 设置元数据
        metadata = {
            "source": str(file_path),
            "law_type": law_type,
            "filename": file_path.name,
            "tags": [law_type, "法律"]  # 基础标签
        }
        
        # 使用改进的导入器导入文档
        success = importer.import_document(
            content=content,
            metadata=metadata,
            max_retries=3,
            retry_delay=1.0
        )
        
        if success:
            logger.info(f"成功导入文件: {file_path.name}")
        else:
            logger.warning(f"部分内容导入失败: {file_path.name}")
            
        return success
    
    except Exception as e:
        logger.error(f"处理文件 {file_path.name} 时出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="批量导入文档到向量数据库")
    parser.add_argument("--dir", type=str, default="origin", help="包含文档的目录路径")
    parser.add_argument("--pattern", type=str, default="*.txt", help="文件匹配模式")
    parser.add_argument("--chunk-size", type=int, default=300, help="文档分块大小")
    parser.add_argument("--retries", type=int, default=3, help="失败重试次数")
    parser.add_argument("--delay", type=float, default=1.0, help="重试延迟时间(秒)")
    parser.add_argument("--reset", action="store_true", help="重置导入进度")
    args = parser.parse_args()

    # 初始化数据库和导入器
    logger.info("初始化向量数据库和导入器...")
    db = VectorDatabase()
    importer = DocumentImporter(db, max_chunk_size=args.chunk_size)
    
    if args.reset:
        importer.reset_progress()
        logger.info("已重置导入进度")
    
    # 获取文档目录
    origin_dir = Path(args.dir)
    if not origin_dir.exists():
        logger.error(f"目录不存在: {args.dir}")
        return False
    
    # 处理所有txt文件
    txt_files = list(origin_dir.glob(args.pattern))
    if not txt_files:
        logger.warning(f"没有找到任何{args.pattern}文件")
        return False
    
    logger.info(f"找到 {len(txt_files)} 个文件")
    
    # 处理每个文件
    success_count = 0
    for file_path in txt_files:
        if process_file(file_path, db, importer):
            success_count += 1
    
    # 打印最终统计信息
    stats = importer.get_stats()
    logger.info("\n导入统计：")
    logger.info(f"总文档数：{stats['total_documents']}")
    logger.info(f"成功导入：{stats['successful_imports']}")
    logger.info(f"失败导入：{stats['failed_imports']}")
    logger.info(f"重试次数：{stats['retried_chunks']}")
    logger.info(f"成功率：{stats.get('success_rate', 0):.2f}%")
    
    return success_count > 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
