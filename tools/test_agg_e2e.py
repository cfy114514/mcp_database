# -*- coding: utf-8 -*-
import json
import os
import sys
# 允许从仓库根目录导入顶层模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from embedding_context_aggregator_mcp import get_user_memories, store_conversation_memory, build_prompt_with_context

user = 'dev-local'
conv = (
    "用户: 我最喜欢的题材是硬科幻，尤其是关于太空探索的故事。\n"
    "AI: 明白，你更偏好科学真实性强的作品。\n"
    "用户: 比如三体、基地、和《太空无垠》，我都看过不止一遍。\n"
    "AI: 这些都是典型的硬科幻代表作。\n"
    "用户: 我害怕恐怖片，但对星舰、轨道力学、推进器细节很着迷。\n"
    "AI: 好的，我会在推荐时避免恐怖元素，更多聚焦航天与工程细节。\n"
    "用户: 周末我常常在家用投影看电影，晚上十点左右开始。\n"
    "AI: 收到，我会在晚间推荐合适的片单和观影计划。\n"
)

print('=== STORE ===')
store_res = store_conversation_memory(user, conv, min_importance=0.0)
print(json.dumps(store_res, ensure_ascii=False, indent=2))

print('\n=== GET ===')
get_res = get_user_memories(user, '硬科幻 太空 星舰 轨道力学 推进器', 6)
print(json.dumps(get_res, ensure_ascii=False, indent=2))

print('\n=== PROMPT ===')
prompt = build_prompt_with_context('uozumi', user, '太空推进器', 3, 'cfy114514', include_persona_prompt=False)
print(prompt)
