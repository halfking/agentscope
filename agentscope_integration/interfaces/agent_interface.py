# -*- coding: utf-8 -*-
"""
AgentScope多智能体编程工作流接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from agentscope.message import Msg
from agentscope.tool import ToolResponse


class AgentRole(str, Enum):
    """智能体角色枚举"""
    CODE_MANAGER = "code_manager"
    COMPLIANCE_AUDITOR = "compliance_auditor"
    SYSTEM_ARCHITECT = "system_architect"
    COMMAND_COORDINATOR = "command_coordinator"


class TaskType(str, Enum):
    """任务类型枚举"""
    CODE_ANALYSIS = "code_analysis"
    QUALITY_CHECK = "quality_check"
    ARCHITECTURE_REVIEW = "architecture_review"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    SECURITY_SCAN = "security_scan"
    TEST_ANALYSIS = "test_analysis"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """智能体任务定义"""
    id: str
    type: TaskType
    title: str
    description: str
    parameters: Dict[str, Any]
    priority: int = 5
    timeout: Optional[int] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    completed_at: Optional[datetime] = None
    artifacts: List[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


@dataclass
class AgentStatus:
    """智能体状态信息"""
    agent_id: str
    role: AgentRole
    status: str
    current_task: Optional[str] = None
    last_update: datetime = None
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.now()
        if self.performance_metrics is None:
            self.performance_metrics = {}


class ISpecializedAgent(ABC):
    """专业化智能体接口"""
    
    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """智能体角色"""
        pass
    
    @property
    @abstractmethod
    def supported_tasks(self) -> List[TaskType]:
        """支持的任务类型"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: AgentTask) -> TaskResult:
        """执行任务"""
        pass
    
    @abstractmethod
    async def get_status(self) -> AgentStatus:
        """获取状态"""
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        pass


class IAgentCoordinator(ABC):
    """智能体协调器接口"""
    
    @abstractmethod
    async def register_agent(self, agent: ISpecializedAgent) -> bool:
        """注册智能体"""
        pass
    
    @abstractmethod
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        pass
    
    @abstractmethod
    async def dispatch_task(self, task: AgentTask) -> str:
        """分发任务"""
        pass
    
    @abstractmethod
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果"""
        pass
    
    @abstractmethod
    async def list_agents(self) -> List[AgentStatus]:
        """列出所有智能体"""
        pass


class IToolProvider(ABC):
    """工具提供者接口"""
    
    @abstractmethod
    async def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResponse:
        """执行工具"""
        pass
    
    @abstractmethod
    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """获取工具模式"""
        pass


class IVSCodeInterface(ABC):
    """VS Code接口"""
    
    @abstractmethod
    async def send_notification(self, message: str, level: str = "info") -> None:
        """发送通知"""
        pass
    
    @abstractmethod
    async def update_agent_status(self, status: AgentStatus) -> None:
        """更新智能体状态"""
        pass
    
    @abstractmethod
    async def show_task_result(self, result: TaskResult) -> None:
        """显示任务结果"""
        pass
    
    @abstractmethod
    async def request_user_input(self, prompt: str) -> str:
        """请求用户输入"""
        pass


class IMCPManager(ABC):
    """MCP管理器接口"""
    
    @abstractmethod
    async def register_mcp_server(self, name: str, config: Dict[str, Any]) -> bool:
        """注册MCP服务器"""
        pass
    
    @abstractmethod
    async def unregister_mcp_server(self, name: str) -> bool:
        """注销MCP服务器"""
        pass
    
    @abstractmethod
    async def list_mcp_tools(self, server_name: str) -> List[str]:
        """列出MCP工具"""
        pass
    
    @abstractmethod
    async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """调用MCP工具"""
        pass


# 事件系统接口
class IEventBus(ABC):
    """事件总线接口"""
    
    @abstractmethod
    async def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """发布事件"""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler) -> str:
        """订阅事件"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        pass


# 配置管理接口
class IConfigManager(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    async def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        pass
    
    @abstractmethod
    async def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        pass
    
    @abstractmethod
    async def load_config_file(self, file_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        pass
    
    @abstractmethod
    async def save_config_file(self, file_path: str, config: Dict[str, Any]) -> None:
        """保存配置文件"""
        pass
