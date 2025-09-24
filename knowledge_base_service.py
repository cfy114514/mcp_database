from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Union
import numpy as np
import json
import logging
from pathlib import Path
import requests
from dotenv import load_dotenv
import base64
from numpy.linalg import norm
import os
import uvicorn
import time

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KnowledgeBase")

class Document(BaseModel):
    id: str
    content: str
    tags: List[str]
    metadata: Optional[Dict] = None

class SearchRequest(BaseModel):
    query: str
    tags: Optional[List[str]] = None # Kept for backward compatibility
    tags_all: Optional[List[str]] = None
    tags_any: Optional[List[str]] = None
    priority_tags: Optional[List[str]] = None
    top_k: Optional[int] = 5
    metadata_filter: Optional[Dict] = None

class SearchResponse(BaseModel):
    success: bool
    results: List[Document]
    message: Optional[str] = None

class EmbeddingAPI:
    def __init__(self):
        self.api_key = os.getenv("EMBEDDING_API_KEY")
        if not self.api_key:
            raise ValueError("EMBEDDING_API_KEY not found in environment variables")
        
        self.model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
        self.api_url = "https://api.siliconflow.cn/v1/embeddings"
        self.api_key = os.getenv("EMBEDDING_API_KEY", "sk-sgrrueslsskswlfcrefyqyeuffunfxjswmmzdicdtgksqqxr")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_embedding(self, text: str, encoding_format: str = "float") -> List[float]:
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "input": text,
                    "encoding_format": encoding_format
                },
                verify=True  # 启用SSL验证
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            raise

