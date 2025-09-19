#!/usr/bin/env python3
"""
记忆系统的存储、处理和读取流程演示

这个脚本完整展示了记忆从创建到检索的整个生命周期：
1. 对话输入 → 记忆提取 → 向量化存储
2. 用户查询 → 向量搜索 → 上下文聚合
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

class MemoryFlowDemo:
    """记忆流程演示类"""
    
    def __init__(self):
        self.kb_url = "http://localhost:8001"
        self.demo_data = self._prepare_demo_data()
    
    def _prepare_demo_data(self) -> Dict:
        """准备演示数据"""
        return {
            "user_id": "demo_user_001",
            "conversations": [
                {
                    "conversation": """
用户: 你好络络，我是李明
络络: 你好李明！很高兴认识你
用户: 我是一名软件工程师，主要做Python开发
络络: 很棒！Python是很实用的语言
用户: 我每天早上都喝咖啡，特别喜欢拿铁
络络: 好的，我记住了你喜欢拿铁咖啡
                    """,
                    "expected_memories": [
                        "用户李明是一名软件工程师，主要做Python开发",
                        "用户李明每天早上都喝咖啡，特别喜欢拿铁"
                    ]
                },
                {
                    "conversation": """
用户: 我住在北京朝阳区，平时工作比较忙
络络: 了解，北京的工作节奏确实很快
用户: 我最近在学习机器学习，对深度学习很感兴趣
络络: 机器学习是很前沿的技术呢
                    """,
                    "expected_memories": [
                        "用户李明住在北京朝阳区，平时工作比较忙",
                        "用户李明最近在学习机器学习，对深度学习很感兴趣"
                    ]
                }
            ],
            "queries": [
                "李明的基本信息",
                "李明的工作情况", 
                "李明的饮食习惯",
                "李明的学习情况",
                "李明的居住地址"
            ]
        }
    
    def show_complete_flow(self):
        """展示完整的记忆流程"""
        print("🧠 记忆系统完整流程演示")
        print("=" * 70)
        
        # 步骤1：展示原始对话
        self._step1_show_conversations()
        
        # 步骤2：记忆提取和处理
        self._step2_memory_extraction()
        
        # 步骤3：向量化存储
        self._step3_vectorization_storage()
        
        # 步骤4：记忆检索流程
        self._step4_memory_retrieval()
        
        # 步骤5：上下文聚合
        self._step5_context_aggregation()
        
        # 步骤6：流程总结
        self._step6_flow_summary()
    
    def _step1_show_conversations(self):
        """步骤1：展示原始对话"""
        print("\n📝 步骤1：原始对话输入")
        print("-" * 50)
        
        for i, conv_data in enumerate(self.demo_data["conversations"], 1):
            print(f"\n对话 {i}:")
            print("=" * 30)
            print(conv_data["conversation"])
            
            print(f"\n预期提取的记忆:")
            for j, memory in enumerate(conv_data["expected_memories"], 1):
                print(f"  {j}. {memory}")
    
    def _step2_memory_extraction(self):
        """步骤2：记忆提取和处理"""
        print(f"\n🧠 步骤2：记忆提取和处理")
        print("-" * 50)
        
        print("🔍 记忆提取流程:")
        print("1. 对话历史输入 → LLM 分析")
        print("2. 提取重要信息 → 结构化数据")
        print("3. 重要性评分 → 质量筛选")
        print("4. 分类标记 → 便于检索")
        
        # 模拟记忆提取过程
        extracted_memories = []
        
        for i, conv_data in enumerate(self.demo_data["conversations"], 1):
            print(f"\n📋 处理对话 {i}:")
            print("-" * 25)
            
            # 模拟提取结果
            for j, expected_memory in enumerate(conv_data["expected_memories"], 1):
                memory_obj = {
                    "content": expected_memory,
                    "importance": 7.0 + j * 0.5,  # 模拟重要性评分
                    "memory_type": "identity" if "工程师" in expected_memory else 
                                  "preference" if "咖啡" in expected_memory else
                                  "knowledge" if "机器学习" in expected_memory else
                                  "location" if "北京" in expected_memory else "general",
                    "emotional_valence": 0.0,
                    "tags": self._generate_tags(expected_memory)
                }
                
                extracted_memories.append(memory_obj)
                
                print(f"  提取记忆 {j}:")
                print(f"    内容: {memory_obj['content']}")
                print(f"    重要性: {memory_obj['importance']}/10")
                print(f"    类型: {memory_obj['memory_type']}")
                print(f"    标签: {', '.join(memory_obj['tags'])}")
        
        self.extracted_memories = extracted_memories
    
    def _generate_tags(self, content: str) -> List[str]:
        """生成记忆标签"""
        tags = ["memory"]
        
        # 基于内容生成标签
        if "工程师" in content or "Python" in content:
            tags.extend(["职业", "技术", "Python"])
        if "咖啡" in content or "拿铁" in content:
            tags.extend(["饮品", "咖啡", "习惯"])
        if "北京" in content or "朝阳区" in content:
            tags.extend(["地址", "北京", "居住"])
        if "机器学习" in content or "深度学习" in content:
            tags.extend(["学习", "技术", "AI"])
        
        return list(set(tags))  # 去重
    
    def _step3_vectorization_storage(self):
        """步骤3：向量化存储"""
        print(f"\n🔢 步骤3：向量化存储")
        print("-" * 50)
        
        print("📊 向量化流程:")
        print("1. 文本内容 → 向量嵌入 (1024维)")
        print("2. 向量存储 → 语义空间建立")
        print("3. 标签索引 → 快速过滤建立")
        print("4. 元数据 → 用户隔离和分类")
        
        # 实际向量化存储演示
        print(f"\n💾 实际存储演示:")
        print("-" * 25)
        
        stored_count = 0
        for i, memory in enumerate(self.extracted_memories, 1):
            print(f"\n存储记忆 {i}:")
            
            # 构建存储数据
            doc_data = {
                "content": memory["content"],
                "tags": memory["tags"],
                "metadata": {
                    "user_id": self.demo_data["user_id"],
                    "importance": memory["importance"],
                    "memory_type": memory["memory_type"],
                    "emotional_valence": memory["emotional_valence"],
                    "created_at": datetime.now().isoformat()
                }
            }
            
            try:
                # 实际存储到知识库
                response = requests.post(
                    f"{self.kb_url}/add",
                    json=doc_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    doc_id = result.get("document_id", "unknown")
                    print(f"  ✅ 存储成功: {doc_id}")
                    print(f"     内容: {memory['content'][:40]}...")
                    print(f"     向量: 1024维 (BAAI/bge-large-zh-v1.5)")
                    print(f"     标签: {', '.join(memory['tags'][:3])}...")
                    stored_count += 1
                else:
                    print(f"  ❌ 存储失败: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 存储错误: {e}")
                
        print(f"\n📊 存储统计: 成功存储 {stored_count}/{len(self.extracted_memories)} 条记忆")
    
    def _step4_memory_retrieval(self):
        """步骤4：记忆检索流程"""
        print(f"\n🔍 步骤4：记忆检索流程")
        print("-" * 50)
        
        print("🎯 检索流程:")
        print("1. 用户查询 → 向量化")
        print("2. 向量搜索 → 语义匹配")
        print("3. 标签过滤 → 精确筛选")
        print("4. 用户隔离 → 数据安全")
        print("5. 重要性排序 → 结果优化")
        
        print(f"\n🔎 检索演示:")
        print("-" * 25)
        
        for i, query in enumerate(self.demo_data["queries"], 1):
            print(f"\n查询 {i}: '{query}'")
            print("-" * 20)
            
            # 构建搜索请求
            search_data = {
                "query": query,
                "tags": ["memory"],
                "metadata_filter": {"user_id": self.demo_data["user_id"]},
                "top_k": 3
            }
            
            try:
                response = requests.post(
                    f"{self.kb_url}/search",
                    json=search_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success") and result.get("results"):
                        results = result["results"]
                        print(f"  ✅ 找到 {len(results)} 条相关记忆:")
                        
                        for j, item in enumerate(results, 1):
                            content = item.get("content", "")
                            metadata = item.get("metadata", {})
                            importance = metadata.get("importance", 0)
                            memory_type = metadata.get("memory_type", "unknown")
                            
                            print(f"    {j}. {content}")
                            print(f"       重要性: {importance}/10 | 类型: {memory_type}")
                    else:
                        print("  ❌ 未找到相关记忆")
                else:
                    print(f"  ❌ 搜索失败: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 搜索错误: {e}")
    
    def _step5_context_aggregation(self):
        """步骤5：上下文聚合"""
        print(f"\n🎯 步骤5：上下文聚合")
        print("-" * 50)
        
        print("🔄 聚合流程:")
        print("1. 记忆检索 → 获取相关记忆")
        print("2. 重要性排序 → 优先级确定")
        print("3. 上下文构建 → 结构化组织")
        print("4. 提示增强 → 完整输出")
        
        # 演示上下文聚合
        demo_query = "李明的个人情况"
        print(f"\n📋 聚合演示: '{demo_query}'")
        print("-" * 30)
        
        # 获取相关记忆
        search_data = {
            "query": demo_query,
            "tags": ["memory"],
            "metadata_filter": {"user_id": self.demo_data["user_id"]},
            "top_k": 5
        }
        
        try:
            response = requests.post(
                f"{self.kb_url}/search",
                json=search_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("results"):
                    memories = result["results"]
                    
                    # 构建上下文
                    print("1. 检索到的记忆:")
                    for i, memory in enumerate(memories, 1):
                        content = memory.get("content", "")
                        importance = memory.get("metadata", {}).get("importance", 0)
                        print(f"   {i}. [重要性: {importance}] {content}")
                    
                    # 构建增强提示
                    print(f"\n2. 构建的上下文:")
                    print("-" * 20)
                    
                    base_prompt = "你是络络，一个友善的AI助手。"
                    
                    memory_section = "\n[用户记忆上下文]\n"
                    for memory in memories:
                        importance = memory.get("metadata", {}).get("importance", 0)
                        content = memory.get("content", "")
                        memory_section += f"- [重要性: {importance}] {content}\n"
                    
                    enhanced_prompt = memory_section + "\n" + base_prompt
                    
                    print("增强后的系统提示:")
                    print("=" * 40)
                    print(enhanced_prompt)
                    print("=" * 40)
                    
                    print("\n3. 效果对比:")
                    print("-" * 15)
                    print("❌ 原始提示: AI 不了解用户任何信息")
                    print("✅ 增强提示: AI 了解用户是软件工程师李明，住北京，喜欢咖啡，在学机器学习")
        
        except Exception as e:
            print(f"❌ 聚合演示失败: {e}")
    
    def _step6_flow_summary(self):
        """步骤6：流程总结"""
        print(f"\n📊 步骤6：完整流程总结")
        print("-" * 50)
        
        print("🔄 记忆生命周期:")
        print("┌─────────────────┐")
        print("│ 1. 对话输入     │")
        print("└────────┬────────┘")
        print("         ↓")
        print("┌─────────────────┐    🧠 LLM 分析")
        print("│ 2. 记忆提取     │ ← 重要性评分")
        print("└────────┬────────┘    分类标记")
        print("         ↓")
        print("┌─────────────────┐    🔢 向量嵌入")
        print("│ 3. 向量化存储   │ ← 1024维向量")
        print("└────────┬────────┘    标签索引")
        print("         ↓")
        print("┌─────────────────┐    🔍 语义搜索")
        print("│ 4. 记忆检索     │ ← 用户隔离")
        print("└────────┬────────┘    重要性排序")
        print("         ↓")
        print("┌─────────────────┐    🎯 智能聚合")
        print("│ 5. 上下文增强   │ ← 提示构建")
        print("└─────────────────┘    对话增强")
        
        print(f"\n💡 核心技术栈:")
        print("-" * 20)
        print("🔢 向量化: BAAI/bge-large-zh-v1.5 (1024维)")
        print("🧠 LLM: 智能记忆提取和重要性评分")
        print("🏷️ 标签: 多维度分类和快速过滤")
        print("🔒 隔离: 基于 metadata 的用户数据隔离")
        print("🎯 聚合: 语义搜索 + 重要性加权")
        
        print(f"\n⚡ 性能特点:")
        print("-" * 20)
        print("✅ 语义理解: 不仅关键词匹配，理解语义关联")
        print("✅ 智能评分: LLM 自动评估记忆重要性")
        print("✅ 用户隔离: 多用户环境下数据完全隔离")
        print("✅ 实时性: 即时存储和检索，无延迟")
        print("✅ 可扩展: 支持大规模用户和记忆存储")
        
        # 获取当前统计
        try:
            response = requests.get(f"{self.kb_url}/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json().get("stats", {})
                print(f"\n📈 当前系统状态:")
                print("-" * 20)
                print(f"📄 总文档数: {stats.get('document_count', 0)}")
                print(f"🔢 向量数量: {stats.get('vector_count', 0)}")
                print(f"👤 演示用户: {self.demo_data['user_id']}")
                print(f"💾 新增记忆: {len(self.extracted_memories)} 条")
        except:
            pass

def main():
    """主函数"""
    print("🧠 记忆系统存储、处理和读取流程演示")
    print("=" * 70)
    print("这个演示将展示记忆从对话输入到上下文聚合的完整流程")
    
    # 检查服务状态
    demo = MemoryFlowDemo()
    try:
        response = requests.get(f"{demo.kb_url}/stats", timeout=3)
        if response.status_code != 200:
            print("❌ 知识库服务未运行，请先启动:")
            print("   python knowledge_base_service.py")
            return
    except:
        print("❌ 无法连接到知识库服务，请先启动:")
        print("   python knowledge_base_service.py")
        return
    
    print("✅ 知识库服务连接正常，开始演示...\n")
    
    # 运行完整流程演示
    demo.show_complete_flow()
    
    print(f"\n🎉 流程演示完成！")
    print("=" * 70)
    print("记忆系统现在可以:")
    print("1. 🤖 智能提取对话中的重要信息")
    print("2. 📊 向量化存储并建立语义索引")
    print("3. 🔍 基于语义相似度智能检索")
    print("4. 🎯 构建包含记忆的增强提示")
    print("5. 🔒 确保不同用户数据完全隔离")

if __name__ == "__main__":
    main()
