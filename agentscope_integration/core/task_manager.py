# -*- coding: utf-8 -*-
"""
任务管理器 - 管理任务的生命周期、队列和结果
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import json

from ..interfaces.agent_interface import (
    AgentTask, TaskResult, TaskType, TaskStatus
)
from .agent_coordinator import AgentCoordinator


class TaskPriority(int, Enum):
    """任务优先级"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 5
    LOW = 7


class TaskManager:
    """任务管理器 - 负责任务的创建、调度、执行和结果管理"""
    
    def __init__(self, agent_coordinator: AgentCoordinator):
        self.logger = logging.getLogger(__name__)
        self.agent_coordinator = agent_coordinator
        
        # 任务存储
        self.pending_tasks: deque = deque()  # 待处理任务队列
        self.running_tasks: Dict[str, AgentTask] = {}  # 正在执行的任务
        self.completed_tasks: Dict[str, TaskResult] = {}  # 已完成的任务
        self.task_history: List[AgentTask] = []  # 任务历史
        
        # 任务调度配置
        self.max_concurrent_tasks = 10
        self.task_timeout = 300  # 5分钟超时
        self.cleanup_interval = 3600  # 1小时清理一次历史
        self.max_history_size = 1000
        
        # 事件回调
        self.event_callback: Optional[Callable] = None
        
        # 调度器状态
        self.scheduler_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.stats = {
            "total_tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_timeout": 0,
            "average_queue_time": 0.0,
            "average_execution_time": 0.0
        }
        
        self.logger.info("TaskManager initialized")
    
    async def start(self):
        """启动任务管理器"""
        if self.scheduler_running:
            self.logger.warning("TaskManager is already running")
            return
        
        self.scheduler_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # 启动清理任务
        asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("TaskManager started")
    
    async def stop(self):
        """停止任务管理器"""
        self.scheduler_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("TaskManager stopped")
    
    async def create_task(
        self,
        task_type: TaskType,
        title: str,
        description: str,
        parameters: Dict[str, Any],
        priority: int = TaskPriority.NORMAL,
        timeout: Optional[int] = None
    ) -> str:
        """创建新任务"""
        try:
            task_id = str(uuid.uuid4())
            
            task = AgentTask(
                id=task_id,
                type=task_type,
                title=title,
                description=description,
                parameters=parameters,
                priority=priority,
                timeout=timeout or self.task_timeout,
                created_at=datetime.now()
            )
            
            # 添加到队列
            self._add_task_to_queue(task)
            
            # 更新统计
            self.stats["total_tasks_created"] += 1
            
            # 记录历史
            self.task_history.append(task)
            
            self.logger.info(f"Created task {task_id}: {title}")
            
            # 发送事件
            await self._emit_event("task_created", {
                "task_id": task_id,
                "type": task_type.value,
                "title": title,
                "priority": priority
            })
            
            return task_id
            
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise
    
    def _add_task_to_queue(self, task: AgentTask):
        """将任务添加到队列（按优先级排序）"""
        # 找到合适的插入位置（优先级越小越靠前）
        inserted = False
        for i, existing_task in enumerate(self.pending_tasks):
            if task.priority < existing_task.priority:
                self.pending_tasks.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.pending_tasks.append(task)
    
    async def _scheduler_loop(self):
        """任务调度循环"""
        while self.scheduler_running:
            try:
                await self._process_pending_tasks()
                await self._check_running_tasks()
                await asyncio.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)  # 出错时等待5秒
    
    async def _process_pending_tasks(self):
        """处理待处理任务"""
        while (len(self.running_tasks) < self.max_concurrent_tasks and 
               len(self.pending_tasks) > 0):
            
            task = self.pending_tasks.popleft()
            
            try:
                # 分发任务给智能体协调器
                await self.agent_coordinator.dispatch_task(task)
                
                # 移动到运行中任务
                self.running_tasks[task.id] = task
                
                # 计算队列等待时间
                queue_time = (datetime.now() - task.created_at).total_seconds()
                self._update_average_queue_time(queue_time)
                
                self.logger.debug(f"Dispatched task {task.id} after {queue_time:.2f}s in queue")
                
                # 发送事件
                await self._emit_event("task_started", {
                    "task_id": task.id,
                    "queue_time": queue_time
                })
                
            except Exception as e:
                self.logger.error(f"Failed to dispatch task {task.id}: {e}")
                
                # 创建失败结果
                result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    error=f"Dispatch failed: {str(e)}",
                    completed_at=datetime.now()
                )
                
                await self._handle_task_completion(task, result)
    
    async def _check_running_tasks(self):
        """检查运行中的任务（超时处理）"""
        current_time = datetime.now()
        timeout_tasks = []
        
        for task_id, task in self.running_tasks.items():
            # 检查任务是否超时
            if task.timeout and (current_time - task.created_at).total_seconds() > task.timeout:
                timeout_tasks.append(task)
        
        # 处理超时任务
        for task in timeout_tasks:
            self.logger.warning(f"Task {task.id} timed out after {task.timeout}s")
            
            # 尝试取消任务
            try:
                # 这里需要与智能体协调器配合取消任务
                # 暂时创建超时结果
                result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    error="Task timeout",
                    execution_time=task.timeout,
                    completed_at=current_time
                )
                
                await self._handle_task_completion(task, result)
                self.stats["tasks_timeout"] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to handle timeout for task {task.id}: {e}")
    
    async def handle_task_result(self, task_id: str, result: TaskResult):
        """处理任务结果（由智能体协调器调用）"""
        if task_id not in self.running_tasks:
            self.logger.warning(f"Received result for unknown task: {task_id}")
            return
        
        task = self.running_tasks[task_id]
        await self._handle_task_completion(task, result)
    
    async def _handle_task_completion(self, task: AgentTask, result: TaskResult):
        """处理任务完成"""
        try:
            # 从运行中任务移除
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            
            # 添加到完成任务
            self.completed_tasks[task.id] = result
            
            # 更新统计
            if result.status == TaskStatus.COMPLETED:
                self.stats["tasks_completed"] += 1
            else:
                self.stats["tasks_failed"] += 1
            
            # 更新平均执行时间
            if result.execution_time:
                self._update_average_execution_time(result.execution_time)
            
            self.logger.info(f"Task {task.id} completed with status: {result.status.value}")
            
            # 发送事件
            await self._emit_event("task_completed", {
                "task_id": task.id,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "error": result.error
            })
            
        except Exception as e:
            self.logger.error(f"Failed to handle task completion for {task.id}: {e}")
    
    def _update_average_queue_time(self, queue_time: float):
        """更新平均队列等待时间"""
        current_avg = self.stats["average_queue_time"]
        total_tasks = self.stats["total_tasks_created"]
        
        if total_tasks > 0:
            self.stats["average_queue_time"] = (
                (current_avg * (total_tasks - 1) + queue_time) / total_tasks
            )
    
    def _update_average_execution_time(self, execution_time: float):
        """更新平均执行时间"""
        current_avg = self.stats["average_execution_time"]
        completed_tasks = self.stats["tasks_completed"] + self.stats["tasks_failed"]
        
        if completed_tasks > 0:
            self.stats["average_execution_time"] = (
                (current_avg * (completed_tasks - 1) + execution_time) / completed_tasks
            )
    
    async def _cleanup_loop(self):
        """清理循环 - 定期清理历史数据"""
        while self.scheduler_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_history()
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_history(self):
        """清理历史数据"""
        # 清理过期的完成任务
        cutoff_time = datetime.now() - timedelta(hours=24)  # 保留24小时
        
        expired_tasks = [
            task_id for task_id, result in self.completed_tasks.items()
            if result.completed_at and result.completed_at < cutoff_time
        ]
        
        for task_id in expired_tasks:
            del self.completed_tasks[task_id]
        
        # 限制历史大小
        if len(self.task_history) > self.max_history_size:
            self.task_history = self.task_history[-self.max_history_size:]
        
        if expired_tasks:
            self.logger.info(f"Cleaned up {len(expired_tasks)} expired task results")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查待处理队列
        for task in self.pending_tasks:
            if task.id == task_id:
                return {
                    "task_id": task_id,
                    "status": "pending",
                    "created_at": task.created_at.isoformat(),
                    "queue_position": list(self.pending_tasks).index(task) + 1
                }
        
        # 检查运行中任务
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "running",
                "created_at": task.created_at.isoformat(),
                "running_time": (datetime.now() - task.created_at).total_seconds()
            }
        
        # 检查完成任务
        if task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": result.status.value,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "execution_time": result.execution_time,
                "error": result.error
            }
        
        return None
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果"""
        return self.completed_tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            # 检查待处理队列
            for i, task in enumerate(self.pending_tasks):
                if task.id == task_id:
                    del self.pending_tasks[i]
                    
                    # 创建取消结果
                    result = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.CANCELLED,
                        completed_at=datetime.now()
                    )
                    self.completed_tasks[task_id] = result
                    
                    await self._emit_event("task_cancelled", {"task_id": task_id})
                    return True
            
            # 检查运行中任务
            if task_id in self.running_tasks:
                # 通知智能体协调器取消任务
                # 这里需要实现与智能体的取消通信
                self.logger.info(f"Requesting cancellation of running task {task_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "pending_tasks": len(self.pending_tasks),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "queue_utilization": len(self.running_tasks) / self.max_concurrent_tasks,
            "stats": self.stats.copy()
        }
    
    async def get_task_list(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取任务列表"""
        tasks = []
        
        if status is None or status == "pending":
            for task in list(self.pending_tasks)[:limit]:
                tasks.append({
                    "task_id": task.id,
                    "type": task.type.value,
                    "title": task.title,
                    "status": "pending",
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat()
                })
        
        if status is None or status == "running":
            for task in list(self.running_tasks.values())[:limit]:
                tasks.append({
                    "task_id": task.id,
                    "type": task.type.value,
                    "title": task.title,
                    "status": "running",
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat()
                })
        
        if status is None or status == "completed":
            for task_id, result in list(self.completed_tasks.items())[:limit]:
                # 从历史中找到原始任务信息
                task_info = next((t for t in self.task_history if t.id == task_id), None)
                if task_info:
                    tasks.append({
                        "task_id": task_id,
                        "type": task_info.type.value,
                        "title": task_info.title,
                        "status": result.status.value,
                        "priority": task_info.priority,
                        "created_at": task_info.created_at.isoformat(),
                        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                        "execution_time": result.execution_time
                    })
        
        # 按创建时间排序
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return tasks[:limit]
    
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
    
    async def shutdown(self):
        """关闭任务管理器"""
        self.logger.info("Shutting down TaskManager...")
        
        await self.stop()
        
        # 取消所有待处理任务
        while self.pending_tasks:
            task = self.pending_tasks.popleft()
            result = TaskResult(
                task_id=task.id,
                status=TaskStatus.CANCELLED,
                error="System shutdown",
                completed_at=datetime.now()
            )
            self.completed_tasks[task.id] = result
        
        self.logger.info("TaskManager shutdown completed")
