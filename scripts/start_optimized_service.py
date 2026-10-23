#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动优化的AgentScope多智能体编程工作流服务
演示深度AgentScope集成和Augment真实集成
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentscope_integration.main_optimized import OptimizedAgentScopeService


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.service = None
        self.logger = logging.getLogger(__name__)
        
    async def start_service(self, host: str = "localhost", port: int = 8000, config_path: str = None):
        """启动服务"""
        try:
            # 设置信号处理
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # 创建服务实例
            config_path = config_path or "config/system_config.json"
            self.service = OptimizedAgentScopeService(config_path)
            
            self.logger.info("🚀 启动优化的AgentScope多智能体编程工作流服务...")
            self.logger.info(f"📍 服务地址: http://{host}:{port}")
            self.logger.info("🔧 新功能特性:")
            self.logger.info("   ✅ 深度AgentScope集成 (ReActAgent, MsgHub, Pipeline)")
            self.logger.info("   ✅ 真实Augment集成 (自然语言指令处理)")
            self.logger.info("   ✅ 智能工作流管理 (顺序、并行、混合)")
            self.logger.info("   ✅ 长期记忆和性能追踪")
            self.logger.info("   ✅ 事件驱动架构")
            
            # 启动服务
            await self.service.start_server(host, port)
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在关闭服务...")
            await self._shutdown()
        except Exception as e:
            self.logger.error(f"服务启动失败: {e}")
            await self._shutdown()
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，准备关闭服务...")
        asyncio.create_task(self._shutdown())
    
    async def _shutdown(self):
        """关闭服务"""
        if self.service:
            await self.service.shutdown()
        self.logger.info("服务已关闭")


async def demo_optimized_features():
    """演示优化功能"""
    print("\n" + "="*80)
    print("🎯 AgentScope多智能体编程工作流 - 优化架构演示")
    print("="*80)
    
    print("\n📋 主要优化特性:")
    
    print("\n1. 🧠 深度AgentScope集成:")
    print("   • 智能体继承自ReActAgent，充分利用AgentScope能力")
    print("   • 使用InMemoryMemory和LongTermMemory进行记忆管理")
    print("   • 集成Toolkit进行工具管理")
    print("   • 使用Session进行会话管理")
    print("   • 集成trace_toolkit进行性能追踪")
    
    print("\n2. 🔄 AgentScope Pipeline工作流:")
    print("   • 使用MsgHub进行消息管理")
    print("   • 支持sequential_pipeline顺序执行")
    print("   • 支持FanoutPipeline并行执行")
    print("   • 支持混合工作流(先顺序后并行)")
    
    print("\n3. 🎤 真实Augment集成:")
    print("   • VS Code插件实时监听Augment活动")
    print("   • 自然语言指令解析和理解")
    print("   • 自动创建AgentScope任务")
    print("   • 支持多种事件类型(代码分析、安全扫描、质量检查等)")
    
    print("\n4. 📊 性能和监控:")
    print("   • 智能体性能追踪")
    print("   • 长期记忆存储分析结果")
    print("   • 事件驱动架构")
    print("   • 实时状态监控")
    
    print("\n5. 🔧 向后兼容:")
    print("   • 保持现有API接口兼容")
    print("   • 渐进式迁移策略")
    print("   • 配置自动迁移")
    
    print("\n" + "="*80)
    print("🌟 准备启动优化服务...")
    print("="*80)


async def test_optimized_integration():
    """测试优化集成功能"""
    print("\n🧪 运行优化集成测试...")
    
    try:
        # 导入测试模块
        from tests.test_optimized_integration import run_integration_tests
        
        # 运行测试
        await run_integration_tests()
        
        print("✅ 优化集成测试通过！")
        return True
        
    except ImportError:
        print("⚠️ 测试模块未找到，跳过集成测试")
        return True
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="启动优化的AgentScope多智能体编程工作流服务")
    parser.add_argument("--host", default="localhost", help="服务主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--test", action="store_true", help="运行集成测试")
    parser.add_argument("--demo", action="store_true", help="显示功能演示")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 显示演示信息
    if args.demo:
        await demo_optimized_features()
    
    # 运行测试
    if args.test:
        test_passed = await test_optimized_integration()
        if not test_passed:
            print("❌ 测试失败，建议修复问题后再启动服务")
            sys.exit(1)
    
    # 启动服务
    service_manager = ServiceManager()
    await service_manager.start_service(
        host=args.host,
        port=args.port,
        config_path=args.config
    )


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              AgentScope多智能体编程工作流                      ║
    ║                     优化架构版本                              ║
    ║                                                              ║
    ║  🚀 深度AgentScope集成                                        ║
    ║  🎤 真实Augment集成                                           ║
    ║  🔄 智能工作流管理                                            ║
    ║  📊 性能追踪和监控                                            ║
    ║  🔧 向后兼容支持                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)
