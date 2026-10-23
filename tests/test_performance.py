# -*- coding: utf-8 -*-
"""
性能测试和压力测试
"""

import pytest
import asyncio
import time
import statistics
import concurrent.futures
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from agentscope_integration.core.agent_coordinator import AgentCoordinator
from agentscope_integration.core.task_manager import TaskManager
from agentscope_integration.core.websocket_manager import WebSocketManager
from agentscope_integration.interfaces.agent_interface import (
    AgentTask, TaskType, TaskStatus, AgentRole
)


class MockAgent:
    """模拟智能体用于性能测试"""
    
    def __init__(self, agent_id: str, role: AgentRole, execution_time: float = 1.0):
        self.agent_id = agent_id
        self.role = role
        self.supported_tasks = [TaskType.CODE_ANALYSIS, TaskType.QUALITY_CHECK]
        self.execution_time = execution_time
        self._task_count = 0
    
    async def execute_task(self, task: AgentTask):
        """模拟任务执行"""
        start_time = time.time()
        
        # 模拟执行时间
        await asyncio.sleep(self.execution_time)
        
        self._task_count += 1
        execution_time = time.time() - start_time
        
        from agentscope_integration.interfaces.agent_interface import TaskResult
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            result={"message": f"Task completed by {self.agent_id}"},
            execution_time=execution_time,
            completed_at=datetime.now()
        )
    
    async def get_status(self):
        """获取智能体状态"""
        from agentscope_integration.interfaces.agent_interface import AgentStatus
        return AgentStatus(
            agent_id=self.agent_id,
            role=self.role,
            status="idle",
            last_update=datetime.now(),
            performance_metrics={
                "tasks_completed": self._task_count,
                "success_rate": 1.0,
                "avg_execution_time": self.execution_time
            }
        )
    
    async def cancel_task(self, task_id: str):
        """取消任务"""
        return True


class TestAgentCoordinatorPerformance:
    """智能体协调器性能测试"""
    
    @pytest.fixture
    async def coordinator_with_agents(self):
        """创建带有多个智能体的协调器"""
        coordinator = AgentCoordinator()
        
        # 添加多个模拟智能体
        agents = [
            MockAgent(f"agent_{i}", AgentRole.CODE_MANAGER, execution_time=0.1)
            for i in range(5)
        ]
        
        for agent in agents:
            await coordinator.register_agent(agent)
        
        return coordinator, agents
    
    @pytest.mark.asyncio
    async def test_concurrent_task_dispatch(self, coordinator_with_agents):
        """测试并发任务分发性能"""
        coordinator, agents = coordinator_with_agents
        
        # 创建大量任务
        tasks = [
            AgentTask(
                id=f"task_{i}",
                type=TaskType.CODE_ANALYSIS,
                title=f"Test Task {i}",
                description=f"Performance test task {i}",
                parameters={"test_param": i}
            )
            for i in range(50)
        ]
        
        start_time = time.time()
        
        # 并发分发任务
        dispatch_tasks = [
            coordinator.dispatch_task(task) for task in tasks
        ]
        
        task_ids = await asyncio.gather(*dispatch_tasks)
        
        dispatch_time = time.time() - start_time
        
        # 验证性能
        assert len(task_ids) == 50
        assert dispatch_time < 5.0  # 应该在5秒内完成分发
        
        # 等待所有任务完成
        await asyncio.sleep(2.0)
        
        # 检查系统统计
        stats = await coordinator.get_system_stats()
        assert stats["task_stats"]["total_tasks_dispatched"] == 50
    
    @pytest.mark.asyncio
    async def test_load_balancing_performance(self, coordinator_with_agents):
        """测试负载均衡性能"""
        coordinator, agents = coordinator_with_agents
        
        # 创建任务
        tasks = [
            AgentTask(
                id=f"lb_task_{i}",
                type=TaskType.CODE_ANALYSIS,
                title=f"Load Balance Test {i}",
                description="Load balancing test",
                parameters={}
            )
            for i in range(25)
        ]
        
        # 分发任务
        for task in tasks:
            await coordinator.dispatch_task(task)
        
        # 等待任务完成
        await asyncio.sleep(1.0)
        
        # 检查负载分布
        stats = await coordinator.get_system_stats()
        load_distribution = stats["agent_load_distribution"]
        
        # 验证负载相对均衡
        load_values = list(load_distribution.values())
        if len(load_values) > 1:
            load_std = statistics.stdev(load_values)
            assert load_std < 3.0  # 标准差应该较小，表示负载均衡
    
    @pytest.mark.asyncio
    async def test_agent_registration_performance(self):
        """测试智能体注册性能"""
        coordinator = AgentCoordinator()
        
        # 测试大量智能体注册
        agents = [
            MockAgent(f"perf_agent_{i}", AgentRole.CODE_MANAGER)
            for i in range(100)
        ]
        
        start_time = time.time()
        
        registration_tasks = [
            coordinator.register_agent(agent) for agent in agents
        ]
        
        results = await asyncio.gather(*registration_tasks)
        
        registration_time = time.time() - start_time
        
        # 验证性能
        assert all(results)  # 所有注册都应该成功
        assert registration_time < 2.0  # 应该在2秒内完成
        assert len(coordinator.agents) == 100


