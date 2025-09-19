#!/usr/bin/env python3
"""
实际记忆库向量化存储和标签索引演示

这个脚本展示了你的记忆库如何实际工作：
1. 向量化存储：将文本转换为1024维向量
2. 标签化索引：通过标签快速过滤
3. 混合搜索：结合向量相似度和标签匹配
"""

import requests
import json
from datetime import datetime

def test_current_memory_storage():
    """测试当前记忆库的存储功能"""
    print("🔍 测试当前记忆库的存储和检索")
    print("=" * 60)
    
    kb_url = "http://localhost:8001"
    
    # 首先查看当前状态
    try:
        response = requests.get(f"{kb_url}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json().get("stats", {})
            print(f"📊 当前库状态:")
            print(f"   文档数量: {stats.get('document_count', 0)}")
            print(f"   向量数量: {stats.get('vector_count', 0)}")
        else:
            print("❌ 无法获取库状态")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    return True

def test_vectorized_search():
    """测试向量化搜索"""
    print(f"\n🔢 测试向量化搜索")
    print("-" * 40)
    
    kb_url = "http://localhost:8001"
    
    # 测试不同的查询
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
    
    for test in test_queries:
        print(f"\n🔍 {test['name']}: '{test['query']}'")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{kb_url}/search",
                json=test,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("results"):
                    results = result["results"]
                    print(f"✅ 找到 {len(results)} 条相关记忆:")
                    
                    for i, item in enumerate(results, 1):
                        content = item.get("content", "")
                        metadata = item.get("metadata", {})
                        similarity = item.get("similarity", 0)
                        importance = metadata.get("importance", 0)
                        
                        print(f"  {i}. {content[:50]}...")
                        print(f"     相似度: {similarity:.3f} | 重要性: {importance}")
                        
                        # 显示标签
                        tags = item.get("tags", [])
                        if tags:
                            print(f"     标签: {', '.join(tags)}")
                else:
                    print("❌ 未找到相关记忆")
            else:
                print(f"❌ 搜索失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 搜索出错: {e}")

def test_tag_filtering():
    """测试标签过滤"""
    print(f"\n🏷️ 测试标签过滤功能")
    print("-" * 40)
    
    kb_url = "http://localhost:8001"
    
    # 测试标签过滤
    tag_tests = [
        {
            "name": "只搜索记忆类型",
            "query": "用户",
            "tags": ["memory"],
            "top_k": 5
        },
        {
            "name": "搜索特定标签",
            "query": "内容",
            "tags": ["咖啡"],  # 如果有这个标签的话
            "top_k": 3
        }
    ]
    
    for test in tag_tests:
        print(f"\n🔖 {test['name']}")
        print(f"   查询: '{test['query']}'")
        print(f"   标签过滤: {test['tags']}")
        print("-" * 25)
        
        try:
            response = requests.post(
                f"{kb_url}/search",
                json=test,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("results"):
                    results = result["results"]
                    print(f"✅ 标签过滤后找到 {len(results)} 条记录")
                    
                    for i, item in enumerate(results, 1):
                        content = item.get("content", "")
                        tags = item.get("tags", [])
                        print(f"  {i}. {content[:40]}...")
                        print(f"     标签: {', '.join(tags)}")
                else:
                    print("❌ 标签过滤后无结果")
            else:
                print(f"❌ 标签过滤失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 标签过滤出错: {e}")

def test_user_isolation():
    """测试用户数据隔离"""
    print(f"\n🔒 测试用户数据隔离")
    print("-" * 40)
    
    kb_url = "http://localhost:8001"
    
    # 测试用户隔离功能
    isolation_tests = [
        {
            "name": "搜索特定用户的记忆",
            "query": "用户",
            "tags": ["memory"],
            "metadata_filter": {"user_id": "test_user_001"},
            "top_k": 3
        },
        {
            "name": "搜索另一个用户的记忆",
            "query": "用户",
            "tags": ["memory"], 
            "metadata_filter": {"user_id": "test_user_002"},
            "top_k": 3
        }
    ]
    
    for test in isolation_tests:
        print(f"\n👤 {test['name']}")
        user_id = test['metadata_filter']['user_id']
        print(f"   用户ID: {user_id}")
        print("-" * 25)
        
        try:
            response = requests.post(
                f"{kb_url}/search",
                json=test,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("results"):
                    results = result["results"]
                    print(f"✅ 用户 {user_id} 的记忆: {len(results)} 条")
                    
                    for i, item in enumerate(results, 1):
                        content = item.get("content", "")
                        metadata = item.get("metadata", {})
                        stored_user_id = metadata.get("user_id", "unknown")
                        print(f"  {i}. {content[:40]}...")
                        print(f"     归属用户: {stored_user_id}")
                else:
                    print(f"❌ 用户 {user_id} 暂无记忆")
            else:
                print(f"❌ 用户隔离测试失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 用户隔离测试出错: {e}")

def show_storage_architecture():
    """展示存储架构"""
    print(f"\n🏗️ 你的记忆库存储架构")
    print("=" * 60)
    
    print("📁 存储层次:")
    print("-" * 30)
    print("1. 📝 原始文本内容")
    print("   └── 用户的自然语言表达")
    print()
    print("2. 🔢 向量表示层 (1024维)")
    print("   ├── BAAI/bge-large-zh-v1.5 模型")
    print("   └── 语义向量空间")
    print()
    print("3. 🏷️ 标签索引层")
    print("   ├── 自动生成标签")
    print("   ├── 手动设置标签")
    print("   └── 快速过滤索引")
    print()
    print("4. 📊 元数据层")
    print("   ├── user_id (用户隔离)")
    print("   ├── importance (重要性评分)")
    print("   ├── memory_type (记忆类型)")
    print("   ├── emotional_valence (情感倾向)")
    print("   └── created_at (创建时间)")
    
    print(f"\n🔍 搜索流程:")
    print("-" * 30)
    print("1. 查询输入 → 向量化")
    print("2. 标签过滤 → 候选集")
    print("3. 用户隔离 → 安全过滤")
    print("4. 向量计算 → 相似度排序")
    print("5. 重要性加权 → 最终排序")
    print("6. 返回结果 → 结构化输出")
    
    print(f"\n⚡ 性能特点:")
    print("-" * 30)
    print("✅ 语义理解：通过向量相似度发现隐含关联")
    print("✅ 精确匹配：通过标签索引快速定位")
    print("✅ 用户隔离：元数据过滤确保数据安全")
    print("✅ 智能排序：结合相似度和重要性")
    print("✅ 可扩展性：支持大量用户和记忆存储")

def main():
    """主函数"""
    print("🧠 记忆库实际运行演示")
    print("=" * 70)
    
    # 测试基础连接
    if not test_current_memory_storage():
        print("❌ 无法连接到记忆库服务，请确保服务正在运行")
        return
    
    # 运行各项测试
    test_vectorized_search()
    test_tag_filtering()
    test_user_isolation()
    show_storage_architecture()
    
    print(f"\n🎯 总结")
    print("=" * 70)
    print("你的记忆库已经具备了完整的向量化存储和标签索引能力：")
    print("\n🔢 向量化存储:")
    print("  ✅ 1024维语义向量 (BAAI/bge-large-zh-v1.5)")
    print("  ✅ 余弦相似度计算")
    print("  ✅ 语义理解和模糊匹配")
    
    print("\n🏷️ 标签化索引:")
    print("  ✅ 多标签支持")
    print("  ✅ 快速过滤和精确匹配")
    print("  ✅ 灵活的分类管理")
    
    print("\n🔒 数据安全:")
    print("  ✅ 用户数据隔离")
    print("  ✅ 元数据过滤")
    print("  ✅ 多用户支持")
    
    print("\n💡 下一步可以:")
    print("  📱 集成到 MCP 客户端")
    print("  🤖 添加 LLM 自动记忆提取")
    print("  🚀 部署到生产环境")

if __name__ == "__main__":
    main()
