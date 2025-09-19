#!/usr/bin/env python3
"""
MCP 记忆系统渐进式集成指南

这个脚本提供了一个分步骤的集成方案，让你可以逐步配置和测试记忆系统的各个组件。
"""

import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ProgressiveIntegration:
    """渐进式集成助手"""
    
    def __init__(self):
        self.kb_port = os.getenv("KB_PORT", "8001")
        self.kb_url = f"http://localhost:{self.kb_port}"
        self.embedding_api_key = os.getenv("EMBEDDING_API_KEY")
        
    def step1_test_embedding_api(self):
        """步骤1: 测试 embedding API"""
        print("🔍 步骤 1: 测试向量嵌入 API")
        print("-" * 50)
        
        if not self.embedding_api_key:
            print("❌ 未设置 EMBEDDING_API_KEY")
            return False
        
        try:
            # 测试 embedding API
            headers = {
                "Authorization": f"Bearer {self.embedding_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "BAAI/bge-large-zh-v1.5",
                "input": ["这是一个测试文本"],
                "encoding_format": "float"
            }
            
            print("正在测试向量嵌入 API...")
            response = requests.post(
                "https://api.siliconflow.cn/v1/embeddings",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result:
                    vector_dim = len(result["data"][0]["embedding"])
                    print(f"✅ 向量嵌入 API 测试成功！")
                    print(f"   向量维度: {vector_dim}")
                    print(f"   模型: BAAI/bge-large-zh-v1.5")
                    return True
            else:
                print(f"❌ API 错误: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def step2_start_knowledge_base(self):
        """步骤2: 启动知识库服务"""
        print(f"\n🚀 步骤 2: 启动知识库服务")
        print("-" * 50)
        
        # 检查服务是否已运行
        try:
            response = requests.get(f"{self.kb_url}/stats", timeout=3)
            if response.status_code == 200:
                print("✅ 知识库服务已在运行")
                stats = response.json().get("stats", {})
                print(f"   文档数量: {stats.get('document_count', 0)}")
                print(f"   向量数量: {stats.get('vector_count', 0)}")
                return True
        except:
            pass
        
        print(f"❌ 知识库服务未运行")
        print("\n📋 启动步骤:")
        print("1. 打开新的终端窗口")
        print("2. 进入项目目录")
        print(f"3. 运行: $env:KB_PORT={self.kb_port}; python knowledge_base_service.py")
        print("4. 等待看到 'Uvicorn running' 消息")
        print("5. 然后继续下一步")
        
        input("\n按 Enter 键继续测试服务连接...")
        
        # 再次检查
        try:
            response = requests.get(f"{self.kb_url}/stats", timeout=3)
            if response.status_code == 200:
                print("✅ 知识库服务连接成功！")
                return True
            else:
                print("❌ 服务响应异常")
                return False
        except Exception as e:
            print(f"❌ 无法连接服务: {e}")
            return False
    
    def step3_test_basic_storage(self):
        """步骤3: 测试基础存储功能"""
        print(f"\n📝 步骤 3: 测试基础存储功能")
        print("-" * 50)
        
        try:
            # 创建测试文档
            test_doc = {
                "content": "用户张三是一名Python开发工程师，工作地点在北京",
                "tags": ["memory", "test"],
                "metadata": {
                    "user_id": "test_user_001",
                    "importance": 8.0,
                    "memory_type": "identity",
                    "timestamp": "2025-09-19T12:00:00"
                }
            }
            
            print("正在存储测试文档...")
            response = requests.post(
                f"{self.kb_url}/add",
                json=test_doc,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                doc_id = result.get("document_id")
                print(f"✅ 文档存储成功！")
                print(f"   文档ID: {doc_id}")
                
                # 测试搜索
                print("\n正在测试搜索功能...")
                search_data = {
                    "query": "Python 开发工程师",
                    "tags": ["memory"],
                    "metadata_filter": {"user_id": "test_user_001"},
                    "top_k": 1
                }
                
                response = requests.post(
                    f"{self.kb_url}/search",
                    json=search_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    if results:
                        print(f"✅ 搜索功能正常！")
                        print(f"   找到 {len(results)} 条相关记录")
                        print(f"   内容: {results[0]['content'][:50]}...")
                        return True
                    else:
                        print("⚠️ 搜索未找到结果")
                        return False
                else:
                    print(f"❌ 搜索失败: {response.status_code}")
                    return False
            else:
                print(f"❌ 存储失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def step4_test_memory_processor_basic(self):
        """步骤4: 测试记忆处理器基础功能"""
        print(f"\n🧠 步骤 4: 测试记忆处理器 (无 LLM 模式)")
        print("-" * 50)
        
        try:
            from memory_processor import MemoryProcessor, ExtractedMemory
            
            # 创建记忆处理器 (不使用 LLM)
            processor = MemoryProcessor()
            
            print("✅ 记忆处理器创建成功")
            
            # 手动创建测试记忆
            test_memory = ExtractedMemory(
                content="用户李明喜欢喝咖啡，每天早上都要来一杯",
                importance=7.5,
                memory_type="habit",
                emotional_valence=0.5,
                tags=["memory"]
            )
            
            print("正在测试记忆保存功能...")
            success = processor.save_memory("test_user_002", test_memory)
            
            if success:
                print("✅ 记忆保存功能正常！")
                print(f"   记忆内容: {test_memory.content}")
                print(f"   重要性: {test_memory.importance}")
                print(f"   类型: {test_memory.memory_type}")
                return True
            else:
                print("❌ 记忆保存失败")
                return False
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def step5_test_context_aggregation(self):
        """步骤5: 测试上下文聚合"""
        print(f"\n🎯 步骤 5: 测试上下文聚合功能")
        print("-" * 50)
        
        try:
            # 模拟上下文聚合过程
            print("正在搜索用户记忆...")
            
            search_data = {
                "query": "咖啡 习惯",
                "tags": ["memory"],
                "metadata_filter": {"user_id": "test_user_002"},
                "top_k": 3
            }
            
            response = requests.post(
                f"{self.kb_url}/search",
                json=search_data,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                
                if results:
                    print(f"✅ 找到 {len(results)} 条相关记忆")
                    
                    # 构建增强提示
                    base_prompt = "你是洛洛，一个友善的AI助手。"
                    
                    memory_section = "\n[用户记忆上下文]\n"
                    for memory in results:
                        importance = memory.get("metadata", {}).get("importance", 0)
                        content = memory.get("content", "")
                        memory_section += f"- [重要性: {importance}] {content}\n"
                    
                    enhanced_prompt = memory_section + "\n" + base_prompt
                    
                    print("✅ 上下文聚合成功！")
                    print("\n增强后的提示:")
                    print("-" * 40)
                    print(enhanced_prompt)
                    print("-" * 40)
                    return True
                else:
                    print("⚠️ 未找到相关记忆")
                    return False
            else:
                print(f"❌ 记忆搜索失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def step6_next_steps(self):
        """步骤6: 后续步骤建议"""
        print(f"\n🚀 步骤 6: 后续集成建议")
        print("-" * 50)
        
        print("🎉 基础功能验证完成！")
        print("\n📋 下一步可选操作:")
        
        print("\n1. 配置 LLM API (可选，用于自动记忆提取):")
        print("   - 编辑 .env 文件")
        print("   - 添加 LLM_API_KEY 和 LLM_BASE_URL")
        print("   - 重新测试记忆提取功能")
        
        print("\n2. 集成到 MCP 客户端:")
        print("   - 使用 context_aggregator_mcp.py 作为 MCP 服务")
        print("   - 配置 mcp_config.json")
        print("   - 在客户端调用 build_prompt_with_context 工具")
        
        print("\n3. 运行完整演示:")
        print("   - python demo_memory_system.py")
        print("   - python test_integration.py")
        
        print("\n4. 部署到生产环境:")
        print("   - python deploy_memory_system.py deploy")
        
        print("\n💡 当前可用功能:")
        print("   ✅ 记忆存储和检索")
        print("   ✅ 用户数据隔离")
        print("   ✅ 上下文聚合")
        print("   ✅ 向量相似度搜索")
        
        return True
    
    def run_integration(self):
        """运行完整的渐进式集成"""
        print("🛠️ MCP 记忆系统渐进式集成")
        print("=" * 60)
        
        steps = [
            ("测试向量嵌入 API", self.step1_test_embedding_api),
            ("启动知识库服务", self.step2_start_knowledge_base),
            ("测试基础存储功能", self.step3_test_basic_storage),
            ("测试记忆处理器", self.step4_test_memory_processor_basic),
            ("测试上下文聚合", self.step5_test_context_aggregation),
            ("后续步骤建议", self.step6_next_steps),
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            print(f"\n{'='*20} {i}/6 {'='*20}")
            try:
                success = step_func()
                if not success and i < len(steps) - 1:  # 最后一步总是显示建议
                    print(f"\n❌ 步骤 {i} 失败，请解决问题后重新运行")
                    return False
            except KeyboardInterrupt:
                print(f"\n⏹️ 用户中断了步骤 {i}")
                return False
            except Exception as e:
                print(f"\n💥 步骤 {i} 发生异常: {e}")
                return False
        
        print(f"\n🎊 集成完成！记忆系统基础功能已就绪。")
        return True

def main():
    """主函数"""
    integration = ProgressiveIntegration()
    integration.run_integration()

if __name__ == "__main__":
    main()
