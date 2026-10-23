#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全漏洞扫描示例

这个示例展示了如何使用ComplianceAuditorAgent进行安全漏洞扫描，
包括SQL注入、XSS、硬编码密钥、依赖漏洞等检测。
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


class SecurityScanner:
    """安全漏洞扫描器"""
    
    def __init__(self, model_config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        
        # 配置模型
        if model_config is None:
            model_config = {
                "model_name": "gpt-4",
                "api_key": "your_openai_api_key"
            }
        
        self.model = OpenAIModel(**model_config)
        self.formatter = JSONFormatter()
        
        # 创建智能体
        self.compliance_auditor = ComplianceAuditorAgent(
            model=self.model,
            formatter=self.formatter
        )
        
        self.logger.info("Security scanner initialized")
    
    async def scan_file(self, file_path: str, scan_types: List[str] = None) -> Dict[str, Any]:
        """扫描单个文件的安全漏洞"""
        if scan_types is None:
            scan_types = [
                "sql_injection",
                "xss_vulnerabilities", 
                "hardcoded_secrets",
                "insecure_functions",
                "path_traversal",
                "command_injection"
            ]
        
        self.logger.info(f"Scanning security vulnerabilities in: {file_path}")
        
        task = AgentTask(
            id=f"security_scan_{Path(file_path).stem}",
            type=TaskType.SECURITY_SCAN,
            title=f"Security Scan: {Path(file_path).name}",
            description=f"Comprehensive security scan for {file_path}",
            parameters={
                "file_path": file_path,
                "scan_types": scan_types,
                "severity_threshold": "low",
                "include_recommendations": True
            }
        )
        
        result = await self.compliance_auditor.execute_task(task)
        
        if result.status.value == "completed":
            return result.result
        else:
            self.logger.error(f"Security scan failed: {result.error}")
            return {"error": result.error}
    
    async def scan_project(self, project_path: str, 
                          file_patterns: List[str] = None) -> Dict[str, Any]:
        """扫描整个项目的安全漏洞"""
        if file_patterns is None:
            file_patterns = ["*.py", "*.js", "*.ts", "*.php", "*.java"]
        
        project_dir = Path(project_path)
        if not project_dir.exists():
            raise ValueError(f"Project directory does not exist: {project_path}")
        
        # 收集文件
        files_to_scan = []
        for pattern in file_patterns:
            files_to_scan.extend(project_dir.rglob(pattern))
        
        # 过滤文件
        excluded_patterns = [
            "*/node_modules/*",
            "*/__pycache__/*",
            "*/venv/*",
            "*/.git/*",
            "*/test/*",
            "*/tests/*"
        ]
        
        filtered_files = []
        for file_path in files_to_scan:
            file_str = str(file_path)
            if not any(pattern.replace("*", "") in file_str for pattern in excluded_patterns):
                filtered_files.append(file_str)
        
        self.logger.info(f"Scanning {len(filtered_files)} files for security vulnerabilities")
        
        # 限制文件数量
        if len(filtered_files) > 30:
            self.logger.warning(f"Too many files ({len(filtered_files)}), limiting to first 30")
            filtered_files = filtered_files[:30]
        
        # 扫描所有文件
        scan_results = {}
        overall_stats = {
            "total_files": len(filtered_files),
            "files_with_vulnerabilities": 0,
            "total_vulnerabilities": 0,
            "vulnerability_types": {},
            "severity_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0}
        }
        
        for file_path in filtered_files:
            try:
                file_result = await self.scan_file(file_path)
                scan_results[file_path] = file_result
                
                # 更新统计信息
                if "vulnerabilities" in file_result and file_result["vulnerabilities"]:
                    overall_stats["files_with_vulnerabilities"] += 1
                    vulnerabilities = file_result["vulnerabilities"]
                    overall_stats["total_vulnerabilities"] += len(vulnerabilities)
                    
                    for vuln in vulnerabilities:
                        vuln_type = vuln.get("type", "unknown")
                        severity = vuln.get("severity", "low")
                        
                        overall_stats["vulnerability_types"][vuln_type] = \
                            overall_stats["vulnerability_types"].get(vuln_type, 0) + 1
                        
                        overall_stats["severity_distribution"][severity] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to scan {file_path}: {e}")
                scan_results[file_path] = {"error": str(e)}
        
        return {
            "scan_results": scan_results,
            "overall_stats": overall_stats
        }
    
    async def scan_dependencies(self, project_path: str) -> Dict[str, Any]:
        """扫描依赖包的安全漏洞"""
        self.logger.info(f"Scanning dependencies for security vulnerabilities: {project_path}")
        
        task = AgentTask(
            id="dependency_security_scan",
            type=TaskType.SECURITY_SCAN,
            title="Dependency Security Scan",
            description=f"Scan dependencies for known vulnerabilities in {project_path}",
            parameters={
                "project_path": project_path,
                "scan_types": ["dependency_vulnerabilities"],
                "include_dev_dependencies": True,
                "vulnerability_databases": ["nvd", "snyk", "github_advisory"]
            }
        )
        
        result = await self.compliance_auditor.execute_task(task)
        
        if result.status.value == "completed":
            return result.result
        else:
            self.logger.error(f"Dependency scan failed: {result.error}")
            return {"error": result.error}
    
    async def generate_security_report(self, scan_results: Dict[str, Any], 
                                     output_path: str = None) -> str:
        """生成安全报告"""
        self.logger.info("Generating security report")
        
        task = AgentTask(
            id="security_report_generation",
            type=TaskType.SECURITY_SCAN,
            title="Security Report Generation",
            description="Generate comprehensive security report from scan results",
            parameters={
                "scan_results": scan_results,
                "report_format": "markdown",
                "include_remediation": True,
                "include_risk_assessment": True,
                "compliance_frameworks": ["OWASP", "CWE"]
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
                
                self.logger.info(f"Security report saved to {output_file}")
            
            return report_content
        else:
            self.logger.error(f"Report generation failed: {result.error}")
            return f"Report generation failed: {result.error}"
    
    def print_security_summary(self, scan_results: Dict[str, Any]):
        """打印安全扫描摘要"""
        if "overall_stats" not in scan_results:
            print("No security statistics available")
            return
        
        stats = scan_results["overall_stats"]
        
        print("\n" + "="*60)
        print("SECURITY SCAN SUMMARY")
        print("="*60)
        
        print(f"Total Files Scanned: {stats['total_files']}")
        print(f"Files with Vulnerabilities: {stats['files_with_vulnerabilities']}")
        print(f"Total Vulnerabilities Found: {stats['total_vulnerabilities']}")
        
        # 严重程度分布
        severity_dist = stats["severity_distribution"]
        print(f"\nSeverity Distribution:")
        print(f"  Critical: {severity_dist['critical']}")
        print(f"  High: {severity_dist['high']}")
        print(f"  Medium: {severity_dist['medium']}")
        print(f"  Low: {severity_dist['low']}")
        
        # 漏洞类型统计
        if stats["vulnerability_types"]:
            print(f"\nVulnerability Types:")
            for vuln_type, count in sorted(stats["vulnerability_types"].items()):
                print(f"  {vuln_type}: {count}")
        
        # 风险评估
        critical_high = severity_dist['critical'] + severity_dist['high']
        if critical_high > 0:
            risk_level = "HIGH"
        elif severity_dist['medium'] > 5:
            risk_level = "MEDIUM"
        elif stats['total_vulnerabilities'] > 0:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        print(f"\nOverall Risk Level: {risk_level}")
        print("="*60)


async def example_file_scan():
    """单文件安全扫描示例"""
    print("=== Single File Security Scan Example ===")
    
    scanner = SecurityScanner()
    
    # 创建示例漏洞代码文件
    vulnerable_code = '''
import sqlite3
import os

def unsafe_login(username, password):
    # SQL注入漏洞
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    
    # 硬编码API密钥
    api_key = "sk-1234567890abcdef"
    secret_key = "secret_123456"
    
    return cursor.fetchone()

def unsafe_file_access(filename):
    # 路径遍历漏洞
    file_path = "/var/www/uploads/" + filename
    with open(file_path, 'r') as f:
        return f.read()

def unsafe_command(user_input):
    # 命令注入漏洞
    os.system(f"echo {user_input}")
    
    # 危险的eval使用
    result = eval(user_input)
    return result
'''
    
    # 保存示例代码
    example_file = Path("examples/vulnerable_code.py")
    example_file.parent.mkdir(exist_ok=True)
    
    with open(example_file, 'w') as f:
        f.write(vulnerable_code)
    
    try:
        result = await scanner.scan_file(str(example_file))
        
        print(f"\nSecurity scan results for {example_file}:")
        print(json.dumps(result, indent=2))
        
        # 清理示例文件
        example_file.unlink()
        
    except Exception as e:
        print(f"Error scanning file: {e}")


async def example_project_scan():
    """项目安全扫描示例"""
    print("=== Project Security Scan Example ===")
    
    scanner = SecurityScanner()
    
    project_path = "."  # 当前目录
    
    try:
        # 扫描项目
        results = await scanner.scan_project(
            project_path,
            file_patterns=["*.py"]
        )
        
        # 打印摘要
        scanner.print_security_summary(results)
        
        # 生成报告
        report = await scanner.generate_security_report(
            results,
            output_path="reports/security_report.md"
        )
        
        print(f"\nSecurity report preview:")
        print(report[:500] + "..." if len(report) > 500 else report)
        
        # 保存完整结果
        with open("reports/security_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print("\nFull results saved to reports/security_results.json")
        
    except Exception as e:
        print(f"Error scanning project: {e}")


async def example_dependency_scan():
    """依赖安全扫描示例"""
    print("=== Dependency Security Scan Example ===")
    
    scanner = SecurityScanner()
    
    project_path = "."
    
    try:
        result = await scanner.scan_dependencies(project_path)
        
        print("Dependency security scan results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error scanning dependencies: {e}")


async def example_custom_security_rules():
    """自定义安全规则示例"""
    print("=== Custom Security Rules Example ===")
    
    scanner = SecurityScanner()
    
    # 创建自定义安全扫描任务
    task = AgentTask(
        id="custom_security_scan",
        type=TaskType.SECURITY_SCAN,
        title="Custom Security Scan",
        description="Security scan with custom rules",
        parameters={
            "file_path": "examples/sample_code.py",
            "custom_security_rules": {
                "forbidden_functions": ["eval", "exec", "compile"],
                "required_input_validation": True,
                "check_crypto_usage": True,
                "detect_timing_attacks": True
            },
            "scan_types": ["custom_rules", "static_analysis"],
            "severity_threshold": "medium"
        }
    )
    
    try:
        result = await scanner.compliance_auditor.execute_task(task)
        
        if result.status.value == "completed":
            print("Custom security scan completed:")
            print(json.dumps(result.result, indent=2))
        else:
            print(f"Custom security scan failed: {result.error}")
            
    except Exception as e:
        print(f"Error in custom security scan: {e}")


async def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("AgentScope Security Scan Examples")
    print("=================================")
    
    # 运行示例
    await example_file_scan()
    print("\n")
    
    await example_project_scan()
    print("\n")
    
    await example_dependency_scan()
    print("\n")
    
    await example_custom_security_rules()


if __name__ == "__main__":
    asyncio.run(main())
