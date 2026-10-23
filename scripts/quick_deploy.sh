#!/bin/bash

# AgentScope多智能体编程工作流 - 快速部署脚本
# 自动化部署整个系统，包括后端服务、VS Code插件和测试验证

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# 检查Python版本
check_python_version() {
    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    local major_version=$(echo $python_version | cut -d'.' -f1)
    local minor_version=$(echo $python_version | cut -d'.' -f2)
    
    if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 9 ]); then
        log_error "Python 3.9+ is required. Current version: $python_version"
        exit 1
    fi
    
    log_success "Python version check passed: $python_version"
}

# 检查Node.js版本
check_node_version() {
    local node_version=$(node --version 2>&1 | cut -d'v' -f2)
    local major_version=$(echo $node_version | cut -d'.' -f1)
    
    if [ "$major_version" -lt 16 ]; then
        log_error "Node.js 16+ is required. Current version: $node_version"
        exit 1
    fi
    
    log_success "Node.js version check passed: $node_version"
}

# 系统要求检查
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # 检查必需的命令
    check_command "python3"
    check_command "pip3"
    check_command "node"
    check_command "npm"
    check_command "git"
    check_command "code"
    
    # 检查版本
    check_python_version
    check_node_version
    
    log_success "System requirements check completed"
}

# 设置环境变量
setup_environment() {
    log_info "Setting up environment variables..."
    
    # 检查必需的环境变量
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OPENAI_API_KEY not set. Please set it before running the system."
        read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
        if [ ! -z "$api_key" ]; then
            export OPENAI_API_KEY="$api_key"
            echo "export OPENAI_API_KEY=\"$api_key\"" >> ~/.bashrc
        fi
    fi
    
    # 设置其他环境变量
    export AGENTSCOPE_LOG_LEVEL="INFO"
    export AGENTSCOPE_CONFIG_PATH="config/system_config.json"
    export PYTHONPATH="$PWD:$PYTHONPATH"
    
    log_success "Environment variables configured"
}

# 安装Python依赖
install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        log_warning "requirements.txt not found, installing basic dependencies..."
        pip install agentscope fastapi uvicorn websockets requests aiofiles
    fi
    
    # 安装开发依赖
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    else
        pip install pytest pytest-asyncio black flake8 mypy
    fi
    
    log_success "Python dependencies installed"
}

# 安装Node.js依赖
install_node_dependencies() {
    log_info "Installing Node.js dependencies..."
    
    if [ -d "vscode-extension" ]; then
        cd vscode-extension
        
        # 安装依赖
        npm install
        
        # 安装全局工具
        npm install -g @vscode/vsce
        
        cd ..
        log_success "Node.js dependencies installed"
    else
        log_warning "vscode-extension directory not found, skipping Node.js dependencies"
    fi
}

# 创建配置文件
create_config_files() {
    log_info "Creating configuration files..."
    
    # 创建配置目录
    mkdir -p config
    mkdir -p standards
    mkdir -p logs
    mkdir -p results
    mkdir -p test_reports
    
    # 复制示例配置文件（如果不存在）
    if [ ! -f "config/system_config.json" ]; then
        if [ -f "config/system_config.json.example" ]; then
            cp config/system_config.json.example config/system_config.json
        else
            log_warning "system_config.json not found, creating minimal config..."
            cat > config/system_config.json << EOF
{
  "backend_host": "localhost",
  "backend_port": 8000,
  "llm_providers": {
    "openai": {
      "name": "openai",
      "api_key": "\${OPENAI_API_KEY}",
      "model": "gpt-4",
      "enabled": true
    }
  },
  "agents": {
    "code_manager": {
      "enabled": true,
      "llm_provider": "openai"
    },
    "compliance_auditor": {
      "enabled": true,
      "llm_provider": "openai"
    }
  }
}
EOF
        fi
    fi
    
    # 创建MCP配置
    if [ ! -f "config/mcp_config.json" ]; then
        if [ -f "config/mcp_config.json.example" ]; then
            cp config/mcp_config.json.example config/mcp_config.json
        fi
    fi
    
    log_success "Configuration files created"
}

# 编译VS Code插件
build_vscode_extension() {
    log_info "Building VS Code extension..."
    
    if [ -d "vscode-extension" ]; then
        cd vscode-extension
        
        # 编译TypeScript
        npm run compile
        
        # 打包插件
        npm run package
        
        cd ..
        log_success "VS Code extension built successfully"
    else
        log_warning "vscode-extension directory not found, skipping extension build"
    fi
}

