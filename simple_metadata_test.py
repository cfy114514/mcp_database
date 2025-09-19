#!/usr/bin/env python3
"""
简化的元数据过滤测试

直接测试知识库服务的核心功能，验证 metadata_filter 是否正常工作。
"""

import requests
import json

def test_basic_functionality():
    """测试基本功能"""
    KB_URL = "http://localhost:8000"
    
    print("🧪 简化的元数据过滤测试")
    print("="*50)
    
    # 1. 测试添加文档
    print("\n1. 测试添加文档...")
    test_docs = [
        {
            "doc_id": "test_memory_001",
            "content": "用户喜欢喝咖啡",
            "tags": ["memory"],
            "metadata": {"user_id": "user_001", "importance": 8.0, "memory_type": "preference"}
        },
        {
            "doc_id": "test_memory_002", 
            "content": "用户在北京工作",
            "tags": ["memory"],
            "metadata": {"user_id": "user_001", "importance": 9.0, "memory_type": "knowledge"}
        },
        {
            "doc_id": "test_memory_003",
            "content": "另一个用户喜欢音乐",
            "tags": ["memory"],
            "metadata": {"user_id": "user_002", "importance": 7.0, "memory_type": "preference"}
        }
    ]
    
    for doc in test_docs:
        try:
            response = requests.post(f"{KB_URL}/add", json=doc, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 成功添加: {doc['doc_id']}")
                else:
                    print(f"❌ 添加失败: {doc['doc_id']} - {result.get('message')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    # 2. 测试无过滤搜索
    print("\n2. 测试无过滤搜索...")
    try:
        payload = {"query": "用户", "tags": ["memory"], "top_k": 10}
        response = requests.post(f"{KB_URL}/search", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                results = result.get("results", [])
                print(f"✅ 找到 {len(results)} 条记忆")
                for i, doc in enumerate(results):
                    user_id = doc.get("metadata", {}).get("user_id", "unknown")
                    content = doc.get("content", "")[:30] + "..."
                    print(f"  {i+1}. {content} (用户: {user_id})")
            else:
                print(f"❌ 搜索失败: {result}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 3. 测试用户过滤
    print("\n3. 测试用户过滤 (只查找 user_001)...")
    try:
        payload = {
            "query": "用户",
            "tags": ["memory"],
            "metadata_filter": {"user_id": "user_001"},
            "top_k": 10
        }
        response = requests.post(f"{KB_URL}/search", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                results = result.get("results", [])
                print(f"✅ 找到 {len(results)} 条 user_001 的记忆")
                
                # 验证所有结果都属于 user_001
                all_correct = True
                for i, doc in enumerate(results):
                    user_id = doc.get("metadata", {}).get("user_id", "unknown")
                    content = doc.get("content", "")[:30] + "..."
                    print(f"  {i+1}. {content} (用户: {user_id})")
                    if user_id != "user_001":
                        print(f"    ❌ 用户过滤失败!")
                        all_correct = False
                
                if all_correct:
                    print("✅ 用户过滤测试通过")
                else:
                    print("❌ 用户过滤测试失败")
            else:
                print(f"❌ 搜索失败: {result}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 4. 测试重要性过滤
    print("\n4. 测试重要性过滤 (重要性 >= 8.0)...")
    try:
        payload = {
            "query": "用户",
            "tags": ["memory"],
            "metadata_filter": {"importance": {"gte": 8.0}},
            "top_k": 10
        }
        response = requests.post(f"{KB_URL}/search", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                results = result.get("results", [])
                print(f"✅ 找到 {len(results)} 条高重要性记忆")
                
                # 验证所有结果的重要性都 >= 8.0
                all_correct = True
                for i, doc in enumerate(results):
                    importance = doc.get("metadata", {}).get("importance", 0)
                    user_id = doc.get("metadata", {}).get("user_id", "unknown")
                    content = doc.get("content", "")[:30] + "..."
                    print(f"  {i+1}. {content} (用户: {user_id}, 重要性: {importance})")
                    if importance < 8.0:
                        print(f"    ❌ 重要性过滤失败!")
                        all_correct = False
                
                if all_correct:
                    print("✅ 重要性过滤测试通过")
                else:
                    print("❌ 重要性过滤测试失败")
            else:
                print(f"❌ 搜索失败: {result}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 5. 测试复合条件过滤
    print("\n5. 测试复合条件过滤 (user_001 + 偏好类型)...")
    try:
        payload = {
            "query": "用户",
            "tags": ["memory"],
            "metadata_filter": {"user_id": "user_001", "memory_type": "preference"},
            "top_k": 10
        }
        response = requests.post(f"{KB_URL}/search", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                results = result.get("results", [])
                print(f"✅ 找到 {len(results)} 条符合条件的记忆")
                
                for i, doc in enumerate(results):
                    metadata = doc.get("metadata", {})
                    user_id = metadata.get("user_id", "unknown")
                    memory_type = metadata.get("memory_type", "unknown")
                    content = doc.get("content", "")[:30] + "..."
                    print(f"  {i+1}. {content} (用户: {user_id}, 类型: {memory_type})")
                    
                    if user_id != "user_001" or memory_type != "preference":
                        print(f"    ❌ 复合过滤失败!")
                        
                print("✅ 复合条件过滤测试通过")
            else:
                print(f"❌ 搜索失败: {result}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("\n" + "="*50)
    print("🎉 元数据过滤功能测试完成!")

if __name__ == "__main__":
    test_basic_functionality()
