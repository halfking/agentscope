# AgentScope多智能体编程工作流 - 用户指南

## 快速开始

### 1. 系统要求

- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Python**: 3.9 或更高版本
- **Node.js**: 16.0 或更高版本
- **VS Code**: 1.70 或更高版本
- **内存**: 至少 4GB RAM
- **存储**: 至少 2GB 可用空间

### 2. 一键部署

```bash
# 克隆项目
git clone https://github.com/your-org/agentscope-multi-agent-workflow.git
cd agentscope-multi-agent-workflow

# 运行快速部署脚本
chmod +x scripts/quick_deploy.sh
./scripts/quick_deploy.sh
```

### 3. 手动安装

#### 3.1 安装Python依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 3.2 配置环境变量
```bash
export OPENAI_API_KEY="your_openai_api_key"
export AGENTSCOPE_LOG_LEVEL="INFO"
```

#### 3.3 启动后端服务
```bash
python -m agentscope_integration.main --host localhost --port 8000
```

#### 3.4 安装VS Code插件
```bash
cd vscode-extension
npm install
npm run compile
npm run package
code --install-extension agentscope-multi-agent-workflow-1.0.0.vsix
```

## 功能使用指南

### 1. VS Code插件使用

#### 1.1 插件激活
1. 打开VS Code
2. 按 `Ctrl+Shift+P` (Windows/Linux) 或 `Cmd+Shift+P` (macOS)
3. 输入 "AgentScope" 查看可用命令

#### 1.2 主要功能

##### 代码分析
- **快捷键**: `Ctrl+Shift+Q`
- **命令**: `AgentScope: Analyze Current File`
- **功能**: 分析当前文件的代码质量、安全问题和架构

##### 质量检查
- **快捷键**: `Ctrl+Shift+C`
- **命令**: `AgentScope: Quality Check`
- **功能**: 执行详细的代码质量检查

##### 安全扫描
- **快捷键**: `Ctrl+Shift+S`
- **命令**: `AgentScope: Security Scan`
- **功能**: 扫描安全漏洞和潜在风险

##### 项目分析
- **命令**: `AgentScope: Analyze Project`
- **功能**: 分析整个项目的代码质量和架构

#### 1.3 仪表板使用
- **快捷键**: `Ctrl+Shift+A`
- **功能**: 打开AgentScope仪表板
- **内容**: 
  - 智能体状态监控
  - 任务队列管理
  - 分析结果查看
  - 系统性能监控

### 2. 配置管理

#### 2.1 基本配置
在VS Code设置中配置以下选项：

```json
{
  "agentscope.backend.host": "localhost",
  "agentscope.backend.port": 8000,
  "agentscope.agents.codeManager.enabled": true,
  "agentscope.agents.complianceAuditor.enabled": true,
  "agentscope.llm.provider": "openai",
  "agentscope.llm.model": "gpt-4"
}
```

#### 2.2 项目特定配置
在项目根目录创建 `.vscode/settings.json`:

```json
{
  "agentscope.analysis.excludePatterns": [
    "node_modules/**",
    "**/*.min.js",
    "**/venv/**"
  ],
  "agentscope.quality.rules": {
    "python": {
      "maxLineLength": 100,
      "requireDocstrings": true
    }
  }
}
```

### 3. 代码审核标准配置

#### 3.1 使用预设标准
系统提供多种预设标准：
- **通用标准**: 适用于所有项目的基础规范
- **语言特定标准**: 针对Python、JavaScript、TypeScript等
- **行业标准**: 金融、医疗等行业的特殊要求

#### 3.2 自定义项目标准
1. 在VS Code中打开命令面板
2. 运行 `AgentScope: Configure Standards`
3. 选择基础模板
4. 自定义规则和严重程度
5. 保存项目特定配置

#### 3.3 标准配置示例
```json
{
  "project_name": "my_project",
  "language_overrides": {
    "python": {
      "standards": {
        "code_style": {
          "max_line_length": {
            "value": 100,
            "severity": "warning"
          }
        },
        "naming_conventions": {
          "functions": {
            "pattern": "^[a-z_][a-z0-9_]*$",
            "severity": "error"
          }
        }
      }
    }
  }
}
```

### 4. 自然语言交互 (Augment集成)

