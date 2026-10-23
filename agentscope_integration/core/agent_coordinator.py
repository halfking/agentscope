# -*- coding: utf-8 -*-
"""
智能体协调器 - 管理和协调多个专业化智能体
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from collections import defaultdict
import uuid

from ..interfaces.agent_interface import (
    ISpecializedAgent, IAgentCoordinator, AgentRole, TaskType, 
    AgentTask, TaskResult, AgentStatus, TaskStatus
)


class AgentCoordinator(IAgentCoordinator):
    """智能体协调器 - 负责管理和协调多个专业化智能体"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 智能体管理
        self.agents: Dict[str, ISpecializedAgent] = {}
        self.agent_capabilities: Dict[str, List[TaskType]] = {}
        self.agent_load: Dict[str, int] = defaultdict(int)
        
        # 任务分发策略
        self.load_balancing_enabled = True
        self.max_concurrent_tasks_per_agent = 3
        
        # 事件回调
        self.event_callback: Optional[Callable] = None
        
        # 统计信息
        self.stats = {
            "total_tasks_dispatched": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_response_time": 0.0
        }
        
        self.logger.info("AgentCoordinator initialized")
    
    async def register_agent(self, agent: ISpecializedAgent) -> bool:
        """注册智能体"""
        try:
            agent_id = agent.agent_id if hasattr(agent, 'agent_id') else str(uuid.uuid4())
            
            # 检查是否已注册
            if agent_id in self.agents:
                self.logger.warning(f"Agent {agent_id} is already registered")
                return False
            
            # 注册智能体
            self.agents[agent_id] = agent
            self.agent_capabilities[agent_id] = agent.supported_tasks
            self.agent_load[agent_id] = 0
            
            self.logger.info(f"Registered agent: {agent_id} ({agent.role.value})")
            
            # 发送事件通知
            await self._emit_event("agent_registered", {
                "agent_id": agent_id,
                "role": agent.role.value,
                "capabilities": [task.value for task in agent.supported_tasks]
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found")
                return False
            
            # 检查是否有正在执行的任务
            if self.agent_load[agent_id] > 0:
                self.logger.warning(f"Agent {agent_id} has {self.agent_load[agent_id]} running tasks")
                return False
            
            # 注销智能体
            del self.agents[agent_id]
            del self.agent_capabilities[agent_id]
            del self.agent_load[agent_id]
            
            self.logger.info(f"Unregistered agent: {agent_id}")
            
            # 发送事件通知
            await self._emit_event("agent_unregistered", {"agent_id": agent_id})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def dispatch_task(self, task: AgentTask) -> str:
        """分发任务到合适的智能体"""
        try:
            # 查找能够处理此任务的智能体
            capable_agents = self._find_capable_agents(task.type)
            
            if not capable_agents:
                raise ValueError(f"No agents available for task type: {task.type.value}")
            
            # 选择最佳智能体
            selected_agent_id = self._select_best_agent(capable_agents, task)
            
            if not selected_agent_id:
                raise ValueError("No suitable agent available")
            
            # 分发任务
            agent = self.agents[selected_agent_id]
            self.agent_load[selected_agent_id] += 1
            
            self.logger.info(f"Dispatching task {task.id} to agent {selected_agent_id}")
            
            # 异步执行任务
            asyncio.create_task(self._execute_task_async(agent, task, selected_agent_id))
            
            # 更新统计
            self.stats["total_tasks_dispatched"] += 1
            
            # 发送事件通知
            await self._emit_event("task_dispatched", {
                "task_id": task.id,
                "agent_id": selected_agent_id,
                "task_type": task.type.value
            })
            
            return task.id
            
        except Exception as e:
            self.logger.error(f"Failed to dispatch task {task.id}: {e}")
            raise
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果"""
        # 这个方法通常由TaskManager实现，这里提供基础实现
        # 在实际使用中，会与TaskManager协作
        self.logger.debug(f"Getting result for task {task_id}")
        return None
    
    async def list_agents(self) -> List[AgentStatus]:
        """列出所有智能体状态"""
        agent_statuses = []
        
        for agent_id, agent in self.agents.items():
            try:
                status = await agent.get_status()
                agent_statuses.append(status)
            except Exception as e:
                self.logger.error(f"Failed to get status for agent {agent_id}: {e}")
                # 创建错误状态
                agent_statuses.append(AgentStatus(
                    agent_id=agent_id,
                    role=agent.role,
                    status="error",
                    last_update=datetime.now(),
                    performance_metrics={}
                ))
        
        return agent_statuses
    
    def _find_capable_agents(self, task_type: TaskType) -> List[str]:
        """查找能够处理指定任务类型的智能体"""
        capable_agents = []
        
        for agent_id, capabilities in self.agent_capabilities.items():
            if task_type in capabilities:
                # 检查智能体是否可用（未超过最大并发任务数）
                if self.agent_load[agent_id] < self.max_concurrent_tasks_per_agent:
                    capable_agents.append(agent_id)
        
        return capable_agents
    
    def _select_best_agent(self, capable_agents: List[str], task: AgentTask) -> Optional[str]:
        """选择最佳智能体执行任务"""
        if not capable_agents:
            return None
        
        if not self.load_balancing_enabled:
            return capable_agents[0]
        
        # 负载均衡：选择当前负载最低的智能体
        best_agent = min(capable_agents, key=lambda agent_id: self.agent_load[agent_id])
        
        # 考虑任务优先级：高优先级任务优先分配给专门的智能体
        if task.priority <= 2:  # 高优先级任务
            # 查找专门处理此类任务的智能体
            specialized_agents = [
                agent_id for agent_id in capable_agents
                if len(self.agent_capabilities[agent_id]) == 1  # 只支持一种任务类型
            ]
            if specialized_agents:
                best_agent = min(specialized_agents, key=lambda agent_id: self.agent_load[agent_id])
        
        return best_agent
    
    async def _execute_task_async(self, agent: ISpecializedAgent, task: AgentTask, agent_id: str):
        """异步执行任务"""
        start_time = datetime.now()
        
        try:
            # 发送任务开始事件
            await self._emit_event("task_started", {
                "task_id": task.id,
                "agent_id": agent_id,
                "start_time": start_time.isoformat()
            })
            
            # 执行任务
            result = await agent.execute_task(task)
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计信息
            if result.status == TaskStatus.COMPLETED:
                self.stats["successful_tasks"] += 1
            else:
                self.stats["failed_tasks"] += 1
            
            # 更新平均响应时间
            total_tasks = self.stats["successful_tasks"] + self.stats["failed_tasks"]
            if total_tasks > 0:
                current_avg = self.stats["average_response_time"]
                self.stats["average_response_time"] = (
                    (current_avg * (total_tasks - 1) + execution_time) / total_tasks
                )
            
            # 发送任务完成事件
            await self._emit_event("task_completed", {
                "task_id": task.id,
                "agent_id": agent_id,
                "status": result.status.value,
                "execution_time": execution_time,
                "result": result.result
            })
            
            self.logger.info(f"Task {task.id} completed by agent {agent_id} in {execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Task {task.id} failed on agent {agent_id}: {e}")
            
            # 发送任务失败事件
            await self._emit_event("task_failed", {
                "task_id": task.id,
                "agent_id": agent_id,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            })
            
        finally:
            # 减少智能体负载
            self.agent_load[agent_id] = max(0, self.agent_load[agent_id] - 1)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """发送事件通知"""
        if self.event_callback:
            try:
                await self.event_callback(event_type, data)
            except Exception as e:
                self.logger.error(f"Failed to emit event {event_type}: {e}")
    
    def set_event_callback(self, callback: Callable):
        """设置事件回调函数"""
        self.event_callback = callback
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            "agents_count": len(self.agents),
            "total_load": sum(self.agent_load.values()),
            "agent_load_distribution": dict(self.agent_load),
            "task_stats": self.stats.copy(),
            "agent_capabilities": {
                agent_id: [task.value for task in capabilities]
                for agent_id, capabilities in self.agent_capabilities.items()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        healthy_agents = 0
        total_agents = len(self.agents)
        
        for agent_id, agent in self.agents.items():
            try:
                status = await agent.get_status()
                if status.status not in ["error", "failed"]:
                    healthy_agents += 1
            except Exception:
                pass
        
        health_status = "healthy" if healthy_agents == total_agents else "degraded"
        if healthy_agents == 0:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "healthy_agents": healthy_agents,
            "total_agents": total_agents,
            "health_ratio": healthy_agents / total_agents if total_agents > 0 else 0
        }
    
    async def shutdown(self):
        """关闭协调器"""
        self.logger.info("Shutting down AgentCoordinator...")
        
        # 等待所有任务完成
        max_wait_time = 30  # 最多等待30秒
        wait_interval = 1
        waited_time = 0
        
        while sum(self.agent_load.values()) > 0 and waited_time < max_wait_time:
            self.logger.info(f"Waiting for {sum(self.agent_load.values())} tasks to complete...")
            await asyncio.sleep(wait_interval)
            waited_time += wait_interval
        
        # 强制停止剩余任务
        if sum(self.agent_load.values()) > 0:
            self.logger.warning(f"Force stopping {sum(self.agent_load.values())} remaining tasks")
            for agent_id in list(self.agent_load.keys()):
                self.agent_load[agent_id] = 0
        
        # 清理资源
        self.agents.clear()
        self.agent_capabilities.clear()
        self.agent_load.clear()
        
        self.logger.info("AgentCoordinator shutdown completed")
