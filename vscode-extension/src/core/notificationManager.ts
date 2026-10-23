import * as vscode from 'vscode';

export type NotificationLevel = 'error' | 'warning' | 'info' | 'debug';

export interface NotificationOptions {
    modal?: boolean;
    detail?: string;
    actions?: string[];
    timeout?: number;
}

export interface NotificationHistory {
    id: string;
    level: NotificationLevel;
    message: string;
    timestamp: Date;
    detail?: string;
    actions?: string[];
    dismissed: boolean;
}

export class NotificationManager {
    private static readonly MAX_HISTORY_SIZE = 100;
    private currentLevel: NotificationLevel = 'info';
    private history: NotificationHistory[] = [];
    private notificationCounter = 0;
    private outputChannel: vscode.OutputChannel;

    constructor() {
        this.outputChannel = vscode.window.createOutputChannel('AgentScope');
    }

    public setLevel(level: NotificationLevel): void {
        this.currentLevel = level;
    }

    public getLevel(): NotificationLevel {
        return this.currentLevel;
    }

    private shouldShow(level: NotificationLevel): boolean {
        const levels: NotificationLevel[] = ['debug', 'info', 'warning', 'error'];
        const currentIndex = levels.indexOf(this.currentLevel);
        const messageIndex = levels.indexOf(level);
        return messageIndex >= currentIndex;
    }

    private addToHistory(
        level: NotificationLevel,
        message: string,
        detail?: string,
        actions?: string[]
    ): string {
        const id = `notification_${++this.notificationCounter}`;
        const notification: NotificationHistory = {
            id,
            level,
            message,
            timestamp: new Date(),
            detail,
            actions,
            dismissed: false
        };

        this.history.unshift(notification);

        // 限制历史记录大小
        if (this.history.length > NotificationManager.MAX_HISTORY_SIZE) {
            this.history = this.history.slice(0, NotificationManager.MAX_HISTORY_SIZE);
        }

        return id;
    }

    private logToOutput(level: NotificationLevel, message: string, detail?: string): void {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
        
        this.outputChannel.appendLine(logMessage);
        
        if (detail) {
            this.outputChannel.appendLine(`  Detail: ${detail}`);
        }
    }

    public async showError(
        message: string,
        options: NotificationOptions = {}
    ): Promise<string | undefined> {
        const id = this.addToHistory('error', message, options.detail, options.actions);
        this.logToOutput('error', message, options.detail);

        if (!this.shouldShow('error')) {
            return undefined;
        }

        let result: string | undefined;

        if (options.modal) {
            result = await vscode.window.showErrorMessage(
                message,
                { modal: true, detail: options.detail },
                ...(options.actions || [])
            );
        } else {
            result = await vscode.window.showErrorMessage(
                message,
                ...(options.actions || [])
            );
        }

        // 标记为已处理
        const notification = this.history.find(n => n.id === id);
        if (notification) {
            notification.dismissed = true;
        }

        return result;
    }

    public async showWarning(
        message: string,
        options: NotificationOptions = {}
    ): Promise<string | undefined> {
        const id = this.addToHistory('warning', message, options.detail, options.actions);
        this.logToOutput('warning', message, options.detail);

        if (!this.shouldShow('warning')) {
            return undefined;
        }

        let result: string | undefined;

        if (options.modal) {
            result = await vscode.window.showWarningMessage(
                message,
                { modal: true, detail: options.detail },
                ...(options.actions || [])
            );
        } else {
            result = await vscode.window.showWarningMessage(
                message,
                ...(options.actions || [])
            );
        }

        // 标记为已处理
        const notification = this.history.find(n => n.id === id);
        if (notification) {
            notification.dismissed = true;
        }

        return result;
    }

    public async showInfo(
        message: string,
        options: NotificationOptions = {}
    ): Promise<string | undefined> {
        const id = this.addToHistory('info', message, options.detail, options.actions);
        this.logToOutput('info', message, options.detail);

        if (!this.shouldShow('info')) {
            return undefined;
        }

        let result: string | undefined;

        if (options.modal) {
            result = await vscode.window.showInformationMessage(
                message,
                { modal: true, detail: options.detail },
                ...(options.actions || [])
            );
        } else {
            result = await vscode.window.showInformationMessage(
                message,
                ...(options.actions || [])
            );
        }

        // 标记为已处理
        const notification = this.history.find(n => n.id === id);
        if (notification) {
            notification.dismissed = true;
        }

        return result;
    }

