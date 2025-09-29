# -*- coding: utf-8 -*-
import json
import sys
import time
from typing import Any, Dict

import requests

BASE_URL = "http://localhost:8100"
USER_ID = "dev-local-8100-demo"


def pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def get(path: str):
    return requests.get(f"{BASE_URL}{path}", timeout=10)


def post(path: str, payload: Dict):
    return requests.post(f"{BASE_URL}{path}", json=payload, timeout=30)


def main():
    print("=== 1) 健康检查 ===")
    try:
        r = get("/health")
        print("/health:", r.status_code, r.text)
    except Exception as e:
        print("无法连接 8100 服务:", e)
        print("请确认 knowledge_base_service.py 已在 8100 端口运行。")
        sys.exit(1)

    r = get("/stats")
    print("/stats:", r.status_code, pretty(r.json() if r.ok else {"error": r.text}))

    print("\n=== 2) 添加示例文档 ===")
    doc = {
        "doc_id": f"demo_{int(time.time())}",
        "content": "银河系探索指南：包含星际航行、轨道力学与推进技术要点。",
        "tags": ["demo", "space", "guide"],
        "metadata": {
            "user_id": USER_ID,
            "domain": "space-tech",
            "importance": 6.2
        }
    }
    r = post("/add", doc)
    print("/add:", r.status_code, pretty(r.json() if r.ok else {"error": r.text}))

    print("\n=== 2.1) 重建索引 ===")
    r = post("/rebuild_index", {})
    print("/rebuild_index:", r.status_code, pretty(r.json() if r.ok else {"error": r.text}))

    print("\n=== 3) 语义检索（按 user_id 隔离） ===")
    search_body = {
        "query": "轨道力学 推进 技术",
        "top_k": 3,
        "metadata_filter": {"user_id": USER_ID}
    }
    r = post("/search", search_body)
    if not r.ok:
        print("/search:", r.status_code, r.text)
        sys.exit(1)
    data = r.json()
    print("/search:", r.status_code)
    # 只打印精简字段
    simplified = []
    for item in data.get("results", []):
        doc = (item or {}).get("document", {})
        simplified.append({
            "content": doc.get("content", "")[:80],
            "tags": doc.get("tags", []),
            "user_id": (doc.get("metadata") or {}).get("user_id"),
            "score": item.get("score")
        })
    print(pretty({"success": data.get("success"), "results": simplified}))


if __name__ == "__main__":
    main()
