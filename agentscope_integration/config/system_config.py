# -*- coding: utf-8 -*-
"""
AgentScope多智能体编程工作流系统配置
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from agentscope.model import ChatModelConfig
from agentscope.formatter import FormatterConfig


@dataclass
class LLMProviderConfig:
    """LLM提供商配置"""
    name: str
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    enabled: bool = True


@dataclass
class AgentConfig:
    """智能体配置"""
    agent_id: str
    role: str
    name: str
    enabled: bool = True
    llm_provider: str = "openai"
    model_override: Optional[str] = None
    max_memory_size: int = 1000
    tools_enabled: List[str] = field(default_factory=list)
    custom_prompt: Optional[str] = None


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    auto_start: bool = True


@dataclass
class VSCodeExtensionConfig:
    """VS Code扩展配置"""
    auto_start: bool = True
    dashboard_auto_open: bool = True
    notification_level: str = "info"
    analysis_auto_run: bool = False
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "node_modules/**", "**/*.min.js", "**/__pycache__/**", ".git/**"
    ])


@dataclass
class SystemConfig:
    """系统总配置"""
    # 基础配置
    project_name: str = "AgentScope Multi-Agent Workflow"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # 服务配置
    backend_host: str = "localhost"
    backend_port: int = 8000
    websocket_port: int = 8001
    
    # LLM提供商配置
    llm_providers: Dict[str, LLMProviderConfig] = field(default_factory=dict)
    default_llm_provider: str = "openai"
    
    # 智能体配置
    agents: Dict[str, AgentConfig] = field(default_factory=dict)
    
    # MCP配置
    mcp_servers: Dict[str, MCPServerConfig] = field(default_factory=dict)
    mcp_config_file: str = "mcp_config.json"
    
    # VS Code扩展配置
    vscode_extension: VSCodeExtensionConfig = field(default_factory=VSCodeExtensionConfig)
    
    # 工作目录配置
    work_dir: str = "./workspace"
    log_dir: str = "./logs"
    cache_dir: str = "./cache"
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.llm_providers:
            self._setup_default_llm_providers()
        
        if not self.agents:
            self._setup_default_agents()
        
        if not self.mcp_servers:
            self._setup_default_mcp_servers()
    
    def _setup_default_llm_providers(self):
        """设置默认LLM提供商"""
        self.llm_providers = {
            "openai": LLMProviderConfig(
                name="openai",
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model="gpt-4",
                enabled=bool(os.getenv("OPENAI_API_KEY"))
            ),
            "anthropic": LLMProviderConfig(
                name="anthropic",
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                model="claude-3-sonnet-20240229",
                enabled=bool(os.getenv("ANTHROPIC_API_KEY"))
            ),
            "siliconflow": LLMProviderConfig(
                name="siliconflow",
                api_key=os.getenv("SILICONFLOW_API_KEY", ""),
                base_url="https://api.siliconflow.cn/v1",
                model="Qwen/Qwen2.5-7B-Instruct",
                enabled=bool(os.getenv("SILICONFLOW_API_KEY"))
            ),
            "dashscope": LLMProviderConfig(
                name="dashscope",
                api_key=os.getenv("DASHSCOPE_API_KEY", ""),
                model="qwen-plus",
                enabled=bool(os.getenv("DASHSCOPE_API_KEY"))
            )
        }
    
    def _setup_default_agents(self):
        """设置默认智能体"""
        self.agents = {
            "code_manager": AgentConfig(
                agent_id="code_manager",
                role="code_manager",
                name="CodeManager",
                llm_provider="openai",
                tools_enabled=["parse_code_file", "analyze_dependencies", "build_knowledge_graph"]
            ),
            "compliance_auditor": AgentConfig(
                agent_id="compliance_auditor",
                role="compliance_auditor", 
                name="ComplianceAuditor",
                llm_provider="anthropic",
                tools_enabled=["static_code_analysis", "security_vulnerability_scan", "test_quality_analysis"]
            ),
            "system_architect": AgentConfig(
                agent_id="system_architect",
                role="system_architect",
                name="SystemArchitect",
                enabled=False,
                llm_provider="siliconflow",
                tools_enabled=["architecture_analysis", "design_pattern_detection"]
            ),
            "command_coordinator": AgentConfig(
                agent_id="command_coordinator",
                role="command_coordinator",
                name="CommandCoordinator",
                llm_provider="openai",
                tools_enabled=["task_coordination", "workflow_management"]
            )
        }
    
    def _setup_default_mcp_servers(self):
        """设置默认MCP服务器"""
        self.mcp_servers = {
            "filesystem": MCPServerConfig(
                name="filesystem",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
            ),
            "git": MCPServerConfig(
                name="git",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-git"]
            ),
            "code_analysis": MCPServerConfig(
                name="code_analysis",
                command="python",
                args=["-m", "agentscope_integration.mcp.servers.code_analysis_server"]
            ),
            "brave_search": MCPServerConfig(
                name="brave_search",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-brave-search"],
                env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")},
                enabled=bool(os.getenv("BRAVE_API_KEY"))
            )
        }
    
    def get_llm_config(self, provider_name: str) -> Optional[ChatModelConfig]:
        """获取LLM配置"""
        provider = self.llm_providers.get(provider_name)
        if not provider or not provider.enabled:
            return None
        
        config_kwargs = {
            "model": provider.model,
            "api_key": provider.api_key,
            "max_tokens": provider.max_tokens,
            "temperature": provider.temperature,
            "timeout": provider.timeout
        }
        
        if provider.base_url:
            config_kwargs["base_url"] = provider.base_url
        
        return ChatModelConfig(**config_kwargs)
    
    def get_enabled_agents(self) -> List[AgentConfig]:
        """获取启用的智能体配置"""
        return [agent for agent in self.agents.values() if agent.enabled]
    
    def get_enabled_mcp_servers(self) -> List[MCPServerConfig]:
        """获取启用的MCP服务器配置"""
        return [server for server in self.mcp_servers.values() if server.enabled]
    
    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []
        
        # 检查LLM提供商配置
        enabled_providers = [p for p in self.llm_providers.values() if p.enabled]
        if not enabled_providers:
            errors.append("No LLM providers are enabled")
        
        # 检查默认提供商
        if self.default_llm_provider not in self.llm_providers:
            errors.append(f"Default LLM provider '{self.default_llm_provider}' not found")
        
        # 检查智能体配置
        enabled_agents = self.get_enabled_agents()
        if not enabled_agents:
            errors.append("No agents are enabled")
        
        # 检查智能体的LLM提供商
        for agent in enabled_agents:
            if agent.llm_provider not in self.llm_providers:
                errors.append(f"Agent '{agent.agent_id}' references unknown LLM provider '{agent.llm_provider}'")
            elif not self.llm_providers[agent.llm_provider].enabled:
                errors.append(f"Agent '{agent.agent_id}' references disabled LLM provider '{agent.llm_provider}'")
        
        # 检查目录
        for dir_name in [self.work_dir, self.log_dir, self.cache_dir]:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """从字典创建配置"""
        # 处理嵌套的dataclass
        if 'llm_providers' in data:
            data['llm_providers'] = {
                k: LLMProviderConfig(**v) if isinstance(v, dict) else v
                for k, v in data['llm_providers'].items()
            }
        
        if 'agents' in data:
            data['agents'] = {
                k: AgentConfig(**v) if isinstance(v, dict) else v
                for k, v in data['agents'].items()
            }
        
        if 'mcp_servers' in data:
            data['mcp_servers'] = {
                k: MCPServerConfig(**v) if isinstance(v, dict) else v
                for k, v in data['mcp_servers'].items()
            }
        
        if 'vscode_extension' in data:
            if isinstance(data['vscode_extension'], dict):
                data['vscode_extension'] = VSCodeExtensionConfig(**data['vscode_extension'])
        
        return cls(**data)
    
    def save_to_file(self, file_path: str):
        """保存配置到文件"""
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'SystemConfig':
        """从文件加载配置"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


