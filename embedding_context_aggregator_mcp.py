#!/usr/bin/env python3
"""
基于Embedding的上下文聚合服务
不依赖LLM，仅使用embedding模型实现记忆处理和上下文构建
"""

import asyncio
import json
import logging
import sys
import requests
from typing import List, Dict, Optional, Any
from mcp.server.fastmcp import FastMCP
from embedding_memory_processor import EmbeddingMemoryProcessor

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EmbeddingContextAggregator")

# 创建 MCP 服务器
mcp = FastMCP("EmbeddingContextAggregator")

# 全局配置
CONFIG = {
    "kb_service_url": "http://localhost:8001",
    "persona_services": {
        "uozumi": {
            "server_name": "persona-uozumi",
            "system_prompt_tool": "get_uozumi_system_prompt"
        },
        "luoluo": {
            "server_name": "persona-uozumi",  # 已合并到 uozumi 服务
            "system_prompt_tool": "get_luoluo_system_prompt"
        }
    }
}

# 初始化基于Embedding的记忆处理器
memory_processor = EmbeddingMemoryProcessor(kb_service_url=CONFIG["kb_service_url"])

@mcp.tool()
def build_prompt_with_context(
    persona_name: str,
    user_id: str,
    user_query: str = "",
    memory_top_k: int = 3,
    user_name: str = "用户",
    char_name: Optional[str] = None
) -> str:
    """
    使用embedding模型动态构建包含长期记忆的系统提示。

    Args:
        persona_name: 角色名称 (e.g., 'uozumi', 'luoluo')
        user_id: 用户唯一标识符
        user_query: 用户当前的查询，用于记忆相关性搜索（可选）
        memory_top_k: 检索记忆的数量
        user_name: 用户名称，用于替换 {{user}} 占位符
        char_name: 角色名称，用于替换 {{char}} 占位符（如果不提供，使用 persona_name）

    Returns:
        str: 组装完成的最终 System Prompt 字符串
    """
    try:
        logger.info(f"为用户 {user_id} 构建 {persona_name} 角色的上下文提示")
        
        # 设置默认角色名
        if char_name is None:
            char_name_map = {
                "uozumi": "仓桥卯月",
                "luoluo": "络络"
            }
            char_name = char_name_map.get(persona_name, persona_name)
        
        # 1. 获取原始角色提示
        original_prompt = _get_persona_prompt(persona_name, user_name, char_name)
        
        # 2. 使用embedding检索用户记忆
        memories = memory_processor.search_memories(user_id, user_query, memory_top_k)
        
        # 3. 格式化记忆内容
        memory_section = _format_memories_as_supplement(memories)
        
        # 4. 智能拼接最终提示
        final_prompt = _combine_prompt_and_memories(original_prompt, memory_section)
        
        logger.info(f"成功构建上下文提示，包含 {len(memories)} 条记忆")
        return final_prompt
        
    except Exception as e:
        logger.error(f"构建上下文提示时发生错误: {e}")
        # 回退到原始提示
        try:
            return _get_persona_prompt(persona_name, user_name, char_name)
        except:
            return f"错误：无法获取 {persona_name} 角色提示"

@mcp.tool()
def store_conversation_memory(
    user_id: str,
    conversation_history: str,
    min_importance: float = 3.0
) -> dict:
    """
    使用embedding模型从对话历史中提取并存储记忆。

    Args:
        user_id: 用户唯一标识符
        conversation_history: 对话历史文本
        min_importance: 最低重要性阈值（1-10）

    Returns:
        dict: 包含操作结果的字典
    """
    try:
        logger.info(f"为用户 {user_id} 处理对话记忆")
        
        # 使用embedding处理器提取并保存记忆
        result = memory_processor.process_and_save_conversation(
            conversation_history, 
            user_id, 
            min_importance
        )
        
        return result
            
    except Exception as e:
        logger.error(f"存储对话记忆时发生错误: {e}")
        return {
            "success": False,
            "message": f"处理记忆时发生错误: {str(e)}",
            "memories_saved": 0
        }