class TestTaskManagerPerformance:
    """任务管理器性能测试"""
    
    @pytest.fixture
    async def task_manager_with_coordinator(self):
        """创建带有协调器的任务管理器"""
        coordinator = AgentCoordinator()
        
        # 添加智能体
        agents = [
            MockAgent(f"tm_agent_{i}", AgentRole.CODE_MANAGER, execution_time=0.05)
            for i in range(3)
        ]
        
        for agent in agents:
            await coordinator.register_agent(agent)
        
        task_manager = TaskManager(coordinator)
        await task_manager.start()
        
        return task_manager, coordinator
    
    @pytest.mark.asyncio
    async def test_high_volume_task_creation(self, task_manager_with_coordinator):
        """测试大量任务创建性能"""
        task_manager, coordinator = task_manager_with_coordinator
        
        start_time = time.time()
        
        # 创建大量任务
        creation_tasks = [
            task_manager.create_task(
                task_type=TaskType.CODE_ANALYSIS,
                title=f"Volume Test {i}",
                description=f"High volume test task {i}",
                parameters={"index": i},
                priority=5
            )
            for i in range(100)
        ]
        
        task_ids = await asyncio.gather(*creation_tasks)
        
        creation_time = time.time() - start_time
        
        # 验证性能
        assert len(task_ids) == 100
        assert creation_time < 3.0  # 应该在3秒内完成创建
        
        # 检查队列状态
        queue_status = await task_manager.get_queue_status()
        assert queue_status["pending_tasks"] + queue_status["running_tasks"] == 100
    
    @pytest.mark.asyncio
    async def test_task_processing_throughput(self, task_manager_with_coordinator):
        """测试任务处理吞吐量"""
        task_manager, coordinator = task_manager_with_coordinator
        
        # 创建任务
        task_count = 30
        for i in range(task_count):
            await task_manager.create_task(
                task_type=TaskType.CODE_ANALYSIS,
                title=f"Throughput Test {i}",
                description="Throughput test",
                parameters={},
                priority=5
            )
        
        start_time = time.time()
        
        # 等待所有任务完成
        while True:
            queue_status = await task_manager.get_queue_status()
            if (queue_status["pending_tasks"] == 0 and 
                queue_status["running_tasks"] == 0 and
                queue_status["completed_tasks"] >= task_count):
                break
            await asyncio.sleep(0.1)
        
        processing_time = time.time() - start_time
        throughput = task_count / processing_time
        
        # 验证吞吐量
        assert throughput > 5.0  # 每秒至少处理5个任务
        
        # 验证统计信息
        stats = queue_status["stats"]
        assert stats["tasks_completed"] >= task_count
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, task_manager_with_coordinator):
        """测试负载下的内存使用"""
        task_manager, coordinator = task_manager_with_coordinator
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建和处理大量任务
        for batch in range(5):
            batch_tasks = []
            for i in range(20):
                task_id = await task_manager.create_task(
                    task_type=TaskType.CODE_ANALYSIS,
                    title=f"Memory Test {batch}_{i}",
                    description="Memory usage test",
                    parameters={"batch": batch, "index": i},
                    priority=5
                )
                batch_tasks.append(task_id)
            
            # 等待批次完成
            await asyncio.sleep(0.5)
        
        # 等待所有任务完成
        await asyncio.sleep(2.0)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内（小于100MB）
        assert memory_increase < 100 * 1024 * 1024


