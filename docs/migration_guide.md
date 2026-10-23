# AgentScope多智能体编程工作流 - 优化架构迁移指南

## 概述

本指南帮助您从当前的AgentScope集成架构平滑迁移到优化的深度集成架构。新架构提供了更好的性能、更深度的AgentScope集成和真实的Augment集成能力。

## 主要变更

### 1. 智能体基类优化

#### 变更前 (BaseSpecializedAgent)
```python
from agentscope_integration.agents.base_specialized_agent import BaseSpecializedAgent

class MyAgent(BaseSpecializedAgent):
    def __init__(self, agent_id, role, name, sys_prompt, model, formatter, **kwargs):
        super().__init__(
            agent_id=agent_id,
            role=role,
            name=name,
            sys_prompt=sys_prompt,
            model=model,
            formatter=formatter,
            **kwargs
        )
```

#### 变更后 (OptimizedSpecializedAgent)
```python
from agentscope_integration.agents.base_specialized_agent import OptimizedSpecializedAgent

class MyAgent(OptimizedSpecializedAgent):
    def __init__(self, model, formatter, **kwargs):
        super().__init__(
            name="MyAgent",
            role=AgentRole.CODE_MANAGER,
            supported_tasks=[TaskType.CODE_ANALYSIS],
            model=model,
            formatter=formatter,
            **kwargs
        )
```

#### 迁移步骤
1. 更新导入语句
2. 修改构造函数参数顺序
3. 移除`agent_id`参数（自动生成）
4. 添加`supported_tasks`参数

### 2. 工作流管理器升级

#### 变更前 (自定义TaskManager)
```python
from agentscope_integration.core.task_manager import TaskManager
from agentscope_integration.core.agent_coordinator import AgentCoordinator

task_manager = TaskManager(agent_coordinator)
task_id = await task_manager.submit_task(task)
```

#### 变更后 (AgentScopeWorkflowManager)
```python
from agentscope_integration.core.agentscope_workflow_manager import AgentScopeWorkflowManager

workflow_manager = AgentScopeWorkflowManager()
await workflow_manager.register_agent(agent)
workflow_id = await workflow_manager.create_workflow(task)
```

#### 迁移步骤
1. 替换TaskManager为AgentScopeWorkflowManager
2. 注册智能体到工作流管理器
3. 使用`create_workflow`替代`submit_task`
4. 更新状态查询方法

### 3. Augment集成升级

#### 变更前 (模拟集成)
```python
# 仅在测试中模拟Augment集成
class AugmentIntegrationTestSuite:
    async def test_augment_integration(self):
        # 模拟测试
        pass
```

#### 变更后 (真实集成)
```python
from agentscope_integration.integrations.augment_integration_hub import AugmentIntegrationHub

augment_hub = AugmentIntegrationHub(workflow_manager)
await augment_hub.start()

# 处理真实的Augment消息
message = AugmentMessage(...)
await augment_hub.process_augment_message(message)
```

#### 迁移步骤
1. 创建AugmentIntegrationHub实例
2. 启动Augment集成服务
3. 注册事件回调处理器
4. 更新VS Code插件集成

## 渐进式迁移策略

### 阶段1: 基础组件迁移 (1周)

#### 1.1 更新智能体基类
```bash
# 备份现有实现
cp agentscope_integration/agents/base_specialized_agent.py \
   agentscope_integration/agents/base_specialized_agent.py.backup

# 逐个更新智能体
# 1. 更新CodeManagerAgent
# 2. 更新ComplianceAuditorAgent
# 3. 测试验证
```

#### 1.2 兼容性适配器
```python
# 创建兼容性适配器
class LegacyAgentAdapter:
    """为旧版智能体提供兼容性支持"""
    
    def __init__(self, legacy_agent):
        self.legacy_agent = legacy_agent
        self.optimized_agent = self._convert_to_optimized(legacy_agent)
    
    def _convert_to_optimized(self, legacy_agent):
        # 转换逻辑
        pass
```

### 阶段2: 工作流系统迁移 (1周)

#### 2.1 并行运行
```python
class HybridWorkflowManager:
    """混合工作流管理器 - 支持新旧系统并行"""
    
    def __init__(self):
        self.legacy_manager = TaskManager()
        self.optimized_manager = AgentScopeWorkflowManager()
        self.use_optimized = False  # 特性开关
    
    async def create_workflow(self, task):
        if self.use_optimized:
            return await self.optimized_manager.create_workflow(task)
        else:
            return await self.legacy_manager.submit_task(task)
```

#### 2.2 数据迁移
```python
async def migrate_task_history():
    """迁移任务历史数据"""
    legacy_tasks = await legacy_manager.get_all_tasks()
    
    for task in legacy_tasks:
        # 转换任务格式
        converted_task = convert_legacy_task(task)
        
        # 存储到新系统
        await optimized_manager.store_task_history(converted_task)
```

### 阶段3: Augment集成迁移 (1周)

#### 3.1 VS Code插件更新
```typescript
// 渐进式启用Augment监听
class ProgressiveAugmentIntegration {
    private useRealIntegration: boolean = false;
    
    async initialize() {
        if (this.useRealIntegration) {
            await this.startRealAugmentWatcher();
        } else {
            await this.startMockAugmentWatcher();
        }
    }
    
    async enableRealIntegration() {
        this.useRealIntegration = true;
        await this.initialize();
    }
}
```

