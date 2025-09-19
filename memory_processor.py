#!/usr/bin/env python3
"""
记忆处理服务 (Memory Processing Service)

该模块负责从对话历史中提取有价值的记忆信息，并将其存储到向量知识库中。
主要功能:
1. 调用大语言模型从对话中提取结构化记忆
2. 对记忆进行重要性评分
3. 将记忆以特定格式存储到知识库
"""

import json
import logging
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MemoryProcessor")

@dataclass
class ExtractedMemory:
    """提取的记忆数据结构"""
    content: str
    importance: float
    memory_type: str
    emotional_valence: Optional[float] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = ["memory"]

class MemoryProcessor:
    """记忆处理器核心类"""
    
    def __init__(self, 
                 llm_api_key: Optional[str] = None,
                 llm_api_base: Optional[str] = None,
                 llm_model: str = "gpt-3.5-turbo",
                 kb_service_url: str = "http://localhost:8000"):
        """
        初始化记忆处理器
        
        Args:
            llm_api_key: LLM API 密钥（如果未提供，从环境变量 LLM_API_KEY 获取）
            llm_api_base: LLM API 基础URL（如果未提供，从环境变量 LLM_API_BASE 获取）
            llm_model: 使用的模型名称
            kb_service_url: 知识库 HTTP 服务的 URL
        """
        # 从环境变量或参数获取配置
        self.llm_api_key = llm_api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.llm_api_base = llm_api_base or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.llm_model = llm_model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        # 知识库服务配置 - 支持环境变量配置
        if kb_service_url == "http://localhost:8000":  # 使用默认值时，检查环境变量
            kb_host = os.getenv("KB_HOST", "localhost")
            kb_port = os.getenv("KB_PORT", "8001")  # 更新默认端口为8001
            self.kb_service_url = f"http://{kb_host}:{kb_port}"
        else:
            self.kb_service_url = kb_service_url.rstrip('/')
        
        # 记忆处理配置
        self.importance_threshold = float(os.getenv("MEMORY_IMPORTANCE_THRESHOLD", "3.0"))
        
        if not self.llm_api_key:
            logger.warning("未设置 LLM API 密钥，记忆提取功能将不可用")
        
        logger.info(f"记忆处理器初始化 - 模型: {self.llm_model}, 知识库: {self.kb_service_url}")
    
    def extract_and_rate_memory(self, conversation_history: str, user_id: Optional[str] = None) -> Optional[ExtractedMemory]:
        """
        从对话历史中提取单条记忆并进行重要性评分
        
        Args:
            conversation_history: 对话历史文本
            user_id: 用户ID（用于个性化记忆提取）
            
        Returns:
            ExtractedMemory 对象或 None（如果没有提取到有价值的记忆）
        """
        if not self.llm_api_key:
            logger.error("LLM API 密钥未设置，无法提取记忆")
            return None
            
        try:
            # 构建记忆提取的 Prompt
            extraction_prompt = self._build_memory_extraction_prompt(conversation_history, user_id)
            
            # 调用 LLM 提取记忆
            response = self._call_llm(extraction_prompt)
            
            if not response:
                logger.warning("LLM 未返回有效响应")
                return None
            
            # 解析 LLM 响应
            extracted_memory = self._parse_llm_response(response)
            
            if extracted_memory and extracted_memory.importance >= 3.0:  # 重要性阈值
                logger.info(f"成功提取记忆: {extracted_memory.content[:50]}... (重要性: {extracted_memory.importance})")
                return extracted_memory
            else:
                logger.debug("对话内容重要性不足，不保存为记忆")
                return None
                
        except Exception as e:
            logger.error(f"记忆提取过程中发生错误: {e}")
            return None
    
    def save_memory(self, user_id: str, memory: ExtractedMemory) -> bool:
        """
        将提取的记忆保存到知识库
        
        Args:
            user_id: 用户唯一标识符
            memory: 提取的记忆对象
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 生成唯一的文档ID
            doc_id = f"memory_{user_id}_{int(time.time() * 1000)}"
            
            # 构建元数据
            metadata = {
                "user_id": user_id,
                "importance": memory.importance,
                "memory_type": memory.memory_type,
                "created_at": datetime.now().isoformat(),
                "emotional_valence": memory.emotional_valence
            }
            
            # 确保tags包含"memory"标签
            tags = ["memory"] + [tag for tag in memory.tags if tag != "memory"]
            
            # 构建请求数据
            payload = {
                "doc_id": doc_id,
                "content": memory.content,
                "tags": tags,
                "metadata": metadata
            }
            
            # 发送到知识库 HTTP 服务
            response = requests.post(
                f"{self.kb_service_url}/add",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success", False):
                    logger.info(f"记忆保存成功: {doc_id}")
                    return True
                else:
                    logger.error(f"知识库返回失败: {result.get('message', '未知错误')}")
                    return False
            else:
                logger.error(f"HTTP 请求失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"保存记忆时发生错误: {e}")
            return False
    
    def extract_and_save_memory(self, conversation_history: str, user_id: str) -> bool:
        """
        便捷方法：提取并保存记忆的一站式操作
        
        Args:
            conversation_history: 对话历史
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        extracted_memory = self.extract_and_rate_memory(conversation_history, user_id)
        if extracted_memory:
            return self.save_memory(user_id, extracted_memory)
        return False
    
    def _build_memory_extraction_prompt(self, conversation: str, user_id: Optional[str] = None) -> str:
        """构建记忆提取的 Prompt"""
        
        user_context = f"用户ID: {user_id}" if user_id else "未知用户"
        
        prompt = f"""你是一个专门从对话中提取有价值记忆的AI助手。请分析以下对话内容，提取出最重要的记忆信息。

{user_context}

对话内容:
{conversation}

请按以下JSON格式输出提取的记忆，如果没有值得记忆的内容，请输出 {{"no_memory": true}}:

{{
    "content": "记忆的具体内容描述（用第三人称，客观描述）",
    "importance": 重要性评分(1-10，浮点数),
    "memory_type": "记忆类型（preference/event/relationship/knowledge/emotional之一）",
    "emotional_valence": 情感倾向(-1到1之间的浮点数，负数表示负面，正数表示正面，null表示中性),
    "tags": ["相关标签1", "相关标签2"]
}}

记忆提取准则:
1. 重要性评分标准:
   - 8-10: 重大事件、重要个人信息、强烈情感表达
   - 6-7: 明确的偏好表达、有意义的互动
   - 4-5: 一般信息、轻微偏好
   - 1-3: 日常对话、无特殊意义内容

2. 记忆类型说明:
   - preference: 用户偏好、习惯
   - event: 重要事件、经历
   - relationship: 人际关系、社交信息
   - knowledge: 用户分享的知识、技能
   - emotional: 情感状态、心情表达

3. 只有重要性 >= 3.0 的内容才会被保存

请仔细分析对话内容，提取最有价值的记忆信息:"""

        return prompt
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用大语言模型"""
        
        headers = {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.llm_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                f"{self.llm_api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"LLM API 调用失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"调用 LLM 时发生错误: {e}")
            return None
    
    def _parse_llm_response(self, response: str) -> Optional[ExtractedMemory]:
        """解析 LLM 的响应"""
        
        try:
            # 尝试提取JSON内容
            response = response.strip()
            
            # 如果响应被代码块包裹，提取内容
            if response.startswith("```json"):
                response = response[7:-3].strip()
            elif response.startswith("```"):
                response = response[3:-3].strip()
            
            # 解析JSON
            data = json.loads(response)
            
            # 检查是否表示没有记忆
            if data.get("no_memory"):
                return None
            
            # 验证必需字段
            required_fields = ["content", "importance", "memory_type"]
            if not all(field in data for field in required_fields):
                logger.warning(f"LLM 响应缺少必需字段: {data}")
                return None
            
            # 创建 ExtractedMemory 对象
            return ExtractedMemory(
                content=data["content"],
                importance=float(data["importance"]),
                memory_type=data["memory_type"],
                emotional_valence=data.get("emotional_valence"),
                tags=data.get("tags", ["memory"])
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"无法解析 LLM 响应为 JSON: {e}")
            logger.debug(f"原始响应: {response}")
            return None
        except Exception as e:
            logger.error(f"解析 LLM 响应时发生错误: {e}")
            return None

def test_memory_processor():
    """测试记忆处理器功能"""
    
    # 初始化处理器
    processor = MemoryProcessor()
    
    # 测试对话
    test_conversation = """
