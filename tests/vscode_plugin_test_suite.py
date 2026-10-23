#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code插件测试套件 - 自动化测试VS Code插件的安装、配置和功能
"""

import asyncio
import json
import logging
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import websocket
import threading


class VSCodePluginTestSuite:
    """VS Code插件测试套件"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.logger = logging.getLogger(__name__)
        self.backend_url = backend_url
        self.websocket_url = backend_url.replace("http", "ws") + "/ws"
        
        # 测试环境
        self.test_workspace = None
        self.vscode_process = None
        self.backend_process = None
        
        # 测试结果
        self.test_results = []
        self.current_test = None
        
        # WebSocket连接
        self.ws = None
        self.ws_messages = []
        
        self.logger.info("VS Code plugin test suite initialized")
    
    async def setup_test_environment(self):
        """设置测试环境"""
        self.logger.info("Setting up test environment...")
        
        # 创建临时工作区
        self.test_workspace = Path(tempfile.mkdtemp(prefix="agentscope_test_"))
        
        # 创建测试项目结构
        await self._create_test_project()
        
        # 启动后端服务
        await self._start_backend_service()
        
        # 等待服务启动
        await self._wait_for_backend()
        
        self.logger.info(f"Test environment ready at: {self.test_workspace}")
    
    async def _create_test_project(self):
        """创建测试项目"""
        # 创建Python测试文件
        python_code = '''
def vulnerable_function(user_input):
    # SQL注入漏洞
    query = "SELECT * FROM users WHERE id = " + user_input
    
    # 硬编码密钥
    api_key = "sk-1234567890abcdef"
    
    # 复杂度过高的函数
    for i in range(100):
        if i % 2 == 0:
            if i % 4 == 0:
                if i % 8 == 0:
                    if i % 16 == 0:
                        print("Too complex")
    
    return query

class BadlyNamedClass:
    def badlyNamedMethod(self):
        password = "hardcoded_password_123"
        return password

# 缺少文档字符串的函数
def undocumented_function(param1, param2, param3, param4, param5, param6):
    return param1 + param2 + param3 + param4 + param5 + param6
'''
        
        # 创建JavaScript测试文件
        js_code = '''
function unsafeFunction(userInput) {
    // XSS漏洞
    document.getElementById("content").innerHTML = userInput;
    
    // 使用eval
    var result = eval(userInput);
    
    // 硬编码API密钥
    var apiKey = "sk-abcdef1234567890";
    
    return result;
}

// 过长的函数
function veryLongFunction() {
    var a = 1; var b = 2; var c = 3; var d = 4; var e = 5; var f = 6; var g = 7; var h = 8; var i = 9; var j = 10;
    return a + b + c + d + e + f + g + h + i + j;
}
'''
        
        # 保存测试文件
        (self.test_workspace / "test_file.py").write_text(python_code)
        (self.test_workspace / "test_file.js").write_text(js_code)
        
        # 创建配置文件
        vscode_settings = {
            "agentscope.backend.host": "localhost",
            "agentscope.backend.port": 8000,
            "agentscope.agents.codeManager.enabled": True,
            "agentscope.agents.complianceAuditor.enabled": True,
            "agentscope.analysis.autoRun": False
        }
        
        vscode_dir = self.test_workspace / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        with open(vscode_dir / "settings.json", 'w') as f:
            json.dump(vscode_settings, f, indent=2)
    
    async def _start_backend_service(self):
        """启动后端服务"""
        try:
            # 启动AgentScope后端
            cmd = [
                "python", "-m", "agentscope_integration.main",
                "--host", "localhost",
                "--port", "8000"
            ]
            
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path.cwd()
            )
            
            self.logger.info("Backend service started")
            
        except Exception as e:
            self.logger.error(f"Failed to start backend service: {e}")
            raise
    
    async def _wait_for_backend(self, timeout: int = 30):
        """等待后端服务启动"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.backend_url}/health", timeout=5)
                if response.status_code == 200:
                    self.logger.info("Backend service is ready")
                    return
            except requests.RequestException:
                pass
            
            await asyncio.sleep(1)
        
        raise TimeoutError("Backend service failed to start within timeout")
    
    def _setup_websocket(self):
        """设置WebSocket连接"""
        def on_message(ws, message):
            self.ws_messages.append(json.loads(message))
        
        def on_error(ws, error):
            self.logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            self.logger.info("WebSocket connection closed")
        
        def on_open(ws):
            self.logger.info("WebSocket connection opened")
            # 订阅所有事件
            ws.send(json.dumps({
                "type": "subscribe",
                "event_types": ["task_started", "task_completed", "agent_status_updated"]
            }))
        
        self.ws = websocket.WebSocketApp(
            self.websocket_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # 在后台线程中运行WebSocket
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 等待连接建立
        time.sleep(2)
    
    async def test_plugin_installation(self) -> Dict[str, Any]:
        """测试插件安装"""
        self.current_test = "plugin_installation"
        self.logger.info("Testing plugin installation...")
        
        try:
            # 检查插件是否已安装
            result = subprocess.run([
                "code", "--list-extensions"
            ], capture_output=True, text=True)
            
            installed_extensions = result.stdout.strip().split('\n')
            plugin_installed = any("agentscope" in ext.lower() for ext in installed_extensions)
            
            test_result = {
                "test_name": "plugin_installation",
                "status": "passed" if plugin_installed else "failed",
                "message": "Plugin installed successfully" if plugin_installed else "Plugin not found",
                "details": {
                    "installed_extensions": installed_extensions,
                    "plugin_found": plugin_installed
                }
            }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            test_result = {
                "test_name": "plugin_installation",
                "status": "error",
                "message": f"Installation test failed: {e}",
                "details": {"error": str(e)}
            }
            
            self.test_results.append(test_result)
            return test_result
    
    async def test_backend_connection(self) -> Dict[str, Any]:
        """测试后端连接"""
        self.current_test = "backend_connection"
        self.logger.info("Testing backend connection...")
        
        try:
            # 测试REST API连接
            response = requests.get(f"{self.backend_url}/health")
            api_connected = response.status_code == 200
            
            # 测试WebSocket连接
            self._setup_websocket()
            ws_connected = self.ws is not None
            
            # 测试智能体状态
            agents_response = requests.get(f"{self.backend_url}/agents")
            agents_available = agents_response.status_code == 200
            
            test_result = {
                "test_name": "backend_connection",
                "status": "passed" if (api_connected and ws_connected and agents_available) else "failed",
                "message": "Backend connection successful",
                "details": {
                    "api_connected": api_connected,
                    "websocket_connected": ws_connected,
                    "agents_available": agents_available,
                    "agents_count": len(agents_response.json()) if agents_available else 0
                }
            }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            test_result = {
                "test_name": "backend_connection",
                "status": "error",
                "message": f"Connection test failed: {e}",
                "details": {"error": str(e)}
            }
            
            self.test_results.append(test_result)
            return test_result
    
    async def test_code_analysis_workflow(self) -> Dict[str, Any]:
        """测试代码分析工作流"""
        self.current_test = "code_analysis_workflow"
        self.logger.info("Testing code analysis workflow...")
        
        try:
            # 清空WebSocket消息
            self.ws_messages.clear()
            
            # 提交代码分析任务
            task_data = {
                "type": "code_analysis",
                "title": "Test Code Analysis",
                "description": "Automated test of code analysis",
                "parameters": {
                    "file_path": str(self.test_workspace / "test_file.py")
                },
                "priority": 3
            }
            
            response = requests.post(f"{self.backend_url}/tasks", json=task_data)
            task_submitted = response.status_code == 200
            
            if task_submitted:
                task_id = response.json()["task_id"]
                
                # 等待任务完成
                task_completed = await self._wait_for_task_completion(task_id)
                
                # 获取任务结果
                if task_completed:
                    result_response = requests.get(f"{self.backend_url}/tasks/{task_id}/result")
                    result_available = result_response.status_code == 200
                    
                    if result_available:
                        result_data = result_response.json()
                        analysis_successful = result_data["status"] == "completed"
                    else:
                        analysis_successful = False
                else:
                    analysis_successful = False
                    result_available = False
            else:
                task_completed = False
                result_available = False
                analysis_successful = False
            
            test_result = {
                "test_name": "code_analysis_workflow",
                "status": "passed" if analysis_successful else "failed",
                "message": "Code analysis workflow completed successfully" if analysis_successful else "Workflow failed",
                "details": {
                    "task_submitted": task_submitted,
                    "task_completed": task_completed,
                    "result_available": result_available,
                    "analysis_successful": analysis_successful,
                    "websocket_messages_received": len(self.ws_messages)
                }
            }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            test_result = {
                "test_name": "code_analysis_workflow",
                "status": "error",
                "message": f"Workflow test failed: {e}",
                "details": {"error": str(e)}
            }
            
            self.test_results.append(test_result)
            return test_result
    
    async def test_quality_check_workflow(self) -> Dict[str, Any]:
        """测试质量检查工作流"""
        self.current_test = "quality_check_workflow"
        self.logger.info("Testing quality check workflow...")
        
        try:
            # 提交质量检查任务
            task_data = {
                "type": "quality_check",
                "title": "Test Quality Check",
                "description": "Automated test of quality check",
                "parameters": {
                    "file_path": str(self.test_workspace / "test_file.py"),
                    "check_types": ["static_analysis", "coding_standards", "complexity"]
                },
                "priority": 3
            }
            
            response = requests.post(f"{self.backend_url}/tasks", json=task_data)
            task_id = response.json()["task_id"]
            
            # 等待任务完成
            task_completed = await self._wait_for_task_completion(task_id)
            
            if task_completed:
                # 获取结果
                result_response = requests.get(f"{self.backend_url}/tasks/{task_id}/result")
                result_data = result_response.json()
                
                # 验证质量检查结果
                issues_found = len(result_data.get("result", {}).get("issues", []))
                quality_score = result_data.get("result", {}).get("quality_score", 0)
                
                # 预期应该发现问题（因为测试文件故意包含问题）
                expected_issues = issues_found > 0
                reasonable_score = 0 <= quality_score <= 100
                
                test_result = {
                    "test_name": "quality_check_workflow",
                    "status": "passed" if (expected_issues and reasonable_score) else "failed",
                    "message": "Quality check completed and found expected issues",
                    "details": {
                        "task_completed": task_completed,
                        "issues_found": issues_found,
                        "quality_score": quality_score,
                        "expected_issues": expected_issues,
                        "reasonable_score": reasonable_score
                    }
                }
            else:
                test_result = {
                    "test_name": "quality_check_workflow",
                    "status": "failed",
                    "message": "Quality check task did not complete",
                    "details": {"task_completed": False}
                }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            test_result = {
                "test_name": "quality_check_workflow",
                "status": "error",
                "message": f"Quality check test failed: {e}",
                "details": {"error": str(e)}
            }
            
            self.test_results.append(test_result)
            return test_result
    
    async def test_security_scan_workflow(self) -> Dict[str, Any]:
        """测试安全扫描工作流"""
        self.current_test = "security_scan_workflow"
        self.logger.info("Testing security scan workflow...")
        
        try:
            # 提交安全扫描任务
            task_data = {
                "type": "security_scan",
                "title": "Test Security Scan",
                "description": "Automated test of security scan",
                "parameters": {
                    "file_path": str(self.test_workspace / "test_file.py"),
                    "scan_types": ["vulnerability_scan", "secret_detection"]
                },
                "priority": 1
            }
            
            response = requests.post(f"{self.backend_url}/tasks", json=task_data)
            task_id = response.json()["task_id"]
            
            # 等待任务完成
            task_completed = await self._wait_for_task_completion(task_id)
            
            if task_completed:
                # 获取结果
                result_response = requests.get(f"{self.backend_url}/tasks/{task_id}/result")
                result_data = result_response.json()
                
                # 验证安全扫描结果
                vulnerabilities = result_data.get("result", {}).get("vulnerabilities", [])
                security_score = result_data.get("result", {}).get("security_score", 100)
                
                # 预期应该发现安全问题
                vulnerabilities_found = len(vulnerabilities) > 0
                reasonable_score = 0 <= security_score <= 100
                
                test_result = {
                    "test_name": "security_scan_workflow",
                    "status": "passed" if (vulnerabilities_found and reasonable_score) else "failed",
                    "message": "Security scan completed and found expected vulnerabilities",
                    "details": {
                        "task_completed": task_completed,
                        "vulnerabilities_found": len(vulnerabilities),
                        "security_score": security_score,
                        "expected_vulnerabilities": vulnerabilities_found,
                        "reasonable_score": reasonable_score
                    }
                }
            else:
                test_result = {
                    "test_name": "security_scan_workflow",
                    "status": "failed",
                    "message": "Security scan task did not complete",
                    "details": {"task_completed": False}
                }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            test_result = {
                "test_name": "security_scan_workflow",
                "status": "error",
                "message": f"Security scan test failed: {e}",
                "details": {"error": str(e)}
            }
            
            self.test_results.append(test_result)
            return test_result
    
    async def _wait_for_task_completion(self, task_id: str, timeout: int = 60) -> bool:
        """等待任务完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.backend_url}/tasks/{task_id}")
                if response.status_code == 200:
                    task_status = response.json()["status"]
                    if task_status in ["completed", "failed"]:
                        return task_status == "completed"
                
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error checking task status: {e}")
                await asyncio.sleep(2)
        
        return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("Starting comprehensive plugin test suite...")
        
        try:
            # 设置测试环境
            await self.setup_test_environment()
            
            # 运行测试
            tests = [
                self.test_plugin_installation(),
                self.test_backend_connection(),
                self.test_code_analysis_workflow(),
                self.test_quality_check_workflow(),
                self.test_security_scan_workflow()
            ]
            
            for test_coro in tests:
                await test_coro
                await asyncio.sleep(1)  # 测试间隔
            
            # 生成测试报告
            report = self._generate_test_report()
            
            return report
            
        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            return {
                "status": "error",
                "message": f"Test suite execution failed: {e}",
                "results": self.test_results
            }
        
        finally:
            await self.cleanup_test_environment()
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "passed"])
        failed_tests = len([r for r in self.test_results if r["status"] == "failed"])
        error_tests = len([r for r in self.test_results if r["status"] == "error"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "status": "completed",
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": success_rate
            },
            "results": self.test_results,
            "timestamp": time.time()
        }
    
    async def cleanup_test_environment(self):
        """清理测试环境"""
        self.logger.info("Cleaning up test environment...")
        
        try:
            # 关闭WebSocket连接
            if self.ws:
                self.ws.close()
            
            # 停止后端服务
            if self.backend_process:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            
            # 删除临时工作区
            if self.test_workspace and self.test_workspace.exists():
                shutil.rmtree(self.test_workspace)
            
            self.logger.info("Test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


async def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    test_suite = VSCodePluginTestSuite()
    report = await test_suite.run_all_tests()
    
    print("\n" + "="*60)
    print("VS CODE PLUGIN TEST REPORT")
    print("="*60)
    
    summary = report["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Errors: {summary['errors']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    
    print("\nDetailed Results:")
    for result in report["results"]:
        status_icon = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⚠️"
        print(f"{status_icon} {result['test_name']}: {result['message']}")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
