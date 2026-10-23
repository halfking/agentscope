#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope多智能体编程工作流系统主启动器
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agentscope import init
from agentscope.model import ChatModelConfig
from agentscope.formatter import FormatterConfig
from agentscope.tool import Toolkit

from .config.system_config import get_config, load_config_from_env, SystemConfig
from .agents.code_manager_agent import CodeManagerAgent
from .agents.compliance_auditor_agent import ComplianceAuditorAgent
from .mcp.mcp_manager import MCPManager
from .core.agent_coordinator import AgentCoordinator
from .core.task_manager import TaskManager
from .core.websocket_manager import WebSocketManager
from .api.routes import create_api_router


class AgentScopeSystem:
    """AgentScope多智能体系统主类"""
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or get_config()
        self.logger = self._setup_logging()
        
        # 核心组件
        self.mcp_manager: Optional[MCPManager] = None
        self.agent_coordinator: Optional[AgentCoordinator] = None
        self.task_manager: Optional[TaskManager] = None
        self.websocket_manager: Optional[WebSocketManager] = None
        
        # FastAPI应用
        self.app: Optional[FastAPI] = None
        
        # 运行状态
        self.is_running = False
        self._shutdown_event = asyncio.Event()
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    Path(self.config.log_dir) / "agentscope_system.log",
                    encoding='utf-8'
                )
            ]
        )
        return logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化系统"""
        self.logger.info("Initializing AgentScope Multi-Agent System...")
        
        try:
            # 验证配置
            config_errors = self.config.validate_config()
            if config_errors:
                for error in config_errors:
                    self.logger.error(f"Configuration error: {error}")
                raise ValueError("Configuration validation failed")
            
            # 初始化AgentScope
            await self._init_agentscope()
            
            # 初始化MCP管理器
            await self._init_mcp_manager()
            
            # 初始化智能体协调器
            await self._init_agent_coordinator()
            
            # 初始化任务管理器
            await self._init_task_manager()
            
            # 初始化WebSocket管理器
            await self._init_websocket_manager()
            
            # 创建FastAPI应用
            await self._create_fastapi_app()
            
            self.logger.info("System initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}")
            raise
    
    async def _init_agentscope(self):
        """初始化AgentScope框架"""
        # 获取启用的LLM提供商配置
        model_configs = []
        for provider_name, provider_config in self.config.llm_providers.items():
            if provider_config.enabled:
                llm_config = self.config.get_llm_config(provider_name)
                if llm_config:
                    model_configs.append(llm_config)
        
        if not model_configs:
            raise ValueError("No enabled LLM providers found")
        
        # 初始化AgentScope
        init(
            model_configs=model_configs,
            project=self.config.project_name,
            name="agentscope_multi_agent_workflow",
            save_dir=self.config.work_dir,
            use_monitor=True,
            logger_level=self.config.log_level
        )
        
        self.logger.info(f"AgentScope initialized with {len(model_configs)} LLM providers")
    
    async def _init_mcp_manager(self):
        """初始化MCP管理器"""
        mcp_config_path = Path(self.config.work_dir) / self.config.mcp_config_file
        self.mcp_manager = MCPManager(str(mcp_config_path) if mcp_config_path.exists() else None)
        
        # 注册配置中的MCP服务器
        for server_name, server_config in self.config.mcp_servers.items():
            if server_config.enabled:
                await self.mcp_manager.register_mcp_server(
                    server_name,
                    {
                        "command": server_config.command,
                        "args": server_config.args,
                        "env": server_config.env,
                        "enabled": server_config.enabled
                    }
                )
        
        # 启动所有MCP服务器
        await self.mcp_manager.start_all_servers()
        
        self.logger.info("MCP Manager initialized")
    
    async def _init_agent_coordinator(self):
        """初始化智能体协调器"""
        self.agent_coordinator = AgentCoordinator()
        
        # 创建并注册智能体
        for agent_config in self.config.get_enabled_agents():
            agent = await self._create_agent(agent_config)
            if agent:
                await self.agent_coordinator.register_agent(agent)
        
        self.logger.info(f"Agent Coordinator initialized with {len(self.agent_coordinator.agents)} agents")
    
    async def _create_agent(self, agent_config):
        """创建智能体实例"""
        try:
            # 获取LLM配置
            llm_config = self.config.get_llm_config(agent_config.llm_provider)
            if not llm_config:
                self.logger.error(f"LLM provider '{agent_config.llm_provider}' not available for agent '{agent_config.agent_id}'")
                return None
            
            # 创建模型和格式化器
            from agentscope.model import get_model
            from agentscope.formatter import get_formatter
            
            model = get_model(llm_config)
            formatter = get_formatter(FormatterConfig())
            
            # 创建工具包
            toolkit = Toolkit()
            
            # 注册MCP工具到工具包
            if self.mcp_manager:
                self.mcp_manager.register_mcp_tools_to_toolkit(toolkit)
            
            # 根据角色创建对应的智能体
            if agent_config.role == "code_manager":
                agent = CodeManagerAgent(
                    model=model,
                    formatter=formatter,
                    toolkit=toolkit
                )
            elif agent_config.role == "compliance_auditor":
                agent = ComplianceAuditorAgent(
                    model=model,
                    formatter=formatter,
                    toolkit=toolkit
                )
            else:
                self.logger.warning(f"Unknown agent role: {agent_config.role}")
                return None
            
            self.logger.info(f"Created agent: {agent_config.agent_id} ({agent_config.role})")
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to create agent '{agent_config.agent_id}': {e}")
            return None
    
    async def _init_task_manager(self):
        """初始化任务管理器"""
        from .core.task_manager import TaskManager
        self.task_manager = TaskManager(self.agent_coordinator)
        self.logger.info("Task Manager initialized")
    
    async def _init_websocket_manager(self):
        """初始化WebSocket管理器"""
        from .core.websocket_manager import WebSocketManager
        self.websocket_manager = WebSocketManager()
        
        # 设置事件监听
        if self.agent_coordinator:
            self.agent_coordinator.set_event_callback(self.websocket_manager.broadcast_event)
        
        if self.task_manager:
            self.task_manager.set_event_callback(self.websocket_manager.broadcast_event)
        
        self.logger.info("WebSocket Manager initialized")
    
    async def _create_fastapi_app(self):
        """创建FastAPI应用"""
        self.app = FastAPI(
            title="AgentScope Multi-Agent Workflow API",
            description="API for AgentScope Multi-Agent Programming Workflow System",
            version=self.config.version,
            debug=self.config.debug
        )
        
        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 添加API路由
        api_router = create_api_router(
            self.agent_coordinator,
            self.task_manager,
            self.mcp_manager
        )
        self.app.include_router(api_router, prefix="/api")
        
        # 添加WebSocket端点
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    await self.websocket_manager.handle_message(websocket, data)
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
        
        # 健康检查端点
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "version": self.config.version,
                "agents_count": len(self.agent_coordinator.agents) if self.agent_coordinator else 0,
                "mcp_servers_count": len(self.mcp_manager.clients) if self.mcp_manager else 0
            }
        
        # 静态文件服务（如果需要）
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        self.logger.info("FastAPI application created")
    
    async def start(self):
        """启动系统"""
        if self.is_running:
            self.logger.warning("System is already running")
            return
        
        try:
            await self.initialize()
            
            # 设置信号处理
            for sig in [signal.SIGTERM, signal.SIGINT]:
                signal.signal(sig, self._signal_handler)
            
            self.is_running = True
            self.logger.info(f"Starting server on {self.config.backend_host}:{self.config.backend_port}")
            
            # 启动FastAPI服务器
            config = uvicorn.Config(
                self.app,
                host=self.config.backend_host,
                port=self.config.backend_port,
                log_level=self.config.log_level.lower(),
                access_log=self.config.debug
            )
            server = uvicorn.Server(config)
            
            # 在后台任务中运行服务器
            server_task = asyncio.create_task(server.serve())
            
            # 等待关闭信号
            await self._shutdown_event.wait()
            
            # 停止服务器
            server.should_exit = True
            await server_task
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            raise
        finally:
            await self.shutdown()
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_event.set()
    
    async def shutdown(self):
        """关闭系统"""
        if not self.is_running:
            return
        
        self.logger.info("Shutting down AgentScope Multi-Agent System...")
        
        try:
            # 关闭MCP管理器
            if self.mcp_manager:
                await self.mcp_manager.close_all()
            
            # 关闭WebSocket连接
            if self.websocket_manager:
                await self.websocket_manager.close_all()
            
            # 停止任务管理器
            if self.task_manager:
                await self.task_manager.shutdown()
            
            # 停止智能体协调器
            if self.agent_coordinator:
                await self.agent_coordinator.shutdown()
            
            self.is_running = False
            self.logger.info("System shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


async def main():
    """主函数"""
    # 加载配置
    config = load_config_from_env()
    
    # 创建并启动系统
    system = AgentScopeSystem(config)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"System error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
