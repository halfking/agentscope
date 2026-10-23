#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的项目分析工作流示例

这个示例展示了如何使用AgentScope多智能体编程工作流进行完整的项目分析，
包括代码分析、质量检查、安全扫描和测试分析。
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from agentscope.model import OpenAIModel
from agentscope.formatter import JSONFormatter

from agentscope_integration.core.agent_coordinator import AgentCoordinator
from agentscope_integration.core.task_manager import TaskManager
from agentscope_integration.mcp.mcp_manager import MCPManager
from agentscope_integration.agents.code_manager_agent import CodeManagerAgent
from agentscope_integration.agents.compliance_auditor_agent import ComplianceAuditorAgent
from agentscope_integration.interfaces.agent_interface import TaskType


class ProjectAnalysisWorkflow:
    """项目分析工作流"""
    
    def __init__(self, project_path: str, config_path: str = None):
        self.project_path = Path(project_path)
        self.config_path = config_path
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.agent_coordinator = None
        self.task_manager = None
        self.mcp_manager = None
        self.agents = {}
        
        # 分析结果
        self.analysis_results = {}
    
    async def initialize(self):
        """初始化工作流组件"""
        self.logger.info("Initializing project analysis workflow...")
        
        # 初始化MCP管理器
        self.mcp_manager = MCPManager(self.config_path)
        await self.mcp_manager.start_all_servers()
        
        # 初始化智能体协调器
        self.agent_coordinator = AgentCoordinator()
        
        # 初始化任务管理器
        self.task_manager = TaskManager(self.agent_coordinator)
        await self.task_manager.start()
        
        # 创建和注册智能体
        await self._create_agents()
        
        self.logger.info("Workflow initialization completed")
    
    async def _create_agents(self):
        """创建和注册智能体"""
        # 创建LLM模型
        model = OpenAIModel(
            model_name="gpt-4",
            api_key="your_openai_api_key"  # 在实际使用中从环境变量获取
        )
        
        formatter = JSONFormatter()
        
        # 创建代码管理员智能体
        code_manager = CodeManagerAgent(
            model=model,
            formatter=formatter
        )
        
        # 注册MCP工具
        toolkit = code_manager.toolkit
        self.mcp_manager.register_mcp_tools_to_toolkit(toolkit, ["filesystem", "git", "code_analysis"])
        
        await self.agent_coordinator.register_agent(code_manager)
        self.agents["code_manager"] = code_manager
        
        # 创建规范审核员智能体
        compliance_auditor = ComplianceAuditorAgent(
            model=model,
            formatter=formatter
        )
        
        # 注册MCP工具
        toolkit = compliance_auditor.toolkit
        self.mcp_manager.register_mcp_tools_to_toolkit(toolkit, ["filesystem", "code_analysis"])
        
        await self.agent_coordinator.register_agent(compliance_auditor)
        self.agents["compliance_auditor"] = compliance_auditor
        
        self.logger.info(f"Created and registered {len(self.agents)} agents")
    
    async def run_complete_analysis(self) -> Dict[str, Any]:
        """运行完整的项目分析"""
        self.logger.info(f"Starting complete analysis of project: {self.project_path}")
        
        try:
            # 1. 项目结构分析
            structure_result = await self._analyze_project_structure()
            self.analysis_results["structure"] = structure_result
            
            # 2. 代码质量分析
            quality_result = await self._analyze_code_quality()
            self.analysis_results["quality"] = quality_result
            
            # 3. 安全漏洞扫描
            security_result = await self._scan_security_vulnerabilities()
            self.analysis_results["security"] = security_result
            
            # 4. 依赖关系分析
            dependency_result = await self._analyze_dependencies()
            self.analysis_results["dependencies"] = dependency_result
            
            # 5. 测试覆盖率分析
            test_result = await self._analyze_test_coverage()
            self.analysis_results["testing"] = test_result
            
            # 6. 生成综合报告
            report = await self._generate_comprehensive_report()
            self.analysis_results["report"] = report
            
            self.logger.info("Complete analysis finished successfully")
            return self.analysis_results
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise
    
    async def _analyze_project_structure(self) -> Dict[str, Any]:
        """分析项目结构"""
        self.logger.info("Analyzing project structure...")
        
        task_id = await self.task_manager.create_task(
            task_type=TaskType.ARCHITECTURE_REVIEW,
            title="Project Structure Analysis",
            description=f"Analyze the structure of project at {self.project_path}",
            parameters={
                "project_path": str(self.project_path),
                "analysis_type": "structure",
                "include_metrics": True
            },
            priority=3
        )
        
        # 等待任务完成
        result = await self._wait_for_task_completion(task_id)
        return result.result if result else {}
    
    async def _analyze_code_quality(self) -> Dict[str, Any]:
        """分析代码质量"""
        self.logger.info("Analyzing code quality...")
        
        # 获取所有Python文件
        python_files = list(self.project_path.rglob("*.py"))
        quality_results = []
        
        # 分析每个文件
        for file_path in python_files[:10]:  # 限制文件数量以避免过多任务
            task_id = await self.task_manager.create_task(
                task_type=TaskType.QUALITY_CHECK,
                title=f"Quality Check: {file_path.name}",
                description=f"Analyze code quality for {file_path}",
                parameters={
                    "file_path": str(file_path),
                    "check_types": ["static_analysis", "coding_standards", "complexity"]
                },
                priority=4
            )
            
            result = await self._wait_for_task_completion(task_id)
            if result:
                quality_results.append({
                    "file": str(file_path),
                    "result": result.result
                })
        
        return {
            "files_analyzed": len(quality_results),
            "results": quality_results,
            "overall_score": self._calculate_overall_quality_score(quality_results)
        }
    
    async def _scan_security_vulnerabilities(self) -> Dict[str, Any]:
        """扫描安全漏洞"""
        self.logger.info("Scanning for security vulnerabilities...")
        
        task_id = await self.task_manager.create_task(
            task_type=TaskType.SECURITY_SCAN,
            title="Security Vulnerability Scan",
            description=f"Scan for security vulnerabilities in {self.project_path}",
            parameters={
                "project_path": str(self.project_path),
                "scan_types": ["vulnerability_scan", "secret_detection", "dependency_check"],
                "severity_threshold": "medium"
            },
            priority=1  # 高优先级
        )
        
        result = await self._wait_for_task_completion(task_id)
        return result.result if result else {}
    
    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """分析依赖关系"""
        self.logger.info("Analyzing dependencies...")
        
        task_id = await self.task_manager.create_task(
            task_type=TaskType.DEPENDENCY_ANALYSIS,
            title="Dependency Analysis",
            description=f"Analyze dependencies for {self.project_path}",
            parameters={
                "project_path": str(self.project_path),
                "include_dev_dependencies": True,
                "check_vulnerabilities": True,
                "check_licenses": True
            },
            priority=4
        )
        
        result = await self._wait_for_task_completion(task_id)
        return result.result if result else {}
    
    async def _analyze_test_coverage(self) -> Dict[str, Any]:
        """分析测试覆盖率"""
        self.logger.info("Analyzing test coverage...")
        
        task_id = await self.task_manager.create_task(
            task_type=TaskType.TEST_ANALYSIS,
            title="Test Coverage Analysis",
            description=f"Analyze test coverage for {self.project_path}",
            parameters={
                "project_path": str(self.project_path),
                "test_frameworks": ["pytest", "unittest"],
                "coverage_threshold": 80
            },
            priority=5
        )
        
        result = await self._wait_for_task_completion(task_id)
        return result.result if result else {}
    
    async def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        self.logger.info("Generating comprehensive report...")
        
        task_id = await self.task_manager.create_task(
            task_type=TaskType.CODE_ANALYSIS,
            title="Comprehensive Report Generation",
            description="Generate comprehensive analysis report",
            parameters={
                "analysis_results": self.analysis_results,
                "project_path": str(self.project_path),
                "report_format": "detailed"
            },
            priority=2
        )
        
        result = await self._wait_for_task_completion(task_id)
        return result.result if result else {}
    
    async def _wait_for_task_completion(self, task_id: str, timeout: int = 300):
        """等待任务完成"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 检查超时
            if asyncio.get_event_loop().time() - start_time > timeout:
                self.logger.warning(f"Task {task_id} timed out")
                return None
            
            # 检查任务状态
            status = await self.task_manager.get_task_status(task_id)
            if not status:
                await asyncio.sleep(1)
                continue
            
            if status["status"] == "completed":
                result = await self.task_manager.get_task_result(task_id)
                return result
            elif status["status"] == "failed":
                self.logger.error(f"Task {task_id} failed")
                return None
            
            await asyncio.sleep(2)
    
    def _calculate_overall_quality_score(self, quality_results: List[Dict]) -> float:
        """计算总体质量分数"""
        if not quality_results:
            return 0.0
        
        scores = []
        for result in quality_results:
            if "result" in result and "quality_score" in result["result"]:
                scores.append(result["result"]["quality_score"])
        
        return sum(scores) / len(scores) if scores else 0.0
    
    async def save_results(self, output_path: str):
        """保存分析结果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Analysis results saved to {output_file}")
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up workflow resources...")
        
        if self.task_manager:
            await self.task_manager.shutdown()
        
        if self.agent_coordinator:
            await self.agent_coordinator.shutdown()
        
        if self.mcp_manager:
            await self.mcp_manager.stop_all_servers()
        
        self.logger.info("Cleanup completed")


async def main():
    """主函数示例"""
    # 配置项目路径
    project_path = "/path/to/your/project"
    config_path = "config/mcp_config.json"
    output_path = "results/analysis_results.json"
    
    # 创建工作流
    workflow = ProjectAnalysisWorkflow(project_path, config_path)
    
    try:
        # 初始化
        await workflow.initialize()
        
        # 运行分析
        results = await workflow.run_complete_analysis()
        
        # 保存结果
        await workflow.save_results(output_path)
        
        # 打印摘要
        print("\n=== Analysis Summary ===")
        if "quality" in results:
            print(f"Overall Quality Score: {results['quality'].get('overall_score', 'N/A')}")
        
        if "security" in results:
            security_result = results["security"]
            vuln_count = len(security_result.get("vulnerabilities", []))
            print(f"Security Vulnerabilities Found: {vuln_count}")
        
        if "testing" in results:
            test_result = results["testing"]
            coverage = test_result.get("coverage_percentage", "N/A")
            print(f"Test Coverage: {coverage}%")
        
        print(f"\nDetailed results saved to: {output_path}")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        raise
    
    finally:
        # 清理资源
        await workflow.cleanup()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
