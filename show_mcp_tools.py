#!/usr/bin/env python3
"""
记忆库 MCP 工具快速查询脚本

运行此脚本可快速查看所有可用的 MCP 工具及其用法
"""

def show_mcp_tools():
    """显示所有 MCP 工具"""
    
    print("🧠 记忆库 MCP 工具列表")
    print("=" * 60)
    
    tools = [
        {
            "name": "build_prompt_with_context",
            "service": "context_aggregator_mcp.py",
            "function": "🎯 构建增强的系统提示",
            "key_params": "persona_name, user_id, user_query",
            "returns": "包含记忆上下文的完整提示",
            "example": 'build_prompt_with_context("luoluo", "user001", "推荐咖啡店")'
        },
        {
            "name": "store_conversation_memory", 
            "service": "context_aggregator_mcp.py",
            "function": "💾 提取并存储对话记忆",
            "key_params": "user_id, conversation_history, force_save",
            "returns": "记忆存储结果和重要性评分",
            "example": 'store_conversation_memory("user001", "对话历史...", False)'
        },
        {
            "name": "get_user_memories",
            "service": "context_aggregator_mcp.py", 
            "function": "🔍 检索用户历史记忆",
            "key_params": "user_id, query, top_k, memory_type",
            "returns": "用户记忆列表和统计信息",
            "example": 'get_user_memories("user001", "咖啡", 5, "preference")'
        },
        {
            "name": "get_service_status",
            "service": "context_aggregator_mcp.py",
            "function": "⚡ 获取服务运行状态",
            "key_params": "无参数",
            "returns": "服务状态和组件信息",
            "example": 'get_service_status()'
        }
    ]
    
    print("📋 MCP 工具概览:")
    print("-" * 60)
    
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   服务: {tool['service']}")
        print(f"   功能: {tool['function']}")
        print(f"   参数: {tool['key_params']}")
        print(f"   返回: {tool['returns']}")
        print(f"   示例: {tool['example']}")
        print()

def show_usage_scenarios():
    """显示使用场景"""
    print("🎯 常用场景示例")
    print("=" * 60)
    
    scenarios = [
        {
            "scenario": "💬 AI 对话增强",
            "description": "在每次对话前为 AI 加载用户记忆",
            "steps": [
                "1. 调用 build_prompt_with_context 获取增强提示",
                "2. 将增强提示作为 AI 的系统提示",
                "3. 进行自然对话，AI 会记住用户偏好"
            ],
            "code": '''
# 构建包含记忆的系统提示
enhanced_prompt = build_prompt_with_context(
    persona_name="luoluo",
    user_id="user001", 
    user_query="今天想喝什么咖啡？"
)
# 使用 enhanced_prompt 作为 AI 系统提示
'''
        },
        {
            "scenario": "🔄 记忆自动存储",
            "description": "对话结束后自动提取重要信息",
            "steps": [
                "1. 收集完整的对话历史",
                "2. 调用 store_conversation_memory 提取记忆",
                "3. 系统自动评估重要性并存储"
            ],
            "code": '''
# 自动存储对话记忆
conversation = """
用户: 我最近爱上了手冲咖啡
络络: 听起来很有趣！你喜欢什么豆子？
用户: 埃塞俄比亚的耶加雪菲，酸度适中
"""
result = store_conversation_memory(
    user_id="user001",
    conversation_history=conversation
)
'''
        },
        {
            "scenario": "📊 记忆分析",
            "description": "查看和分析用户的历史记忆",
            "steps": [
                "1. 使用 get_user_memories 检索记忆",
                "2. 根据记忆类型和重要性分析",
                "3. 了解用户的偏好和特征"
            ],
            "code": '''
# 获取用户咖啡相关记忆
memories = get_user_memories(
    user_id="user001",
    query="咖啡 豆子 口味",
    top_k=10,
    memory_type="preference"
)
'''
        },
        {
            "scenario": "🔧 系统监控",
            "description": "监控记忆系统的运行状态",
            "steps": [
                "1. 定期调用 get_service_status",
                "2. 检查各组件连接状态",
                "3. 确保记忆功能正常工作"
            ],
            "code": '''
# 检查系统状态
status = get_service_status()
if status['status'] == 'running':
    print("✅ 记忆系统运行正常")
else:
    print("❌ 记忆系统异常")
'''
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['scenario']}")
        print(f"   描述: {scenario['description']}")
        print("   流程:")
        for step in scenario['steps']:
            print(f"      {step}")
        print("   代码示例:")
        print(scenario['code'])
        print()

def show_api_reference():
    """显示 API 参考"""
    print("📚 API 快速参考")
    print("=" * 60)
    
    print("🔗 REST API 端点 (知识库服务):")
    print("-" * 40)
    print("POST http://localhost:8001/add     - 添加记忆")
    print("POST http://localhost:8001/search  - 搜索记忆") 
    print("GET  http://localhost:8001/stats   - 获取统计")
    
    print(f"\n🛠️ MCP 工具 (上下文聚合服务):")
    print("-" * 40)
    print("build_prompt_with_context      - 构建增强提示")
    print("store_conversation_memory      - 存储对话记忆")
    print("get_user_memories             - 获取用户记忆")
    print("get_service_status            - 获取服务状态")
    
    print(f"\n⚙️ 配置文件:")
    print("-" * 40)
    print(".env                          - 环境变量配置")
    print("mcp_config.json               - MCP 服务配置")
    print("memory-lab.md                 - 系统设计文档")
    print("MCP_TOOLS_LIST.md             - 工具详细文档")

def main():
    """主函数"""
    show_mcp_tools()
    print()
    show_usage_scenarios()
    print()
    show_api_reference()
    
    print(f"\n🎉 记忆库已就绪！")
    print("=" * 60)
    print("你现在可以：")
    print("1. 🚀 启动 MCP 服务: python context_aggregator_mcp.py")
    print("2. 🔧 运行集成测试: python test_integration.py")
    print("3. 🎬 查看演示效果: python demo_memory_system.py")
    print("4. 📖 阅读详细文档: MCP_TOOLS_LIST.md")

if __name__ == "__main__":
    main()
