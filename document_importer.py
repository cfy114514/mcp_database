import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import time
import json
from knowledge_base_service import VectorDatabase, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentImporter:
    def __init__(self, db: VectorDatabase, max_chunk_size: int = 300):
        self.db = db
        self.max_chunk_size = max_chunk_size
        self.stats = {
            "total_documents": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "retried_chunks": 0,
            "last_successful_id": None
        }
        self.progress_file = Path("import_progress.json")
        self._load_progress()

    def split_document(self, content: str) -> List[str]:
        """智能分割文档，确保每个片段不超过最大长度限制"""
        chunks = []
        current_chunk = ""
        
        # 按句号分割
        sentences = content.split("。")
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # 如果单个句子就超过限制，需要进一步分割
            if len(sentence) > self.max_chunk_size:
                sub_chunks = self._split_long_sentence(sentence)
                chunks.extend(sub_chunks)
                continue
                
            # 尝试添加句子到当前块
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + "。"
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """处理超长句子，按逗号或其他标点符号分割"""
        chunks = []
        current_chunk = ""
        
        # 按逗号分割
        parts = sentence.split("，")
        
        for part in parts:
            if len(part) > self.max_chunk_size:
                # 如果还是太长，按固定长度分割，但尽量在词的边界处断开
                sub_parts = [part[i:i+self.max_chunk_size] for i in range(0, len(part), self.max_chunk_size)]
                chunks.extend(sub_parts)
                continue
                
            if len(current_chunk) + len(part) <= self.max_chunk_size:
                current_chunk += part + "，"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = part + "，"
        
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def import_document(self, content: str, metadata: Optional[Dict[str, Any]] = None, 
                       max_retries: int = 3, retry_delay: float = 1.0,
                       exponential_backoff: bool = True) -> bool:
        """导入单个文档，支持重试机制和断点续传
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            exponential_backoff: 是否使用指数退避策略
        """
        chunks = self.split_document(content)
        self.stats["total_documents"] += len(chunks)
        
        success = True
        for i, chunk in enumerate(chunks):
            # 检查是否已经成功导入过
            doc_id = f"doc_{time.time()}_{i}"
            if self.stats["last_successful_id"] and doc_id <= self.stats["last_successful_id"]:
                logger.debug(f"跳过已导入的文档: {doc_id}")
                continue

            retries = 0
            current_delay = retry_delay
            
            while retries < max_retries:
                try:
                    # 如果内容过长，进一步分割
                    if len(chunk) > self.max_chunk_size:
                        logger.warning(f"文档片段过长 ({len(chunk)} 字符)，进行二次分割")
                        sub_chunks = self._split_long_sentence(chunk)
                        for sub_chunk in sub_chunks:
                            doc = Document(
                                id=f"{doc_id}_sub_{sub_chunks.index(sub_chunk)}",
                                content=sub_chunk,
                                metadata=metadata or {},
                                tags=metadata.get("tags", []) if metadata else []
                            )
                            self.db.add_document(doc)
                    else:
                        doc = Document(
                            id=doc_id,
                            content=chunk,
                            metadata=metadata or {},
                            tags=metadata.get("tags", []) if metadata else []
                        )
                        self.db.add_document(doc)
                    
                    self.stats["successful_imports"] += 1
                    self.stats["last_successful_id"] = doc_id
                    self._save_progress()  # 保存进度
                    break
                    
                except Exception as e:
                    logger.error(f"导入失败 (第 {retries + 1} 次尝试): {str(e)}")
                    retries += 1
                    self.stats["retried_chunks"] += 1
                    
                    if retries < max_retries:
                        if exponential_backoff:
                            current_delay *= 2  # 指数退避
                        logger.info(f"等待 {current_delay} 秒后重试...")
                        time.sleep(current_delay)
                    else:
                        logger.error(f"导入文档片段失败，已达到最大重试次数: {chunk[:100]}...")
                        self.stats["failed_imports"] += 1
                        success = False
                        break
        
        self._save_progress()  # 保存最终进度
        return success

    def import_from_directory(self, directory: str, file_pattern: str = "*.txt") -> Dict[str, Any]:
        """从目录批量导入文档"""
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
            
        for file_path in directory_path.glob(file_pattern):
            try:
                content = file_path.read_text(encoding='utf-8')
                metadata = {"source": file_path.name}
                
                logger.info(f"Importing file: {file_path.name}")
                self.import_document(content, metadata)
                
            except Exception as e:
                logger.error(f"Error importing file {file_path}: {str(e)}")
                self.stats["failed_imports"] += 1
        
        return self.stats

    def _save_progress(self):
        """保存导入进度到文件"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'stats': self.stats,
                    'timestamp': time.time()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存进度失败: {e}")

    def _load_progress(self):
        """从文件加载上次的导入进度"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats = data['stats']
                    logger.info(f"已加载之前的导入进度: {self.stats}")
            except Exception as e:
                logger.warning(f"加载进度失败: {e}")

    def reset_progress(self):
        """重置导入进度"""
        self.stats = {
            "total_documents": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "retried_chunks": 0,
            "last_successful_id": None
        }
        if self.progress_file.exists():
            self.progress_file.unlink()
        logger.info("导入进度已重置")

    def get_stats(self) -> Dict[str, Any]:
        """获取导入统计信息"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_imports"] / self.stats["total_documents"] * 100
                if self.stats["total_documents"] > 0 else 0
            )
        }

if __name__ == "__main__":
    db = VectorDatabase()
    importer = DocumentImporter(db, max_chunk_size=400)  # 设置较保守的块大小限制
    
    stats = importer.import_from_directory("origin")
    
    print("\n导入统计：")
    print(f"总文档数：{stats['total_documents']}")
    print(f"成功导入：{stats['successful_imports']}")
    print(f"失败导入：{stats['failed_imports']}")
    print(f"重试次数：{stats['retried_chunks']}")
