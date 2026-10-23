#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Augment集成测试套件 - 测试通过自然语言指令触发代码修改的完整流程
"""

import asyncio
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import time


class AugmentIntegrationTestSuite:
    """Augment集成测试套件"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.logger = logging.getLogger(__name__)
        self.backend_url = backend_url
        
        # 测试环境
        self.test_workspace = None
        self.test_scenarios = []
        self.test_results = []
        
        # Augment模拟器
        self.augment_commands = []
        
        self.logger.info("Augment integration test suite initialized")
    
    async def setup_test_environment(self):
        """设置测试环境"""
        self.logger.info("Setting up Augment integration test environment...")
        
        # 创建临时工作区
        self.test_workspace = Path(tempfile.mkdtemp(prefix="augment_test_"))
        
        # 创建测试项目
        await self._create_test_project()
        
        # 定义测试场景
        self._define_test_scenarios()
        
        self.logger.info(f"Test environment ready at: {self.test_workspace}")
    
    async def _create_test_project(self):
        """创建测试项目"""
        # 创建有问题的Python代码
        problematic_code = '''
import os
import sqlite3

class UserManager:
    def __init__(self):
        self.db_path = "users.db"
        self.api_key = "sk-1234567890abcdef"  # 硬编码API密钥
    
    def get_user(self, user_id):
        # SQL注入漏洞
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        return cursor.fetchone()
    
    def authenticate_user(self, username, password):
        # 不安全的密码比较
        if password == "admin123":  # 硬编码密码
            return True
        return False
    
    def process_file(self, filename):
        # 路径遍历漏洞
        file_path = "/var/uploads/" + filename
        with open(file_path, 'r') as f:
            return f.read()
    
    def execute_command(self, cmd):
        # 命令注入漏洞
        os.system(cmd)
    
    # 缺少文档字符串的复杂函数
    def complex_calculation(self, a, b, c, d, e, f, g, h):
        result = 0
        for i in range(100):
            if i % 2 == 0:
                if i % 4 == 0:
                    if i % 8 == 0:
                        if i % 16 == 0:
                            result += a * b * c * d * e * f * g * h
        return result
'''
        
        # 创建JavaScript代码
        js_code = '''
function processUserInput(input) {
    // XSS漏洞
    document.getElementById("output").innerHTML = input;
    
    // 使用eval
    var result = eval(input);
    
    // 硬编码API密钥
    var apiKey = "sk-abcdef1234567890";
    
    return result;
}

// 过长的函数行
function longLineFunction() { var a = 1; var b = 2; var c = 3; var d = 4; var e = 5; var f = 6; var g = 7; var h = 8; var i = 9; var j = 10; return a + b + c + d + e + f + g + h + i + j; }
'''
        
        # 保存测试文件
        (self.test_workspace / "user_manager.py").write_text(problematic_code)
        (self.test_workspace / "frontend.js").write_text(js_code)
        
        # 创建配置文件
        (self.test_workspace / "requirements.txt").write_text("requests==2.28.0\nsqlite3")
        (self.test_workspace / "package.json").write_text('{"name": "test-project", "version": "1.0.0"}')
    
    def _define_test_scenarios(self):
        """定义测试场景"""
        self.test_scenarios = [
            {
                "name": "natural_language_code_analysis",
                "description": "通过自然语言指令触发代码分析",
                "augment_command": "请分析这个Python文件中的代码质量问题，特别关注安全漏洞和编码规范",
                "target_file": "user_manager.py",
                "expected_task_type": "code_analysis",
                "expected_findings": ["sql_injection", "hardcoded_secrets", "complexity_issues"]
            },
            {
                "name": "security_focused_analysis",
                "description": "专注于安全问题的分析",
                "augment_command": "扫描这个文件中的安全漏洞，包括SQL注入、XSS和硬编码密钥",
                "target_file": "user_manager.py",
                "expected_task_type": "security_scan",
                "expected_findings": ["sql_injection", "hardcoded_api_key", "command_injection"]
            },
            {
                "name": "quality_improvement_suggestions",
                "description": "获取代码质量改进建议",
                "augment_command": "检查这个文件的代码质量，提供改进建议，特别是函数复杂度和文档",
                "target_file": "user_manager.py",
                "expected_task_type": "quality_check",
                "expected_findings": ["missing_docstrings", "high_complexity", "too_many_parameters"]
            },
            {
                "name": "multi_file_analysis",
                "description": "多文件分析",
                "augment_command": "分析整个项目的代码质量和安全问题",
                "target_file": None,  # 整个项目
                "expected_task_type": "code_analysis",
                "expected_findings": ["multiple_vulnerabilities", "cross_file_issues"]
            },
            {
                "name": "dependency_security_check",
                "description": "依赖安全检查",
                "augment_command": "检查项目依赖中的安全漏洞",
                "target_file": "requirements.txt",
                "expected_task_type": "dependency_analysis",
                "expected_findings": ["outdated_dependencies", "vulnerable_packages"]
            }
        ]
    
    async def test_natural_language_command_processing(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """测试自然语言命令处理"""
        test_name = f"nl_command_{scenario['name']}"
        self.logger.info(f"Testing scenario: {scenario['name']}")
        
        try:
            # 模拟Augment Agent接收自然语言指令
            command_processed = await self._process_augment_command(scenario)
            
            if not command_processed:
                return {
                    "test_name": test_name,
                    "status": "failed",
                    "message": "Failed to process natural language command",
                    "details": {"scenario": scenario["name"]}
                }
            
            # 验证任务是否正确创建
            task_created = await self._verify_task_creation(scenario)
            
            if not task_created:
                return {
                    "test_name": test_name,
                    "status": "failed",
                    "message": "Task was not created correctly",
                    "details": {"scenario": scenario["name"]}
                }
            
            # 等待任务完成
            task_result = await self._wait_for_task_completion(scenario)
            
            if not task_result:
                return {
                    "test_name": test_name,
                    "status": "failed",
                    "message": "Task did not complete successfully",
                    "details": {"scenario": scenario["name"]}
                }
            
            # 验证结果质量
            result_quality = await self._verify_result_quality(scenario, task_result)
            
            return {
                "test_name": test_name,
                "status": "passed" if result_quality["valid"] else "failed",
                "message": result_quality["message"],
                "details": {
                    "scenario": scenario["name"],
                    "command_processed": command_processed,
                    "task_created": task_created,
                    "task_completed": bool(task_result),
                    "result_quality": result_quality
                }
            }
            
        except Exception as e:
            return {
                "test_name": test_name,
                "status": "error",
                "message": f"Test failed with error: {e}",
                "details": {"scenario": scenario["name"], "error": str(e)}
            }
    
    async def _process_augment_command(self, scenario: Dict[str, Any]) -> bool:
        """模拟处理Augment命令"""
        try:
            # 模拟自然语言处理
            command = scenario["augment_command"]
            target_file = scenario.get("target_file")
            
            # 解析命令意图
            intent = self._parse_command_intent(command)
            
            # 确定目标文件
            if target_file:
                file_path = str(self.test_workspace / target_file)
            else:
                file_path = str(self.test_workspace)
            
            # 创建任务请求
            task_data = {
                "type": intent["task_type"],
                "title": f"Augment Request: {scenario['name']}",
                "description": command,
                "parameters": {
                    "file_path": file_path,
                    "analysis_type": intent["analysis_type"],
                    "natural_language_request": command
                },
                "priority": 2
            }
            
            # 提交任务
            response = requests.post(f"{self.backend_url}/tasks", json=task_data)
            
            if response.status_code == 200:
                scenario["task_id"] = response.json()["task_id"]
                return True
            else:
                self.logger.error(f"Failed to submit task: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing Augment command: {e}")
            return False
    
    def _parse_command_intent(self, command: str) -> Dict[str, str]:
        """解析命令意图"""
        command_lower = command.lower()
        
        # 简单的意图识别
        if "安全" in command or "漏洞" in command or "security" in command_lower:
            return {
                "task_type": "security_scan",
                "analysis_type": "security_focused"
            }
        elif "质量" in command or "quality" in command_lower or "改进" in command:
            return {
                "task_type": "quality_check",
                "analysis_type": "quality_focused"
            }
        elif "依赖" in command or "dependency" in command_lower:
            return {
                "task_type": "dependency_analysis",
                "analysis_type": "dependency_focused"
            }
        else:
            return {
                "task_type": "code_analysis",
                "analysis_type": "comprehensive"
            }
    
    async def _verify_task_creation(self, scenario: Dict[str, Any]) -> bool:
        """验证任务是否正确创建"""
        try:
            if "task_id" not in scenario:
                return False
            
            task_id = scenario["task_id"]
            response = requests.get(f"{self.backend_url}/tasks/{task_id}")
            
            if response.status_code == 200:
                task_data = response.json()
                expected_type = scenario["expected_task_type"]
                actual_type = task_data.get("type")
                
                return actual_type == expected_type
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error verifying task creation: {e}")
            return False
    
    async def _wait_for_task_completion(self, scenario: Dict[str, Any], timeout: int = 120) -> Optional[Dict]:
        """等待任务完成"""
        try:
            task_id = scenario["task_id"]
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                response = requests.get(f"{self.backend_url}/tasks/{task_id}")
                
                if response.status_code == 200:
                    task_data = response.json()
                    status = task_data.get("status")
                    
                    if status == "completed":
                        # 获取任务结果
                        result_response = requests.get(f"{self.backend_url}/tasks/{task_id}/result")
                        if result_response.status_code == 200:
                            return result_response.json()
                    elif status == "failed":
                        self.logger.error(f"Task {task_id} failed")
                        return None
                
                await asyncio.sleep(3)
            
            self.logger.warning(f"Task {task_id} timed out")
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for task completion: {e}")
            return None
    
    async def _verify_result_quality(self, scenario: Dict[str, Any], task_result: Dict) -> Dict[str, Any]:
        """验证结果质量"""
        try:
            expected_findings = scenario.get("expected_findings", [])
            result_data = task_result.get("result", {})
            
            # 检查是否找到了预期的问题
            found_issues = []
            
            if "issues" in result_data:
                issues = result_data["issues"]
                for issue in issues:
                    issue_type = issue.get("type", "").lower()
                    for expected in expected_findings:
                        if expected.lower() in issue_type:
                            found_issues.append(expected)
            
            if "vulnerabilities" in result_data:
                vulnerabilities = result_data["vulnerabilities"]
                for vuln in vulnerabilities:
                    vuln_type = vuln.get("type", "").lower()
                    for expected in expected_findings:
                        if expected.lower() in vuln_type:
                            found_issues.append(expected)
            
            # 计算匹配率
            if expected_findings:
                match_rate = len(set(found_issues)) / len(expected_findings)
                valid = match_rate >= 0.5  # 至少找到50%的预期问题
            else:
                valid = True  # 如果没有特定期望，认为有效
            
            return {
                "valid": valid,
                "message": f"Found {len(found_issues)} of {len(expected_findings)} expected issues",
                "expected_findings": expected_findings,
                "found_issues": list(set(found_issues)),
                "match_rate": match_rate if expected_findings else 1.0,
                "result_summary": {
                    "total_issues": len(result_data.get("issues", [])),
                    "total_vulnerabilities": len(result_data.get("vulnerabilities", [])),
                    "quality_score": result_data.get("quality_score"),
                    "security_score": result_data.get("security_score")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying result quality: {e}")
            return {
                "valid": False,
                "message": f"Error verifying results: {e}",
                "expected_findings": scenario.get("expected_findings", []),
                "found_issues": [],
                "match_rate": 0.0
            }
    
    async def test_multi_agent_collaboration(self) -> Dict[str, Any]:
        """测试多智能体协作"""
        test_name = "multi_agent_collaboration"
        self.logger.info("Testing multi-agent collaboration...")
        
        try:
            # 提交需要多个智能体协作的复杂任务
            task_data = {
                "type": "code_analysis",
                "title": "Comprehensive Project Analysis",
                "description": "Complete analysis requiring multiple agents",
                "parameters": {
                    "project_path": str(self.test_workspace),
                    "analysis_types": ["quality", "security", "architecture"],
                    "require_collaboration": True
                },
                "priority": 1
            }
            
            response = requests.post(f"{self.backend_url}/tasks", json=task_data)
            
            if response.status_code != 200:
                return {
                    "test_name": test_name,
                    "status": "failed",
                    "message": "Failed to submit collaboration task",
                    "details": {}
                }
            
            task_id = response.json()["task_id"]
            
            # 监控智能体状态变化
            agent_activities = await self._monitor_agent_activities(task_id)
            
            # 等待任务完成
            start_time = time.time()
            task_completed = False
            
            while time.time() - start_time < 180:  # 3分钟超时
                response = requests.get(f"{self.backend_url}/tasks/{task_id}")
                if response.status_code == 200:
                    status = response.json().get("status")
                    if status in ["completed", "failed"]:
                        task_completed = (status == "completed")
                        break
                
                await asyncio.sleep(5)
            
            # 验证协作效果
            collaboration_effective = len(agent_activities) >= 2  # 至少两个智能体参与
            
            return {
                "test_name": test_name,
                "status": "passed" if (task_completed and collaboration_effective) else "failed",
                "message": "Multi-agent collaboration successful" if collaboration_effective else "Collaboration failed",
                "details": {
                    "task_completed": task_completed,
                    "agents_involved": len(agent_activities),
                    "agent_activities": agent_activities,
                    "collaboration_effective": collaboration_effective
                }
            }
            
        except Exception as e:
            return {
                "test_name": test_name,
                "status": "error",
                "message": f"Collaboration test failed: {e}",
                "details": {"error": str(e)}
            }
    
    async def _monitor_agent_activities(self, task_id: str) -> List[Dict[str, Any]]:
        """监控智能体活动"""
        activities = []
        
        try:
            # 获取智能体状态
            response = requests.get(f"{self.backend_url}/agents")
            if response.status_code == 200:
                agents = response.json()
                
                for agent in agents:
                    if agent.get("current_task") == task_id:
                        activities.append({
                            "agent_id": agent["agent_id"],
                            "role": agent["role"],
                            "status": agent["status"],
                            "task_id": task_id
                        })
            
        except Exception as e:
            self.logger.error(f"Error monitoring agent activities: {e}")
        
        return activities
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有Augment集成测试"""
        self.logger.info("Starting Augment integration test suite...")
        
        try:
            # 设置测试环境
            await self.setup_test_environment()
            
            # 运行场景测试
            for scenario in self.test_scenarios:
                result = await self.test_natural_language_command_processing(scenario)
                self.test_results.append(result)
                await asyncio.sleep(2)  # 测试间隔
            
            # 运行多智能体协作测试
            collaboration_result = await self.test_multi_agent_collaboration()
            self.test_results.append(collaboration_result)
            
            # 生成测试报告
            report = self._generate_test_report()
            
            return report
            
        except Exception as e:
            self.logger.error(f"Augment integration test suite failed: {e}")
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
            "scenarios_tested": len(self.test_scenarios),
            "timestamp": time.time()
        }
    
    async def cleanup_test_environment(self):
        """清理测试环境"""
        self.logger.info("Cleaning up Augment integration test environment...")
        
        try:
            # 删除临时工作区
            if self.test_workspace and self.test_workspace.exists():
                shutil.rmtree(self.test_workspace)
            
            self.logger.info("Test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


async def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    test_suite = AugmentIntegrationTestSuite()
    report = await test_suite.run_all_tests()
    
    print("\n" + "="*60)
    print("AUGMENT INTEGRATION TEST REPORT")
    print("="*60)
    
    summary = report["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Errors: {summary['errors']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Scenarios Tested: {report['scenarios_tested']}")
    
    print("\nDetailed Results:")
    for result in report["results"]:
        status_icon = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⚠️"
        print(f"{status_icon} {result['test_name']}: {result['message']}")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
