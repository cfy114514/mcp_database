#!/usr/bin/env python3
"""
MCP 客户端演示脚本 - 使用 MCP 协议调用知识库工具
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

async def main():
    # 配置 MCP 服务器参数
    server_params = StdioServerParameters(
        command="python",
        args=["knowledge_base_mcp.py"],
        env={"PYTHONPATH": "."}
    )

    print("连接到 MCP 服务器...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()

            print("MCP 连接成功！")
            # print("可用工具:", [tool.name for tool in await session.list_tools()])

            # 测试搜索工具
            print("\n=== 测试搜索功能 ===")

            # 调用 search_similar 工具
            result = await session.call_tool("search_similar", {
                "user_id": "demo_user",
                "query": "MCP 记忆系统",
                "limit": 3
            })

            print("搜索结果:")
            for content in result.content:
                if isinstance(content, TextContent):
                    print(content.text)
                else:
                    print(f"非文本内容: {type(content)} - {content}")

            # 调用 get_user_memories 工具
            print("\n=== 测试获取用户记忆 ===")

            memories = await session.call_tool("get_user_memories", {
                "user_id": "demo_user",
                "top_k": 2
            })

            print("用户记忆:")
            print(json.dumps(memories.content, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
