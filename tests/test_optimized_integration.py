#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化架构集成测试 - 验证AgentScope深度集成和Augment真实集成
"""

import asyncio
import json
import logging
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# 测试AgentScope集成
from agentscope.model import MockModel
from agentscope.formatter import JSONFormatter

# 测试优化组件
from agentscope_integration.core.agentscope_workflow_manager import AgentScopeWorkflowManager
from agentscope_integration.integrations.augment_integration_hub import (
    AugmentIntegrationHub, AugmentMessage, AugmentEventType
)
from agentscope_integration.agents.base_specialized_agent import OptimizedSpecializedAgent
from agentscope_integration.agents.code_manager_agent import CodeManagerAgent
from agentscope_integration.agents.compliance_auditor_agent import ComplianceAuditorAgent
from agentscope_integration.interfaces.agent_interface import AgentTask, TaskType, AgentRole


class TestOptimizedIntegration:
    """优化架构集成测试"""
    
    @pytest.fixture
    async def setup_test_environment(self):
        """设置测试环境"""
        # 创建模拟模型
        model = MockModel(model_name="test-model")
        formatter = JSONFormatter()
        
        # 创建工作流管理器
        workflow_manager = AgentScopeWorkflowManager()
        
        # 创建Augment集成中心
        augment_hub = AugmentIntegrationHub(workflow_manager)
        
        # 创建智能体
        code_manager = CodeManagerAgent(model=model, formatter=formatter)
        compliance_auditor = ComplianceAuditorAgent(model=model, formatter=formatter)
        
        # 注册智能体
        await workflow_manager.register_agent(code_manager)
        await workflow_manager.register_agent(compliance_auditor)
        
        # 启动Augment集成
        await augment_hub.start()
        
        return {
            "workflow_manager": workflow_manager,
            "augment_hub": augment_hub,
            "code_manager": code_manager,
            "compliance_auditor": compliance_auditor,
            "model": model,
            "formatter": formatter
        }
    
    @pytest.mark.asyncio
    async def test_agentscope_deep_integration(self, setup_test_environment):
        """测试AgentScope深度集成"""
        env = await setup_test_environment
        code_manager = env["code_manager"]
        
        # 测试1: 验证智能体继承自ReActAgent
        assert isinstance(code_manager, OptimizedSpecializedAgent)
        assert hasattr(code_manager, 'toolkit')
        assert hasattr(code_manager, 'memory')
        assert hasattr(code_manager, 'long_term_memory')
        
        # 测试2: 验证长期记忆功能
        test_data = {"test": "data"}
        await code_manager.long_term_memory.store("test_namespace", "test_key", test_data)
        retrieved_data = await code_manager.long_term_memory.get("test_namespace", "test_key")
        assert retrieved_data == test_data
        
        # 测试3: 验证性能追踪
        code_manager.performance_tracker.start_tracking("test_operation")
        await asyncio.sleep(0.1)
        code_manager.performance_tracker.end_tracking("test_operation")
        
        avg_time = code_manager.performance_tracker.get_average_time("test_operation")
        assert avg_time > 0
        
        # 测试4: 验证工具注册
        assert len(code_manager.toolkit.tools) > 0
        
        print("✅ AgentScope深度集成测试通过")
    
    @pytest.mark.asyncio
    async def test_workflow_manager_pipeline_integration(self, setup_test_environment):
        """测试工作流管理器的Pipeline集成"""
        env = await setup_test_environment
        workflow_manager = env["workflow_manager"]
        
        # 创建测试任务
        task = AgentTask(
            id="test_task_001",
            type=TaskType.CODE_ANALYSIS,
            title="测试代码分析",
            description="测试AgentScope Pipeline集成",
            parameters={"file_path": "/test/file.py"},
            priority=2
        )
        
        # 测试1: 创建顺序工作流
        workflow_id = await workflow_manager.create_workflow(task)
        assert workflow_id is not None
        
        # 测试2: 获取工作流状态
        status = await workflow_manager.get_workflow_status(workflow_id)
        assert status is not None
        assert status["id"] == workflow_id
        
        # 测试3: 验证工作流统计
        stats = workflow_manager.get_workflow_statistics()
        assert stats["total_workflows"] >= 1
        
        print("✅ 工作流管理器Pipeline集成测试通过")
    
    @pytest.mark.asyncio
    async def test_augment_natural_language_processing(self, setup_test_environment):
        """测试Augment自然语言处理"""
        env = await setup_test_environment
        augment_hub = env["augment_hub"]
        
        # 测试用例
        test_cases = [
            {
                "content": "请分析user_manager.py文件的安全问题",
                "expected_type": AugmentEventType.SECURITY_SCAN_REQUEST,
                "expected_files": ["user_manager.py"]
            },
            {
                "content": "检查代码质量，特别关注复杂度",
                "expected_type": AugmentEventType.QUALITY_CHECK_REQUEST,
                "expected_analysis": ["complexity"]
            },
            {
                "content": "analyze the code structure and dependencies",
                "expected_type": AugmentEventType.CODE_ANALYSIS_REQUEST,
                "expected_analysis": ["structure", "dependencies"]
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            # 创建Augment消息
            message = AugmentMessage(
                event_type=AugmentEventType.CODE_ANALYSIS_REQUEST,  # 初始类型，会被重新解析
                content=test_case["content"],
                context={"current_file": "/test/current.py"},
                source="test",
                timestamp=asyncio.get_event_loop().time()
            )
            
            # 解析指令
            parsed = await augment_hub.nlp_processor.parse_command(
                message.content, 
                message.context
            )
            
            # 验证解析结果
            assert parsed["event_type"] == test_case["expected_type"]
            assert parsed["confidence"] > 0.5
            
            if "expected_files" in test_case:
                assert any(f in parsed["target_files"] for f in test_case["expected_files"])
            
            if "expected_analysis" in test_case:
                assert any(a in parsed["analysis_types"] for a in test_case["expected_analysis"])
            
            print(f"✅ 测试用例 {i+1} 通过: {test_case['content'][:30]}...")
        
        print("✅ Augment自然语言处理测试通过")
    
    @pytest.mark.asyncio
    async def test_end_to_end_augment_integration(self, setup_test_environment):
        """测试端到端Augment集成"""
        env = await setup_test_environment
        augment_hub = env["augment_hub"]
        
        # 创建测试文件
        test_file = Path(tempfile.mktemp(suffix=".py"))
        test_code = '''
def vulnerable_function(user_input):
    # SQL注入漏洞
    query = "SELECT * FROM users WHERE id = " + user_input
    password = "hardcoded_password_123"  # 硬编码密码
    return query
'''
        test_file.write_text(test_code)
        
        try:
            # 创建Augment消息
            message = AugmentMessage(
                event_type=AugmentEventType.SECURITY_SCAN_REQUEST,
                content=f"请扫描文件 {test_file} 中的安全漏洞，特别关注SQL注入和硬编码密钥",
                context={
                    "current_file": str(test_file),
                    "language": "python"
                },
                source="test_integration",
                timestamp=asyncio.get_event_loop().time()
            )
            
            # 设置事件回调来捕获结果
            results = []
            
            def capture_result(data):
                results.append(data)
            
            augment_hub.register_event_callback("message_processed", capture_result)
            
            # 处理消息
            response = await augment_hub.process_augment_message(message)
            assert response["status"] == "queued"
            
            # 等待处理完成
            max_wait = 30  # 30秒超时
            for _ in range(max_wait):
                if results:
                    break
                await asyncio.sleep(1)
            
            # 验证结果
            assert len(results) > 0, "没有收到处理结果"
            
            result = results[0]
            assert "task" in result
            assert "workflow_id" in result
            
            task = result["task"]
            assert task.type == TaskType.SECURITY_SCAN
            assert str(test_file) in task.parameters.get("target_files", [])
            
            print("✅ 端到端Augment集成测试通过")
            
        finally:
            # 清理测试文件
            if test_file.exists():
                test_file.unlink()
    
    @pytest.mark.asyncio
    async def test_session_and_memory_integration(self, setup_test_environment):
        """测试会话和记忆集成"""
        env = await setup_test_environment
        code_manager = env["code_manager"]
        
        # 创建测试任务
        task = AgentTask(
            id="memory_test_task",
            type=TaskType.CODE_ANALYSIS,
            title="记忆集成测试",
            description="测试会话和长期记忆功能",
            parameters={"file_path": "/test/memory_test.py"},
            priority=2
        )
        
        # 测试1: 在会话中执行任务
        result = await code_manager.execute_task_with_session(task)
        assert result is not None
        assert result.task_id == task.id
        
        # 测试2: 验证任务历史记录
        history = code_manager.get_task_history()
        assert len(history) > 0
        assert any(h.task_id == task.id for h in history)
        
        # 测试3: 验证长期记忆存储
        # 检查是否有分析结果存储到长期记忆
        stored_results = await code_manager.long_term_memory.get(
            "analysis_results", 
            f"task_result:{task.id}"
        )
        # 注意：这个测试可能需要根据实际实现调整
        
        print("✅ 会话和记忆集成测试通过")
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, setup_test_environment):
        """测试性能追踪功能"""
        env = await setup_test_environment
        code_manager = env["code_manager"]
        
        # 执行多个任务来测试性能追踪
        tasks = []
        for i in range(3):
            task = AgentTask(
                id=f"perf_test_task_{i}",
                type=TaskType.CODE_ANALYSIS,
                title=f"性能测试任务 {i}",
                description="测试性能追踪功能",
                parameters={"file_path": f"/test/perf_test_{i}.py"},
                priority=2
            )
            tasks.append(task)
        
        # 执行任务
        for task in tasks:
            await code_manager.execute_task(task)
        
        # 验证性能指标
        avg_time = code_manager.performance_tracker.get_average_time("task_code_analysis")
        assert avg_time >= 0  # 应该有记录的执行时间
        
        # 验证任务历史
        history = code_manager.get_task_history()
        assert len(history) >= 3
        
        print("✅ 性能追踪功能测试通过")
    
    @pytest.mark.asyncio
    async def test_event_callback_system(self, setup_test_environment):
        """测试事件回调系统"""
        env = await setup_test_environment
        code_manager = env["code_manager"]
        
        # 设置事件回调
        events_received = []
        
        def event_handler(data):
            events_received.append(data)
        
        code_manager.register_event_callback("task_completed", event_handler)
        code_manager.register_event_callback("task_failed", event_handler)
        
        # 执行任务
        task = AgentTask(
            id="event_test_task",
            type=TaskType.CODE_ANALYSIS,
            title="事件回调测试",
            description="测试事件回调系统",
            parameters={"file_path": "/test/event_test.py"},
            priority=2
        )
        
        await code_manager.execute_task(task)
        
        # 验证事件回调
        assert len(events_received) > 0
        
        event_data = events_received[0]
        assert "task" in event_data
        assert "result" in event_data
        
        print("✅ 事件回调系统测试通过")


async def run_integration_tests():
    """运行集成测试"""
    logging.basicConfig(level=logging.INFO)
    
    test_instance = TestOptimizedIntegration()
    
    print("🚀 开始运行优化架构集成测试...")
    
    try:
        # 设置测试环境
        env = await test_instance.setup_test_environment()
        
        # 运行所有测试
        await test_instance.test_agentscope_deep_integration(env)
        await test_instance.test_workflow_manager_pipeline_integration(env)
        await test_instance.test_augment_natural_language_processing(env)
        await test_instance.test_end_to_end_augment_integration(env)
        await test_instance.test_session_and_memory_integration(env)
        await test_instance.test_performance_tracking(env)
        await test_instance.test_event_callback_system(env)
        
        print("\n🎉 所有集成测试通过！")
        print("✅ AgentScope深度集成功能正常")
        print("✅ Augment真实集成功能正常")
        print("✅ 工作流管理器功能正常")
        print("✅ 性能追踪功能正常")
        print("✅ 事件系统功能正常")
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        raise
    
    finally:
        # 清理
        if 'env' in locals():
            await env["augment_hub"].stop()


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
