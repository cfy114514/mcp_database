import requests

KB_URL = "http://localhost:8001"

docs = [
    {"doc_id": "karlach_template_warm_mem_A", "content": "有你在，稳些。", "tags": ["karlach","templates","bucket:Warm","memory"], "metadata": {"persona":"karlach","type":"template","user_id":"dev-local"}},
    {"doc_id": "karlach_template_resolute_mem_A", "content": "先活着，再算账。顺序别乱。", "tags": ["karlach","templates","bucket:Resolute","memory"], "metadata": {"persona":"karlach","type":"template","user_id":"dev-local"}},
    {"doc_id": "karlach_template_narrator_move_mem_A", "content": "(暮色中，远处一座桥在烟雾中隐约可见)\n卡菈克：桥不稳，火还在胸口。你要跟我一起冲，还是找替代路线？\n选项：1) 冲；2) 找路；3) 侦查桥下", "tags": ["karlach","templates","situation:narrator_move","memory"], "metadata": {"persona":"karlach","type":"template","user_id":"dev-local"}},
]

for d in docs:
    r = requests.post(f"{KB_URL}/add", json=d)
    print("ADD", d["doc_id"], r.status_code, r.text)

# 重建索引
r = requests.post(f"{KB_URL}/rebuild_index")
print("REBUILD", r.status_code, r.text)

# 直查：按标签
query_payload = {
    "query": "卡菈克 模板",
    "top_k": 5,
    "tags_all": ["karlach","templates"]
}
r = requests.post(f"{KB_URL}/search", json=query_payload)
print("SEARCH_TAGS", r.status_code)
print(r.text)

# 带 user_id 的记忆检索（embedding-context-aggregator 会这样查）
query_payload_user = {
    "query": "卡菈克 模板",
    "top_k": 5,
    "tags_all": ["memory"],
    "metadata_filter": {"user_id": "dev-local"}
}
r = requests.post(f"{KB_URL}/search", json=query_payload_user)
print("SEARCH_USER", r.status_code)
print(r.text)
