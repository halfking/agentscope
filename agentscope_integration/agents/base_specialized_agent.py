# -*- coding: utf-8 -*-
"""
优化的专业化智能体基类 - 深度集成AgentScope能力
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Type, Callable
from datetime import datetime
import shortuuid
import time

from agentscope.agent import ReActAgent
from agentscope.message import Msg, TextBlock, ToolUseBlock, ToolResultBlock
from agentscope.tool import Toolkit, ToolResponse
from agentscope.memory import MemoryBase, InMemoryMemory, LongTermMemoryBase
from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase
from agentscope.session import JSONSession
from agentscope.tracing import trace_toolkit

from ..interfaces.agent_interface import (
    ISpecializedAgent, AgentRole, TaskType, AgentTask, TaskResult,
    AgentStatus, TaskStatus
)


class PerformanceTracker:
    """性能追踪器 - 用于监控智能体性能"""

    def __init__(self):
        self.metrics = {}
        self.start_times = {}

    def start_tracking(self, operation: str):
        """开始追踪操作"""
        self.start_times[operation] = time.time()

    def end_tracking(self, operation: str):
        """结束追踪操作"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(duration)
            del self.start_times[operation]

    def get_average_time(self, operation: str) -> float:
        """获取平均执行时间"""
        if operation in self.metrics and self.metrics[operation]:
            return sum(self.metrics[operation]) / len(self.metrics[operation])
        return 0.0


