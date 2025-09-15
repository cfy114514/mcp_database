import os
from pathlib import Path
import json
from typing import List, Optional, Dict
import logging
from knowledge_base_service import Document, VectorDatabase

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImportTool")

def import_documents_from_file(db: VectorDatabase, file_path: str, default_tags: Optional[List[str]] = None) -> dict:
    """从文本文件导入文档"""
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {"success": False, "message": f"File not found: {file_path}"}

        documents_added = 0
        errors = []

        if file_path_obj.suffix.lower() == '.txt':
            # 处理文本文件，每个段落作为一个文档
            # 先尝试UTF-8编码，如果失败则尝试GBK编码
            try:
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path_obj, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError as e:
                    return {"success": False, "message": f"无法读取文件编码，请确保文件为UTF-8或GBK编码: {str(e)}"}
            
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                
            for i, paragraph in enumerate(paragraphs):
                    try:
                        doc_id = f"{file_path_obj.stem}_{i+1}"
                        document = Document(
                            id=doc_id,
                            content=paragraph,
                            tags=default_tags or [],
                            metadata={"source_file": str(file_path_obj)}
                        )
                        if db.add_document(document):
                            documents_added += 1
                            logger.info(f"Added document {doc_id}")
                        else:
                            errors.append(f"Failed to add document {doc_id}")
                    except Exception as e:
                        errors.append(f"Error processing paragraph {i+1}: {str(e)}")

        elif file_path_obj.suffix.lower() == '.json':
            # 处理JSON文件，支持单个文档或文档数组
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                data = json.load(f)
                documents = data if isinstance(data, list) else [data]
                
                for i, doc_data in enumerate(documents):
                    try:
                        doc_id = doc_data.get('id', f"{file_path_obj.stem}_{i+1}")
                        tags = doc_data.get('tags', default_tags or [])
                        metadata = doc_data.get('metadata', {})
                        metadata['source_file'] = str(file_path_obj)
                        
                        document = Document(
                            id=doc_id,
                            content=doc_data['content'],
                            tags=tags,
                            metadata=metadata
                        )
                        if db.add_document(document):
                            documents_added += 1
                            logger.info(f"Added document {doc_id}")
                        else:
                            errors.append(f"Failed to add document {doc_id}")
                    except Exception as e:
                        errors.append(f"Error processing document {i+1}: {str(e)}")
        
        else:
            return {"success": False, "message": f"Unsupported file format: {file_path_obj.suffix}"}

        message = f"Successfully imported {documents_added} documents"
        if errors:
            message += f"\nErrors occurred: {'; '.join(errors)}"

        return {
            "success": documents_added > 0,
            "message": message,
            "documents_added": documents_added,
            "errors": errors
        }

    except Exception as e:
        return {"success": False, "message": f"Import failed: {str(e)}"}

if __name__ == "__main__":
    # 示例用法
    db = VectorDatabase()
    
    # 导入文本文件
    result = import_documents_from_file(
        db=db,
        file_path="xingfa.txt",
        default_tags=["示例", "文档"]
    )
    print("导入结果:", result)
