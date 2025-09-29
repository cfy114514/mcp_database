import requests

KB_URL = "http://localhost:8001"

docs = [
    {"doc_id": "karlach_template_curt_mem_1", "content": "滚远点。我胸口正热得想杀人。", "tags": ["karlach","templates","bucket:Curt","memory"]},
    {"doc_id": "karlach_template_guarded_mem_1", "content": "问可以，别越界。", "tags": ["karlach","templates","bucket:Guarded","memory"]},
    {"doc_id": "karlach_template_gruff_mem_1", "content": "找我？那就别怕烫。", "tags": ["karlach","templates","bucket:Gruff","memory"]},
    {"doc_id": "karlach_template_warm_mem_1", "content": "有你在，稳些。", "tags": ["karlach","templates","bucket:Warm","memory"]},
    {"doc_id": "karlach_template_resolute_mem_1", "content": "先活着，再算账。顺序别乱。", "tags": ["karlach","templates","bucket:Resolute","memory"]},
    {"doc_id": "karlach_template_narrator_move_mem_1", "content": "(暮色中，远处一座桥在烟雾中隐约可见)\n卡菈克：桥不稳，火还在胸口。你要跟我一起冲，还是找替代路线？\n选项：1) 冲；2) 找路；3) 侦查桥下", "tags": ["karlach","templates","situation:narrator_move","memory"]},
]

for d in docs:
    payload = {
        "doc_id": d["doc_id"],
        "content": d["content"],
        "tags": d["tags"],
        "metadata": {"persona":"karlach","type":"template","user_id":"dev-local"}
    }
    r = requests.post(f"{KB_URL}/add", json=payload)
    print(d["doc_id"], r.status_code, r.text)

# 重建索引
r = requests.post(f"{KB_URL}/rebuild_index")
print("rebuild_index:", r.status_code, r.text)

# 检索：按 tags_all 测试
query_payload = {
    "query": "卡菈克 模板",
    "top_k": 5,
    "tags_all": ["karlach","templates"]
}
r = requests.post(f"{KB_URL}/search", json=query_payload)
print("search:", r.status_code)
print(r.text)
