#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope深度集成优化方案
基于审计结果的具体实现指导
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from agentscope.agent import ReActAgent
from agentscope.message import Msg, TextBlock, ToolUseBlock
from agentscope.tool import Toolkit, ToolResponse
from agentscope.memory import InMemoryMemory, LongTermMemory
from agentscope.pipeline import MsgHub, sequential_pipeline, FanoutPipeline
from agentscope.session import Session
from agentscope.tracing import trace_toolkit
from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase


class OptimizedSpecializedAgent(ReActAgent):
    """优化的专业化智能体 - 深度集成AgentScope能力"""
    
    def __init__(
        self,
        name: str,
        role: str,
        supported_tasks: List[str],
        model: ChatModelBase,
        formatter: FormatterBase,
        **kwargs
    ):
        # 使用AgentScope标准记忆系统
        memory = InMemoryMemory()
        
        # 创建专业化工具包
        toolkit = Toolkit()
        
        super().__init__(
            name=name,
            model=model,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
            **kwargs
        )
        
        # 专业化属性
        self.role = role
        self.supported_tasks = supported_tasks
        
        # 长期记忆用于代码知识图谱
        self.long_term_memory = LongTermMemory()
        
        # 性能追踪
        self.performance_tracker = PerformanceTracker()
        
        # 注册专业化工具
        asyncio.create_task(self.register_specialized_tools())
    
    async def register_specialized_tools(self):
        """注册专业化工具到AgentScope Toolkit"""
        # 基于角色注册不同的工具
        if self.role == "code_manager":
            await self._register_code_management_tools()
        elif self.role == "compliance_auditor":
            await self._register_compliance_tools()
    
    async def _register_code_management_tools(self):
        """注册代码管理工具"""
        
        @trace_toolkit
        async def parse_code_structure(file_path: str) -> ToolResponse:
            """解析代码结构并存储到长期记忆"""
            try:
                # 解析代码
                structure = await self._parse_code_file(file_path)
                
                # 存储到长期记忆
                await self.long_term_memory.store(
                    key=f"code_structure:{file_path}",
                    value=structure,
                    metadata={"type": "code_structure", "file": file_path}
                )
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"代码结构解析完成: {json.dumps(structure, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"代码解析失败: {str(e)}")]
                )
        
        @trace_toolkit
        async def build_knowledge_graph(project_path: str) -> ToolResponse:
            """构建项目知识图谱"""
            try:
                # 构建知识图谱
                graph = await self._build_project_graph(project_path)
                
                # 存储到长期记忆
                await self.long_term_memory.store(
                    key=f"knowledge_graph:{project_path}",
                    value=graph,
                    metadata={"type": "knowledge_graph", "project": project_path}
                )
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"知识图谱构建完成，包含 {len(graph['nodes'])} 个节点"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"知识图谱构建失败: {str(e)}")]
                )
        
        # 注册工具到toolkit
        self.toolkit.register_tool_function(parse_code_structure)
        self.toolkit.register_tool_function(build_knowledge_graph)
    
    async def _register_compliance_tools(self):
        """注册合规检查工具"""
        
        @trace_toolkit
        async def security_scan(file_path: str, scan_types: List[str]) -> ToolResponse:
            """安全扫描"""
            try:
                # 执行安全扫描
                vulnerabilities = await self._perform_security_scan(file_path, scan_types)
                
                # 存储扫描结果
                await self.long_term_memory.store(
                    key=f"security_scan:{file_path}",
                    value=vulnerabilities,
                    metadata={"type": "security_scan", "file": file_path}
                )
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"安全扫描完成，发现 {len(vulnerabilities)} 个问题"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"安全扫描失败: {str(e)}")]
                )
        
        self.toolkit.register_tool_function(security_scan)
    
    async def execute_task_with_session(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """在会话中执行任务"""
        async with Session() as session:
            # 记录任务开始
            session.add_event("task_started", task)
            
            try:
                # 执行任务
                result = await self._execute_task(task)
                
                # 记录成功
                session.add_event("task_completed", {"task_id": task["id"], "result": result})
                
                return result
                
            except Exception as e:
                # 记录失败
                session.add_event("task_failed", {"task_id": task["id"], "error": str(e)})
                raise
    
    async def _parse_code_file(self, file_path: str) -> Dict[str, Any]:
        """解析代码文件"""
        # 实现代码解析逻辑
        return {"classes": [], "functions": [], "imports": []}
    
    async def _build_project_graph(self, project_path: str) -> Dict[str, Any]:
        """构建项目知识图谱"""
        # 实现知识图谱构建逻辑
        return {"nodes": [], "edges": []}
    
    async def _perform_security_scan(self, file_path: str, scan_types: List[str]) -> List[Dict]:
        """执行安全扫描"""
        # 实现安全扫描逻辑
        return []
    
    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体任务"""
        # 实现任务执行逻辑
        return {"status": "completed", "result": {}}


class AgentScopeWorkflowManager:
    """基于AgentScope Pipeline的工作流管理器"""
    
    def __init__(self):
        self.agents: Dict[str, OptimizedSpecializedAgent] = {}
        self.active_hubs: Dict[str, MsgHub] = {}
        self.session_manager = SessionManager()
    
    async def register_agent(self, agent: OptimizedSpecializedAgent):
        """注册智能体"""
        self.agents[agent.name] = agent
    
    async def create_analysis_workflow(self, task: Dict[str, Any]) -> str:
        """创建分析工作流"""
        task_type = task.get("type")
        
        if task_type == "comprehensive_analysis":
            return await self._create_comprehensive_workflow(task)
        elif task_type == "security_focused":
            return await self._create_security_workflow(task)
        elif task_type == "quality_focused":
            return await self._create_quality_workflow(task)
        else:
            return await self._create_default_workflow(task)
    
    async def _create_comprehensive_workflow(self, task: Dict[str, Any]) -> str:
        """创建综合分析工作流"""
        # 选择参与的智能体
        participants = [
            self.agents["code_manager"],
            self.agents["compliance_auditor"]
        ]
        
        # 创建消息中心
        hub_id = f"workflow_{task['id']}"
        
        async with MsgHub(participants=participants) as hub:
            self.active_hubs[hub_id] = hub
            
            # 创建初始消息
            initial_msg = Msg(
                name="WorkflowManager",
                content=f"开始综合分析任务: {task['description']}",
                role="system"
            )
            
            # 广播任务开始消息
            await hub.broadcast(initial_msg)
            
            # 执行顺序分析流程
            results = await sequential_pipeline(participants)
            
            return hub_id
    
    async def _create_security_workflow(self, task: Dict[str, Any]) -> str:
        """创建安全分析工作流"""
        # 主要使用合规审核智能体
        participants = [self.agents["compliance_auditor"]]
        
        # 如果需要代码结构信息，也包含代码管理智能体
        if task.get("include_structure_analysis"):
            participants.insert(0, self.agents["code_manager"])
        
        hub_id = f"security_workflow_{task['id']}"
        
        async with MsgHub(participants=participants) as hub:
            self.active_hubs[hub_id] = hub
            
            # 创建安全分析消息
            security_msg = Msg(
                name="SecurityWorkflow",
                content=f"执行安全扫描: {task['parameters']}",
                role="system"
            )
            
            await hub.broadcast(security_msg)
            
            # 如果是多智能体，使用顺序流程
            if len(participants) > 1:
                await sequential_pipeline(participants)
            else:
                # 单智能体直接执行
                await participants[0].reply(security_msg)
            
            return hub_id
    
    async def _create_quality_workflow(self, task: Dict[str, Any]) -> str:
        """创建质量检查工作流"""
        participants = [
            self.agents["code_manager"],
            self.agents["compliance_auditor"]
        ]
        
        hub_id = f"quality_workflow_{task['id']}"
        
        # 使用并行流程进行质量检查
        async with MsgHub(participants=participants) as hub:
            self.active_hubs[hub_id] = hub
            
            quality_msg = Msg(
                name="QualityWorkflow",
                content=f"执行质量检查: {task['parameters']}",
                role="system"
            )
            
            await hub.broadcast(quality_msg)
            
            # 使用扇出流程并行执行
            fanout = FanoutPipeline(participants)
            await fanout.run(quality_msg)
            
            return hub_id
    
    async def _create_default_workflow(self, task: Dict[str, Any]) -> str:
        """创建默认工作流"""
        # 选择最适合的智能体
        best_agent = self._select_best_agent(task)
        
        hub_id = f"default_workflow_{task['id']}"
        
        async with MsgHub(participants=[best_agent]) as hub:
            self.active_hubs[hub_id] = hub
            
            task_msg = Msg(
                name="DefaultWorkflow",
                content=f"执行任务: {task['description']}",
                role="system"
            )
            
            result = await best_agent.reply(task_msg)
            
            return hub_id
    
    def _select_best_agent(self, task: Dict[str, Any]) -> OptimizedSpecializedAgent:
        """选择最适合的智能体"""
        task_type = task.get("type", "")
        
        if "security" in task_type or "compliance" in task_type:
            return self.agents["compliance_auditor"]
        elif "code" in task_type or "structure" in task_type:
            return self.agents["code_manager"]
        else:
            # 默认返回代码管理智能体
            return self.agents["code_manager"]
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流状态"""
        if workflow_id in self.active_hubs:
            hub = self.active_hubs[workflow_id]
            return {
                "status": "active",
                "participants": [agent.name for agent in hub.participants],
                "message_count": len(hub.message_history) if hasattr(hub, 'message_history') else 0
            }
        else:
            return {"status": "completed_or_not_found"}


class PerformanceTracker:
    """性能追踪器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_tracking(self, operation: str):
        """开始追踪操作"""
        import time
        self.start_times[operation] = time.time()
    
    def end_tracking(self, operation: str):
        """结束追踪操作"""
        import time
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


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.active_sessions = {}
    
    async def create_session(self, session_id: str) -> Session:
        """创建新会话"""
        session = Session()
        self.active_sessions[session_id] = session
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.active_sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """关闭会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


# 使用示例
async def example_optimized_workflow():
    """优化工作流使用示例"""
    
    # 创建工作流管理器
    workflow_manager = AgentScopeWorkflowManager()
    
    # 创建优化的智能体
    from agentscope.model import OpenAIModel
    from agentscope.formatter import JSONFormatter
    
    model = OpenAIModel(model_name="gpt-4")
    formatter = JSONFormatter()
    
    code_manager = OptimizedSpecializedAgent(
        name="CodeManager",
        role="code_manager",
        supported_tasks=["code_analysis", "structure_analysis"],
        model=model,
        formatter=formatter
    )
    
    compliance_auditor = OptimizedSpecializedAgent(
        name="ComplianceAuditor", 
        role="compliance_auditor",
        supported_tasks=["security_scan", "quality_check"],
        model=model,
        formatter=formatter
    )
    
    # 注册智能体
    await workflow_manager.register_agent(code_manager)
    await workflow_manager.register_agent(compliance_auditor)
    
    # 创建分析任务
    task = {
        "id": "task_001",
        "type": "comprehensive_analysis",
        "description": "分析项目代码质量和安全性",
        "parameters": {
            "project_path": "/path/to/project",
            "include_security": True,
            "include_quality": True
        }
    }
    
    # 执行工作流
    workflow_id = await workflow_manager.create_analysis_workflow(task)
    
    # 监控工作流状态
    status = await workflow_manager.get_workflow_status(workflow_id)
    print(f"工作流状态: {status}")


if __name__ == "__main__":
    asyncio.run(example_optimized_workflow())