# 安装VS Code插件
install_vscode_extension() {
    log_info "Installing VS Code extension..."
    
    if [ -f "vscode-extension/agentscope-multi-agent-workflow-1.0.0.vsix" ]; then
        code --install-extension vscode-extension/agentscope-multi-agent-workflow-1.0.0.vsix --force
        log_success "VS Code extension installed"
    else
        log_warning "VS Code extension package not found, skipping installation"
    fi
}

# 启动后端服务
start_backend_service() {
    log_info "Starting backend service..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查端口是否被占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        log_warning "Port 8000 is already in use. Stopping existing service..."
        pkill -f "agentscope_integration.main" || true
        sleep 2
    fi
    
    # 启动服务
    nohup python -m agentscope_integration.main --host localhost --port 8000 > logs/backend.log 2>&1 &
    
    # 等待服务启动
    log_info "Waiting for backend service to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Backend service started successfully"
            return 0
        fi
        sleep 2
    done
    
    log_error "Backend service failed to start"
    return 1
}

# 运行基本测试
run_basic_tests() {
    log_info "Running basic tests..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 测试后端健康检查
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    # 测试智能体状态
    if curl -s http://localhost:8000/agents | grep -q "agent_id"; then
        log_success "Agents endpoint test passed"
    else
        log_warning "Agents endpoint test failed or no agents available"
    fi
    
    # 运行单元测试（如果存在）
    if [ -f "tests/test_agents.py" ]; then
        log_info "Running unit tests..."
        python -m pytest tests/test_agents.py -v --tb=short || log_warning "Some unit tests failed"
    fi
    
    log_success "Basic tests completed"
}

# 显示部署状态
show_deployment_status() {
    echo ""
    echo "=================================="
    echo "   DEPLOYMENT STATUS SUMMARY"
    echo "=================================="
    
    # 检查后端服务
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "Backend Service: ${GREEN}✓ Running${NC} (http://localhost:8000)"
    else
        echo -e "Backend Service: ${RED}✗ Not Running${NC}"
    fi
    
    # 检查VS Code插件
    if code --list-extensions | grep -q "agentscope"; then
        echo -e "VS Code Extension: ${GREEN}✓ Installed${NC}"
    else
        echo -e "VS Code Extension: ${YELLOW}? Not Found${NC}"
    fi
    
    # 显示配置信息
    echo ""
    echo "Configuration:"
    echo "  - Config Path: config/system_config.json"
    echo "  - Log Path: logs/backend.log"
    echo "  - Results Path: results/"
    
    echo ""
    echo "Next Steps:"
    echo "  1. Open VS Code in your project directory"
    echo "  2. Use Ctrl+Shift+P and search for 'AgentScope'"
    echo "  3. Configure your API keys in VS Code settings"
    echo "  4. Start analyzing your code!"
    
    echo ""
    echo "Useful Commands:"
    echo "  - View logs: tail -f logs/backend.log"
    echo "  - Stop service: pkill -f agentscope_integration.main"
    echo "  - Run tests: python scripts/run_comprehensive_tests.py"
    
    echo "=================================="
}

# 清理函数
cleanup() {
    log_info "Cleaning up..."
    # 这里可以添加清理逻辑
}

# 主函数
main() {
    echo "=================================="
    echo "  AgentScope Multi-Agent Workflow"
    echo "     Quick Deployment Script"
    echo "=================================="
    echo ""
    
    # 设置错误处理
    trap cleanup EXIT
    
    # 检查参数
    SKIP_TESTS=false
    SKIP_EXTENSION=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-extension)
                SKIP_EXTENSION=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-tests      Skip running tests"
                echo "  --skip-extension  Skip VS Code extension installation"
                echo "  --help, -h        Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行部署步骤
    check_system_requirements
    setup_environment
    install_python_dependencies
    install_node_dependencies
    create_config_files
    
    if [ "$SKIP_EXTENSION" = false ]; then
        build_vscode_extension
        install_vscode_extension
    fi
    
    start_backend_service
    
    if [ "$SKIP_TESTS" = false ]; then
        run_basic_tests
    fi
    
    show_deployment_status
    
    log_success "Deployment completed successfully!"
}

# 运行主函数
main "$@"
