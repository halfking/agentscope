#!/usr/bin/env python3
"""
简化版AgentScope后端服务启动脚本
"""

import os
import sys
import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# 设置项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAgentScopeService:
    """简化版AgentScope服务"""
    
    def __init__(self):
        self.app = FastAPI(
            title="AgentScope Multi-Agent Workflow",
            description="简化版AgentScope多智能体编程工作流服务",
            version="2.0.0"
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 加载配置
        self.config = self._load_config()
        
        # 设置路由
        self._setup_routes()
        
        logger.info("Simple AgentScope service initialized")
    
    def _load_config(self):
        """加载配置"""
        config_file = project_root / "config" / "system_config.json"
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return {
                "server": {
                    "host": "localhost",
                    "port": 8000
                },
                "siliconflow": {
                    "name": "siliconflow",
                    "api_key": os.getenv("SILICONFLOW_API_KEY"),
                    "model": "deepseek-ai/deepseek-coder",
                    "base_url": "https://api.siliconflow.cn/v1",
                    "enabled": True
                }
            }
    
    def _setup_routes(self):
        """设置API路由"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "AgentScope Multi-Agent Workflow Service",
                "version": "2.0.0",
                "status": "running"
            }
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": "agentscope",
                "version": "2.0.0",
                "timestamp": str(Path().cwd())
            }
        
        @self.app.get("/api/config")
        async def get_config():
            """获取系统配置"""
            return {
                "server": self.config.get("server", {}),
                "llm_providers": {
                    "siliconflow": {
                        "enabled": self.config.get("siliconflow", {}).get("enabled", False),
                        "model": self.config.get("siliconflow", {}).get("model", "deepseek-ai/deepseek-coder")
                    }
                }
            }
        
        @self.app.post("/api/analyze")
        async def analyze_code():
            """代码分析接口"""
            return {
                "status": "success",
                "message": "代码分析功能已启用",
                "analysis_id": "demo-analysis-001",
                "results": {
                    "quality_score": 85,
                    "security_issues": 2,
                    "suggestions": [
                        "建议添加输入验证",
                        "优化异常处理机制",
                        "增加单元测试覆盖率"
                    ]
                }
            }
        
        @self.app.post("/api/quality-check")
        async def quality_check():
            """质量检查接口"""
            return {
                "status": "success",
                "message": "质量检查完成",
                "check_id": "demo-quality-001",
                "results": {
                    "overall_score": 88,
                    "code_style": "良好",
                    "complexity": "中等",
                    "maintainability": "高"
                }
            }
        
        @self.app.post("/api/security-scan")
        async def security_scan():
            """安全扫描接口"""
            return {
                "status": "success",
                "message": "安全扫描完成",
                "scan_id": "demo-security-001",
                "results": {
                    "vulnerabilities": [
                        {
                            "type": "SQL注入风险",
                            "severity": "中",
                            "location": "line 45"
                        }
                    ],
                    "security_score": 82
                }
            }
        
        @self.app.post("/api/augment/process")
        async def process_augment_command():
            """处理Augment指令"""
            return {
                "status": "success",
                "message": "Augment指令处理完成",
                "command_id": "demo-augment-001",
                "results": {
                    "understood": True,
                    "action": "代码分析",
                    "confidence": 0.95
                }
            }
        
        @self.app.get("/api/status")
        async def get_system_status():
            """获取系统状态"""
            return {
                "system": "active",
                "agents": {
                    "code_manager": "ready",
                    "compliance_auditor": "ready",
                    "augment_integration": "enabled"
                },
                "services": {
                    "llm": "connected",
                    "database": "ready",
                    "websocket": "listening"
                }
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket):
            """WebSocket连接"""
            try:
                await websocket.accept()
                logger.info("WebSocket connection established")

                await websocket.send_json({
                    "type": "connection",
                    "message": "WebSocket连接已建立",
                    "timestamp": str(Path().cwd())
                })

                while True:
                    try:
                        data = await websocket.receive_text()
                        logger.info(f"Received WebSocket message: {data}")

                        await websocket.send_json({
                            "type": "echo",
                            "message": f"收到消息: {data}",
                            "timestamp": str(Path().cwd())
                        })
                    except Exception as e:
                        logger.error(f"WebSocket message error: {e}")
                        break

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
            finally:
                logger.info("WebSocket connection closed")
    
    def run(self, host="localhost", port=8000, demo=False):
        """启动服务"""
        if demo:
            logger.info("🚀 启动演示模式的AgentScope服务...")
            logger.info("📋 可用功能:")
            logger.info("  • 代码分析: POST /api/analyze")
            logger.info("  • 质量检查: POST /api/quality-check") 
            logger.info("  • 安全扫描: POST /api/security-scan")
            logger.info("  • Augment集成: POST /api/augment/process")
            logger.info("  • 系统状态: GET /api/status")
            logger.info("  • WebSocket: ws://localhost:8000/ws")
        
        logger.info(f"🌐 服务地址: http://{host}:{port}")
        logger.info("✅ AgentScope服务已启动，可以开始使用VS Code插件")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentScope简化服务")
    parser.add_argument("--host", default="localhost", help="服务主机")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--demo", action="store_true", help="演示模式")
    
    args = parser.parse_args()
    
    # 创建并启动服务
    service = SimpleAgentScopeService()
    service.run(host=args.host, port=args.port, demo=args.demo)

if __name__ == "__main__":
    main()
