# AgentScope多智能体编程工作流部署指南

## 系统要求

### 硬件要求
- **CPU**: 4核心以上，推荐8核心
- **内存**: 8GB以上，推荐16GB
- **存储**: 20GB可用空间
- **网络**: 稳定的互联网连接（用于LLM API调用）

### 软件要求
- **Python**: 3.9+
- **Node.js**: 16+ (用于MCP服务器)
- **VS Code**: 1.70+ (用于插件)
- **Git**: 2.0+

## 安装步骤

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd agentscope-multi-agent-workflow

# 创建Python虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖（用于MCP服务器）
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-brave-search
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# LLM API密钥
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
SILICONFLOW_API_KEY=your_siliconflow_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key

# 可选：搜索API密钥
BRAVE_API_KEY=your_brave_api_key

# 系统配置
AGENTSCOPE_DEBUG=false
AGENTSCOPE_LOG_LEVEL=INFO
AGENTSCOPE_BACKEND_HOST=localhost
AGENTSCOPE_BACKEND_PORT=8000
AGENTSCOPE_DEFAULT_LLM=openai
```

### 3. 初始化配置

```bash
# 创建工作目录
mkdir -p workspace logs cache

# 生成默认配置文件
python -m agentscope_integration.config.generate_config

# 编辑配置文件（可选）
vim config/system_config.json
```

### 4. 启动后端服务

```bash
# 开发模式启动
python -m agentscope_integration.main

# 或使用uvicorn直接启动
uvicorn agentscope_integration.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 安装VS Code插件

```bash
# 进入插件目录
cd vscode-extension

# 安装依赖
npm install

# 编译插件
npm run compile

# 打包插件
npm run package

# 安装到VS Code
code --install-extension agentscope-multi-agent-workflow-1.0.0.vsix
```

## 配置说明

### 系统配置文件

主配置文件位于 `config/system_config.json`：

```json
{
  "project_name": "AgentScope Multi-Agent Workflow",
  "version": "1.0.0",
  "debug": false,
  "log_level": "INFO",
  "backend_host": "localhost",
  "backend_port": 8000,
  "websocket_port": 8001,
  "llm_providers": {
    "openai": {
      "name": "openai",
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4",
      "enabled": true
    }
  },
  "agents": {
    "code_manager": {
      "agent_id": "code_manager",
      "role": "code_manager",
      "name": "CodeManager",
      "enabled": true,
      "llm_provider": "openai"
    }
  }
}
```

### MCP服务器配置

MCP配置文件位于 `workspace/mcp_config.json`：

```json
{
  "mcp_servers": {
    "filesystem": {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
      "enabled": true,
      "auto_start": true
    },
    "git": {
      "name": "git", 
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "enabled": true,
      "auto_start": true
    }
  }
}
```

### VS Code插件配置

在VS Code设置中配置：

```json
{
  "agentscope.backend.host": "localhost",
  "agentscope.backend.port": 8000,
  "agentscope.agents.codeManager.enabled": true,
  "agentscope.agents.complianceAuditor.enabled": true,
  "agentscope.llm.provider": "openai",
  "agentscope.analysis.autoRun": false,
  "agentscope.dashboard.autoOpen": true
}
```

## 验证安装

### 1. 检查后端服务

```bash
# 检查健康状态
curl http://localhost:8000/health

# 检查API文档
open http://localhost:8000/docs
```

### 2. 检查智能体状态

```bash
# 获取智能体列表
curl http://localhost:8000/api/agents

# 提交测试任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "code_analysis",
    "title": "Test Analysis",
    "description": "Test task",
    "parameters": {"file_path": "./test.py"},
    "priority": 5
  }'
```

### 3. 检查VS Code插件

1. 打开VS Code
2. 按 `Ctrl+Shift+P` 打开命令面板
3. 输入 "AgentScope" 查看可用命令
4. 运行 "AgentScope: Show Agent Dashboard"

## 故障排除

### 常见问题

#### 1. 后端服务启动失败

**问题**: `ModuleNotFoundError: No module named 'agentscope'`

**解决方案**:
```bash
pip install agentscope
# 或从源码安装
pip install -e .
```

#### 2. LLM API调用失败

**问题**: `Authentication failed`

**解决方案**:
- 检查API密钥是否正确设置
- 验证API密钥是否有效
- 检查网络连接

#### 3. MCP服务器启动失败

**问题**: `Command not found: npx`

**解决方案**:
```bash
# 安装Node.js和npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证安装
node --version
npm --version
```

#### 4. VS Code插件无法连接

**问题**: `Failed to connect to AgentScope backend`

**解决方案**:
- 确保后端服务正在运行
- 检查端口配置是否正确
- 检查防火墙设置

### 日志查看

```bash
# 查看系统日志
tail -f logs/agentscope_system.log

# 查看特定智能体日志
tail -f logs/agent_code_manager.log

# 查看MCP服务器日志
tail -f logs/mcp_*.log
```

### 性能监控

```bash
# 检查系统资源使用
htop

# 检查端口占用
netstat -tulpn | grep :8000

# 检查进程状态
ps aux | grep agentscope
```

## 生产部署

### 使用Docker部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 复制项目文件
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 安装MCP服务器
RUN npm install -g @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-git

# 创建工作目录
RUN mkdir -p workspace logs cache

EXPOSE 8000

CMD ["python", "-m", "agentscope_integration.main"]
```

```bash
# 构建镜像
docker build -t agentscope-workflow .

# 运行容器
docker run -d \
  --name agentscope-workflow \
  -p 8000:8000 \
  -v $(pwd)/workspace:/app/workspace \
  -v $(pwd)/logs:/app/logs \
  -e OPENAI_API_KEY=your_key \
  agentscope-workflow
```

### 使用docker-compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  agentscope-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./workspace:/app/workspace
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - agentscope-backend
    restart: unless-stopped
```

### 系统服务配置

```ini
# /etc/systemd/system/agentscope-workflow.service
[Unit]
Description=AgentScope Multi-Agent Workflow
After=network.target

[Service]
Type=simple
User=agentscope
WorkingDirectory=/opt/agentscope-workflow
Environment=PATH=/opt/agentscope-workflow/venv/bin
ExecStart=/opt/agentscope-workflow/venv/bin/python -m agentscope_integration.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable agentscope-workflow
sudo systemctl start agentscope-workflow
sudo systemctl status agentscope-workflow
```

## 安全配置

### 1. API访问控制

```python
# 添加API密钥认证
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Security(security)):
    if token.credentials != "your-api-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token
```

### 2. HTTPS配置

```bash
# 生成SSL证书
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# 配置uvicorn使用HTTPS
uvicorn agentscope_integration.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --ssl-keyfile key.pem \
  --ssl-certfile cert.pem
```

### 3. 防火墙配置

```bash
# 只允许必要端口
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

## 维护和更新

### 定期维护任务

```bash
# 清理日志文件
find logs/ -name "*.log" -mtime +30 -delete

# 清理缓存
rm -rf cache/*

# 更新依赖
pip install --upgrade -r requirements.txt
npm update -g
```

### 备份策略

```bash
# 备份配置和数据
tar -czf backup-$(date +%Y%m%d).tar.gz \
  config/ \
  workspace/ \
  logs/

# 上传到云存储
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

### 监控和告警

```bash
# 设置健康检查
*/5 * * * * curl -f http://localhost:8000/health || echo "Service down" | mail -s "AgentScope Alert" admin@example.com
```
