from typing import List, Optional, Dict
import requests
from mcp.server.fastmcp import FastMCP
import logging
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorDB")

# 知识库服务配置
KB_HOST = os.getenv("KB_HOST", "http://localhost:8000")

# 创建 MCP 服务器
mcp = FastMCP("VectorDB")

@mcp.tool()
def search_documents(query: str, tags: Optional[List[str]] = None, top_k: int = 5) -> dict:
    """搜索文档"""
    try:
        response = requests.post(
            f"{KB_HOST}/search",
            json={
                "query": query,
                "tags": tags,
                "top_k": top_k
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error calling knowledge base API: {str(e)}")
        return {
            "success": False,
            "results": [],
            "message": f"Error: {str(e)}"
        }

# 启动服务器
if __name__ == "__main__":
    mcp.run(transport="stdio")
