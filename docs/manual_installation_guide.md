# AgentScope VS Code插件手动安装指南

## 🎯 概述

本指南提供AgentScope VS Code插件的手动安装步骤，适用于无法使用自动部署脚本的情况。

## 📋 前提条件

### 必需软件
- ✅ **VS Code**: 版本 1.70.0 或更高
- ✅ **Node.js**: 版本 16.x 或更高
- ✅ **Python**: 版本 3.8 或更高
- ✅ **Git**: 用于代码管理

### 可选软件
- **VS Code命令行工具**: 用于自动化安装
- **Docker**: 用于容器化部署

## 🚀 安装步骤

### 步骤1: 准备插件包

插件包已经生成在以下位置：
```
/Users/xutaohuang/workspace/ai/agentscope/vscode-extension/agentscope-multi-agent-workflow-2.0.0.vsix
```

### 步骤2: 手动安装插件

#### 方法A: 通过VS Code界面安装（推荐）

1. **打开VS Code**
2. **打开扩展面板**:
   - 点击左侧活动栏的扩展图标（四个方块）
   - 或使用快捷键 `Ctrl+Shift+X` (Mac: `Cmd+Shift+X`)

3. **安装插件**:
   - 点击扩展面板右上角的"..."菜单
   - 选择"从VSIX安装..."（Install from VSIX...）
   - 浏览并选择插件文件: `agentscope-multi-agent-workflow-2.0.0.vsix`
   - 点击"安装"

4. **重启VS Code**:
   - 安装完成后，VS Code会提示重启
   - 点击"重新加载"或重启VS Code

#### 方法B: 通过命令行安装

如果VS Code命令行工具已配置：

```bash
# 进入插件目录
cd /Users/xutaohuang/workspace/ai/agentscope/vscode-extension

# 安装插件
code --install-extension agentscope-multi-agent-workflow-2.0.0.vsix
```

### 步骤3: 配置环境变量

1. **创建环境配置文件**:
```bash
# 在项目根目录创建.env文件
cd /Users/xutaohuang/workspace/ai/agentscope
cat > .env << EOF
# 硅基流动API配置
SILICONFLOW_API_KEY=your-siliconflow-api-key-here

# AgentScope服务配置
AGENTSCOPE_HOST=localhost
AGENTSCOPE_PORT=8000
AGENTSCOPE_WEBSOCKET_PORT=8001

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/agentscope.log
EOF
```

2. **验证配置文件**:
```bash
# 检查.env文件内容
cat .env
```

### 步骤4: 启动后端服务

```bash
# 进入项目目录
cd /Users/xutaohuang/workspace/ai/agentscope

# 安装Python依赖（如果尚未安装）
pip install -r requirements.txt

# 启动优化服务
python3 scripts/start_optimized_service.py --demo
```

### 步骤5: 验证安装

1. **检查插件是否已安装**:
   - 在VS Code中打开扩展面板
   - 搜索"AgentScope"
   - 确认插件显示为"已安装"

2. **检查活动栏图标**:
   - 在VS Code左侧活动栏中应该看到机器人图标（🤖）
   - 点击图标打开AgentScope面板

3. **测试基本功能**:
   - 点击"Start Agent System"
   - 检查是否能连接到后端服务
   - 尝试启用Augment集成

## ⚙️ VS Code设置配置

### 打开设置

1. **通过菜单**: File → Preferences → Settings (Mac: Code → Preferences → Settings)
2. **通过快捷键**: `Ctrl+,` (Mac: `Cmd+,`)
3. **搜索**: 在设置搜索框中输入"agentscope"

### 推荐配置

```json
{
    "agentscope.backend.host": "localhost",
    "agentscope.backend.port": 8000,
    "agentscope.backend.protocol": "http",
    "agentscope.websocket.port": 8001,
    "agentscope.llm.provider": "siliconflow",
    "agentscope.llm.model": "deepseek-ai/deepseek-coder",
    "agentscope.augment.enabled": true,
    "agentscope.augment.realTimeMonitoring": true,
    "agentscope.augment.nlpConfidenceThreshold": 0.7,
    "agentscope.analysis.autoRun": false,
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
    "agentscope.features.optimizedAgents": true,
    "agentscope.features.agentscopeWorkflows": true,
    "agentscope.features.realAugmentIntegration": true,
    "agentscope.notifications.level": "info",
    "agentscope.dashboard.autoOpen": true
}
```

