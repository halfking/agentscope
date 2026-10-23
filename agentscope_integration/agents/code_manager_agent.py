# -*- coding: utf-8 -*-
"""
基于AgentScope的代码管理员智能体
"""

import os
import ast
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock, ToolUseBlock
from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase

from .base_specialized_agent import OptimizedSpecializedAgent, register_specialized_tool
from ..interfaces.agent_interface import AgentRole, TaskType, AgentTask, TaskResult, TaskStatus


class CodeManagerAgent(OptimizedSpecializedAgent):
    """代码管理员智能体 - 基于AgentScope ReActAgent"""
    
    def __init__(
        self,
        model: ChatModelBase,
        formatter: FormatterBase,
        **kwargs
    ):
        # 定义支持的任务类型
        supported_tasks = [
            TaskType.CODE_ANALYSIS,
            TaskType.DEPENDENCY_ANALYSIS,
            TaskType.ARCHITECTURE_REVIEW
        ]
        
        # 系统提示词
        sys_prompt = """你是一个专业的代码管理员智能体，负责维护完整的代码库知识图谱。

你的核心职责包括：
1. 分析代码结构和依赖关系
2. 维护代码知识图谱
3. 跟踪代码变更和影响范围
4. 提供代码查询和搜索服务
5. 评估架构设计和模块划分

你拥有以下专业工具：
- parse_code_file: 解析代码文件结构
- analyze_dependencies: 分析模块依赖关系
- build_knowledge_graph: 构建代码知识图谱
- search_code_elements: 搜索代码元素
- analyze_impact: 分析变更影响范围

请根据任务要求，使用合适的工具进行分析，并提供详细、准确的结果。"""
        
        super().__init__(
            name="CodeManager",
            role=AgentRole.CODE_MANAGER,
            supported_tasks=supported_tasks,
            model=model,
            formatter=formatter,
            sys_prompt=sys_prompt,
            **kwargs
        )
        
        # 代码库状态
        self.knowledge_graph: Dict[str, Any] = {}
        self.file_checksums: Dict[str, str] = {}
        self.project_path: Optional[str] = None
    
    async def _register_specialized_tools(self):
        """注册代码管理专业工具"""

        from agentscope.tracing import trace_toolkit

        @trace_toolkit
        async def parse_code_file(file_path: str) -> ToolResponse:
            """解析代码文件结构"""
            try:
                if not os.path.exists(file_path):
                    return ToolResponse(
                        content=[TextBlock(type="text", text=f"文件不存在: {file_path}")]
                    )
                
                file_ext = Path(file_path).suffix.lower()
                
                if file_ext == '.py':
                    result = await self._parse_python_file(file_path)
                elif file_ext in ['.js', '.ts']:
                    result = await self._parse_javascript_file(file_path)
                elif file_ext == '.java':
                    result = await self._parse_java_file(file_path)
                else:
                    return ToolResponse(
                        content=[TextBlock(type="text", text=f"不支持的文件类型: {file_ext}")]
                    )
                
                # 存储到长期记忆
                await self.long_term_memory.store(
                    "code_structures",
                    f"structure:{file_path}",
                    result
                )

                # 更新本地知识图谱
                self.knowledge_graph[file_path] = result

                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"代码文件解析结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"解析失败: {str(e)}")]
                )

        # 注册工具到toolkit
        self.toolkit.register_tool_function(parse_code_file)
        
        @register_specialized_tool([TaskType.DEPENDENCY_ANALYSIS], "分析模块依赖关系")
        async def analyze_dependencies(target_path: str) -> ToolResponse:
            """分析模块依赖关系"""
            try:
                dependencies = await self._analyze_dependencies(target_path)
                
                result = {
                    "target": target_path,
                    "dependencies": dependencies,
                    "dependency_count": len(dependencies),
                    "analysis_time": "now"
                }
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"依赖关系分析结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"依赖分析失败: {str(e)}")]
                )
        
        @register_specialized_tool([TaskType.CODE_ANALYSIS], "构建代码知识图谱")
        async def build_knowledge_graph(project_path: str) -> ToolResponse:
            """构建代码知识图谱"""
            try:
                self.project_path = project_path
                graph = await self._build_knowledge_graph(project_path)
                self.knowledge_graph = graph
                
                stats = {
                    "total_files": len(graph.get("files", {})),
                    "total_classes": len(graph.get("classes", {})),
                    "total_functions": len(graph.get("functions", {})),
                    "total_dependencies": len(graph.get("dependencies", []))
                }
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"知识图谱构建完成:\n{json.dumps(stats, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"知识图谱构建失败: {str(e)}")]
                )
        
        @register_specialized_tool([TaskType.CODE_ANALYSIS], "搜索代码元素")
        async def search_code_elements(query: str, element_type: str = "all") -> ToolResponse:
            """搜索代码元素"""
            try:
                results = await self._search_code_elements(query, element_type)
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"搜索结果 (查询: {query}):\n{json.dumps(results, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"搜索失败: {str(e)}")]
                )
        
        @register_specialized_tool([TaskType.ARCHITECTURE_REVIEW], "分析变更影响范围")
        async def analyze_impact(file_path: str) -> ToolResponse:
            """分析变更影响范围"""
            try:
                impact = await self._analyze_impact(file_path)
                
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"影响范围分析结果:\n{json.dumps(impact, ensure_ascii=False, indent=2)}"
                    )]
                )
                
            except Exception as e:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"影响分析失败: {str(e)}")]
                )
        
        # 注册工具到toolkit
        self.toolkit.register_tool_function(parse_code_file)
        self.toolkit.register_tool_function(analyze_dependencies)
        self.toolkit.register_tool_function(build_knowledge_graph)
        self.toolkit.register_tool_function(search_code_elements)
        self.toolkit.register_tool_function(analyze_impact)
    
    async def _parse_python_file(self, file_path: str) -> Dict[str, Any]:
        """解析Python文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "docstring": ast.get_docstring(node)
                    })
                elif isinstance(node, ast.FunctionDef):
                    if not any(node.lineno >= cls["line"] for cls in classes):  # 不在类中的函数
                        functions.append({
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args],
                            "docstring": ast.get_docstring(node)
                        })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module or "")
            
            return {
                "file_path": file_path,
                "language": "python",
                "classes": classes,
                "functions": functions,
                "imports": list(set(imports)),
                "lines_of_code": len(content.splitlines())
            }
            
        except SyntaxError as e:
            return {
                "file_path": file_path,
                "language": "python",
                "error": f"语法错误: {str(e)}",
                "classes": [],
                "functions": [],
                "imports": []
            }
    
    async def _parse_javascript_file(self, file_path: str) -> Dict[str, Any]:
        """解析JavaScript/TypeScript文件（简化版）"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简化的正则表达式解析
        import re
        
        # 查找函数定义
        function_pattern = r'(?:function\s+(\w+)|(\w+)\s*[:=]\s*(?:function|\([^)]*\)\s*=>))'
        functions = re.findall(function_pattern, content)
        
        # 查找类定义
        class_pattern = r'class\s+(\w+)'
        classes = re.findall(class_pattern, content)
        
        # 查找导入
        import_pattern = r'(?:import.*from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\))'
        imports = re.findall(import_pattern, content)
        
        return {
            "file_path": file_path,
            "language": "javascript",
            "functions": [f[0] or f[1] for f in functions],
            "classes": classes,
            "imports": [imp[0] or imp[1] for imp in imports],
            "lines_of_code": len(content.splitlines())
        }
    
    async def _parse_java_file(self, file_path: str) -> Dict[str, Any]:
        """解析Java文件（简化版）"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        
        # 查找类定义
        class_pattern = r'(?:public\s+)?class\s+(\w+)'
        classes = re.findall(class_pattern, content)
        
        # 查找方法定义
        method_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)'
        methods = re.findall(method_pattern, content)
        
        # 查找导入
        import_pattern = r'import\s+([^;]+);'
        imports = re.findall(import_pattern, content)
        
        return {
            "file_path": file_path,
            "language": "java",
            "classes": classes,
            "methods": methods,
            "imports": imports,
            "lines_of_code": len(content.splitlines())
        }
    
    async def _analyze_dependencies(self, target_path: str) -> List[Dict[str, Any]]:
        """分析依赖关系"""
        dependencies = []
        
        if os.path.isfile(target_path):
            file_info = await self._parse_python_file(target_path)
            for imp in file_info.get("imports", []):
                dependencies.append({
                    "type": "import",
                    "source": target_path,
                    "target": imp,
                    "relationship": "depends_on"
                })
        
        return dependencies
    
    async def _build_knowledge_graph(self, project_path: str) -> Dict[str, Any]:
        """构建知识图谱"""
        graph = {
            "files": {},
            "classes": {},
            "functions": {},
            "dependencies": []
        }
        
        # 遍历项目文件
        for root, dirs, files in os.walk(project_path):
            # 跳过隐藏目录和常见的忽略目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java')):
                    file_path = os.path.join(root, file)
                    try:
                        file_info = await self._parse_python_file(file_path)
                        graph["files"][file_path] = file_info
                        
                        # 添加类和函数到图谱
                        for cls in file_info.get("classes", []):
                            graph["classes"][f"{file_path}:{cls['name']}"] = cls
                        
                        for func in file_info.get("functions", []):
                            graph["functions"][f"{file_path}:{func['name']}"] = func
                        
                        # 添加依赖关系
                        deps = await self._analyze_dependencies(file_path)
                        graph["dependencies"].extend(deps)
                        
                    except Exception as e:
                        print(f"解析文件失败 {file_path}: {e}")
        
        return graph
    
    async def _search_code_elements(self, query: str, element_type: str = "all") -> List[Dict[str, Any]]:
        """搜索代码元素"""
        results = []
        
        if not self.knowledge_graph:
            return results
        
        query_lower = query.lower()
        
        # 搜索类
        if element_type in ["all", "class"]:
            for key, cls in self.knowledge_graph.get("classes", {}).items():
                if query_lower in cls["name"].lower():
                    results.append({
                        "type": "class",
                        "name": cls["name"],
                        "location": key,
                        "line": cls.get("line"),
                        "match_score": 1.0 if query_lower == cls["name"].lower() else 0.8
                    })
        
        # 搜索函数
        if element_type in ["all", "function"]:
            for key, func in self.knowledge_graph.get("functions", {}).items():
                if query_lower in func["name"].lower():
                    results.append({
                        "type": "function",
                        "name": func["name"],
                        "location": key,
                        "line": func.get("line"),
                        "match_score": 1.0 if query_lower == func["name"].lower() else 0.8
                    })
        
        # 按匹配度排序
        results.sort(key=lambda x: x["match_score"], reverse=True)
        
        return results[:20]  # 返回前20个结果
    
    async def _analyze_impact(self, file_path: str) -> Dict[str, Any]:
        """分析变更影响范围"""
        impact = {
            "direct_dependents": [],
            "indirect_dependents": [],
            "affected_modules": [],
            "risk_level": "low"
        }
        
        if not self.knowledge_graph:
            return impact
        
        # 查找直接依赖此文件的模块
        for dep in self.knowledge_graph.get("dependencies", []):
            if dep.get("target") == file_path or file_path in dep.get("target", ""):
                impact["direct_dependents"].append(dep["source"])
        
        # 计算风险级别
        direct_count = len(impact["direct_dependents"])
        if direct_count > 10:
            impact["risk_level"] = "high"
        elif direct_count > 5:
            impact["risk_level"] = "medium"
        
        impact["affected_modules"] = list(set(impact["direct_dependents"]))
        
        return impact
