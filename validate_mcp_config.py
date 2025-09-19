#!/usr/bin/env python3
"""
MCP配置验证和修复工具
用于检查和修复Linux环境下的MCP配置问题
"""

import json
import os
import sys
import subprocess
import requests
import time
from pathlib import Path

class MCPConfigValidator:
    def __init__(self, work_dir="/root/mcp_database"):
        self.work_dir = Path(work_dir)
        self.config_file = self.work_dir / "configs" / "mcp_config.linux.json"
        self.errors = []
        self.warnings = []
        self.fixes_applied = []
    
    def print_status(self, message, status="INFO"):
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m", 
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "RESET": "\033[0m"
        }
        print(f"{colors.get(status, '')}{status}: {message}{colors['RESET']}")
    
    def check_file_exists(self, filepath, description):
        """检查文件是否存在"""
        if filepath.exists():
            self.print_status(f"✓ {description} 存在", "SUCCESS")
            return True
        else:
            self.print_status(f"✗ {description} 不存在: {filepath}", "ERROR")
            self.errors.append(f"{description} 文件缺失")
            return False
    
    def check_python_environment(self):
        """检查Python环境"""
        self.print_status("检查Python环境...", "INFO")
        
        # 检查python3命令
        try:
            result = subprocess.run(["python3", "--version"], 
                                  capture_output=True, text=True, check=True)
            self.print_status(f"✓ Python3 版本: {result.stdout.strip()}", "SUCCESS")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_status("✗ Python3 命令不可用", "ERROR")
            self.errors.append("Python3 未安装或不在PATH中")
        
        # 检查关键Python包
        required_packages = ["fastapi", "uvicorn", "numpy", "requests"]
        for package in required_packages:
            try:
                subprocess.run(["python3", "-c", f"import {package}"], 
                             capture_output=True, check=True)
                self.print_status(f"✓ Python包 {package} 可用", "SUCCESS")
            except subprocess.CalledProcessError:
                self.print_status(f"✗ Python包 {package} 缺失", "ERROR")
                self.errors.append(f"Python包 {package} 未安装")
    
    def load_config(self):
        """加载并验证配置文件"""
        self.print_status("检查MCP配置文件...", "INFO")
        
        if not self.check_file_exists(self.config_file, "MCP配置文件"):
            return None
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.print_status("✓ 配置文件格式正确", "SUCCESS")
            return config
        except json.JSONDecodeError as e:
            self.print_status(f"✗ 配置文件JSON格式错误: {e}", "ERROR")
            self.errors.append("配置文件JSON格式无效")
            return None
    
    def validate_config_structure(self, config):
        """验证配置文件结构"""
        self.print_status("验证配置文件结构...", "INFO")
        
        if not config:
            return False
        
        # 检查基本结构
        if "mcpServers" not in config:
            self.print_status("✗ 缺少 mcpServers 配置", "ERROR")
            self.errors.append("配置文件缺少 mcpServers 部分")
            return False
        
        mcp_servers = config["mcpServers"]
        
        # 检查关键服务
        required_services = ["context-aggregator", "knowledge-base", "knowledge-base-http"]
        for service in required_services:
            if service in mcp_servers:
                self.print_status(f"✓ 服务 {service} 配置存在", "SUCCESS")
                self.validate_service_config(service, mcp_servers[service])
            else:
                self.print_status(f"✗ 缺少服务 {service} 配置", "ERROR")
                self.errors.append(f"缺少服务 {service} 配置")
        
        return True
    
    def validate_service_config(self, service_name, service_config):
        """验证单个服务配置"""
        # 检查command字段
        if "command" in service_config:
            command = service_config["command"]
            if command == "python3":
                self.print_status(f"✓ {service_name} 使用正确的Python命令", "SUCCESS")
            elif command == "python":
                self.print_status(f"⚠ {service_name} 使用 'python' 命令，建议使用 'python3'", "WARNING")
                self.warnings.append(f"{service_name} 应使用 python3 命令")
            else:
                self.print_status(f"? {service_name} 使用命令: {command}", "INFO")
        
        # 检查args字段中的脚本路径
        if "args" in service_config and service_config["args"]:
            script_path = service_config["args"][0]
            full_path = self.work_dir / script_path
            if full_path.exists():
                self.print_status(f"✓ {service_name} 脚本文件存在", "SUCCESS")
            else:
                self.print_status(f"✗ {service_name} 脚本文件不存在: {full_path}", "ERROR")
                self.errors.append(f"{service_name} 脚本文件缺失")
        
        # 检查环境变量中的端口配置
        if "env" in service_config:
            env = service_config["env"]
            if "KB_PORT" in env:
                port = env["KB_PORT"]
                if port == "8001":
                    self.print_status(f"✓ {service_name} 端口配置正确 (8001)", "SUCCESS")
                else:
                    self.print_status(f"⚠ {service_name} 端口配置: {port}, 建议使用 8001", "WARNING")
                    self.warnings.append(f"{service_name} 端口不是标准的8001")
    
    def check_port_availability(self, port=8001):
        """检查端口可用性"""
        self.print_status(f"检查端口 {port} 可用性...", "INFO")
        
        try:
            result = subprocess.run(["netstat", "-tlnp"], 
                                  capture_output=True, text=True, check=True)
            if f":{port} " in result.stdout:
                self.print_status(f"⚠ 端口 {port} 已被占用", "WARNING")
                self.warnings.append(f"端口 {port} 被其他进程占用")
                
                # 尝试找出占用进程
                for line in result.stdout.split('\n'):
                    if f":{port} " in line:
                        self.print_status(f"占用详情: {line.strip()}", "INFO")
                        break
            else:
                self.print_status(f"✓ 端口 {port} 可用", "SUCCESS")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_status("无法检查端口状态 (netstat不可用)", "WARNING")
    
    def test_service_connection(self, port=8001):
        """测试服务连接"""
        self.print_status(f"测试服务连接 localhost:{port}...", "INFO")
        
        try:
            response = requests.get(f"http://localhost:{port}/docs", timeout=5)
            if response.status_code == 200:
                self.print_status(f"✓ 服务 localhost:{port} 连接成功", "SUCCESS")
                return True
            else:
                self.print_status(f"⚠ 服务 localhost:{port} 返回状态码: {response.status_code}", "WARNING")
                return False
        except requests.exceptions.ConnectionError:
            self.print_status(f"✗ 无法连接到 localhost:{port}", "ERROR")
            return False
        except requests.exceptions.Timeout:
            self.print_status(f"⚠ 连接 localhost:{port} 超时", "WARNING")
            return False
        except Exception as e:
            self.print_status(f"⚠ 连接测试异常: {e}", "WARNING")
            return False
    
    def apply_fixes(self):
        """应用自动修复"""
        if not self.warnings and not self.errors:
            self.print_status("没有需要修复的问题", "SUCCESS")
            return
        
        self.print_status("尝试应用自动修复...", "INFO")
        
        # 修复配置文件中的python命令
        config = self.load_config()
        if config:
            modified = False
            for service_name, service_config in config.get("mcpServers", {}).items():
                if service_config.get("command") == "python":
                    service_config["command"] = "python3"
                    self.print_status(f"✓ 修复 {service_name} Python命令", "SUCCESS")
                    self.fixes_applied.append(f"更新 {service_name} 使用 python3")
                    modified = True
            
            if modified:
                try:
                    with open(self.config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    self.print_status("✓ 配置文件已更新", "SUCCESS")
                except Exception as e:
                    self.print_status(f"✗ 保存配置文件失败: {e}", "ERROR")
    
    def generate_fix_script(self):
        """生成修复脚本"""
        fix_script_path = self.work_dir / "fix_mcp_config.sh"
        
        script_content = """#!/bin/bash

# MCP配置自动修复脚本
echo "开始MCP配置修复..."

# 设置工作目录
cd /root/mcp_database

# 确保Python3可用
if ! command -v python3 &> /dev/null; then
    echo "安装Python3..."
    apt-get update
    apt-get install -y python3 python3-pip
fi

# 安装必要的Python包
echo "安装Python依赖..."
pip3 install fastapi uvicorn numpy requests python-multipart

# 创建必要的目录
mkdir -p /root/logs /root/pids

# 设置脚本权限
chmod +x *.sh

# 检查服务是否在运行，如果是则停止
if pgrep -f "knowledge_base_service.py" > /dev/null; then
    echo "停止现有服务..."
    pkill -f "knowledge_base_service.py"
    sleep 2
fi

# 启动知识库服务
echo "启动知识库服务..."
export KB_PORT=8001
export PYTHONPATH="/root/mcp_database"
nohup python3 knowledge_base_service.py > /root/logs/knowledge_base_http.log 2>&1 &
echo $! > /root/pids/knowledge_base_http.pid

# 等待服务启动
echo "等待服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8001/docs > /dev/null 2>&1; then
        echo "✓ 服务启动成功"
        break
    fi
    sleep 1
done

echo "MCP配置修复完成！"
"""
        
        try:
            with open(fix_script_path, 'w') as f:
                f.write(script_content)
            os.chmod(fix_script_path, 0o755)
            self.print_status(f"✓ 修复脚本已生成: {fix_script_path}", "SUCCESS")
            return fix_script_path
        except Exception as e:
            self.print_status(f"✗ 生成修复脚本失败: {e}", "ERROR")
            return None
    
    def run_validation(self):
        """运行完整验证流程"""
        self.print_status("开始MCP配置验证...", "INFO")
        print("=" * 50)
        
        # 1. 检查工作目录
        if not self.work_dir.exists():
            self.print_status(f"✗ 工作目录不存在: {self.work_dir}", "ERROR")
            self.errors.append("工作目录不存在")
            return False
        
        # 2. 检查关键文件
        key_files = [
            ("knowledge_base_service.py", "知识库服务脚本"),
            ("embedding_memory_processor.py", "记忆处理脚本"),
            ("embedding_context_aggregator_mcp.py", "MCP聚合器脚本"),
        ]
        
        for filename, description in key_files:
            self.check_file_exists(self.work_dir / filename, description)
        
        # 3. 检查Python环境
        self.check_python_environment()
        
        # 4. 验证配置文件
        config = self.load_config()
        self.validate_config_structure(config)
        
        # 5. 检查端口
        self.check_port_availability()
        
        # 6. 测试服务连接
        self.test_service_connection()
        
        print("=" * 50)
        self.print_summary()
        
        return len(self.errors) == 0
    
    def print_summary(self):
        """打印验证摘要"""
        self.print_status("验证摘要", "INFO")
        
        if self.errors:
            self.print_status(f"发现 {len(self.errors)} 个错误:", "ERROR")
            for error in self.errors:
                print(f"  ✗ {error}")
        
        if self.warnings:
            self.print_status(f"发现 {len(self.warnings)} 个警告:", "WARNING")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        if self.fixes_applied:
            self.print_status(f"应用了 {len(self.fixes_applied)} 个修复:", "SUCCESS")
            for fix in self.fixes_applied:
                print(f"  ✓ {fix}")
        
        if not self.errors and not self.warnings:
            self.print_status("✓ 所有检查通过！", "SUCCESS")
        elif not self.errors:
            self.print_status("✓ 验证通过，有一些警告", "SUCCESS")
        else:
            self.print_status("✗ 验证失败，需要修复错误", "ERROR")
            fix_script = self.generate_fix_script()
            if fix_script:
                self.print_status(f"运行修复脚本: {fix_script}", "INFO")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP配置验证和修复工具")
    parser.add_argument("--work-dir", default="/root/mcp_database", 
                       help="工作目录路径")
    parser.add_argument("--fix", action="store_true", 
                       help="自动应用修复")
    parser.add_argument("--port", type=int, default=8001, 
                       help="检查的服务端口")
    
    args = parser.parse_args()
    
    validator = MCPConfigValidator(args.work_dir)
    
    # 运行验证
    success = validator.run_validation()
    
    # 应用修复（如果请求）
    if args.fix:
        validator.apply_fixes()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
