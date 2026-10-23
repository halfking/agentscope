# AgentScope多智能体编程工作流 - 优化架构用户指南

## 🚀 概述

欢迎使用AgentScope多智能体编程工作流优化版本！这个版本提供了深度的AgentScope集成、真实的Augment集成和显著的性能提升。

### ✨ 新功能亮点

- **🧠 深度AgentScope集成**: 充分利用ReActAgent、MsgHub、Pipeline等原生能力
- **🎤 真实Augment集成**: 实时监听和处理Augment Agent的自然语言指令
- **🔄 智能工作流管理**: 支持顺序、并行、混合工作流
- **📊 性能追踪**: 内置性能监控和长期记忆存储
- **🔧 向后兼容**: 平滑迁移，保持现有功能

### 📈 性能提升

基于性能基准测试结果：
- **总体评级**: A级 (97分)
- **并发处理**: 98.91 tasks/s
- **工作流管理**: 3.31 workflows/s
- **Augment集成**: 4.83 messages/s
- **内存效率**: 632,625 ops/s

## 🛠️ 快速开始

### 1. 启动优化服务

```bash
# 基础启动
python scripts/start_optimized_service.py

# 带演示和测试
python scripts/start_optimized_service.py --demo --test

# 自定义配置
python scripts/start_optimized_service.py --host 0.0.0.0 --port 8080 --config custom_config.json
```

### 2. VS Code插件配置

在VS Code中安装插件后，配置Augment集成：

```json
{
  "agentscope": {
    "augment": {
      "enabled": true,
      "realTimeMonitoring": true,
      "nlpConfidenceThreshold": 0.7
    },
    "features": {
      "optimizedAgents": true,
      "agentscopeWorkflows": true,
      "realAugmentIntegration": true
    }
  }
}
```

### 3. 验证安装

运行集成测试验证系统正常工作：

```bash
python tests/test_optimized_integration_standalone.py
```

## 🎤 Augment集成使用

### 自然语言指令

优化版本支持通过自然语言指令触发代码分析：

#### 代码分析指令
```
"分析这个文件的代码结构"
"analyze the code quality"
"检查user_manager.py文件"
"explain this function"
```

#### 安全扫描指令
```
"扫描安全漏洞"
"check for SQL injection"
"检查硬编码密码"
"find security issues"
```

#### 质量检查指令
```
"检查代码质量"
"lint this code"
"代码规范检查"
"check best practices"
```

#### 重构建议指令
```
"优化这段代码"
"refactor suggestion"
"简化逻辑"
"improve performance"
```

### VS Code中的使用

1. **自动监听**: 插件会自动监听Augment Agent的活动
2. **手动触发**: 使用命令面板执行 `AgentScope: Process Augment Command`
3. **实时反馈**: 分析结果会实时显示在专用面板中

### 命令面板操作

- `AgentScope: Enable Augment Integration` - 启用Augment集成
- `AgentScope: Disable Augment Integration` - 禁用Augment集成
- `AgentScope: Detect Augment Activity` - 手动检测Augment活动
- `AgentScope: Show Augment Status` - 显示Augment集成状态

## 🔄 工作流管理

### 工作流类型

#### 1. 顺序工作流 (Sequential)
适用于需要依次执行的任务：
```python
# 代码分析 → 安全扫描 → 质量检查
task = AgentTask(
    type=TaskType.COMPREHENSIVE_ANALYSIS,
    title="全面代码分析",
    parameters={"file_path": "src/main.py"}
)
```

#### 2. 并行工作流 (Parallel)
适用于可以同时执行的任务：
```python
# 同时进行质量检查和性能分析
task = AgentTask(
    type=TaskType.QUALITY_CHECK,
    title="并行质量检查",
    parameters={"directory": "src/"}
)
```

