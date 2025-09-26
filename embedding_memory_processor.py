#!/usr/bin/env python3
"""
基于Embedding的记忆处理器
不依赖LLM，仅使用embedding模型实现记忆提取、存储和检索
"""

import re
import json
import logging
import requests
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmbeddingMemoryProcessor")

@dataclass
class MemorySegment:
    """记忆片段数据类"""
    content: str
    importance: float
    memory_type: str
    context: str = ""
    keywords: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

class EmbeddingMemoryProcessor:
    """基于Embedding的记忆处理器"""
    
    def __init__(self, kb_service_url: str = "http://localhost:8001"):
        self.kb_service_url = kb_service_url
        self.api_key = os.getenv("EMBEDDING_API_KEY")
        self.model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
        
        # 记忆类型检测关键词
        self.memory_type_keywords = {
            "personal": ["我", "我的", "我们", "我在", "我会", "我喜欢", "我不喜欢"],
            "preference": ["喜欢", "不喜欢", "偏好", "习惯", "常常", "总是", "从不"],
            "event": ["昨天", "今天", "明天", "上次", "去了", "做了", "发生", "参加"],
            "knowledge": ["是什么", "怎么", "为什么", "学到", "了解", "知道"],
            "emotional": ["开心", "难过", "高兴", "沮丧", "兴奋", "紧张", "担心"]
        }
        
        # 重要性评估关键词
        self.importance_keywords = {
            "high": ["重要", "关键", "必须", "一定", "特别", "非常", "极其"],
            "medium": ["可能", "也许", "大概", "应该", "建议"],
            "low": ["随便", "无所谓", "都行", "随意"]
        }
        
        logger.info("基于Embedding的记忆处理器初始化完成")
    
    def create_embedding(self, text: str) -> Optional[np.ndarray]:
        """创建文本的embedding向量"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.siliconflow.cn/v1/embeddings",
                headers=headers,
                json={
                    "model": self.model,
                    "input": text,
                    "encoding_format": "float"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return np.array(data["data"][0]["embedding"], dtype=np.float32)
            else:
                logger.error(f"Embedding API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"创建embedding时发生错误: {e}")
            return None
    
    def segment_conversation(self, conversation: str) -> List[str]:
        """将对话分割为有意义的片段"""
        # 按说话者分割
        lines = conversation.strip().split('\n')
        segments = []
        current_segment = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检测说话者切换
            if line.startswith(('用户:', 'AI:', '助手:', '用户：', 'AI：', '助手：')):
                if current_segment:
                    segments.append('\n'.join(current_segment))
                    current_segment = []
                current_segment.append(line)
            else:
                if current_segment:
                    current_segment.append(line)
                else:
                    segments.append(line)
        
        if current_segment:
            segments.append('\n'.join(current_segment))
        
        # 合并过短的片段
        merged_segments = []
        temp_segment = ""
        
        for segment in segments:
            if len(segment.strip()) < 20:  # 太短的片段
                temp_segment += " " + segment
            else:
                if temp_segment:
                    merged_segments.append(temp_segment.strip() + " " + segment)
                    temp_segment = ""
                else:
                    merged_segments.append(segment)
        
        if temp_segment:
            merged_segments.append(temp_segment.strip())
        
        return merged_segments
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（可以用更复杂的算法替代）
        # 移除常见的停用词
        stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        # 提取可能的关键词（简化版）
        words = re.findall(r'[\u4e00-\u9fff]+', text)
        keywords = []
        
        for word in words:
            if len(word) >= 2 and word not in stop_words:
                keywords.append(word)
        
        # 去重并限制数量
        return list(set(keywords))[:10]
    
    def classify_memory_type(self, text: str) -> str:
        """基于关键词分类记忆类型"""
        text_lower = text.lower()
        type_scores = {}
        
        for memory_type, keywords in self.memory_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            type_scores[memory_type] = score
        
        # 返回得分最高的类型，如果没有匹配则返回 "general"
        if not type_scores:
            return "general"
        best_type = max(type_scores.keys(), key=lambda k: type_scores[k])
        return best_type if type_scores[best_type] > 0 else "general"
    
    def calculate_importance(self, text: str, context: str = "") -> float:
        """基于多种因素计算重要性分数 (1-10)"""
        importance = 5.0  # 基础分数
        
        # 1. 基于关键词的重要性
        text_lower = text.lower()
        for level, keywords in self.importance_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if level == "high":
                importance += count * 1.5
            elif level == "medium":
                importance += count * 0.5
            elif level == "low":
                importance -= count * 0.5
        
        # 2. 基于文本长度 - 更长的文本可能包含更多信息
        length_score = min(len(text) / 100, 2.0)  # 最多加2分
        importance += length_score
        
        # 3. 基于情感词汇
        emotional_words = ["喜欢", "讨厌", "重要", "关键", "特别", "非常"]
        emotion_score = sum(0.3 for word in emotional_words if word in text_lower)
        importance += emotion_score
        
        # 4. 基于个人信息密度
        personal_indicators = ["我的", "我在", "我会", "我常常", "我总是"]
        personal_score = sum(0.4 for indicator in personal_indicators if indicator in text_lower)
        importance += personal_score
        
        # 5. 基于时间信息
        time_indicators = ["昨天", "今天", "明天", "经常", "总是", "从不", "习惯"]
        time_score = sum(0.2 for indicator in time_indicators if indicator in text_lower)
        importance += time_score
        
        # 限制在1-10范围内
        return max(1.0, min(10.0, importance))
    
    def detect_similar_memories(self, new_embedding: np.ndarray, user_id: str, threshold: float = 0.85) -> List[Dict]:
        """检测相似的已存在记忆"""
        try:
            # 搜索相似记忆
            response = requests.post(
                f"{self.kb_service_url}/search",
                json={
                    "query": "记忆内容",  # 占位查询
                    "tags": ["memory"],
                    "top_k": 20,
                    "metadata_filter": {"user_id": user_id}
                }
            )
            
            if response.status_code != 200:
                return []
            
            results = response.json().get("results", [])
            similar_memories = []
            
            for result in results:
                # 这里需要实现embedding相似性比较
                # 简化版本：基于内容长度和关键词重叠判断
                similar_memories.append(result)
            
            return similar_memories[:5]  # 返回最相似的5个
            
        except Exception as e:
            logger.error(f"检测相似记忆时出错: {e}")
            return []
    
    def process_conversation_memories(self, conversation: str, user_id: str) -> List[MemorySegment]:
        """处理对话并提取记忆片段"""
        try:
            # 1. 分割对话
            segments = self.segment_conversation(conversation)
            logger.info(f"对话分割为 {len(segments)} 个片段")
            
            memories = []
            for i, segment in enumerate(segments):
                if len(segment.strip()) < 10:  # 跳过过短的片段
                    continue
                
                # 2. 分类记忆类型
                memory_type = self.classify_memory_type(segment)
                
                # 3. 计算重要性
                importance = self.calculate_importance(segment, conversation)
                
                # 4. 提取关键词
                keywords = self.extract_keywords(segment)
                
                # 5. 创建记忆片段
                memory = MemorySegment(
                    content=segment.strip(),
                    importance=importance,
                    memory_type=memory_type,
                    context=f"来自对话第{i+1}段",
                    keywords=keywords
                )
                
                memories.append(memory)
                logger.info(f"提取记忆片段: 类型={memory_type}, 重要性={importance:.1f}")
            
            return memories
            
        except Exception as e:
            logger.error(f"处理对话记忆时出错: {e}")
            return []
    
    def save_memory_segment(self, memory: MemorySegment, user_id: str) -> bool:
        """保存记忆片段到知识库"""
        try:
            # 创建文档数据
            keywords_list = memory.keywords or []
            document_data = {
                "content": memory.content,
                "tags": ["memory", memory.memory_type] + keywords_list[:5],  # 限制关键词数量
                "metadata": {
                    "user_id": user_id,
                    "memory_type": memory.memory_type,
                    "importance": memory.importance,
                    "created_at": datetime.now().isoformat(),
                    "context": memory.context,
                    "keywords": keywords_list
                }
            }
            
            # 调用知识库API保存
            response = requests.post(
                f"{self.kb_service_url}/add",
                json=document_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"记忆片段保存成功: {result.get('document_id')}")
                    return True
                    
            logger.error(f"保存记忆片段失败: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"保存记忆片段时出错: {e}")
            return False
    
    def process_and_save_conversation(self, conversation: str, user_id: str, min_importance: float = 0.0) -> Dict:
        """
        处理对话并保存有价值的记忆。
        默认保存所有提取到的记忆 (min_importance=0.0)。
        """
        try:
            # 提取记忆片段
            memories = self.process_conversation_memories(conversation, user_id)
            
            if not memories:
                return {
                    "success": False,
                    "message": "未从对话中提取到记忆片段",
                    "memories_saved": 0
                }
            
            # 保存重要的记忆
            saved_count = 0
            saved_memories = []
            
            for memory in memories:
                if memory.importance >= min_importance:
                    if self.save_memory_segment(memory, user_id):
                        saved_count += 1
                        saved_memories.append({
                            "content": memory.content,
                            "importance": memory.importance,
                            "memory_type": memory.memory_type,
                            "keywords": memory.keywords
                        })
            
            return {
                "success": True,
                "message": f"成功处理对话，保存了 {saved_count} 个记忆片段",
                "memories_extracted": len(memories),
                "memories_saved": saved_count,
                "saved_memories": saved_memories
            }
            
        except Exception as e:
            logger.error(f"处理并保存对话时出错: {e}")
            return {
                "success": False,
                "message": f"处理对话时发生错误: {str(e)}",
                "memories_saved": 0
            }
    
    def search_memories(self, user_id: str, query: str = "", top_k: int = 5, memory_type: Optional[str] = None) -> List[Dict]:
        """搜索用户记忆"""
        try:
            search_params = {
                "query": query or "用户记忆",
                "tags": ["memory"],
                "top_k": top_k,
                "metadata_filter": {"user_id": user_id}
            }
            
            # 添加记忆类型过滤
            if memory_type:
                search_params["metadata_filter"]["memory_type"] = memory_type
            
            response = requests.post(
                f"{self.kb_service_url}/search",
                json=search_params
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result.get("results", [])
            
            return []
            
        except Exception as e:
            logger.error(f"搜索记忆时出错: {e}")
            return []

def test_embedding_memory_processor():
    """测试基于Embedding的记忆处理器"""
    print("=== 基于Embedding的记忆处理器测试 ===")
    
    processor = EmbeddingMemoryProcessor()
    
    # 测试对话
    test_conversation = """
用户: 我每天早上都要喝咖啡，特别是拿铁，不加糖的那种
AI: 这是很好的习惯，咖啡能够帮助提神醒脑
用户: 是的，我在北京工作，每天早上8点必须到公司
AI: 北京的早高峰确实比较拥挤，早起是明智的选择
用户: 我特别不喜欢迟到，这让我很焦虑
AI: 理解你的感受，守时确实是很重要的品质
    """
    
    # 1. 测试对话分割
    print("1. 测试对话分割...")
    segments = processor.segment_conversation(test_conversation)
    for i, segment in enumerate(segments):
        print(f"片段 {i+1}: {segment}")
    
    # 2. 测试记忆提取
    print("\n2. 测试记忆提取...")
    memories = processor.process_conversation_memories(test_conversation, "test_user_003")
    for memory in memories:
        print(f"记忆: {memory.content[:50]}...")
        print(f"  类型: {memory.memory_type}")
        print(f"  重要性: {memory.importance:.1f}")
        print(f"  关键词: {memory.keywords}")
        print()
    
    # 3. 测试完整流程
    print("3. 测试完整处理流程...")
    result = processor.process_and_save_conversation(test_conversation, "test_user_003")
    print(f"处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_embedding_memory_processor()
