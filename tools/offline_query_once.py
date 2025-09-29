# -*- coding: utf-8 -*-
import json
from pathlib import Path
import sys

# Ensure project root on path
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from knowledge_base_service import VectorDatabase

def pretty(x):
    return json.dumps(x, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    db = VectorDatabase()
    query = "卡菈克 模板"
    results = db.search(query=query, top_k=5)
    out = []
    for r in results:
        doc_obj = r.get("document")
        score = float(r.get("score", 0.0))
        d = {}
        if doc_obj is not None:
            if hasattr(doc_obj, "model_dump"):
                d = doc_obj.model_dump()
            elif hasattr(doc_obj, "dict"):
                d = doc_obj.dict()
            elif isinstance(doc_obj, dict):
                d = doc_obj
        out.append({
            "id": d.get("id"),
            "tags": d.get("tags"),
            "content": (d.get("content") or "")[:120] if d else "",
            "score": round(score, 4)
        })
    print(pretty({"query": query, "count": len(out), "results": out}))