class VectorDatabase:
    def __init__(self, dimension: int = 1024, data_dir: Optional[str] = None):
        self.embedding_api = EmbeddingAPI()
        self.dimension = dimension
        self.vectors = []
        self.documents = {}
        self.document_ids = []
        self.tag_index = {}
        
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # 将数据目录固定在仓库内的 data 子目录
            repo_root = Path(__file__).parent
            self.data_dir = repo_root / "data"
        
        try:
            self.data_dir.mkdir(exist_ok=True)
        except Exception as e:
            logger.warning(f"无法创建 data 目录 ({self.data_dir}): {e}")
        logger.info(f"VectorDatabase data_dir set to: {self.data_dir.resolve()}")
        self._load_data()

    def _load_data(self):
        vectors_file = self.data_dir / "vectors.npy"
        docs_file = self.data_dir / "documents.json"
        
        # Load documents if the file exists, regardless of vectors
        if docs_file.exists():
            try:
                with open(docs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both list and dict formats
                    if isinstance(data, list):
                        self.documents = {doc['id']: Document(**doc) for doc in data if 'id' in doc}
                    else:
                        self.documents = {k: Document(**v) for k, v in data.items()}
                    
                    self.document_ids = list(self.documents.keys())
                    self._rebuild_tag_index()
                logger.info(f"成功加载 {len(self.documents)} 个文档")
            except Exception as e:
                logger.error(f"加载文档数据时出错: {e}")
                self.documents = {}
                self.document_ids = []
                self.tag_index = {}

        # Load vectors only if both files exist
        if vectors_file.exists() and docs_file.exists():
            try:
                # 加载向量数据
                loaded_vectors = np.load(str(vectors_file))
                self.vectors = [vec for vec in loaded_vectors]  # 转换为列表
                
                # Verify vector and document count match
                if len(self.vectors) != len(self.documents):
                    logger.warning(f"向量数量 ({len(self.vectors)}) 与文档数量 ({len(self.documents)}) 不匹配。可能需要重建向量。")

                logger.info(f"成功加载 {len(self.vectors)} 个向量")
            except Exception as e:
                logger.error(f"加载向量数据时出错: {e}")
                self.vectors = []
        else:
            # If vectors don't exist, ensure the list is empty
            self.vectors = []

    def _save_data(self):
        """保存数据到磁盘"""
        try:
            vectors_file = self.data_dir / "vectors.npy"
            docs_file = self.data_dir / "documents.json"
            
            # 确保向量是numpy数组并保存
            vectors_array = np.array(self.vectors, dtype=np.float32)
            np.save(str(vectors_file), vectors_array)
            
            # 保存文档数据
            with open(docs_file, 'w', encoding='utf-8') as f:
                json.dump({k: v.model_dump() for k, v in self.documents.items()}, f, ensure_ascii=False)
            
            logger.info(f"成功保存 {len(self.vectors)} 个向量和 {len(self.documents)} 个文档")
        except Exception as e:
            logger.error(f"保存数据时出错: {e}")

    def add_document(self, document: Document) -> bool:
        """添加文档到数据库"""
        try:
            # 使用 API 生成文档向量
            vector = self.embedding_api.create_embedding(document.content)
            if isinstance(vector, str):  # 如果返回的是 base64 编码
                vector = np.frombuffer(base64.b64decode(vector), dtype=np.float32)
            vector = np.array(vector, dtype=np.float32)
            
            # 添加向量到列表
            self.vectors.append(vector)
            
            # 存储文档
            self.documents[document.id] = document
            self.document_ids.append(document.id)
            
            # 更新标签索引
            for tag in document.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                self.tag_index[tag].add(document.id)
            
            # 保存数据
            self._save_data()
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

    def search(self, query: str, tags: Optional[List[str]] = None, top_k: int = 5, metadata_filter: Optional[Dict] = None,
             tags_all: Optional[List[str]] = None, tags_any: Optional[List[str]] = None, 
             priority_tags: Optional[List[str]] = None, boost: float = 1.5) -> List[Document]:
        try:
            # --- Backward compatibility ---
            if tags and not tags_all:
                tags_all = tags

            # --- Tag Filtering Logic ---
            candidate_ids = set(self.document_ids) # Start with all documents

            # Filter by tags_all (AND logic)
            if tags_all:
                all_candidates = set()
                # Get the intersection of documents for all tags in tags_all
                initial_tag = tags_all[0]
                all_candidates.update(self.tag_index.get(initial_tag, set()))
                for tag in tags_all[1:]:
                    all_candidates.intersection_update(self.tag_index.get(tag, set()))
                candidate_ids.intersection_update(all_candidates)

            # Filter by tags_any (OR logic)
            if tags_any:
                any_candidates = set()
                for tag in tags_any:
                    any_candidates.update(self.tag_index.get(tag, set()))
                
                # If tags_all was also present, we take the intersection.
                # If only tags_any is present, this becomes the candidate set.
                if tags_all:
                    candidate_ids.intersection_update(any_candidates)
                else:
                    candidate_ids = any_candidates

            if not candidate_ids:
                logger.warning("No candidates found after tag filtering.")
                return []
            
            query_vector = self.embedding_api.create_embedding(query)
            query_vector = np.array(query_vector, dtype=np.float32)
            
            # Ensure query_vector is normalized
            query_vector_norm = np.linalg.norm(query_vector)
            if query_vector_norm > 0:
                query_vector /= query_vector_norm
            
            candidate_indices = [self.document_ids.index(doc_id) for doc_id in candidate_ids]

            scores = []
            for i in candidate_indices:
                vec = self.vectors[i]
                vec = np.array(vec, dtype=np.float32)
                
                # CRITICAL FIX: Normalize document vectors before dot product
                vec_norm = np.linalg.norm(vec)
                if vec_norm > 0:
                    vec /= vec_norm
                
                similarity = np.dot(query_vector, vec)
                doc_id = self.document_ids[i]
                
                # --- Priority Boost ---
                if priority_tags and any(pt in self.documents[doc_id].tags for pt in priority_tags):
                    similarity *= boost

                scores.append((similarity, doc_id))
            
            # Sort by score descending
            scores.sort(key=lambda x: x[0], reverse=True)
            
            # Get top_k results
            top_k_results = scores[:top_k]
            
            # Filter by metadata if provided
            results = []
            for score, doc_id in top_k_results:
                doc = self.documents[doc_id]
                if metadata_filter:
                    # Safely check metadata
                    if not doc.metadata or not all(doc.metadata.get(key) == value for key, value in metadata_filter.items()):
                        continue
                results.append(doc)
            
            return results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def _rebuild_tag_index(self):
        self.tag_index = {}
        for doc_id, doc in self.documents.items():
            for tag in doc.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                self.tag_index[tag].add(doc_id)

    def _rebuild_tag_index_from_docs(self, documents: List[Union[Document, Dict]]):
        """Helper to rebuild tag index from a specific list of documents."""
        self.tag_index = {}
        for doc in documents:
            doc_id = None
            tags = []
            if isinstance(doc, Document):
                doc_id = doc.id
                tags = doc.tags
            elif isinstance(doc, dict):
                doc_id = doc.get('id')
                tags = doc.get('tags', [])

            if not doc_id or not tags:
                continue
            for tag in tags:
                if isinstance(tag, str):
                    if tag not in self.tag_index:
                        self.tag_index[tag] = set()
                    self.tag_index[tag].add(doc_id)

    def _matches_metadata_filter(self, doc_metadata: Optional[Dict], filter_criteria: Dict) -> bool:
        """
        检查文档元数据是否匹配过滤条件
        
        Args:
            doc_metadata: 文档的元数据
            filter_criteria: 过滤条件字典
            
        Returns:
            bool: 是否匹配过滤条件
        """
        if not doc_metadata or not filter_criteria:
            return True
            
        for key, expected_value in filter_criteria.items():
            if key not in doc_metadata:
                return False
            
            actual_value = doc_metadata[key]
            
            # 支持不同类型的匹配
            if isinstance(expected_value, dict):
                # 支持范围查询，如 {"importance": {"gte": 5}}
                if "gte" in expected_value and actual_value < expected_value["gte"]:
                    return False
                if "lte" in expected_value and actual_value > expected_value["lte"]:
                    return False
                if "gt" in expected_value and actual_value <= expected_value["gt"]:
                    return False
                if "lt" in expected_value and actual_value >= expected_value["lt"]:
                    return False
            else:
                # 精确匹配
                if actual_value != expected_value:
                    return False
                    
        return True

# 创建 FastAPI 应用
app = FastAPI(title="Knowledge Base API")
db = VectorDatabase()

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """搜索文档"""
    try:
        results = db.search(
            query=request.query,
            tags=request.tags,
            top_k=request.top_k if request.top_k is not None else 5,
            metadata_filter=request.metadata_filter,
            tags_all=request.tags_all,
            tags_any=request.tags_any,
            priority_tags=request.priority_tags
        )
        return SearchResponse(success=True, results=results)
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add")
async def add_document(request: Dict):
    """添加文档到知识库"""
    try:
        # 创建文档对象
        document = Document(
            id=f"doc_{int(time.time() * 1000)}_{len(db.documents)}",
            content=request["content"],
            tags=request.get("tags", []),
            metadata=request.get("metadata", {})
        )
        
        # 添加到数据库
        success = db.add_document(document)
        
        if success:
            return {"success": True, "document_id": document.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to add document")
            
    except Exception as e:
        logger.error(f"Add document error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """获取知识库统计信息"""
    try:
        stats = {
            "document_count": len(db.documents),
            "vector_count": len(db.vectors),
            "tag_count": len(db.tag_index),
            "tags": list(db.tag_index.keys()),
            "status": "running"
        }
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("KB_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
