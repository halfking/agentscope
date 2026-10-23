# -*- coding: utf-8 -*-
"""
代码审核标准管理器 - 管理通用和项目特定的代码审核标准
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import copy

from ..interfaces.agent_interface import TaskType


class StandardsManager:
    """代码审核标准管理器"""
    
    def __init__(self, standards_dir: str = "standards"):
        self.logger = logging.getLogger(__name__)
        self.standards_dir = Path(standards_dir)
        
        # 标准规范存储
        self.universal_standards = {}
        self.project_standards = {}
        self.active_standards = {}
        
        # 版本控制
        self.standards_history = []
        
        # 加载标准规范
        self._load_universal_standards()
        self._load_project_standards()
        
        self.logger.info("Standards manager initialized")
    
    def _load_universal_standards(self):
        """加载通用标准规范"""
        universal_file = self.standards_dir / "universal_code_review_standards.json"
        
        if universal_file.exists():
            try:
                with open(universal_file, 'r', encoding='utf-8') as f:
                    self.universal_standards = json.load(f)
                
                self.logger.info("Universal standards loaded successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to load universal standards: {e}")
                self.universal_standards = {}
        else:
            self.logger.warning(f"Universal standards file not found: {universal_file}")
    
    def _load_project_standards(self):
        """加载项目特定标准规范"""
        project_files = list(self.standards_dir.glob("project_*.json"))
        
        for project_file in project_files:
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                project_name = project_data.get("project_name", project_file.stem)
                self.project_standards[project_name] = project_data
                
                self.logger.info(f"Loaded project standards: {project_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load project standards from {project_file}: {e}")
    
    def get_standards_for_language(self, language: str, project_name: str = None) -> Dict[str, Any]:
        """获取指定语言的审核标准"""
        # 从通用标准开始
        standards = {}
        
        if language in self.universal_standards.get("languages", {}):
            standards = copy.deepcopy(self.universal_standards["languages"][language])
        
        # 应用项目特定标准
        if project_name and project_name in self.project_standards:
            project_data = self.project_standards[project_name]
            
            if language in project_data.get("language_overrides", {}):
                project_overrides = project_data["language_overrides"][language]
                standards = self._merge_standards(standards, project_overrides)
        
        # 添加全局规则
        if "global_rules" in self.universal_standards:
            standards["global_rules"] = self.universal_standards["global_rules"]
        
        # 添加严重程度级别
        if "severity_levels" in self.universal_standards:
            standards["severity_levels"] = self.universal_standards["severity_levels"]
        
        return standards
    
    def _merge_standards(self, base_standards: Dict, overrides: Dict) -> Dict:
        """合并标准规范，项目特定规范覆盖通用规范"""
        merged = copy.deepcopy(base_standards)
        
        for key, value in overrides.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_standards(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def create_project_standards(self, project_name: str, 
                                base_template: str = "default",
                                custom_rules: Dict[str, Any] = None) -> bool:
        """创建项目特定标准规范"""
        try:
            project_standards = {
                "metadata": {
                    "project_name": project_name,
                    "version": "1.0.0",
                    "created_date": datetime.now().isoformat(),
                    "base_template": base_template,
                    "description": f"Project-specific standards for {project_name}"
                },
                "language_overrides": custom_rules or {},
                "project_rules": {
                    "file_naming": {
                        "pattern": "^[a-z_][a-z0-9_]*$",
                        "severity": "warning",
                        "description": "文件名使用小写字母和下划线"
                    },
                    "directory_structure": {
                        "max_depth": 5,
                        "severity": "info",
                        "description": "目录结构最大深度"
                    }
                },
                "team_preferences": {
                    "review_threshold": "warning",
                    "auto_fix_enabled": False,
                    "notification_level": "error"
                }
            }
            
            # 保存到文件
            project_file = self.standards_dir / f"project_{project_name}.json"
            project_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_standards, f, indent=2, ensure_ascii=False)
            
            # 更新内存中的标准
            self.project_standards[project_name] = project_standards
            
            self.logger.info(f"Created project standards for: {project_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create project standards: {e}")
            return False
    
    def update_project_standards(self, project_name: str, 
                               updates: Dict[str, Any]) -> bool:
        """更新项目特定标准规范"""
        try:
            if project_name not in self.project_standards:
                self.logger.error(f"Project standards not found: {project_name}")
                return False
            
            # 备份当前版本
            current_standards = copy.deepcopy(self.project_standards[project_name])
            self.standards_history.append({
                "project_name": project_name,
                "timestamp": datetime.now().isoformat(),
                "standards": current_standards
            })
            
            # 应用更新
            updated_standards = self._merge_standards(current_standards, updates)
            updated_standards["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 保存到文件
            project_file = self.standards_dir / f"project_{project_name}.json"
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(updated_standards, f, indent=2, ensure_ascii=False)
            
            # 更新内存
            self.project_standards[project_name] = updated_standards
            
            self.logger.info(f"Updated project standards for: {project_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update project standards: {e}")
            return False
    
    def validate_standards(self, standards: Dict[str, Any]) -> List[str]:
        """验证标准规范的有效性"""
        errors = []
        
        # 检查必需字段
        if "metadata" not in standards:
            errors.append("Missing metadata section")
        
        # 检查严重程度级别
        severity_levels = ["critical", "error", "warning", "info"]
        
        def check_severity(obj, path=""):
            if isinstance(obj, dict):
                if "severity" in obj:
                    severity = obj["severity"]
                    if severity not in severity_levels:
                        errors.append(f"Invalid severity level '{severity}' at {path}")
                
                for key, value in obj.items():
                    check_severity(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_severity(item, f"{path}[{i}]")
        
        check_severity(standards)
        
        return errors
    
    def get_project_list(self) -> List[Dict[str, Any]]:
        """获取所有项目的标准规范列表"""
        projects = []
        
        for project_name, standards in self.project_standards.items():
            metadata = standards.get("metadata", {})
            projects.append({
                "name": project_name,
                "version": metadata.get("version", "unknown"),
                "created_date": metadata.get("created_date"),
                "last_updated": metadata.get("last_updated"),
                "description": metadata.get("description", "")
            })
        
        return projects
    
    def export_standards(self, project_name: str = None) -> Dict[str, Any]:
        """导出标准规范"""
        if project_name:
            if project_name in self.project_standards:
                return self.project_standards[project_name]
            else:
                raise ValueError(f"Project not found: {project_name}")
        else:
            return {
                "universal_standards": self.universal_standards,
                "project_standards": self.project_standards
            }
    
    def import_standards(self, standards_data: Dict[str, Any], 
                        project_name: str = None) -> bool:
        """导入标准规范"""
        try:
            # 验证标准规范
            errors = self.validate_standards(standards_data)
            if errors:
                self.logger.error(f"Standards validation failed: {errors}")
                return False
            
            if project_name:
                # 导入项目特定标准
                self.project_standards[project_name] = standards_data
                
                # 保存到文件
                project_file = self.standards_dir / f"project_{project_name}.json"
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(standards_data, f, indent=2, ensure_ascii=False)
            else:
                # 导入通用标准
                self.universal_standards = standards_data
                
                # 保存到文件
                universal_file = self.standards_dir / "universal_code_review_standards.json"
                with open(universal_file, 'w', encoding='utf-8') as f:
                    json.dump(standards_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Standards imported successfully for: {project_name or 'universal'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import standards: {e}")
            return False
    
    def get_standards_history(self, project_name: str) -> List[Dict[str, Any]]:
        """获取项目标准规范的历史版本"""
        return [
            entry for entry in self.standards_history
            if entry["project_name"] == project_name
        ]
    
    def rollback_standards(self, project_name: str, timestamp: str) -> bool:
        """回滚到指定时间的标准规范版本"""
        try:
            # 查找历史版本
            target_version = None
            for entry in self.standards_history:
                if (entry["project_name"] == project_name and 
                    entry["timestamp"] == timestamp):
                    target_version = entry["standards"]
                    break
            
            if not target_version:
                self.logger.error(f"History version not found: {timestamp}")
                return False
            
            # 恢复版本
            self.project_standards[project_name] = target_version
            
            # 保存到文件
            project_file = self.standards_dir / f"project_{project_name}.json"
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(target_version, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Rolled back standards for {project_name} to {timestamp}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback standards: {e}")
            return False
