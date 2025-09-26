import requests
import json

# 知识库服务的地址
url = "http://127.0.0.1:8100/search"

# 定义搜索查询和过滤器
query = "卡菈克 暴力破坏摄像头 反应"
metadata_filter = {
    "doc_type": {
        "in": ["world_knowledge", "persona_description", "source_material"]
    }
}

# 构建请求体
payload = {
    "query": query,
    "top_k": 5,
    "metadata_filter": metadata_filter  # 修正字段名
}

print(f"正在搜索: '{query}'")
print(f"使用过滤器: {json.dumps(metadata_filter, ensure_ascii=False)}")
print("-" * 20)

try:
    # 发送POST请求
    response = requests.post(url, json=payload)
    response.raise_for_status()  # 如果请求失败则抛出异常

    # 解析并打印结果
    response_data = response.json()

    # 修正: 从响应字典中获取 'results' 列表
    if response_data and response_data.get("success"):
        results = response_data.get("results", [])
        if not results:
            print("没有找到相关结果。")
        else:
            print(f"找到 {len(results)} 个结果:")
            for i, result in enumerate(results):
                doc = result.get('document', {})
                metadata = doc.get('metadata', {})
                score = result.get('score', 0.0)
                print(f"\n--- 结果 {i+1} (相似度: {score:.4f}) ---")
                print(f"  内容: {doc.get('content', 'N/A')[:200]}...")
                print(f"  类型: {metadata.get('doc_type', 'N/A')}")
                print(f"  来源: {metadata.get('source', 'N/A')}")
    else:
        print(f"搜索失败: {response_data.get('message', '未知错误')}")

except requests.exceptions.RequestException as e:
    print(f"\n[错误] 无法连接到知识库服务: {e}")
    print("请确保 'knowledge_base_service.py' 正在运行。")
    print("您可以尝试使用以下命令启动它：")
    print("conda activate base; python knowledge_base_service.py")

except Exception as e:
    print(f"发生未知错误: {e}")
