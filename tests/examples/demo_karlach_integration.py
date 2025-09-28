#!/usr/bin/env python3

"""
Karlach MCP工具使用演示
"""
import json
from pathlib import Path

# 计算仓库根目录（tests/examples/ -> tests -> repo root）
REPO_ROOT = Path(__file__).resolve().parents[2]


def demonstrate_karlach_tools():
    """演示karlach MCP工具"""
    print("🔥 Karlach MCP工具演示")
    print("=" * 50)
    
    # 显示可用的karlach工具
    print("\n📋 可用的Karlach MCP工具:")
    tools = [
        "karlach-persona - 获取角色基本信息",
        "karlach-system-prompt - 获取系统提示词", 
        "karlach-safety - 获取安全指导原则",
        "karlach-worldbook - 获取世界观设定",
        "karlach-worldbook-entry - 获取特定世界观条目",
        "karlach-levels - 获取等级系统",
        "karlach-buckets - 获取情绪桶系统", 
        "karlach-templates - 获取对话模板",
        "karlach-template - 获取特定模板"
    ]
    
    for i, tool in enumerate(tools, 1):
        print(f"{i:2d}. {tool}")
        
    print(f"\n✨ 总共{len(tools)}个karlach专用工具已集成到MCP服务器中")
    
    # 显示配置文件信息
    print("\n📁 Karlach配置文件:")
    karlach_dir = REPO_ROOT / "configs" / "personas" / "karlach"
    if karlach_dir.exists():
        files = list(karlach_dir.glob("*"))
        for file in files:
            size = file.stat().st_size if file.is_file() else 0
            print(f"   📄 {file.name} ({size} bytes)")
    else:
        print(f"   ⚠️ 目录不存在: {karlach_dir}")
            
    # 显示一些示例数据
    print("\n🎮 示例配置数据:")
    
    # 显示等级信息
    try:
        with open(karlach_dir / "levels.v1.json", 'r', encoding='utf-8') as f:
            levels = json.load(f)
            print(f"   🔥 等级系统: {len(levels['levels'])}个等级")
            if levels['levels']:
                first_level = levels['levels'][0]
                print(f"      - 第1级: {first_level.get('name', 'N/A')} (经验: {first_level.get('experience_required', 0)})")
                if len(levels['levels']) > 1:
                    last_level = levels['levels'][-1]
                    print(f"      - 最高级: {last_level.get('name', 'N/A')} (经验: {last_level.get('experience_required', 0)})")
    except Exception as e:
        print(f"   ❌ 无法读取等级数据: {e}")
        
    # 显示情绪桶信息
    try:
        with open(karlach_dir / "buckets.v1.json", 'r', encoding='utf-8') as f:
            buckets = json.load(f)
            print(f"   😊 情绪系统: {len(buckets['buckets'])}个情绪状态")
            for bucket in buckets['buckets'][:3]:  # 显示前3个
                print(f"      - {bucket.get('name', 'N/A')}: {bucket.get('description', 'N/A')}")
            if len(buckets['buckets']) > 3:
                print(f"      - ... 还有{len(buckets['buckets']) - 3}个情绪状态")
    except Exception as e:
        print(f"   ❌ 无法读取情绪数据: {e}")


def show_mcp_config():
    """显示MCP配置信息"""
    print("\n⚙️ MCP配置文件:")
    
    config_file = REPO_ROOT / "mcp-persona-uozumi" / "xiaozhi.mcp.config.example.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            print(f"   📄 配置文件: {config_file.name}")
            
            # 显示MCP服务器配置
            if "mcpServers" in config:
                servers = config["mcpServers"]
                print(f"   🖥️ 配置的MCP服务器: {len(servers)}个")
                
                for server_name, server_config in servers.items():
                    command = server_config.get("command", "")
                    print(f"      - {server_name}: {command}")
                    
            # 显示自动注入配置
            if "autoInjection" in config:
                auto_inject = config["autoInjection"]
                print(f"   💉 自动注入配置:")
                for item in auto_inject:
                    print(f"      - {item.get('type', 'N/A')}: {item.get('content', 'N/A')[:50]}...")
                    
        except Exception as e:
            print(f"   ❌ 无法读取配置文件: {e}")
    else:
        print(f"   ⚠️ 配置文件不存在: {config_file}")


def show_usage_instructions():
    """显示使用说明"""
    print("\n📖 使用说明:")
    print("=" * 50)
    
    print("\n1️⃣ 启动MCP服务器:")
    print("   cd mcp-persona-uozumi")
    print("   npm start")
    print("   # 或使用开发模式: npm run dev")
    
    print("\n2️⃣ 在VS Code中配置MCP:")
    print("   - 复制 xiaozhi.mcp.config.example.json 到你的VS Code设置")
    print("   - 或使用GitHub Copilot的MCP支持")
    
    print("\n3️⃣ 使用Karlach工具:")
    print("   - 在AI对话中直接调用karlach工具")
    print("   - 例如: '获取karlach的等级系统'")
    print("   - 或: '显示karlach当前情绪状态'")
    
    print("\n4️⃣ 可用命令示例:")
    print("   - karlach-persona: 获取角色基本信息")
    print("   - karlach-levels: 查看完整等级系统")
    print("   - karlach-buckets: 查看情绪状态系统")
    print("   - karlach-worldbook: 获取世界观设定")


def main():
    """主演示函数"""
    print("🎉 Karlach MCP工具集成完成!")
    print("=" * 60)
    
    # 不再切换到示例目录，直接使用仓库根目录定位文件
    # ...existing code...
    
    # 运行演示
    demonstrate_karlach_tools()
    show_mcp_config()
    show_usage_instructions()
    
    print("\n" + "=" * 60)
    print("🔥 Karlach已成功集成到MCP工具链中!")
    print("现在你可以通过MCP协议访问所有Karlach角色功能。")
    print("=" * 60)


if __name__ == "__main__":
    main()
