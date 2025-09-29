# -*- coding: utf-8 -*-
"""
用 MCP 工具验证 metadata_filter 过滤：
{
  "query": "卡菈克",
  "top_k": 8,
  "metadata_filter": {
    "doc_type": {"in": ["world_knowledge", "persona_description", "source_material", "dialogue_template"]},
    "user_id": "cfy1145"
  }
}
注意：knowledge_base_service 已改为 user_id 缺省视为公共（匹配通过）。
"""
from __future__ import annotations
import asyncio
import json
import sys
import textwrap
from typing import Any, Dict, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


def to_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def extract_json(result) -> Dict[str, Any] | None:
    try:
        for c in result.content:
            if isinstance(c, TextContent):
                try:
                    return json.loads(c.text)
                except Exception:
                    continue
    except Exception:
        pass
    return None


def summarize(res: Dict[str, Any]) -> None:
    items = res.get("results") if isinstance(res, dict) else None
    if not isinstance(items, list):
        print("结构非常规：\n" + to_json(res))
        return
    for i, item in enumerate(items, 1):
        doc = item if isinstance(item, dict) else {}
        score = doc.get("score")
        doc_id = doc.get("id") or doc.get("doc_id")
        content = (doc.get("content") or "").strip()
        snippet = textwrap.shorten(content.replace("\n", " "), width=180, placeholder="...")
        if isinstance(score, (int, float)):
            print(f"{i:02d}. score={score:.4f} id={doc_id} | {snippet}")
        else:
            print(f"{i:02d}. id={doc_id} | {snippet}")


async def main() -> int:
    server_params = StdioServerParameters(
        command="python",
        args=["knowledge_base_mcp.py"],
        env={"PYTHONPATH": ".", "PYTHONIOENCODING": "utf-8"}
    )

    print("启动并连接 KnowledgeBase MCP 服务器…")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("已连接。调用 get_status …")
            status = await session.call_tool("get_status", {})
            print(to_json(extract_json(status) or {}))

            payload: Dict[str, Any] = {
                "query": "卡菈克",
                "top_k": 8,
                "metadata_filter": {
                    "doc_type": {"in": [
                        "world_knowledge",
                        "persona_description",
                        "source_material",
                        "dialogue_template"
                    ]},
                    "user_id": "cfy1145"
                }
            }
            print("\n调用 search_documents …\nPayload:")
            print(to_json(payload))
            res = await session.call_tool("search_documents", payload)
            data = extract_json(res)
            if data is None:
                print("非JSON返回：\n" + to_json(res))
                return 1
            print("\n完整返回：\n" + to_json(data))
            print("\n摘要：")
            summarize(data)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
