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
    tags: Optional[List[str]] = None
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
    def __init__(self, dimension: int = 1024):
        self.embedding_api = EmbeddingAPI()
        self.dimension = dimension
        self.vectors = []
        self.documents = {}
        self.document_ids = []
        self.tag_index = {}
        
        # 使用项目根目录的 data 文件夹
        # 通过查找 mcp_config.json 确定项目根目录
        current_dir = Path(__file__).parent
        while current_dir.parent != current_dir:  # 向上查找，直到到达根目录
            if (current_dir / "mcp_config.json").exists():
                break
            current_dir = current_dir.parent
        self.data_dir = current_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        self._load_data()

    def _load_data(self):
        vectors_file = self.data_dir / "vectors.npy"
        docs_file = self.data_dir / "documents.json"
        
        if vectors_file.exists() and docs_file.exists():
            try:
                # 加载向量数据
                loaded_vectors = np.load(str(vectors_file))
                self.vectors = [vec for vec in loaded_vectors]  # 转换为列表
                
                # 加载文档数据
                with open(docs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = {k: Document(**v) for k, v in data.items()}
                    self.document_ids = list(self.documents.keys())
                    self._rebuild_tag_index()
                
                logger.info(f"成功加载 {len(self.vectors)} 个向量和 {len(self.documents)} 个文档")
            except Exception as e:
                logger.error(f"加载数据时出错: {e}")
                # 如果加载失败，初始化空数据
                self.vectors = []
                self.documents = {}
                self.document_ids = []
                self.tag_index = {}

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

    def search(self, query: str, tags: Optional[List[str]] = None, top_k: int = 5, metadata_filter: Optional[Dict] = None) -> List[Document]:
        try:
            candidate_ids = None
            if tags:
                for tag in tags:
                    if tag in self.tag_index:
                        if candidate_ids is None:
                            candidate_ids = self.tag_index[tag].copy()
                        else:
                            candidate_ids &= self.tag_index[tag]
                
                if not candidate_ids:
                    return []
            
            query_vector = self.embedding_api.create_embedding(query)
            
            # 确保query_vector是numpy数组
            query_vector = np.array(query_vector, dtype=np.float32)
            
            # 标准化查询向量
            query_vector_norm = np.linalg.norm(query_vector)
            if query_vector_norm > 0:
                query_vector = query_vector / query_vector_norm
            
            scores = []
            for i, vec in enumerate(self.vectors):
                # 确保文档向量也是标准化的
                vec = np.array(vec, dtype=np.float32)
                vec_norm = np.linalg.norm(vec)
                if vec_norm > 0:
                    vec = vec / vec_norm
                
                # 计算余弦相似度
                similarity = np.dot(query_vector, vec)
                doc_id = self.document_ids[i]
                
                # 检查候选文档集合（基于标签过滤）
                if candidate_ids is not None and doc_id not in candidate_ids:
                    continue
                
                # 检查元数据过滤
                if metadata_filter:
                    doc = self.documents[doc_id]
                    if not self._matches_metadata_filter(doc.metadata, metadata_filter):
                        continue
                
                scores.append((similarity, i))
            
            scores.sort(reverse=True)
            results = []
            for similarity, idx in scores[:top_k]:
                doc_id = self.document_ids[idx]
                results.append(self.documents[doc_id])
            
            return results
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def _rebuild_tag_index(self):
        self.tag_index = {}
        for doc_id, doc in self.documents.items():
            for tag in doc.tags:
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
            metadata_filter=request.metadata_filter
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
