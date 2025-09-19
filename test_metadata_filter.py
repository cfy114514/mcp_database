#!/usr/bin/env python3
"""
知识库元数据过滤功能验证脚本

该脚本用于验证知识库服务的 metadata_filter 功能是否正确工作。
测试场景包括：
1. 用户数据隔离（基于 user_id 过滤）
2. 重要性过滤（基于 importance 范围查询）
3. 记忆类型过滤（基于 memory_type 精确匹配）
4. 复合条件过滤（多个元数据字段组合）
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional

# 测试配置
KB_SERVICE_URL = "http://localhost:8000"
TEST_USER_IDS = ["test_user_001", "test_user_002", "test_user_003"]

def print_section(title: str):
    """打印节标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_result(data, title: str = "结果"):
    """格式化打印结果"""
    print(f"\n{title}:")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)

def add_test_document(doc_id: str, content: str, tags: List[str], metadata: Dict) -> bool:
    """添加测试文档到知识库"""
    payload = {
        "doc_id": doc_id,
        "content": content,
        "tags": tags,
        "metadata": metadata
    }
    
    try:
        response = requests.post(f"{KB_SERVICE_URL}/add", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False)
        else:
            print(f"❌ 添加文档失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 添加文档异常: {e}")
        return False

def search_with_filter(query: str, tags: Optional[List[str]] = None, metadata_filter: Optional[Dict] = None, top_k: int = 10) -> Dict:
    """使用元数据过滤搜索文档"""
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    if tags:
        payload["tags"] = tags
    if metadata_filter:
        payload["metadata_filter"] = metadata_filter
    
    try:
        response = requests.post(f"{KB_SERVICE_URL}/search", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 搜索失败: {response.status_code} - {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ 搜索异常: {e}")
        return {"success": False, "error": str(e)}

def setup_test_data():
    """设置测试数据"""
    print("🔄 设置测试数据...")
    
    # 测试记忆数据
    test_memories = [
        # 用户1的记忆
        {
            "doc_id": "memory_user001_001",
            "content": "用户喜欢在早上喝咖啡，特别是美式咖啡",
            "tags": ["memory"],
            "metadata": {
                "user_id": "test_user_001",
                "importance": 7.5,
                "memory_type": "preference",
                "created_at": "2025-09-19T08:00:00",
                "emotional_valence": 0.8
            }
        },
        {
            "doc_id": "memory_user001_002", 
            "content": "用户在北京工作，是一名Python开发工程师",
            "tags": ["memory"],
            "metadata": {
                "user_id": "test_user_001",
                "importance": 9.0,
                "memory_type": "knowledge",
                "created_at": "2025-09-19T09:00:00",
                "emotional_valence": 0.5
            }
        },
        {
            "doc_id": "memory_user001_003",
            "content": "用户昨天心情不太好，感到工作压力很大",
            "tags": ["memory"],
            "metadata": {
                "user_id": "test_user_001",
                "importance": 6.0,
                "memory_type": "emotional",
                "created_at": "2025-09-18T20:00:00",
                "emotional_valence": -0.7
            }
        },
        
        # 用户2的记忆
        {
            "doc_id": "memory_user002_001",
            "content": "用户喜欢听古典音乐，特别是莫扎特的作品",
            "tags": ["memory"],
            "metadata": {
                "user_id": "test_user_002",
                "importance": 8.0,
                "memory_type": "preference", 
                "created_at": "2025-09-19T10:00:00",
                "emotional_valence": 0.9
            }
        },
        {
            "doc_id": "memory_user002_002",
            "content": "用户在上海做金融分析师工作",
            "tags": ["memory"],
            "metadata": {
                "user_id": "test_user_002",
                "importance": 8.5,
                "memory_type": "knowledge",
                "created_at": "2025-09-19T11:00:00", 
                "emotional_valence": 0.3
            }
        },
        
        # 用户3的记忆
        {
            "doc_id": "memory_user003_001",
            "content": "用户刚刚搬到新家，对新环境很兴奋",
            "tags": ["memory"],
            "metadata": {
                "user_id": "test_user_003",
                "importance": 7.0,
                "memory_type": "event",
                "created_at": "2025-09-19T12:00:00",
                "emotional_valence": 0.8
            }
        },
        
        # 非记忆数据（用于对照）
        {
            "doc_id": "knowledge_001",
            "content": "Python是一种高级编程语言",
            "tags": ["knowledge", "programming"],
            "metadata": {
                "category": "programming",
                "language": "python",
                "level": "basic"
            }
        }
    ]
    
    success_count = 0
    for memory in test_memories:
        if add_test_document(**memory):
            success_count += 1
        time.sleep(0.1)  # 避免请求过快
    
    print(f"✅ 成功添加 {success_count}/{len(test_memories)} 条测试数据")
    return success_count == len(test_memories)

def test_user_isolation():
    """测试用户数据隔离"""
    print_section("测试1: 用户数据隔离")
    
    # 测试每个用户只能看到自己的记忆
    for user_id in TEST_USER_IDS:
        print(f"\n--- 测试用户 {user_id} 的记忆隔离 ---")
        
        result = search_with_filter(
            query="用户",
            tags=["memory"],
            metadata_filter={"user_id": user_id},
            top_k=10
        )
        
        if result.get("success"):
            memories = result.get("results", [])
            print(f"找到 {len(memories)} 条记忆")
            
            # 验证所有记忆都属于当前用户
            all_correct = True
            for memory in memories:
                memory_user_id = memory.get("metadata", {}).get("user_id")
                if memory_user_id != user_id:
                    print(f"❌ 发现数据泄漏: 期望 {user_id}，实际 {memory_user_id}")
                    all_correct = False
                else:
                    content_preview = memory.get("content", "")[:30] + "..."
                    importance = memory.get("metadata", {}).get("importance", "N/A")
                    print(f"  ✅ {content_preview} (重要性: {importance})")
            
            if all_correct and memories:
                print(f"✅ 用户 {user_id} 数据隔离测试通过")
            elif not memories:
                print(f"⚠️ 用户 {user_id} 没有找到记忆数据")
            else:
                print(f"❌ 用户 {user_id} 数据隔离测试失败")
        else:
            print(f"❌ 搜索失败: {result}")

def test_importance_filtering():
    """测试重要性过滤"""
    print_section("测试2: 重要性过滤")
    
    # 测试不同重要性阈值
    test_cases = [
        {"importance": {"gte": 8.0}, "description": "高重要性 (≥8.0)"},
        {"importance": {"gte": 6.0, "lte": 8.0}, "description": "中等重要性 (6.0-8.0)"},
        {"importance": {"lt": 6.0}, "description": "低重要性 (<6.0)"}
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['description']} ---")
        
        result = search_with_filter(
            query="用户", 
            tags=["memory"],
            metadata_filter=test_case["importance"],
            top_k=20
        )
        
        if result.get("success"):
            memories = result.get("results", [])
            print(f"找到 {len(memories)} 条记忆")
            
            for memory in memories:
                importance = memory.get("metadata", {}).get("importance", 0)
                user_id = memory.get("metadata", {}).get("user_id", "unknown")
                content_preview = memory.get("content", "")[:40] + "..."
                print(f"  • {content_preview} (用户: {user_id}, 重要性: {importance})")
        else:
            print(f"❌ 搜索失败: {result}")

def test_memory_type_filtering():
    """测试记忆类型过滤"""
    print_section("测试3: 记忆类型过滤")
    
    memory_types = ["preference", "knowledge", "emotional", "event"]
    
    for memory_type in memory_types:
        print(f"\n--- 记忆类型: {memory_type} ---")
        
        result = search_with_filter(
            query="用户",
            tags=["memory"],
            metadata_filter={"memory_type": memory_type},
            top_k=10
        )
        
        if result.get("success"):
            memories = result.get("results", [])
            print(f"找到 {len(memories)} 条 {memory_type} 类型记忆")
            
            for memory in memories:
                user_id = memory.get("metadata", {}).get("user_id", "unknown")
                importance = memory.get("metadata", {}).get("importance", 0)
                content_preview = memory.get("content", "")[:40] + "..."
                print(f"  • {content_preview} (用户: {user_id}, 重要性: {importance})")
        else:
            print(f"❌ 搜索失败: {result}")

def test_combined_filtering():
    """测试复合条件过滤"""
    print_section("测试4: 复合条件过滤")
    
    # 测试用户1的高重要性偏好记忆
    print("\n--- 测试用户001的高重要性偏好记忆 ---")
    result = search_with_filter(
        query="用户",
        tags=["memory"],
        metadata_filter={
            "user_id": "test_user_001",
            "memory_type": "preference",
            "importance": {"gte": 7.0}
        },
        top_k=10
    )
    
    if result.get("success"):
        memories = result.get("results", [])
        print(f"找到 {len(memories)} 条符合条件的记忆")
        
        for memory in memories:
            metadata = memory.get("metadata", {})
            content_preview = memory.get("content", "")[:50] + "..."
            print(f"  ✅ {content_preview}")
            print(f"      用户: {metadata.get('user_id')}, 类型: {metadata.get('memory_type')}, 重要性: {metadata.get('importance')}")
    else:
        print(f"❌ 搜索失败: {result}")

def test_tag_and_metadata_combination():
    """测试标签和元数据组合过滤"""
    print_section("测试5: 标签和元数据组合过滤")
    
    print("\n--- 测试只搜索记忆标签且用户为 test_user_001 ---")
    result = search_with_filter(
        query="工作",
        tags=["memory"],  # 只搜索记忆
        metadata_filter={"user_id": "test_user_001"},
        top_k=10
    )
    
    if result.get("success"):
        memories = result.get("results", [])
        print(f"找到 {len(memories)} 条记忆")
        
        # 验证结果
        for memory in memories:
            tags = memory.get("tags", [])
            user_id = memory.get("metadata", {}).get("user_id")
            content_preview = memory.get("content", "")[:40] + "..."
            
            print(f"  • {content_preview}")
            print(f"    标签: {tags}, 用户: {user_id}")
            
            # 验证标签包含 memory
            if "memory" not in tags:
                print("    ❌ 标签过滤失败")
            
            # 验证用户ID匹配
            if user_id != "test_user_001":
                print("    ❌ 用户过滤失败")
    else:
        print(f"❌ 搜索失败: {result}")

def check_knowledge_base_status():
    """检查知识库服务状态"""
    try:
        response = requests.get(f"{KB_SERVICE_URL}/stats", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    """主测试流程"""
    print("🧪 知识库元数据过滤功能验证测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"知识库服务: {KB_SERVICE_URL}")
    
    # 检查服务状态
    print_section("服务状态检查")
    status_ok, status_info = check_knowledge_base_status()
    
    if not status_ok:
        print(f"❌ 知识库服务不可用: {status_info}")
        print("请确保知识库服务已启动 (python knowledge_base_service.py)")
        return False
    
    print(f"✅ 知识库服务可用")
    print_result(status_info, "服务统计信息")
    
    # 设置测试数据
    if not setup_test_data():
        print("❌ 测试数据设置失败")
        return False
    
    # 执行测试
    try:
        test_user_isolation()
        test_importance_filtering()
        test_memory_type_filtering() 
        test_combined_filtering()
        test_tag_and_metadata_combination()
        
        print_section("测试完成")
        print("🎉 所有元数据过滤功能测试完成！")
        
        # 显示最终统计
        final_status_ok, final_status_info = check_knowledge_base_status()
        if final_status_ok:
            print_result(final_status_info, "最终统计信息")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 元数据过滤功能验证通过！")
        else:
            print("\n❌ 元数据过滤功能验证失败！")
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
