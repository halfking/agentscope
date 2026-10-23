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
export declare class NotificationManager {
    private static readonly MAX_HISTORY_SIZE;
    private currentLevel;
    private history;
    private notificationCounter;
    private outputChannel;
    constructor();
    setLevel(level: NotificationLevel): void;
    getLevel(): NotificationLevel;
    private shouldShow;
    private addToHistory;
    private logToOutput;
    showError(message: string, options?: NotificationOptions): Promise<string | undefined>;
    showWarning(message: string, options?: NotificationOptions): Promise<string | undefined>;
    showInfo(message: string, options?: NotificationOptions): Promise<string | undefined>;
    showDebug(message: string, detail?: string): void;
    showProgress<T>(title: string, task: (progress: vscode.Progress<{
        message?: string;
        increment?: number;
    }>) => Promise<T>): Promise<T>;
    showProgressWithCancellation<T>(title: string, task: (progress: vscode.Progress<{
        message?: string;
        increment?: number;
    }>, token: vscode.CancellationToken) => Promise<T>): Promise<T>;
    showQuickPick<T extends vscode.QuickPickItem>(items: T[], options?: vscode.QuickPickOptions): Promise<T | undefined>;
    showInputBox(options?: vscode.InputBoxOptions): Promise<string | undefined>;
    showOpenDialog(options?: vscode.OpenDialogOptions): Promise<vscode.Uri[] | undefined>;
    showSaveDialog(options?: vscode.SaveDialogOptions): Promise<vscode.Uri | undefined>;
    getHistory(): NotificationHistory[];
    getHistoryByLevel(level: NotificationLevel): NotificationHistory[];
    clearHistory(): void;
    clearHistoryByLevel(level: NotificationLevel): void;
    getUnreadCount(): number;
    getUnreadCountByLevel(level: NotificationLevel): number;
    markAsRead(id: string): void;
    markAllAsRead(): void;
    showOutputChannel(): void;
    hideOutputChannel(): void;
    showConnectionError(error: string): Promise<string | undefined>;
    showTaskError(taskId: string, error: string): Promise<string | undefined>;
    showTaskSuccess(taskId: string, message: string): Promise<string | undefined>;
    showAgentStatus(agentId: string, status: string): Promise<void>;
    confirmAction(message: string, detail?: string, confirmText?: string, cancelText?: string): Promise<boolean>;
    showConfigurationPrompt(): Promise<string | undefined>;
    dispose(): void;
}
//# sourceMappingURL=notificationManager.d.ts.map