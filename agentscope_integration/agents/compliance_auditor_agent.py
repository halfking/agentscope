# -*- coding: utf-8 -*-
"""
基于AgentScope的规范审核员智能体
"""

import os
import re
import ast
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock
from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase

from .base_specialized_agent import OptimizedSpecializedAgent, register_specialized_tool
from ..interfaces.agent_interface import AgentRole, TaskType, AgentTask, TaskResult, TaskStatus


class ViolationSeverity(str, Enum):
    """违规严重程度"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class ComplianceAuditorAgent(OptimizedSpecializedAgent):
    """规范审核员智能体 - 基于AgentScope ReActAgent"""
    
    def __init__(
        self,
        model: ChatModelBase,
        formatter: FormatterBase,
        **kwargs
    ):
        # 定义支持的任务类型
        supported_tasks = [
            TaskType.QUALITY_CHECK,
            TaskType.SECURITY_SCAN,
            TaskType.TEST_ANALYSIS
        ]
        
        # 系统提示词
        sys_prompt = """你是一个严格的代码质量和安全专家，负责确保代码符合项目规范和安全要求。

你的核心职责包括：
1. 执行静态代码分析，检测代码质量问题
2. 进行安全漏洞扫描和风险评估
3. 分析测试质量，特别是检测虚假测试
4. 检查代码是否符合编码规范
5. 提供具体的修改建议和最佳实践指导

你拥有以下专业工具：
- static_code_analysis: 静态代码分析
- security_vulnerability_scan: 安全漏洞扫描
- test_quality_analysis: 测试质量分析
- coding_standards_check: 编码规范检查
- generate_quality_report: 生成质量报告

你特别关注：
- SQL注入、XSS等安全漏洞
- 硬编码密钥和敏感信息
- 使用H2数据库等虚假测试
- 代码复杂度和可维护性
- 异常处理和错误管理

