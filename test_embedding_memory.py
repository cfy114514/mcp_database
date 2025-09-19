#!/usr/bin/env python3
"""
MCP Embedding记忆系统统一测试脚本

整合所有测试功能，提供完整的系统测试套件：
1. 环境和配置测试
2. 记忆存储和检索测试  
3. 元数据过滤和用户隔离测试
4. 向量化搜索和性能测试
5. 集成和端到端测试

Usage:
    python test_embedding_memory.py --help
    python test_embedding_memory.py env        # 环境测试
    python test_embedding_memory.py api        # API配置测试
    python test_embedding_memory.py storage    # 存储功能测试
    python test_embedding_memory.py filter     # 过滤功能测试
    python test_embedding_memory.py integration # 集成测试
    python test_embedding_memory.py all        # 完整测试
"""

import os
import sys
import json
import time
import asyncio
import argparse
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EmbeddingMemoryTest")

class Colors:
    """控制台颜色"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """打印状态信息"""
    color_map = {
        "SUCCESS": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARNING": Colors.YELLOW,
        "INFO": Colors.BLUE
    }
    color = color_map.get(status, Colors.NC)
    print(f"{color}[{status}]{Colors.NC} {message}")

def print_section(title: str):
    """打印节标题"""
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print(f"{'='*70}")

class EnvironmentTester:
    """环境和配置测试器"""
    
    def test_python_environment(self) -> bool:
        """测试Python环境"""
        print_section("Python 环境测试")
        
        try:
            print_status(f"Python 版本: {sys.version}")
            print_status(f"Python 可执行文件: {sys.executable}")
            print_status(f"当前工作目录: {os.getcwd()}")
            return True
        except Exception as e:
            print_status(f"Python环境测试失败: {e}", "ERROR")
            return False
    
    def test_module_imports(self) -> bool:
        """测试关键模块导入"""
        print_section("模块导入测试")
        
        modules_to_test = [
            ('requests', 'HTTP 请求库'),
            ('numpy', 'NumPy 数值计算'),
            ('fastapi', 'FastAPI Web框架'),
            ('dotenv', '环境变量加载'),
            ('json', 'JSON 模块（内置）'),
            ('logging', '日志模块（内置）'),
            ('typing', '类型提示（内置）')
        ]
        
        success_count = 0
        for module_name, description in modules_to_test:
            try:
                __import__(module_name)
                print_status(f"✓ {module_name} - {description}", "SUCCESS")
                success_count += 1
            except ImportError as e:
                print_status(f"✗ {module_name} - {description}: {e}", "ERROR")
        
        result = success_count == len(modules_to_test)
        print_status(f"模块导入测试: {success_count}/{len(modules_to_test)} 成功", 
                    "SUCCESS" if result else "ERROR")
        return result
    
    def test_file_access(self) -> bool:
        """测试文件访问权限"""
        print_section("文件访问测试")
        
        try:
            key_files = [
                "embedding_memory_processor.py",
                "embedding_context_aggregator_mcp.py", 
                "knowledge_base_service.py",
                "mcp_memory_manager.py"
            ]
            
            missing_files = []
            for file in key_files:
                if not Path(file).exists():
                    missing_files.append(file)
                else:
                    print_status(f"✓ {file} 存在")
            
            if missing_files:
                print_status(f"缺失关键文件: {missing_files}", "ERROR")
                return False
            
            print_status("所有关键文件检查通过", "SUCCESS")
            return True
            
        except Exception as e:
            print_status(f"文件访问测试失败: {e}", "ERROR")
            return False


class APIConfigTester:
    """API配置测试器"""
    
    def __init__(self):
        self.embedding_api_key = os.getenv("EMBEDDING_API_KEY")
        self.embedding_api_url = os.getenv("EMBEDDING_API_URL", "https://api.siliconflow.cn/v1/embeddings")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
        self.kb_url = f"http://localhost:{os.getenv('KB_PORT', '8001')}"
    
    def test_embedding_api(self) -> bool:
        """测试embedding API配置和连接"""
        print_section("Embedding API 测试")
        
        if not self.embedding_api_key:
            print_status("未设置 EMBEDDING_API_KEY", "ERROR")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.embedding_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.embedding_model,
                "input": "测试文本",
                "encoding_format": "float"
            }
            
            print_status(f"测试URL: {self.embedding_api_url}")
            print_status(f"测试模型: {self.embedding_model}")
            
            response = requests.post(
                self.embedding_api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0]["embedding"]
                    print_status(f"✓ API测试成功，向量维度: {len(embedding)}", "SUCCESS")
                    return True
                else:
                    print_status(f"API响应格式错误: {result}", "ERROR")
                    return False
            else:
                print_status(f"API请求失败: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"Embedding API测试失败: {e}", "ERROR")
            return False
    
    def test_knowledge_base_service(self) -> bool:
        """测试知识库服务连接"""
        print_section("知识库服务测试")
        
        try:
            print_status(f"测试知识库服务: {self.kb_url}")
            
            # 测试健康检查
            response = requests.get(f"{self.kb_url}/health", timeout=10)
            if response.status_code == 200:
                print_status("✓ 知识库服务健康检查通过", "SUCCESS")
                
                # 测试统计信息
                stats_response = requests.get(f"{self.kb_url}/stats", timeout=10)
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    print_status(f"✓ 服务统计: {stats}", "SUCCESS")
                    return True
                else:
                    print_status("服务统计接口异常", "WARNING")
                    return True  # 健康检查通过就算成功
            else:
                print_status(f"知识库服务连接失败: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"知识库服务测试失败: {e}", "ERROR")
            return False


class MemoryStorageTester:
    """记忆存储功能测试器"""
    
    def __init__(self):
        self.kb_url = f"http://localhost:{os.getenv('KB_PORT', '8001')}"
    
    def test_memory_storage(self) -> bool:
        """测试记忆存储功能"""
        print_section("记忆存储测试")
        
        try:
            # 测试文档添加
            test_doc = {
                "doc_id": f"test_memory_{int(time.time())}",
                "content": "用户喜欢喝咖啡，每天早上都要来一杯拿铁",
                "tags": ["memory", "preference"],
                "metadata": {
                    "user_id": "test_user_001",
                    "importance": 8.0,
                    "memory_type": "preference",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            print_status(f"添加测试记忆: {test_doc['content'][:30]}...")
            
            response = requests.post(
                f"{self.kb_url}/add",
                json=test_doc,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print_status(f"✓ 记忆存储成功: {result}", "SUCCESS")
                return True
            else:
                print_status(f"记忆存储失败: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"记忆存储测试失败: {e}", "ERROR")
            return False
    
    def test_memory_retrieval(self) -> bool:
        """测试记忆检索功能"""
        print_section("记忆检索测试")
        
        try:
            # 测试搜索
            search_data = {
                "query": "咖啡 拿铁 习惯",
                "tags": ["memory"],
                "top_k": 5
            }
            
            print_status(f"搜索查询: {search_data['query']}")
            
            response = requests.post(
                f"{self.kb_url}/search",
                json=search_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    results = result.get("results", [])
                    print_status(f"✓ 检索成功，找到 {len(results)} 条记忆", "SUCCESS")
                    
                    # 显示前3条结果
                    for i, doc in enumerate(results[:3]):
                        content = doc.get("content", "")[:50]
                        print_status(f"  {i+1}. {content}...")
                    
                    return True
                else:
                    print_status(f"检索失败: {result}", "ERROR")
                    return False
            else:
                print_status(f"检索请求失败: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"记忆检索测试失败: {e}", "ERROR")
            return False
    
    def test_vectorized_search(self) -> bool:
        """测试向量化搜索"""
        print_section("向量化搜索测试")
        
        test_queries = [
            {
                "name": "咖啡相关查询",
                "query": "咖啡 喝咖啡 习惯",
                "tags": ["memory"],
                "top_k": 3
            },
            {
                "name": "地址相关查询", 
                "query": "住址 位置 地方",
                "tags": ["memory"],
                "top_k": 3
            },
            {
                "name": "情感相关查询",
                "query": "心情 感受 情绪",
                "tags": ["memory"],
                "top_k": 3
            }
        ]
        
        success_count = 0
        for test_case in test_queries:
            try:
                print_status(f"测试 {test_case['name']}: {test_case['query']}")
                
                response = requests.post(
                    f"{self.kb_url}/search",
                    json=test_case,
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        results = result.get("results", [])
                        print_status(f"  ✓ 找到 {len(results)} 条相关记忆", "SUCCESS")
                        success_count += 1
                    else:
                        print_status(f"  ✗ 搜索失败: {result}", "ERROR")
                else:
                    print_status(f"  ✗ 请求失败: {response.status_code}", "ERROR")
                    
            except Exception as e:
                print_status(f"  ✗ 测试失败: {e}", "ERROR")
        
        result = success_count == len(test_queries)
        print_status(f"向量化搜索测试: {success_count}/{len(test_queries)} 成功", 
                    "SUCCESS" if result else "ERROR")
        return result


class MetadataFilterTester:
    """元数据过滤测试器"""
    
    def __init__(self):
        self.kb_url = f"http://localhost:{os.getenv('KB_PORT', '8001')}"
    
    def setup_test_data(self) -> bool:
        """设置测试数据"""
        print_section("设置元数据过滤测试数据")
        
        test_docs = [
            {
                "doc_id": "filter_test_001",
                "content": "用户张三喜欢喝咖啡",
                "tags": ["memory"],
                "metadata": {"user_id": "user_001", "importance": 8.0, "memory_type": "preference"}
            },
            {
                "doc_id": "filter_test_002", 
                "content": "用户张三在北京工作",
                "tags": ["memory"],
                "metadata": {"user_id": "user_001", "importance": 9.0, "memory_type": "knowledge"}
            },
            {
                "doc_id": "filter_test_003",
                "content": "用户李四喜欢听音乐",
                "tags": ["memory"],
                "metadata": {"user_id": "user_002", "importance": 7.0, "memory_type": "preference"}
            },
            {
                "doc_id": "filter_test_004",
                "content": "用户李四昨天很高兴",
                "tags": ["memory"],
                "metadata": {"user_id": "user_002", "importance": 6.0, "memory_type": "emotional"}
            }
        ]
        
        success_count = 0
        for doc in test_docs:
            try:
                response = requests.post(f"{self.kb_url}/add", json=doc, timeout=20)
                if response.status_code == 200:
                    success_count += 1
                    print_status(f"✓ 添加测试文档: {doc['doc_id']}")
                else:
                    print_status(f"✗ 添加文档失败: {doc['doc_id']}", "ERROR")
            except Exception as e:
                print_status(f"✗ 添加文档异常: {doc['doc_id']} - {e}", "ERROR")
        
        result = success_count == len(test_docs)
        print_status(f"测试数据设置: {success_count}/{len(test_docs)} 成功", 
                    "SUCCESS" if result else "ERROR")
        return result
    
    def test_user_isolation(self) -> bool:
        """测试用户数据隔离"""
        print_section("用户数据隔离测试")
        
        try:
            # 测试用户1的数据
            search_data = {
                "query": "喜欢",
                "tags": ["memory"],
                "metadata_filter": {"user_id": "user_001"},
                "top_k": 10
            }
            
            response = requests.post(f"{self.kb_url}/search", json=search_data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    results = result.get("results", [])
                    user_001_count = len(results)
                    
                    # 验证只返回user_001的数据
                    for doc in results:
                        metadata = doc.get("metadata", {})
                        if metadata.get("user_id") != "user_001":
                            print_status("✗ 数据隔离失败：返回了其他用户数据", "ERROR")
                            return False
                    
                    print_status(f"✓ 用户user_001独立数据: {user_001_count} 条", "SUCCESS")
                    
                    # 测试用户2的数据
                    search_data["metadata_filter"] = {"user_id": "user_002"}
                    response = requests.post(f"{self.kb_url}/search", json=search_data, timeout=20)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            results = result.get("results", [])
                            user_002_count = len(results)
                            
                            # 验证只返回user_002的数据
                            for doc in results:
                                metadata = doc.get("metadata", {})
                                if metadata.get("user_id") != "user_002":
                                    print_status("✗ 数据隔离失败：返回了其他用户数据", "ERROR")
                                    return False
                            
                            print_status(f"✓ 用户user_002独立数据: {user_002_count} 条", "SUCCESS")
                            print_status("✓ 用户数据隔离测试通过", "SUCCESS")
                            return True
                        else:
                            print_status(f"用户2搜索失败: {result}", "ERROR")
                            return False
                    else:
                        print_status(f"用户2搜索请求失败: {response.status_code}", "ERROR")
                        return False
                else:
                    print_status(f"用户1搜索失败: {result}", "ERROR")
                    return False
            else:
                print_status(f"用户1搜索请求失败: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"用户隔离测试失败: {e}", "ERROR")
            return False
    
    def test_importance_filtering(self) -> bool:
        """测试重要性过滤"""
        print_section("重要性过滤测试")
        
        try:
            # 测试高重要性记忆（importance >= 8.0）
            search_data = {
                "query": "用户",
                "tags": ["memory"],
                "metadata_filter": {"importance": {"$gte": 8.0}},
                "top_k": 10
            }
            
            response = requests.post(f"{self.kb_url}/search", json=search_data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    results = result.get("results", [])
                    high_importance_count = len(results)
                    
                    # 验证所有结果的重要性都 >= 8.0
                    for doc in results:
                        importance = doc.get("metadata", {}).get("importance", 0)
                        if importance < 8.0:
                            print_status(f"✗ 重要性过滤失败：found importance {importance} < 8.0", "ERROR")
                            return False
                    
                    print_status(f"✓ 高重要性记忆: {high_importance_count} 条", "SUCCESS")
                    print_status("✓ 重要性过滤测试通过", "SUCCESS")
                    return True
                else:
                    print_status(f"重要性过滤搜索失败: {result}", "ERROR")
                    return False
            else:
                print_status(f"重要性过滤请求失败: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"重要性过滤测试失败: {e}", "ERROR")
            return False
    
    def test_memory_type_filtering(self) -> bool:
        """测试记忆类型过滤"""
        print_section("记忆类型过滤测试")
        
        memory_types = ["preference", "knowledge", "emotional"]
        
        for memory_type in memory_types:
            try:
                search_data = {
                    "query": "用户",
                    "tags": ["memory"],
                    "metadata_filter": {"memory_type": memory_type},
                    "top_k": 10
                }
                
                response = requests.post(f"{self.kb_url}/search", json=search_data, timeout=20)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        results = result.get("results", [])
                        
                        # 验证所有结果的类型都匹配
                        for doc in results:
                            doc_type = doc.get("metadata", {}).get("memory_type")
                            if doc_type != memory_type:
                                print_status(f"✗ 类型过滤失败：expected {memory_type}, got {doc_type}", "ERROR")
                                return False
                        
                        print_status(f"✓ {memory_type} 类型记忆: {len(results)} 条", "SUCCESS")
                    else:
                        print_status(f"类型 {memory_type} 搜索失败: {result}", "ERROR")
                        return False
                else:
                    print_status(f"类型 {memory_type} 请求失败: {response.status_code}", "ERROR")
                    return False
                    
            except Exception as e:
                print_status(f"记忆类型 {memory_type} 测试失败: {e}", "ERROR")
                return False
        
        print_status("✓ 记忆类型过滤测试通过", "SUCCESS")
        return True


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self):
        self.kb_url = f"http://localhost:{os.getenv('KB_PORT', '8001')}"
    
    def test_end_to_end_workflow(self) -> bool:
        """测试端到端工作流程"""
        print_section("端到端工作流程测试")
        
        try:
            # 1. 模拟对话和记忆提取
            conversations = [
                {
                    "user_id": "integration_user_001",
                    "content": "我叫王小明，是一名程序员，平时喜欢喝美式咖啡",
                    "memory_type": "personal",
                    "importance": 9.0
                },
                {
                    "user_id": "integration_user_001", 
                    "content": "我住在上海浦东新区，每天坐地铁上班",
                    "memory_type": "knowledge",
                    "importance": 8.0
                },
                {
                    "user_id": "integration_user_001",
                    "content": "昨天加班到很晚，感觉有点累",
                    "memory_type": "emotional",
                    "importance": 6.0
                }
            ]
            
            print_status("1. 存储模拟对话记忆...")
            stored_memories = []
            
            for i, conv in enumerate(conversations):
                doc_data = {
                    "doc_id": f"integration_memory_{int(time.time())}_{i}",
                    "content": conv["content"],
                    "tags": ["memory", "integration_test"],
                    "metadata": {
                        "user_id": conv["user_id"],
                        "memory_type": conv["memory_type"],
                        "importance": conv["importance"],
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                response = requests.post(f"{self.kb_url}/add", json=doc_data, timeout=20)
                if response.status_code == 200:
                    stored_memories.append(doc_data)
                    print_status(f"  ✓ 存储记忆: {conv['content'][:30]}...")
                else:
                    print_status(f"  ✗ 存储失败: {response.status_code}", "ERROR")
                    return False
            
            # 2. 测试上下文检索和聚合
            print_status("2. 测试上下文检索...")
            
            search_queries = [
                "告诉我关于王小明的基本信息",
                "王小明住在哪里",
                "王小明最近的心情怎么样"
            ]
            
            for query in search_queries:
                search_data = {
                    "query": query,
                    "tags": ["memory"],
                    "metadata_filter": {"user_id": "integration_user_001"},
                    "top_k": 5
                }
                
                response = requests.post(f"{self.kb_url}/search", json=search_data, timeout=20)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        results = result.get("results", [])
                        print_status(f"  ✓ 查询'{query[:20]}...' 找到 {len(results)} 条相关记忆")
                        
                        # 显示最相关的记忆
                        if results:
                            best_match = results[0]
                            content = best_match.get("content", "")[:50]
                            print_status(f"    最相关: {content}...")
                    else:
                        print_status(f"  ✗ 查询失败: {result}", "ERROR")
                        return False
                else:
                    print_status(f"  ✗ 查询请求失败: {response.status_code}", "ERROR")
                    return False
            
            # 3. 测试记忆聚合和上下文构建
            print_status("3. 测试记忆聚合...")
            
            # 获取用户的所有记忆进行聚合
            search_data = {
                "query": "王小明的所有信息",
                "tags": ["memory"],
                "metadata_filter": {"user_id": "integration_user_001"},
                "top_k": 10
            }
            
            response = requests.post(f"{self.kb_url}/search", json=search_data, timeout=20)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    all_memories = result.get("results", [])
                    
                    # 按重要性排序
                    sorted_memories = sorted(
                        all_memories, 
                        key=lambda x: x.get("metadata", {}).get("importance", 0), 
                        reverse=True
                    )
                    
                    # 构建上下文
                    context_parts = []
                    for memory in sorted_memories[:3]:  # 取前3个最重要的记忆
                        content = memory.get("content", "")
                        memory_type = memory.get("metadata", {}).get("memory_type", "")
                        importance = memory.get("metadata", {}).get("importance", 0)
                        context_parts.append(f"[{memory_type}] {content} (重要性: {importance})")
                    
                    aggregated_context = "\n".join(context_parts)
                    print_status("  ✓ 聚合上下文构建成功:")
                    print_status(f"    {aggregated_context[:100]}...")
                    
                    print_status("✓ 端到端工作流程测试通过", "SUCCESS")
                    return True
                else:
                    print_status(f"聚合搜索失败: {result}", "ERROR")
                    return False
            else:
                print_status(f"聚合搜索请求失败: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"端到端工作流程测试失败: {e}", "ERROR")
            return False
    
    def test_system_performance(self) -> bool:
        """测试系统性能"""
        print_section("系统性能测试")
        
        try:
            # 测试批量存储性能
            print_status("测试批量存储性能...")
            
            start_time = time.time()
            batch_size = 10
            
            for i in range(batch_size):
                doc_data = {
                    "doc_id": f"perf_test_{int(time.time())}_{i}",
                    "content": f"性能测试文档 {i}：这是一个用于测试系统性能的文档，包含一些测试内容。",
                    "tags": ["performance_test"],
                    "metadata": {
                        "user_id": "perf_test_user",
                        "batch_id": int(time.time()),
                        "index": i
                    }
                }
                
                response = requests.post(f"{self.kb_url}/add", json=doc_data, timeout=10)
                if response.status_code != 200:
                    print_status(f"批量存储失败: {response.status_code}", "ERROR")
                    return False
            
            storage_time = time.time() - start_time
            avg_storage_time = (storage_time / batch_size) * 1000  # 毫秒
            
            print_status(f"✓ 批量存储 {batch_size} 个文档耗时: {storage_time:.2f}s")
            print_status(f"✓ 平均存储时间: {avg_storage_time:.1f}ms/文档")
            
            # 测试批量检索性能
            print_status("测试批量检索性能...")
            
            start_time = time.time()
            search_count = 5
            
            for i in range(search_count):
                search_data = {
                    "query": f"性能测试 {i}",
                    "tags": ["performance_test"],
                    "top_k": 5
                }
                
                response = requests.post(f"{self.kb_url}/search", json=search_data, timeout=10)
                if response.status_code != 200:
                    print_status(f"批量检索失败: {response.status_code}", "ERROR")
                    return False
            
            retrieval_time = time.time() - start_time
            avg_retrieval_time = (retrieval_time / search_count) * 1000  # 毫秒
            
            print_status(f"✓ 批量检索 {search_count} 次耗时: {retrieval_time:.2f}s")
            print_status(f"✓ 平均检索时间: {avg_retrieval_time:.1f}ms/查询")
            
            # 性能评估
            if avg_storage_time < 500 and avg_retrieval_time < 200:
                print_status("✓ 系统性能测试通过", "SUCCESS")
                return True
            else:
                print_status("⚠ 系统性能较慢，建议优化", "WARNING")
                return True  # 性能慢不算失败，只是警告
                
        except Exception as e:
            print_status(f"系统性能测试失败: {e}", "ERROR")
            return False


class EmbeddingMemoryTestSuite:
    """Embedding记忆系统测试套件"""
    
    def __init__(self):
        self.env_tester = EnvironmentTester()
        self.api_tester = APIConfigTester()
        self.storage_tester = MemoryStorageTester()
        self.filter_tester = MetadataFilterTester()
        self.integration_tester = IntegrationTester()
    
    def run_environment_tests(self) -> bool:
        """运行环境测试"""
        print_section("🔧 环境和配置测试")
        
        results = [
            self.env_tester.test_python_environment(),
            self.env_tester.test_module_imports(),
            self.env_tester.test_file_access()
        ]
        
        success = all(results)
        print_status(f"环境测试结果: {'通过' if success else '失败'}", 
                    "SUCCESS" if success else "ERROR")
        return success
    
    def run_api_tests(self) -> bool:
        """运行API配置测试"""
        print_section("🔌 API配置测试")
        
        results = [
            self.api_tester.test_embedding_api(),
            self.api_tester.test_knowledge_base_service()
        ]
        
        success = all(results)
        print_status(f"API测试结果: {'通过' if success else '失败'}", 
                    "SUCCESS" if success else "ERROR")
        return success
    
    def run_storage_tests(self) -> bool:
        """运行存储功能测试"""
        print_section("💾 存储功能测试")
        
        results = [
            self.storage_tester.test_memory_storage(),
            self.storage_tester.test_memory_retrieval(),
            self.storage_tester.test_vectorized_search()
        ]
        
        success = all(results)
        print_status(f"存储测试结果: {'通过' if success else '失败'}", 
                    "SUCCESS" if success else "ERROR")
        return success
    
    def run_filter_tests(self) -> bool:
        """运行过滤功能测试"""
        print_section("🔍 过滤功能测试")
        
        # 先设置测试数据
        if not self.filter_tester.setup_test_data():
            print_status("测试数据设置失败", "ERROR")
            return False
        
        results = [
            self.filter_tester.test_user_isolation(),
            self.filter_tester.test_importance_filtering(),
            self.filter_tester.test_memory_type_filtering()
        ]
        
        success = all(results)
        print_status(f"过滤测试结果: {'通过' if success else '失败'}", 
                    "SUCCESS" if success else "ERROR")
        return success
    
    def run_integration_tests(self) -> bool:
        """运行集成测试"""
        print_section("🔗 集成测试")
        
        results = [
            self.integration_tester.test_end_to_end_workflow(),
            self.integration_tester.test_system_performance()
        ]
        
        success = all(results)
        print_status(f"集成测试结果: {'通过' if success else '失败'}", 
                    "SUCCESS" if success else "ERROR")
        return success
    
    def run_all_tests(self) -> bool:
        """运行完整测试套件"""
        print_section("🧪 MCP Embedding记忆系统完整测试套件")
        
        test_results = []
        
        # 按顺序运行所有测试
        test_results.append(("环境测试", self.run_environment_tests()))
        test_results.append(("API测试", self.run_api_tests()))
        test_results.append(("存储测试", self.run_storage_tests()))
        test_results.append(("过滤测试", self.run_filter_tests()))
        test_results.append(("集成测试", self.run_integration_tests()))
        
        # 汇总结果
        print_section("📊 测试结果汇总")
        
        passed_count = 0
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print_status(f"{test_name}: {status}")
            if result:
                passed_count += 1
        
        total_tests = len(test_results)
        success_rate = (passed_count / total_tests) * 100
        
        print_status(f"总体测试结果: {passed_count}/{total_tests} 通过 ({success_rate:.1f}%)")
        
        if passed_count == total_tests:
            print_status("🎉 所有测试通过！系统运行正常", "SUCCESS")
            return True
        else:
            print_status("⚠️ 部分测试失败，请检查相关组件", "WARNING")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP Embedding记忆系统测试套件")
    parser.add_argument("test_type", nargs="?", default="all",
                       choices=["env", "api", "storage", "filter", "integration", "all"],
                       help="测试类型")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建测试套件
    test_suite = EmbeddingMemoryTestSuite()
    
    # 根据参数运行相应测试
    if args.test_type == "env":
        success = test_suite.run_environment_tests()
    elif args.test_type == "api":
        success = test_suite.run_api_tests()
    elif args.test_type == "storage":
        success = test_suite.run_storage_tests()
    elif args.test_type == "filter":
        success = test_suite.run_filter_tests()
    elif args.test_type == "integration":
        success = test_suite.run_integration_tests()
    elif args.test_type == "all":
        success = test_suite.run_all_tests()
    else:
        print_status("未知的测试类型", "ERROR")
        return 1
    
    # 返回退出码
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