#### 3.2 配置管理
```json
{
  "agentscope": {
    "features": {
      "optimized_agents": true,
      "agentscope_workflows": true,
      "real_augment_integration": false
    },
    "migration": {
      "legacy_compatibility": true,
      "data_migration_completed": false
    }
  }
}
```

## API兼容性

### 保持兼容的API

#### 1. 任务提交接口
```python
# 旧接口继续支持
@app.post("/tasks")
async def submit_task(task_data: dict):
    # 内部转换为新的工作流
    task = convert_legacy_task(task_data)
    workflow_id = await workflow_manager.create_workflow(task)
    
    # 返回兼容格式
    return {"task_id": workflow_id, "status": "submitted"}
```

#### 2. 智能体状态接口
```python
# 保持相同的响应格式
@app.get("/agents")
async def get_agents():
    agents_status = []
    for agent in optimized_agents:
        # 转换为旧格式
        status = convert_to_legacy_format(agent.get_status())
        agents_status.append(status)
    return agents_status
```

### 废弃的API

#### 1. 直接智能体调用
```python
# 废弃：直接调用智能体
# agent.execute_task(task)

# 推荐：通过工作流管理器
# workflow_manager.create_workflow(task)
```

#### 2. 自定义任务分发
```python
# 废弃：自定义AgentCoordinator
# coordinator.dispatch_task(task, agent_id)

# 推荐：使用AgentScope Pipeline
# workflow_manager.create_workflow(task)
```

## 配置迁移

### 1. 系统配置更新

#### 旧配置格式
```json
{
  "agents": {
    "code_manager": {
      "agent_id": "code_manager",
      "role": "code_manager",
      "enabled": true
    }
  },
  "task_management": {
    "max_concurrent_tasks": 5,
    "task_timeout": 300
  }
}
```

#### 新配置格式
```json
{
  "agents": {
    "code_manager": {
      "name": "CodeManager",
      "role": "code_manager",
      "enabled": true,
      "supported_tasks": ["code_analysis", "architecture_analysis"]
    }
  },
  "workflow_management": {
    "max_concurrent_workflows": 5,
    "workflow_timeout": 300,
    "use_agentscope_pipelines": true
  },
  "augment_integration": {
    "enabled": true,
    "real_time_monitoring": true,
    "nlp_confidence_threshold": 0.7
  }
}
```

### 2. 配置迁移脚本
```python
def migrate_configuration(old_config_path: str, new_config_path: str):
    """迁移配置文件"""
    with open(old_config_path) as f:
        old_config = json.load(f)
    
    new_config = {
        "agents": {},
        "workflow_management": {},
        "augment_integration": {
            "enabled": False,  # 默认禁用，手动启用
            "real_time_monitoring": True,
            "nlp_confidence_threshold": 0.7
        }
    }
    
    # 迁移智能体配置
    for agent_id, agent_config in old_config.get("agents", {}).items():
        new_config["agents"][agent_id] = {
            "name": agent_config.get("name", agent_id.title()),
            "role": agent_config["role"],
            "enabled": agent_config.get("enabled", True),
            "supported_tasks": get_default_tasks_for_role(agent_config["role"])
        }
    
    # 迁移任务管理配置
    task_config = old_config.get("task_management", {})
    new_config["workflow_management"] = {
        "max_concurrent_workflows": task_config.get("max_concurrent_tasks", 5),
        "workflow_timeout": task_config.get("task_timeout", 300),
        "use_agentscope_pipelines": True
    }
    
    with open(new_config_path, 'w') as f:
        json.dump(new_config, f, indent=2)
```

## 测试和验证

### 1. 迁移验证清单

- [ ] 所有智能体成功迁移到OptimizedSpecializedAgent
- [ ] 工作流管理器正常工作
- [ ] 现有API接口保持兼容
- [ ] 配置文件成功迁移
- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 性能测试显示改进

### 2. 回滚计划

```bash
#!/bin/bash
# 回滚脚本

echo "开始回滚到旧版本..."

# 1. 恢复备份文件
cp agentscope_integration/agents/base_specialized_agent.py.backup \
   agentscope_integration/agents/base_specialized_agent.py

# 2. 恢复配置文件
cp config/system_config.json.backup \
   config/system_config.json

# 3. 重启服务
systemctl restart agentscope-service

echo "回滚完成"
```

### 3. 监控和告警

```python
class MigrationMonitor:
    """迁移监控器"""
    
    def __init__(self):
        self.metrics = {
            "legacy_api_calls": 0,
            "optimized_api_calls": 0,
            "migration_errors": 0
        }
    
    def track_api_call(self, api_type: str):
        self.metrics[f"{api_type}_api_calls"] += 1
    
    def track_error(self, error: Exception):
        self.metrics["migration_errors"] += 1
        # 发送告警
        self.send_alert(f"Migration error: {error}")
```

## 最佳实践

### 1. 迁移前准备
- 完整备份现有系统
- 在测试环境先行验证
- 准备详细的回滚计划
- 通知所有相关团队

### 2. 迁移过程中
- 逐步启用新功能
- 密切监控系统状态
- 保持新旧系统并行运行
- 及时处理发现的问题

### 3. 迁移后验证
- 全面的功能测试
- 性能基准测试
- 用户接受度测试
- 文档更新

## 支持和帮助

如果在迁移过程中遇到问题，请：

1. 查看详细的错误日志
2. 参考故障排除指南
3. 联系技术支持团队
4. 在必要时执行回滚计划

迁移完成后，您将获得：
- 更好的性能和稳定性
- 深度的AgentScope集成
- 真实的Augment集成能力
- 更强的可扩展性和维护性
