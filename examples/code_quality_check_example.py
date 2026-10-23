#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量检查使用示例

这个示例展示了如何使用ComplianceAuditorAgent进行详细的代码质量检查，
包括静态分析、编码规范检查、复杂度分析等。
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from agentscope.model import OpenAIModel
from agentscope.formatter import JSONFormatter

from agentscope_integration.agents.compliance_auditor_agent import ComplianceAuditorAgent
from agentscope_integration.interfaces.agent_interface import TaskType, AgentTask


class CodeQualityChecker:
    """代码质量检查器"""
    
    def __init__(self, model_config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        
        # 配置模型
        if model_config is None:
            model_config = {
                "model_name": "gpt-4",
                "api_key": "your_openai_api_key"  # 从环境变量获取
            }
        
        self.model = OpenAIModel(**model_config)
        self.formatter = JSONFormatter()
        
        # 创建智能体
        self.compliance_auditor = ComplianceAuditorAgent(
            model=self.model,
            formatter=self.formatter
        )
        
        self.logger.info("Code quality checker initialized")
    
    async def check_single_file(self, file_path: str) -> Dict[str, Any]:
        """检查单个文件的代码质量"""
        self.logger.info(f"Checking code quality for: {file_path}")
        
        task = AgentTask(
            id=f"quality_check_{Path(file_path).stem}",
            type=TaskType.QUALITY_CHECK,
            title=f"Quality Check: {Path(file_path).name}",
            description=f"Comprehensive quality check for {file_path}",
            parameters={
                "file_path": file_path,
                "check_types": [
                    "static_analysis",
                    "coding_standards", 
                    "complexity",
                    "maintainability",
                    "documentation"
                ],
                "severity_threshold": "low"
            }
        )
        
        result = await self.compliance_auditor.execute_task(task)
        
        if result.status.value == "completed":
            return result.result
        else:
            self.logger.error(f"Quality check failed: {result.error}")
            return {"error": result.error}
    
    async def check_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """检查多个文件的代码质量"""
        self.logger.info(f"Checking code quality for {len(file_paths)} files")
        
        results = {}
        overall_metrics = {
            "total_files": len(file_paths),
            "files_with_issues": 0,
            "total_issues": 0,
            "quality_scores": [],
            "issue_categories": {}
        }
        
        for file_path in file_paths:
            try:
                file_result = await self.check_single_file(file_path)
                results[file_path] = file_result
                
                # 更新总体指标
                if "issues" in file_result and file_result["issues"]:
                    overall_metrics["files_with_issues"] += 1
                    overall_metrics["total_issues"] += len(file_result["issues"])
                    
                    # 统计问题类别
                    for issue in file_result["issues"]:
                        category = issue.get("category", "unknown")
                        overall_metrics["issue_categories"][category] = \
                            overall_metrics["issue_categories"].get(category, 0) + 1
                
                if "quality_score" in file_result:
                    overall_metrics["quality_scores"].append(file_result["quality_score"])
                
            except Exception as e:
                self.logger.error(f"Failed to check {file_path}: {e}")
                results[file_path] = {"error": str(e)}
        
        # 计算平均质量分数
        if overall_metrics["quality_scores"]:
            overall_metrics["average_quality_score"] = \
                sum(overall_metrics["quality_scores"]) / len(overall_metrics["quality_scores"])
        
        return {
            "file_results": results,
            "overall_metrics": overall_metrics
        }
    
    async def check_project_directory(self, project_path: str, 
                                    file_patterns: List[str] = None) -> Dict[str, Any]:
        """检查项目目录中的代码质量"""
        if file_patterns is None:
            file_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c"]
        
        project_dir = Path(project_path)
        if not project_dir.exists():
            raise ValueError(f"Project directory does not exist: {project_path}")
        
        # 收集文件
        files_to_check = []
        for pattern in file_patterns:
            files_to_check.extend(project_dir.rglob(pattern))
        
        # 过滤掉不需要检查的文件
        excluded_patterns = [
            "*/node_modules/*",
            "*/__pycache__/*",
            "*/venv/*",
            "*/env/*",
            "*/.git/*",
            "*/dist/*",
            "*/build/*"
        ]
        
        filtered_files = []
        for file_path in files_to_check:
            file_str = str(file_path)
            if not any(pattern.replace("*", "") in file_str for pattern in excluded_patterns):
                filtered_files.append(file_str)
        
        self.logger.info(f"Found {len(filtered_files)} files to check in {project_path}")
        
        # 限制文件数量以避免过多的API调用
        if len(filtered_files) > 50:
            self.logger.warning(f"Too many files ({len(filtered_files)}), limiting to first 50")
            filtered_files = filtered_files[:50]
        
        return await self.check_multiple_files(filtered_files)
    
    async def generate_quality_report(self, check_results: Dict[str, Any], 
                                    output_path: str = None) -> str:
        """生成质量报告"""
        self.logger.info("Generating quality report")
        
        task = AgentTask(
            id="quality_report_generation",
            type=TaskType.QUALITY_CHECK,
            title="Quality Report Generation",
            description="Generate comprehensive quality report from analysis results",
            parameters={
                "analysis_results": check_results,
                "report_format": "markdown",
                "include_recommendations": True,
                "include_metrics": True
            }
        )
        
        result = await self.compliance_auditor.execute_task(task)
        
        if result.status.value == "completed":
            report_content = result.result.get("report", "")
            
            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                self.logger.info(f"Quality report saved to {output_file}")
            
            return report_content
        else:
            self.logger.error(f"Report generation failed: {result.error}")
            return f"Report generation failed: {result.error}"
    
    def print_summary(self, check_results: Dict[str, Any]):
        """打印检查结果摘要"""
        if "overall_metrics" not in check_results:
            print("No overall metrics available")
            return
        
        metrics = check_results["overall_metrics"]
        
        print("\n" + "="*50)
        print("CODE QUALITY CHECK SUMMARY")
        print("="*50)
        
        print(f"Total Files Checked: {metrics['total_files']}")
        print(f"Files with Issues: {metrics['files_with_issues']}")
        print(f"Total Issues Found: {metrics['total_issues']}")
        
        if "average_quality_score" in metrics:
            score = metrics["average_quality_score"]
            print(f"Average Quality Score: {score:.1f}/100")
            
            # 质量等级
            if score >= 90:
                grade = "Excellent"
            elif score >= 80:
                grade = "Good"
            elif score >= 70:
                grade = "Fair"
            elif score >= 60:
                grade = "Poor"
            else:
                grade = "Very Poor"
            
            print(f"Quality Grade: {grade}")
        
        # 问题类别统计
        if metrics["issue_categories"]:
            print("\nIssue Categories:")
            for category, count in sorted(metrics["issue_categories"].items()):
                print(f"  {category}: {count}")
        
        print("="*50)


async def example_single_file_check():
    """单文件检查示例"""
    print("=== Single File Quality Check Example ===")
    
    checker = CodeQualityChecker()
    
    # 检查单个文件
    file_path = "examples/sample_code.py"  # 替换为实际文件路径
    
    try:
        result = await checker.check_single_file(file_path)
        
        print(f"\nQuality check results for {file_path}:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error checking file: {e}")


async def example_project_check():
    """项目检查示例"""
    print("=== Project Quality Check Example ===")
    
    checker = CodeQualityChecker()
    
    # 检查整个项目
    project_path = "."  # 当前目录
    
    try:
        results = await checker.check_project_directory(
            project_path,
            file_patterns=["*.py"]  # 只检查Python文件
        )
        
        # 打印摘要
        checker.print_summary(results)
        
        # 生成详细报告
        report = await checker.generate_quality_report(
            results,
            output_path="reports/quality_report.md"
        )
        
        print(f"\nDetailed report preview:")
        print(report[:500] + "..." if len(report) > 500 else report)
        
        # 保存完整结果
        with open("reports/quality_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print("\nFull results saved to reports/quality_results.json")
        
    except Exception as e:
        print(f"Error checking project: {e}")


async def example_custom_rules_check():
    """自定义规则检查示例"""
    print("=== Custom Rules Quality Check Example ===")
    
    checker = CodeQualityChecker()
    
    # 创建自定义检查任务
    task = AgentTask(
        id="custom_quality_check",
        type=TaskType.QUALITY_CHECK,
        title="Custom Quality Check",
        description="Quality check with custom rules",
        parameters={
            "file_path": "examples/sample_code.py",
            "custom_rules": {
                "max_line_length": 120,
                "max_function_length": 50,
                "max_complexity": 10,
                "require_docstrings": True,
                "enforce_type_hints": True
            },
            "check_types": ["custom_rules", "static_analysis"],
            "severity_threshold": "medium"
        }
    )
    
    try:
        result = await checker.compliance_auditor.execute_task(task)
        
        if result.status.value == "completed":
            print("Custom rules check completed:")
            print(json.dumps(result.result, indent=2))
        else:
            print(f"Custom rules check failed: {result.error}")
            
    except Exception as e:
        print(f"Error in custom rules check: {e}")


async def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("AgentScope Code Quality Check Examples")
    print("=====================================")
    
    # 运行示例
    await example_single_file_check()
    print("\n")
    
    await example_project_check()
    print("\n")
    
    await example_custom_rules_check()


if __name__ == "__main__":
    asyncio.run(main())
