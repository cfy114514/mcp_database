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
from typing import Optional, Any, Dict, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DocImporter")

# 新增：健壮的文件读取（自动编码回退）
_DEF_ENCODINGS = [
    "utf-8-sig", "utf-8", "gbk", "big5", "utf-16", "utf-16-le", "utf-16-be", "cp1252"
]

def _read_text_auto(file_path: Path) -> str:
    data = file_path.read_bytes()
    for enc in _DEF_ENCODINGS:
        try:
            text = data.decode(enc)
            # 粗略校验：若包含常见乱码片段，继续尝试下一编码
            if "Ã" in text or "锟" in text:
                continue
            return text
        except Exception:
            continue
    # 兜底：以 utf-8 容错解码
    return data.decode("utf-8", errors="replace")


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


# --- 新增：JSON 展平为可读文本 ---
def _flatten_worldbook(data: Dict[str, Any]) -> str:
    entries: List[Dict[str, Any]] = data.get("entries", []) if isinstance(data, dict) else []
    lines: List[str] = []
    for e in entries:
        title = e.get("title") or e.get("id") or "条目"
        chunks = e.get("chunks", [])
        lines.append(f"【{title}】")
        for c in chunks:
            content = c.get("content") if isinstance(c, dict) else None
            if content:
                lines.append(content.strip())
    return "。".join([ln.strip().rstrip("。") for ln in lines if ln.strip()]) + "。"


def _flatten_templates(data: Dict[str, Any]) -> str:
    lines: List[str] = []
    templates = data.get("templates", {}) if isinstance(data, dict) else {}
    if isinstance(templates, dict):
        for bucket, arr in templates.items():
            if not isinstance(arr, list):
                continue
            lines.append(f"【{bucket}】")
            for t in arr[:10]:  # 每桶取前10条代表
                if isinstance(t, str):
                    lines.append(t.strip())
    situ = data.get("situational_templates", {}) if isinstance(data, dict) else {}
    if isinstance(situ, dict):
        for key, obj in situ.items():
            arr = obj.get("templates") if isinstance(obj, dict) else None
            if isinstance(arr, list) and arr:
                lines.append(f"【情境:{key}】{arr[0].strip()}")
    return "。".join([ln.strip().rstrip("。") for ln in lines if ln.strip()]) + "。"


def _flatten_buckets(data: Dict[str, Any]) -> str:
    buckets = data.get("buckets", []) if isinstance(data, dict) else []
    lines: List[str] = []
    for b in buckets[:5]:  # 取前5个桶概要
        name = b.get("name", "桶")
        examples = b.get("examples", [])
        lines.append(f"【桶:{name}】")
        if examples:
            ex = examples[:2]
            for e in ex:
                if isinstance(e, str):
                    lines.append(e.strip())
        # 微模板摘要
        tm = b.get("templates", {}).get("micro", []) if isinstance(b.get("templates"), dict) else []
        for t in tm[:2]:
            if isinstance(t, str):
                lines.append(t.strip())
    # 触发器摘要
    trig = data.get("situational_triggers", [])
    if isinstance(trig, list) and trig:
        lines.append("【情境触发】检测移动/离开等意图时优先使用 narrator_move 模板。")
    return "。".join([ln.strip().rstrip("。") for ln in lines if ln.strip()]) + "。"


def _flatten_levels(data: Dict[str, Any]) -> str:
    levels = data.get("levels", []) if isinstance(data, dict) else []
    lines: List[str] = []
    for lv in levels[:8]:  # 取前8关节选
        pid = lv.get("id")
        player = lv.get("player")
        opts = lv.get("options", [])
        if player:
            lines.append(f"【关卡{pid}】玩家：{player}")
        if isinstance(opts, list) and opts:
            rep = opts[0].get("reply") if isinstance(opts[0], dict) else None
            if rep:
                lines.append(f"卡菈克：{rep}")
    return "。".join([ln.strip().rstrip("。") for ln in lines if ln.strip()]) + "。"


