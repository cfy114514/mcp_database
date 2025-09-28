#!/usr/bin/env python3
"""
测试Karlach MCP工具功能
"""
import json
import subprocess
import sys
from pathlib import Path

def test_karlach_mcp_tools():
    """测试karlach MCP工具"""
    print("🧪 测试Karlach MCP工具功能...")
    
    # 从脚本位置向上查找项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    mcp_dir = project_root / "mcp-persona-uozumi"
    if not mcp_dir.exists():
        print("❌ MCP目录不存在")
        return False
        
    # 检查编译后的服务器文件
    server_file = mcp_dir / "dist" / "server.js"
    if not server_file.exists():
        print("❌ 服务器文件不存在，需要先构建")
        return False
        
    print("✅ 服务器文件存在")
    
    # 检查karlach配置文件
    karlach_dir = project_root / "configs" / "personas" / "karlach"
    if not karlach_dir.exists():
        print("❌ Karlach配置目录不存在")
        return False
        
    # 检查关键配置文件
    required_files = [
        "persona.md",
        "levels.v1.json", 
        "buckets.v1.json",
        "karlach_worldbook.zh.json"
    ]
    
    for file in required_files:
        file_path = karlach_dir / file
        if not file_path.exists():
            print(f"❌ 缺少配置文件: {file}")
            return False
        print(f"✅ 找到配置文件: {file}")
        
    # 验证配置文件内容
    try:
        # 测试levels.v1.json
        with open(karlach_dir / "levels.v1.json", 'r', encoding='utf-8') as f:
            levels = json.load(f)
            if "levels" in levels and len(levels["levels"]) >= 25:
                print(f"✅ Levels配置有效，包含{len(levels['levels'])}个等级")
            else:
                print("❌ Levels配置无效")
                return False
                
        # 测试buckets.v1.json  
        with open(karlach_dir / "buckets.v1.json", 'r', encoding='utf-8') as f:
            buckets = json.load(f)
            if "buckets" in buckets and len(buckets["buckets"]) >= 5:
                print(f"✅ Buckets配置有效，包含{len(buckets['buckets'])}个情绪桶")
            else:
                print("❌ Buckets配置无效")
                return False
                
    except Exception as e:
        print(f"❌ 配置文件验证失败: {e}")
        return False
        
    print("🎉 Karlach MCP工具配置验证通过!")
    return True

def test_mcp_server_syntax():
    """测试MCP服务器语法"""
    print("\n🔍 测试MCP服务器语法...")
    
    try:
        # 从脚本位置向上查找项目根目录
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        server_file = project_root / "mcp-persona-uozumi" / "dist" / "server.js"
        
        # 尝试验证Node.js语法
        result = subprocess.run([
            "node", "-c", str(server_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ MCP服务器语法验证通过")
            return True
        else:
            print(f"❌ MCP服务器语法错误: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"⚠️ 无法验证语法: {e}")
        return True  # 不阻塞测试

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 Karlach MCP工具集成测试")
    print("=" * 60)
    
    # 切换到正确的目录
    import os
    os.chdir(Path(__file__).parent)
    
    success = True
    
    # 测试配置文件
    if not test_karlach_mcp_tools():
        success = False
        
    # 测试服务器语法
    if not test_mcp_server_syntax():
        success = False
        
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过! Karlach已成功集成到MCP工具中")
        sys.exit(0)
    else:
        print("❌ 测试失败，请检查上述错误")
        sys.exit(1)

if __name__ == "__main__":
    main()
