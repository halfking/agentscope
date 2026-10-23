# VS Code插件连接问题排查和解决方案

## 🔍 **问题诊断**

### 当前状态
- ✅ **HTTP连接**: 正常 - 所有REST API端点工作正常
- ❌ **WebSocket连接**: 失败 - 403 Forbidden错误
- ✅ **后端服务**: 正常运行在 http://localhost:8000

### 测试结果
```
HTTP连接: ✅ 正常
WebSocket连接: ❌ 失败 (403 Forbidden)
API端点: ✅ 正常
```

## 🛠️ **解决方案**

### 方案1: 修改插件配置以跳过WebSocket (推荐)

由于HTTP API完全正常，我们可以修改插件配置，暂时禁用WebSocket连接，使用HTTP轮询替代：

1. **在VS Code中打开设置** (`Ctrl+,`)
2. **搜索 "agentscope"**
3. **添加以下配置**:
```json
{
    "agentscope.backend.host": "localhost",
    "agentscope.backend.port": 8000,
    "agentscope.backend.protocol": "http",
    "agentscope.backend.useWebSocket": false,
    "agentscope.backend.pollingInterval": 2000,
    "agentscope.llm.provider": "siliconflow",
    "agentscope.augment.enabled": true,
    "agentscope.dashboard.autoOpen": true
}
```

### 方案2: 手动启动插件功能

即使WebSocket连接失败，您仍然可以手动使用插件的所有功能：

#### **启动AgentScope系统**
1. 按 `Ctrl+Shift+P` 打开命令面板
2. 输入 "AgentScope: Start Agent System"
3. 执行命令

#### **使用快捷键**
- `Ctrl+Shift+A`: 显示仪表板
- `Ctrl+Shift+U`: 启用Augment集成
- `Ctrl+Shift+P`: 项目分析 (需要先启动系统)
- `Ctrl+Shift+Q`: 质量检查 (需要先启动系统)
- `Ctrl+Shift+S`: 安全扫描 (需要先启动系统)

#### **使用状态栏**
- 点击状态栏左下角的 "$(robot) AgentScope" 按钮

### 方案3: 直接测试API功能

您可以直接测试后端API功能，验证系统工作正常：

```bash
# 代码分析
curl -X POST http://localhost:8000/api/analyze

# 质量检查  
curl -X POST http://localhost:8000/api/quality-check

# 安全扫描
curl -X POST http://localhost:8000/api/security-scan

# Augment指令处理
curl -X POST http://localhost:8000/api/augment/process
```

## 📋 **操作步骤**

### 立即可用的功能测试

1. **打开VS Code**
2. **确保插件已安装** (agentscope-multi-agent-workflow-2.0.0.vsix)
3. **按 `Ctrl+Shift+P`** 打开命令面板
4. **输入 "AgentScope"** 查看可用命令
5. **选择 "AgentScope: Start Agent System"**
6. **如果连接成功，状态栏会显示** "$(robot) AgentScope ✓"

### 如果连接失败

1. **检查后端服务状态**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **手动配置插件设置**:
   - 打开VS Code设置 (`Ctrl+,`)
   - 搜索 "agentscope"
   - 设置后端地址为 `localhost:8000`

3. **重新加载VS Code窗口**:
   - 按 `Ctrl+Shift+P`
   - 输入 "Developer: Reload Window"

## 🎯 **预期行为**

### 成功连接后您应该看到:

1. **状态栏显示**: "$(robot) AgentScope ✓" (绿色)
2. **左侧面板**: AgentScope视图容器
3. **可用视图**:
   - Agent Status (智能体状态)
   - Task Queue (任务队列)
   - Analysis Results (分析结果)
   - Augment Integration (Augment集成)

### 可用功能:

1. **代码分析**: 分析项目代码质量和结构
2. **质量检查**: 检查代码规范和最佳实践
3. **安全扫描**: 扫描安全漏洞和风险
4. **Augment集成**: 自然语言指令处理
5. **实时监控**: 任务状态和结果展示

## 🔧 **故障排除**

### 如果插件仍然无法工作:

1. **检查插件是否正确安装**:
   - 在扩展面板中搜索 "AgentScope"
   - 确认插件已启用

2. **检查VS Code开发者控制台**:
   - 按 `F12` 打开开发者工具
   - 查看Console标签页的错误信息

3. **重新安装插件**:
   - 卸载现有插件
   - 重新安装 .vsix 文件

4. **检查配置文件**:
   - 确认 `config/system_config.json` 存在
   - 确认 `.env` 文件包含正确的API密钥

## 📞 **技术支持**

如果问题仍然存在，请提供以下信息：

1. VS Code版本
2. 插件安装状态
3. 后端服务状态 (`curl http://localhost:8000/health`)
4. VS Code开发者控制台的错误信息
5. 插件配置设置

---

**💡 提示**: 即使WebSocket连接失败，HTTP API功能完全正常，您仍然可以使用所有核心功能！
