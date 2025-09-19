#!/usr/bin/env python3
"""
MCP 记忆系统统一部署脚本

集成三套工具的完整部署和管理：
1. 记忆库工具 (端口 8001) - embedding_memory_processor.py
2. 向量数据库工具 (端口 8000) - knowledge_base_service.py  
3. 角色人设服务 - mcp-persona-uozumi

功能:
- 一键环境检查和依赖安装
- 统一配置管理
- 服务启动和状态监控
- 系统测试和验证
- 服务停止和清理

Usage:
    python deploy_all_tools.py --help
    python deploy_all_tools.py check      # 检查环境
    python deploy_all_tools.py install    # 安装依赖
    python deploy_all_tools.py config     # 配置系统
    python deploy_all_tools.py start      # 启动所有服务
    python deploy_all_tools.py test       # 测试所有功能
    python deploy_all_tools.py stop       # 停止所有服务
    python deploy_all_tools.py deploy     # 一键部署（包含所有步骤）
    python deploy_all_tools.py status     # 查看服务状态
"""

import os
import sys
import json
import time
import argparse
import subprocess
import logging
import shutil
import socket
import signal
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPDeployment")

class Colors:
    """控制台颜色"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """打印状态信息"""
    color_map = {
        "SUCCESS": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARNING": Colors.YELLOW,
        "INFO": Colors.BLUE,
        "DEBUG": Colors.CYAN
    }
    color = color_map.get(status, Colors.NC)
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] [{status}]{Colors.NC} {message}")

def print_header(title: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{'='*80}")
    print(f"  🚀 {title}")
    print(f"{'='*80}{Colors.NC}\n")

class MCPUnifiedDeployment:
    """MCP统一部署管理器"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.config_dir = self.project_root / "configs"
        self.log_dir = self.project_root / "logs"
        self.pid_dir = self.project_root / "pids"
        
        # 服务配置
        self.services = {
            "memory_library": {
                "name": "记忆库工具",
                "port": 8001,
                "script": "knowledge_base_service.py",
                "env": {"KB_PORT": "8001"},
                "health_url": "http://localhost:8001/docs",
                "pid_file": "memory_library.pid",
                "log_file": "memory_library.log",
                "description": "基于Embedding的记忆存储和检索服务"
            },
            "vector_database": {
                "name": "向量数据库工具", 
                "port": 8000,
                "script": "knowledge_base_service.py",
                "env": {"KB_PORT": "8000"},
                "health_url": "http://localhost:8000/docs",
                "pid_file": "vector_database.pid",
                "log_file": "vector_database.log",
                "description": "通用向量数据库存储服务"
            },
            "persona_service": {
                "name": "角色人设服务",
                "port": 3000,
                "script": "mcp-persona-uozumi/dist/server.js",
                "command": "node",
                "health_url": None,
                "pid_file": "persona_service.pid", 
                "log_file": "persona_service.log",
                "description": "TypeScript角色人设MCP服务"
            }
        }
        
        # MCP工具配置
        self.mcp_tools = {
            "embedding_context_aggregator": {
                "name": "记忆库上下文聚合器",
                "script": "embedding_context_aggregator_mcp.py",
                "depends_on": ["memory_library"],
                "description": "基于Embedding的记忆上下文聚合"
            },
            "context_aggregator": {
                "name": "向量数据库上下文聚合器", 
                "script": "context_aggregator_mcp.py",
                "depends_on": ["vector_database"],
                "description": "传统向量数据库上下文聚合"
            },
            "knowledge_base_mcp": {
                "name": "知识库MCP工具",
                "script": "knowledge_base_mcp.py", 
                "depends_on": ["vector_database"],
                "description": "知识库MCP接口工具"
            }
        }
        
        self.processes = {}
        
    def ensure_directories(self):
        """确保必要目录存在"""
        for directory in [self.log_dir, self.pid_dir, self.config_dir]:
            directory.mkdir(exist_ok=True)
            
    def check_environment(self) -> bool:
        """检查环境要求"""
        print_header("环境检查")
        
        success = True
        
        # 检查Python
        try:
            python_version = subprocess.check_output([sys.executable, "--version"], text=True).strip()
            print_status(f"✓ Python: {python_version}", "SUCCESS")
        except Exception as e:
            print_status(f"✗ Python检查失败: {e}", "ERROR")
            success = False
            
        # 检查Node.js (persona服务需要)
        try:
            node_version = subprocess.check_output(["node", "--version"], text=True).strip()
            npm_version = subprocess.check_output(["npm", "--version"], text=True).strip()
            print_status(f"✓ Node.js: {node_version}", "SUCCESS")
            print_status(f"✓ npm: {npm_version}", "SUCCESS")
        except Exception as e:
            print_status(f"⚠ Node.js未安装，角色人设服务将不可用", "WARNING")
            
        # 检查必要文件
        required_files = [
            "knowledge_base_service.py",
            "embedding_memory_processor.py", 
            "embedding_context_aggregator_mcp.py",
            "context_aggregator_mcp.py",
            "knowledge_base_mcp.py"
        ]
        
        for file in required_files:
            if (self.project_root / file).exists():
                print_status(f"✓ {file}", "SUCCESS")
            else:
                print_status(f"✗ {file} 缺失", "ERROR")
                success = False
                
        # 检查配置文件
        config_files = ["mcp_config.json", "mcp_config.dev.json", "mcp_config.linux.json"]
        for config in config_files:
            config_path = self.config_dir / config
            if config_path.exists():
                print_status(f"✓ configs/{config}", "SUCCESS")
            else:
                print_status(f"⚠ configs/{config} 缺失", "WARNING")
                
        return success
        
    def install_dependencies(self) -> bool:
        """安装依赖包"""
        print_header("依赖安装")
        
        # Python依赖
        python_deps = [
            "fastapi>=0.104.1",
            "uvicorn>=0.24.0",
            "numpy>=1.25.2",
            "requests>=2.31.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.5.0"
        ]
        
        print_status("安装Python依赖...", "INFO")
        try:
            for dep in python_deps:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", dep
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print_status(f"✓ {dep}", "SUCCESS")
        except subprocess.CalledProcessError as e:
            print_status(f"✗ Python依赖安装失败: {e}", "ERROR")
            return False
            
        # Node.js依赖 (如果Node.js可用)
        persona_dir = self.project_root / "mcp-persona-uozumi"
        if persona_dir.exists():
            try:
                print_status("安装Node.js依赖...", "INFO")
                subprocess.check_call(
                    ["npm", "install"], 
                    cwd=persona_dir,
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                
                # 构建TypeScript
                if (persona_dir / "src").exists():
                    print_status("构建TypeScript...", "INFO")
                    subprocess.check_call(
                        ["npm", "run", "build"],
                        cwd=persona_dir,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                print_status("✓ Node.js依赖安装完成", "SUCCESS")
            except subprocess.CalledProcessError:
                print_status("⚠ Node.js依赖安装失败，角色人设服务将不可用", "WARNING")
                
        return True
        
    def configure_system(self) -> bool:
        """配置系统"""
        print_header("系统配置")
        
        # 创建或更新 .env 文件
        env_file = self.project_root / ".env"
        env_config = {
            "KB_PORT": "8001",
            "EMBEDDING_API_KEY": "your_api_key_here",
            "EMBEDDING_API_BASE": "https://api.siliconflow.cn/v1",
            "EMBEDDING_MODEL": "BAAI/bge-large-zh-v1.5"
        }
        
        if not env_file.exists():
            with open(env_file, 'w', encoding='utf-8') as f:
                for key, value in env_config.items():
                    f.write(f"{key}={value}\n")
            print_status("✓ .env 配置文件已创建", "SUCCESS")
        else:
            print_status("✓ .env 配置文件已存在", "INFO")
            
        # 检查API密钥配置
        if "your_api_key_here" in env_file.read_text():
            print_status("⚠ 请在 .env 文件中配置您的 EMBEDDING_API_KEY", "WARNING")
            
        # 创建启动脚本
        self._create_startup_scripts()
        
        return True
        
    def _create_startup_scripts(self):
        """创建启动脚本"""
        # Windows批处理脚本
        bat_script = self.project_root / "start_all_services.bat"
        with open(bat_script, 'w', encoding='utf-8') as f:
            f.write(f"""@echo off
REM MCP 三工具统一启动脚本
echo ========================================
echo     MCP 三工具统一启动器
echo ========================================

python deploy_all_tools.py start
pause
""")
        
        # Linux Shell脚本
        sh_script = self.project_root / "start_all_services.sh"
        with open(sh_script, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/bash
# MCP 三工具统一启动脚本

echo "========================================"
echo "    MCP 三工具统一启动器"
echo "========================================"

python3 deploy_all_tools.py start
""")
        
        # 设置执行权限
        if os.name != 'nt':
            os.chmod(sh_script, 0o755)
            
        print_status("✓ 启动脚本已创建", "SUCCESS")
        
    def check_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
            
    def start_service(self, service_name: str) -> bool:
        """启动单个服务"""
        service = self.services.get(service_name)
        if not service:
            print_status(f"未知服务: {service_name}", "ERROR")
            return False
            
        print_status(f"启动 {service['name']}...", "INFO")
        
        # 检查端口
        if not self.check_port_available(service['port']):
            print_status(f"端口 {service['port']} 已被占用", "ERROR")
            return False
            
        # 准备环境变量
        env = os.environ.copy()
        env.update(service.get('env', {}))
        env['PYTHONPATH'] = str(self.project_root)
        
        # 准备日志和PID文件
        log_file = self.log_dir / service['log_file']
        pid_file = self.pid_dir / service['pid_file']
        
        # 启动服务
        try:
            script_path = self.project_root / service['script']
            
            if service_name == "persona_service":
                # Node.js服务
                cmd = ["node", str(script_path)]
            else:
                # Python服务
                cmd = [sys.executable, str(script_path)]
                
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=self.project_root
                )
                
            # 保存进程信息
            self.processes[service_name] = process
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
                
            # 等待服务启动
            time.sleep(3)
            
            # 检查服务健康状态
            if self._check_service_health(service_name):
                print_status(f"✓ {service['name']} 启动成功 (PID: {process.pid})", "SUCCESS")
                return True
            else:
                print_status(f"✗ {service['name']} 启动失败", "ERROR")
                self.stop_service(service_name)
                return False
                
        except Exception as e:
            print_status(f"✗ {service['name']} 启动异常: {e}", "ERROR")
            return False
            
    def _check_service_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        service = self.services[service_name]
        
        if service.get('health_url'):
            try:
                response = requests.get(service['health_url'], timeout=5)
                return response.status_code == 200
            except:
                return False
        else:
            # 对于没有健康检查URL的服务，检查进程是否还在运行
            process = self.processes.get(service_name)
            return process and process.poll() is None
            
    def stop_service(self, service_name: str) -> bool:
        """停止单个服务"""
        service = self.services.get(service_name)
        if not service:
            return False
            
        print_status(f"停止 {service['name']}...", "INFO")
        
        # 从进程字典中获取进程
        process = self.processes.get(service_name)
        pid_file = self.pid_dir / service['pid_file']
        
        # 如果没有进程对象，尝试从PID文件读取
        if not process and pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                    if os.name == 'nt':
                        subprocess.call(['taskkill', '/F', '/PID', str(pid)], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(2)
                        try:
                            os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
            except:
                pass
                
        # 如果有进程对象，直接终止
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass
                
        # 清理文件
        if pid_file.exists():
            pid_file.unlink()
            
        if service_name in self.processes:
            del self.processes[service_name]
            
        print_status(f"✓ {service['name']} 已停止", "SUCCESS")
        return True
        
    def start_all_services(self) -> bool:
        """启动所有服务"""
        print_header("启动所有服务")
        
        success = True
        
        # 按依赖顺序启动服务
        start_order = ["memory_library", "vector_database", "persona_service"]
        
        for service_name in start_order:
            if not self.start_service(service_name):
                success = False
                break
            time.sleep(2)  # 服务间启动间隔
            
        if success:
            print_status("🎉 所有服务启动成功！", "SUCCESS")
            self._show_service_urls()
        else:
            print_status("❌ 部分服务启动失败", "ERROR")
            
        return success
        
    def stop_all_services(self) -> bool:
        """停止所有服务"""
        print_header("停止所有服务")
        
        for service_name in self.services.keys():
            self.stop_service(service_name)
            
        print_status("✓ 所有服务已停止", "SUCCESS")
        return True
        
    def _show_service_urls(self):
        """显示服务访问地址"""
        print_status("\n📋 服务访问地址:", "INFO")
        print(f"  🧠 记忆库工具: http://localhost:8001/docs")
        print(f"  📚 向量数据库工具: http://localhost:8000/docs") 
        print(f"  👤 角色人设服务: Node.js MCP服务 (无HTTP接口)")
        
    def test_all_systems(self) -> bool:
        """测试所有系统"""
        print_header("系统功能测试")
        
        success = True
        
        # 测试记忆库工具
        print_status("测试记忆库工具...", "INFO")
        if self._test_memory_service():
            print_status("✓ 记忆库工具测试通过", "SUCCESS")
        else:
            print_status("✗ 记忆库工具测试失败", "ERROR")
            success = False
            
        # 测试向量数据库工具
        print_status("测试向量数据库工具...", "INFO") 
        if self._test_vector_service():
            print_status("✓ 向量数据库工具测试通过", "SUCCESS")
        else:
            print_status("✗ 向量数据库工具测试失败", "ERROR")
            success = False
            
        # 运行统一测试脚本
        print_status("运行完整测试套件...", "INFO")
        try:
            result = subprocess.run([
                sys.executable, "test_embedding_memory.py", "all"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print_status("✓ 完整测试套件通过", "SUCCESS")
            else:
                print_status("⚠ 完整测试套件有警告，请查看详细日志", "WARNING")
                
        except Exception as e:
            print_status(f"✗ 测试套件运行失败: {e}", "ERROR")
            success = False
            
        return success
        
    def _test_memory_service(self) -> bool:
        """测试记忆库服务"""
        try:
            response = requests.get("http://localhost:8001/docs", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def _test_vector_service(self) -> bool:
        """测试向量数据库服务"""
        try:
            response = requests.get("http://localhost:8000/docs", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def show_status(self) -> bool:
        """显示服务状态"""
        print_header("服务状态")
        
        for service_name, service in self.services.items():
            pid_file = self.pid_dir / service['pid_file']
            
            if pid_file.exists():
                try:
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()
                    
                    # 检查进程是否还在运行
                    if os.name == 'nt':
                        result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}'],
                            capture_output=True, text=True
                        )
                        is_running = pid in result.stdout
                    else:
                        try:
                            os.kill(int(pid), 0)
                            is_running = True
                        except ProcessLookupError:
                            is_running = False
                            
                    if is_running:
                        status = "运行中"
                        color = "SUCCESS"
                        
                        # 检查健康状态
                        if self._check_service_health(service_name):
                            health = "健康"
                        else:
                            health = "异常"
                            color = "WARNING"
                    else:
                        status = "已停止"
                        health = "N/A"
                        color = "ERROR"
                        
                except Exception:
                    status = "未知"
                    health = "N/A"
                    color = "WARNING"
            else:
                status = "未启动"
                health = "N/A"
                color = "ERROR"
                
            print_status(f"{service['name']}: {status} ({health})", color)
            print(f"    端口: {service['port']}")
            print(f"    PID文件: {pid_file}")
            print(f"    日志: {self.log_dir / service['log_file']}")
            print()
            
        return True
        
    def deploy_system(self) -> bool:
        """一键部署系统"""
        print_header("MCP 三工具统一部署")
        
        steps = [
            ("环境检查", self.check_environment),
            ("创建目录", self.ensure_directories),
            ("安装依赖", self.install_dependencies),
            ("配置系统", self.configure_system),
            ("启动服务", self.start_all_services),
            ("测试功能", self.test_all_systems)
        ]
        
        for step_name, step_func in steps:
            print_status(f"执行步骤: {step_name}", "INFO")
            if not step_func():
                print_status(f"❌ 部署失败在: {step_name}", "ERROR")
                return False
            time.sleep(1)
            
        print_header("🎉 部署完成")
        print_status("所有工具已成功部署并启动！", "SUCCESS")
        print_status("您现在可以使用以下命令:", "INFO")
        print("  python deploy_all_tools.py status  # 查看服务状态")
        print("  python deploy_all_tools.py test    # 运行测试")
        print("  python deploy_all_tools.py stop    # 停止所有服务")
        
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP 三工具统一部署管理")
    parser.add_argument('action', choices=[
        'check', 'install', 'config', 'start', 'stop', 'test', 'status', 'deploy'
    ], help='执行的操作')
    
    args = parser.parse_args()
    
    # 注册信号处理器用于优雅关闭
    deployment = MCPUnifiedDeployment()
    
    def signal_handler(signum, frame):
        print_status("\n接收到停止信号，正在关闭服务...", "WARNING")
        deployment.stop_all_services()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    # 执行对应操作
    try:
        if args.action == 'check':
            success = deployment.check_environment()
        elif args.action == 'install':
            success = deployment.install_dependencies()
        elif args.action == 'config':
            deployment.ensure_directories()
            success = deployment.configure_system()
        elif args.action == 'start':
            deployment.ensure_directories()
            success = deployment.start_all_services()
        elif args.action == 'stop':
            success = deployment.stop_all_services()
        elif args.action == 'test':
            success = deployment.test_all_systems()
        elif args.action == 'status':
            success = deployment.show_status()
        elif args.action == 'deploy':
            success = deployment.deploy_system()
        else:
            print_status(f"未知操作: {args.action}", "ERROR")
            success = False
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print_status("\n用户中断操作", "WARNING")
        deployment.stop_all_services()
        sys.exit(1)
    except Exception as e:
        print_status(f"执行失败: {e}", "ERROR")
        logger.exception("详细错误信息:")
        sys.exit(1)


if __name__ == "__main__":
    main()