@mcp.tool()
def get_user_memories(
    user_id: str,
    query: str = "",
    top_k: int = 10,
    memory_type: Optional[str] = None
) -> dict:
    """
    获取用户的历史记忆。

    Args:
        user_id: 用户唯一标识符
        query: 搜索查询（可选）
        top_k: 返回的记忆数量
        memory_type: 记忆类型过滤（可选）

    Returns:
        dict: 包含记忆列表的字典
    """
    try:
        logger.info(f"检索用户 {user_id} 的记忆，查询: '{query}'")
        
        memories = memory_processor.search_memories(user_id, query, top_k, memory_type)
        
        # 格式化记忆用于展示
        formatted_memories = []
        for memory in memories:
            formatted_memories.append({
                "content": memory.get("content", ""),
                "importance": memory.get("metadata", {}).get("importance", 0),
                "memory_type": memory.get("metadata", {}).get("memory_type", "unknown"),
                "created_at": memory.get("metadata", {}).get("created_at", ""),
                "keywords": memory.get("metadata", {}).get("keywords", []),
                "tags": memory.get("tags", [])
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "total_memories": len(formatted_memories),
            "memories": formatted_memories
        }
        
    except Exception as e:
        logger.error(f"检索用户记忆时发生错误: {e}")
        return {
            "success": False,
            "message": f"检索记忆时发生错误: {str(e)}",
            "memories": []
        }

@mcp.tool()
def analyze_conversation_insights(
    user_id: str,
    conversation_history: str
) -> dict:
    """
    分析对话获得用户洞察，不保存记忆。

    Args:
        user_id: 用户唯一标识符
        conversation_history: 对话历史文本

    Returns:
        dict: 包含分析结果的字典
    """
    try:
        logger.info(f"分析用户 {user_id} 的对话洞察")
        
        # 提取记忆片段但不保存
        memories = memory_processor.process_conversation_memories(conversation_history, user_id)
        
        # 分析结果
        insights = {
            "memory_segments": len(memories),
            "memory_types": {},
            "importance_distribution": {"high": 0, "medium": 0, "low": 0},
            "key_topics": [],
            "average_importance": 0
        }
        
        total_importance = 0
        all_keywords = []
        
        for memory in memories:
            # 统计记忆类型
            mem_type = memory.memory_type
            insights["memory_types"][mem_type] = insights["memory_types"].get(mem_type, 0) + 1
            
            # 统计重要性分布
            if memory.importance >= 7:
                insights["importance_distribution"]["high"] += 1
            elif memory.importance >= 4:
                insights["importance_distribution"]["medium"] += 1
            else:
                insights["importance_distribution"]["low"] += 1
            
            total_importance += memory.importance
            all_keywords.extend(memory.keywords or [])
        
        # 计算平均重要性
        if memories:
            insights["average_importance"] = total_importance / len(memories)
        
        # 提取关键主题（高频关键词）
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # 按频率排序，取前5个
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        insights["key_topics"] = [kw for kw, freq in top_keywords]
        
        return {
            "success": True,
            "user_id": user_id,
            "insights": insights,
            "detailed_memories": [
                {
                    "content": mem.content[:100] + "..." if len(mem.content) > 100 else mem.content,
                    "type": mem.memory_type,
                    "importance": mem.importance,
                    "keywords": mem.keywords
                }
                for mem in memories
            ]
        }
        
    except Exception as e:
        logger.error(f"分析对话洞察时发生错误: {e}")
        return {
            "success": False,
            "message": f"分析对话时发生错误: {str(e)}"
        }

@mcp.tool()
def get_service_status() -> dict:
    """
    获取基于Embedding的聚合服务状态信息。

    Returns:
        dict: 服务状态信息
    """
    try:
        # 检查知识库服务状态
        kb_status = _check_knowledge_base_status()
        
        # 检查embedding API状态
        embedding_status = memory_processor.api_key is not None
        
        return {
            "service": "EmbeddingContextAggregator",
            "status": "running",
            "components": {
                "knowledge_base": {
                    "status": "connected" if kb_status else "disconnected",
                    "url": CONFIG["kb_service_url"]
                },
                "embedding_processor": {
                    "status": "ready" if embedding_status else "not_configured",
                    "api_configured": embedding_status,
                    "model": memory_processor.model
                },
                "persona_services": list(CONFIG["persona_services"].keys())
            },
            "features": {
                "llm_free": True,
                "embedding_based": True,
                "automatic_memory_extraction": True,
                "importance_scoring": True,
                "memory_type_classification": True
            }
        }
        
    except Exception as e:
        logger.error(f"获取服务状态时发生错误: {e}")
        return {
            "service": "EmbeddingContextAggregator",
            "status": "error",
            "message": str(e)
        }

def _get_persona_prompt(persona_name: str, user_name: str, char_name: Optional[str]) -> str:
    """
    获取指定角色的系统提示
    
    注意：这里模拟 MCP 服务调用，实际部署时需要通过 MCP 客户端调用
    """
    try:
        persona_config = CONFIG["persona_services"].get(persona_name)
        if not persona_config:
            raise ValueError(f"未知的角色名称: {persona_name}")
        
        # 模拟调用角色服务的逻辑
        # 在实际部署中，这里应该通过 MCP 客户端调用其他服务
        logger.warning("当前为模拟模式，实际部署时需要配置 MCP 客户端调用")
        
        # 返回基础提示（实际应从角色服务获取）
        base_prompts = {
            "uozumi": f"你是{char_name}，一个AI助手。用户是{user_name}。",
            "luoluo": f"你是{char_name}，一个仿生人AI。用户{user_name}是你的创造者。"
        }
        
        return base_prompts.get(persona_name, f"你是{char_name}，用户是{user_name}。")
        
    except Exception as e:
        logger.error(f"获取角色提示时发生错误: {e}")
        return f"你是{char_name}，用户是{user_name}。"

def _format_memories_as_supplement(memories: List[Dict]) -> str:
    """将记忆列表格式化为补充说明文本"""
    if not memories:
        return ""
    
    # 按重要性和类型分组记忆
    memory_groups = {
        "important": [],  # 重要性 >= 7
        "medium": [],     # 重要性 4-6
        "general": []     # 其他
    }
    
    for memory in memories:
        content = memory.get("content", "")
        importance = memory.get("metadata", {}).get("importance", 0)
        memory_type = memory.get("metadata", {}).get("memory_type", "general")
        
        # 添加类型标识
        content_with_type = f"[{memory_type}] {content}"
        
        if importance >= 7:
            memory_groups["important"].append(content_with_type)
        elif importance >= 4:
            memory_groups["medium"].append(content_with_type)
        else:
            memory_groups["general"].append(content_with_type)
    
    # 构建记忆文本
    memory_sections = []
    
    if memory_groups["important"]:
        important_items = "\n".join([f"• {item}" for item in memory_groups["important"]])
        memory_sections.append(f"**重要记忆**:\n{important_items}")
    
    if memory_groups["medium"]:
        medium_items = "\n".join([f"• {item}" for item in memory_groups["medium"]])
        memory_sections.append(f"**相关记忆**:\n{medium_items}")
    
    if memory_groups["general"]:
        general_items = "\n".join([f"• {item}" for item in memory_groups["general"][:2]])  # 限制一般记忆数量
        memory_sections.append(f"**其他记忆**:\n{general_items}")
    
    if memory_sections:
        return f"""[智能记忆上下文]
基于语义分析，以下是关于这位用户的相关记忆：

{chr(10).join(memory_sections)}

请在对话中自然地体现这些记忆，展现你对用户的了解。"""
    
    return ""

def _combine_prompt_and_memories(original_prompt: str, memory_section: str) -> str:
    """智能拼接原始提示和记忆内容"""
    if memory_section:
        return f"{memory_section}\n\n---\n\n{original_prompt}"
    else:
        return original_prompt

def _check_knowledge_base_status() -> bool:
    """检查知识库服务状态"""
    try:
        response = requests.get(f"{CONFIG['kb_service_url']}/stats", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_embedding_context_aggregator():
    """测试基于Embedding的上下文聚合器功能"""
    print("=== 基于Embedding的上下文聚合器测试 ===")
    
    # 测试获取服务状态
    print("1. 检查服务状态...")
    status = get_service_status()
    print(f"服务状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    # 测试记忆存储
    print("\n2. 测试记忆存储...")
    test_conversation = """
用户: 我特别喜欢在周末去咖啡店工作，那里的环境很安静
AI: 咖啡店确实是很好的工作环境，有轻松的氛围。
用户: 是的，我在北京朝阳区有一家常去的咖啡店，叫蓝调咖啡
AI: 听起来是个不错的地方，有固定的工作场所很重要。
用户: 我通常点美式咖啡，加一点牛奶，不加糖
AI: 这样的搭配既能品味咖啡原味，又不会太苦。
    """
    
    memory_result = store_conversation_memory("test_user_004", test_conversation)
    print(f"记忆存储结果: {json.dumps(memory_result, indent=2, ensure_ascii=False)}")
    
    # 测试对话分析
    print("\n3. 测试对话分析...")
    insights = analyze_conversation_insights("test_user_004", test_conversation)
    print(f"对话洞察: {json.dumps(insights, indent=2, ensure_ascii=False)}")
    
    # 测试上下文构建
    print("\n4. 测试上下文构建...")
    context_prompt = build_prompt_with_context(
        persona_name="luoluo",
        user_id="test_user_004",
        user_query="咖啡和工作",
        user_name="测试用户"
    )
    print(f"构建的上下文提示:\n{context_prompt}")
    
    # 测试记忆检索
    print("\n5. 测试记忆检索...")
    memories = get_user_memories("test_user_004", "咖啡店工作", 5)
    print(f"用户记忆: {json.dumps(memories, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    # 启动 MCP 服务
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_embedding_context_aggregator()
    else:
        logger.info("启动基于Embedding的上下文聚合 MCP 服务...")
        mcp.run(transport="stdio")
