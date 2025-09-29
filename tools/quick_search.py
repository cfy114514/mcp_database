#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick offline search tester for the local VectorDatabase.
Usage:
  python tools/quick_search.py "地狱引擎" "narrator_move" "戴蒙"
If no args provided, uses a default query set.
"""
# 加入仓库根到 sys.path，避免在某些环境下 import 失败
import sys, json, re, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_base_service import VectorDatabase


def clean_snippet(text: str, max_len: int = 160) -> str:
    t = text.strip()
    # Heuristic: if it's JSON-like, try extract Chinese content or values of "content"/"reply"/"title"
    if t.startswith('{') or t.startswith('['):
        # Try find "content": "..."
        m = re.search(r'"content"\s*:\s*"([^"]{10,})"', t)
        if m:
            t = m.group(1)
        else:
            # Try find "reply": "..." or "title": "..."
            m = re.search(r'"reply"\s*:\s*"([^"]{10,})"', t) or re.search(r'"title"\s*:\s*"([^"]{6,})"', t)
            if m:
                t = m.group(1)
    # Collapse newlines/spaces
    t = re.sub(r'\s+', ' ', t)
    # Trim
    if len(t) > max_len:
        t = t[:max_len] + '…'
    return t


def main():
    queries = sys.argv[1:] or ['地狱引擎', 'narrator_move', '戴蒙', '模板 冷却', '卡菈克 基本信息']
    db = VectorDatabase()
    for q in queries:
        res = db.search(q, top_k=8)
        rows = []
        for r in res:
            doc = r['document']
            score = float(r['score'])
            rows.append({
                'id': doc.id,
                'score': round(score, 4),
                'snippet': clean_snippet(doc.content)
            })
        print('QUERY:', q)
        print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
