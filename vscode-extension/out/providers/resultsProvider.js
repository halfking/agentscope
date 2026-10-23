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
exports.ResultsProvider = void 0;
const vscode = __importStar(require("vscode"));
class ResultsProvider {
    constructor(agentSystemManager, eventBus) {
        this.agentSystemManager = agentSystemManager;
        this.eventBus = eventBus;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.results = [];
        this.maxResults = 100; // 最大保存结果数量
        this.setupEventListeners();
        this.loadInitialResults();
    }
    setupEventListeners() {
        this.eventBus.on('analysisCompleted', (result) => {
            this.addResult(result);
        });
        this.eventBus.on('augmentTaskCompleted', (taskData) => {
            const result = {
                id: taskData.id || Date.now().toString(),
                title: taskData.title || 'Augment Task',
                type: 'augment-task',
                status: taskData.success ? 'success' : 'error',
                agent: 'Augment Integration',
                timestamp: new Date(),
                summary: taskData.summary || 'Augment task completed',
                details: taskData.details,
                filePath: taskData.filePath,
                recommendations: taskData.recommendations
            };
            this.addResult(result);
        });
        this.eventBus.on('systemStatusChanged', () => {
            this.loadInitialResults();
        });
    }
    async loadInitialResults() {
        try {
            // 从后端获取分析结果
            // const response = await this.agentSystemManager.sendRequest('/api/results');
            const response = null; // 暂时禁用，避免编译错误
            if (response && Array.isArray(response.results)) {
                this.results = response.results.map((result) => ({
                    id: result.id,
                    title: result.title || 'Analysis Result',
                    type: result.type || 'code-analysis',
                    status: result.status || 'info',
                    agent: result.agent || 'Unknown Agent',
                    timestamp: new Date(result.timestamp || Date.now()),
                    summary: result.summary || 'No summary available',
                    details: result.details,
                    filePath: result.file_path,
                    lineNumber: result.line_number,
                    severity: result.severity,
                    recommendations: result.recommendations
                }));
                this.refresh();
            }
        }
        catch (error) {
            console.error('Failed to load analysis results:', error);
            this.results = [];
            this.refresh();
        }
    }
    addResult(result) {
        this.results.unshift(result); // 新结果添加到开头
        // 限制结果数量
        if (this.results.length > this.maxResults) {
            this.results = this.results.slice(0, this.maxResults);
        }
        this.refresh();
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        const item = new vscode.TreeItem(element.title, vscode.TreeItemCollapsibleState.None);
        // 设置图标
        switch (element.status) {
            case 'success':
                item.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('charts.green'));
                break;
            case 'warning':
                item.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('charts.yellow'));
                break;
            case 'error':
                item.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('charts.red'));
                break;
            case 'info':
                item.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('charts.blue'));
                break;
        }
        // 设置描述
        const timeAgo = this.getTimeAgo(element.timestamp);
        item.description = `${element.agent} • ${timeAgo}`;
        // 设置标签
        if (element.severity) {
            item.label = `${element.title} [${element.severity.toUpperCase()}]`;
        }
        // 设置工具提示
        const tooltipContent = [
            `**${element.title}**`,
            `**Type:** ${element.type}`,
            `**Status:** ${element.status}`,
            `**Agent:** ${element.agent}`,
            `**Time:** ${element.timestamp.toLocaleString()}`,
            element.severity ? `**Severity:** ${element.severity}` : '',
            element.filePath ? `**File:** ${element.filePath}` : '',
            element.lineNumber ? `**Line:** ${element.lineNumber}` : '',
            '',
            `**Summary:** ${element.summary}`
        ].filter(Boolean);
        if (element.recommendations && element.recommendations.length > 0) {
            tooltipContent.push('', '**Recommendations:**');
            element.recommendations.forEach(rec => {
                tooltipContent.push(`• ${rec}`);
            });
        }
        item.tooltip = new vscode.MarkdownString(tooltipContent.join('\n\n'));
        // 设置上下文值
        item.contextValue = `result-${element.type}-${element.status}`;
        // 设置命令
        item.command = {
            command: 'agentscope.showResultDetails',
            title: 'Show Details',
            arguments: [element]
        };
        return item;
    }
    getChildren(element) {
        if (!element) {
            // 返回根级别的结果，按时间排序（新的在前）
            return Promise.resolve(this.results.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()));
        }
        return Promise.resolve([]);
    }
    getParent(element) {
        return null;
    }
    // 辅助方法
    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        if (diffMins < 1)
            return 'just now';
        if (diffMins < 60)
            return `${diffMins}m ago`;
        if (diffHours < 24)
            return `${diffHours}h ago`;
        if (diffDays < 7)
            return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }
    // 公共方法
    getResultCount() {
        return this.results.length;
    }
    getResultsByType(type) {
        return this.results.filter(r => r.type === type);
    }
    getResultsByStatus(status) {
        return this.results.filter(r => r.status === status);
    }
    getResultsBySeverity(severity) {
        return this.results.filter(r => r.severity === severity);
    }
    clearResults() {
        this.results = [];
        this.refresh();
    }
    clearResultsByType(type) {
        this.results = this.results.filter(r => r.type !== type);
        this.refresh();
    }
    exportResults() {
        return JSON.stringify(this.results, null, 2);
    }
    getResultById(id) {
        return this.results.find(r => r.id === id);
    }
}
exports.ResultsProvider = ResultsProvider;
//# sourceMappingURL=resultsProvider.js.map