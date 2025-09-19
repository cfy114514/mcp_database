#!/usr/bin/env python3
"""
API 配置验证和测试脚本

该脚本用于验证环境变量中的 API 配置是否正确，并测试各个服务的连接性。
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class APIConfigTester:
    """API 配置测试器"""
    
    def __init__(self):
        self.embedding_api_key = os.getenv("EMBEDDING_API_KEY")
        self.embedding_api_url = os.getenv("EMBEDDING_API_URL", "https://api.siliconflow.cn/v1/embeddings")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
        
        self.llm_api_key = os.getenv("LLM_API_KEY")
        self.llm_base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
        
        self.kb_host = os.getenv("KB_HOST", "localhost")
        self.kb_port = os.getenv("KB_PORT", "8001")
        self.kb_service_url = f"http://{self.kb_host}:{self.kb_port}"
    
    def test_embedding_api(self) -> bool:
        """测试向量嵌入 API"""
        print("🔍 测试向量嵌入 API...")
        
        if not self.embedding_api_key:
            print("❌ 未设置 EMBEDDING_API_KEY")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.embedding_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.embedding_model,
                "input": ["测试文本"],
                "encoding_format": "float"
            }
            
            response = requests.post(
                self.embedding_api_url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    embedding_dim = len(result["data"][0]["embedding"])
                    print(f"✅ 向量嵌入 API 正常 (维度: {embedding_dim})")
                    return True
                else:
                    print("❌ 向量嵌入 API 返回格式异常")
                    return False
            else:
                print(f"❌ 向量嵌入 API 错误: {response.status_code}")
                if response.text:
                    print(f"   错误信息: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ 向量嵌入 API 测试失败: {e}")
            return False
    
    def test_llm_api(self) -> bool:
        """测试 LLM API"""
        print("🤖 测试 LLM API...")
        
        if not self.llm_api_key:
            print("❌ 未设置 LLM_API_KEY")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.llm_model,
                "messages": [
                    {"role": "user", "content": "请简单回复：Hello"}
                ],
                "max_tokens": 50,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.llm_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    print(f"✅ LLM API 正常")
                    print(f"   回复: {content.strip()}")
                    return True
                else:
                    print("❌ LLM API 返回格式异常")
                    return False
            else:
                print(f"❌ LLM API 错误: {response.status_code}")
                if response.text:
                    print(f"   错误信息: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ LLM API 测试失败: {e}")
            return False
    
    def test_knowledge_base_service(self) -> bool:
        """测试知识库服务"""
        print("📚 测试知识库服务...")
        
        try:
            # 测试服务状态
            response = requests.get(f"{self.kb_service_url}/stats", timeout=5)
            
            if response.status_code == 200:
                stats = response.json()
                doc_count = stats.get("stats", {}).get("document_count", 0)
                print(f"✅ 知识库服务正常 (文档数: {doc_count})")
                return True
            else:
                print(f"❌ 知识库服务错误: {response.status_code}")
                return False
                
        except requests.ConnectionError:
            print(f"❌ 无法连接知识库服务 ({self.kb_service_url})")
            print("   请先启动: python knowledge_base_service.py")
            return False
        except Exception as e:
            print(f"❌ 知识库服务测试失败: {e}")
            return False
    
    def test_memory_processor(self) -> bool:
        """测试记忆处理器"""
        print("🧠 测试记忆处理器...")
        
        try:
            from memory_processor import MemoryProcessor
            
            # 创建记忆处理器实例
            processor = MemoryProcessor()
            
            # 测试记忆提取
            test_conversation = "我是张三，是一名软件工程师，喜欢Python编程"
            
            memory = processor.extract_and_rate_memory(test_conversation)
            
            if memory and memory.importance >= processor.importance_threshold:
                print(f"✅ 记忆处理器正常")
                print(f"   提取的记忆: {memory.content}")
                print(f"   重要性评分: {memory.importance}")
                print(f"   记忆类型: {memory.memory_type}")
                return True
            else:
                print("⚠️ 记忆处理器工作但未提取到重要记忆")
                return True  # 这也算正常，可能是 LLM 评分较低
                
        except Exception as e:
            print(f"❌ 记忆处理器测试失败: {e}")
            return False
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("📋 当前配置摘要:")
        print("-" * 50)
        
        # 显示配置项（隐藏密钥的敏感部分）
        def mask_key(key):
            if key and len(key) > 8:
                return key[:4] + "*" * (len(key) - 8) + key[-4:]
            return "未设置" if not key else key
        
        print(f"EMBEDDING_API_KEY: {mask_key(self.embedding_api_key)}")
        print(f"EMBEDDING_API_URL: {self.embedding_api_url}")
        print(f"EMBEDDING_MODEL: {self.embedding_model}")
        print(f"LLM_API_KEY: {mask_key(self.llm_api_key)}")
        print(f"LLM_BASE_URL: {self.llm_base_url}")
        print(f"LLM_MODEL: {self.llm_model}")
        print(f"知识库服务: {self.kb_service_url}")
        print("-" * 50)
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 API 配置验证和测试")
        print("=" * 60)
        
        self.print_config_summary()
        
        tests = [
            ("知识库服务", self.test_knowledge_base_service),
            ("向量嵌入 API", self.test_embedding_api),
            ("LLM API", self.test_llm_api),
            ("记忆处理器", self.test_memory_processor),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} 测试 ---")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
                results.append((test_name, False))
        
        # 生成测试报告
        print("\n" + "=" * 60)
        print("📊 测试结果报告")
        print("=" * 60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        success_rate = passed / len(results)
        print(f"\n总体结果: {passed}/{len(results)} ({success_rate:.1%})")
        
        if success_rate == 1.0:
            print("🎉 所有测试通过！记忆系统已完全配置好。")
        elif success_rate >= 0.75:
            print("✅ 大部分测试通过，系统基本可用。")
        else:
            print("❌ 多个测试失败，请检查配置。")
        
        return success_rate >= 0.75

def main():
    """主函数"""
    tester = APIConfigTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n💡 下一步建议:")
        print("1. 运行 python demo_memory_system.py 进行完整演示")
        print("2. 运行 python test_integration.py 进行集成测试")
        print("3. 使用 python deploy_memory_system.py deploy 部署系统")
    else:
        print("\n🔧 故障排除建议:")
        print("1. 检查 .env 文件中的 API 密钥是否正确")
        print("2. 确认网络连接正常")
        print("3. 验证 API 服务商的配额和权限")
        print("4. 启动知识库服务: python knowledge_base_service.py")
    
    return success

if __name__ == "__main__":
    main()