# 全局配置实例
_global_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """获取全局配置"""
    global _global_config
    if _global_config is None:
        _global_config = SystemConfig()
    return _global_config


def set_config(config: SystemConfig):
    """设置全局配置"""
    global _global_config
    _global_config = config


def load_config_from_file(file_path: str) -> SystemConfig:
    """从文件加载配置并设置为全局配置"""
    config = SystemConfig.load_from_file(file_path)
    set_config(config)
    return config


def load_config_from_env() -> SystemConfig:
    """从环境变量加载配置"""
    config = SystemConfig()
    
    # 从环境变量覆盖配置
    if os.getenv("AGENTSCOPE_DEBUG"):
        config.debug = os.getenv("AGENTSCOPE_DEBUG").lower() == "true"
    
    if os.getenv("AGENTSCOPE_LOG_LEVEL"):
        config.log_level = os.getenv("AGENTSCOPE_LOG_LEVEL")
    
    if os.getenv("AGENTSCOPE_BACKEND_HOST"):
        config.backend_host = os.getenv("AGENTSCOPE_BACKEND_HOST")
    
    if os.getenv("AGENTSCOPE_BACKEND_PORT"):
        config.backend_port = int(os.getenv("AGENTSCOPE_BACKEND_PORT"))
    
    if os.getenv("AGENTSCOPE_DEFAULT_LLM"):
        config.default_llm_provider = os.getenv("AGENTSCOPE_DEFAULT_LLM")
    
    set_config(config)
    return config
