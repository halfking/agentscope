#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope工作流管理器 - 使用MsgHub和Pipeline替代自定义TaskManager
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import shortuuid

from agentscope.pipeline import MsgHub, sequential_pipeline, FanoutPipeline
from agentscope.message import Msg
from agentscope.session import JSONSession

from ..interfaces.agent_interface import (
    ISpecializedAgent, AgentTask, TaskResult, TaskType, TaskStatus
)
from ..agents.base_specialized_agent import OptimizedSpecializedAgent


class WorkflowType:
    """工作流类型定义"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    HYBRID = "hybrid"


class AgentScopeWorkflowManager:
    """基于AgentScope Pipeline的工作流管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, OptimizedSpecializedAgent] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
        # 工作流模板
        self.workflow_templates = {
            TaskType.CODE_ANALYSIS: {
                "type": WorkflowType.SEQUENTIAL,
                "agents": ["code_manager"],
                "description": "代码分析工作流"
            },
            TaskType.SECURITY_SCAN: {
                "type": WorkflowType.SEQUENTIAL,
                "agents": ["code_manager", "compliance_auditor"],
                "description": "安全扫描工作流"
            },
            TaskType.QUALITY_CHECK: {
                "type": WorkflowType.PARALLEL,
                "agents": ["code_manager", "compliance_auditor"],
                "description": "质量检查工作流"
            },
            TaskType.COMPREHENSIVE_ANALYSIS: {
                "type": WorkflowType.HYBRID,
                "agents": ["code_manager", "compliance_auditor"],
                "description": "综合分析工作流"
            }
        }
        
        self.logger.info("AgentScope workflow manager initialized")
    
    async def register_agent(self, agent: OptimizedSpecializedAgent):
        """注册智能体"""
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name} ({agent.role.value})")
    
    async def create_workflow(self, task: AgentTask) -> str:
        """创建工作流"""
        workflow_id = f"workflow_{shortuuid.uuid()}"
        
        try:
            # 获取工作流模板
            template = self.workflow_templates.get(task.type)
            if not template:
                template = self.workflow_templates[TaskType.CODE_ANALYSIS]  # 默认模板
            
            # 选择参与的智能体
            participants = self._select_workflow_agents(task, template)
            
            if not participants:
                raise ValueError(f"No suitable agents found for task type: {task.type}")
            
            # 创建工作流配置
            workflow_config = {
                "id": workflow_id,
                "task": task,
                "template": template,
                "participants": participants,
                "status": "created",
                "created_at": datetime.now(),
                "session_id": None
            }
            
            # 根据工作流类型执行
            if template["type"] == WorkflowType.SEQUENTIAL:
                result = await self._execute_sequential_workflow(workflow_config)
            elif template["type"] == WorkflowType.PARALLEL:
                result = await self._execute_parallel_workflow(workflow_config)
            elif template["type"] == WorkflowType.HYBRID:
                result = await self._execute_hybrid_workflow(workflow_config)
            else:
                result = await self._execute_sequential_workflow(workflow_config)  # 默认
            
            # 更新工作流状态
            workflow_config["status"] = "completed"
            workflow_config["result"] = result
            workflow_config["completed_at"] = datetime.now()
            
            # 记录历史
            self.workflow_history.append(workflow_config)
            
            return workflow_id
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {e}")
            
            # 记录失败的工作流
            failed_config = {
                "id": workflow_id,
                "task": task,
                "status": "failed",
                "error": str(e),
                "created_at": datetime.now(),
                "failed_at": datetime.now()
            }
            self.workflow_history.append(failed_config)
            
            raise
    
    def _select_workflow_agents(self, task: AgentTask, template: Dict[str, Any]) -> List[OptimizedSpecializedAgent]:
        """选择工作流智能体"""
        participants = []
        
        for agent_name in template["agents"]:
            # 根据角色名称查找智能体
            agent = None
            for registered_agent in self.agents.values():
                if (agent_name == "code_manager" and registered_agent.role.value == "code_manager") or \
                   (agent_name == "compliance_auditor" and registered_agent.role.value == "compliance_auditor"):
                    agent = registered_agent
                    break
            
            if agent and task.type in agent.supported_tasks:
                participants.append(agent)
        
        return participants
    
    async def _execute_sequential_workflow(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行顺序工作流"""
        task = config["task"]
        participants = config["participants"]
        
        self.logger.info(f"Executing sequential workflow for task {task.id}")
        
        async with JSONSession() as session:
            config["session_id"] = session.session_id
            
            # 记录工作流开始
            session.add_event("workflow_started", {
                "workflow_id": config["id"],
                "task_id": task.id,
                "participants": [agent.name for agent in participants]
            })
            
            async with MsgHub(participants=participants) as hub:
                # 创建初始消息
                initial_msg = Msg(
                    name="WorkflowManager",
                    content=f"开始执行任务: {task.title}\n描述: {task.description}",
                    role="system"
                )
                
                # 广播任务开始消息
                await hub.broadcast(initial_msg)
                
                # 执行顺序流程
                results = []
                for agent in participants:
                    try:
                        result = await agent.execute_task_with_session(task)
                        results.append({
                            "agent": agent.name,
                            "result": result.to_dict()
                        })
                        
                        # 如果任务失败，停止后续执行
                        if result.status == TaskStatus.FAILED:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Agent {agent.name} failed: {e}")
                        results.append({
                            "agent": agent.name,
                            "error": str(e)
                        })
                        break
                
                # 记录工作流完成
                session.add_event("workflow_completed", {
                    "workflow_id": config["id"],
                    "results_count": len(results)
                })
                
                return {
                    "workflow_type": "sequential",
                    "results": results,
                    "session_id": session.session_id
                }
    
    async def _execute_parallel_workflow(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行并行工作流"""
        task = config["task"]
        participants = config["participants"]
        
        self.logger.info(f"Executing parallel workflow for task {task.id}")
        
        async with JSONSession() as session:
            config["session_id"] = session.session_id
            
            session.add_event("workflow_started", {
                "workflow_id": config["id"],
                "task_id": task.id,
                "participants": [agent.name for agent in participants]
            })
            
            async with MsgHub(participants=participants) as hub:
                # 创建初始消息
                initial_msg = Msg(
                    name="WorkflowManager",
                    content=f"开始并行执行任务: {task.title}\n描述: {task.description}",
                    role="system"
                )
                
                # 广播任务开始消息
                await hub.broadcast(initial_msg)
                
                # 使用扇出流程并行执行
                fanout = FanoutPipeline(participants)
                
                # 并行执行所有智能体
                tasks_coroutines = [
                    agent.execute_task_with_session(task) 
                    for agent in participants
                ]
                
                results = []
                try:
                    task_results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
                    
                    for i, result in enumerate(task_results):
                        agent = participants[i]
                        if isinstance(result, Exception):
                            results.append({
                                "agent": agent.name,
                                "error": str(result)
                            })
                        else:
                            results.append({
                                "agent": agent.name,
                                "result": result.to_dict()
                            })
                
                except Exception as e:
                    self.logger.error(f"Parallel workflow execution failed: {e}")
                    raise
                
                session.add_event("workflow_completed", {
                    "workflow_id": config["id"],
                    "results_count": len(results)
                })
                
                return {
                    "workflow_type": "parallel",
                    "results": results,
                    "session_id": session.session_id
                }
    
    async def _execute_hybrid_workflow(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行混合工作流 - 先代码分析，再并行质量和安全检查"""
        task = config["task"]
        participants = config["participants"]
        
        self.logger.info(f"Executing hybrid workflow for task {task.id}")
        
        # 分离智能体
        code_managers = [a for a in participants if a.role.value == "code_manager"]
        auditors = [a for a in participants if a.role.value == "compliance_auditor"]
        
        async with JSONSession() as session:
            config["session_id"] = session.session_id
            
            session.add_event("workflow_started", {
                "workflow_id": config["id"],
                "task_id": task.id,
                "workflow_type": "hybrid"
            })
            
            results = []
            
            # 第一阶段：代码结构分析
            if code_managers:
                self.logger.info("Phase 1: Code structure analysis")
                for manager in code_managers:
                    try:
                        result = await manager.execute_task_with_session(task)
                        results.append({
                            "agent": manager.name,
                            "phase": "structure_analysis",
                            "result": result.to_dict()
                        })
                    except Exception as e:
                        results.append({
                            "agent": manager.name,
                            "phase": "structure_analysis",
                            "error": str(e)
                        })
            
            # 第二阶段：并行质量和安全检查
            if auditors:
                self.logger.info("Phase 2: Parallel quality and security checks")
                audit_tasks = [
                    auditor.execute_task_with_session(task) 
                    for auditor in auditors
                ]
                
                try:
                    audit_results = await asyncio.gather(*audit_tasks, return_exceptions=True)
                    
                    for i, result in enumerate(audit_results):
                        auditor = auditors[i]
                        if isinstance(result, Exception):
                            results.append({
                                "agent": auditor.name,
                                "phase": "audit",
                                "error": str(result)
                            })
                        else:
                            results.append({
                                "agent": auditor.name,
                                "phase": "audit",
                                "result": result.to_dict()
                            })
                
                except Exception as e:
                    self.logger.error(f"Audit phase failed: {e}")
            
            session.add_event("workflow_completed", {
                "workflow_id": config["id"],
                "results_count": len(results)
            })
            
            return {
                "workflow_type": "hybrid",
                "results": results,
                "session_id": session.session_id
            }
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # 在历史记录中查找
        for workflow in self.workflow_history:
            if workflow["id"] == workflow_id:
                return workflow
        
        return None
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            
            # 取消所有参与的智能体任务
            for agent in workflow.get("participants", []):
                if hasattr(agent, "cancel_current_task"):
                    await agent.cancel_current_task()
            
            # 更新状态
            workflow["status"] = "cancelled"
            workflow["cancelled_at"] = datetime.now()
            
            # 移动到历史记录
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
            
            return True
        
        return False
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """获取工作流统计信息"""
        total_workflows = len(self.workflow_history)
        completed = len([w for w in self.workflow_history if w["status"] == "completed"])
        failed = len([w for w in self.workflow_history if w["status"] == "failed"])
        cancelled = len([w for w in self.workflow_history if w["status"] == "cancelled"])
        
        return {
            "total_workflows": total_workflows,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "success_rate": (completed / total_workflows * 100) if total_workflows > 0 else 0,
            "active_workflows": len(self.active_workflows)
        }
