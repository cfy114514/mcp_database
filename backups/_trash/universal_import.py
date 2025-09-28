#!/usr/bin/env python3
from knowledge_base_service import VectorDatabase, Document
from document_importer import DocumentImporter
from domain_processor import DomainProcessor, LegalDomainProcessor
from pathlib import Path
import logging
import argparse
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UniversalDocImporter")

def process_file(file_path: Path, db: VectorDatabase, importer: DocumentImporter, 
                processor: DomainProcessor) -> bool:
    """处理单个文件"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"文件 {file_path.name} 为空")
            return False
        
        # 获取文档类型
        doc_type = processor.extract_document_type(file_path.name)
        logger.info(f"处理文件: {file_path.name} (类型: {doc_type})")
        
        # 提取基础标签
        base_tags = processor.extract_tags(content, doc_type)
        
        # 设置元数据
        metadata = {
            "source": str(file_path),
            "doc_type": doc_type,
            "filename": file_path.name,
            "tags": base_tags,
            "domain": processor.get_domain_info()["name"]
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
    parser = argparse.ArgumentParser(description="通用文档批量导入工具")
    parser.add_argument("--dir", type=str, default="origin", help="包含文档的目录路径")
    parser.add_argument("--pattern", type=str, default="*.txt", help="文件匹配模式")
    parser.add_argument("--config", type=str, help="领域配置文件路径")
    parser.add_argument("--domain", type=str, choices=["legal", "general"], 
                      help="预定义领域类型")
    parser.add_argument("--chunk-size", type=int, default=300, help="文档分块大小")
    parser.add_argument("--retries", type=int, default=3, help="失败重试次数")
    parser.add_argument("--delay", type=float, default=1.0, help="重试延迟时间(秒)")
    parser.add_argument("--reset", action="store_true", help="重置导入进度")
    args = parser.parse_args()

    # 初始化领域处理器
    if args.domain == "legal":
        processor = LegalDomainProcessor()
    elif args.config:
        processor = DomainProcessor(args.config)
    else:
        processor = DomainProcessor()  # 使用通用配置
    
    # 显示领域信息
    domain_info = processor.get_domain_info()
    logger.info(f"使用领域配置: {domain_info['name']}")
    logger.info(f"支持的文档类型: {', '.join(domain_info['supported_types'])}")

    # 初始化数据库和导入器
    logger.info("初始化向量数据库和导入器...")
    db = VectorDatabase()
    
    # 根据领域配置调整分块大小
    chunk_size = args.chunk_size
    if hasattr(processor.config["domain_config"], "chunking_config"):
        suggested_size = processor.config["domain_config"]["chunking_config"]["max_length"]
        if suggested_size < chunk_size:
            chunk_size = suggested_size
            logger.info(f"根据领域配置调整分块大小为: {chunk_size}")
    
    importer = DocumentImporter(db, max_chunk_size=chunk_size)
    
    if args.reset:
        importer.reset_progress()
        logger.info("已重置导入进度")
    
    # 获取文档目录
    doc_dir = Path(args.dir)
    if not doc_dir.exists():
        logger.error(f"目录不存在: {args.dir}")
        return False
    
    # 处理所有匹配的文件
    files = list(doc_dir.glob(args.pattern))
    if not files:
        logger.warning(f"没有找到任何{args.pattern}文件")
        return False
    
    logger.info(f"找到 {len(files)} 个文件")
    
    # 处理每个文件
    success_count = 0
    for file_path in files:
        if process_file(file_path, db, importer, processor):
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
