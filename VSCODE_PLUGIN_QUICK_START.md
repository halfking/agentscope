# 🚀 VS Code插件快速启动指南

## ✅ **前提条件检查**

### 1. 后端服务状态
- ✅ **服务运行中**: http://localhost:8000
- ✅ **API功能正常**: 所有REST端点工作正常
- ⚠️ **WebSocket问题**: 暂时跳过，使用HTTP模式

### 2. 插件文件
- ✅ **插件包**: `agentscope-multi-agent-workflow-2.0.0.vsix`
- ✅ **大小**: 1.05MB
- ✅ **位置**: `/Users/xutaohuang/workspace/ai/agentscope/vscode-extension/`

## 📦 **插件安装步骤**

### 步骤1: 安装插件
1. **打开VS Code**
2. **打开扩展面板**: `Ctrl+Shift+X`
3. **点击"..."菜单** → **"从VSIX安装..."**
4. **选择文件**: `agentscope-multi-agent-workflow-2.0.0.vsix`
5. **等待安装完成**
6. **重新加载窗口**: `Ctrl+Shift+P` → "Developer: Reload Window"

### 步骤2: 验证安装
1. **检查扩展列表**: 搜索 "AgentScope"
2. **查看状态栏**: 应该显示 "$(robot) AgentScope"
3. **检查左侧面板**: 应该有AgentScope图标

## 🎮 **功能测试**

### 测试1: 命令面板功能
1. **按 `Ctrl+Shift+P`** 打开命令面板
2. **输入 "AgentScope"** 查看可用命令
3. **应该看到以下命令**:
   - AgentScope: Start Agent System
   - AgentScope: Stop Agent System
   - AgentScope: Analyze Project
   - AgentScope: Quality Check
   - AgentScope: Security Scan
   - AgentScope: Show Agent Dashboard
   - AgentScope: Configure Agents
   - AgentScope: View Task History

### 测试2: 启动系统
1. **执行命令**: "AgentScope: Start Agent System"
2. **观察状态栏变化**: 应该显示连接进度
3. **成功后状态栏显示**: "$(robot) AgentScope ✓"

### 测试3: 快捷键功能
- **`Ctrl+Shift+A`**: 显示仪表板
- **`Ctrl+Shift+U`**: 启用Augment集成

### 测试4: 左侧面板
1. **点击左侧AgentScope图标** (🤖)
2. **应该看到4个视图**:
   - Agent Status (智能体状态)
   - Task Queue (任务队列)  
   - Analysis Results (分析结果)
   - Augment Integration (Augment集成)

## 🔧 **配置设置**

### 推荐配置
在VS Code设置中添加以下配置 (`Ctrl+,` → 搜索 "agentscope"):

```json
{
    "agentscope.backend.host": "localhost",
    "agentscope.backend.port": 8000,
    "agentscope.backend.protocol": "http",
    "agentscope.backend.useWebSocket": false,
    "agentscope.backend.pollingInterval": 2000,
    "agentscope.llm.provider": "siliconflow",
    "agentscope.augment.enabled": true,
    "agentscope.dashboard.autoOpen": true,
    "agentscope.analysis.autoRun": false
}
```

## 🎯 **实际使用场景**

### 场景1: 代码分析
1. **打开一个代码文件**
2. **按 `Ctrl+Shift+P`**
3. **执行**: "AgentScope: Analyze Project"
4. **查看分析结果**

### 场景2: 质量检查
1. **选中代码文件**
2. **按 `Ctrl+Shift+Q`** (需要先启动系统)
3. **查看质量报告**

### 场景3: 安全扫描
1. **选中代码文件**
2. **按 `Ctrl+Shift+S`** (需要先启动系统)
3. **查看安全报告**

### 场景4: Augment集成
1. **按 `Ctrl+Shift+U`** 启用Augment集成
2. **使用自然语言指令**: "分析这个文件的安全问题"
3. **查看智能分析结果**

## 🐛 **常见问题解决**

### 问题1: 插件未显示
**解决方案**:
1. 确认插件已正确安装
2. 重新加载VS Code窗口
3. 检查扩展是否已启用

### 问题2: 无法连接后端
**解决方案**:
1. 确认后端服务运行: `curl http://localhost:8000/health`
2. 检查配置设置中的host和port
3. 暂时禁用WebSocket: `"agentscope.backend.useWebSocket": false`

### 问题3: 快捷键不工作
**解决方案**:
1. 先执行 "Start Agent System"
2. 确认系统状态为 "active"
3. 检查快捷键冲突

### 问题4: 命令不可用
**解决方案**:
1. 检查上下文条件 (systemActive)
2. 先启动系统再使用功能命令
3. 查看开发者控制台错误信息

## 📊 **成功指标**

### 插件正常工作的标志:
1. ✅ **状态栏显示**: "$(robot) AgentScope ✓"
2. ✅ **左侧面板**: AgentScope视图容器可见
3. ✅ **命令可用**: 所有AgentScope命令在命令面板中可见
4. ✅ **快捷键响应**: Ctrl+Shift+A 能打开仪表板
5. ✅ **功能执行**: 能够执行代码分析等功能

### 后端连接成功的标志:
1. ✅ **HTTP连接**: API调用返回正确响应
2. ✅ **状态更新**: 智能体状态正常显示
3. ✅ **任务执行**: 分析任务能够创建和执行
4. ✅ **结果展示**: 分析结果能够正确显示

## 🎉 **开始使用**

现在您可以：

1. **安装插件** (按照上述步骤)
2. **启动系统** (Start Agent System)
3. **开始分析** (使用各种分析功能)
4. **享受智能化编程体验**!

---

**💡 提示**: 即使WebSocket连接有问题，HTTP API功能完全正常，您仍然可以使用所有核心功能！插件会自动降级到HTTP轮询模式。