def flatten_json_to_text(json_data: Any, filename: str, doc_type: str) -> str:
    """将结构化 JSON 展开为便于嵌入与检索的中文文本。"""
    name = filename.lower()
    try:
        if doc_type == "world_knowledge" or "worldbook" in name:
            return _flatten_worldbook(json_data)
        if doc_type == "dialogue_template" or "templates" in name:
            return _flatten_templates(json_data)
        if "buckets" in name:
            return _flatten_buckets(json_data)
        if "levels" in name:
            return _flatten_levels(json_data)
    except Exception as e:
        logger.warning(f"JSON 展平失败，回退为原始文本: {e}")
    # 回退：压缩后的 JSON 文本（不缩进，减少噪声）
    try:
        return json.dumps(json_data, ensure_ascii=False)
    except Exception:
        return str(json_data)


# --- 新增：路径驱动的标签 ---
def infer_tags(file_path: Path, doc_type: str) -> List[str]:
    tags: List[str] = []
    parts_lower = [p.lower() for p in file_path.parts]
    if any("karlach" in p for p in parts_lower):
        tags.append("role:karlach")
    # type tag
    if doc_type == "world_knowledge":
        tags.append("type:worldbook")
    elif doc_type == "dialogue_template":
        tags.append("type:templates")
    elif doc_type == "persona_description":
        tags.append("type:persona")
    elif doc_type == "system_config":
        if "levels" in file_path.name.lower():
            tags.append("type:levels")
        elif "buckets" in file_path.name.lower():
            tags.append("type:buckets")
        else:
            tags.append("type:config")
    else:
        tags.append(f"type:{doc_type}")
    return tags


def process_file(file_path: Path, db: VectorDatabase, importer: DocumentImporter, 
                processor: Optional[DomainProcessor] = None) -> bool:
    """处理单个文件"""
    try:
        # 读取文件内容（自动编码识别/回退）
        content = ""
        is_json = file_path.suffix.lower() == '.json'
        if is_json:
            # 多编码尝试以解析 JSON
            raw = file_path.read_bytes()
            json_obj = None
            chosen_enc = None
            for enc in _DEF_ENCODINGS:
                try:
                    txt = raw.decode(enc)
                    json_obj = json.loads(txt)
                    chosen_enc = enc
                    break
                except Exception:
                    continue
            if json_obj is None:
                # 最后再尝试原读+回退为纯文本
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_obj = json.load(f)
                        chosen_enc = 'utf-8'
                except Exception:
                    # 解析失败时作为文本处理
                    content = _read_text_auto(file_path)
                    logger.warning(f"无法以JSON解析 {file_path.name}，按文本编码导入（content length={len(content)}）")
            if json_obj is not None and not content:
                doc_type = get_doc_type_from_filename(file_path.name)
                content = flatten_json_to_text(json_obj, file_path.name, doc_type)
                if chosen_enc:
                    logger.info(f"JSON文件 {file_path.name} 使用编码 {chosen_enc} 解析成功")
        else:
            content = _read_text_auto(file_path)
            logger.info(f"文本文件 {file_path.name} 按自动编码读取（len={len(content)}）")
        
        if not content.strip():
            logger.warning(f"文件 {file_path.name} 为空")
            return False
        
        # 获取文档类型
        doc_type = get_doc_type_from_filename(file_path.name)
        logger.info(f"处理文件: {file_path.name} (类型: {doc_type})")
        
        # 提取基础标签
        base_tags: List[str] = []
        if processor:
            base_tags = processor.extract_tags(content, doc_type)
        # 路径驱动标签
        path_tags = infer_tags(file_path, doc_type)
        all_tags = list(dict.fromkeys((base_tags or []) + path_tags))
        
        # 设置元数据
        metadata: Dict[str, Any] = {
            "source": str(file_path),
            "doc_type": doc_type,
            "filename": file_path.name,
            "tags": all_tags,
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
    parser.add_argument("--pattern", type=str, default="*", help="文件匹配模式, e.g., '*.txt', '*' ")
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

    # 新增：导入完成后持久化保存并重建索引，便于HTTP服务立即可检索
    try:
        db._save_data()
        db.rebuild_index()
        logger.info("已保存数据到磁盘并重建索引。")
    except Exception as e:
        logger.warning(f"保存/重建索引时出现问题: {e}")
    
    return success_count > 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
