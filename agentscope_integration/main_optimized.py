#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的AgentScope多智能体编程工作流主服务
集成深度优化的AgentScope能力和Augment真实集成
"""

import asyncio
import logging
import argparse
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# AgentScope组件
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter

# 优化的组件
from .core.agentscope_workflow_manager import AgentScopeWorkflowManager
from .integrations.augment_integration_hub import AugmentIntegrationHub, AugmentMessage, AugmentEventType
from .agents.code_manager_agent import CodeManagerAgent
from .agents.compliance_auditor_agent import ComplianceAuditorAgent

# 原有组件
from .core.websocket_manager import WebSocketManager
from .core.config_manager import ConfigManager
from .interfaces.agent_interface import AgentTask, TaskType


class OptimizedAgentScopeService:
    """优化的AgentScope服务"""
    
    def __init__(self, config_path: str = "config/system_config.json"):
        self.logger = logging.getLogger(__name__)
        
        # 配置管理
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_configuration()
        
        # 核心组件
        self.workflow_manager = AgentScopeWorkflowManager()
        self.augment_hub = AugmentIntegrationHub(self.workflow_manager)
        self.websocket_manager = WebSocketManager()
        
        # 智能体
        self.agents: Dict[str, Any] = {}
        
        # FastAPI应用
        self.app = FastAPI(title="AgentScope Multi-Agent Workflow (Optimized)")
        self._setup_fastapi()
        
        self.logger.info("Optimized AgentScope service initialized")
    
    async def initialize(self):
        """初始化服务"""
        self.logger.info("Initializing optimized AgentScope service...")
        
        try:
            # 1. 初始化LLM模型
            await self._initialize_models()
            
            # 2. 创建和注册智能体
            await self._create_agents()
            
            # 3. 启动Augment集成
            await self._start_augment_integration()
            
            # 4. 设置事件处理
            self._setup_event_handlers()
            
            self.logger.info("Service initialization completed")
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            raise
    
    async def _initialize_models(self):
        """初始化LLM模型"""
        llm_config = self.config.get("llm_providers", {}).get("openai", {})
        
        if not llm_config.get("enabled", False):
            raise ValueError("OpenAI LLM provider is not enabled")
        
        self.model = OpenAIChatModel(
            model_name=llm_config.get("model", "gpt-4"),
            api_key=llm_config.get("api_key"),
            temperature=llm_config.get("temperature", 0.7)
        )
        
        self.formatter = OpenAIChatFormatter()
        
        self.logger.info("LLM models initialized")
    
    async def _create_agents(self):
        """创建和注册智能体"""
        # 创建代码管理员智能体
        code_manager = CodeManagerAgent(
            model=self.model,
            formatter=self.formatter
        )
        
        # 创建合规审核智能体
        compliance_auditor = ComplianceAuditorAgent(
            model=self.model,
            formatter=self.formatter
        )
        
        # 注册到工作流管理器
        await self.workflow_manager.register_agent(code_manager)
        await self.workflow_manager.register_agent(compliance_auditor)
        
        # 保存引用
        self.agents["code_manager"] = code_manager
        self.agents["compliance_auditor"] = compliance_auditor
        
        self.logger.info(f"Created and registered {len(self.agents)} agents")
    
    async def _start_augment_integration(self):
        """启动Augment集成"""
        # 注册事件回调
        self.augment_hub.register_event_callback(
            "message_processed",
            self._on_augment_message_processed
        )
        
        self.augment_hub.register_event_callback(
            "message_failed",
            self._on_augment_message_failed
        )
        
        # 启动集成中心
        await self.augment_hub.start()
        
        self.logger.info("Augment integration started")
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        # 为智能体注册事件回调
        for agent in self.agents.values():
            agent.register_event_callback(
                "task_completed",
                self._on_agent_task_completed
            )
            
            agent.register_event_callback(
                "task_failed",
                self._on_agent_task_failed
            )
    
    async def _on_augment_message_processed(self, data: Dict[str, Any]):
        """处理Augment消息完成事件"""
        self.logger.info(f"Augment message processed: {data['task'].id}")
        
        # 通过WebSocket广播事件
        await self.websocket_manager.broadcast_event("augment_task_completed", {
            "task_id": data["task"].id,
            "workflow_id": data["workflow_id"],
            "result": data.get("result", {})
        })
    
    async def _on_augment_message_failed(self, data: Dict[str, Any]):
        """处理Augment消息失败事件"""
        self.logger.error(f"Augment message failed: {data.get('error')}")
        
        # 通过WebSocket广播错误事件
        await self.websocket_manager.broadcast_event("augment_task_failed", {
            "error": data.get("error"),
            "message": data.get("message", {})
        })
    
    async def _on_agent_task_completed(self, data: Dict[str, Any]):
        """处理智能体任务完成事件"""
        task = data["task"]
        result = data["result"]
        
        # 广播任务完成事件
        await self.websocket_manager.broadcast_event("task_completed", {
            "task_id": task.id,
            "agent_id": result.get("agent_id"),
            "status": result.status.value,
            "result": result.to_dict()
        })
    
    async def _on_agent_task_failed(self, data: Dict[str, Any]):
        """处理智能体任务失败事件"""
        task = data["task"]
        error = data["error"]
        
        # 广播任务失败事件
        await self.websocket_manager.broadcast_event("task_failed", {
            "task_id": task.id,
            "error": error
        })
    
    def _setup_fastapi(self):
        """设置FastAPI路由"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            return {"status": "ok", "service": "agentscope-optimized"}
        
        # 智能体状态
        @self.app.get("/agents")
        async def get_agents():
            agents_status = []
            for name, agent in self.agents.items():
                status = await agent.get_status()
                agents_status.append({
                    "name": name,
                    "agent_id": agent.agent_id,
                    "role": agent.role.value,
                    "status": status,
                    "supported_tasks": [t.value for t in agent.supported_tasks]
                })
            return agents_status
        
        # 创建工作流
        @self.app.post("/workflows")
        async def create_workflow(task_data: dict):
            try:
                # 创建任务对象
                task = AgentTask(
                    id=task_data.get("id", f"task_{asyncio.get_event_loop().time()}"),
                    type=TaskType(task_data["type"]),
                    title=task_data["title"],
                    description=task_data["description"],
                    parameters=task_data.get("parameters", {}),
                    priority=task_data.get("priority", 2)
                )
                
                # 创建工作流
                workflow_id = await self.workflow_manager.create_workflow(task)
                
                return {
                    "workflow_id": workflow_id,
                    "task_id": task.id,
                    "status": "created"
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # 处理Augment消息
        @self.app.post("/augment/message")
        async def process_augment_message(message_data: dict):
            try:
                # 创建Augment消息
                message = AugmentMessage(
                    event_type=AugmentEventType(message_data.get("event_type", "code_analysis_request")),
                    content=message_data["content"],
                    context=message_data.get("context", {}),
                    source=message_data.get("source", "api"),
                    timestamp=asyncio.get_event_loop().time(),
                    metadata=message_data.get("metadata")
                )
                
                # 处理消息
                result = await self.augment_hub.process_augment_message(message)
                
                return result
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # 工作流状态
        @self.app.get("/workflows/{workflow_id}")
        async def get_workflow_status(workflow_id: str):
            status = await self.workflow_manager.get_workflow_status(workflow_id)
            if not status:
                raise HTTPException(status_code=404, detail="Workflow not found")
            return status
        
        # 统计信息
        @self.app.get("/statistics")
        async def get_statistics():
            return {
                "workflow_stats": self.workflow_manager.get_workflow_statistics(),
                "augment_stats": self.augment_hub.get_statistics(),
                "websocket_connections": self.websocket_manager.get_connection_count()
            }
        
        # WebSocket连接
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # 处理客户端消息
                    await self._handle_websocket_message(websocket, data)
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
    
    async def _handle_websocket_message(self, websocket: WebSocket, data: str):
        """处理WebSocket消息"""
        try:
            import json
            message = json.loads(data)
            
            if message.get("type") == "augment_command":
                # 处理来自VS Code的Augment命令
                augment_message = AugmentMessage(
                    event_type=AugmentEventType.CODE_ANALYSIS_REQUEST,
                    content=message["content"],
                    context=message.get("context", {}),
                    source="vscode",
                    timestamp=asyncio.get_event_loop().time()
                )
                
                await self.augment_hub.process_augment_message(augment_message)
                
        except Exception as e:
            self.logger.error(f"WebSocket message handling error: {e}")
    
    async def start_server(self, host: str = "localhost", port: int = 8000):
        """启动服务器"""
        await self.initialize()
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    async def shutdown(self):
        """关闭服务"""
        self.logger.info("Shutting down optimized AgentScope service...")
        
        # 停止Augment集成
        await self.augment_hub.stop()
        
        # 关闭WebSocket连接
        await self.websocket_manager.disconnect_all()
        
        self.logger.info("Service shutdown completed")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AgentScope Multi-Agent Workflow (Optimized)")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--config", default="config/system_config.json", help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建和启动服务
    service = OptimizedAgentScopeService(args.config)
    
    try:
        await service.start_server(args.host, args.port)
    except KeyboardInterrupt:
        await service.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