请根据任务要求，使用合适的工具进行分析，并提供详细的问题报告和改进建议。"""
        
        super().__init__(
            agent_id="compliance_auditor",
            role=AgentRole.COMPLIANCE_AUDITOR,
            name="ComplianceAuditor",
            sys_prompt=sys_prompt,
            model=model,
            formatter=formatter,
            supported_tasks=supported_tasks,
            **kwargs
        )
        
        # 审计规则和配置
        self.rules = self._load_audit_rules()
        self.audit_history: List[Dict[str, Any]] = []
    
    def _register_specialized_tools(self):
        """注册规范审核专业工具"""
        
        @register_specialized_tool([TaskType.QUALITY_CHECK], "静态代码分析")
        async def static_code_analysis(file_path: str) -> ToolResponse:
            """执行静态代码分析"""
            try:
                violations = await self._analyze_code_quality(file_path)
                score = self._calculate_quality_score(violations)
                
                result = {
                    "file_path": file_path,
                    "quality_score": score,
                    "violations": violations,
                    "summary": self._generate_violation_summary(violations)
                }
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"静态代码分析结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"静态分析失败: {str(e)}")]
                )
        
        @register_specialized_tool([TaskType.SECURITY_SCAN], "安全漏洞扫描")
        async def security_vulnerability_scan(file_path: str) -> ToolResponse:
            """执行安全漏洞扫描"""
            try:
                vulnerabilities = await self._scan_security_vulnerabilities(file_path)
                risk_level = self._assess_security_risk(vulnerabilities)
                
                result = {
                    "file_path": file_path,
                    "risk_level": risk_level,
                    "vulnerabilities": vulnerabilities,
                    "recommendations": self._generate_security_recommendations(vulnerabilities)
                }
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"安全漏洞扫描结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"安全扫描失败: {str(e)}")]
                )
        
        @register_specialized_tool([TaskType.TEST_ANALYSIS], "测试质量分析")
        async def test_quality_analysis(file_path: str) -> ToolResponse:
            """分析测试质量"""
            try:
                test_issues = await self._analyze_test_quality(file_path)
                quality_score = self._calculate_test_quality_score(test_issues)
                
                result = {
                    "file_path": file_path,
                    "test_quality_score": quality_score,
                    "issues": test_issues,
                    "recommendations": self._generate_test_recommendations(test_issues)
                }
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"测试质量分析结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"测试分析失败: {str(e)}")]
                )
        
        @register_specialized_tool([TaskType.QUALITY_CHECK], "编码规范检查")
        async def coding_standards_check(file_path: str) -> ToolResponse:
            """检查编码规范"""
            try:
                violations = await self._check_coding_standards(file_path)
                compliance_score = self._calculate_compliance_score(violations)
                
                result = {
                    "file_path": file_path,
                    "compliance_score": compliance_score,
                    "violations": violations,
                    "standards_applied": list(self.rules.keys())
                }
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"编码规范检查结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"规范检查失败: {str(e)}")]
                )
        
        @register_specialized_tool([TaskType.QUALITY_CHECK], "生成质量报告")
        async def generate_quality_report(target_path: str) -> ToolResponse:
            """生成综合质量报告"""
            try:
                report = await self._generate_comprehensive_report(target_path)
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"综合质量报告:\n{json.dumps(report, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"报告生成失败: {str(e)}")]
                )
        
        # 注册工具到toolkit
        self.toolkit.register_tool_function(static_code_analysis)
        self.toolkit.register_tool_function(security_vulnerability_scan)
        self.toolkit.register_tool_function(test_quality_analysis)
        self.toolkit.register_tool_function(coding_standards_check)
        self.toolkit.register_tool_function(generate_quality_report)
    
    def _load_audit_rules(self) -> Dict[str, Any]:
        """加载审计规则"""
        return {
            "security": {
                "sql_injection": {
                    "patterns": [
                        r'"\s*\+\s*\w+\s*\+\s*"',  # 字符串拼接
                        r"'\s*\+\s*\w+\s*\+\s*'",  # 单引号拼接
                        r'f".*\{.*\}.*".*execute',  # f-string在SQL中
                    ],
                    "severity": ViolationSeverity.CRITICAL,
                    "message": "潜在的SQL注入漏洞",
                    "suggestion": "使用参数化查询或ORM方法"
                },
                "hardcoded_secrets": {
                    "patterns": [
                        r'password\s*=\s*["\'][^"\']+["\']',
                        r'api_key\s*=\s*["\'][^"\']+["\']',
                        r'secret\s*=\s*["\'][^"\']+["\']',
                        r'token\s*=\s*["\'][^"\']+["\']'
                    ],
                    "severity": ViolationSeverity.CRITICAL,
                    "message": "检测到硬编码密钥",
                    "suggestion": "使用环境变量或安全配置"
                }
            },
            "quality": {
                "code_complexity": {
                    "max_function_length": 50,
                    "max_cyclomatic_complexity": 10,
                    "severity": ViolationSeverity.MAJOR,
                    "message": "代码复杂度过高",
                    "suggestion": "拆分函数，降低复杂度"
                },
                "naming_conventions": {
                    "patterns": {
                        "class_name": r'^[A-Z][a-zA-Z0-9]*$',
                        "function_name": r'^[a-z_][a-z0-9_]*$',
                        "constant_name": r'^[A-Z_][A-Z0-9_]*$'
                    },
                    "severity": ViolationSeverity.MINOR,
                    "message": "命名规范违规",
                    "suggestion": "遵循PEP8命名规范"
                }
            },
            "testing": {
                "fake_database": {
                    "patterns": [
                        r'H2Database',
                        r'jdbc:h2:mem',
                        r'@DataJpaTest.*H2',
                        r'TestContainers.*H2'
                    ],
                    "severity": ViolationSeverity.MAJOR,
                    "message": "检测到虚假数据库测试",
                    "suggestion": "使用真实数据库进行集成测试"
                },
                "mock_overuse": {
                    "patterns": [
                        r'@Mock.*Repository',
                        r'Mockito\.when.*Repository',
                        r'mock\(.*Repository\.class\)'
                    ],
                    "severity": ViolationSeverity.MINOR,
                    "message": "过度使用Mock对象",
                    "suggestion": "考虑使用真实实现进行测试"
                }
            }
        }
    
    async def _analyze_code_quality(self, file_path: str) -> List[Dict[str, Any]]:
        """分析代码质量"""
        violations = []
        
        if not os.path.exists(file_path):
            return violations
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查安全问题
        for rule_name, rule in self.rules["security"].items():
            for pattern in rule["patterns"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    violations.append({
                        "rule": rule_name,
                        "severity": rule["severity"].value,
                        "line": line_num,
                        "message": rule["message"],
                        "suggestion": rule["suggestion"],
                        "code_snippet": self._get_code_snippet(content, line_num)
                    })
        
        # 检查代码复杂度（针对Python文件）
        if file_path.endswith('.py'):
            violations.extend(await self._check_python_complexity(file_path, content))
        
        return violations
    
    async def _scan_security_vulnerabilities(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描安全漏洞"""
        vulnerabilities = []
        
        if not os.path.exists(file_path):
            return vulnerabilities
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 只检查安全相关规则
        for rule_name, rule in self.rules["security"].items():
            for pattern in rule["patterns"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    vulnerabilities.append({
                        "type": rule_name,
                        "severity": rule["severity"].value,
                        "line": line_num,
                        "description": rule["message"],
                        "recommendation": rule["suggestion"],
                        "code_snippet": self._get_code_snippet(content, line_num),
                        "cwe_id": self._get_cwe_id(rule_name)
                    })
        
        return vulnerabilities
    
    async def _analyze_test_quality(self, file_path: str) -> List[Dict[str, Any]]:
        """分析测试质量"""
        issues = []
        
        if not os.path.exists(file_path):
            return issues
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查测试相关问题
        for rule_name, rule in self.rules["testing"].items():
            for pattern in rule["patterns"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        "issue_type": rule_name,
                        "severity": rule["severity"].value,
                        "line": line_num,
                        "description": rule["message"],
                        "recommendation": rule["suggestion"],
                        "code_snippet": self._get_code_snippet(content, line_num)
                    })
        
        return issues
    
    async def _check_coding_standards(self, file_path: str) -> List[Dict[str, Any]]:
        """检查编码规范"""
        violations = []
        
        if not os.path.exists(file_path):
            return violations
        
        # 检查质量相关规则
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for rule_name, rule in self.rules["quality"].items():
            if rule_name == "naming_conventions" and file_path.endswith('.py'):
                violations.extend(await self._check_python_naming(file_path, content))
        
        return violations
    
    async def _check_python_complexity(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检查Python代码复杂度"""
        violations = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 检查函数长度
                    func_lines = node.end_lineno - node.lineno + 1
                    if func_lines > self.rules["quality"]["code_complexity"]["max_function_length"]:
                        violations.append({
                            "rule": "function_too_long",
                            "severity": ViolationSeverity.MAJOR.value,
                            "line": node.lineno,
                            "message": f"函数过长 ({func_lines} 行)",
                            "suggestion": "将函数拆分为更小的函数",
                            "code_snippet": f"def {node.name}(...):"
                        })
        
        except SyntaxError:
            pass
        
        return violations
    
    async def _check_python_naming(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检查Python命名规范"""
        violations = []
        
        try:
            tree = ast.parse(content)
            patterns = self.rules["quality"]["naming_conventions"]["patterns"]
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not re.match(patterns["class_name"], node.name):
                        violations.append({
                            "rule": "class_naming",
                            "severity": ViolationSeverity.MINOR.value,
                            "line": node.lineno,
                            "message": f"类名不符合规范: {node.name}",
                            "suggestion": "使用PascalCase命名类",
                            "code_snippet": f"class {node.name}:"
                        })
                
                elif isinstance(node, ast.FunctionDef):
                    if not re.match(patterns["function_name"], node.name):
                        violations.append({
                            "rule": "function_naming",
                            "severity": ViolationSeverity.MINOR.value,
                            "line": node.lineno,
                            "message": f"函数名不符合规范: {node.name}",
                            "suggestion": "使用snake_case命名函数",
                            "code_snippet": f"def {node.name}(...):"
                        })
        
        except SyntaxError:
            pass
        
        return violations
    
    def _get_code_snippet(self, content: str, line_num: int, context: int = 2) -> str:
        """获取代码片段"""
        lines = content.splitlines()
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            snippet_lines.append(f"{prefix}{lines[i]}")
        
        return "\n".join(snippet_lines)
    
    def _get_cwe_id(self, rule_name: str) -> Optional[str]:
        """获取CWE ID"""
        cwe_mapping = {
            "sql_injection": "CWE-89",
            "hardcoded_secrets": "CWE-798"
        }
        return cwe_mapping.get(rule_name)
    
    def _calculate_quality_score(self, violations: List[Dict[str, Any]]) -> float:
        """计算质量评分"""
        if not violations:
            return 100.0
        
        penalty = 0
        for violation in violations:
            severity = violation.get("severity", "info")
            if severity == "critical":
                penalty += 20
            elif severity == "major":
                penalty += 10
            elif severity == "minor":
                penalty += 5
            else:
                penalty += 1
        
        return max(0.0, 100.0 - penalty)
    
    def _assess_security_risk(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """评估安全风险级别"""
        if not vulnerabilities:
            return "low"
        
        critical_count = sum(1 for v in vulnerabilities if v.get("severity") == "critical")
        major_count = sum(1 for v in vulnerabilities if v.get("severity") == "major")
        
        if critical_count > 0:
            return "critical"
        elif major_count > 2:
            return "high"
        elif major_count > 0:
            return "medium"
        else:
            return "low"
    
    def _calculate_test_quality_score(self, issues: List[Dict[str, Any]]) -> float:
        """计算测试质量评分"""
        if not issues:
            return 100.0
        
        penalty = 0
        for issue in issues:
            severity = issue.get("severity", "info")
            if severity == "major":
                penalty += 15
            elif severity == "minor":
                penalty += 5
            else:
                penalty += 2
        
        return max(0.0, 100.0 - penalty)
    
    def _calculate_compliance_score(self, violations: List[Dict[str, Any]]) -> float:
        """计算合规评分"""
        return self._calculate_quality_score(violations)
    
    def _generate_violation_summary(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成违规摘要"""
        summary = {
            "total_violations": len(violations),
            "by_severity": {},
            "by_rule": {}
        }
        
        for violation in violations:
            severity = violation.get("severity", "info")
            rule = violation.get("rule", "unknown")
            
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            summary["by_rule"][rule] = summary["by_rule"].get(rule, 0) + 1
        
        return summary
    
    def _generate_security_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        if any(v.get("type") == "sql_injection" for v in vulnerabilities):
            recommendations.append("使用参数化查询防止SQL注入")
        
        if any(v.get("type") == "hardcoded_secrets" for v in vulnerabilities):
            recommendations.append("将敏感信息移至环境变量或安全配置文件")
        
        if not recommendations:
            recommendations.append("继续保持良好的安全实践")
        
        return recommendations
    
    def _generate_test_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """生成测试建议"""
        recommendations = []
        
        if any(i.get("issue_type") == "fake_database" for i in issues):
            recommendations.append("使用真实数据库进行集成测试，避免虚假测试")
        
        if any(i.get("issue_type") == "mock_overuse" for i in issues):
            recommendations.append("减少Mock对象的使用，增加真实场景测试")
        
        if not recommendations:
            recommendations.append("测试质量良好，继续保持")
        
        return recommendations
    
    async def _generate_comprehensive_report(self, target_path: str) -> Dict[str, Any]:
        """生成综合质量报告"""
        report = {
            "target": target_path,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files_analyzed": 0,
                "overall_quality_score": 0.0,
                "security_risk_level": "low",
                "test_quality_score": 0.0
            },
            "details": {
                "quality_issues": [],
                "security_vulnerabilities": [],
                "test_issues": []
            },
            "recommendations": []
        }
        
        files_to_analyze = []
        
        if os.path.isfile(target_path):
            files_to_analyze = [target_path]
        elif os.path.isdir(target_path):
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    if file.endswith(('.py', '.java', '.js', '.ts')):
                        files_to_analyze.append(os.path.join(root, file))
        
        total_quality_score = 0
        total_test_score = 0
        all_vulnerabilities = []
        
        for file_path in files_to_analyze:
            # 质量分析
            quality_violations = await self._analyze_code_quality(file_path)
            quality_score = self._calculate_quality_score(quality_violations)
            total_quality_score += quality_score
            
            # 安全扫描
            vulnerabilities = await self._scan_security_vulnerabilities(file_path)
            all_vulnerabilities.extend(vulnerabilities)
            
            # 测试分析（如果是测试文件）
            if 'test' in file_path.lower():
                test_issues = await self._analyze_test_quality(file_path)
                test_score = self._calculate_test_quality_score(test_issues)
                total_test_score += test_score
                report["details"]["test_issues"].extend(test_issues)
            
            report["details"]["quality_issues"].extend(quality_violations)
        
        # 计算总体评分
        report["summary"]["total_files_analyzed"] = len(files_to_analyze)
        if files_to_analyze:
            report["summary"]["overall_quality_score"] = total_quality_score / len(files_to_analyze)
        
        report["summary"]["security_risk_level"] = self._assess_security_risk(all_vulnerabilities)
        report["details"]["security_vulnerabilities"] = all_vulnerabilities
        
        # 生成建议
        report["recommendations"] = self._generate_comprehensive_recommendations(report)
        
        return report
    
    def _generate_comprehensive_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        quality_score = report["summary"]["overall_quality_score"]
        security_risk = report["summary"]["security_risk_level"]
        
        if quality_score < 70:
            recommendations.append("代码质量需要改进，建议重构复杂函数并遵循编码规范")
        
        if security_risk in ["critical", "high"]:
            recommendations.append("存在严重安全风险，需要立即修复安全漏洞")
        
        if len(report["details"]["test_issues"]) > 0:
            recommendations.append("测试质量有待提升，建议使用真实数据库和减少Mock使用")
        
        if not recommendations:
            recommendations.append("代码质量良好，继续保持现有标准")
        
        return recommendations