## 🎮 快速开始

### 基本使用流程

1. **启动系统**:
   - 打开VS Code
   - 点击AgentScope图标
   - 点击"Start Agent System"

2. **启用Augment集成**:
   - 使用快捷键 `Ctrl+Shift+U`
   - 或在命令面板中搜索"Enable Augment Integration"

3. **执行代码分析**:
   - 项目分析: `Ctrl+Shift+P`
   - 质量检查: `Ctrl+Shift+Q`
   - 安全扫描: `Ctrl+Shift+S`

### 快捷键总览

| 功能 | Windows/Linux | Mac |
|------|---------------|-----|
| 显示仪表板 | `Ctrl+Shift+A` | `Cmd+Shift+A` |
| 项目分析 | `Ctrl+Shift+P` | `Cmd+Shift+P` |
| 质量检查 | `Ctrl+Shift+Q` | `Cmd+Shift+Q` |
| 安全扫描 | `Ctrl+Shift+S` | `Cmd+Shift+S` |
| 启用Augment集成 | `Ctrl+Shift+U` | `Cmd+Shift+U` |

## 🔧 故障排除

### 常见问题

#### 1. 插件安装失败
- **问题**: 无法从VSIX安装
- **解决**: 
  - 确保VS Code版本 ≥ 1.70.0
  - 尝试重启VS Code后重新安装
  - 检查VSIX文件是否完整

#### 2. 后端连接失败
- **问题**: 无法连接到AgentScope服务
- **解决**:
  ```bash
  # 检查服务状态
  curl http://localhost:8000/health
  
  # 重启服务
  python3 scripts/start_optimized_service.py --demo
  
  # 检查端口占用
  lsof -i :8000
  ```

#### 3. Augment集成无响应
- **问题**: Augment功能不工作
- **解决**:
  - 检查VS Code开发者控制台: Help → Toggle Developer Tools
  - 确认配置中`agentscope.augment.enabled`为true
  - 重启VS Code和后端服务

#### 4. API密钥错误
- **问题**: 硅基流动API调用失败
- **解决**:
  - 验证.env文件中的API密钥
  - 检查网络连接
  - 确认API密钥有效期

### 日志查看

```bash
# 后端服务日志
tail -f logs/agentscope.log

# VS Code插件日志
# 在VS Code中: Help → Toggle Developer Tools → Console

# 运行诊断测试
python3 tests/test_optimized_integration.py
```

## 📊 验证安装成功

### 功能检查清单

- [ ] VS Code中显示AgentScope图标
- [ ] 能够打开AgentScope面板
- [ ] 后端服务正常运行
- [ ] 能够启动Agent System
- [ ] Augment集成功能正常
- [ ] 代码分析功能可用
- [ ] 快捷键响应正常

### 性能测试

```bash
# 运行性能基准测试
python3 tests/performance_benchmark.py

# 预期结果:
# - 总体评级: A级 (90+分)
# - 并发处理: >80 tasks/s
# - 工作流管理: >3 workflows/s
# - Augment集成: >4 messages/s
```

## 🔄 卸载插件

如需卸载插件：

1. **通过VS Code界面**:
   - 打开扩展面板
   - 找到"AgentScope Multi-Agent Workflow"
   - 点击齿轮图标 → 卸载

2. **通过命令行**:
   ```bash
   code --uninstall-extension agentscope.agentscope-multi-agent-workflow
   ```

3. **清理配置**:
   ```bash
   # 删除配置文件
   rm .env
   rm -rf logs/
   ```

## 📚 下一步

安装完成后，建议阅读：
- [VS Code插件使用指南](vscode_plugin_guide.md)
- [优化用户指南](optimized_user_guide.md)
- [API文档](api_documentation.md)

---

**安装完成后，您就可以开始使用AgentScope多智能体编程工作流系统了！** 🎉
