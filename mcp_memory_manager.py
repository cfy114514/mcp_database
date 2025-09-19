#!/usr/bin/env python3
"""
MCP Embedding记忆库 - 统一管理脚本

功能：
1. 环境检查和验证
2. 服务启动和管理  
3. 系统测试和验证
4. 一键部署和配置

Usage:
    python mcp_memory_manager.py --help
    python mcp_memory_manager.py check     # 检查环境
    python mcp_memory_manager.py start     # 启动服务
    python mcp_memory_manager.py test      # 测试功能
    python mcp_memory_manager.py deploy    # 一键部署
"""

import os
import sys
import json
import time
import argparse
import subprocess
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPMemoryManager")

class Colors:
    """控制台颜色"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

def print_status(message: str, status: str = "INFO"):
    """打印状态信息"""
    color_map = {
        "SUCCESS": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARNING": Colors.YELLOW,
        "INFO": Colors.BLUE
    }
    color = color_map.get(status, Colors.NC)
    print(f"{color}[{status}]{Colors.NC} {message}")

class MCPMemoryManager:
    """MCP记忆库管理器"""
    
    def __init__(self):
        self.work_dir = Path.cwd()
        self.kb_port = 8001
        self.kb_url = f"http://localhost:{self.kb_port}"
        self.log_dir = self.work_dir / "logs"
        self.pid_dir = self.work_dir / "pids"
        
        # 创建必要目录
        self.log_dir.mkdir(exist_ok=True)
        self.pid_dir.mkdir(exist_ok=True)
        
        # 核心文件列表
        self.core_files = [
            "knowledge_base_service.py",
            "embedding_memory_processor.py", 
            "embedding_context_aggregator_mcp.py"
        ]
    
    def check_environment(self) -> bool:
        """检查环境配置"""
        print_status("=== 环境检查 ===", "INFO")
        success = True
        
        # 1. 检查Python环境
        try:
            python_version = sys.version.split()[0]
            print_status(f"✓ Python版本: {python_version}", "SUCCESS")
        except Exception:
            print_status("✗ Python环境异常", "ERROR")
            success = False
        
        # 2. 检查必需的Python包
        required_packages = [
            "fastapi", "uvicorn", "numpy", "requests", "python-multipart"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                print_status(f"✓ Python包 {package} 可用", "SUCCESS")
            except ImportError:
                print_status(f"✗ Python包 {package} 缺失", "ERROR")
                success = False
        
        # 3. 检查核心文件
        for file in self.core_files:
            file_path = self.work_dir / file
            if file_path.exists():
                print_status(f"✓ 核心文件 {file} 存在", "SUCCESS")
            else:
                print_status(f"✗ 核心文件 {file} 缺失", "ERROR")
                success = False
        
        # 4. 检查配置文件
        config_path = self.work_dir / "configs" / "mcp_config.linux.json"
        if config_path.exists():
            print_status("✓ 配置文件存在", "SUCCESS")
        else:
            print_status("⚠ 配置文件不存在", "WARNING")
        
        # 5. 检查端口占用
        if self._check_port_available(self.kb_port):
            print_status(f"✓ 端口 {self.kb_port} 可用", "SUCCESS")
        else:
            print_status(f"⚠ 端口 {self.kb_port} 被占用", "WARNING")
        
        return success
    
    def start_services(self) -> bool:
        """启动服务"""
        print_status("=== 启动服务 ===", "INFO")
        
        # 停止现有服务
        self._stop_service("knowledge_base_http")
        
        # 启动知识库HTTP服务
        return self._start_knowledge_base()
    
    def test_system(self) -> bool:
        """测试系统功能"""
        print_status("=== 系统测试 ===", "INFO")
        
        try:
            # 运行统一测试脚本
            import subprocess
            print_status("启动统一测试套件...", "INFO")
            
            result = subprocess.run([
                sys.executable, "test_embedding_memory.py", "all", "--verbose"
            ], timeout=600)  # 10分钟超时
            
            if result.returncode == 0:
                print_status("✓ 所有测试通过!", "SUCCESS")
                return True
            else:
                print_status("部分测试失败，请查看详细输出", "WARNING")
                return False
                
        except subprocess.TimeoutExpired:
            print_status("测试超时，可能系统响应较慢", "WARNING")
            return False
        except Exception as e:
            print_status(f"测试执行异常: {e}", "ERROR")
            # 回退到基本测试
            return self._run_basic_tests()
    
    def _run_basic_tests(self) -> bool:
        """运行基本测试（回退方案）"""
        print_status("运行基本功能测试...", "INFO")
        
        # 1. 测试服务可用性
        if not self._test_service_health():
            return False
        
        # 2. 测试基本API
        if not self._test_basic_api():
            return False
        
        # 3. 测试记忆存储
        if not self._test_memory_storage():
            return False
        
        # 4. 测试记忆检索
        if not self._test_memory_retrieval():
            return False
        
        print_status("✓ 基本测试通过!", "SUCCESS")
        return True
    
    def deploy_system(self) -> bool:
        """一键部署系统"""
        print_status("=== 一键部署 ===", "INFO")
        
        # 1. 环境检查
        if not self.check_environment():
            print_status("环境检查失败，尝试自动修复...", "WARNING")
            if not self._auto_fix_environment():
                print_status("自动修复失败，请手动解决环境问题", "ERROR")
                return False
        
        # 2. 启动服务
        if not self.start_services():
            print_status("服务启动失败", "ERROR")
            return False
        
        # 3. 测试系统
        if not self.test_system():
            print_status("系统测试失败", "ERROR")
            return False
        
        print_status("✓ 部署成功!", "SUCCESS")
        self._show_usage_info()
        return True
    
    def stop_services(self) -> bool:
        """停止服务"""
        print_status("=== 停止服务 ===", "INFO")
        return self._stop_service("knowledge_base_http")
    
    def show_status(self) -> bool:
        """显示服务状态"""
        print_status("=== 服务状态 ===", "INFO")
        
        # 检查进程状态
        pid_file = self.pid_dir / "knowledge_base_http.pid"
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # 检查进程是否存在
                try:
                    os.kill(pid, 0)  # 发送信号0检查进程
                    print_status(f"✓ 知识库服务运行中 (PID: {pid})", "SUCCESS")
                    
                    # 检查HTTP服务
                    if self._test_service_health():
                        print_status(f"✓ HTTP服务正常 ({self.kb_url})", "SUCCESS")
                    else:
                        print_status("⚠ HTTP服务不响应", "WARNING")
                        
                except ProcessLookupError:
                    print_status("✗ 进程已停止", "ERROR")
                    pid_file.unlink()  # 清理过期的PID文件
                    
            except Exception as e:
                print_status(f"✗ 状态检查异常: {e}", "ERROR")
        else:
            print_status("✗ 服务未运行", "ERROR")
        
        return True
    
    def _check_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) != 0
        except Exception:
            return False
    
    def _start_knowledge_base(self) -> bool:
        """启动知识库服务"""
        print_status("启动知识库HTTP服务...", "INFO")
        
        # 设置环境变量
        env = os.environ.copy()
        env.update({
            "KB_PORT": str(self.kb_port),
            "PYTHONPATH": str(self.work_dir)
        })
        
        # 启动服务
        log_file = self.log_dir / "knowledge_base_http.log"
        pid_file = self.pid_dir / "knowledge_base_http.pid"
        
        try:
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    [sys.executable, "knowledge_base_service.py"],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=self.work_dir
                )
            
            # 保存PID
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            
            print_status(f"服务启动中 (PID: {process.pid})", "INFO")
            
            # 等待服务启动
            for i in range(30):  # 最多等待30秒
                if self._test_service_health():
                    print_status("✓ 知识库服务启动成功", "SUCCESS")
                    return True
                time.sleep(1)
            
            print_status("✗ 服务启动超时", "ERROR")
            return False
            
        except Exception as e:
            print_status(f"✗ 启动失败: {e}", "ERROR")
            return False
    
    def _stop_service(self, service_name: str) -> bool:
        """停止服务"""
        pid_file = self.pid_dir / f"{service_name}.pid"
        
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                os.kill(pid, 15)  # 发送SIGTERM
                time.sleep(2)
                
                try:
                    os.kill(pid, 0)  # 检查进程是否还存在
                    os.kill(pid, 9)  # 强制终止
                    print_status(f"强制停止 {service_name}", "WARNING")
                except ProcessLookupError:
                    pass
                
                pid_file.unlink()
                print_status(f"✓ {service_name} 已停止", "SUCCESS")
                return True
                
            except Exception as e:
                print_status(f"停止服务异常: {e}", "ERROR")
                if pid_file.exists():
                    pid_file.unlink()
        
        return True
    
    def _test_service_health(self) -> bool:
        """测试服务健康状态"""
        try:
            response = requests.get(f"{self.kb_url}/docs", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _test_basic_api(self) -> bool:
        """测试基本API功能"""
        try:
            response = requests.get(f"{self.kb_url}/stats", timeout=5)
            if response.status_code == 200:
                print_status("✓ 基本API测试通过", "SUCCESS")
                return True
        except Exception:
            pass
        
        print_status("✗ 基本API测试失败", "ERROR")
        return False
    
    def _test_memory_storage(self) -> bool:
        """测试记忆存储功能"""
        try:
            test_data = {
                "content": f"测试记忆存储 - {datetime.now().isoformat()}",
                "tags": ["test", "memory", "embedding"],
                "metadata": {
                    "user_id": "test_user",
                    "memory_type": "test",
                    "importance": 5.0,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                f"{self.kb_url}/add",
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print_status("✓ 记忆存储测试通过", "SUCCESS")
                    return True
            
        except Exception as e:
            print_status(f"记忆存储测试异常: {e}", "ERROR")
        
        print_status("✗ 记忆存储测试失败", "ERROR")
        return False
    
    def _test_memory_retrieval(self) -> bool:
        """测试记忆检索功能"""
        try:
            search_data = {
                "query": "测试记忆",
                "tags": ["test"],
                "top_k": 3,
                "metadata_filter": {"user_id": "test_user"}
            }
            
            response = requests.post(
                f"{self.kb_url}/search",
                json=search_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print_status("✓ 记忆检索测试通过", "SUCCESS")
                    return True
            
        except Exception as e:
            print_status(f"记忆检索测试异常: {e}", "ERROR")
        
        print_status("✗ 记忆检索测试失败", "ERROR")
        return False
    
    def _auto_fix_environment(self) -> bool:
        """自动修复环境"""
        print_status("尝试自动修复环境...", "INFO")
        
        try:
            # 安装缺失的Python包
            required_packages = [
                "fastapi", "uvicorn", "numpy", "requests", "python-multipart"
            ]
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    print_status(f"安装 {package}...", "INFO")
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", package
                    ])
            
            print_status("✓ 环境修复完成", "SUCCESS")
            return True
            
        except Exception as e:
            print_status(f"自动修复失败: {e}", "ERROR")
            return False
    
    def _show_usage_info(self):
        """显示使用信息"""
        print("\n" + "="*60)
        print_status("MCP Embedding记忆库部署成功!", "SUCCESS")
        print("="*60)
        print(f"🌐 知识库服务: {self.kb_url}")
        print(f"📖 API文档: {self.kb_url}/docs")
        print(f"📊 服务状态: {self.kb_url}/stats")
        print("\n📋 管理命令:")
        print("  python mcp_memory_manager.py status   # 查看状态")
        print("  python mcp_memory_manager.py test     # 测试功能")
        print("  python mcp_memory_manager.py stop     # 停止服务")
        print("\n📂 重要文件:")
        print(f"  日志文件: {self.log_dir}/knowledge_base_http.log")
        print(f"  进程文件: {self.pid_dir}/knowledge_base_http.pid")
        print("="*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="MCP Embedding记忆库管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python mcp_memory_manager.py check     # 检查环境
  python mcp_memory_manager.py deploy    # 一键部署
  python mcp_memory_manager.py start     # 启动服务
  python mcp_memory_manager.py test      # 测试功能
  python mcp_memory_manager.py status    # 查看状态
  python mcp_memory_manager.py stop      # 停止服务
        """
    )
    
    parser.add_argument(
        "action",
        choices=["check", "start", "stop", "test", "deploy", "status"],
        help="要执行的操作"
    )
    
    args = parser.parse_args()
    
    manager = MCPMemoryManager()
    
    # 执行对应的操作
    if args.action == "check":
        success = manager.check_environment()
    elif args.action == "start":
        success = manager.start_services()
    elif args.action == "stop":
        success = manager.stop_services()
    elif args.action == "test":
        success = manager.test_system()
    elif args.action == "deploy":
        success = manager.deploy_system()
    elif args.action == "status":
        success = manager.show_status()
    else:
        parser.print_help()
        return
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