#### 3. 混合工作流 (Hybrid)
先进行代码结构分析，再并行执行质量和安全检查：
```python
# 结构分析 → (质量检查 || 安全扫描)
task = AgentTask(
    type=TaskType.COMPREHENSIVE_ANALYSIS,
    title="混合分析工作流",
    parameters={"project_path": "/path/to/project"}
)
```

### API使用示例

#### 创建工作流
```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "type": "code_analysis",
    "title": "分析用户管理模块",
    "description": "分析user_manager.py的代码质量和安全性",
    "parameters": {
      "file_path": "src/user_manager.py",
      "include_security": true
    }
  }'
```

#### 查询工作流状态
```bash
curl http://localhost:8000/workflows/{workflow_id}
```

#### 处理Augment消息
```bash
curl -X POST http://localhost:8000/augment/message \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请分析这个文件的安全问题",
    "context": {
      "current_file": "src/auth.py",
      "language": "python"
    },
    "source": "manual"
  }'
```

## 📊 监控和统计

### 实时监控

访问 `http://localhost:8000/statistics` 获取系统统计信息：

```json
{
  "workflow_stats": {
    "total_workflows": 156,
    "completed": 152,
    "failed": 2,
    "success_rate": 97.4,
    "active_workflows": 2
  },
  "augment_stats": {
    "queue_size": 0,
    "cache_size": 45,
    "registered_callbacks": 3
  },
  "websocket_connections": 3
}
```

### 性能指标

系统内置性能追踪，可以查看：
- 任务执行时间
- 智能体性能指标
- 内存使用情况
- 工作流成功率

### 仪表板

访问 `http://localhost:8000` 查看Web仪表板，包含：
- 实时系统状态
- 任务执行历史
- 性能图表
- Augment集成状态

## 🔧 配置管理

### 系统配置

```json
{
  "agents": {
    "code_manager": {
      "name": "CodeManager",
      "role": "code_manager",
      "enabled": true,
      "supported_tasks": ["code_analysis", "architecture_analysis"]
    },
    "compliance_auditor": {
      "name": "ComplianceAuditor",
      "role": "compliance_auditor", 
      "enabled": true,
      "supported_tasks": ["security_scan", "quality_check"]
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
    "nlp_confidence_threshold": 0.7,
    "supported_languages": ["python", "javascript", "typescript", "java"]
  },
  "llm_providers": {
    "openai": {
      "enabled": true,
      "model": "gpt-4",
      "api_key": "your-api-key",
      "temperature": 0.7
    }
  }
}
```

### 环境变量

```bash
# 基础配置
export AGENTSCOPE_HOST=localhost
export AGENTSCOPE_PORT=8000
export AGENTSCOPE_CONFIG_PATH=config/system_config.json

# LLM配置
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-4

# Augment集成
export AUGMENT_INTEGRATION_ENABLED=true
export AUGMENT_CONFIDENCE_THRESHOLD=0.7

# 日志配置
export LOG_LEVEL=INFO
export LOG_FILE=logs/agentscope.log
```

## 🚨 故障排除

### 常见问题

#### 1. Augment集成无法启动
```bash
# 检查配置
curl http://localhost:8000/statistics

# 查看日志
tail -f logs/agentscope.log

# 重启Augment集成
# 在VS Code命令面板中执行：
# AgentScope: Disable Augment Integration
# AgentScope: Enable Augment Integration
```

#### 2. 工作流执行失败
```bash
# 检查智能体状态
curl http://localhost:8000/agents

# 查看工作流详情
curl http://localhost:8000/workflows/{workflow_id}

# 检查后端连接
# 在VS Code中查看输出面板的AgentScope日志
```

#### 3. 性能问题
```bash
# 运行性能基准测试
python tests/performance_benchmark.py

# 检查系统资源
curl http://localhost:8000/statistics

# 调整并发设置
# 修改配置文件中的max_concurrent_workflows
```

### 日志分析

