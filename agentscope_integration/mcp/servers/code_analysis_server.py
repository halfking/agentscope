#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义代码分析MCP服务器
提供专业的代码分析工具，集成到AgentScope的MCP生态系统中
"""

import asyncio
import json
import sys
import os
import ast
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

# MCP相关导入（假设使用标准MCP库）
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult
except ImportError:
    # 如果没有标准MCP库，使用简化实现
    print("Warning: MCP library not found, using simplified implementation")


class CodeAnalysisServer:
    """代码分析MCP服务器"""
    
    def __init__(self):
        self.server = Server("code-analysis-server")
        self.setup_tools()
    
    def setup_tools(self):
        """设置可用工具"""
        
        @self.server.tool("parse_python_ast")
        async def parse_python_ast(file_path: str) -> Dict[str, Any]:
            """解析Python文件的AST结构"""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                result = {
                    "file_path": file_path,
                    "classes": [],
                    "functions": [],
                    "imports": [],
                    "constants": [],
                    "complexity_metrics": {}
                }
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_info = {
                            "name": node.name,
                            "line": node.lineno,
                            "end_line": getattr(node, 'end_lineno', None),
                            "methods": [],
                            "docstring": ast.get_docstring(node),
                            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                            "bases": [self._get_base_name(base) for base in node.bases]
                        }
                        
                        # 获取类方法
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                method_info = {
                                    "name": item.name,
                                    "line": item.lineno,
                                    "args": [arg.arg for arg in item.args.args],
                                    "decorators": [self._get_decorator_name(d) for d in item.decorator_list],
                                    "is_property": any("property" in self._get_decorator_name(d) for d in item.decorator_list),
                                    "is_static": any("staticmethod" in self._get_decorator_name(d) for d in item.decorator_list),
                                    "is_class": any("classmethod" in self._get_decorator_name(d) for d in item.decorator_list)
                                }
                                class_info["methods"].append(method_info)
                        
                        result["classes"].append(class_info)
                    
                    elif isinstance(node, ast.FunctionDef) and not self._is_in_class(node, tree):
                        func_info = {
                            "name": node.name,
                            "line": node.lineno,
                            "end_line": getattr(node, 'end_lineno', None),
                            "args": [arg.arg for arg in node.args.args],
                            "returns": self._get_return_annotation(node),
                            "docstring": ast.get_docstring(node),
                            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                            "is_async": isinstance(node, ast.AsyncFunctionDef)
                        }
                        result["functions"].append(func_info)
                    
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                result["imports"].append({
                                    "type": "import",
                                    "module": alias.name,
                                    "alias": alias.asname,
                                    "line": node.lineno
                                })
                        else:
                            for alias in node.names:
                                result["imports"].append({
                                    "type": "from_import",
                                    "module": node.module,
                                    "name": alias.name,
                                    "alias": alias.asname,
                                    "line": node.lineno
                                })
                    
                    elif isinstance(node, ast.Assign):
                        # 检测常量定义
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id.isupper():
                                result["constants"].append({
                                    "name": target.id,
                                    "line": node.lineno,
                                    "value": self._get_constant_value(node.value)
                                })
                
                # 计算复杂度指标
                result["complexity_metrics"] = self._calculate_complexity_metrics(tree)
                
                return result
                
            except Exception as e:
                return {"error": f"Failed to parse Python file: {str(e)}"}
        
        @self.server.tool("analyze_code_quality")
        async def analyze_code_quality(file_path: str) -> Dict[str, Any]:
            """分析代码质量"""
            try:
                result = {
                    "file_path": file_path,
                    "quality_score": 0.0,
                    "issues": [],
                    "metrics": {},
                    "suggestions": []
                }
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                
                # 基本指标
                result["metrics"] = {
                    "lines_of_code": len(lines),
                    "blank_lines": sum(1 for line in lines if not line.strip()),
                    "comment_lines": sum(1 for line in lines if line.strip().startswith('#')),
                    "avg_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0
                }
                
                # 质量检查
                issues = []
                
                # 检查长行
                for i, line in enumerate(lines, 1):
                    if len(line) > 120:
                        issues.append({
                            "type": "long_line",
                            "line": i,
                            "severity": "minor",
                            "message": f"Line too long ({len(line)} characters)",
                            "suggestion": "Consider breaking long lines"
                        })
                
                # 检查TODO/FIXME
                for i, line in enumerate(lines, 1):
                    if 'TODO' in line or 'FIXME' in line:
                        issues.append({
                            "type": "todo_fixme",
                            "line": i,
                            "severity": "info",
                            "message": "TODO/FIXME comment found",
                            "suggestion": "Address pending tasks"
                        })
                
                # 如果是Python文件，进行AST分析
                if file_path.endswith('.py'):
                    try:
                        tree = ast.parse(content)
                        
                        # 检查函数复杂度
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                complexity = self._calculate_cyclomatic_complexity(node)
                                if complexity > 10:
                                    issues.append({
                                        "type": "high_complexity",
                                        "line": node.lineno,
                                        "severity": "major",
                                        "message": f"Function '{node.name}' has high complexity ({complexity})",
                                        "suggestion": "Consider refactoring to reduce complexity"
                                    })
                    
                    except SyntaxError as e:
                        issues.append({
                            "type": "syntax_error",
                            "line": e.lineno or 0,
                            "severity": "critical",
                            "message": f"Syntax error: {e.msg}",
                            "suggestion": "Fix syntax errors"
                        })
                
                result["issues"] = issues
                
                # 计算质量评分
                penalty = 0
                for issue in issues:
                    if issue["severity"] == "critical":
                        penalty += 20
                    elif issue["severity"] == "major":
                        penalty += 10
                    elif issue["severity"] == "minor":
                        penalty += 5
                    else:
                        penalty += 1
                
                result["quality_score"] = max(0.0, 100.0 - penalty)
                
                # 生成建议
                if result["quality_score"] < 70:
                    result["suggestions"].append("Code quality needs improvement")
                if any(issue["type"] == "high_complexity" for issue in issues):
                    result["suggestions"].append("Reduce function complexity")
                if any(issue["type"] == "long_line" for issue in issues):
                    result["suggestions"].append("Follow line length guidelines")
                
                return result
                
            except Exception as e:
                return {"error": f"Failed to analyze code quality: {str(e)}"}
        
        @self.server.tool("detect_security_issues")
        async def detect_security_issues(file_path: str) -> Dict[str, Any]:
            """检测安全问题"""
            try:
                result = {
                    "file_path": file_path,
                    "security_score": 100.0,
                    "vulnerabilities": [],
                    "risk_level": "low"
                }
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                vulnerabilities = []
                
                # 检查硬编码密钥
                import re
                patterns = {
                    "hardcoded_password": r'password\s*=\s*["\'][^"\']+["\']',
                    "hardcoded_api_key": r'api_key\s*=\s*["\'][^"\']+["\']',
                    "hardcoded_secret": r'secret\s*=\s*["\'][^"\']+["\']',
                    "sql_injection": r'["\'].*\+.*["\'].*execute|execute.*["\'].*\+.*["\']',
                    "eval_usage": r'\beval\s*\(',
                    "exec_usage": r'\bexec\s*\('
                }
                
                lines = content.splitlines()
                for pattern_name, pattern in patterns.items():
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            severity = "critical" if pattern_name in ["sql_injection", "eval_usage", "exec_usage"] else "major"
                            vulnerabilities.append({
                                "type": pattern_name,
                                "line": i,
                                "severity": severity,
                                "description": f"Potential {pattern_name.replace('_', ' ')} detected",
                                "code_snippet": line.strip(),
                                "recommendation": self._get_security_recommendation(pattern_name)
                            })
                
                result["vulnerabilities"] = vulnerabilities
                
                # 计算安全评分
                penalty = 0
                for vuln in vulnerabilities:
                    if vuln["severity"] == "critical":
                        penalty += 30
                    elif vuln["severity"] == "major":
                        penalty += 15
                    else:
                        penalty += 5
                
                result["security_score"] = max(0.0, 100.0 - penalty)
                
                # 评估风险级别
                if result["security_score"] < 50:
                    result["risk_level"] = "critical"
                elif result["security_score"] < 70:
                    result["risk_level"] = "high"
                elif result["security_score"] < 85:
                    result["risk_level"] = "medium"
                else:
                    result["risk_level"] = "low"
                
                return result
                
            except Exception as e:
                return {"error": f"Failed to detect security issues: {str(e)}"}
        
        @self.server.tool("analyze_dependencies")
        async def analyze_dependencies(project_path: str) -> Dict[str, Any]:
            """分析项目依赖关系"""
            try:
                result = {
                    "project_path": project_path,
                    "dependencies": [],
                    "dependency_graph": {},
                    "circular_dependencies": [],
                    "unused_imports": []
                }
                
                # 扫描Python文件
                python_files = []
                for root, dirs, files in os.walk(project_path):
                    # 跳过常见的忽略目录
                    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules']]
                    
                    for file in files:
                        if file.endswith('.py'):
                            python_files.append(os.path.join(root, file))
                
                # 分析每个文件的导入
                file_imports = {}
                for file_path in python_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        tree = ast.parse(content)
                        imports = []
                        
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.append(alias.name)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.append(node.module)
                        
                        file_imports[file_path] = imports
                        
                    except Exception as e:
                        print(f"Error analyzing {file_path}: {e}")
                
                # 构建依赖图
                for file_path, imports in file_imports.items():
                    result["dependency_graph"][file_path] = imports
                
                # 检测循环依赖（简化版）
                # 这里可以实现更复杂的循环依赖检测算法
                
                return result
                
            except Exception as e:
                return {"error": f"Failed to analyze dependencies: {str(e)}"}
    
    def _get_decorator_name(self, decorator) -> str:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.attr}"
        else:
            return str(decorator)
    
    def _get_base_name(self, base) -> str:
        """获取基类名称"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.attr}"
        else:
            return str(base)
    
    def _get_return_annotation(self, node) -> Optional[str]:
        """获取返回类型注解"""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            else:
                return str(node.returns)
        return None
    
    def _is_in_class(self, func_node, tree) -> bool:
        """检查函数是否在类中"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item == func_node:
                        return True
        return False
    
    def _get_constant_value(self, node) -> Any:
        """获取常量值"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        else:
            return None
    
    def _calculate_complexity_metrics(self, tree) -> Dict[str, Any]:
        """计算复杂度指标"""
        metrics = {
            "total_functions": 0,
            "total_classes": 0,
            "max_function_complexity": 0,
            "avg_function_complexity": 0.0
        }
        
        function_complexities = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics["total_functions"] += 1
                complexity = self._calculate_cyclomatic_complexity(node)
                function_complexities.append(complexity)
                metrics["max_function_complexity"] = max(metrics["max_function_complexity"], complexity)
            elif isinstance(node, ast.ClassDef):
                metrics["total_classes"] += 1
        
        if function_complexities:
            metrics["avg_function_complexity"] = sum(function_complexities) / len(function_complexities)
        
        return metrics
    
    def _calculate_cyclomatic_complexity(self, node) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _get_security_recommendation(self, vulnerability_type: str) -> str:
        """获取安全建议"""
        recommendations = {
            "hardcoded_password": "Use environment variables or secure configuration files",
            "hardcoded_api_key": "Store API keys in environment variables",
            "hardcoded_secret": "Use secure secret management systems",
            "sql_injection": "Use parameterized queries or ORM methods",
            "eval_usage": "Avoid using eval(), consider safer alternatives",
            "exec_usage": "Avoid using exec(), consider safer alternatives"
        }
        return recommendations.get(vulnerability_type, "Review and fix security issue")
    
    async def run(self):
        """运行MCP服务器"""
        await self.server.run()


async def main():
    """主函数"""
    server = CodeAnalysisServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
