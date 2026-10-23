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
exports.NotificationManager = void 0;
const vscode = __importStar(require("vscode"));
class NotificationManager {
    constructor() {
        this.currentLevel = 'info';
        this.history = [];
        this.notificationCounter = 0;
        this.outputChannel = vscode.window.createOutputChannel('AgentScope');
    }
    setLevel(level) {
        this.currentLevel = level;
    }
    getLevel() {
        return this.currentLevel;
    }
    shouldShow(level) {
        const levels = ['debug', 'info', 'warning', 'error'];
        const currentIndex = levels.indexOf(this.currentLevel);
        const messageIndex = levels.indexOf(level);
        return messageIndex >= currentIndex;
    }
    addToHistory(level, message, detail, actions) {
        const id = `notification_${++this.notificationCounter}`;
        const notification = {
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
    logToOutput(level, message, detail) {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
        this.outputChannel.appendLine(logMessage);
        if (detail) {
            this.outputChannel.appendLine(`  Detail: ${detail}`);
        }
    }
    async showError(message, options = {}) {
        const id = this.addToHistory('error', message, options.detail, options.actions);
        this.logToOutput('error', message, options.detail);
        if (!this.shouldShow('error')) {
            return undefined;
        }
        let result;
        if (options.modal) {
            result = await vscode.window.showErrorMessage(message, { modal: true, detail: options.detail }, ...(options.actions || []));
        }
        else {
            result = await vscode.window.showErrorMessage(message, ...(options.actions || []));
        }
        // 标记为已处理
        const notification = this.history.find(n => n.id === id);
        if (notification) {
            notification.dismissed = true;
        }
        return result;
    }
    async showWarning(message, options = {}) {
        const id = this.addToHistory('warning', message, options.detail, options.actions);
        this.logToOutput('warning', message, options.detail);
        if (!this.shouldShow('warning')) {
            return undefined;
        }
        let result;
        if (options.modal) {
            result = await vscode.window.showWarningMessage(message, { modal: true, detail: options.detail }, ...(options.actions || []));
        }
        else {
            result = await vscode.window.showWarningMessage(message, ...(options.actions || []));
        }
        // 标记为已处理
        const notification = this.history.find(n => n.id === id);
        if (notification) {
            notification.dismissed = true;
        }
        return result;
    }
    async showInfo(message, options = {}) {
        const id = this.addToHistory('info', message, options.detail, options.actions);
        this.logToOutput('info', message, options.detail);
        if (!this.shouldShow('info')) {
            return undefined;
        }
        let result;
        if (options.modal) {
            result = await vscode.window.showInformationMessage(message, { modal: true, detail: options.detail }, ...(options.actions || []));
        }
        else {
            result = await vscode.window.showInformationMessage(message, ...(options.actions || []));
        }
        // 标记为已处理
        const notification = this.history.find(n => n.id === id);
        if (notification) {
            notification.dismissed = true;
        }
        return result;
    }
    showDebug(message, detail) {
        this.addToHistory('debug', message, detail);
        this.logToOutput('debug', message, detail);
        // Debug消息只记录到输出通道，不显示弹窗
    }
    async showProgress(title, task) {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title,
            cancellable: false
        }, task);
    }
    async showProgressWithCancellation(title, task) {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title,
            cancellable: true
        }, task);
    }
    async showQuickPick(items, options) {
        return vscode.window.showQuickPick(items, options);
    }
    async showInputBox(options) {
        return vscode.window.showInputBox(options);
    }
    async showOpenDialog(options) {
        return vscode.window.showOpenDialog(options);
    }
    async showSaveDialog(options) {
        return vscode.window.showSaveDialog(options);
    }
    getHistory() {
        return [...this.history];
    }
    getHistoryByLevel(level) {
        return this.history.filter(n => n.level === level);
    }
    clearHistory() {
        this.history = [];
    }
    clearHistoryByLevel(level) {
        this.history = this.history.filter(n => n.level !== level);
    }
    getUnreadCount() {
        return this.history.filter(n => !n.dismissed).length;
    }
    getUnreadCountByLevel(level) {
        return this.history.filter(n => n.level === level && !n.dismissed).length;
    }
    markAsRead(id) {
        const notification = this.history.find(n => n.id === id);
        if (notification) {
            notification.dismissed = true;
        }
    }
    markAllAsRead() {
        this.history.forEach(n => n.dismissed = true);
    }
    showOutputChannel() {
        this.outputChannel.show();
    }
    hideOutputChannel() {
        this.outputChannel.hide();
    }
    async showConnectionError(error) {
        return this.showError('Failed to connect to AgentScope backend', {
            detail: error,
            actions: ['Retry', 'Configure', 'Show Logs'],
            modal: false
        });
    }
    async showTaskError(taskId, error) {
        return this.showError(`Task ${taskId} failed`, {
            detail: error,
            actions: ['Retry', 'Show Details', 'Dismiss'],
            modal: false
        });
    }
    async showTaskSuccess(taskId, message) {
        return this.showInfo(`Task ${taskId} completed successfully`, {
            detail: message,
            actions: ['Show Results', 'Dismiss'],
            modal: false
        });
    }
    async showAgentStatus(agentId, status) {
        if (status === 'error') {
            await this.showWarning(`Agent ${agentId} encountered an error`, {
                actions: ['Show Details', 'Restart Agent', 'Dismiss']
            });
        }
        else if (status === 'busy') {
            this.showDebug(`Agent ${agentId} is busy processing tasks`);
        }
        else if (status === 'idle') {
            this.showDebug(`Agent ${agentId} is idle and ready for tasks`);
        }
    }
    async confirmAction(message, detail, confirmText = 'Confirm', cancelText = 'Cancel') {
        const result = await vscode.window.showWarningMessage(message, { modal: true, detail }, confirmText, cancelText);
        return result === confirmText;
    }
    async showConfigurationPrompt() {
        return this.showWarning('AgentScope is not configured properly', {
            detail: 'Please configure the backend connection and agent settings',
            actions: ['Open Settings', 'Quick Setup', 'Dismiss']
        });
    }
    dispose() {
        this.outputChannel.dispose();
    }
}
exports.NotificationManager = NotificationManager;
NotificationManager.MAX_HISTORY_SIZE = 100;
//# sourceMappingURL=notificationManager.js.map