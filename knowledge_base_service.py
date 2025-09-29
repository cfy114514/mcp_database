from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
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
import faiss  # 导入faiss

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KnowledgeBase")

class Document(BaseModel):
    # 兼容历史字段名 doc_id
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="doc_id")
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
        self.index = None  # FAISS索引
        
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
        if self.vectors:
            self.rebuild_index()

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
                        # list: preserve order explicitly
                        self.documents = {doc['id']: Document(**doc) for doc in data if 'id' in doc}
                        self.document_ids = [doc['id'] for doc in data if 'id' in doc]
                    else:
                        # dict: fall back to key order (may not reflect vector order)
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
                loaded_vectors = np.load(str(vectors_file))
                self.vectors = [vec for vec in loaded_vectors]
                if len(self.vectors) != len(self.documents):
                    logger.warning(f"向量数量 ({len(self.vectors)}) 与文档数量 ({len(self.documents)}) 不匹配。将进行自动修复。")
                logger.info(f"成功加载 {len(self.vectors)} 个向量")
            except Exception as e:
                logger.error(f"加载向量数据时出错: {e}")
                self.vectors = []
        else:
            self.vectors = []

        # Auto-heal: if mismatch, rebuild all vectors from documents to realign order and counts
        try:
            if self.documents and (len(self.vectors) != len(self.documents)):
                logger.info("触发启动自修复：为所有文档重建向量以对齐数量与顺序…")
                ok = self.rebuild_all_vectors()
                if not ok:
                    logger.warning("自动重建失败，服务将以未对齐状态继续运行。")
        except Exception as e:
            logger.error(f"启动自修复流程出错: {e}")

        if self.vectors:
            self.rebuild_index()

    def _save_data(self):
        """保存数据到磁盘"""
        try:
            vectors_file = self.data_dir / "vectors.npy"
            docs_file = self.data_dir / "documents.json"
            
            # 始终保存文档，使用与 self.document_ids 对齐的顺序列表，确保与向量顺序一致
            ordered_docs = []
            for doc_id in self.document_ids:
                doc = self.documents.get(doc_id)
                if doc is not None:
                    ordered_docs.append(doc.model_dump())
            with open(docs_file, 'w', encoding='utf-8') as f:
                json.dump(ordered_docs, f, ensure_ascii=False)

            # 保存向量（可能为空）；不再清空文档文件
            if self.vectors:
                vectors_array = np.array(self.vectors, dtype=np.float32)
                np.save(str(vectors_file), vectors_array)
            else:
                # 若当前无向量，确保不存在旧的 vectors.npy，避免误导
                try:
                    if vectors_file.exists():
                        vectors_file.unlink()
                except Exception as e:
                    logger.warning(f"删除旧向量文件失败: {e}")
            
            logger.info(f"已保存文档 {len(ordered_docs)} 条，向量 {len(self.vectors)} 条")
        except Exception as e:
            logger.error(f"保存数据时出错: {e}")

    def _save_vectors_only(self):
        """仅保存向量到磁盘，不改写 documents.json（用于向量重建）。"""
        try:
            vectors_file = self.data_dir / "vectors.npy"
            if self.vectors:
                vectors_array = np.array(self.vectors, dtype=np.float32)
                np.save(str(vectors_file), vectors_array)
                logger.info(f"已仅保存向量 {len(self.vectors)} 条（未改写 documents.json）")
            else:
                if vectors_file.exists():
                    try:
                        vectors_file.unlink()
                    except Exception as e:
                        logger.warning(f"删除旧向量文件失败: {e}")
        except Exception as e:
            logger.error(f"仅保存向量时出错: {e}")

    def add_document(self, document: Document, save: bool = False) -> bool:
        """
        添加文档到数据库。
        注意：为了性能，默认不立即保存。
        """
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
            
            if save:
                self._save_data()
                self.rebuild_index() # 如果保存，则重建索引

            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

    def batch_add_documents(self, documents: List[Document]) -> bool:
        """批量添加文档并保存"""
        try:
            contents = [doc.content for doc in documents]
            # 假设embedding_api支持批量处理，如果不支持，则需要循环调用
            # 这里为了简化，我们循环调用
            vectors = [self.embedding_api.create_embedding(content) for content in contents]

            for i, document in enumerate(documents):
                vector = np.array(vectors[i], dtype=np.float32)
                self.vectors.append(vector)
                self.documents[document.id] = document
                self.document_ids.append(document.id)
                for tag in document.tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = set()
                    self.tag_index[tag].add(document.id)
            
            self._save_data()
            self.rebuild_index()
            logger.info(f"成功批量添加 {len(documents)} 个文档并重建索引。")
            return True
        except Exception as e:
            logger.error(f"批量添加文档时出错: {e}")
            return False

    def rebuild_index(self):
        """使用当前向量重建FAISS索引"""
        if not self.vectors:
            logger.info("没有向量可用于构建索引。")
            self.index = None
            return

        logger.info(f"开始为 {len(self.vectors)} 个向量重建FAISS索引...")
        try:
            vectors_np = np.array(self.vectors, dtype='float32')
            self.index = faiss.IndexFlatL2(self.dimension)  # 使用L2距离
            self.index.add(vectors_np)  # type: ignore[arg-type]
            logger.info(f"FAISS索引重建完成，共 {self.index.ntotal} 个向量。")
        except Exception as e:
            logger.error(f"重建FAISS索引时出错: {e}")
            self.index = None

    def rebuild_all_vectors(self):
        """为当前所有文档重建向量，确保与文档一一对应。"""
        try:
            logger.info(f"开始为 {len(self.document_ids)} 个文档全量重建向量...")
            new_vectors = []
            for doc_id in self.document_ids:
                doc = self.documents.get(doc_id)
                if not doc:
                    continue
                vec = self.embedding_api.create_embedding(doc.content)
                if isinstance(vec, str):
                    import base64, numpy as np
                    vec = np.frombuffer(base64.b64decode(vec), dtype=np.float32)
                import numpy as np
                new_vectors.append(np.array(vec, dtype=np.float32))
            self.vectors = new_vectors
            # 仅保存向量，避免覆盖较新的 documents.json
            self._save_vectors_only()
            self.rebuild_index()
            logger.info("全量重建向量完成。")
            return True
        except Exception as e:
            logger.error(f"全量重建向量失败: {e}")
            return False

    def search(self, query: str, tags: Optional[List[str]] = None, top_k: int = 5, metadata_filter: Optional[Dict] = None,
             tags_all: Optional[List[str]] = None, tags_any: Optional[List[str]] = None, 
             priority_tags: Optional[List[str]] = None, boost: float = 1.5) -> List[Dict]:
        
        if not self.index:
            logger.warning("FAISS索引未初始化，无法执行搜索。")
            return []

        try:
            # --- Backward compatibility ---
            if tags and not tags_all:
                tags_all = tags

            # --- Tag and Metadata Filtering Logic ---
            candidate_indices = self._get_filtered_indices(metadata_filter, tags_all, tags_any)
            
            if not candidate_indices:
                return []

            # --- FAISS Search ---
            query_vector = self.embedding_api.create_embedding(query)
            import numpy as np
            query_vector_np = np.array([query_vector], dtype='float32')

            # FAISS search returns distances and indices (labels)
            # We search for a larger k to account for post-filtering
            search_k = min(max(top_k * 5, top_k), self.index.ntotal)
            if search_k <= 0:
                return []
            distances, indices = self.index.search(query_vector_np, search_k)  # type: ignore[misc]

            # --- Result Processing ---
            results = []
            seen_doc_ids = set()
            candidate_id_set = {self.document_ids[i] for i in candidate_indices if i < len(self.document_ids)}

            for i in range(indices.shape[1]):
                doc_index = int(indices[0, i])
                if doc_index < 0 or doc_index >= len(self.document_ids):
                    # 越界保护：跳过非法索引
                    continue
                distance = float(distances[0, i])
                doc_id = self.document_ids[doc_index]
                if doc_id in candidate_id_set and doc_id not in seen_doc_ids:
                    doc = self.documents.get(doc_id)
                    if doc:
                        score = 1 / (1 + distance)
                        results.append({"document": doc, "score": score})
                        seen_doc_ids.add(doc_id)
                if len(results) >= top_k:
                    break
            results.sort(key=lambda x: x['score'], reverse=True)
            return results

        except Exception as e:
            logger.error(f"搜索时发生错误: {e}")
            return []

    def _get_filtered_indices(self, metadata_filter, tags_all, tags_any):
        """根据元数据和标签获取过滤后的文档索引列表"""
        candidate_ids = set(self.document_ids)

        # Metadata filtering
        if metadata_filter:
            filtered_by_meta = set()
            for doc_id, doc in self.documents.items():
                if self._matches_metadata_filter(doc.metadata, metadata_filter):
                    filtered_by_meta.add(doc_id)
            candidate_ids &= filtered_by_meta

        # Tag filtering
        if tags_all:
            doc_ids_with_all_tags = set(self.document_ids)
            for tag in tags_all:
                doc_ids_with_all_tags &= self.tag_index.get(tag, set())
            candidate_ids &= doc_ids_with_all_tags
        
        if tags_any:
            doc_ids_with_any_tag = set()
            for tag in tags_any:
                doc_ids_with_any_tag.update(self.tag_index.get(tag, set()))
            candidate_ids &= doc_ids_with_any_tag

        # Convert final doc_ids to indices for numpy array
        id_to_index = {doc_id: i for i, doc_id in enumerate(self.document_ids)}
        return [id_to_index[doc_id] for doc_id in candidate_ids if doc_id in id_to_index]

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
        if not filter_criteria:
            return True
        
        if not doc_metadata:
            return False
            
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
app = FastAPI()
db = VectorDatabase()