#### 4.1 支持的指令类型
- **代码分析**: "分析这个文件的代码质量"
- **安全检查**: "扫描安全漏洞"
- **重构建议**: "提供重构建议"
- **文档生成**: "生成API文档"

#### 4.2 使用示例
```
用户: "请分析user_manager.py文件中的安全问题，特别关注SQL注入和硬编码密钥"

系统: 正在分析文件安全问题...
- 发现SQL注入漏洞 (第23行)
- 发现硬编码API密钥 (第15行)
- 发现命令注入风险 (第45行)

建议修复方案:
1. 使用参数化查询防止SQL注入
2. 将API密钥移至环境变量
3. 验证和清理用户输入
```

### 5. 结果解读和处理

#### 5.1 分析结果结构
```json
{
  "quality_score": 85,
  "security_score": 70,
  "issues": [
    {
      "type": "complexity",
      "severity": "warning",
      "line": 45,
      "message": "函数复杂度过高",
      "suggestion": "考虑拆分函数"
    }
  ],
  "vulnerabilities": [
    {
      "type": "sql_injection",
      "severity": "critical",
      "line": 23,
      "description": "SQL注入漏洞",
      "fix_suggestion": "使用参数化查询"
    }
  ]
}
```

#### 5.2 严重程度说明
- **Critical (严重)**: 必须立即修复的安全漏洞
- **Error (错误)**: 需要修复的功能性问题
- **Warning (警告)**: 建议修复的质量问题
- **Info (信息)**: 可选的改进建议

#### 5.3 修复建议
系统会为每个问题提供：
- 问题描述和影响
- 具体的修复建议
- 代码示例（如适用）
- 相关文档链接

### 6. 高级功能

#### 6.1 批量分析
```bash
# 分析整个项目
python examples/project_analysis_workflow.py --project-path /path/to/project

# 分析特定目录
python examples/code_quality_check_example.py --directory src/
```

#### 6.2 自定义规则
创建自定义规则文件 `custom_rules.json`:
```json
{
  "custom_checks": {
    "no_print_statements": {
      "pattern": "print\\(",
      "severity": "warning",
      "message": "避免在生产代码中使用print语句"
    }
  }
}
```

#### 6.3 集成CI/CD
```yaml
# .github/workflows/code-quality.yml
name: Code Quality Check
on: [push, pull_request]
jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run quality check
        run: python scripts/run_comprehensive_tests.py
```

## 故障排除

### 1. 常见问题

#### 1.1 后端服务无法启动
**问题**: 端口8000被占用
**解决**: 
```bash
# 查找占用端口的进程
lsof -i :8000
# 终止进程
kill -9 <PID>
```

#### 1.2 VS Code插件无法连接后端
**问题**: 连接超时
**解决**:
1. 检查后端服务是否运行: `curl http://localhost:8000/health`
2. 检查防火墙设置
3. 验证VS Code配置中的主机和端口

#### 1.3 API密钥错误
**问题**: OpenAI API调用失败
**解决**:
1. 验证API密钥是否正确
2. 检查API配额和余额
3. 确认网络连接正常

### 2. 日志查看
```bash
# 查看后端日志
tail -f logs/backend.log

# 查看VS Code插件日志
# 在VS Code中: View -> Output -> AgentScope
```

### 3. 重置配置
```bash
# 重置为默认配置
rm config/system_config.json
cp config/system_config.json.example config/system_config.json
```

## 最佳实践

### 1. 代码质量
- 定期运行代码分析
- 设置合理的质量阈值
- 及时修复高优先级问题
- 建立代码审查流程

### 2. 安全实践
- 启用所有安全扫描
- 定期更新依赖包
- 遵循安全编码规范
- 实施安全培训

### 3. 团队协作
- 统一代码标准配置
- 共享自定义规则
- 建立问题跟踪流程
- 定期回顾和改进

### 4. 性能优化
- 合理配置分析范围
- 使用排除模式过滤无关文件
- 定期清理历史数据
- 监控系统资源使用

## 支持和反馈

### 获取帮助
- **文档**: [在线文档](https://docs.agentscope.com)
- **社区**: [GitHub Discussions](https://github.com/your-org/agentscope/discussions)
- **问题报告**: [GitHub Issues](https://github.com/your-org/agentscope/issues)

### 贡献代码
欢迎提交Pull Request来改进系统功能。请参考[贡献指南](CONTRIBUTING.md)了解详细信息。

### 许可证
本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。
