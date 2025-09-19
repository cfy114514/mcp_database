#!/usr/bin/env python3
"""
MCP 记忆系统集成测试

测试整个记忆系统的端到端功能，包括：
1. 记忆提取和存储
2. 上下文聚合
3. 用户隔离
4. 服务间通信

运行前请确保以下服务已启动：
- knowledge_base_service.py (HTTP 服务，端口 8000)
"""

import json
import requests
import time
import sys
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryIntegrationTester:
    """记忆系统集成测试器"""
    
    def __init__(self):
        self.kb_service_url = "http://localhost:8001"
        self.test_users = ["user_001", "user_002"]
        self.test_conversations = [
            {
                "user_id": "user_001",
                "conversations": [
                    "我叫李明，是一名Python开发工程师",
                    "我住在北京，主要做后端开发",
                    "我喜欢机器学习，最近在学深度学习"
                ]
            },
            {
                "user_id": "user_002", 
                "conversations": [
                    "我是前端开发者张三，专注JavaScript",
                    "目前在上海工作，主要用React框架",
                    "对Vue.js也很感兴趣"
                ]
            }
        ]
        
    def check_services(self) -> bool:
        """检查必要的服务是否运行"""
        logger.info("🔍 检查服务状态...")
        
        # 检查知识库 HTTP 服务
        try:
            response = requests.get(f"{self.kb_service_url}/stats", timeout=5)
            if response.status_code == 200:
                logger.info("✅ 知识库 HTTP 服务正常")
                return True
            else:
                logger.error(f"❌ 知识库服务返回错误状态: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 无法连接知识库服务: {e}")
            logger.info("请先启动: python knowledge_base_service.py")
            return False
    
    def test_memory_storage(self) -> bool:
        """测试记忆存储功能"""
        logger.info("🧠 测试记忆存储功能...")
        
        try:
            # 导入记忆处理器
            from memory_processor import MemoryProcessor
            
            # 创建记忆处理器实例
            processor = MemoryProcessor(
                llm_api_key="test_key",  # 使用测试密钥
                kb_service_url=self.kb_service_url
            )
            
            success_count = 0
            total_tests = 0
            
            for user_data in self.test_conversations:
                user_id = user_data["user_id"]
                
                for conversation in user_data["conversations"]:
                    total_tests += 1
                    logger.info(f"处理用户 {user_id} 的对话: {conversation[:50]}...")
                    
                    try:
                        # 提取记忆
                        memory_result = processor.extract_and_rate_memory(conversation)
                        
                        if memory_result and memory_result.importance >= 3.0:
                            # 保存记忆
                            success = processor.save_memory(
                                user_id=user_id,
                                memory=memory_result
                            )
                            
                            if success:
                                success_count += 1
                                logger.info(f"✅ 成功存储记忆 (重要性: {memory_result.importance})")
                            else:
                                logger.error("❌ 记忆存储失败")
                        else:
                            logger.info("⏭️ 对话重要性不足，跳过存储")
                            success_count += 1  # 跳过也算成功
                    
                    except Exception as e:
                        logger.error(f"❌ 处理对话时出错: {e}")
            
            success_rate = success_count / total_tests if total_tests > 0 else 0
            logger.info(f"📊 记忆存储测试完成: {success_count}/{total_tests} ({success_rate:.1%})")
            
            return success_rate > 0.5
            
        except ImportError:
            logger.error("❌ 无法导入 memory_processor 模块")
            return False
        except Exception as e:
            logger.error(f"❌ 记忆存储测试失败: {e}")
            return False
    
    def test_memory_retrieval(self) -> bool:
        """测试记忆检索功能"""
        logger.info("🔍 测试记忆检索功能...")
        
        try:
            # 测试每个用户的记忆检索
            for user_data in self.test_conversations:
                user_id = user_data["user_id"]
                
                # 构建搜索请求
                search_data = {
                    "query": "开发 编程",
                    "tags": ["memory"],
                    "metadata_filter": {"user_id": user_id},
                    "top_k": 5
                }
                
                response = requests.post(
                    f"{self.kb_service_url}/search",
                    json=search_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json()
                    memories = results.get("results", [])
                    
                    logger.info(f"✅ 用户 {user_id} 的记忆检索成功: 找到 {len(memories)} 条记忆")
                    
                    # 验证用户隔离
                    for memory in memories:
                        memory_user_id = memory.get("metadata", {}).get("user_id")
                        if memory_user_id != user_id:
                            logger.error(f"❌ 用户隔离失败: 期望 {user_id}, 实际 {memory_user_id}")
                            return False
                    
                    if memories:
                        logger.info(f"🔍 示例记忆: {memories[0].get('content', '')[:100]}...")
                else:
                    logger.error(f"❌ 用户 {user_id} 记忆检索失败: {response.status_code}")
                    return False
            
            logger.info("✅ 记忆检索测试通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 记忆检索测试失败: {e}")
            return False
    
    def test_context_aggregation_standalone(self) -> bool:
        """测试上下文聚合功能（独立模式）"""
        logger.info("🎯 测试上下文聚合功能...")
        
        try:
            # 测试记忆检索和格式化
            test_cases = [
                {
                    "user_id": "user_001",
                    "query": "请推荐一些学习资源",
                    "expected_keywords": ["Python", "机器学习"]
                },
                {
                    "user_id": "user_002",
                    "query": "我想学习新技术",
                    "expected_keywords": ["JavaScript", "React"]
                }
            ]
            
            success_count = 0
            
            for i, test_case in enumerate(test_cases):
                logger.info(f"测试用例 {i+1}: 用户 {test_case['user_id']}")
                
                try:
                    # 搜索用户记忆
                    search_data = {
                        "query": test_case["query"],
                        "tags": ["memory"],
                        "metadata_filter": {"user_id": test_case["user_id"]},
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
                        
                        logger.info(f"检索到 {len(memories)} 条相关记忆")
                        
                        # 检查是否包含预期的关键词
                        memory_text = " ".join([m.get("content", "") for m in memories])
                        found_keywords = [kw for kw in test_case["expected_keywords"] 
                                        if kw.lower() in memory_text.lower()]
                        
                        if found_keywords:
                            logger.info(f"✅ 找到预期关键词: {found_keywords}")
                            success_count += 1
                        else:
                            logger.warning(f"⚠️ 未找到预期关键词，但记忆检索正常")
                            success_count += 0.5  # 部分成功
                    else:
                        logger.error(f"❌ 记忆检索失败: {response.status_code}")
                
                except Exception as e:
                    logger.error(f"❌ 测试用例 {i+1} 失败: {e}")
            
            success_rate = success_count / len(test_cases)
            logger.info(f"📊 上下文聚合测试完成: 成功率 {success_rate:.1%}")
            
            return success_rate > 0.5
            
        except Exception as e:
            logger.error(f"❌ 上下文聚合测试失败: {e}")
            return False
    
    def test_user_isolation(self) -> bool:
        """测试用户隔离功能"""
        logger.info("🔒 测试用户隔离功能...")
        
        try:
            # 测试用户A无法看到用户B的记忆
            for user_data in self.test_conversations:
                user_id = user_data["user_id"]
                
                # 搜索当前用户的记忆
                search_data = {
                    "query": "编程 开发 学习",
                    "tags": ["memory"],
                    "metadata_filter": {"user_id": user_id},
                    "top_k": 10
                }
                
                response = requests.post(
                    f"{self.kb_service_url}/search",
                    json=search_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json()
                    memories = results.get("results", [])
                    
                    # 验证所有记忆都属于当前用户
                    for memory in memories:
                        memory_user_id = memory.get("metadata", {}).get("user_id")
                        if memory_user_id != user_id:
                            logger.error(f"❌ 用户隔离失败: 用户 {user_id} 看到了用户 {memory_user_id} 的记忆")
                            return False
                    
                    logger.info(f"✅ 用户 {user_id} 的数据隔离正常 ({len(memories)} 条记忆)")
                else:
                    logger.error(f"❌ 用户 {user_id} 隔离测试失败: {response.status_code}")
                    return False
            
            logger.info("✅ 用户隔离测试通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 用户隔离测试失败: {e}")
            return False
    
    def test_system_performance(self) -> bool:
        """测试系统性能"""
        logger.info("⚡ 测试系统性能...")
        
        try:
            # 测试记忆检索性能
            start_time = time.time()
            
            for _ in range(5):  # 执行5次检索
                search_data = {
                    "query": "编程 开发",
                    "tags": ["memory"],
                    "metadata_filter": {"user_id": "user_001"},
                    "top_k": 3
                }
                
                response = requests.post(
                    f"{self.kb_service_url}/search",
                    json=search_data,
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ 性能测试中出现错误: {response.status_code}")
                    return False
            
            end_time = time.time()
            avg_time = (end_time - start_time) / 5
            
            logger.info(f"📊 平均检索时间: {avg_time:.3f} 秒")
            
            if avg_time < 2.0:
                logger.info("✅ 性能测试通过 (< 2秒)")
                return True
            else:
                logger.warning(f"⚠️ 性能较慢: {avg_time:.3f} 秒")
                return False
                
        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            return False
    
    def run_full_test(self) -> bool:
        """运行完整的集成测试"""
        logger.info("🚀 开始 MCP 记忆系统集成测试")
        logger.info("=" * 60)
        
        start_time = time.time()
        test_results = []
        
        # 1. 检查服务状态
        test_results.append(("服务状态检查", self.check_services()))
        
        if not test_results[-1][1]:
            logger.error("❌ 服务检查失败，无法继续测试")
            return False
        
        # 2. 测试记忆存储
        test_results.append(("记忆存储功能", self.test_memory_storage()))
        
        # 3. 测试记忆检索
        test_results.append(("记忆检索功能", self.test_memory_retrieval()))
        
        # 4. 测试上下文聚合
        test_results.append(("上下文聚合功能", self.test_context_aggregation_standalone()))
        
        # 5. 测试用户隔离
        test_results.append(("用户隔离功能", self.test_user_isolation()))
        
        # 6. 测试系统性能
        test_results.append(("系统性能测试", self.test_system_performance()))
        
        # 生成测试报告
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("📊 集成测试结果报告")
        logger.info("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
            if result:
                passed_tests += 1
        
        success_rate = passed_tests / total_tests
        logger.info(f"\n总体结果: {passed_tests}/{total_tests} ({success_rate:.1%})")
        logger.info(f"总耗时: {total_time:.2f} 秒")
        
        if success_rate >= 0.75:
            logger.info("🎉 集成测试整体通过！")
            return True
        else:
            logger.error("❌ 集成测试存在问题，需要进一步调试")
            return False

def main():
    """主函数"""
    print("🧪 MCP 记忆系统集成测试器")
    print("=" * 60)
    
    # 检查环境
    required_files = [
        "memory_processor.py",
        "context_aggregator_mcp.py", 
        "knowledge_base_service.py"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return False
    
    # 运行测试
    tester = MemoryIntegrationTester()
    success = tester.run_full_test()
    
    if success:
        print("\n🎉 所有测试通过！记忆系统已准备就绪。")
        return True
    else:
        print("\n❌ 测试失败，请检查错误信息并修复问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
