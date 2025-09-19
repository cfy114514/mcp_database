#!/usr/bin/env python3
"""
记忆库的向量化存储和标签化索引架构演示

这个脚本展示了记忆系统如何通过向量化和标签化实现智能存储和检索
"""

import numpy as np
import json
import requests
from typing import List, Dict, Any

def demonstrate_vectorized_storage():
    """演示向量化存储机制"""
    print("🔢 向量化存储机制演示")
    print("=" * 60)
    
    # 模拟记忆文本和其向量表示
    memories = [
        {
            "text": "用户李明喜欢喝咖啡，每天早上都要来一杯",
            "vector": [0.1, 0.8, 0.3, 0.9, 0.2],  # 简化的5维向量
            "similarity_concepts": ["咖啡", "习惯", "早上", "饮品"]
        },
        {
            "text": "用户住在朝阳区三里屯附近",
            "vector": [0.7, 0.2, 0.9, 0.1, 0.6],
            "similarity_concepts": ["地址", "居住", "朝阳区", "位置"]
        },
        {
            "text": "用户最喜欢的咖啡店关门了，感到难过",
            "vector": [0.2, 0.9, 0.1, 0.8, 0.4],
            "similarity_concepts": ["咖啡", "情感", "难过", "关门"]
        }
    ]
    
    print("📝 存储的记忆及其向量表示:")
    print("-" * 40)
    for i, memory in enumerate(memories, 1):
        print(f"{i}. {memory['text']}")
        print(f"   向量: {memory['vector']}")
        print(f"   相关概念: {', '.join(memory['similarity_concepts'])}")
        print()
    
    # 模拟查询
    query_text = "推荐咖啡店"
    query_vector = [0.15, 0.85, 0.25, 0.9, 0.3]  # 查询的向量表示
    
    print(f"🔍 查询: '{query_text}'")
    print(f"   查询向量: {query_vector}")
    print("\n📊 相似度计算结果:")
    print("-" * 40)
    
    # 计算余弦相似度
    def cosine_similarity(v1, v2):
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        return dot_product / (norm_v1 * norm_v2)
    
    similarities = []
    for memory in memories:
        similarity = cosine_similarity(query_vector, memory['vector'])
        similarities.append((memory['text'], similarity))
        print(f"相似度 {similarity:.3f}: {memory['text']}")
    
    # 排序并显示最相关的记忆
    similarities.sort(key=lambda x: x[1], reverse=True)
    print(f"\n🎯 最相关的记忆: {similarities[0][0]}")

def demonstrate_tag_indexing():
    """演示标签化索引机制"""
    print(f"\n🏷️ 标签化索引机制演示")
    print("=" * 60)
    
    # 模拟标签索引结构
    tag_index = {
        "咖啡": ["memory_001", "memory_003"],
        "习惯": ["memory_001", "memory_004"],
        "地址": ["memory_002"],
        "朝阳区": ["memory_002"],
        "情感": ["memory_003", "memory_005"],
        "早上": ["memory_001"],
        "难过": ["memory_003"]
    }
    
    # 记忆内容映射
    memory_content = {
        "memory_001": "用户李明喜欢喝咖啡，每天早上都要来一杯",
        "memory_002": "用户住在朝阳区三里屯附近", 
        "memory_003": "用户最喜欢的咖啡店关门了，感到难过",
        "memory_004": "用户习惯每天下午3点开会",
        "memory_005": "用户今天心情很好，升职了"
    }
    
    print("🗂️ 标签索引结构:")
    print("-" * 40)
    for tag, memory_ids in tag_index.items():
        print(f"标签 '{tag}': {memory_ids}")
    
    # 演示标签查询
    def search_by_tags(tags: List[str]) -> List[str]:
        """根据标签搜索记忆"""
        result_sets = []
        for tag in tags:
            if tag in tag_index:
                result_sets.append(set(tag_index[tag]))
        
        if not result_sets:
            return []
        
        # 取交集（AND 查询）
        intersection = result_sets[0]
        for result_set in result_sets[1:]:
            intersection = intersection.intersection(result_set)
        
        return list(intersection)
    
    print("\n🔍 标签查询示例:")
    print("-" * 40)
    
    # 示例查询
    queries = [
        ["咖啡"],
        ["咖啡", "习惯"],
        ["情感"],
        ["咖啡", "情感"]
    ]
    
    for query_tags in queries:
        results = search_by_tags(query_tags)
        print(f"查询标签 {query_tags}:")
        if results:
            for memory_id in results:
                print(f"  ✅ {memory_id}: {memory_content[memory_id]}")
        else:
            print("  ❌ 未找到匹配的记忆")
        print()

