#!/usr/bin/env python3
"""
端口冲突检查工具

检查记忆库工具(8001)和向量数据库工具(8000)之间的端口配置，确保没有冲突。
"""

import os
import json
import glob
import re
from typing import Dict, List, Tuple, Set
from pathlib import Path

class PortConflictChecker:
    """端口冲突检查器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.memory_tools_port = 8001  # 记忆库工具端口
        self.vector_db_port = 8000     # 向量数据库工具端口
        
        # 定义工具分类
        self.memory_tools = {
            "embedding_memory_processor.py",
            "embedding_context_aggregator_mcp.py", 
            "test_embedding_memory.py",
            "mcp_memory_manager.py"
        }
        
        self.vector_db_tools = {
            "knowledge_base_service.py",
            "context_aggregator_mcp.py",
            "memory_processor.py",
            "mcp-calculator/vector_db.py",
            "mcp-calculator/knowledge_base_service.py"
        }
        
        self.conflicts = []
        self.warnings = []
        
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
        
    def extract_port_from_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """从文件中提取端口配置"""
        ports_found = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找端口模式
            patterns = [
                r'localhost:(\d{4})',           # localhost:8000
                r'"(\d{4})"',                   # "8000"
                r'=\s*(\d{4})',                 # = 8000
                r'port\s*=\s*(\d{4})',          # port = 8000
                r'KB_PORT.*?(\d{4})',           # KB_PORT": "8000"
                r'http://localhost:(\d{4})'     # http://localhost:8000
            ]
            
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        port = int(match)
                        if 8000 <= port <= 8001:  # 只关注这两个端口
                            ports_found.append((port, f"第{i}行", line.strip()))
                            
        except Exception as e:
            self.print_status(f"读取文件 {file_path} 时出错: {e}", "ERROR")
            
        return ports_found
        
    def check_python_files(self) -> Dict[str, List[Tuple[int, str, str]]]:
        """检查Python文件中的端口配置"""
        results = {}
        
        # 搜索所有Python文件
        python_files = list(self.project_root.glob("**/*.py"))
        
        for file_path in python_files:
            relative_path = str(file_path.relative_to(self.project_root))
            ports = self.extract_port_from_file(file_path)
            
            if ports:
                results[relative_path] = ports
                
        return results
        
    def check_json_configs(self) -> Dict[str, List[Tuple[int, str, str]]]:
        """检查JSON配置文件"""
        results = {}
        
        # 搜索所有JSON文件
        json_files = list(self.project_root.glob("**/*.json"))
        
        for file_path in json_files:
            relative_path = str(file_path.relative_to(self.project_root))
            ports = self.extract_port_from_file(file_path)
            
            if ports:
                results[relative_path] = ports
                
        return results
        
    def analyze_conflicts(self, python_results: Dict, json_results: Dict):
        """分析端口冲突"""
        self.print_status("\n=== 端口冲突分析 ===", "INFO")
        
        all_results = {**python_results, **json_results}
        
        for file_path, ports in all_results.items():
            file_name = os.path.basename(file_path)
            
            # 确定文件应该使用的端口
            expected_port = None
            tool_type = None
            
            if any(tool in file_path for tool in self.memory_tools):
                expected_port = self.memory_tools_port
                tool_type = "记忆库工具"
            elif any(tool in file_path for tool in self.vector_db_tools):
                expected_port = self.vector_db_port  
                tool_type = "向量数据库工具"
            elif "mcp_config" in file_path:
                # MCP配置文件需要特殊处理
                tool_type = "MCP配置"
                
            for port, location, line in ports:
                if expected_port:
                    if port == expected_port:
                        self.print_status(f"✓ {file_path} ({tool_type}) - 端口 {port} 配置正确", "SUCCESS")
                    else:
                        conflict_msg = f"⚠ {file_path} ({tool_type}) - 端口 {port} 应为 {expected_port}"
                        self.print_status(conflict_msg, "WARNING")
                        self.conflicts.append({
                            "file": file_path,
                            "current_port": port,
                            "expected_port": expected_port,
                            "tool_type": tool_type,
                            "location": location,
                            "line": line
                        })
                else:
                    # 未分类的文件
                    self.print_status(f"? {file_path} - 端口 {port} (未分类)", "INFO")
                    
    def generate_fix_suggestions(self):
        """生成修复建议"""
        if not self.conflicts:
            self.print_status("\n🎉 没有发现端口冲突！", "SUCCESS")
            return
            
        self.print_status(f"\n⚠ 发现 {len(self.conflicts)} 个端口配置问题：", "WARNING")
        self.print_status("\n=== 修复建议 ===", "INFO")
        
        for i, conflict in enumerate(self.conflicts, 1):
            print(f"\n{i}. 文件: {conflict['file']}")
            print(f"   工具类型: {conflict['tool_type']}")
            print(f"   当前端口: {conflict['current_port']}")
            print(f"   建议端口: {conflict['expected_port']}")
            print(f"   位置: {conflict['location']}")
            print(f"   代码行: {conflict['line']}")
            
        self.print_status("\n=== 端口分配规则 ===", "INFO")
        print("📋 记忆库工具 (端口 8001):")
        for tool in sorted(self.memory_tools):
            print(f"   - {tool}")
            
        print("\n📋 向量数据库工具 (端口 8000):")
        for tool in sorted(self.vector_db_tools):
            print(f"   - {tool}")
            
    def run_check(self):
        """执行完整的端口冲突检查"""
        self.print_status("🔍 开始检查端口配置冲突...", "INFO")
        self.print_status(f"项目根目录: {self.project_root}", "INFO")
        
        # 检查Python文件
        self.print_status("\n📝 检查Python文件...", "INFO")
        python_results = self.check_python_files()
        
        # 检查JSON配置文件
        self.print_status("📋 检查JSON配置文件...", "INFO") 
        json_results = self.check_json_configs()
        
        # 分析冲突
        self.analyze_conflicts(python_results, json_results)
        
        # 生成修复建议
        self.generate_fix_suggestions()
        
        return len(self.conflicts) == 0


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查MCP工具端口配置冲突")
    parser.add_argument("--project-root", default=".", help="项目根目录路径")
    
    args = parser.parse_args()
    
    checker = PortConflictChecker(args.project_root)
    success = checker.run_check()
    
    if success:
        print(f"\n✅ 端口配置检查完成，无冲突")
        exit(0)
    else:
        print(f"\n❌ 发现端口配置冲突，请参考上述修复建议")
        exit(1)


if __name__ == "__main__":
    main()