class TestWebSocketManagerPerformance:
    """WebSocket管理器性能测试"""
    
    @pytest.fixture
    def websocket_manager(self):
        """创建WebSocket管理器"""
        return WebSocketManager()
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, websocket_manager):
        """测试并发连接性能"""
        # 模拟WebSocket连接
        class MockWebSocket:
            def __init__(self, client_id):
                self.client_id = client_id
                self.closed = False
            
            async def accept(self):
                pass
            
            async def send_text(self, text):
                if self.closed:
                    raise Exception("Connection closed")
            
            async def close(self):
                self.closed = True
        
        # 创建大量模拟连接
        connections = []
        start_time = time.time()
        
        for i in range(100):
            mock_ws = MockWebSocket(f"client_{i}")
            client_id = await websocket_manager.connect(mock_ws, f"client_{i}")
            connections.append((mock_ws, client_id))
        
        connection_time = time.time() - start_time
        
        # 验证性能
        assert len(connections) == 100
        assert connection_time < 2.0  # 应该在2秒内完成
        assert len(websocket_manager.connections) == 100
    
    @pytest.mark.asyncio
    async def test_message_broadcasting_performance(self, websocket_manager):
        """测试消息广播性能"""
        # 创建模拟连接
        class MockWebSocket:
            def __init__(self):
                self.messages = []
            
            async def accept(self):
                pass
            
            async def send_text(self, text):
                self.messages.append(text)
        
        # 添加连接
        websockets = []
        for i in range(50):
            mock_ws = MockWebSocket()
            await websocket_manager.connect(mock_ws, f"broadcast_client_{i}")
            websockets.append(mock_ws)
        
        # 测试广播性能
        start_time = time.time()
        
        for i in range(10):
            await websocket_manager.broadcast_event(
                "performance_test",
                {"message": f"Broadcast test {i}"}
            )
        
        broadcast_time = time.time() - start_time
        
        # 验证性能
        assert broadcast_time < 1.0  # 应该在1秒内完成
        
        # 验证消息接收
        for ws in websockets:
            assert len(ws.messages) == 10


class TestSystemIntegrationPerformance:
    """系统集成性能测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance(self):
        """测试端到端性能"""
        # 创建完整系统
        coordinator = AgentCoordinator()
        task_manager = TaskManager(coordinator)
        websocket_manager = WebSocketManager()
        
        # 添加智能体
        agents = [
            MockAgent(f"e2e_agent_{i}", AgentRole.CODE_MANAGER, execution_time=0.1)
            for i in range(3)
        ]
        
        for agent in agents:
            await coordinator.register_agent(agent)
        
        await task_manager.start()
        
        # 设置事件回调
        async def event_callback(event_type, data):
            await websocket_manager.broadcast_event(event_type, data)
        
        coordinator.set_event_callback(event_callback)
        task_manager.set_event_callback(event_callback)
        
        start_time = time.time()
        
        # 创建和处理任务
        task_ids = []
        for i in range(20):
            task_id = await task_manager.create_task(
                task_type=TaskType.CODE_ANALYSIS,
                title=f"E2E Test {i}",
                description="End-to-end performance test",
                parameters={"index": i},
                priority=5
            )
            task_ids.append(task_id)
        
        # 等待所有任务完成
        while True:
            queue_status = await task_manager.get_queue_status()
            if (queue_status["pending_tasks"] == 0 and 
                queue_status["running_tasks"] == 0):
                break
            await asyncio.sleep(0.1)
        
        total_time = time.time() - start_time
        
        # 验证性能
        assert total_time < 10.0  # 应该在10秒内完成
        assert len(task_ids) == 20
        
        # 验证系统状态
        coordinator_stats = await coordinator.get_system_stats()
        assert coordinator_stats["task_stats"]["total_tasks_dispatched"] == 20
        
        queue_status = await task_manager.get_queue_status()
        assert queue_status["stats"]["tasks_completed"] == 20
        
        # 清理
        await task_manager.stop()
        await websocket_manager.close_all()
    
    @pytest.mark.asyncio
    async def test_stress_test(self):
        """压力测试"""
        coordinator = AgentCoordinator()
        task_manager = TaskManager(coordinator)
        
        # 添加更多智能体
        agents = [
            MockAgent(f"stress_agent_{i}", AgentRole.CODE_MANAGER, execution_time=0.05)
            for i in range(10)
        ]
        
        for agent in agents:
            await coordinator.register_agent(agent)
        
        await task_manager.start()
        
        # 创建大量任务
        task_count = 200
        start_time = time.time()
        
        # 分批创建任务以避免内存问题
        batch_size = 50
        for batch_start in range(0, task_count, batch_size):
            batch_tasks = []
            for i in range(batch_start, min(batch_start + batch_size, task_count)):
                task_coro = task_manager.create_task(
                    task_type=TaskType.CODE_ANALYSIS,
                    title=f"Stress Test {i}",
                    description="Stress test task",
                    parameters={"index": i},
                    priority=5
                )
                batch_tasks.append(task_coro)
            
            await asyncio.gather(*batch_tasks)
            await asyncio.sleep(0.1)  # 短暂暂停
        
        # 等待所有任务完成
        while True:
            queue_status = await task_manager.get_queue_status()
            if (queue_status["pending_tasks"] == 0 and 
                queue_status["running_tasks"] == 0):
                break
            await asyncio.sleep(0.5)
        
        total_time = time.time() - start_time
        throughput = task_count / total_time
        
        # 验证压力测试结果
        assert throughput > 10.0  # 每秒至少处理10个任务
        
        queue_status = await task_manager.get_queue_status()
        assert queue_status["stats"]["tasks_completed"] == task_count
        
        # 清理
        await task_manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