def demonstrate_hybrid_search():
    """演示向量+标签混合搜索"""
    print(f"\n🎯 向量+标签混合搜索演示")
    print("=" * 60)
    
    print("💡 混合搜索的优势:")
    print("-" * 40)
    print("✅ 向量搜索：基于语义相似度，发现隐含关联")
    print("✅ 标签搜索：基于精确匹配，确保相关性")
    print("✅ 组合搜索：兼顾语义理解和精确匹配")
    
    print("\n🔄 搜索流程:")
    print("-" * 40)
    print("1. 用户输入查询：'推荐三里屯的咖啡店'")
    print("2. 标签预过滤：找到包含'咖啡'或'三里屯'标签的记忆")
    print("3. 向量计算：在过滤结果中计算语义相似度")
    print("4. 排序返回：按相似度和重要性排序")
    
    # 模拟混合搜索结果
    search_results = [
        {
            "memory_id": "memory_001",
            "content": "用户李明喜欢喝咖啡，每天早上都要来一杯",
            "vector_similarity": 0.85,
            "matched_tags": ["咖啡"],
            "importance": 6.0,
            "final_score": 0.85 * 0.7 + 6.0 * 0.1  # 向量权重0.7 + 重要性权重0.1
        },
        {
            "memory_id": "memory_002", 
            "content": "用户住在朝阳区三里屯附近",
            "vector_similarity": 0.65,
            "matched_tags": ["朝阳区"],
            "importance": 8.0,
            "final_score": 0.65 * 0.7 + 8.0 * 0.1
        },
        {
            "memory_id": "memory_003",
            "content": "用户最喜欢的咖啡店关门了，感到难过", 
            "vector_similarity": 0.78,
            "matched_tags": ["咖啡"],
            "importance": 7.5,
            "final_score": 0.78 * 0.7 + 7.5 * 0.1
        }
    ]
    
    # 按最终得分排序
    search_results.sort(key=lambda x: x['final_score'], reverse=True)
    
    print("\n📊 混合搜索结果 (按相关性排序):")
    print("-" * 40)
    for i, result in enumerate(search_results, 1):
        print(f"{i}. {result['content']}")
        print(f"   向量相似度: {result['vector_similarity']:.2f}")
        print(f"   匹配标签: {result['matched_tags']}")
        print(f"   重要性: {result['importance']}")
        print(f"   最终得分: {result['final_score']:.2f}")
        print()

def show_actual_implementation():
    """展示实际的实现方式"""
    print(f"\n🛠️ 实际系统实现方式")
    print("=" * 60)
    
    print("📁 存储结构:")
    print("-" * 40)
    print("每条记忆包含:")
    memory_structure = {
        "doc_id": "memory_user001_1726745928495",
        "content": "用户李明喜欢喝咖啡，每天早上都要来一杯",
        "vector": "1024维向量 (BAAI/bge-large-zh-v1.5)",
        "tags": ["memory", "咖啡", "习惯", "早上"],
        "metadata": {
            "user_id": "user001",
            "importance": 6.0,
            "memory_type": "preference",
            "emotional_valence": 0.0,
            "created_at": "2025-09-19T13:42:28"
        }
    }
    
    print(json.dumps(memory_structure, ensure_ascii=False, indent=2))
    
    print("\n🔍 搜索API:")
    print("-" * 40)
    print("POST /search")
    search_request = {
        "query": "咖啡店推荐",  # 自动向量化
        "tags": ["咖啡"],      # 标签过滤
        "metadata_filter": {   # 用户隔离
            "user_id": "user001"
        },
        "top_k": 5            # 返回数量
    }
    print(json.dumps(search_request, ensure_ascii=False, indent=2))
    
    print("\n⚡ 性能优化:")
    print("-" * 40)
    print("✅ 向量索引：使用余弦相似度快速计算")
    print("✅ 标签索引：基于哈希表的O(1)查找")
    print("✅ 元数据过滤：用户数据隔离")
    print("✅ 重要性加权：确保重要记忆优先显示")
    print("✅ 缓存机制：避免重复向量化计算")

def main():
    """主函数"""
    print("🧠 记忆库架构：向量化存储 + 标签化索引")
    print("=" * 70)
    
    demonstrate_vectorized_storage()
    demonstrate_tag_indexing() 
    demonstrate_hybrid_search()
    show_actual_implementation()
    
    print(f"\n🎯 总结")
    print("=" * 70)
    print("你的记忆库通过以下方式实现智能存储和检索：")
    print("\n🔢 向量化存储:")
    print("  • 使用 BAAI/bge-large-zh-v1.5 模型生成1024维向量")
    print("  • 通过余弦相似度计算语义相关性")
    print("  • 支持模糊匹配和语义理解")
    
    print("\n🏷️ 标签化索引:")
    print("  • 自动生成和手动设置的标签")
    print("  • 支持精确匹配和快速过滤")
    print("  • 便于分类管理和组织")
    
    print("\n🎯 混合搜索:")
    print("  • 结合向量相似度和标签匹配")
    print("  • 考虑记忆重要性和时间因素")
    print("  • 确保搜索结果的相关性和准确性")
    
    print("\n🔒 用户隔离:")
    print("  • 基于 metadata.user_id 过滤")
    print("  • 确保用户隐私和数据安全")
    print("  • 支持多用户并发使用")

if __name__ == "__main__":
    main()