@app.post("/add", response_model=Dict)
async def add_document(document: Document):
    success = db.add_document(document, save=True) # 为了简单，这里设为True，但在高频场景应为False
    if success:
        return {"success": True, "message": "文档已添加并立即保存和索引。"}
    else:
        raise HTTPException(status_code=500, detail="添加文档时出错")

@app.post("/batch_add", response_model=Dict)
async def batch_add_documents(documents: List[Document]):
    success = db.batch_add_documents(documents)
    if success:
        return {"success": True, "message": f"成功批量处理 {len(documents)} 个文档。"}
    else:
        raise HTTPException(status_code=500, detail="批量添加文档时出错")

@app.post("/search")
async def search(request: SearchRequest):
    top_k = request.top_k if request.top_k is not None else 5
    tags_all = request.tags_all or request.tags

    results = db.search(
        query=request.query,
        top_k=top_k,
        metadata_filter=request.metadata_filter,
        tags_all=tags_all,
        tags_any=request.tags_any,
        priority_tags=request.priority_tags
    )

    response_results = []
    for res in results:
        doc = res.get("document")
        score = float(res.get("score", 0.0)) if res.get("score") is not None else 0.0
        if doc is not None:
            doc_dict = doc.model_dump() if hasattr(doc, "model_dump") else doc.dict() if hasattr(doc, "dict") else doc
            response_results.append({"document": doc_dict, "score": score})

    return {"success": True, "results": response_results}

@app.post("/save", response_model=Dict)
async def save_data():
    try:
        db._save_data()
        return {"success": True, "message": "数据已成功保存到磁盘。"}
    except Exception as e:
        logger.error(f"手动保存数据时出错: {e}")
        raise HTTPException(status_code=500, detail=f"保存数据失败: {e}")

@app.post("/rebuild_index", response_model=Dict)
async def rebuild_index():
    try:
        db.rebuild_index()
        return {"success": True, "message": "FAISS索引已成功重建。"}
    except Exception as e:
        logger.error(f"手动重建索引时出错: {e}")
        raise HTTPException(status_code=500, detail=f"重建索引失败: {e}")

@app.get("/")
async def root():
    return {"status": "ok", "service": "knowledge_base_service"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/stats")
async def stats():
    try:
        return {
            "vectors": len(db.vectors),
            "documents": len(db.documents),
            "doc_ids": len(db.document_ids),
            "index_ntotal": db.index.ntotal if db.index is not None else 0,
            "mismatch": len(db.vectors) != len(db.documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rebuild_all_vectors", response_model=Dict)
async def rebuild_all_vectors():
    ok = db.rebuild_all_vectors()
    if ok:
        return {"success": True, "message": "已为所有文档重建向量并重建索引。"}