用户: 你好，我叫小明，是个程序员
AI: 很高兴认识你，小明！程序员是很棒的职业。
用户: 我最喜欢用Python写代码，也很喜欢喝咖啡
AI: Python确实是很优雅的语言，咖啡也是程序员的好伙伴呢。
用户: 对了，明天是我的生日，我计划和朋友们一起庆祝
AI: 生日快乐！提前祝你生日快乐，和朋友们度过美好时光。
"""
    
    print("=== 记忆处理器测试 ===")
    print(f"测试对话:\n{test_conversation}")
    print("\n" + "="*50)
    
    # 提取记忆
    extracted_memory = processor.extract_and_rate_memory(test_conversation, "test_user_001")
    
    if extracted_memory:
        print("✅ 记忆提取成功!")
        print(f"内容: {extracted_memory.content}")
        print(f"重要性: {extracted_memory.importance}")
        print(f"类型: {extracted_memory.memory_type}")
        print(f"情感倾向: {extracted_memory.emotional_valence}")
        print(f"标签: {extracted_memory.tags}")
        
        # 尝试保存记忆（需要知识库服务运行）
        print(f"\n尝试保存记忆到知识库...")
        success = processor.save_memory("test_user_001", extracted_memory)
        if success:
            print("✅ 记忆保存成功!")
        else:
            print("❌ 记忆保存失败（可能是知识库服务未运行）")
    else:
        print("❌ 未提取到有价值的记忆")

if __name__ == "__main__":
    test_memory_processor()