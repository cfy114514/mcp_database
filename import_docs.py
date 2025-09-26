#!/usr/bin/env python3
"""
通用文档导入工具
支持通过配置文件适配不同领域的文档处理需求

使用示例：
- 法律文档：python import_docs.py --domain legal
- 通用文档：python import_docs.py --domain general  
- 自定义配置：python import_docs.py --config configs/my_domain.json
- 导入origin目录：python import_docs.py --dir origin --pattern "*"
"""
from knowledge_base_service import VectorDatabase, Document
from document_importer import DocumentImporter
from domain_processor import DomainProcessor, LegalDomainProcessor
from pathlib import Path
import logging
import argparse
import sys
import json
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DocImporter")

def get_doc_type_from_filename(filename: str) -> str:
    """根据文件名和内容猜测文档类型"""
    filename_lower = filename.lower()
    if "kalake" in filename_lower and ".txt" in filename_lower:
        return "persona_config"
    if "worldbook" in filename_lower and ".json" in filename_lower:
        return "world_knowledge"
    if "persona" in filename_lower and ".md" in filename_lower:
        return "persona_description"
    if "buckets" in filename_lower or "templates" in filename_lower:
        return "dialogue_template"
    if "levels" in filename_lower:
        return "system_config"
    if "source" in filename_lower:
        return "source_material"
    if "xingfa" in filename_lower:
        return "legal_document"
    
    # 默认类型
    if filename_lower.endswith(".json"):
        return "system_config"
    if filename_lower.endswith(".txt") or filename_lower.endswith(".md"):
        return "source_material"
        
    return "unknown"


def process_file(file_path: Path, db: VectorDatabase, importer: DocumentImporter, 
                processor: Optional[DomainProcessor] = None) -> bool:
    """处理单个文件"""
    try:
        # 读取文件内容
        content = ""
        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    # 对于JSON，将其转换为格式化的字符串以便阅读和嵌入
                    json_data = json.load(f)
                    content = json.dumps(json_data, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析JSON文件 {file_path.name}，将作为纯文本处理。")
                    f.seek(0)
                    content = f.read()
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        if not content.strip():
            logger.warning(f"文件 {file_path.name} 为空")
            return False
        
        # 获取文档类型
        doc_type = get_doc_type_from_filename(file_path.name)
        logger.info(f"处理文件: {file_path.name} (类型: {doc_type})")
        
        # 提取基础标签
        base_tags = []
        if processor:
            base_tags = processor.extract_tags(content, doc_type)
        
        # 设置元数据
        metadata = {
            "source": str(file_path),
            "doc_type": doc_type,
            "filename": file_path.name,
            "tags": base_tags,
        }
        if processor:
            metadata["domain"] = processor.get_domain_info()["name"]

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
    parser.add_argument("--pattern", type=str, default="*", help="文件匹配模式, e.g., '*.txt', '*'")
    parser.add_argument("--config", type=str, help="领域配置文件路径")
    parser.add_argument("--domain", type=str, choices=["legal", "general"], 
                      help="预定义领域类型（legal=法律, general=通用）")
    parser.add_argument("--chunk-size", type=int, default=300, help="文档分块大小")
    parser.add_argument("--retries", type=int, default=3, help="失败重试次数")
    parser.add_argument("--delay", type=float, default=1.0, help="重试延迟时间(秒)")
    parser.add_argument("--reset", action="store_true", help="重置导入进度")
    args = parser.parse_args()

    # 初始化领域处理器
    processor = None
    if args.domain == "legal":
        processor = LegalDomainProcessor()
        logger.info("使用法律领域配置")
    elif args.config:
        processor = DomainProcessor(args.config)
        logger.info(f"使用自定义配置: {args.config}")
    elif args.dir != "origin": # 只有在处理非origin目录时才使用通用配置
        processor = DomainProcessor()  # 使用通用配置
        logger.info("使用通用配置")
    else:
        logger.info("正在处理 'origin' 目录，将使用基于文件名的类型检测。")

    # 显示领域信息
    if processor:
        domain_info = processor.get_domain_info()
        logger.info(f"领域名称: {domain_info['name']}")
        logger.info(f"支持的文档类型: {', '.join(domain_info['supported_types'])}")

    # 初始化数据库和导入器
    logger.info("初始化向量数据库和导入器...")
    db = VectorDatabase()
    
    # 根据领域配置调整分块大小
    chunk_size = args.chunk_size
    if processor:
        chunking_config = processor.config["domain_config"].get("chunking_config", {})
        if "max_length" in chunking_config:
            suggested_size = chunking_config["max_length"]
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
    files = [f for f in doc_dir.glob(args.pattern) if f.is_file()]
    if not files:
        logger.warning(f"在 '{doc_dir}' 中没有找到任何匹配 '{args.pattern}' 的文件")
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
