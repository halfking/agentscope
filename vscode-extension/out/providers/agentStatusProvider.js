"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AgentStatusProvider = exports.AgentMetricItem = exports.AgentStatusItem = void 0;
const vscode = __importStar(require("vscode"));
class AgentStatusItem extends vscode.TreeItem {
    constructor(agentStatus, collapsibleState) {
        super(agentStatus.role, collapsibleState);
        this.agentStatus = agentStatus;
        this.collapsibleState = collapsibleState;
        this.id = agentStatus.agentId;
        this.tooltip = this.getTooltip();
        this.description = this.getDescription();
        this.iconPath = this.getIcon();
        this.contextValue = 'agentStatus';
        // 设置命令
        this.command = {
            command: 'agentscope.showAgentDetails',
            title: 'Show Agent Details',
            arguments: [agentStatus.agentId]
        };
    }
    getTooltip() {
        const metrics = this.agentStatus.performanceMetrics;
        const successRate = metrics.success_rate ? (metrics.success_rate * 100).toFixed(1) : 'N/A';
        const avgTime = metrics.avg_execution_time ? metrics.avg_execution_time.toFixed(2) : 'N/A';
        return `Agent: ${this.agentStatus.role}
Status: ${this.agentStatus.status}
Current Task: ${this.agentStatus.currentTask || 'None'}
Success Rate: ${successRate}%
Avg Execution Time: ${avgTime}s
Last Update: ${new Date(this.agentStatus.lastUpdate).toLocaleString()}`;
    }
    getDescription() {
        if (this.agentStatus.currentTask) {
            return `Running: ${this.agentStatus.currentTask.substring(0, 20)}...`;
        }
        return this.agentStatus.status;
    }
    getIcon() {
        switch (this.agentStatus.status) {
            case 'idle':
                return new vscode.ThemeIcon('circle-outline', new vscode.ThemeColor('charts.green'));
            case 'busy':
                return new vscode.ThemeIcon('sync~spin', new vscode.ThemeColor('charts.yellow'));
            case 'error':
                return new vscode.ThemeIcon('error', new vscode.ThemeColor('charts.red'));
            default:
                return new vscode.ThemeIcon('circle-outline', new vscode.ThemeColor('charts.gray'));
        }
    }
}
exports.AgentStatusItem = AgentStatusItem;
class AgentMetricItem extends vscode.TreeItem {
    constructor(label, value, description) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.label = label;
        this.value = value;
        this.description = description;
        this.description = value;
        this.tooltip = description || `${label}: ${value}`;
        this.contextValue = 'agentMetric';
        this.iconPath = new vscode.ThemeIcon('graph');
    }
}
exports.AgentMetricItem = AgentMetricItem;
class AgentStatusProvider {
    constructor(agentSystemManager, eventBus) {
        this.agentSystemManager = agentSystemManager;
        this.eventBus = eventBus;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.agents = [];
        this.setupEventListeners();
        this.startAutoRefresh();
    }
    setupEventListeners() {
        // 监听智能体状态更新事件
        this.eventBus.on('agentStatusUpdated', (agentStatus) => {
            this.updateAgentStatus(agentStatus);
        });
        // 监听系统状态变化
        this.eventBus.on('systemStatusChanged', (status) => {
            if (status === 'active') {
                this.refresh();
            }
            else {
                this.agents = [];
                this._onDidChangeTreeData.fire();
            }
        });
        // 监听任务状态变化
        this.eventBus.on('taskStarted', (data) => {
            this.refresh();
        });
        this.eventBus.on('taskCompleted', (data) => {
            this.refresh();
        });
    }
    startAutoRefresh() {
        // 每30秒自动刷新一次
        this.refreshInterval = setInterval(() => {
            if (this.agentSystemManager.isSystemConnected()) {
                this.refresh();
            }
        }, 30000);
    }
    updateAgentStatus(agentStatus) {
        const index = this.agents.findIndex(agent => agent.agentId === agentStatus.agentId);
        if (index !== -1) {
            this.agents[index] = agentStatus;
        }
        else {
            this.agents.push(agentStatus);
        }
        this._onDidChangeTreeData.fire();
    }
    async refresh() {
        try {
            if (this.agentSystemManager.isSystemConnected()) {
                this.agents = this.agentSystemManager.getCachedAgents();
                // 如果缓存为空，尝试从服务器获取
                if (this.agents.length === 0) {
                    await this.agentSystemManager.getAgents();
                    this.agents = this.agentSystemManager.getCachedAgents();
                }
            }
            else {
                this.agents = [];
            }
        }
        catch (error) {
            console.error('Failed to refresh agent status:', error);
            this.agents = [];
        }
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            // 根级别：显示所有智能体
            return Promise.resolve(this.getAgentItems());
        }
        else if (element instanceof AgentStatusItem) {
            // 智能体级别：显示性能指标
            return Promise.resolve(this.getMetricItems(element.agentStatus));
        }
        else {
            // 指标级别：没有子项
            return Promise.resolve([]);
        }
    }
    getAgentItems() {
        if (!this.agentSystemManager.isSystemConnected()) {
            return [];
        }
        return this.agents.map(agent => new AgentStatusItem(agent, vscode.TreeItemCollapsibleState.Collapsed));
    }
    getMetricItems(agentStatus) {
        const items = [];
        const metrics = agentStatus.performanceMetrics;
        // 基本信息
        items.push(new AgentMetricItem('Agent ID', agentStatus.agentId, 'Unique identifier for this agent'));
        items.push(new AgentMetricItem('Status', agentStatus.status, 'Current operational status'));
        if (agentStatus.currentTask) {
            items.push(new AgentMetricItem('Current Task', agentStatus.currentTask, 'Currently executing task'));
        }
        items.push(new AgentMetricItem('Last Update', new Date(agentStatus.lastUpdate).toLocaleString(), 'Last status update time'));
        // 性能指标
        if (metrics.success_rate !== undefined) {
            items.push(new AgentMetricItem('Success Rate', `${(metrics.success_rate * 100).toFixed(1)}%`, 'Percentage of successfully completed tasks'));
        }
        if (metrics.avg_execution_time !== undefined) {
            items.push(new AgentMetricItem('Avg Execution Time', `${metrics.avg_execution_time.toFixed(2)}s`, 'Average time to complete tasks'));
        }
        // 任务统计
        Object.entries(metrics).forEach(([key, value]) => {
            if (key.startsWith('tasks_') && typeof value === 'number') {
                const taskType = key.replace('tasks_', '').replace('_', ' ');
                items.push(new AgentMetricItem(`${taskType} Tasks`, value.toString(), `Number of ${taskType} tasks completed`));
            }
        });
        return items;
    }
    getAgentCount() {
        return this.agents.length;
    }
    getActiveAgentCount() {
        return this.agents.filter(agent => agent.status === 'busy').length;
    }
    getIdleAgentCount() {
        return this.agents.filter(agent => agent.status === 'idle').length;
    }
    getErrorAgentCount() {
        return this.agents.filter(agent => agent.status === 'error').length;
    }
    getAgentByRole(role) {
        return this.agents.find(agent => agent.role === role);
    }
    getAgentById(agentId) {
        return this.agents.find(agent => agent.agentId === agentId);
    }
    getSystemHealth() {
        if (this.agents.length === 0) {
            return {
                status: 'error',
                message: 'No agents available',
                details: { totalAgents: 0 }
            };
        }
        const errorCount = this.getErrorAgentCount();
        const totalCount = this.getAgentCount();
        const errorRate = errorCount / totalCount;
        if (errorRate > 0.5) {
            return {
                status: 'error',
                message: `${errorCount}/${totalCount} agents have errors`,
                details: {
                    totalAgents: totalCount,
                    errorAgents: errorCount,
                    errorRate: errorRate
                }
            };
        }
        else if (errorRate > 0) {
            return {
                status: 'warning',
                message: `${errorCount}/${totalCount} agents have errors`,
                details: {
                    totalAgents: totalCount,
                    errorAgents: errorCount,
                    errorRate: errorRate
                }
            };
        }
        else {
            return {
                status: 'healthy',
                message: `All ${totalCount} agents are operational`,
                details: {
                    totalAgents: totalCount,
                    activeAgents: this.getActiveAgentCount(),
                    idleAgents: this.getIdleAgentCount()
                }
            };
        }
    }
    dispose() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = undefined;
        }
        this._onDidChangeTreeData.dispose();
    }
}
exports.AgentStatusProvider = AgentStatusProvider;
//# sourceMappingURL=agentStatusProvider.js.map