#!/usr/bin/env python3
"""
MCP 记忆系统部署管理脚本

该脚本用于管理整个 MCP 记忆系统的部署，包括：
1. 服务依赖检查
2. 配置验证
3. 服务启动/停止
4. 健康检查
5. 日志管理
"""

import json
import os
import subprocess
import time
import sys
import requests
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import signal

class MCPDeploymentManager:
    """MCP 记忆系统部署管理器"""
    
    def __init__(self, config_file: str = "configs/mcp_config.json"):
        self.config_file = Path(config_file)
        self.processes: Dict[str, subprocess.Popen] = {}
        self.config = self._load_config()
        self.workspace_root = Path.cwd()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            sys.exit(1)
    
    def validate_config(self) -> bool:
        """验证配置文件的有效性"""
        print("🔍 验证配置文件...")
        
        required_sections = ["mcpServers", "globalConfig"]
        for section in required_sections:
            if section not in self.config:
                print(f"❌ 配置缺少必需节: {section}")
                return False
        
        # 验证必需的服务
        required_services = ["knowledge-base", "context-aggregator"]
        mcp_servers = self.config.get("mcpServers", {})
        
        for service in required_services:
            if service not in mcp_servers:
                print(f"❌ 缺少必需服务: {service}")
                return False
        
        print("✅ 配置文件验证通过")
        return True
    
    def check_dependencies(self) -> bool:
        """检查依赖项"""
        print("🔍 检查系统依赖...")
        
        # 检查 Python
        try:
            result = subprocess.run(["python", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Python: {result.stdout.strip()}")
            else:
                print("❌ Python 未安装或不可用")
                return False
        except:
            print("❌ Python 检查失败")
            return False
        
        # 检查 Node.js (如果需要)
        if "persona-uozumi" in self.config.get("mcpServers", {}):
            try:
                result = subprocess.run(["node", "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Node.js: {result.stdout.strip()}")
                else:
                    print("❌ Node.js 未安装或不可用")
                    return False
            except:
                print("❌ Node.js 检查失败")
                return False
        
        # 检查 Python 包
        required_packages = ["mcp", "fastapi", "requests", "numpy"]
        for package in required_packages:
            try:
                result = subprocess.run([
                    "python", "-c", f"import {package}; print('{package} 已安装')"
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Python 包: {package}")
                else:
                    print(f"❌ Python 包缺失: {package}")
                    return False
            except:
                print(f"❌ Python 包检查失败: {package}")
                return False
        
        print("✅ 依赖检查通过")
        return True
    
    def start_http_services(self) -> bool:
        """启动 HTTP 服务"""
        http_services = self.config.get("httpServices", {})
        
        for service_name, service_config in http_services.items():
            print(f"🚀 启动 HTTP 服务: {service_name}")
            
            try:
                # 设置环境变量
                env = os.environ.copy()
                env.update(service_config.get("env", {}))
                
                # 启动进程
                process = subprocess.Popen(
                    [service_config["command"]] + service_config["args"],
                    cwd=service_config["cwd"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.processes[service_name] = process
                
                # 等待服务启动
                if "port" in service_config:
                    port = service_config["port"]
                    if self._wait_for_service(f"http://localhost:{port}", timeout=30):
                        print(f"✅ {service_name} 启动成功 (端口 {port})")
                    else:
                        print(f"❌ {service_name} 启动失败")
                        return False
                else:
                    time.sleep(3)
                    if process.poll() is None:
                        print(f"✅ {service_name} 启动成功")
                    else:
                        print(f"❌ {service_name} 启动失败")
                        return False
                        
            except Exception as e:
                print(f"❌ 启动 {service_name} 时发生错误: {e}")
                return False
        
        return True
    
    def start_mcp_services(self) -> bool:
        """启动 MCP 服务"""
        mcp_servers = self.config.get("mcpServers", {})
        
        # 按依赖顺序启动服务
        start_order = ["persona-uozumi", "knowledge-base", "context-aggregator"]
        
        for service_name in start_order:
            if service_name not in mcp_servers:
                continue
                
            service_config = mcp_servers[service_name]
            print(f"🚀 启动 MCP 服务: {service_name}")
            
            try:
                # 设置环境变量
                env = os.environ.copy()
                env.update(service_config.get("env", {}))
                
                # 启动进程
                process = subprocess.Popen(
                    [service_config["command"]] + service_config["args"],
                    cwd=service_config["cwd"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.processes[service_name] = process
                
                # 等待一段时间确保服务启动
                time.sleep(2)
                
                if process.poll() is None:
                    print(f"✅ {service_name} 启动成功")
                else:
                    stdout, stderr = process.communicate()
                    print(f"❌ {service_name} 启动失败")
                    print(f"输出: {stdout.decode()}")
                    print(f"错误: {stderr.decode()}")
                    return False
                    
            except Exception as e:
                print(f"❌ 启动 {service_name} 时发生错误: {e}")
                return False
        
        return True
    
    def _wait_for_service(self, url: str, timeout: int = 30) -> bool:
        """等待服务可用"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code in [200, 404]:  # 404 也表示服务在运行
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        print("🔍 执行健康检查...")
        
        results = {}
        
        # 检查 HTTP 服务
        http_services = self.config.get("httpServices", {})
        for service_name, service_config in http_services.items():
            if "healthCheck" in service_config:
                url = service_config["healthCheck"]["url"]
                try:
                    response = requests.get(url, timeout=5)
                    results[service_name] = response.status_code == 200
                    status = "✅" if results[service_name] else "❌"
                    print(f"{status} {service_name}: {response.status_code}")
                except Exception as e:
                    results[service_name] = False
                    print(f"❌ {service_name}: {e}")
        
        # 检查 MCP 服务进程
        for service_name, process in self.processes.items():
            if service_name not in results:  # 避免重复检查
                is_running = process.poll() is None
                results[service_name] = is_running
                status = "✅" if is_running else "❌"
                print(f"{status} {service_name}: {'运行中' if is_running else '已停止'}")
        
        return results
    
    def stop_all(self):
        """停止所有服务"""
        print("🛑 停止所有服务...")
        
        for service_name, process in self.processes.items():
            try:
                print(f"停止 {service_name}...")
                process.terminate()
                
                # 等待进程终止
                try:
                    process.wait(timeout=10)
                    print(f"✅ {service_name} 已停止")
                except subprocess.TimeoutExpired:
                    print(f"强制终止 {service_name}...")
                    process.kill()
                    process.wait()
                    print(f"✅ {service_name} 已强制停止")
            except Exception as e:
                print(f"❌ 停止 {service_name} 时发生错误: {e}")
        
        self.processes.clear()
    
    def deploy(self) -> bool:
        """完整部署流程"""
        print("🚀 开始部署 MCP 记忆系统...")
        print("="*60)
        
        # 1. 验证配置
        if not self.validate_config():
            return False
        
        # 2. 检查依赖
        if not self.check_dependencies():
            return False
        
        # 3. 启动 HTTP 服务
        if not self.start_http_services():
            self.stop_all()
            return False
        
        # 4. 启动 MCP 服务
        if not self.start_mcp_services():
            self.stop_all()
            return False
        
        # 5. 健康检查
        time.sleep(5)  # 等待服务稳定
        health_results = self.health_check()
        
        if all(health_results.values()):
            print("\n" + "="*60)
            print("🎉 MCP 记忆系统部署成功！")
            print("\n可用服务:")
            for service, status in health_results.items():
                print(f"  ✅ {service}")
            return True
        else:
            print("\n" + "="*60)
            print("❌ 部署过程中发现问题")
            failed_services = [s for s, status in health_results.items() if not status]
            print(f"失败的服务: {', '.join(failed_services)}")
            return False
    
    def status(self):
        """显示服务状态"""
        print("📊 MCP 记忆系统状态")
        print("="*60)
        
        health_results = self.health_check()
        
        running_count = sum(1 for status in health_results.values() if status)
        total_count = len(health_results)
        
        print(f"\n状态概览: {running_count}/{total_count} 服务运行中")
        
        if running_count == total_count:
            print("🟢 所有服务正常运行")
        elif running_count > 0:
            print("🟡 部分服务运行中")
        else:
            print("🔴 所有服务已停止")

def signal_handler(signum, frame):
    """信号处理器"""
    global deployment_manager
    print("\n接收到停止信号，正在停止服务...")
    if 'deployment_manager' in globals():
        deployment_manager.stop_all()
    sys.exit(0)

def main():
    """主函数"""
    global deployment_manager
    
    parser = argparse.ArgumentParser(description="MCP 记忆系统部署管理器")
    parser.add_argument("action", choices=["deploy", "start", "stop", "status", "health"], 
                       help="执行的操作")
    parser.add_argument("--config", default="configs/mcp_config.json",
                       help="配置文件路径")
    parser.add_argument("--dev", action="store_true",
                       help="使用开发配置")
    
    args = parser.parse_args()
    
    # 选择配置文件
    config_file = "configs/mcp_config.dev.json" if args.dev else args.config
    
    # 创建部署管理器
    deployment_manager = MCPDeploymentManager(config_file)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.action == "deploy":
            success = deployment_manager.deploy()
            if success:
                print("\n按 Ctrl+C 停止所有服务")
                # 保持运行状态
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            sys.exit(0 if success else 1)
            
        elif args.action == "start":
            print("🚀 启动 MCP 记忆系统...")
            deployment_manager.start_http_services()
            deployment_manager.start_mcp_services()
            print("✅ 启动完成")
            
        elif args.action == "stop":
            deployment_manager.stop_all()
            
        elif args.action == "status":
            deployment_manager.status()
            
        elif args.action == "health":
            deployment_manager.health_check()
            
    except KeyboardInterrupt:
        print("\n正在停止...")
        deployment_manager.stop_all()
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
