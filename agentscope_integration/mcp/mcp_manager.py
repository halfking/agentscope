# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 管理器
集成AgentScope的MCP能力，提供统一的工具管理接口
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from dataclasses import dataclass, asdict

from agentscope.tool.mcp import MCPClient, MCPClientConfig
from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import TextBlock

from ..interfaces.agent_interface import IMCPManager


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    command: str
    args: List[str] = None
    env: Dict[str, str] = None
    transport: str = "stdio"  # stdio, sse, http
    url: Optional[str] = None
    enabled: bool = True
    description: str = ""
    
    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.env is None:
            self.env = {}


class MCPManager(IMCPManager):
    """MCP管理器 - 集成AgentScope的MCP功能"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.clients: Dict[str, MCPClient] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        self.available_tools: Dict[str, List[str]] = {}
        
        # 加载配置
        if config_file:
            self.load_config_file(config_file)
        else:
            self._load_default_configs()
    
    def load_config_file(self, config_file: str):
        """从配置文件加载MCP服务器配置"""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                for server_name, server_config in config_data.get("mcp_servers", {}).items():
                    self.server_configs[server_name] = MCPServerConfig(
                        name=server_name,
                        **server_config
                    )
                    
                self.logger.info(f"Loaded {len(self.server_configs)} MCP server configurations")
            else:
                self.logger.warning(f"Config file not found: {config_file}")
                self._load_default_configs()
                
        except Exception as e:
            self.logger.error(f"Failed to load config file: {e}")
            self._load_default_configs()
    
    def _load_default_configs(self):
        """加载默认MCP服务器配置"""
        default_configs = {
            "filesystem": MCPServerConfig(
                name="filesystem",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                description="文件系统操作工具"
            ),
            "brave_search": MCPServerConfig(
                name="brave_search",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-brave-search"],
                env={"BRAVE_API_KEY": "your-api-key"},
                description="Brave搜索工具"
            ),
            "git": MCPServerConfig(
                name="git",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-git"],
                description="Git操作工具"
            ),
            "postgres": MCPServerConfig(
                name="postgres",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-postgres"],
                env={"POSTGRES_CONNECTION_STRING": "postgresql://user:pass@localhost/db"},
                description="PostgreSQL数据库工具"
            ),
            "code_analysis": MCPServerConfig(
                name="code_analysis",
                command="python",
                args=["-m", "agentscope_integration.mcp.servers.code_analysis_server"],
                description="代码分析专用工具"
            )
        }
        
        self.server_configs.update(default_configs)
        self.logger.info("Loaded default MCP server configurations")
    
    async def register_mcp_server(self, name: str, config: Dict[str, Any]) -> bool:
        """注册MCP服务器"""
        try:
            server_config = MCPServerConfig(name=name, **config)
            self.server_configs[name] = server_config
            
            if server_config.enabled:
                await self._start_mcp_client(name, server_config)
            
            self.logger.info(f"Registered MCP server: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register MCP server {name}: {e}")
            return False
    
    async def unregister_mcp_server(self, name: str) -> bool:
        """注销MCP服务器"""
        try:
            if name in self.clients:
                await self.clients[name].close()
                del self.clients[name]
            
            if name in self.server_configs:
                del self.server_configs[name]
            
            if name in self.available_tools:
                del self.available_tools[name]
            
            self.logger.info(f"Unregistered MCP server: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister MCP server {name}: {e}")
            return False
    
    async def start_all_servers(self):
        """启动所有启用的MCP服务器"""
        tasks = []
        for name, config in self.server_configs.items():
            if config.enabled:
                tasks.append(self._start_mcp_client(name, config))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for r in results if not isinstance(r, Exception))
            self.logger.info(f"Started {successful}/{len(tasks)} MCP servers")
    
    async def _start_mcp_client(self, name: str, config: MCPServerConfig):
        """启动单个MCP客户端"""
        try:
            # 创建MCP客户端配置
            client_config = MCPClientConfig(
                command=config.command,
                args=config.args,
                env=config.env
            )
            
            # 创建并启动客户端
            client = MCPClient(client_config)
            await client.start()
            
            # 获取可用工具
            tools = await client.list_tools()
            self.available_tools[name] = [tool.name for tool in tools]
            
            self.clients[name] = client
            self.logger.info(f"Started MCP client: {name} with {len(tools)} tools")
            
        except Exception as e:
            self.logger.error(f"Failed to start MCP client {name}: {e}")
            raise
    
    async def list_mcp_tools(self, server_name: str) -> List[str]:
        """列出指定MCP服务器的工具"""
        return self.available_tools.get(server_name, [])
    
    async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """调用MCP工具"""
        try:
            if server_name not in self.clients:
                raise ValueError(f"MCP server not found: {server_name}")
            
            client = self.clients[server_name]
            result = await client.call_tool(tool_name, kwargs)
            
            self.logger.debug(f"Called MCP tool {server_name}.{tool_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to call MCP tool {server_name}.{tool_name}: {e}")
            raise
    
    def register_mcp_tools_to_toolkit(self, toolkit: Toolkit, server_names: Optional[List[str]] = None):
        """将MCP工具注册到AgentScope Toolkit"""
        if server_names is None:
            server_names = list(self.clients.keys())
        
        for server_name in server_names:
            if server_name not in self.clients:
                continue
            
            tools = self.available_tools.get(server_name, [])
            for tool_name in tools:
                # 创建工具包装函数
                wrapped_tool = self._create_tool_wrapper(server_name, tool_name)
                
                # 注册到toolkit
                toolkit.register_tool_function(
                    tool_func=wrapped_tool,
                    group_name=f"mcp_{server_name}"
                )
        
        self.logger.info(f"Registered MCP tools from {len(server_names)} servers to toolkit")
    
    def _create_tool_wrapper(self, server_name: str, tool_name: str):
        """创建MCP工具的包装函数"""
        async def mcp_tool_wrapper(**kwargs) -> ToolResponse:
            try:
                result = await self.call_mcp_tool(server_name, tool_name, **kwargs)
                
                # 格式化结果
                if isinstance(result, dict):
                    content_text = json.dumps(result, ensure_ascii=False, indent=2)
                else:
                    content_text = str(result)
                
                return ToolResponse(
                    content=[TextBlock(type="text", text=content_text)]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"MCP工具调用失败: {str(e)}")]
                )
        
        # 设置函数元数据
        mcp_tool_wrapper.__name__ = f"{server_name}_{tool_name}"
        mcp_tool_wrapper.__doc__ = f"MCP工具: {server_name}.{tool_name}"
        
        return mcp_tool_wrapper
    
    async def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """获取MCP服务器信息"""
        if server_name not in self.clients:
            return None
        
        try:
            client = self.clients[server_name]
            config = self.server_configs[server_name]
            tools = self.available_tools.get(server_name, [])
            
            return {
                "name": server_name,
                "description": config.description,
                "status": "connected",
                "tools_count": len(tools),
                "tools": tools,
                "config": asdict(config)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get server info for {server_name}: {e}")
            return None
    
    async def get_all_servers_info(self) -> List[Dict[str, Any]]:
        """获取所有MCP服务器信息"""
        servers_info = []
        
        for server_name in self.server_configs:
            info = await self.get_server_info(server_name)
            if info:
                servers_info.append(info)
            else:
                # 添加未连接的服务器信息
                config = self.server_configs[server_name]
                servers_info.append({
                    "name": server_name,
                    "description": config.description,
                    "status": "disconnected",
                    "tools_count": 0,
                    "tools": [],
                    "config": asdict(config)
                })
        
        return servers_info
    
    async def reload_server(self, server_name: str) -> bool:
        """重新加载MCP服务器"""
        try:
            # 停止现有客户端
            if server_name in self.clients:
                await self.clients[server_name].close()
                del self.clients[server_name]
            
            # 重新启动
            if server_name in self.server_configs:
                config = self.server_configs[server_name]
                if config.enabled:
                    await self._start_mcp_client(server_name, config)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to reload MCP server {server_name}: {e}")
            return False
    
    async def close_all(self):
        """关闭所有MCP客户端"""
        tasks = []
        for client in self.clients.values():
            tasks.append(client.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.clients.clear()
        self.available_tools.clear()
        self.logger.info("Closed all MCP clients")
    
    def save_config(self, config_file: str):
        """保存配置到文件"""
        try:
            config_data = {
                "mcp_servers": {
                    name: asdict(config) 
                    for name, config in self.server_configs.items()
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved MCP configuration to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            raise
