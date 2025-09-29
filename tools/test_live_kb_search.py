# -*- coding: utf-8 -*-
"""
Live test script for Knowledge Base service (port 8001).
- Checks /health and /stats
- Executes /search with UTF-8 headers and prints readable Chinese

Usage examples:
  python tools/test_live_kb_search.py
  python tools/test_live_kb_search.py --query "卡菈克 基本信息" --tags role:karlach --top-k 5
  python tools/test_live_kb_search.py --url http://127.0.0.1:8001 --user-id dev-local

Requires: requests
"""
from __future__ import annotations
import argparse
import json
import sys
import textwrap
import time
from typing import List, Optional

import requests

DEFAULT_URL = "http://127.0.0.1:8001"


def _print_json(title: str, data: object, max_len: int = 0) -> None:
    print(f"\n=== {title} ===")
    if max_len and isinstance(data, (dict, list)):
        s = json.dumps(data, ensure_ascii=False, indent=2)
        if len(s) > max_len:
            s = s[: max_len - 3] + "..."
        print(s)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


def _get(url: str, path: str, timeout: float = 10.0) -> requests.Response:
    r = requests.get(f"{url}{path}", timeout=timeout)
    r.raise_for_status()
    # Respect server-declared encoding, fallback to utf-8
    if not r.encoding:
        r.encoding = "utf-8"
    return r


def _post_json(url: str, path: str, payload: dict, timeout: float = 20.0) -> requests.Response:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    r = requests.post(f"{url}{path}", headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), timeout=timeout)
    r.raise_for_status()
    if not r.encoding:
        r.encoding = "utf-8"
    return r


def run(url: str, query: str, top_k: int, tags_all: List[str], user_id: Optional[str]) -> int:
    print(f"Target KB URL: {url}")

    # 1) health
    try:
        r = _get(url, "/health")
        _print_json("/health", r.json())
        ct = r.headers.get("Content-Type", "")
        print(f"Content-Type: {ct}")
    except Exception as e:
        print(f"ERROR calling /health: {e}")
        return 1

    # 2) stats
    try:
        r = _get(url, "/stats")
        stats = r.json()
        _print_json("/stats", stats)
    except Exception as e:
        print(f"ERROR calling /stats: {e}")
        return 1

    # 3) search
    payload = {
        "query": query,
        "top_k": top_k,
    }
    if tags_all:
        payload["tags_all"] = tags_all
    if user_id:
        payload["metadata_filter"] = {"user_id": user_id}

    print("\nRequest payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    try:
        r = _post_json(url, "/search", payload)
    except Exception as e:
        print(f"ERROR calling /search: {e}")
        return 1

    # Confirm content-type carries charset
    ct = r.headers.get("Content-Type", "")
    print(f"\n/search Content-Type: {ct}")

    try:
        data = r.json()
    except Exception:
        # If JSON decoding fails, print raw text for diagnosis
        print("Raw response text (truncated 2KB):")
        print(r.text[:2048])
        return 1

    # Pretty print results with readable Chinese
    _print_json("/search results (raw)", data, max_len=0)

    # Summarized view
    print("\n=== /search summary ===")
    results_list = None
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        results_list = data["results"]
    elif isinstance(data, list):
        results_list = data

    if isinstance(results_list, list):
        for i, item in enumerate(results_list, 1):
            doc = item.get("document", {}) if isinstance(item, dict) else {}
            score = item.get("score") if isinstance(item, dict) else None
            doc_id = doc.get("id") or doc.get("doc_id")
            content = (doc.get("content") or "").strip()
            snippet = textwrap.shorten(content.replace("\n", " "), width=180, placeholder="...")
            if isinstance(score, (int, float)):
                print(f"{i:02d}. score={score:.4f} id={doc_id} | {snippet}")
            else:
                print(f"{i:02d}. id={doc_id} | {snippet}")
    else:
        print("Unexpected response structure; expected a list or an object with 'results'.")

    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Live test for KB service (8001)")
    parser.add_argument("--url", default=DEFAULT_URL, help="KB base URL, default http://127.0.0.1:8001")
    parser.add_argument("--query", default="卡菈克 基本信息", help="Search query text")
    parser.add_argument("--top-k", type=int, default=5, dest="top_k", help="Top K to request from KB")
    parser.add_argument("--tags", nargs="*", default=["role:karlach"], help="tags_all filter values")
    parser.add_argument("--user-id", default=None, help="Optional metadata_filter.user_id")
    args = parser.parse_args(argv)

    try:
        return run(args.url, args.query, args.top_k, args.tags, args.user_id)
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
