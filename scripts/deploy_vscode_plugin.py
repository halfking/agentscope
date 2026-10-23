#!/usr/bin/env python3
"""
AgentScope VS Code插件部署脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 命令执行失败: {cmd}")
            print(f"错误输出: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ 命令执行异常: {e}")
        return False

def check_prerequisites():
    """检查部署前提条件"""
    print("🔍 检查部署前提条件...")
    
    # 检查Node.js
    if not run_command("node --version"):
        print("❌ Node.js未安装，请先安装Node.js")
        return False
    
    # 检查npm
    if not run_command("npm --version"):
        print("❌ npm未安装，请先安装npm")
        return False
    
    # 检查VS Code
    if not run_command("code --version"):
        print("⚠️  VS Code未在PATH中，请确保VS Code已安装")
    
    print("✅ 前提条件检查完成")
    return True

def deploy_plugin():
    """部署VS Code插件"""
    print("🚀 开始部署AgentScope VS Code插件...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    vscode_dir = project_root / "vscode-extension"
    
    if not vscode_dir.exists():
        print("❌ VS Code插件目录不存在")
        return False
    
    print(f"📁 插件目录: {vscode_dir}")
    
    # 检查插件包是否存在
    vsix_files = list(vscode_dir.glob("*.vsix"))
    if not vsix_files:
        print("❌ 未找到.vsix插件包，请先运行打包命令")
        return False
    
    vsix_file = vsix_files[0]  # 使用第一个找到的.vsix文件
    print(f"📦 找到插件包: {vsix_file.name}")
    
    # 安装插件
    print("📥 安装VS Code插件...")
    install_cmd = f"code --install-extension {vsix_file}"
    if not run_command(install_cmd, cwd=vscode_dir):
        print("❌ 插件安装失败")
        return False
    
    print("✅ 插件安装成功")
    
    # 验证安装
    print("🔍 验证插件安装...")
    list_cmd = "code --list-extensions"
    result = subprocess.run(list_cmd, shell=True, capture_output=True, text=True)
    if "agentscope-multi-agent-workflow" in result.stdout:
        print("✅ 插件验证成功")
    else:
        print("⚠️  插件验证失败，但可能已正确安装")
    
    return True

def start_backend_service():
    """启动后端服务"""
    print("🔧 启动AgentScope后端服务...")
    
    project_root = Path(__file__).parent.parent
    
    # 检查环境变量
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ 找到环境配置文件")
    else:
        print("⚠️  未找到.env文件，使用默认配置")
    
    # 启动优化服务
    start_script = project_root / "scripts" / "start_optimized_service.py"
    if start_script.exists():
        print("🚀 启动优化服务...")
        if run_command(f"python {start_script} --demo", cwd=project_root):
            print("✅ 后端服务启动成功")
            return True
        else:
            print("❌ 后端服务启动失败")
            return False
    else:
        print("⚠️  未找到启动脚本，请手动启动后端服务")
        return True

def create_desktop_shortcut():
    """创建桌面快捷方式"""
    print("🔗 创建桌面快捷方式...")
    
    try:
        # 获取桌面路径
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "桌面"  # 中文系统
        
        if desktop.exists():
            shortcut_content = """#!/bin/bash
# AgentScope VS Code插件启动脚本
echo "🚀 启动AgentScope多智能体编程工作流..."
code --new-window
echo "✅ VS Code已启动，请在扩展面板中查找AgentScope插件"
"""
            shortcut_path = desktop / "AgentScope-VSCode.sh"
            with open(shortcut_path, 'w') as f:
                f.write(shortcut_content)
            
            # 设置执行权限
            os.chmod(shortcut_path, 0o755)
            print(f"✅ 桌面快捷方式已创建: {shortcut_path}")
        else:
            print("⚠️  未找到桌面目录，跳过快捷方式创建")
    except Exception as e:
        print(f"⚠️  创建桌面快捷方式失败: {e}")

def show_usage_instructions():
    """显示使用说明"""
    print("\n" + "="*60)
    print("🎉 AgentScope VS Code插件部署完成！")
    print("="*60)
    print()
    print("📋 使用说明:")
    print("1. 打开VS Code")
    print("2. 在活动栏中找到AgentScope图标（机器人图标）")
    print("3. 点击图标打开AgentScope面板")
    print("4. 使用以下功能:")
    print("   • 启用Augment集成: Ctrl+Shift+U (Mac: Cmd+Shift+U)")
    print("   • 显示仪表板: Ctrl+Shift+A (Mac: Cmd+Shift+A)")
    print("   • 项目分析: Ctrl+Shift+P (Mac: Cmd+Shift+P)")
    print("   • 质量检查: Ctrl+Shift+Q (Mac: Cmd+Shift+Q)")
    print("   • 安全扫描: Ctrl+Shift+S (Mac: Cmd+Shift+S)")
    print()
    print("🔧 配置说明:")
    print("• 在VS Code设置中搜索'agentscope'进行配置")
    print("• 默认使用硅基流动API (deepseek-ai/deepseek-coder)")
    print("• 支持自然语言指令处理")
    print()
    print("📚 更多信息:")
    print("• 用户指南: docs/optimized_user_guide.md")
    print("• 迁移指南: docs/migration_guide.md")
    print("• 项目状态: PROJECT_STATUS_OPTIMIZED.md")
    print()
    print("🆘 如遇问题:")
    print("• 检查后端服务是否运行")
    print("• 查看VS Code开发者控制台")
    print("• 重启VS Code和后端服务")
    print("="*60)

def main():
    """主函数"""
    print("🚀 AgentScope VS Code插件部署工具")
    print("="*50)
    
    # 检查前提条件
    if not check_prerequisites():
        sys.exit(1)
    
    # 部署插件
    if not deploy_plugin():
        sys.exit(1)
    
    # 启动后端服务
    start_backend_service()
    
    # 创建桌面快捷方式
    create_desktop_shortcut()
    
    # 显示使用说明
    show_usage_instructions()
    
    print("\n🎉 部署完成！请打开VS Code开始使用AgentScope插件。")

if __name__ == "__main__":
    main()
