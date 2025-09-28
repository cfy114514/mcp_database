#!/usr/bin/env python3
"""
MCP工具调用情况检查

检查各个MCP工具的配置状况和调用情况，确保工具正确配置。
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import importlib.util

class MCPToolChecker:
    """MCP工具检查器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.tools_status = {}
        # 标记归档（非权威）文件
        self.archived = {
            "mcp-calculator/vector_db.py",
            "mcp-calculator/knowledge_base_service.py",
        }
        
    def print_status(self, message: str, status: str = "INFO"):
        """打印状态信息"""
        colors = {
            "SUCCESS": "\033[92m",  # 绿色
            "WARNING": "\033[93m",  # 黄色  
            "ERROR": "\033[91m",    # 红色
            "INFO": "\033[94m",     # 蓝色
            "RESET": "\033[0m"      # 重置
        }
        
        color = colors.get(status, colors["INFO"])
        print(f"{color}{message}{colors['RESET']}")
        
    def check_mcp_configs(self) -> Dict[str, Any]:
        """检查MCP配置文件"""
        self.print_status("\n🔧 检查MCP配置文件...", "INFO")
        
        configs = {}
        config_files = [
            "configs/mcp_config.json",
            "configs/mcp_config.dev.json", 
            "configs/mcp_config.linux.json",
            "mcp-calculator/studio.json"
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        configs[config_file] = config_data
                        
                    # 检查配置内容
                    self.print_status(f"✓ {config_file} - 配置文件存在", "SUCCESS")
                    
                    # 检查MCP服务器配置
                    if "mcpServers" in config_data:
                        for server_name, server_config in config_data["mcpServers"].items():
                            self.print_status(f"  📋 MCP服务器: {server_name}", "INFO")
                            
                    # 检查HTTP服务配置  
                    if "httpServices" in config_data:
                        for service_name, service_config in config_data["httpServices"].items():
                            port = service_config.get("port", "未知")
                            self.print_status(f"  🌐 HTTP服务: {service_name} (端口: {port})", "INFO")
                            
                except Exception as e:
                    self.print_status(f"❌ {config_file} - 读取失败: {e}", "ERROR")
                    configs[config_file] = None
            else:
                self.print_status(f"⚠ {config_file} - 文件不存在", "WARNING")
                
        return configs
        
    def check_mcp_tools(self) -> Dict[str, Dict]:
        """检查MCP工具文件"""
        self.print_status("\n🛠 检查MCP工具文件...", "INFO")
        
        mcp_tools = {
            "context_aggregator_mcp.py": {
                "name": "向量数据库上下文聚合器",
                "port": 8100,
                "type": "向量数据库工具"
            },
            "embedding_context_aggregator_mcp.py": {
                "name": "记忆库上下文聚合器", 
                "port": 8001,
                "type": "记忆库工具"
            },
            "knowledge_base_mcp.py": {
                "name": "知识库MCP工具",
                "port": 8100,
                "type": "向量数据库工具"
            },
            # 归档项不计入权威清单
            "mcp-calculator/vector_db.py": {
                "name": "向量数据库工具（归档）",
                "port": 8100,
                "type": "向量数据库工具（归档）",
                "archived": True,
            }
        }
        
        tools_status = {}
        
        for tool_path, tool_info in mcp_tools.items():
            full_path = self.project_root / tool_path
            is_archived = tool_info.get("archived", False) or (tool_path in self.archived)
            
            if full_path.exists():
                tools_status[tool_path] = {
                    "exists": True,
                    "info": tool_info,
                    "size": full_path.stat().st_size,
                    "archived": is_archived,
                }
                
                # 检查文件内容
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 检查FastMCP导入
                    has_fastmcp = "FastMCP" in content or "from mcp" in content
                    # 检查工具定义
                    has_tools = "@mcp.tool" in content or "def " in content
                    # 检查端口配置
                    expected_port = str(tool_info["port"])
                    has_correct_port = expected_port in content or "KB_PORT" in content
                    
                    tools_status[tool_path].update({
                        "has_fastmcp": has_fastmcp,
                        "has_tools": has_tools,
                        "has_correct_port": has_correct_port
                    })
                    
                    status = "SUCCESS"
                    if not all([has_fastmcp, has_tools, has_correct_port]):
                        status = "WARNING" if is_archived else "WARNING"
                        # 归档文件的缺失不影响整体成功标记
                    
                    label = f"{tool_info['name']}" + (" [ARCHIVED]" if is_archived else "")
                    self.print_status(f"✓ {tool_path} ({label}) - {tool_info['type']}", status)
                    self.print_status(f"  📦 FastMCP: {'是' if has_fastmcp else '否'} | 工具定义: {'是' if has_tools else '否'} | 端口配置: {'是' if has_correct_port else '否'}", "INFO")
                    
                except Exception as e:
                    tools_status[tool_path]["error"] = str(e)
                    self.print_status(f"❌ {tool_path} - 读取文件时出错: {e}", "ERROR")
                    
            else:
                tools_status[tool_path] = {
                    "exists": False,
                    "info": tool_info,
                    "archived": is_archived,
                }
                level = "INFO" if is_archived else "WARNING"
                self.print_status(f"{'ℹ' if is_archived else '⚠'} {tool_path} ({tool_info['name']}) - 文件不存在{('（归档，已跳过）' if is_archived else '')}", level)
                
        return tools_status
        
    def check_service_files(self) -> Dict[str, Dict]:
        """检查HTTP服务文件"""
        self.print_status("\n🌐 检查HTTP服务文件...", "INFO")
        
        service_files = {
            "knowledge_base_service.py": {
                "name": "向量数据库HTTP服务",
                "port": 8100,
                "type": "向量数据库工具"
            },
            # 归档服务展示但不计入失败
            "mcp-calculator/knowledge_base_service.py": {
                "name": "计算器向量数据库服务（归档）",
                "port": 8100, 
                "type": "向量数据库工具（归档）",
                "archived": True,
            }
        }
        
        services_status = {}
        
        for service_path, service_info in service_files.items():
            full_path = self.project_root / service_path
            is_archived = service_info.get("archived", False)
            
            if full_path.exists():
                services_status[service_path] = {
                    "exists": True,
                    "info": service_info,
                    "size": full_path.stat().st_size,
                    "archived": is_archived,
                }
                
                # 检查文件内容
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 检查FastAPI导入
                    has_fastapi = "FastAPI" in content or "from fastapi" in content
                    # 检查路由定义
                    has_routes = "@app." in content or "router" in content
                    # 检查端口配置
                    expected_port = str(service_info["port"])
                    has_correct_port = expected_port in content or "KB_PORT" in content
                    
                    services_status[service_path].update({
                        "has_fastapi": has_fastapi,
                        "has_routes": has_routes,
                        "has_correct_port": has_correct_port
                    })
                    
                    status = "SUCCESS"
                    if not all([has_fastapi, has_routes, has_correct_port]):
                        status = "WARNING" if is_archived else "WARNING"
                    
                    label = f"{service_info['name']}" + (" [ARCHIVED]" if is_archived else "")
                    self.print_status(f"✓ {service_path} ({label}) - {service_info['type']}", status)
                    self.print_status(f"  🚀 FastAPI: {'是' if has_fastapi else '否'} | 路由: {'是' if has_routes else '否'} | 端口配置: {'是' if has_correct_port else '否'}", "INFO")
                    
                except Exception as e:
                    services_status[service_path]["error"] = str(e)
                    self.print_status(f"❌ {service_path} - 读取文件时出错: {e}", "ERROR")
                    
            else:
                services_status[service_path] = {
                    "exists": False,
                    "info": service_info,
                    "archived": is_archived,
                }
                level = "INFO" if is_archived else "WARNING"
                self.print_status(f"{'ℹ' if is_archived else '⚠'} {service_path} ({service_info['name']}) - 文件不存在{('（归档，已跳过）' if is_archived else '')}", level)
                
        return services_status
        
    def check_dependencies(self) -> Dict[str, bool]:
        """检查依赖项"""
        self.print_status("\n📦 检查依赖项...", "INFO")
        
        required_packages = [
            "fastapi",
            "uvicorn", 
            "fastmcp",
            "requests",
            "numpy",
            "openai"
        ]
        
        dependencies_status = {}
        
        for package in required_packages:
            try:
                spec = importlib.util.find_spec(package)
                if spec is not None:
                    dependencies_status[package] = True
                    self.print_status(f"✓ {package} - 已安装", "SUCCESS")
                else:
                    dependencies_status[package] = False
                    self.print_status(f"❌ {package} - 未安装", "ERROR")
            except Exception as e:
                dependencies_status[package] = False
                self.print_status(f"❌ {package} - 检查时出错: {e}", "ERROR")
                
        return dependencies_status
        
    def generate_summary(self, configs: Dict, tools: Dict, services: Dict, dependencies: Dict):
        """生成检查总结"""
        self.print_status("\n📊 检查总结", "INFO")
        
        # 配置文件统计
        config_total = len(configs)
        config_ok = sum(1 for v in configs.values() if v is not None)
        self.print_status(f"📋 配置文件: {config_ok}/{config_total} 正常", "SUCCESS" if config_ok == config_total else "WARNING")
        
        # MCP工具统计  
        tools_total = len([k for k, v in tools.items() if not v.get('archived')])
        tools_ok = sum(1 for v in tools.values() if v.get("exists", False) and not v.get('archived'))
        self.print_status(f"🛠 MCP工具: {tools_ok}/{tools_total} 存在（归档项不计入）", "SUCCESS" if tools_ok == tools_total else "WARNING")
        
        # HTTP服务统计
        services_total = len([k for k, v in services.items() if not v.get('archived')])
        services_ok = sum(1 for v in services.values() if v.get("exists", False) and not v.get('archived'))
        self.print_status(f"🌐 HTTP服务: {services_ok}/{services_total} 存在（归档项不计入）", "SUCCESS" if services_ok == services_total else "WARNING")
        
        # 依赖项统计
        deps_total = len(dependencies)
        deps_ok = sum(1 for v in dependencies.values() if v)
        self.print_status(f"📦 依赖项: {deps_ok}/{deps_total} 已安装", "SUCCESS" if deps_ok == deps_total else "WARNING")
        
        # 端口分配总结
        self.print_status("\n🔧 端口分配状况:", "INFO")
        self.print_status("  📍 端口 8100: 向量数据库工具", "INFO")
        self.print_status("    - knowledge_base_service.py", "INFO")
        self.print_status("    - context_aggregator_mcp.py", "INFO")
        self.print_status("    - memory_processor.py", "INFO")
        self.print_status("    - knowledge_base_mcp.py", "INFO")
        
        self.print_status("  📍 端口 8001: 记忆库工具", "INFO")
        self.print_status("    - embedding_memory_processor.py", "INFO")
        self.print_status("    - embedding_context_aggregator_mcp.py", "INFO")
        self.print_status("    - test_embedding_memory.py", "INFO")
        self.print_status("    - mcp_memory_manager.py", "INFO")
        
        # 归档提示
        archived_list = [k for k, v in {**tools, **services}.items() if v.get('archived')]
        if archived_list:
            self.print_status("\n📦 归档（非权威，已从成功率统计中排除）:", "INFO")
            for item in sorted(archived_list):
                self.print_status(f"  - {item}", "INFO")
        
        # 整体状态
        overall_ok = all([
            config_ok == config_total,
            tools_ok == tools_total,
            services_ok == services_total,
            deps_ok == deps_total
        ])
        
        if overall_ok:
            self.print_status("\n🎉 所有MCP工具配置正常！", "SUCCESS")
        else:
            self.print_status("\n⚠ 部分MCP工具配置需要检查", "WARNING")
            
        return overall_ok
        
    def run_check(self):
        """执行完整的MCP工具检查"""
        self.print_status("🔍 开始检查MCP工具调用情况...", "INFO")
        self.print_status(f"项目根目录: {self.project_root}", "INFO")
        
        # 检查各个组件
        configs = self.check_mcp_configs()
        tools = self.check_mcp_tools()
        services = self.check_service_files()
        dependencies = self.check_dependencies()
        
        # 生成总结
        success = self.generate_summary(configs, tools, services, dependencies)
        
        return success


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查MCP工具调用情况")
    parser.add_argument("--project-root", default=".", help="项目根目录路径")
    
    args = parser.parse_args()
    
    checker = MCPToolChecker(args.project_root)
    success = checker.run_check()
    
    if success:
        print(f"\n✅ MCP工具检查完成，一切正常")
        exit(0)
    else:
        print(f"\n❌ 发现MCP工具配置问题，请参考上述信息")
        exit(1)


if __name__ == "__main__":
    main()