class OptimizedSpecializedAgent(ReActAgent, ISpecializedAgent):
    """优化的专业化智能体基类 - 深度集成AgentScope能力"""
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        supported_tasks: List[TaskType],
        model: ChatModelBase,
        formatter: FormatterBase,
        sys_prompt: Optional[str] = None,
        **kwargs
    ):
        # 使用AgentScope标准记忆系统
        memory = InMemoryMemory()

        # 创建专业化工具包
        toolkit = Toolkit()

        # 初始化AgentScope ReActAgent
        super().__init__(
            name=name,
            model=model,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
            sys_prompt=sys_prompt or self._generate_default_prompt(role),
            **kwargs
        )

        # 专业化智能体属性
        self.agent_id = shortuuid.uuid()
        self._role = role
        self._supported_tasks = supported_tasks
        self._current_task: Optional[AgentTask] = None
        self._task_history: List[TaskResult] = []

        # 长期记忆用于代码知识图谱和历史数据
        self.long_term_memory = LongTermMemoryBase()

        # 性能追踪
        self.performance_tracker = PerformanceTracker()

        # 会话管理
        self.current_session: Optional[Session] = None

        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {}

        # 异步初始化专业化工具
        asyncio.create_task(self._initialize_specialized_tools())
    
    def _generate_default_prompt(self, role: AgentRole) -> str:
        """生成默认系统提示词"""
        role_prompts = {
            AgentRole.CODE_MANAGER: """你是一个专业的代码管理员智能体，负责维护完整的代码库知识图谱。

你的核心职责包括：
1. 分析代码结构和依赖关系
2. 维护代码知识图谱
3. 跟踪代码变更和影响范围
4. 提供代码查询和搜索服务
5. 评估架构设计和模块划分

你拥有专业的代码分析工具，能够深入理解代码结构、依赖关系和架构模式。""",

            AgentRole.COMPLIANCE_AUDITOR: """你是一个严格的代码质量和安全专家，负责确保代码符合项目规范和安全要求。

你的核心职责包括：
1. 执行静态代码分析，检测代码质量问题
2. 进行安全漏洞扫描和风险评估
3. 分析测试质量，特别是检测虚假测试
4. 检查代码是否符合编码规范
5. 提供具体的修改建议和最佳实践指导

你特别关注SQL注入、XSS等安全漏洞，硬编码密钥和敏感信息，以及代码复杂度和可维护性。"""
        }

        return role_prompts.get(role, "你是一个专业的代码分析智能体。")

    async def _initialize_specialized_tools(self):
        """异步初始化专业化工具"""
        try:
            # 注册专业化工具
            await self._register_specialized_tools()

            # 初始化长期记忆
            await self._setup_long_term_memory()

        except Exception as e:
            print(f"Failed to initialize specialized tools: {e}")

    async def _setup_long_term_memory(self):
        """设置长期记忆"""
        # 为不同类型的数据创建命名空间
        await self.long_term_memory.create_namespace("code_structures")
        await self.long_term_memory.create_namespace("knowledge_graphs")
        await self.long_term_memory.create_namespace("analysis_results")
        await self.long_term_memory.create_namespace("performance_metrics")

    @property
    def role(self) -> AgentRole:
        """智能体角色"""
        return self._role

    @property
    def supported_tasks(self) -> List[TaskType]:
        """支持的任务类型"""
        return self._supported_tasks
    
    async def execute_task_with_session(self, task: AgentTask) -> TaskResult:
        """在会话中执行任务 - 集成AgentScope Session管理"""
        async with Session() as session:
            # 记录任务开始
            session.add_event("task_started", {
                "task_id": task.id,
                "task_type": task.type.value,
                "agent_id": self.agent_id
            })

            try:
                result = await self.execute_task(task)

                # 记录任务完成
                session.add_event("task_completed", {
                    "task_id": task.id,
                    "status": result.status.value,
                    "execution_time": result.execution_time
                })

                return result

            except Exception as e:
                # 记录任务失败
                session.add_event("task_failed", {
                    "task_id": task.id,
                    "error": str(e)
                })
                raise

    @trace_toolkit
    async def execute_task(self, task: AgentTask) -> TaskResult:
        """执行任务 - 带性能追踪"""
        self.performance_tracker.start_tracking(f"task_{task.type.value}")

        try:
            # 检查任务类型是否支持
            if task.type not in self.supported_tasks:
                return TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    error=f"Unsupported task type: {task.type}",
                    completed_at=datetime.now()
                )

            # 设置当前任务
            self._current_task = task

            # 从长期记忆中获取相关上下文
            context = await self._get_task_context(task)

            # 构造任务消息
            task_msg = self._create_task_message(task, context)

            # 执行任务
            response = await self(task_msg)

            # 解析结果
            result = await self._parse_task_result(task, response)

            # 存储结果到长期记忆
            await self._store_task_result(task, result)

            # 记录任务历史
            self._task_history.append(result)

            # 触发事件回调
            await self._trigger_event_callbacks("task_completed", {
                "task": task,
                "result": result
            })

            return result

        except Exception as e:
            error_result = TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=str(e),
                completed_at=datetime.now()
            )

            # 触发错误事件
            await self._trigger_event_callbacks("task_failed", {
                "task": task,
                "error": str(e)
            })

            return error_result

        finally:
            self.performance_tracker.end_tracking(f"task_{task.type.value}")
            self._current_task = None
    
    async def get_status(self) -> AgentStatus:
        """获取智能体状态"""
        return AgentStatus(
            agent_id=self.agent_id,
            role=self.role,
            status="busy" if self._current_task else "idle",
            current_task=self._current_task.id if self._current_task else None,
            last_update=datetime.now(),
            performance_metrics=self._performance_metrics.copy()
        )
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if self._current_task and self._current_task.id == task_id:
            # 中断当前执行
            if hasattr(self, '_reply_task') and self._reply_task:
                self._reply_task.cancel()
            self._current_task = None
            return True
        return False
    
    def _create_task_message(self, task: AgentTask, context: Dict[str, Any] = None) -> Msg:
        """创建任务消息 - 包含上下文信息"""
        content_parts = [
            f"任务类型: {task.type.value}",
            f"任务标题: {task.title}",
            f"任务描述: {task.description}",
            f"任务参数: {json.dumps(task.parameters, ensure_ascii=False, indent=2)}"
        ]

        # 添加上下文信息
        if context:
            content_parts.append("\n=== 相关上下文信息 ===")

            if "code_structure" in context:
                content_parts.append(f"代码结构: {json.dumps(context['code_structure'], ensure_ascii=False, indent=2)}")

            if "similar_results" in context:
                content_parts.append("相似任务的历史结果:")
                for i, result in enumerate(context["similar_results"], 1):
                    content_parts.append(f"{i}. {result.result.get('summary', 'N/A')}")

        content_parts.append("\n请根据你的专业能力和提供的上下文信息执行这个任务，并提供详细的分析结果。")

        return Msg(
            name="user",
            content="\n".join(content_parts),
            role="user"
        )
    
    async def _parse_task_result(self, task: AgentTask, response: Msg) -> TaskResult:
        """解析任务结果"""
        # 默认实现，子类可以重写
        result_data = {
            "response": response.get_text_content(),
            "metadata": response.metadata or {}
        }
        
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            result=result_data,
            completed_at=datetime.now()
        )
    
    def _update_performance_metrics(self, task: AgentTask, result: TaskResult):
        """更新性能指标"""
        # 任务完成率
        total_tasks = len(self._task_history) + 1
        successful_tasks = sum(1 for r in self._task_history if r.status == TaskStatus.COMPLETED) + (1 if result.status == TaskStatus.COMPLETED else 0)
        self._performance_metrics["success_rate"] = successful_tasks / total_tasks
        
        # 平均执行时间
        if result.execution_time:
            execution_times = [r.execution_time for r in self._task_history if r.execution_time] + [result.execution_time]
            self._performance_metrics["avg_execution_time"] = sum(execution_times) / len(execution_times)
        
        # 任务类型统计
        task_type_key = f"tasks_{task.type.value}"
        self._performance_metrics[task_type_key] = self._performance_metrics.get(task_type_key, 0) + 1
    
    async def _get_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """从长期记忆中获取任务相关上下文"""
        context = {}

        try:
            # 获取相关的代码结构信息
            if "file_path" in task.parameters:
                file_path = task.parameters["file_path"]
                structure_key = f"code_structure:{file_path}"
                structure = await self.long_term_memory.get("code_structures", structure_key)
                if structure:
                    context["code_structure"] = structure

            # 获取历史分析结果
            similar_tasks = [
                r for r in self._task_history
                if r.status == TaskStatus.COMPLETED and
                   any(param in task.parameters for param in r.result.get("parameters", {}))
            ]
            if similar_tasks:
                context["similar_results"] = similar_tasks[-3:]  # 最近3个相似结果

        except Exception as e:
            print(f"Failed to get task context: {e}")

        return context

    async def _store_task_result(self, task: AgentTask, result: TaskResult):
        """存储任务结果到长期记忆"""
        try:
            # 存储分析结果
            result_key = f"task_result:{task.id}"
            await self.long_term_memory.store(
                "analysis_results",
                result_key,
                {
                    "task": task.to_dict(),
                    "result": result.to_dict(),
                    "timestamp": datetime.now().isoformat()
                }
            )

            # 更新性能指标
            metrics_key = f"performance:{self.agent_id}"
            current_metrics = await self.long_term_memory.get("performance_metrics", metrics_key) or {}

            # 更新指标
            task_type_key = f"tasks_{task.type.value}"
            current_metrics[task_type_key] = current_metrics.get(task_type_key, 0) + 1
            current_metrics["total_tasks"] = current_metrics.get("total_tasks", 0) + 1

            if result.status == TaskStatus.COMPLETED:
                current_metrics["successful_tasks"] = current_metrics.get("successful_tasks", 0) + 1

            await self.long_term_memory.store("performance_metrics", metrics_key, current_metrics)

        except Exception as e:
            print(f"Failed to store task result: {e}")

    async def _trigger_event_callbacks(self, event_type: str, data: Dict[str, Any]):
        """触发事件回调"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    print(f"Event callback error: {e}")

    def register_event_callback(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    async def _register_specialized_tools(self):
        """注册专业化工具，子类实现"""
        pass
    
    # AgentScope ReActAgent的扩展方法
    async def handle_interrupt(self, *args, **kwargs) -> Msg:
        """处理中断"""
        if self._current_task:
            # 记录任务被中断
            result = TaskResult(
                task_id=self._current_task.id,
                status=TaskStatus.CANCELLED,
                error="Task was interrupted",
                completed_at=datetime.now()
            )
            self._task_history.append(result)
            self._current_task = None
        
        return Msg(
            name=self.name,
            content="任务已被中断",
            role="assistant"
        )
    
    def get_task_history(self) -> List[TaskResult]:
        """获取任务历史"""
        return self._task_history.copy()
    
    def clear_task_history(self):
        """清空任务历史"""
        self._task_history.clear()
        self._performance_metrics.clear()


class SpecializedToolFunction:
    """专业化工具函数装饰器"""
    
    def __init__(self, task_types: List[TaskType], description: str = ""):
        self.task_types = task_types
        self.description = description
    
    def __call__(self, func):
        func._task_types = self.task_types
        func._tool_description = self.description
        return func


def register_specialized_tool(task_types: List[TaskType], description: str = ""):
    """注册专业化工具的装饰器"""
    return SpecializedToolFunction(task_types, description)
