import * as vscode from 'vscode';
import { AgentSystemManager } from '../core/agentSystemManager';
import { EventBus } from '../core/eventBus';

export interface TaskQueueItem {
    id: string;
    title: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    agent: string;
    priority: number;
    createdAt: Date;
    estimatedDuration?: number;
}

export class TaskQueueProvider implements vscode.TreeDataProvider<TaskQueueItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<TaskQueueItem | undefined | null | void> = new vscode.EventEmitter<TaskQueueItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<TaskQueueItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private tasks: TaskQueueItem[] = [];

    constructor(
        private agentSystemManager: AgentSystemManager,
        private eventBus: EventBus
    ) {
        this.setupEventListeners();
        this.loadInitialTasks();
    }

    private setupEventListeners(): void {
        this.eventBus.on('taskAdded', (task: TaskQueueItem) => {
            this.tasks.push(task);
            this.refresh();
        });

        this.eventBus.on('taskUpdated', (updatedTask: TaskQueueItem) => {
            const index = this.tasks.findIndex(t => t.id === updatedTask.id);
            if (index !== -1) {
                this.tasks[index] = updatedTask;
                this.refresh();
            }
        });

        this.eventBus.on('taskRemoved', (taskId: string) => {
            this.tasks = this.tasks.filter(t => t.id !== taskId);
            this.refresh();
        });

        this.eventBus.on('systemStatusChanged', () => {
            this.loadInitialTasks();
        });
    }

    private async loadInitialTasks(): Promise<void> {
        try {
            // 从后端获取任务队列
            // const response = await this.agentSystemManager.sendRequest('/api/tasks/queue');
            const response = null; // 暂时禁用，避免编译错误
            if (response && Array.isArray(response.tasks)) {
                this.tasks = response.tasks.map((task: any) => ({
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
        } catch (error) {
            console.error('Failed to load task queue:', error);
            this.tasks = [];
            this.refresh();
        }
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: TaskQueueItem): vscode.TreeItem {
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

    getChildren(element?: TaskQueueItem): Thenable<TaskQueueItem[]> {
        if (!element) {
            // 返回根级别的任务，按优先级和创建时间排序
            return Promise.resolve(
                this.tasks.sort((a, b) => {
                    // 首先按状态排序：running > pending > completed > failed
                    const statusOrder = { running: 0, pending: 1, completed: 2, failed: 3 };
                    const statusDiff = statusOrder[a.status] - statusOrder[b.status];
                    if (statusDiff !== 0) return statusDiff;
                    
                    // 然后按优先级排序（数字越小优先级越高）
                    const priorityDiff = a.priority - b.priority;
                    if (priorityDiff !== 0) return priorityDiff;
                    
                    // 最后按创建时间排序（新的在前）
                    return b.createdAt.getTime() - a.createdAt.getTime();
                })
            );
        }
        
        return Promise.resolve([]);
    }

    getParent(element: TaskQueueItem): vscode.ProviderResult<TaskQueueItem> {
        return null;
    }

    // 公共方法
    public getTaskCount(): number {
        return this.tasks.length;
    }

    public getPendingTaskCount(): number {
        return this.tasks.filter(t => t.status === 'pending').length;
    }

    public getRunningTaskCount(): number {
        return this.tasks.filter(t => t.status === 'running').length;
    }

    public getTaskById(id: string): TaskQueueItem | undefined {
        return this.tasks.find(t => t.id === id);
    }

    public clearCompletedTasks(): void {
        this.tasks = this.tasks.filter(t => t.status !== 'completed');
        this.refresh();
    }

    public clearAllTasks(): void {
        this.tasks = [];
        this.refresh();
    }
}