    public showDebug(message: string, detail?: string): void {
        this.addToHistory('debug', message, detail);
        this.logToOutput('debug', message, detail);

        // Debug消息只记录到输出通道，不显示弹窗
    }

    public async showProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ message?: string; increment?: number }>) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title,
                cancellable: false
            },
            task
        );
    }

    public async showProgressWithCancellation<T>(
        title: string,
        task: (
            progress: vscode.Progress<{ message?: string; increment?: number }>,
            token: vscode.CancellationToken
        ) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title,
                cancellable: true
            },
            task
        );
    }

    public async showQuickPick<T extends vscode.QuickPickItem>(
        items: T[],
        options?: vscode.QuickPickOptions
    ): Promise<T | undefined> {
        return vscode.window.showQuickPick(items, options);
    }

    public async showInputBox(options?: vscode.InputBoxOptions): Promise<string | undefined> {
        return vscode.window.showInputBox(options);
    }

    public async showOpenDialog(options?: vscode.OpenDialogOptions): Promise<vscode.Uri[] | undefined> {
        return vscode.window.showOpenDialog(options);
    }

    public async showSaveDialog(options?: vscode.SaveDialogOptions): Promise<vscode.Uri | undefined> {
        return vscode.window.showSaveDialog(options);
    }

    public getHistory(): NotificationHistory[] {
        return [...this.history];
    }

    public getHistoryByLevel(level: NotificationLevel): NotificationHistory[] {
        return this.history.filter(n => n.level === level);
    }

    public clearHistory(): void {
        this.history = [];
    }

    public clearHistoryByLevel(level: NotificationLevel): void {
        this.history = this.history.filter(n => n.level !== level);
    }

    public getUnreadCount(): number {
        return this.history.filter(n => !n.dismissed).length;
    }

    public getUnreadCountByLevel(level: NotificationLevel): number {
        return this.history.filter(n => n.level === level && !n.dismissed).length;
    }

    public markAsRead(id: string): void {
        const notification = this.history.find(n => n.id === id);
        if (notification) {
            notification.dismissed = true;
        }
    }

    public markAllAsRead(): void {
        this.history.forEach(n => n.dismissed = true);
    }

    public showOutputChannel(): void {
        this.outputChannel.show();
    }

    public hideOutputChannel(): void {
        this.outputChannel.hide();
    }

    public async showConnectionError(error: string): Promise<string | undefined> {
        return this.showError(
            'Failed to connect to AgentScope backend',
            {
                detail: error,
                actions: ['Retry', 'Configure', 'Show Logs'],
                modal: false
            }
        );
    }

    public async showTaskError(taskId: string, error: string): Promise<string | undefined> {
        return this.showError(
            `Task ${taskId} failed`,
            {
                detail: error,
                actions: ['Retry', 'Show Details', 'Dismiss'],
                modal: false
            }
        );
    }

    public async showTaskSuccess(taskId: string, message: string): Promise<string | undefined> {
        return this.showInfo(
            `Task ${taskId} completed successfully`,
            {
                detail: message,
                actions: ['Show Results', 'Dismiss'],
                modal: false
            }
        );
    }

    public async showAgentStatus(agentId: string, status: string): Promise<void> {
        if (status === 'error') {
            await this.showWarning(
                `Agent ${agentId} encountered an error`,
                {
                    actions: ['Show Details', 'Restart Agent', 'Dismiss']
                }
            );
        } else if (status === 'busy') {
            this.showDebug(`Agent ${agentId} is busy processing tasks`);
        } else if (status === 'idle') {
            this.showDebug(`Agent ${agentId} is idle and ready for tasks`);
        }
    }

    public async confirmAction(
        message: string,
        detail?: string,
        confirmText: string = 'Confirm',
        cancelText: string = 'Cancel'
    ): Promise<boolean> {
        const result = await vscode.window.showWarningMessage(
            message,
            { modal: true, detail },
            confirmText,
            cancelText
        );
        return result === confirmText;
    }

    public async showConfigurationPrompt(): Promise<string | undefined> {
        return this.showWarning(
            'AgentScope is not configured properly',
            {
                detail: 'Please configure the backend connection and agent settings',
                actions: ['Open Settings', 'Quick Setup', 'Dismiss']
            }
        );
    }

    public dispose(): void {
        this.outputChannel.dispose();
    }
}
