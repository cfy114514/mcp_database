#!/usr/bin/env python3
"""
MCP 服务器环境测试脚本
用于验证 Python 环境和模块导入是否正常
"""

import sys
import os

def test_python_environment():
    """测试 Python 环境"""
    print("=== Python 环境测试 ===")
    print(f"Python 版本: {sys.version}")
    print(f"Python 可执行文件: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python 路径: {sys.path[:3]}...")  # 只显示前3个路径
    
def test_module_imports():
    """测试关键模块导入"""
    print("\n=== 模块导入测试 ===")
    
    modules_to_test = [
        ('mcp', 'MCP 核心库'),
        ('mcp.server.fastmcp', 'FastMCP 服务器'),
        ('fastapi', 'FastAPI Web框架'),
        ('requests', 'HTTP 请求库'),
        ('numpy', 'NumPy 数值计算'),
        ('logging', '日志模块（内置）'),
        ('json', 'JSON 模块（内置）'),
        ('typing', '类型提示（内置）')
    ]
    
    success_count = 0
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {description}: {module_name}")
            success_count += 1
        except ImportError as e:
            print(f"✗ {description}: {module_name} - {e}")
        except Exception as e:
            print(f"⚠ {description}: {module_name} - 其他错误: {e}")
    
    print(f"\n导入测试结果: {success_count}/{len(modules_to_test)} 成功")
    return success_count == len(modules_to_test)

def test_file_access():
    """测试文件访问权限"""
    print("\n=== 文件访问测试 ===")
    
    files_to_check = [
        'context_aggregator_mcp.py',
        'knowledge_base_mcp.py', 
        'knowledge_base_service.py',
        'memory_processor.py',
        'configs/mcp_config.linux.json'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            readable = os.access(file_path, os.R_OK)
            executable = os.access(file_path, os.X_OK)
            print(f"✓ {file_path} - 可读: {readable}, 可执行: {executable}")
        else:
            print(f"✗ {file_path} - 文件不存在")

def test_mcp_service_creation():
    """测试 MCP 服务创建"""
    print("\n=== MCP 服务创建测试 ===")
    
    try:
        from mcp.server.fastmcp import FastMCP
        test_mcp = FastMCP("TestServer")
        print("✓ FastMCP 服务器创建成功")
        
        # 测试工具装饰器
        @test_mcp.tool()
        def test_tool() -> str:
            """测试工具"""
            return "测试成功"
        
        print("✓ MCP 工具装饰器工作正常")
        return True
        
    except Exception as e:
        print(f"✗ MCP 服务创建失败: {e}")
        return False

def main():
    """主函数"""
    print("Linux 服务器 MCP 环境诊断")
    print("=" * 50)
    
    # 基础环境测试
    test_python_environment()
    
    # 模块导入测试
    modules_ok = test_module_imports()
    
    # 文件访问测试
    test_file_access()
    
    # MCP 服务测试
    mcp_ok = test_mcp_service_creation()
    
    print("\n" + "=" * 50)
    print("诊断总结:")
    
    if modules_ok and mcp_ok:
        print("✓ 环境检查通过，可以启动 MCP 服务")
        print("\n建议的启动命令:")
        print("python3 context_aggregator_mcp.py")
        return 0
    else:
        print("✗ 环境检查发现问题，请先解决依赖问题")
        print("\n建议的修复命令:")
        print("pip3 install -r requirements.txt")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
