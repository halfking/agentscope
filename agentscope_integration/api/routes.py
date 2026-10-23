# -*- coding: utf-8 -*-
"""
API路由模块 - 定义所有REST API端点
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ..core.agent_coordinator import AgentCoordinator
from ..core.task_manager import TaskManager
from ..mcp.mcp_manager import MCPManager
from ..interfaces.agent_interface import TaskType, TaskStatus


# Pydantic模型定义
class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    type: str = Field(..., description="任务类型")
    title: str = Field(..., description="任务标题")
    description: str = Field("", description="任务描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    priority: int = Field(5, ge=1, le=10, description="任务优先级(1-10)")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str


class AgentStatusResponse(BaseModel):
    """智能体状态响应"""
    agent_id: str
    role: str
    status: str
    current_task: Optional[str]
    last_update: str
    performance_metrics: Dict[str, float]


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    created_at: str
    completed_at: Optional[str]
    execution_time: Optional[float]
    error: Optional[str]
    result: Optional[Dict[str, Any]]


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    agents_count: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_response_time: float
    system_uptime: str


def create_api_router(
    agent_coordinator: AgentCoordinator,
    task_manager: TaskManager,
    mcp_manager: MCPManager
) -> APIRouter:
    """创建API路由器"""
    
    router = APIRouter()
    
    # 智能体相关端点
    @router.get("/agents", response_model=List[AgentStatusResponse])
    async def get_agents():
        """获取所有智能体状态"""
        try:
            agent_statuses = await agent_coordinator.list_agents()
            return [
                AgentStatusResponse(
                    agent_id=status.agent_id,
                    role=status.role.value,
                    status=status.status,
                    current_task=status.current_task,
                    last_update=status.last_update.isoformat(),
                    performance_metrics=status.performance_metrics
                )
                for status in agent_statuses
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")
    
    @router.get("/agents/{agent_id}")
    async def get_agent_status(agent_id: str):
        """获取指定智能体状态"""
        try:
            agent_statuses = await agent_coordinator.list_agents()
            for status in agent_statuses:
                if status.agent_id == agent_id:
                    return AgentStatusResponse(
                        agent_id=status.agent_id,
                        role=status.role.value,
                        status=status.status,
                        current_task=status.current_task,
                        last_update=status.last_update.isoformat(),
                        performance_metrics=status.performance_metrics
                    )
            raise HTTPException(status_code=404, detail="Agent not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")
    
    # 任务相关端点
    @router.post("/tasks", response_model=TaskResponse)
    async def create_task(request: TaskCreateRequest):
        """创建新任务"""
        try:
            # 验证任务类型
            try:
                task_type = TaskType(request.type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid task type: {request.type}")
            
            # 创建任务
            task_id = await task_manager.create_task(
                task_type=task_type,
                title=request.title,
                description=request.description,
                parameters=request.parameters,
                priority=request.priority,
                timeout=request.timeout
            )
            
            return TaskResponse(
                task_id=task_id,
                status="created",
                message="Task created successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
    
    @router.get("/tasks", response_model=List[Dict[str, Any]])
    async def get_tasks(
        status: Optional[str] = Query(None, description="任务状态过滤"),
        limit: int = Query(50, ge=1, le=200, description="返回数量限制")
    ):
        """获取任务列表"""
        try:
            tasks = await task_manager.get_task_list(status=status, limit=limit)
            return tasks
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")
    
    @router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
    async def get_task_status(task_id: str):
        """获取任务状态"""
        try:
            task_status = await task_manager.get_task_status(task_id)
            if not task_status:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return TaskStatusResponse(**task_status)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")
    
    @router.get("/tasks/{task_id}/result")
    async def get_task_result(task_id: str):
        """获取任务结果"""
        try:
            result = await task_manager.get_task_result(task_id)
            if not result:
                raise HTTPException(status_code=404, detail="Task result not found")
            
            return {
                "task_id": task_id,
                "status": result.status.value,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "artifacts": result.artifacts
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get task result: {str(e)}")
    
    @router.delete("/tasks/{task_id}")
    async def cancel_task(task_id: str):
        """取消任务"""
        try:
            success = await task_manager.cancel_task(task_id)
            if not success:
                raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
            
            return {"message": "Task cancelled successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")
    
    # 队列状态端点
    @router.get("/queue/status")
    async def get_queue_status():
        """获取任务队列状态"""
        try:
            return await task_manager.get_queue_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")
    
    # MCP相关端点
    @router.get("/mcp/servers")
    async def get_mcp_servers():
        """获取MCP服务器列表"""
        try:
            return await mcp_manager.get_all_servers_info()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get MCP servers: {str(e)}")
    
    @router.get("/mcp/servers/{server_name}")
    async def get_mcp_server_info(server_name: str):
        """获取指定MCP服务器信息"""
        try:
            server_info = await mcp_manager.get_server_info(server_name)
            if not server_info:
                raise HTTPException(status_code=404, detail="MCP server not found")
            return server_info
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get MCP server info: {str(e)}")
    
    @router.get("/mcp/servers/{server_name}/tools")
    async def get_mcp_server_tools(server_name: str):
        """获取MCP服务器工具列表"""
        try:
            tools = await mcp_manager.list_mcp_tools(server_name)
            return {"server_name": server_name, "tools": tools}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get MCP tools: {str(e)}")
    
    @router.post("/mcp/servers/{server_name}/tools/{tool_name}")
    async def call_mcp_tool(
        server_name: str,
        tool_name: str,
        parameters: Dict[str, Any] = Body(default_factory=dict)
    ):
        """调用MCP工具"""
        try:
            result = await mcp_manager.call_mcp_tool(server_name, tool_name, **parameters)
            return {
                "server_name": server_name,
                "tool_name": tool_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to call MCP tool: {str(e)}")
    
    @router.post("/mcp/servers/{server_name}/reload")
    async def reload_mcp_server(server_name: str):
        """重新加载MCP服务器"""
        try:
            success = await mcp_manager.reload_server(server_name)
            if not success:
                raise HTTPException(status_code=404, detail="MCP server not found or failed to reload")
            return {"message": f"MCP server {server_name} reloaded successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to reload MCP server: {str(e)}")
    
    # 系统统计端点
    @router.get("/stats", response_model=SystemStatsResponse)
    async def get_system_stats():
        """获取系统统计信息"""
        try:
            agent_stats = await agent_coordinator.get_system_stats()
            queue_stats = await task_manager.get_queue_status()
            
            return SystemStatsResponse(
                agents_count=agent_stats["agents_count"],
                active_tasks=queue_stats["running_tasks"],
                completed_tasks=queue_stats["stats"]["tasks_completed"],
                failed_tasks=queue_stats["stats"]["tasks_failed"],
                average_response_time=agent_stats["task_stats"]["average_response_time"],
                system_uptime="N/A"  # 可以添加系统启动时间跟踪
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")
    
    # 健康检查端点
    @router.get("/health")
    async def health_check():
        """系统健康检查"""
        try:
            agent_health = await agent_coordinator.health_check()
            queue_status = await task_manager.get_queue_status()
            
            overall_status = "healthy"
            if agent_health["status"] != "healthy":
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "agents": agent_health,
                    "task_queue": {
                        "status": "healthy" if queue_status["pending_tasks"] < 100 else "warning",
                        "pending_tasks": queue_status["pending_tasks"],
                        "running_tasks": queue_status["running_tasks"]
                    },
                    "mcp_servers": {
                        "status": "healthy",  # 可以添加MCP健康检查
                        "active_servers": len(mcp_manager.clients)
                    }
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    # 快捷操作端点
    @router.post("/actions/analyze-project")
    async def analyze_project(
        project_path: str = Body(..., embed=True),
        analysis_type: str = Body("comprehensive", embed=True)
    ):
        """快捷项目分析"""
        try:
            task_id = await task_manager.create_task(
                task_type=TaskType.CODE_ANALYSIS,
                title=f"Project Analysis: {project_path}",
                description=f"Comprehensive analysis of project at {project_path}",
                parameters={
                    "project_path": project_path,
                    "analysis_type": analysis_type
                },
                priority=3
            )
            
            return TaskResponse(
                task_id=task_id,
                status="created",
                message="Project analysis task created"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create analysis task: {str(e)}")
    
    @router.post("/actions/quality-check")
    async def quality_check(
        file_path: str = Body(..., embed=True),
        check_types: List[str] = Body(["static_analysis", "coding_standards"], embed=True)
    ):
        """快捷质量检查"""
        try:
            task_id = await task_manager.create_task(
                task_type=TaskType.QUALITY_CHECK,
                title=f"Quality Check: {file_path}",
                description=f"Quality analysis for {file_path}",
                parameters={
                    "file_path": file_path,
                    "check_types": check_types
                },
                priority=3
            )
            
            return TaskResponse(
                task_id=task_id,
                status="created",
                message="Quality check task created"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create quality check task: {str(e)}")
    
    @router.post("/actions/security-scan")
    async def security_scan(
        file_path: str = Body(..., embed=True),
        scan_types: List[str] = Body(["vulnerability_scan", "secret_detection"], embed=True)
    ):
        """快捷安全扫描"""
        try:
            task_id = await task_manager.create_task(
                task_type=TaskType.SECURITY_SCAN,
                title=f"Security Scan: {file_path}",
                description=f"Security vulnerability scan for {file_path}",
                parameters={
                    "file_path": file_path,
                    "scan_types": scan_types
                },
                priority=1  # 安全扫描高优先级
            )
            
            return TaskResponse(
                task_id=task_id,
                status="created",
                message="Security scan task created"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create security scan task: {str(e)}")
    
    return router
