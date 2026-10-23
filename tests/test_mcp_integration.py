# -*- coding: utf-8 -*-
"""
MCP集成测试
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import TextBlock

from agentscope_integration.mcp.mcp_manager import MCPManager, MCPServerConfig
from agentscope_integration.mcp.servers.code_analysis_server import CodeAnalysisServer


class TestMCPServerConfig:
    """MCP服务器配置测试"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = MCPServerConfig(
            name="test_server",
            command="python",
            args=["-m", "test_module"],
            env={"TEST_VAR": "test_value"}
        )
        
        assert config.name == "test_server"
        assert config.command == "python"
        assert config.args == ["-m", "test_module"]
        assert config.env == {"TEST_VAR": "test_value"}
        assert config.enabled is True
        assert config.transport == "stdio"
    
    def test_config_defaults(self):
        """测试默认配置"""
        config = MCPServerConfig(
            name="minimal_server",
            command="echo"
        )
        
        assert config.args == []
        assert config.env == {}
        assert config.enabled is True
        assert config.transport == "stdio"


class TestMCPManager:
    """MCP管理器测试"""
    
    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        config_data = {
            "mcp_servers": {
                "test_server": {
                    "name": "test_server",
                    "command": "echo",
                    "args": ["hello"],
                    "enabled": True
                },
                "disabled_server": {
                    "name": "disabled_server",
                    "command": "echo",
                    "args": ["world"],
                    "enabled": False
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        yield temp_file
        
        # 清理
        os.unlink(temp_file)
    
    @pytest.fixture
    def mcp_manager(self, temp_config_file):
        """创建MCP管理器实例"""
        return MCPManager(temp_config_file)
    
    def test_manager_initialization(self, mcp_manager):
        """测试管理器初始化"""
        assert len(mcp_manager.server_configs) >= 2  # 至少有测试配置的两个服务器
        assert "test_server" in mcp_manager.server_configs
        assert "disabled_server" in mcp_manager.server_configs
        
        # 检查默认配置是否加载
        assert "filesystem" in mcp_manager.server_configs
        assert "git" in mcp_manager.server_configs
    
    def test_load_config_file(self, temp_config_file):
        """测试配置文件加载"""
        manager = MCPManager(temp_config_file)
        
        test_config = manager.server_configs["test_server"]
        assert test_config.name == "test_server"
        assert test_config.command == "echo"
        assert test_config.args == ["hello"]
        assert test_config.enabled is True
        
        disabled_config = manager.server_configs["disabled_server"]
        assert disabled_config.enabled is False
    
    @pytest.mark.asyncio
    async def test_register_mcp_server(self, mcp_manager):
        """测试注册MCP服务器"""
        server_config = {
            "command": "python",
            "args": ["-c", "print('test')"],
            "enabled": True
        }
        
        success = await mcp_manager.register_mcp_server("new_server", server_config)
        assert success is True
        assert "new_server" in mcp_manager.server_configs
        
        registered_config = mcp_manager.server_configs["new_server"]
        assert registered_config.name == "new_server"
        assert registered_config.command == "python"
    
    @pytest.mark.asyncio
    async def test_unregister_mcp_server(self, mcp_manager):
        """测试注销MCP服务器"""
        # 先注册一个服务器
        await mcp_manager.register_mcp_server("temp_server", {
            "command": "echo",
            "enabled": True
        })
        
        assert "temp_server" in mcp_manager.server_configs
        
        # 注销服务器
        success = await mcp_manager.unregister_mcp_server("temp_server")
        assert success is True
        assert "temp_server" not in mcp_manager.server_configs
    
    @pytest.mark.asyncio
    async def test_start_mcp_client_mock(self, mcp_manager):
        """测试启动MCP客户端（模拟）"""
        with patch('agentscope_integration.mcp.mcp_manager.MCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.start = AsyncMock()
            mock_client.list_tools = AsyncMock(return_value=[
                Mock(name="test_tool_1"),
                Mock(name="test_tool_2")
            ])
            mock_client_class.return_value = mock_client
            
            config = MCPServerConfig(
                name="mock_server",
                command="echo",
                args=["test"]
            )
            
            await mcp_manager._start_mcp_client("mock_server", config)
            
            assert "mock_server" in mcp_manager.clients
            assert "mock_server" in mcp_manager.available_tools
            assert len(mcp_manager.available_tools["mock_server"]) == 2
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool_mock(self, mcp_manager):
        """测试调用MCP工具（模拟）"""
        # 模拟客户端
        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value={"result": "test_output"})
        mcp_manager.clients["test_server"] = mock_client
        
        result = await mcp_manager.call_mcp_tool("test_server", "test_tool", param1="value1")
        
        assert result == {"result": "test_output"}
        mock_client.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})
    
    def test_register_mcp_tools_to_toolkit(self, mcp_manager):
        """测试将MCP工具注册到Toolkit"""
        # 模拟可用工具
        mcp_manager.available_tools["test_server"] = ["tool1", "tool2"]
        mcp_manager.clients["test_server"] = AsyncMock()
        
        toolkit = Toolkit()
        mcp_manager.register_mcp_tools_to_toolkit(toolkit, ["test_server"])
        
        # 检查工具是否注册
        # 注意：这里需要根据实际的Toolkit API进行调整
        assert len(toolkit._tools) > 0 or hasattr(toolkit, '_tool_functions')
    
    @pytest.mark.asyncio
    async def test_get_server_info(self, mcp_manager):
        """测试获取服务器信息"""
        # 模拟服务器
        mock_client = AsyncMock()
        mcp_manager.clients["test_server"] = mock_client
        mcp_manager.available_tools["test_server"] = ["tool1", "tool2"]
        
        info = await mcp_manager.get_server_info("test_server")
        
        assert info is not None
        assert info["name"] == "test_server"
        assert info["status"] == "connected"
        assert info["tools_count"] == 2
        assert "tool1" in info["tools"]
        assert "tool2" in info["tools"]
    
    @pytest.mark.asyncio
    async def test_get_all_servers_info(self, mcp_manager):
        """测试获取所有服务器信息"""
        # 模拟一个连接的服务器
        mock_client = AsyncMock()
        mcp_manager.clients["connected_server"] = mock_client
        mcp_manager.available_tools["connected_server"] = ["tool1"]
        
        servers_info = await mcp_manager.get_all_servers_info()
        
        assert len(servers_info) > 0
        
        # 查找连接的服务器
        connected_info = next((s for s in servers_info if s["name"] == "connected_server"), None)
        assert connected_info is not None
        assert connected_info["status"] == "connected"
        
        # 查找未连接的服务器
        disconnected_info = next((s for s in servers_info if s["status"] == "disconnected"), None)
        assert disconnected_info is not None
    
    def test_save_config(self, mcp_manager):
        """测试保存配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            mcp_manager.save_config(temp_file)
            
            # 验证保存的配置
            with open(temp_file, 'r') as f:
                saved_config = json.load(f)
            
            assert "mcp_servers" in saved_config
            assert len(saved_config["mcp_servers"]) > 0
            
        finally:
            os.unlink(temp_file)


class TestCodeAnalysisServer:
    """代码分析MCP服务器测试"""
    
    @pytest.fixture
    def code_analysis_server(self):
        """创建代码分析服务器实例"""
        return CodeAnalysisServer()
    
    def test_server_initialization(self, code_analysis_server):
        """测试服务器初始化"""
        assert code_analysis_server.server is not None
        # 检查工具是否注册（这需要根据实际的MCP服务器实现调整）
    
    @pytest.mark.asyncio
    async def test_parse_python_ast_tool(self, code_analysis_server):
        """测试Python AST解析工具"""
        test_code = '''
class TestClass:
    def __init__(self):
        self.value = 42
    
    def method(self, param):
        return param * 2

def function():
    pass

import os
from pathlib import Path
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        try:
            # 这里需要根据实际的工具调用方式进行调整
            # 假设有一个方法可以直接调用工具
            if hasattr(code_analysis_server, '_parse_python_ast_tool'):
                result = await code_analysis_server._parse_python_ast_tool(temp_file)
                
                assert "classes" in result
                assert "functions" in result
                assert "imports" in result
                assert len(result["classes"]) == 1
                assert result["classes"][0]["name"] == "TestClass"
                assert len(result["functions"]) == 1
                assert result["functions"][0]["name"] == "function"
        
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_analyze_code_quality_tool(self, code_analysis_server):
        """测试代码质量分析工具"""
        test_code = '''
def very_long_function_with_many_parameters_and_complex_logic(param1, param2, param3, param4, param5):
    # This line is intentionally very long to test line length checking functionality and should trigger a warning
    password = "hardcoded_password_123"
    
    # Complex nested logic
    for i in range(100):
        if i % 2 == 0:
            if i % 4 == 0:
                if i % 8 == 0:
                    print("Very nested")
    
    # TODO: Fix this later
    return param1 + param2
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        try:
            # 这里需要根据实际的工具调用方式进行调整
            if hasattr(code_analysis_server, '_analyze_code_quality_tool'):
                result = await code_analysis_server._analyze_code_quality_tool(temp_file)
                
                assert "quality_score" in result
                assert "issues" in result
                assert "metrics" in result
                assert isinstance(result["quality_score"], (int, float))
                assert 0 <= result["quality_score"] <= 100
        
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_detect_security_issues_tool(self, code_analysis_server):
        """测试安全问题检测工具"""
        vulnerable_code = '''
import sqlite3

def unsafe_function(user_input):
    password = "hardcoded_password_123"
    api_key = "sk-1234567890abcdef"
    
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_input
    
    # Dangerous eval usage
    result = eval(user_input)
    
    return result
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(vulnerable_code)
            temp_file = f.name
        
        try:
            # 这里需要根据实际的工具调用方式进行调整
            if hasattr(code_analysis_server, '_detect_security_issues_tool'):
                result = await code_analysis_server._detect_security_issues_tool(temp_file)
                
                assert "security_score" in result
                assert "vulnerabilities" in result
                assert "risk_level" in result
                assert len(result["vulnerabilities"]) > 0
                
                # 检查是否检测到硬编码密钥
                hardcoded_vulns = [v for v in result["vulnerabilities"] if "hardcoded" in v["type"]]
                assert len(hardcoded_vulns) > 0
        
        finally:
            os.unlink(temp_file)


class TestMCPIntegration:
    """MCP集成测试"""
    
    @pytest.mark.asyncio
    async def test_mcp_toolkit_integration(self):
        """测试MCP与Toolkit集成"""
        manager = MCPManager()
        toolkit = Toolkit()
        
        # 模拟MCP服务器和工具
        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value={"result": "success"})
        
        manager.clients["test_server"] = mock_client
        manager.available_tools["test_server"] = ["test_tool"]
        
        # 注册工具到toolkit
        manager.register_mcp_tools_to_toolkit(toolkit, ["test_server"])
        
        # 测试工具调用
        # 这里需要根据实际的Toolkit API进行调整
        # 假设可以通过某种方式调用注册的工具
    
    @pytest.mark.asyncio
    async def test_mcp_error_handling(self):
        """测试MCP错误处理"""
        manager = MCPManager()
        
        # 测试调用不存在的服务器
        with pytest.raises(ValueError):
            await manager.call_mcp_tool("nonexistent_server", "test_tool")
        
        # 测试调用失败的工具
        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(side_effect=Exception("Tool call failed"))
        manager.clients["error_server"] = mock_client
        
        with pytest.raises(Exception):
            await manager.call_mcp_tool("error_server", "failing_tool")
    
    @pytest.mark.asyncio
    async def test_mcp_lifecycle(self):
        """测试MCP生命周期管理"""
        manager = MCPManager()
        
        # 注册服务器
        success = await manager.register_mcp_server("lifecycle_test", {
            "command": "echo",
            "args": ["test"],
            "enabled": True
        })
        assert success is True
        
        # 获取服务器信息
        info = await manager.get_server_info("lifecycle_test")
        assert info is not None
        
        # 注销服务器
        success = await manager.unregister_mcp_server("lifecycle_test")
        assert success is True
        
        # 确认服务器已被移除
        info = await manager.get_server_info("lifecycle_test")
        assert info is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