系统日志位于 `logs/agentscope.log`，包含：
- 智能体执行日志
- 工作流状态变化
- Augment集成事件
- 性能指标
- 错误和异常信息

### 诊断工具

```bash
# 运行完整诊断
python scripts/start_optimized_service.py --test

# 检查配置有效性
python -c "
from agentscope_integration.core.config_manager import ConfigManager
config = ConfigManager('config/system_config.json')
print('配置有效' if config.validate_configuration() else '配置无效')
"

# 测试后端连接
curl -f http://localhost:8000/health || echo "后端服务未运行"
```

## 📚 高级用法

### 自定义智能体

```python
from agentscope_integration.agents.base_specialized_agent import OptimizedSpecializedAgent

class CustomAnalysisAgent(OptimizedSpecializedAgent):
    def __init__(self, model, formatter, **kwargs):
        super().__init__(
            name="CustomAnalyzer",
            role=AgentRole.CODE_MANAGER,
            supported_tasks=[TaskType.CODE_ANALYSIS],
            model=model,
            formatter=formatter,
            **kwargs
        )
    
    async def _register_specialized_tools(self):
        """注册自定义工具"""
        @trace_toolkit
        async def custom_analysis_tool(file_path: str) -> ToolResponse:
            # 自定义分析逻辑
            result = await self.perform_custom_analysis(file_path)
            
            # 存储到长期记忆
            await self.long_term_memory.store(
                "custom_analysis",
                f"result:{file_path}",
                result
            )
            
            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"自定义分析完成: {result}"
            )])
        
        self.toolkit.register_tool_function(custom_analysis_tool)
```

### 自定义工作流

```python
from agentscope_integration.core.agentscope_workflow_manager import AgentScopeWorkflowManager

class CustomWorkflowManager(AgentScopeWorkflowManager):
    async def create_custom_workflow(self, task: AgentTask) -> str:
        """创建自定义工作流"""
        # 自定义工作流逻辑
        participants = self.select_custom_agents(task)
        
        async with MsgHub(participants=participants) as hub:
            # 自定义消息流
            result = await self.execute_custom_pipeline(participants, task)
            return result
```

### 扩展Augment集成

```python
from agentscope_integration.integrations.augment_integration_hub import AugmentIntegrationHub

class ExtendedAugmentHub(AugmentIntegrationHub):
    async def process_custom_augment_event(self, event_data: Dict[str, Any]):
        """处理自定义Augment事件"""
        # 扩展事件处理逻辑
        custom_task = await self.create_custom_task(event_data)
        workflow_id = await self.workflow_manager.create_workflow(custom_task)
        return workflow_id
```

## 🔄 更新和维护

### 版本更新

```bash
# 检查当前版本
curl http://localhost:8000/health

# 备份配置
cp config/system_config.json config/system_config.json.backup

# 更新代码
git pull origin main

# 运行迁移脚本（如果需要）
python scripts/migrate_configuration.py

# 重启服务
python scripts/start_optimized_service.py
```

### 定期维护

1. **清理日志文件**
   ```bash
   find logs/ -name "*.log" -mtime +30 -delete
   ```

2. **清理缓存**
   ```bash
   curl -X POST http://localhost:8000/admin/clear-cache
   ```

3. **性能检查**
   ```bash
   python tests/performance_benchmark.py
   ```

4. **配置验证**
   ```bash
   python scripts/validate_configuration.py
   ```

## 📞 支持和反馈

如果您遇到问题或有改进建议：

1. **查看文档**: 首先查看本指南和故障排除部分
2. **检查日志**: 查看系统日志获取详细错误信息
3. **运行诊断**: 使用内置的诊断工具
4. **性能测试**: 运行基准测试检查系统性能
5. **联系支持**: 提供详细的错误信息和系统配置

---

🎉 **恭喜！您现在已经掌握了AgentScope多智能体编程工作流优化版本的使用方法。享受智能化的代码分析体验吧！**
