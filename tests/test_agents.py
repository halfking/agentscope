# -*- coding: utf-8 -*-
"""
智能体迁移功能单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase
from agentscope.tool import Toolkit

from agentscope_integration.agents.base_specialized_agent import BaseSpecializedAgent
from agentscope_integration.agents.code_manager_agent import CodeManagerAgent
from agentscope_integration.agents.compliance_auditor_agent import ComplianceAuditorAgent
from agentscope_integration.interfaces.agent_interface import (
    AgentRole, TaskType, AgentTask, TaskResult, TaskStatus
)


class TestBaseSpecializedAgent:
    """基础专业化智能体测试"""
    
    @pytest.fixture
    def mock_model(self):
        """模拟LLM模型"""
        model = Mock(spec=ChatModelBase)
        model.generate = AsyncMock(return_value="Test response")
        return model
    
    @pytest.fixture
    def mock_formatter(self):
        """模拟格式化器"""
        return Mock(spec=FormatterBase)
    
    @pytest.fixture
    def mock_toolkit(self):
        """模拟工具包"""
        return Mock(spec=Toolkit)
    
    @pytest.fixture
    def base_agent(self, mock_model, mock_formatter, mock_toolkit):
        """创建基础智能体实例"""
        return BaseSpecializedAgent(
            agent_id="test_agent",
            role=AgentRole.CODE_MANAGER,
            name="TestAgent",
            sys_prompt="Test system prompt",
            model=mock_model,
            formatter=mock_formatter,
            toolkit=mock_toolkit,
            supported_tasks=[TaskType.CODE_ANALYSIS]
        )
    
    def test_agent_initialization(self, base_agent):
        """测试智能体初始化"""
        assert base_agent.agent_id == "test_agent"
        assert base_agent.role == AgentRole.CODE_MANAGER
        assert base_agent.name == "TestAgent"
        assert TaskType.CODE_ANALYSIS in base_agent.supported_tasks
        assert len(base_agent._task_history) == 0
        assert base_agent._current_task is None
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self, base_agent):
        """测试成功执行任务"""
        task = AgentTask(
            id="test_task_1",
            type=TaskType.CODE_ANALYSIS,
            title="Test Task",
            description="Test task description",
            parameters={"file_path": "/test/file.py"}
        )
        
        # 模拟AgentScope的回复
        with patch.object(base_agent, '__call__', new_callable=AsyncMock) as mock_call:
            mock_response = Mock()
            mock_response.get_text_content.return_value = "Analysis complete"
            mock_call.return_value = mock_response
            
            result = await base_agent.execute_task(task)
            
            assert result.task_id == "test_task_1"
            assert result.status == TaskStatus.COMPLETED
            assert result.result is not None
            assert result.execution_time is not None
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_unsupported_task(self, base_agent):
        """测试执行不支持的任务类型"""
        task = AgentTask(
            id="test_task_2",
            type=TaskType.SECURITY_SCAN,  # 不支持的任务类型
            title="Unsupported Task",
            description="This task type is not supported",
            parameters={}
        )
        
        result = await base_agent.execute_task(task)
        
        assert result.task_id == "test_task_2"
        assert result.status == TaskStatus.FAILED
        assert "Unsupported task type" in result.error
    
    @pytest.mark.asyncio
    async def test_get_status(self, base_agent):
        """测试获取智能体状态"""
        status = await base_agent.get_status()
        
        assert status.agent_id == "test_agent"
        assert status.role == AgentRole.CODE_MANAGER
        assert status.status == "idle"
        assert status.current_task is None
        assert isinstance(status.performance_metrics, dict)
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, base_agent):
        """测试取消任务"""
        # 没有运行中的任务
        result = await base_agent.cancel_task("nonexistent_task")
        assert result is False
        
        # 模拟有运行中的任务
        base_agent._current_task = AgentTask(
            id="running_task",
            type=TaskType.CODE_ANALYSIS,
            title="Running Task",
            description="Currently running task",
            parameters={}
        )
        
        result = await base_agent.cancel_task("running_task")
        assert result is True
        assert base_agent._current_task is None
    
    def test_performance_metrics_update(self, base_agent):
        """测试性能指标更新"""
        # 模拟任务结果
        task = AgentTask(
            id="test_task",
            type=TaskType.CODE_ANALYSIS,
            title="Test Task",
            description="Test",
            parameters={}
        )
        
        result = TaskResult(
            task_id="test_task",
            status=TaskStatus.COMPLETED,
            execution_time=2.5,
            completed_at=datetime.now()
        )
        
        base_agent._update_performance_metrics(task, result)
        
        metrics = base_agent._performance_metrics
        assert metrics["success_rate"] == 1.0
        assert metrics["avg_execution_time"] == 2.5
        assert metrics["tasks_code_analysis"] == 1


class TestCodeManagerAgent:
    """代码管理员智能体测试"""
    
    @pytest.fixture
    def mock_model(self):
        model = Mock(spec=ChatModelBase)
        model.generate = AsyncMock(return_value="Code analysis complete")
        return model
    
    @pytest.fixture
    def mock_formatter(self):
        return Mock(spec=FormatterBase)
    
    @pytest.fixture
    def code_manager(self, mock_model, mock_formatter):
        """创建代码管理员智能体实例"""
        return CodeManagerAgent(
            model=mock_model,
            formatter=mock_formatter
        )
    
    def test_code_manager_initialization(self, code_manager):
        """测试代码管理员初始化"""
        assert code_manager.agent_id == "code_manager"
        assert code_manager.role == AgentRole.CODE_MANAGER
        assert TaskType.CODE_ANALYSIS in code_manager.supported_tasks
        assert TaskType.DEPENDENCY_ANALYSIS in code_manager.supported_tasks
        assert TaskType.ARCHITECTURE_REVIEW in code_manager.supported_tasks
    
    @pytest.mark.asyncio
    async def test_parse_python_file(self, code_manager):
        """测试Python文件解析"""
        # 创建临时Python文件
        test_code = '''
class TestClass:
    """Test class docstring"""
    
    def __init__(self):
        self.value = 42
    
    def test_method(self, param):
        """Test method docstring"""
        return param * 2

def standalone_function():
    """Standalone function"""
    pass

import os
from pathlib import Path
'''
        
        with patch('builtins.open', mock_open(read_data=test_code)):
            result = await code_manager._parse_python_file("test.py")
            
            assert result["language"] == "python"
            assert len(result["classes"]) == 1
            assert result["classes"][0]["name"] == "TestClass"
            assert len(result["classes"][0]["methods"]) == 2
            assert len(result["functions"]) == 1
            assert result["functions"][0]["name"] == "standalone_function"
            assert "os" in result["imports"]
            assert "pathlib" in result["imports"]
    
    @pytest.mark.asyncio
    async def test_analyze_dependencies(self, code_manager):
        """测试依赖关系分析"""
        with patch.object(code_manager, '_parse_python_file') as mock_parse:
            mock_parse.return_value = {
                "imports": ["numpy", "pandas", "matplotlib"]
            }
            
            dependencies = await code_manager._analyze_dependencies("test.py")
            
            assert len(dependencies) == 3
            assert all(dep["type"] == "import" for dep in dependencies)
            assert all(dep["source"] == "test.py" for dep in dependencies)


class TestComplianceAuditorAgent:
    """规范审核员智能体测试"""
    
    @pytest.fixture
    def mock_model(self):
        model = Mock(spec=ChatModelBase)
        model.generate = AsyncMock(return_value="Compliance check complete")
        return model
    
    @pytest.fixture
    def mock_formatter(self):
        return Mock(spec=FormatterBase)
    
    @pytest.fixture
    def compliance_auditor(self, mock_model, mock_formatter):
        """创建规范审核员智能体实例"""
        return ComplianceAuditorAgent(
            model=mock_model,
            formatter=mock_formatter
        )
    
    def test_compliance_auditor_initialization(self, compliance_auditor):
        """测试规范审核员初始化"""
        assert compliance_auditor.agent_id == "compliance_auditor"
        assert compliance_auditor.role == AgentRole.COMPLIANCE_AUDITOR
        assert TaskType.QUALITY_CHECK in compliance_auditor.supported_tasks
        assert TaskType.SECURITY_SCAN in compliance_auditor.supported_tasks
        assert TaskType.TEST_ANALYSIS in compliance_auditor.supported_tasks
    
    def test_audit_rules_loading(self, compliance_auditor):
        """测试审计规则加载"""
        rules = compliance_auditor.rules
        
        assert "security" in rules
        assert "quality" in rules
        assert "testing" in rules
        
        # 检查安全规则
        security_rules = rules["security"]
        assert "sql_injection" in security_rules
        assert "hardcoded_secrets" in security_rules
        
        # 检查质量规则
        quality_rules = rules["quality"]
        assert "code_complexity" in quality_rules
        assert "naming_conventions" in quality_rules
    
    @pytest.mark.asyncio
    async def test_analyze_code_quality(self, compliance_auditor):
        """测试代码质量分析"""
        test_code = '''
def very_long_function_name_that_exceeds_normal_length_limits():
    password = "hardcoded_password_123"
    api_key = "sk-1234567890abcdef"
    
    # This is a very long line that exceeds the recommended line length limit of 120 characters and should be flagged
    
    for i in range(100):
        if i % 2 == 0:
            if i % 4 == 0:
                if i % 8 == 0:
                    print("Complex nested logic")
'''
        
        with patch('builtins.open', mock_open(read_data=test_code)):
            violations = await compliance_auditor._analyze_code_quality("test.py")
            
            # 应该检测到硬编码密钥
            hardcoded_violations = [v for v in violations if v["rule"] == "hardcoded_password"]
            assert len(hardcoded_violations) > 0
            
            # 检查质量评分计算
            score = compliance_auditor._calculate_quality_score(violations)
            assert 0 <= score <= 100
    
    @pytest.mark.asyncio
    async def test_scan_security_vulnerabilities(self, compliance_auditor):
        """测试安全漏洞扫描"""
        vulnerable_code = '''
import sqlite3

def unsafe_query(user_input):
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    
    # SQL注入漏洞
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    cursor.execute(query)
    
    # 硬编码API密钥
    api_key = "sk-1234567890abcdef"
    
    # 使用eval（危险）
    result = eval(user_input)
    
    return result
'''
        
        with patch('builtins.open', mock_open(read_data=vulnerable_code)):
            vulnerabilities = await compliance_auditor._scan_security_vulnerabilities("test.py")
            
            # 应该检测到多个安全问题
            assert len(vulnerabilities) > 0
            
            # 检查SQL注入检测
            sql_injection_vulns = [v for v in vulnerabilities if v["type"] == "sql_injection"]
            assert len(sql_injection_vulns) > 0
            
            # 检查硬编码密钥检测
            hardcoded_vulns = [v for v in vulnerabilities if v["type"] == "hardcoded_api_key"]
            assert len(hardcoded_vulns) > 0
            
            # 检查eval使用检测
            eval_vulns = [v for v in vulnerabilities if v["type"] == "eval_usage"]
            assert len(eval_vulns) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_test_quality(self, compliance_auditor):
        """测试测试质量分析"""
        test_code = '''
import unittest
from unittest.mock import Mock
import h2database

class TestWithH2(unittest.TestCase):
    
    def setUp(self):
        # 使用H2内存数据库进行测试
        self.db = h2database.connect("jdbc:h2:mem:testdb")
        
    def test_with_mock_repository(self):
        # 过度使用Mock
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = {"id": 1, "name": "test"}
        
        result = self.service.get_user(1)
        self.assertEqual(result["name"], "test")
'''
        
        with patch('builtins.open', mock_open(read_data=test_code)):
            issues = await compliance_auditor._analyze_test_quality("test.py")
            
            # 应该检测到虚假数据库使用
            fake_db_issues = [i for i in issues if i["issue_type"] == "fake_database"]
            assert len(fake_db_issues) > 0
            
            # 应该检测到过度使用Mock
            mock_issues = [i for i in issues if i["issue_type"] == "mock_overuse"]
            assert len(mock_issues) > 0


# 测试工具函数
def mock_open(read_data=''):
    """创建mock open函数"""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)


# 集成测试
class TestAgentIntegration:
    """智能体集成测试"""
    
    @pytest.mark.asyncio
    async def test_agent_coordination(self):
        """测试智能体协调"""
        # 这里可以添加智能体协调的集成测试
        pass
    
    @pytest.mark.asyncio
    async def test_task_workflow(self):
        """测试任务工作流"""
        # 这里可以添加完整任务工作流的测试
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
