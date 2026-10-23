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
exports.TaskQueueProvider = void 0;
const vscode = __importStar(require("vscode"));
class TaskQueueProvider {
    constructor(agentSystemManager, eventBus) {
        this.agentSystemManager = agentSystemManager;
        this.eventBus = eventBus;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.tasks = [];
        this.setupEventListeners();
        this.loadInitialTasks();
    }
    setupEventListeners() {
        this.eventBus.on('taskAdded', (task) => {
            this.tasks.push(task);
            this.refresh();
        });
        this.eventBus.on('taskUpdated', (updatedTask) => {
            const index = this.tasks.findIndex(t => t.id === updatedTask.id);
            if (index !== -1) {
                this.tasks[index] = updatedTask;
                this.refresh();
            }
        });
        this.eventBus.on('taskRemoved', (taskId) => {
            this.tasks = this.tasks.filter(t => t.id !== taskId);
            this.refresh();
        });
        this.eventBus.on('systemStatusChanged', () => {
            this.loadInitialTasks();
        });
    }
    async loadInitialTasks() {
        try {
            // 从后端获取任务队列
            // const response = await this.agentSystemManager.sendRequest('/api/tasks/queue');
            const response = null; // 暂时禁用，避免编译错误
            if (response && Array.isArray(response.tasks)) {
                this.tasks = response.tasks.map((task) => ({
                    id: task.id,
                    title: task.title || task.description || 'Unknown Task',
                    status: task.status || 'pending',
                    agent: task.agent || 'Unknown Agent',
                    priority: task.priority || 5,
                    createdAt: new Date(task.created_at || Date.now()),
                    estimatedDuration: task.estimated_duration
                }));
                this.refresh();
            }
        }
        catch (error) {
            console.error('Failed to load task queue:', error);
            this.tasks = [];
            this.refresh();
        }
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        const item = new vscode.TreeItem(element.title, vscode.TreeItemCollapsibleState.None);
        // 设置图标
        switch (element.status) {
            case 'pending':
                item.iconPath = new vscode.ThemeIcon('clock');
                break;
            case 'running':
                item.iconPath = new vscode.ThemeIcon('sync~spin');
                break;
            case 'completed':
                item.iconPath = new vscode.ThemeIcon('check');
                break;
            case 'failed':
                item.iconPath = new vscode.ThemeIcon('error');
                break;
        }
        // 设置描述
        const duration = element.estimatedDuration ? ` (~${element.estimatedDuration}s)` : '';
        item.description = `${element.agent} | Priority: ${element.priority}${duration}`;
        // 设置工具提示
        item.tooltip = new vscode.MarkdownString([
            `**Task ID:** ${element.id}`,
            `**Status:** ${element.status}`,
            `**Agent:** ${element.agent}`,
            `**Priority:** ${element.priority}`,
            `**Created:** ${element.createdAt.toLocaleString()}`,
            element.estimatedDuration ? `**Estimated Duration:** ${element.estimatedDuration}s` : ''
        ].filter(Boolean).join('\n\n'));
        // 设置上下文值
        item.contextValue = `task-${element.status}`;
        // 设置命令
        if (element.status === 'completed') {
            item.command = {
                command: 'agentscope.showTaskResult',
                title: 'Show Result',
                arguments: [element.id]
            };
        }
        return item;
    }
    getChildren(element) {
        if (!element) {
            // 返回根级别的任务，按优先级和创建时间排序
            return Promise.resolve(this.tasks.sort((a, b) => {
                // 首先按状态排序：running > pending > completed > failed
                const statusOrder = { running: 0, pending: 1, completed: 2, failed: 3 };
                const statusDiff = statusOrder[a.status] - statusOrder[b.status];
                if (statusDiff !== 0)
                    return statusDiff;
                // 然后按优先级排序（数字越小优先级越高）
                const priorityDiff = a.priority - b.priority;
                if (priorityDiff !== 0)
                    return priorityDiff;
                // 最后按创建时间排序（新的在前）
                return b.createdAt.getTime() - a.createdAt.getTime();
            }));
        }
        return Promise.resolve([]);
    }
    getParent(element) {
        return null;
    }
    // 公共方法
    getTaskCount() {
        return this.tasks.length;
    }
    getPendingTaskCount() {
        return this.tasks.filter(t => t.status === 'pending').length;
    }
    getRunningTaskCount() {
        return this.tasks.filter(t => t.status === 'running').length;
    }
    getTaskById(id) {
        return this.tasks.find(t => t.id === id);
    }
    clearCompletedTasks() {
        this.tasks = this.tasks.filter(t => t.status !== 'completed');
        this.refresh();
    }
    clearAllTasks() {
        this.tasks = [];
        this.refresh();
    }
}
exports.TaskQueueProvider = TaskQueueProvider;
//# sourceMappingURL=taskQueueProvider.js.map