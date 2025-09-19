#!/usr/bin/env python3
"""
上下文聚合服务 (Context Aggregation Service)

该模块作为 MCP 服务，负责动态构建包含长期记忆和角色人设的系统提示。
是应用与 MCP 服务集群交互的统一入口，实现零侵入性的记忆集成。

主要功能:
1. 并行调用角色人设服务获取原始 prompt
2. 从向量知识库检索用户相关记忆
3. 智能拼接记忆和人设，生成最终的系统提示
4. 提供记忆存储的便捷接口
"""

import asyncio
import json
import logging
import sys
import requests
from typing import List, Dict, Optional, Any
from mcp.server.fastmcp import FastMCP
from memory_processor import MemoryProcessor

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
logger = logging.getLogger("ContextAggregator")

# 创建 MCP 服务器
mcp = FastMCP("ContextAggregator")

# 全局配置
CONFIG = {
    "kb_service_url": "http://localhost:8000",  # 向量数据库工具使用8000端口
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

# 初始化记忆处理器
memory_processor = MemoryProcessor(kb_service_url=CONFIG["kb_service_url"])

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
    动态构建一个包含长期记忆和角色人设的系统提示。

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
        
        # 2. 检索用户记忆
        memories = _search_user_memories(user_id, user_query, memory_top_k)
        
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
    force_save: bool = False
) -> dict:
    """
    从对话历史中提取并存储记忆。

    Args:
        user_id: 用户唯一标识符
        conversation_history: 对话历史文本
        force_save: 是否强制保存（忽略重要性阈值）

    Returns:
        dict: 包含操作结果的字典
    """
    try:
        logger.info(f"为用户 {user_id} 处理对话记忆")
        
        # 提取记忆
        extracted_memory = memory_processor.extract_and_rate_memory(conversation_history, user_id)
        
        if not extracted_memory:
            return {
                "success": False,
                "message": "未从对话中提取到有价值的记忆",
                "memory_saved": False
            }
        
        # 检查是否需要强制保存
        if force_save or extracted_memory.importance >= 3.0:
            # 保存记忆
            success = memory_processor.save_memory(user_id, extracted_memory)
            
            return {
                "success": success,
                "message": "记忆提取并保存成功" if success else "记忆提取成功但保存失败",
                "memory_saved": success,
                "memory_content": extracted_memory.content,
                "importance": extracted_memory.importance,
                "memory_type": extracted_memory.memory_type
            }
        else:
            return {
                "success": True,
                "message": f"记忆重要性不足 ({extracted_memory.importance} < 3.0)，未保存",
                "memory_saved": False,
                "memory_content": extracted_memory.content,
                "importance": extracted_memory.importance
            }
            
    except Exception as e:
        logger.error(f"存储对话记忆时发生错误: {e}")
        return {
            "success": False,
            "message": f"处理记忆时发生错误: {str(e)}",
            "memory_saved": False
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
        
        memories = _search_user_memories(user_id, query, top_k, memory_type)
        
        # 格式化记忆用于展示
        formatted_memories = []
        for memory in memories:
            formatted_memories.append({
                "content": memory.get("content", ""),
                "importance": memory.get("metadata", {}).get("importance", 0),
                "memory_type": memory.get("metadata", {}).get("memory_type", "unknown"),
                "created_at": memory.get("metadata", {}).get("created_at", ""),
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
def get_service_status() -> dict:
    """
    获取聚合服务的状态信息。

    Returns:
        dict: 服务状态信息
    """
    try:
        # 检查知识库服务状态
        kb_status = _check_knowledge_base_status()
        
        # 检查记忆处理器状态
        memory_processor_status = memory_processor.llm_api_key is not None
        
        return {
            "service": "ContextAggregator",
            "status": "running",
            "components": {
                "knowledge_base": {
                    "status": "connected" if kb_status else "disconnected",
                    "url": CONFIG["kb_service_url"]
                },
                "memory_processor": {
                    "status": "ready" if memory_processor_status else "not_configured",
                    "llm_configured": memory_processor_status
                },
                "persona_services": list(CONFIG["persona_services"].keys())
            }
        }
        
    except Exception as e:
        logger.error(f"获取服务状态时发生错误: {e}")
        return {
            "service": "ContextAggregator",
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

def _search_user_memories(user_id: str, query: str, top_k: int, memory_type: Optional[str] = None) -> List[Dict]:
    """从知识库搜索用户记忆"""
    try:
        # 构建搜索参数，添加元数据过滤
        search_params = {
            "query": query or "用户记忆",
            "tags": ["memory"],
            "top_k": top_k,
            "metadata_filter": {"user_id": user_id}  # 关键：用户隔离
        }
        
        # 如果指定了记忆类型，添加到元数据过滤中
        if memory_type:
            search_params["metadata_filter"]["memory_type"] = memory_type
        
        # 发送搜索请求到知识库
        response = requests.post(
            f"{CONFIG['kb_service_url']}/search",
            json=search_params,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                memories = result.get("results", [])
                
                # 按重要性排序（服务端已过滤用户，这里只需排序）
                memories.sort(key=lambda x: x.get("metadata", {}).get("importance", 0), reverse=True)
                
                return memories[:top_k]
        
        logger.warning(f"搜索用户记忆失败: {response.status_code}")
        return []
        
    except Exception as e:
        logger.error(f"搜索用户记忆时发生错误: {e}")
        return []

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
        
        if importance >= 7:
            memory_groups["important"].append(content)
        elif importance >= 4:
            memory_groups["medium"].append(content)
        else:
            memory_groups["general"].append(content)
    
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
        return f"""[补充记忆上下文]
关于这位用户，请参考以下你之前的记忆：

{chr(10).join(memory_sections)}

请在对话中自然地体现这些记忆，但不要直接提及"记忆"或"我记得"等表述。"""
    
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

def test_context_aggregator():
    """测试上下文聚合器功能"""
    print("=== 上下文聚合器测试 ===")
    
    # 测试获取服务状态
    print("1. 检查服务状态...")
    status = get_service_status()
    print(f"服务状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    # 测试记忆存储
    print("\n2. 测试记忆存储...")
    test_conversation = """
用户: 我喜欢在早上喝咖啡看新闻
AI: 这是很好的习惯，咖啡能帮助提神，新闻让你了解世界。
用户: 是的，特别是我最爱喝拿铁，不加糖的那种
AI: 拿铁的奶香和咖啡的苦味平衡得很好，不加糖更能品味原味。
"""
    
    memory_result = store_conversation_memory("test_user_002", test_conversation)
    print(f"记忆存储结果: {json.dumps(memory_result, indent=2, ensure_ascii=False)}")
    
    # 测试上下文构建
    print("\n3. 测试上下文构建...")
    context_prompt = build_prompt_with_context(
        persona_name="luoluo",
        user_id="test_user_002",
        user_query="早上的习惯",
        user_name="测试用户"
    )
    print(f"构建的上下文提示:\n{context_prompt}")
    
    # 测试记忆检索
    print("\n4. 测试记忆检索...")
    memories = get_user_memories("test_user_002", "咖啡", 5)
    print(f"用户记忆: {json.dumps(memories, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    # 启动 MCP 服务
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_context_aggregator()
    else:
        logger.info("启动上下文聚合 MCP 服务...")
        mcp.run(transport="stdio")
