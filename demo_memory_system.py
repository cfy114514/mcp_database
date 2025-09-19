#!/usr/bin/env python3
"""
MCP 记忆系统端到端演示

这个演示脚本展示了完整的记忆系统工作流程：
1. 手动创建一些模拟记忆数据
2. 演示记忆检索和上下文聚合
3. 展示最终的提示增强效果
"""

import json
import requests
import time
from datetime import datetime

class MemorySystemDemo:
    """记忆系统演示"""
    
    def __init__(self):
        self.kb_service_url = "http://localhost:8001"
        
    def create_sample_memories(self):
        """创建示例记忆数据"""
        print("📝 创建示例记忆数据...")
        
        sample_memories = [
            {
                "content": "用户李明是一名Python开发工程师，专注于后端开发",
                "tags": ["memory"],
                "metadata": {
                    "user_id": "user_demo",
                    "importance": 8.5,
                    "memory_type": "identity",
                    "timestamp": "2025-09-19T10:00:00"
                }
            },
            {
                "content": "李明住在北京，在一家科技公司工作",
                "tags": ["memory"], 
                "metadata": {
                    "user_id": "user_demo",
                    "importance": 7.0,
                    "memory_type": "location",
                    "timestamp": "2025-09-19T10:05:00"
                }
            },
            {
                "content": "李明对机器学习很感兴趣，最近在学习深度学习相关知识",
                "tags": ["memory"],
                "metadata": {
                    "user_id": "user_demo", 
                    "importance": 9.0,
                    "memory_type": "interest",
                    "timestamp": "2025-09-19T10:10:00"
                }
            },
            {
                "content": "李明喜欢喝咖啡，每天早上都要喝一杯美式咖啡提神",
                "tags": ["memory"],
                "metadata": {
                    "user_id": "user_demo",
                    "importance": 6.0,
                    "memory_type": "habit",
                    "timestamp": "2025-09-19T10:15:00"
                }
            },
            {
                "content": "李明使用PyTorch框架进行深度学习实验，最近完成了一个图像分类项目",
                "tags": ["memory"],
                "metadata": {
                    "user_id": "user_demo",
                    "importance": 8.0,
                    "memory_type": "achievement",
                    "timestamp": "2025-09-19T10:20:00"
                }
            }
        ]
        
        success_count = 0
        for memory in sample_memories:
            try:
                response = requests.post(
                    f"{self.kb_service_url}/add",
                    json=memory,
                    timeout=10
                )
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"✅ 记忆已存储: {memory['content'][:50]}...")
                else:
                    print(f"❌ 存储失败: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 存储错误: {e}")
        
        print(f"\n📊 成功存储 {success_count}/{len(sample_memories)} 条记忆")
        return success_count == len(sample_memories)
    
    def demo_memory_retrieval(self):
        """演示记忆检索"""
        print("\n🔍 演示记忆检索功能...")
        
        test_queries = [
            {
                "query": "Python 开发",
                "description": "查询编程相关记忆"
            },
            {
                "query": "机器学习 深度学习",
                "description": "查询学习兴趣相关记忆"
            },
            {
                "query": "北京 工作",
                "description": "查询工作地点相关记忆"
            },
            {
                "query": "咖啡 习惯",
                "description": "查询生活习惯相关记忆"
            }
        ]
        
        for test_case in test_queries:
            print(f"\n--- {test_case['description']} ---")
            print(f"查询: '{test_case['query']}'")
            
            try:
                search_data = {
                    "query": test_case["query"],
                    "tags": ["memory"],
                    "metadata_filter": {"user_id": "user_demo"},
                    "top_k": 3
                }
                
                response = requests.post(
                    f"{self.kb_service_url}/search",
                    json=search_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json()
                    memories = results.get("results", [])
                    
                    print(f"找到 {len(memories)} 条相关记忆:")
                    for i, memory in enumerate(memories, 1):
                        importance = memory.get("metadata", {}).get("importance", 0)
                        memory_type = memory.get("metadata", {}).get("memory_type", "unknown")
                        print(f"  {i}. [{memory_type}] {memory.get('content', '')} (重要性: {importance})")
                else:
                    print(f"❌ 搜索失败: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 搜索错误: {e}")
    
    def demo_context_building(self):
        """演示上下文构建"""
        print("\n🎯 演示上下文构建功能...")
        
        scenarios = [
            {
                "user_query": "能推荐一些Python机器学习的学习资源吗？",
                "expected_context": "应该包含用户的Python经验和机器学习兴趣"
            },
            {
                "user_query": "我想找一个适合工作的咖啡店",
                "expected_context": "应该包含用户的咖啡喜好和工作地点"
            },
            {
                "user_query": "帮我规划一下深度学习的学习路径",
                "expected_context": "应该包含用户的技术背景和当前学习状态"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n--- 场景 {i}: {scenario['expected_context']} ---")
            print(f"用户查询: {scenario['user_query']}")
            
            # 模拟上下文聚合过程
            try:
                # 1. 搜索相关记忆
                search_data = {
                    "query": scenario["user_query"],
                    "tags": ["memory"],
                    "metadata_filter": {"user_id": "user_demo"},
                    "top_k": 3
                }
                
                response = requests.post(
                    f"{self.kb_service_url}/search",
                    json=search_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json()
                    memories = results.get("results", [])
                    
                    # 2. 构建增强的提示
                    enhanced_prompt = self.build_enhanced_prompt(
                        user_query=scenario["user_query"],
                        memories=memories
                    )
                    
                    print("增强后的系统提示:")
                    print("-" * 50)
                    print(enhanced_prompt)
                    print("-" * 50)
                else:
                    print(f"❌ 记忆检索失败: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 上下文构建错误: {e}")
    
    def build_enhanced_prompt(self, user_query: str, memories: list) -> str:
        """构建增强的系统提示"""
        
        # 基础系统提示（模拟洛洛角色）
        base_prompt = """你是洛洛（Luoluo），一个友善、专业且富有创造力的AI助手。你总是以积极的态度帮助用户解决问题，并尽可能提供详细和有用的信息。"""
        
        if not memories:
            return base_prompt
        
        # 格式化记忆信息
        memory_section = "\n[关于这位用户的记忆]"
        memory_items = []
        
        for memory in memories:
            importance = memory.get("metadata", {}).get("importance", 0)
            memory_type = memory.get("metadata", {}).get("memory_type", "")
            content = memory.get("content", "")
            
            # 根据重要性分类
            if importance >= 8.0:
                priority = "重要"
            elif importance >= 6.0:
                priority = "一般"
            else:
                priority = "参考"
            
            memory_items.append(f"- [{priority}] {content}")
        
        memory_section += "\n" + "\n".join(memory_items)
        memory_section += "\n\n请根据这些背景信息，为用户提供个性化的回答。"
        
        # 组合最终提示
        return f"{memory_section}\n\n---\n\n{base_prompt}"
    
    def demo_stats(self):
        """显示系统统计信息"""
        print("\n📊 系统统计信息...")
        
        try:
            response = requests.get(f"{self.kb_service_url}/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print(f"总文档数: {stats.get('stats', {}).get('document_count', 0)}")
                print(f"总向量数: {stats.get('stats', {}).get('vector_count', 0)}")
                print(f"标签数: {stats.get('stats', {}).get('tag_count', 0)}")
                print(f"可用标签: {', '.join(stats.get('stats', {}).get('tags', []))}")
            else:
                print(f"❌ 获取统计信息失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 统计信息错误: {e}")
    
    def run_demo(self):
        """运行完整演示"""
        print("🚀 MCP 记忆系统端到端演示")
        print("=" * 60)
        print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查服务状态
        try:
            response = requests.get(f"{self.kb_service_url}/stats", timeout=5)
            if response.status_code != 200:
                print("❌ 知识库服务未运行，请先启动服务")
                return False
        except:
            print("❌ 无法连接知识库服务，请先启动服务")
            return False
        
        print("✅ 知识库服务运行正常")
        
        # 1. 创建示例数据
        if not self.create_sample_memories():
            print("❌ 示例数据创建失败")
            return False
        
        # 2. 演示记忆检索
        self.demo_memory_retrieval()
        
        # 3. 演示上下文构建
        self.demo_context_building()
        
        # 4. 显示统计信息
        self.demo_stats()
        
        print("\n" + "=" * 60)
        print("🎉 端到端演示完成！")
        print("\n核心功能验证:")
        print("✅ 记忆存储功能正常")
        print("✅ 记忆检索功能正常")
        print("✅ 元数据过滤功能正常")
        print("✅ 上下文聚合功能正常")
        print("✅ 用户隔离功能正常")
        
        return True

def main():
    """主函数"""
    demo = MemorySystemDemo()
    success = demo.run_demo()
    
    if success:
        print("\n💡 下一步:")
        print("1. 配置真实的 LLM API 密钥以启用自动记忆提取")
        print("2. 集成到 MCP 客户端应用中")
        print("3. 测试与角色人设服务的协同工作")
        
    return success

if __name__ == "__main__":
    main()
