#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope多智能体编程工作流 - 生产环境部署脚本
"""

import os
import sys
import json
import shutil
import subprocess
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class ProductionDeployer:
    """生产环境部署器"""
    
    def __init__(self, config_path: str = "config/production_config.json"):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.deployment_log = []
        
        # 部署配置
        self.config = self.load_deployment_config()
        
        # 部署路径
        self.project_root = Path(__file__).parent.parent
        self.deployment_dir = Path(self.config.get("deployment_dir", "/opt/agentscope"))
        self.backup_dir = Path(self.config.get("backup_dir", "/opt/agentscope/backups"))
        self.log_dir = Path(self.config.get("log_dir", "/var/log/agentscope"))
        
    def load_deployment_config(self) -> Dict[str, Any]:
        """加载部署配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 创建默认配置
            default_config = {
                "deployment_dir": "/opt/agentscope",
                "backup_dir": "/opt/agentscope/backups",
                "log_dir": "/var/log/agentscope",
                "service_name": "agentscope",
                "service_user": "agentscope",
                "service_group": "agentscope",
                "python_executable": "/usr/bin/python3",
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 4,
                "environment": "production",
                "ssl": {
                    "enabled": False,
                    "cert_file": "/etc/ssl/certs/agentscope.crt",
                    "key_file": "/etc/ssl/private/agentscope.key"
                },
                "monitoring": {
                    "enabled": True,
                    "metrics_port": 9090,
                    "health_check_interval": 30
                },
                "backup": {
                    "enabled": True,
                    "retention_days": 30,
                    "schedule": "0 2 * * *"  # 每天凌晨2点
                }
            }
            
            # 保存默认配置
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    
    def log_step(self, message: str, success: bool = True):
        """记录部署步骤"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "✅" if success else "❌"
        log_entry = f"{timestamp} {status} {message}"
        
        print(log_entry)
        self.deployment_log.append(log_entry)
        self.logger.info(message)
    
    async def deploy(self):
        """执行完整部署"""
        print("🚀 开始生产环境部署...")
        print(f"📅 部署时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 目标目录: {self.deployment_dir}")
        
        try:
            # 1. 预检查
            await self.pre_deployment_checks()
            
            # 2. 创建备份
            await self.create_backup()
            
            # 3. 准备环境
            await self.prepare_environment()
            
            # 4. 部署代码
            await self.deploy_code()
            
            # 5. 安装依赖
            await self.install_dependencies()
            
            # 6. 配置服务
            await self.configure_service()
            
            # 7. 设置监控
            await self.setup_monitoring()
            
            # 8. 启动服务
            await self.start_service()
            
            # 9. 验证部署
            await self.verify_deployment()
            
            # 10. 清理
            await self.cleanup()
            
            self.log_step("生产环境部署完成！")
            await self.generate_deployment_report()
            
        except Exception as e:
            self.log_step(f"部署失败: {e}", False)
            await self.rollback()
            raise
    
    async def pre_deployment_checks(self):
        """部署前检查"""
        self.log_step("执行部署前检查...")
        
        # 检查系统要求
        checks = [
            ("Python版本", self.check_python_version),
            ("磁盘空间", self.check_disk_space),
            ("内存", self.check_memory),
            ("网络端口", self.check_ports),
            ("权限", self.check_permissions),
            ("依赖服务", self.check_dependencies)
        ]
        
        for check_name, check_func in checks:
            try:
                await check_func()
                self.log_step(f"  ✓ {check_name}检查通过")
            except Exception as e:
                self.log_step(f"  ✗ {check_name}检查失败: {e}", False)
                raise
    
    async def check_python_version(self):
        """检查Python版本"""
        result = subprocess.run([
            self.config["python_executable"], "--version"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception("Python不可用")
        
        version = result.stdout.strip()
        if not version.startswith("Python 3."):
            raise Exception(f"需要Python 3.x，当前版本: {version}")
    
    async def check_disk_space(self):
        """检查磁盘空间"""
        stat = shutil.disk_usage(self.deployment_dir.parent)
        free_gb = stat.free / (1024**3)
        
        if free_gb < 5:  # 至少需要5GB空间
            raise Exception(f"磁盘空间不足，可用: {free_gb:.1f}GB")
    
    async def check_memory(self):
        """检查内存"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            for line in meminfo.split('\n'):
                if line.startswith('MemAvailable:'):
                    available_kb = int(line.split()[1])
                    available_gb = available_kb / (1024**2)
                    
                    if available_gb < 2:  # 至少需要2GB内存
                        raise Exception(f"内存不足，可用: {available_gb:.1f}GB")
                    break
        except Exception as e:
            self.log_step(f"内存检查警告: {e}")
    
    async def check_ports(self):
        """检查端口可用性"""
        import socket
        
        ports_to_check = [
            self.config["port"],
            self.config.get("monitoring", {}).get("metrics_port", 9090)
        ]
        
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    raise Exception(f"端口 {port} 已被占用")
            finally:
                sock.close()
    
    async def check_permissions(self):
        """检查权限"""
        # 检查部署目录写权限
        test_file = self.deployment_dir / "test_write"
        try:
            os.makedirs(self.deployment_dir, exist_ok=True)
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            raise Exception(f"部署目录权限不足: {e}")
    
    async def check_dependencies(self):
        """检查依赖服务"""
        # 检查systemd
        result = subprocess.run(["systemctl", "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("systemd不可用")
    
    async def create_backup(self):
        """创建备份"""
        if not self.deployment_dir.exists():
            self.log_step("首次部署，跳过备份")
            return
        
        self.log_step("创建当前版本备份...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 复制当前部署
        shutil.copytree(self.deployment_dir, backup_path)
        
        self.log_step(f"备份已创建: {backup_path}")
        
        # 清理旧备份
        await self.cleanup_old_backups()
    
    async def cleanup_old_backups(self):
        """清理旧备份"""
        retention_days = self.config.get("backup", {}).get("retention_days", 30)
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
        
        for backup_dir in self.backup_dir.glob("backup_*"):
            if backup_dir.stat().st_mtime < cutoff_time:
                shutil.rmtree(backup_dir)
                self.log_step(f"清理旧备份: {backup_dir}")
    
    async def prepare_environment(self):
        """准备环境"""
        self.log_step("准备部署环境...")
        
        # 创建目录结构
        directories = [
            self.deployment_dir,
            self.deployment_dir / "config",
            self.deployment_dir / "logs",
            self.deployment_dir / "data",
            self.log_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.log_step(f"  创建目录: {directory}")
        
        # 创建服务用户（如果不存在）
        await self.create_service_user()
    
    async def create_service_user(self):
        """创建服务用户"""
        user = self.config["service_user"]
        group = self.config["service_group"]
        
        # 检查用户是否存在
        result = subprocess.run(["id", user], capture_output=True)
        if result.returncode != 0:
            # 创建组
            subprocess.run(["groupadd", "-r", group], check=False)
            
            # 创建用户
            subprocess.run([
                "useradd", "-r", "-g", group, "-d", str(self.deployment_dir),
                "-s", "/bin/false", user
            ], check=True)
            
            self.log_step(f"创建服务用户: {user}")
    
    async def deploy_code(self):
        """部署代码"""
        self.log_step("部署应用代码...")
        
        # 复制代码文件
        source_dirs = [
            "agentscope_integration",
            "vscode-extension",
            "scripts",
            "config",
            "tests"
        ]
        
        for source_dir in source_dirs:
            source_path = self.project_root / source_dir
            target_path = self.deployment_dir / source_dir
            
            if source_path.exists():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
                self.log_step(f"  部署: {source_dir}")
        
        # 复制重要文件
        important_files = [
            "requirements.txt",
            "package.json",
            "README.md"
        ]
        
        for file_name in important_files:
            source_file = self.project_root / file_name
            target_file = self.deployment_dir / file_name
            
            if source_file.exists():
                shutil.copy2(source_file, target_file)
                self.log_step(f"  部署文件: {file_name}")
    
    async def install_dependencies(self):
        """安装依赖"""
        self.log_step("安装Python依赖...")
        
        # 创建虚拟环境
        venv_path = self.deployment_dir / "venv"
        subprocess.run([
            self.config["python_executable"], "-m", "venv", str(venv_path)
        ], check=True)
        
        # 安装依赖
        pip_path = venv_path / "bin" / "pip"
        requirements_file = self.deployment_dir / "requirements.txt"
        
        if requirements_file.exists():
            subprocess.run([
                str(pip_path), "install", "-r", str(requirements_file)
            ], check=True)
        
        # 安装额外的生产依赖
        production_packages = [
            "uvicorn[standard]",
            "gunicorn",
            "prometheus-client",
            "psutil"
        ]
        
        subprocess.run([
            str(pip_path), "install"
        ] + production_packages, check=True)
        
        self.log_step("Python依赖安装完成")
    
    async def configure_service(self):
        """配置系统服务"""
        self.log_step("配置systemd服务...")
        
        # 生成服务配置
        service_config = self.generate_service_config()
        
        # 写入服务文件
        service_file = f"/etc/systemd/system/{self.config['service_name']}.service"
        with open(service_file, 'w') as f:
            f.write(service_config)
        
        # 重新加载systemd
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        
        # 启用服务
        subprocess.run([
            "systemctl", "enable", self.config['service_name']
        ], check=True)
        
        self.log_step("systemd服务配置完成")
    
    def generate_service_config(self) -> str:
        """生成systemd服务配置"""
        python_path = self.deployment_dir / "venv" / "bin" / "python"
        script_path = self.deployment_dir / "scripts" / "start_optimized_service.py"
        
        return f"""[Unit]
Description=AgentScope Multi-Agent Programming Workflow
After=network.target

[Service]
Type=simple
User={self.config['service_user']}
Group={self.config['service_group']}
WorkingDirectory={self.deployment_dir}
Environment=PYTHONPATH={self.deployment_dir}
Environment=AGENTSCOPE_CONFIG_PATH={self.deployment_dir}/config/production_config.json
ExecStart={python_path} {script_path} --host {self.config['host']} --port {self.config['port']}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=agentscope

[Install]
WantedBy=multi-user.target
"""
    
    async def setup_monitoring(self):
        """设置监控"""
        if not self.config.get("monitoring", {}).get("enabled", False):
            self.log_step("跳过监控设置")
            return
        
        self.log_step("设置监控...")
        
        # 创建监控配置
        monitoring_config = {
            "metrics_port": self.config["monitoring"]["metrics_port"],
            "health_check_interval": self.config["monitoring"]["health_check_interval"]
        }
        
        config_file = self.deployment_dir / "config" / "monitoring.json"
        with open(config_file, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        self.log_step("监控配置完成")
    
    async def start_service(self):
        """启动服务"""
        self.log_step("启动AgentScope服务...")
        
        # 设置文件权限
        user = self.config["service_user"]
        group = self.config["service_group"]
        
        subprocess.run([
            "chown", "-R", f"{user}:{group}", str(self.deployment_dir)
        ], check=True)
        
        # 启动服务
        subprocess.run([
            "systemctl", "start", self.config['service_name']
        ], check=True)
        
        # 等待服务启动
        await asyncio.sleep(5)
        
        self.log_step("服务启动完成")
    
    async def verify_deployment(self):
        """验证部署"""
        self.log_step("验证部署...")
        
        # 检查服务状态
        result = subprocess.run([
            "systemctl", "is-active", self.config['service_name']
        ], capture_output=True, text=True)
        
        if result.stdout.strip() != "active":
            raise Exception("服务未正常启动")
        
        # 检查HTTP端点
        import urllib.request
        import urllib.error
        
        url = f"http://{self.config['host']}:{self.config['port']}/health"
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"健康检查失败，状态码: {response.status}")
        except urllib.error.URLError as e:
            raise Exception(f"无法连接到服务: {e}")
        
        self.log_step("部署验证通过")
    
    async def cleanup(self):
        """清理临时文件"""
        self.log_step("清理临时文件...")
        
        # 清理可能的临时文件
        temp_patterns = [
            "*.pyc",
            "__pycache__",
            "*.tmp",
            ".DS_Store"
        ]
        
        for pattern in temp_patterns:
            for temp_file in self.deployment_dir.rglob(pattern):
                if temp_file.is_file():
                    temp_file.unlink()
                elif temp_file.is_dir():
                    shutil.rmtree(temp_file)
        
        self.log_step("清理完成")
    
    async def rollback(self):
        """回滚到上一个版本"""
        self.log_step("执行回滚...")
        
        # 查找最新备份
        backups = sorted(self.backup_dir.glob("backup_*"), reverse=True)
        
        if not backups:
            self.log_step("没有可用的备份，无法回滚", False)
            return
        
        latest_backup = backups[0]
        
        # 停止服务
        subprocess.run([
            "systemctl", "stop", self.config['service_name']
        ], check=False)
        
        # 恢复备份
        if self.deployment_dir.exists():
            shutil.rmtree(self.deployment_dir)
        
        shutil.copytree(latest_backup, self.deployment_dir)
        
        # 重启服务
        subprocess.run([
            "systemctl", "start", self.config['service_name']
        ], check=False)
        
        self.log_step(f"已回滚到: {latest_backup}")
    
    async def generate_deployment_report(self):
        """生成部署报告"""
        report = {
            "deployment_time": datetime.now().isoformat(),
            "deployment_dir": str(self.deployment_dir),
            "config": self.config,
            "log": self.deployment_log,
            "status": "success"
        }
        
        report_file = self.deployment_dir / "deployment_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 部署报告已保存到: {report_file}")
        print("\n🎉 生产环境部署成功！")
        print(f"🌐 服务地址: http://{self.config['host']}:{self.config['port']}")
        print(f"📊 监控地址: http://{self.config['host']}:{self.config.get('monitoring', {}).get('metrics_port', 9090)}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentScope生产环境部署")
    parser.add_argument("--config", default="config/production_config.json", help="部署配置文件")
    parser.add_argument("--dry-run", action="store_true", help="模拟部署（不执行实际操作）")
    parser.add_argument("--rollback", action="store_true", help="回滚到上一个版本")
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    deployer = ProductionDeployer(args.config)
    
    try:
        if args.rollback:
            await deployer.rollback()
        elif args.dry_run:
            print("🧪 模拟部署模式（不执行实际操作）")
            # 这里可以添加模拟部署逻辑
        else:
            await deployer.deploy()
    
    except KeyboardInterrupt:
        print("\n⚠️ 部署被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 部署失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
