#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Augment集成中心 - 作为Augment与AgentScope之间的桥梁
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..core.agentscope_workflow_manager import AgentScopeWorkflowManager
from ..interfaces.agent_interface import AgentTask, TaskType


class AugmentEventType(Enum):
    """Augment事件类型"""
    CODE_ANALYSIS_REQUEST = "code_analysis_request"
    SECURITY_SCAN_REQUEST = "security_scan_request"
    QUALITY_CHECK_REQUEST = "quality_check_request"
    REFACTOR_SUGGESTION = "refactor_suggestion"
    DOCUMENTATION_REQUEST = "documentation_request"


@dataclass
class AugmentMessage:
    """Augment消息结构"""
    event_type: AugmentEventType
    content: str
    context: Dict[str, Any]
    source: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


class NaturalLanguageProcessor:
    """自然语言处理器 - 解析Augment指令"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 指令模式匹配
        self.patterns = {
            AugmentEventType.CODE_ANALYSIS_REQUEST: [
                r"分析.*代码",
                r"检查.*文件",
                r"analyze.*code",
                r"review.*file",
                r"代码.*分析",
                r"文件.*检查"
            ],
            AugmentEventType.SECURITY_SCAN_REQUEST: [
                r"安全.*扫描",
                r"漏洞.*检测",
                r"security.*scan",
                r"vulnerability.*check",
                r"安全.*检查",
                r"漏洞.*分析"
            ],
            AugmentEventType.QUALITY_CHECK_REQUEST: [
                r"质量.*检查",
                r"代码.*质量",
                r"quality.*check",
                r"code.*quality",
                r"质量.*分析",
                r"代码.*规范"
            ],
            AugmentEventType.REFACTOR_SUGGESTION: [
                r"重构.*建议",
                r"优化.*代码",
                r"refactor.*suggestion",
                r"optimize.*code",
                r"代码.*优化",
                r"重构.*方案"
            ],
            AugmentEventType.DOCUMENTATION_REQUEST: [
                r"生成.*文档",
                r"添加.*注释",
                r"generate.*documentation",
                r"add.*comments",
                r"文档.*生成",
                r"注释.*添加"
            ]
        }
        
        # 参数提取模式
        self.parameter_patterns = {
            "file_path": r"(?:文件|file)[:：]\s*([^\s]+)",
            "directory": r"(?:目录|directory)[:：]\s*([^\s]+)",
            "language": r"(?:语言|language)[:：]\s*([^\s]+)",
            "severity": r"(?:严重程度|severity)[:：]\s*([^\s]+)"
        }
    
    async def parse_command(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """解析自然语言指令"""
        try:
            # 1. 识别事件类型
            event_type = self._identify_event_type(content)
            
            # 2. 提取参数
            parameters = self._extract_parameters(content, context)
            
            # 3. 推断目标文件
            target_files = self._infer_target_files(content, context)
            
            # 4. 确定分析类型
            analysis_types = self._determine_analysis_types(content, event_type)
            
            # 5. 计算置信度
            confidence = self._calculate_confidence(content, event_type)
            
            return {
                "event_type": event_type,
                "parameters": parameters,
                "target_files": target_files,
                "analysis_types": analysis_types,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse command: {e}")
            return {
                "event_type": AugmentEventType.CODE_ANALYSIS_REQUEST,
                "parameters": {},
                "target_files": [],
                "analysis_types": ["general"],
                "confidence": 0.5
            }
    
    def _identify_event_type(self, content: str) -> AugmentEventType:
        """识别事件类型"""
        content_lower = content.lower()
        
        # 计算每种事件类型的匹配分数
        scores = {}
        for event_type, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    score += 1
            scores[event_type] = score
        
        # 返回得分最高的事件类型
        if scores:
            best_event = max(scores, key=scores.get)
            if scores[best_event] > 0:
                return best_event
        
        # 默认返回代码分析请求
        return AugmentEventType.CODE_ANALYSIS_REQUEST
    
    def _extract_parameters(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """提取参数"""
        parameters = {}
        
        # 从内容中提取明确指定的参数
        for param_name, pattern in self.parameter_patterns.items():
            match = re.search(pattern, content)
            if match:
                parameters[param_name] = match.group(1)
        
        # 从上下文中补充参数
        if "current_file" in context:
            parameters.setdefault("file_path", context["current_file"])
        
        if "workspace_root" in context:
            parameters.setdefault("workspace_root", context["workspace_root"])
        
        if "language" in context:
            parameters.setdefault("language", context["language"])
        
        return parameters
    
    def _infer_target_files(self, content: str, context: Dict[str, Any]) -> List[str]:
        """推断目标文件"""
        target_files = []
        
        # 从内容中提取文件路径
        file_patterns = [
            r"([a-zA-Z_][a-zA-Z0-9_]*\.py)",
            r"([a-zA-Z_][a-zA-Z0-9_]*\.js)",
            r"([a-zA-Z_][a-zA-Z0-9_]*\.ts)",
            r"([a-zA-Z_][a-zA-Z0-9_]*\.java)",
            r"([a-zA-Z_][a-zA-Z0-9_]*\.cpp)",
            r"([a-zA-Z_][a-zA-Z0-9_]*\.c)"
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            target_files.extend(matches)
        
        # 如果没有明确指定文件，使用当前文件
        if not target_files and "current_file" in context:
            target_files.append(context["current_file"])
        
        return list(set(target_files))  # 去重
    
    def _determine_analysis_types(self, content: str, event_type: AugmentEventType) -> List[str]:
        """确定分析类型"""
        analysis_types = []
        
        # 基于事件类型的默认分析类型
        if event_type == AugmentEventType.SECURITY_SCAN_REQUEST:
            analysis_types = ["security", "vulnerability"]
        elif event_type == AugmentEventType.QUALITY_CHECK_REQUEST:
            analysis_types = ["quality", "style", "complexity"]
        elif event_type == AugmentEventType.CODE_ANALYSIS_REQUEST:
            analysis_types = ["structure", "dependencies", "metrics"]
        elif event_type == AugmentEventType.REFACTOR_SUGGESTION:
            analysis_types = ["refactor", "optimization"]
        elif event_type == AugmentEventType.DOCUMENTATION_REQUEST:
            analysis_types = ["documentation", "comments"]
        else:
            analysis_types = ["general"]
        
        # 根据内容细化分析类型
        content_lower = content.lower()
        
        if "sql注入" in content_lower or "sql injection" in content_lower:
            analysis_types.append("sql_injection")
        
        if "xss" in content_lower:
            analysis_types.append("xss")
        
        if "复杂度" in content_lower or "complexity" in content_lower:
            analysis_types.append("complexity")
        
        if "性能" in content_lower or "performance" in content_lower:
            analysis_types.append("performance")
        
        if "测试" in content_lower or "test" in content_lower:
            analysis_types.append("testing")
        
        return list(set(analysis_types))  # 去重
    
    def _calculate_confidence(self, content: str, event_type: AugmentEventType) -> float:
        """计算解析置信度"""
        confidence = 0.5  # 基础置信度
        
        # 根据匹配的模式数量调整置信度
        matched_patterns = 0
        for pattern in self.patterns[event_type]:
            if re.search(pattern, content.lower()):
                matched_patterns += 1
        
        confidence += matched_patterns * 0.15
        
        # 根据参数完整性调整
        if self._extract_parameters(content, {}):
            confidence += 0.1
        
        # 根据内容长度调整（太短的指令置信度较低）
        if len(content.strip()) < 10:
            confidence -= 0.2
        elif len(content.strip()) > 50:
            confidence += 0.1
        
        return min(max(confidence, 0.0), 1.0)


class AugmentIntegrationHub:
    """Augment集成中心"""
    
    def __init__(self, workflow_manager: AgentScopeWorkflowManager):
        self.logger = logging.getLogger(__name__)
        self.workflow_manager = workflow_manager
        self.nlp_processor = NaturalLanguageProcessor()
        
        # 消息队列
        self.message_queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        
        # 上下文管理
        self.current_context = {}
        
        # 结果缓存
        self.result_cache = {}
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        self.logger.info("Augment Integration Hub initialized")
    
    async def start(self):
        """启动集成中心"""
        self.logger.info("Starting Augment Integration Hub")
        
        # 启动消息处理器
        self.processing_task = asyncio.create_task(self._process_messages())
    
    async def stop(self):
        """停止集成中心"""
        self.logger.info("Stopping Augment Integration Hub")
        
        # 停止消息处理器
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
    
    async def process_augment_message(self, message: AugmentMessage) -> Dict[str, Any]:
        """处理Augment消息"""
        await self.message_queue.put(message)
        
        # 返回处理确认
        return {
            "status": "queued",
            "message_id": f"msg_{int(message.timestamp)}",
            "estimated_processing_time": "2-5 seconds"
        }
    
    async def _process_messages(self):
        """处理消息队列"""
        while True:
            try:
                message = await self.message_queue.get()
                await self._process_single_message(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Message processing error: {e}")
    
    async def _process_single_message(self, message: AugmentMessage):
        """处理单个消息"""
        try:
            self.logger.info(f"Processing Augment message: {message.content[:100]}...")
            
            # 1. 解析自然语言指令
            parsed_command = await self.nlp_processor.parse_command(
                message.content, 
                message.context
            )
            
            # 2. 创建AgentScope任务
            task = await self._create_agentscope_task(parsed_command, message)
            
            # 3. 执行任务
            workflow_id = await self.workflow_manager.create_workflow(task)
            
            # 4. 监控任务执行
            result = await self._monitor_workflow_execution(workflow_id)
            
            # 5. 触发完成事件
            await self._trigger_event_callbacks("message_processed", {
                "message": message,
                "task": task,
                "workflow_id": workflow_id,
                "result": result
            })
            
        except Exception as e:
            self.logger.error(f"Failed to process message: {e}")
            
            # 触发错误事件
            await self._trigger_event_callbacks("message_failed", {
                "message": message,
                "error": str(e)
            })
    
    async def _create_agentscope_task(self, parsed_command: Dict[str, Any], message: AugmentMessage) -> AgentTask:
        """创建AgentScope任务"""
        task_type = self._map_event_type_to_task_type(parsed_command["event_type"])
        
        task = AgentTask(
            id=f"augment_{int(message.timestamp)}",
            type=task_type,
            title=f"Augment请求: {message.content[:50]}...",
            description=message.content,
            parameters={
                **parsed_command["parameters"],
                "target_files": parsed_command["target_files"],
                "analysis_types": parsed_command["analysis_types"],
                "source": message.source,
                "confidence": parsed_command["confidence"],
                "augment_context": message.context
            },
            priority=self._determine_priority(parsed_command),
            metadata={
                "augment_message": message,
                "parsed_command": parsed_command
            }
        )
        
        return task
    
    def _map_event_type_to_task_type(self, event_type: AugmentEventType) -> TaskType:
        """映射事件类型到任务类型"""
        mapping = {
            AugmentEventType.CODE_ANALYSIS_REQUEST: TaskType.CODE_ANALYSIS,
            AugmentEventType.SECURITY_SCAN_REQUEST: TaskType.SECURITY_SCAN,
            AugmentEventType.QUALITY_CHECK_REQUEST: TaskType.QUALITY_CHECK,
            AugmentEventType.REFACTOR_SUGGESTION: TaskType.CODE_ANALYSIS,
            AugmentEventType.DOCUMENTATION_REQUEST: TaskType.CODE_ANALYSIS
        }
        
        return mapping.get(event_type, TaskType.COMPREHENSIVE_ANALYSIS)
    
    def _determine_priority(self, parsed_command: Dict[str, Any]) -> int:
        """确定任务优先级"""
        event_type = parsed_command["event_type"]
        confidence = parsed_command["confidence"]
        
        # 基础优先级
        base_priority = 2
        
        # 根据事件类型调整
        if event_type == AugmentEventType.SECURITY_SCAN_REQUEST:
            base_priority = 1  # 安全扫描高优先级
        elif event_type == AugmentEventType.DOCUMENTATION_REQUEST:
            base_priority = 3  # 文档生成低优先级
        
        # 根据置信度调整
        if confidence > 0.8:
            base_priority = max(1, base_priority - 1)
        elif confidence < 0.6:
            base_priority = min(3, base_priority + 1)
        
        return base_priority
    
    async def _monitor_workflow_execution(self, workflow_id: str) -> Dict[str, Any]:
        """监控工作流执行"""
        # 等待工作流完成
        max_wait_time = 300  # 5分钟超时
        check_interval = 2   # 2秒检查一次
        
        for _ in range(max_wait_time // check_interval):
            status = await self.workflow_manager.get_workflow_status(workflow_id)
            
            if status and status.get("status") in ["completed", "failed", "cancelled"]:
                return status
            
            await asyncio.sleep(check_interval)
        
        # 超时
        self.logger.warning(f"Workflow {workflow_id} execution timeout")
        return {"status": "timeout", "workflow_id": workflow_id}
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    async def _trigger_event_callbacks(self, event_type: str, data: Dict[str, Any]):
        """触发事件回调"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"Event callback error: {e}")
    
    def update_context(self, context: Dict[str, Any]):
        """更新当前上下文"""
        self.current_context.update(context)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "queue_size": self.message_queue.qsize(),
            "cache_size": len(self.result_cache),
            "context_keys": list(self.current_context.keys()),
            "registered_callbacks": {
                event_type: len(callbacks) 
                for event_type, callbacks in self.event_callbacks.items()
            }
        }
