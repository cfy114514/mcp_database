# -*- coding: utf-8 -*-
"""
MCP 客户端：直接调用 KnowledgeBase MCP 工具进行连通性与检索测试。

用法：
  python tools/test_mcp_kb_tool.py
  python tools/test_mcp_kb_tool.py --query "卡菈克 基本信息" --tags role:karlach --top-k 5
"""
from __future__ import annotations
import asyncio
import json
import sys
import argparse
import textwrap
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


def to_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def extract_json_from_tool_result(result) -> Optional[Dict[str, Any]]:
    # 尝试从 result.content 中提取 JSON 对象
    try:
        for c in result.content:
            if isinstance(c, TextContent):
                txt = c.text
                try:
                    return json.loads(txt)
                except Exception:
                    # 不是 JSON 文本，跳过
                    continue
        # 有些实现可能直接给 Python 对象（罕见），做个兜底
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    return None


def summarize_results(data: Dict[str, Any]) -> None:
    print("\n=== 摘要 ===")
    items: Optional[List[Dict[str, Any]]] = None
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        items = data["results"]
    elif isinstance(data, list):
        items = data

    if not isinstance(items, list):
        print("结果结构非常规，原样展示：")
        print(to_json(data))
        return

    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            # 扁平化结果（id/content/tags/score 在顶层）
            if "id" in item or "content" in item:
                doc = item
                score = item.get("score")
            else:
                # 兼容嵌套结构 {document, score}
                doc = item.get("document", {})
                score = item.get("score")
        else:
            doc = {}
            score = None
        doc_id = doc.get("id") or doc.get("doc_id")
        content = (doc.get("content") or "").strip()
        snippet = textwrap.shorten(content.replace("\n", " "), width=180, placeholder="...")
        if isinstance(score, (int, float)):
            print(f"{i:02d}. score={score:.4f} id={doc_id} | {snippet}")
        else:
            print(f"{i:02d}. id={doc_id} | {snippet}")


def _tool_names(tools_any: Any) -> List[str]:
    names: List[str] = []
    try:
        for t in tools_any or []:
            name = None
            if isinstance(t, dict):
                name = t.get("name") or t.get("tool")
            if name is None:
                name = getattr(t, "name", None)
            if name is None:
                name = str(t)
            names.append(name)
    except Exception:
        pass
    return names


async def run(query: str, tags_all: List[str], top_k: int, metadata_filter: Optional[Dict[str, Any]]) -> int:
    server_params = StdioServerParameters(
        command="python",
        args=["knowledge_base_mcp.py"],
        env={"PYTHONPATH": ".", "PYTHONIOENCODING": "utf-8"}
    )

    print("启动并连接 KnowledgeBase MCP 服务器…")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("已连接。列出工具（原始）：")
            tools = await session.list_tools()
            print(to_json(tools))
            print("工具名：")
            print(to_json(_tool_names(tools)))

            print("\n调用 get_stats …")
            stats_res = await session.call_tool("get_stats", {})
            stats_json = extract_json_from_tool_result(stats_res)
            print(to_json(stats_json if stats_json is not None else stats_res))

            print("\n调用 get_status …")
            status_res = await session.call_tool("get_status", {})
            status_json = extract_json_from_tool_result(status_res)
            print(to_json(status_json if status_json is not None else status_res))

            print("\n调用 search_documents …（将被工具端强制裁剪至最多3条）")
            payload: Dict[str, Any] = {"query": query, "top_k": top_k}
            if tags_all:
                payload["tags_all"] = tags_all
            if metadata_filter:
                payload["metadata_filter"] = metadata_filter
            res = await session.call_tool("search_documents", payload)
            res_json = extract_json_from_tool_result(res)
            if res_json is None:
                print("原始返回（非JSON）：")
                print(to_json(res))
                return 0

            print("完整返回：")
            print(to_json(res_json))
            summarize_results(res_json)

    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Test KnowledgeBase MCP tool")
    parser.add_argument("--query", default="卡菈克 基本信息")
    parser.add_argument("--tags", nargs="*", default=["role:karlach"], help="tags_all")
    parser.add_argument("--top-k", type=int, default=5, dest="top_k")
    parser.add_argument("--metadata-filter", dest="metadata_filter", default=None, help="JSON for metadata_filter")
    args = parser.parse_args(argv)

    metadata_filter: Optional[Dict[str, Any]] = None
    if args.metadata_filter:
        try:
            metadata_filter = json.loads(args.metadata_filter)
        except Exception as e:
            print(f"metadata_filter JSON 解析失败: {e}")
            metadata_filter = None

    try:
        return asyncio.run(run(args.query, args.tags, args.top_k, metadata_filter))
    except KeyboardInterrupt:
        print("Interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
