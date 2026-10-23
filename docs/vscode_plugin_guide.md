# AgentScope VS Code插件安装和使用指南

## 🎯 概述

AgentScope VS Code插件是一个企业级的多智能体编程工作流系统，集成了真实的Augment监听和处理能力，支持自然语言指令驱动的代码分析和质量管理。

## 📦 插件特性

### 🔥 核心功能
- **AgentScope深度集成**: 使用ReActAgent、MsgHub、Pipeline等原生组件
- **真实Augment集成**: 监听和处理Augment Agent的实际输出
- **自然语言处理**: 支持中文和英文指令解析
- **智能代码分析**: 自动化代码质量检查和安全扫描
- **实时工作流管理**: 可视化任务队列和结果展示

### 🛠️ 技术特性
- **硅基流动API集成**: 使用deepseek-ai/deepseek-coder模型
- **企业级性能**: 支持大规模并发处理
- **向后兼容**: 平滑迁移现有系统
- **可扩展架构**: 支持自定义智能体和工作流

## 🚀 快速安装

### 方法1: 自动部署脚本（推荐）

```bash
# 进入项目目录
cd /path/to/agentscope

# 运行部署脚本
python scripts/deploy_vscode_plugin.py
```

### 方法2: 手动安装

```bash
# 1. 编译插件
cd vscode-extension
npm install
npm run compile

# 2. 打包插件
npx vsce package

# 3. 安装插件
code --install-extension agentscope-multi-agent-workflow-2.0.0.vsix

# 4. 启动后端服务
cd ..
python scripts/start_optimized_service.py --demo
```

## ⚙️ 配置说明

### 环境变量配置

创建或编辑 `.env` 文件：

```bash
# 硅基流动API配置
SILICONFLOW_API_KEY=your-siliconflow-api-key-here

# AgentScope服务配置
AGENTSCOPE_HOST=localhost
AGENTSCOPE_PORT=8000
AGENTSCOPE_WEBSOCKET_PORT=8001

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/agentscope.log
```

### VS Code设置

在VS Code设置中搜索 `agentscope` 进行配置：

```json
{
    "agentscope.backend.host": "localhost",
    "agentscope.backend.port": 8000,
    "agentscope.llm.provider": "siliconflow",
    "agentscope.llm.model": "deepseek-ai/deepseek-coder",
    "agentscope.augment.enabled": true,
    "agentscope.augment.realTimeMonitoring": true,
    "agentscope.analysis.autoRun": false,
    "agentscope.features.optimizedAgents": true,
    "agentscope.features.agentscopeWorkflows": true,
    "agentscope.features.realAugmentIntegration": true
}
```

## 🎮 使用指南

### 基本操作

#### 1. 启动系统
- 打开VS Code
- 在活动栏中点击AgentScope图标（🤖）
- 点击"Start Agent System"或使用快捷键 `Ctrl+Shift+A`

#### 2. 启用Augment集成
- 使用命令面板: `Ctrl+Shift+P` → "AgentScope: Enable Augment Integration"
- 或使用快捷键: `Ctrl+Shift+U`
- 或在AgentScope面板中点击"Enable Augment Integration"

#### 3. 代码分析
```bash
# 项目分析
Ctrl+Shift+P (Mac: Cmd+Shift+P)

# 质量检查
Ctrl+Shift+Q (Mac: Cmd+Shift+Q)

# 安全扫描
Ctrl+Shift+S (Mac: Cmd+Shift+S)
```

### 高级功能

#### 自然语言指令
1. 启用Augment集成后，使用命令: "Process Augment Command"
2. 输入自然语言指令，例如：
   - "分析这个文件的安全问题"
   - "检查代码质量并提供改进建议"
   - "扫描项目中的潜在漏洞"

#### 实时监听
- 插件会自动监听Augment Agent的活动
- 检测到相关指令时会自动创建分析任务
- 结果会显示在AgentScope面板中

#### 工作流管理
- **任务队列**: 查看当前和历史任务
- **分析结果**: 浏览详细的分析报告
- **智能体状态**: 监控各个智能体的运行状态

## 🔧 故障排除

### 常见问题

#### 1. 插件无法启动
```bash
# 检查后端服务
curl http://localhost:8000/health

# 重启后端服务
python scripts/start_optimized_service.py --demo

# 检查VS Code开发者控制台
Help → Toggle Developer Tools → Console
```

#### 2. Augment集成失败
- 确保Augment Agent正在运行
- 检查VS Code扩展权限
- 重启VS Code和后端服务

#### 3. API连接错误
- 验证硅基流动API密钥
- 检查网络连接
- 查看后端服务日志

#### 4. 性能问题
- 调整并发设置
- 优化分析范围
- 检查系统资源使用

### 日志查看

```bash
# 后端服务日志
tail -f logs/agentscope.log

# VS Code插件日志
# 在VS Code中: Help → Toggle Developer Tools → Console

# 系统性能监控
python tests/performance_benchmark.py
```

## 📊 性能优化

### 推荐配置

```json
{
    "agentscope.analysis.excludePatterns": [
        "node_modules/**",
        "**/*.min.js",
        "**/__pycache__/**",
        "**/venv/**",
        "**/env/**",
        "**/.git/**",
        "**/dist/**",
        "**/build/**"
    ],
    "agentscope.augment.nlpConfidenceThreshold": 0.7,
    "agentscope.notifications.level": "info"
}
```

### 性能基准

基于最新测试结果：
- **总体评级**: A级 (97分)
- **并发处理**: 98.91 tasks/s
- **工作流管理**: 3.31 workflows/s
- **Augment集成**: 4.83 messages/s
- **内存效率**: 632,625 ops/s

## 🔄 更新和维护

### 插件更新
```bash
# 重新打包和安装
cd vscode-extension
npm run compile
npx vsce package
code --install-extension agentscope-multi-agent-workflow-2.0.0.vsix
```

### 配置备份
```bash
# 导出VS Code设置
code --list-extensions > extensions.txt

# 备份配置文件
cp .env .env.backup
cp config/system_config.json config/system_config.json.backup
```

## 📚 相关文档

- [优化用户指南](optimized_user_guide.md)
- [迁移指南](migration_guide.md)
- [项目状态](../PROJECT_STATUS_OPTIMIZED.md)
- [API文档](api_documentation.md)

## 🆘 技术支持

如遇问题，请：
1. 查看本指南的故障排除部分
2. 检查项目GitHub Issues
3. 运行诊断脚本: `python tests/test_optimized_integration.py`
4. 提供详细的错误日志和系统信息

---

**AgentScope VS Code插件 v2.0.0** - 企业级多智能体编程工作流系统
