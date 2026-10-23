"use strict";
/**
 * 增强的智能体系统管理器 - 集成Augment监听和处理能力
 */
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
exports.EnhancedAgentSystemManager = void 0;
const vscode = __importStar(require("vscode"));
const agentSystemManager_1 = require("./agentSystemManager");
const augmentActivityWatcher_1 = require("../augment/augmentActivityWatcher");
const augmentCommandProcessor_1 = require("../augment/augmentCommandProcessor");
class EnhancedAgentSystemManager extends agentSystemManager_1.AgentSystemManager {
    constructor(eventBus, configManager, notificationManager) {
        super(eventBus, configManager, notificationManager);
        this.augmentWatcher = null;
        this.augmentEnabled = false;
        // 公共属性用于访问Augment命令
        this.augmentCommands = [];
        this.augmentProcessor = new augmentCommandProcessor_1.AugmentCommandProcessor();
    }
    async initialize() {
        console.log('Initializing enhanced AgentScope system...');
        // 调用父类初始化
        await super.initialize();
        // 检查是否启用Augment集成
        const config = vscode.workspace.getConfiguration('agentscope');
        this.augmentEnabled = config.get('augment.enabled', false);
        if (this.augmentEnabled) {
            await this.initializeAugmentIntegration();
        }
    }
    async initializeAugmentIntegration() {
        try {
            console.log('Initializing Augment integration...');
            // 创建Augment活动监听器
            this.augmentWatcher = new augmentActivityWatcher_1.AugmentActivityWatcher();
            // 注册活动处理器
            this.augmentWatcher.on('activity', (activity) => {
                this.handleAugmentActivity(activity);
            });
            // 启动监听
            await this.augmentWatcher.start();
            // 注册Augment相关命令
            this.registerAugmentCommands();
            console.log('Augment integration initialized successfully');
            // 通知用户
            this.notificationManager.showInfo('Augment集成已启用', '现在可以通过自然语言指令触发代码分析');
        }
        catch (error) {
            console.error('Failed to initialize Augment integration:', error);
            this.notificationManager.showError(`Augment集成初始化失败: ${error.message}`);
        }
    }
    async handleAugmentActivity(activity) {
        try {
            console.log('Detected Augment activity:', activity.type, activity.content.substring(0, 100));
            // 处理活动，转换为任务
            const task = await this.augmentProcessor.processActivity(activity);
            if (!task) {
                console.log('No valid task generated from Augment activity');
                return;
            }
            // 验证任务
            const validation = this.augmentProcessor.validateTask(task);
            if (!validation.valid) {
                console.warn('Invalid task generated:', validation.errors);
                return;
            }
            // 显示处理通知
            this.notificationManager.showInfo(`处理Augment指令: ${task.title}`, '正在执行分析任务...');
            // 发送任务到后端
            await this.sendAugmentTaskToBackend(task);
            // 触发事件
            this.eventBus.emit('augmentTaskCreated', {
                activity,
                task,
                timestamp: Date.now()
            });
        }
        catch (error) {
            console.error('Failed to handle Augment activity:', error);
            this.notificationManager.showError(`处理Augment指令失败: ${error.message}`);
        }
    }
    async sendAugmentTaskToBackend(task) {
        if (!this.isConnected || !this.backendConnection) {
            throw new Error('Backend not connected');
        }
        try {
            // 发送Augment消息到后端
            const message = {
                type: 'augment_message',
                data: {
                    event_type: task.type,
                    content: task.description,
                    context: {
                        ...task.parameters,
                        source: 'vscode_augment'
                    },
                    source: 'vscode',
                    timestamp: Date.now(),
                    metadata: task.metadata
                }
            };
            this.backendConnection.send(JSON.stringify(message));
            console.log('Augment task sent to backend:', task.id);
        }
        catch (error) {
            console.error('Failed to send Augment task to backend:', error);
            throw error;
        }
    }
    registerAugmentCommands() {
        // 注册Augment相关命令
        const commands = [
            vscode.commands.registerCommand('agentscope.augment.enableIntegration', async () => {
                await this.enableAugmentIntegration();
            }),
            vscode.commands.registerCommand('agentscope.augment.disableIntegration', async () => {
                await this.disableAugmentIntegration();
            }),
            vscode.commands.registerCommand('agentscope.augment.detectActivity', async () => {
                await this.detectCurrentAugmentActivity();
            }),
            vscode.commands.registerCommand('agentscope.augment.processCommand', async (command) => {
                await this.processAugmentCommand(command);
            }),
            vscode.commands.registerCommand('agentscope.augment.showStatus', () => {
                this.showAugmentStatus();
            })
        ];
        // 这些命令需要在extension.ts中添加到subscriptions
        this.augmentCommands = commands;
    }
    async enableAugmentIntegration() {
        if (this.augmentEnabled) {
            this.notificationManager.showInfo('Augment集成已经启用');
            return;
        }
        try {
            // 更新配置
            const config = vscode.workspace.getConfiguration('agentscope');
            await config.update('augment.enabled', true, vscode.ConfigurationTarget.Workspace);
            // 初始化集成
            await this.initializeAugmentIntegration();
            this.augmentEnabled = true;
            this.notificationManager.showInfo('Augment集成已启用', '现在可以监听Augment Agent的活动');
        }
        catch (error) {
            this.notificationManager.showError(`启用Augment集成失败: ${error.message}`);
        }
    }
    async disableAugmentIntegration() {
        if (!this.augmentEnabled) {
            this.notificationManager.showInfo('Augment集成已经禁用');
            return;
        }
        try {
            // 停止监听
            if (this.augmentWatcher) {
                this.augmentWatcher.stop();
                this.augmentWatcher = null;
            }
            // 更新配置
            const config = vscode.workspace.getConfiguration('agentscope');
            await config.update('augment.enabled', false, vscode.ConfigurationTarget.Workspace);
            this.augmentEnabled = false;
            this.notificationManager.showInfo('Augment集成已禁用');
        }
        catch (error) {
            this.notificationManager.showError(`禁用Augment集成失败: ${error.message}`);
        }
    }
    async detectCurrentAugmentActivity() {
        if (!this.augmentWatcher) {
            this.notificationManager.showWarning('Augment集成未启用');
            return;
        }
        try {
            const activities = await this.augmentWatcher.detectCurrentActivity();
            if (activities.length === 0) {
                this.notificationManager.showInfo('未检测到Augment活动');
                return;
            }
            this.notificationManager.showInfo(`检测到 ${activities.length} 个Augment活动`, '正在处理...');
            // 处理检测到的活动
            for (const activity of activities) {
                await this.handleAugmentActivity(activity);
            }
        }
        catch (error) {
            this.notificationManager.showError(`检测Augment活动失败: ${error.message}`);
        }
    }
    async processAugmentCommand(command) {
        if (!command || command.trim().length === 0) {
            this.notificationManager.showWarning('请提供有效的Augment指令');
            return;
        }
        try {
            // 创建模拟的Augment活动
            const activity = {
                type: 'command',
                content: command,
                context: this.augmentWatcher?.getCurrentContext() || {},
                timestamp: Date.now(),
                source: 'manual_command'
            };
            // 处理指令
            await this.handleAugmentActivity(activity);
        }
        catch (error) {
            this.notificationManager.showError(`处理Augment指令失败: ${error.message}`);
        }
    }
    showAugmentStatus() {
        const status = {
            enabled: this.augmentEnabled,
            watcher_active: this.augmentWatcher !== null,
            supported_types: this.augmentProcessor.getSupportedTaskTypes(),
            backend_connected: this.isConnected
        };
        const statusMessage = `
Augment集成状态:
• 启用状态: ${status.enabled ? '✅ 已启用' : '❌ 已禁用'}
• 监听器状态: ${status.watcher_active ? '✅ 活跃' : '❌ 未活跃'}
• 后端连接: ${status.backend_connected ? '✅ 已连接' : '❌ 未连接'}
• 支持的任务类型: ${status.supported_types.join(', ')}
        `.trim();
        vscode.window.showInformationMessage(statusMessage, { modal: true });
    }
    handleBackendMessage(message) {
        // 调用父类处理
        super.handleBackendMessage(message);
        // 处理Augment相关消息
        switch (message.type) {
            case 'augment_task_completed':
                this.handleAugmentTaskCompleted(message.data);
                break;
            case 'augment_task_failed':
                this.handleAugmentTaskFailed(message.data);
                break;
        }
    }
    handleAugmentTaskCompleted(taskData) {
        console.log('Augment task completed:', taskData.task_id);
        // 显示完成通知
        this.notificationManager.showInfo(`Augment任务完成: ${taskData.title || taskData.task_id}`, '查看结果', () => this.showAugmentTaskResults(taskData));
        // 触发事件
        this.eventBus.emit('augmentTaskCompleted', taskData);
    }
    handleAugmentTaskFailed(taskData) {
        console.error('Augment task failed:', taskData.task_id, taskData.error);
        this.notificationManager.showError(`Augment任务失败: ${taskData.title || taskData.task_id}`, taskData.error);
        this.eventBus.emit('augmentTaskFailed', taskData);
    }
    async showAugmentTaskResults(taskData) {
        // 创建结果显示面板
        const panel = vscode.window.createWebviewPanel('agentscope.augmentResults', `Augment分析结果: ${taskData.title || taskData.task_id}`, vscode.ViewColumn.Two, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        // 生成结果HTML
        panel.webview.html = this.generateAugmentResultsHTML(taskData);
    }
    generateAugmentResultsHTML(taskData) {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Augment分析结果</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    padding: 20px; 
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                }
                .header { 
                    border-bottom: 2px solid var(--vscode-panel-border); 
                    padding-bottom: 15px; 
                    margin-bottom: 20px; 
                }
                .section { 
                    margin-bottom: 25px; 
                    padding: 15px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 5px;
                }
                .issue { 
                    background: var(--vscode-inputValidation-warningBackground); 
                    border: 1px solid var(--vscode-inputValidation-warningBorder); 
                    padding: 10px; 
                    margin: 8px 0; 
                    border-radius: 3px;
                }
                .vulnerability { 
                    background: var(--vscode-inputValidation-errorBackground); 
                    border: 1px solid var(--vscode-inputValidation-errorBorder); 
                    padding: 10px; 
                    margin: 8px 0; 
                    border-radius: 3px;
                }
                .suggestion { 
                    background: var(--vscode-inputValidation-infoBackground); 
                    border: 1px solid var(--vscode-inputValidation-infoBorder); 
                    padding: 10px; 
                    margin: 8px 0; 
                    border-radius: 3px;
                }
                .metadata {
                    font-size: 0.9em;
                    color: var(--vscode-descriptionForeground);
                    margin-top: 10px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎤 Augment分析结果</h1>
                <div class="metadata">
                    <strong>任务ID:</strong> ${taskData.task_id || 'N/A'}<br>
                    <strong>类型:</strong> ${taskData.type || 'N/A'}<br>
                    <strong>状态:</strong> ${taskData.status || 'N/A'}<br>
                    <strong>完成时间:</strong> ${new Date().toLocaleString()}
                </div>
            </div>
            
            <div class="section">
                <h2>📋 任务信息</h2>
                <p><strong>标题:</strong> ${taskData.title || 'N/A'}</p>
                <p><strong>描述:</strong> ${taskData.description || 'N/A'}</p>
            </div>
            
            <div class="section">
                <h2>📊 分析结果</h2>
                ${this.formatAugmentAnalysisResults(taskData.result || {})}
            </div>
            
            <div class="section">
                <h2>🔍 Augment集成信息</h2>
                <p><strong>原始指令:</strong> ${taskData.original_command || 'N/A'}</p>
                <p><strong>置信度:</strong> ${taskData.confidence || 'N/A'}</p>
                <p><strong>处理时间:</strong> ${taskData.processing_time || 'N/A'}ms</p>
            </div>
        </body>
        </html>
        `;
    }
    formatAugmentAnalysisResults(result) {
        let html = '';
        if (result.issues && result.issues.length > 0) {
            html += '<h3>⚠️ 发现的问题</h3>';
            for (const issue of result.issues) {
                html += `<div class="issue">
                    <strong>${issue.type}:</strong> ${issue.message}
                    <br><small>文件: ${issue.file}, 行: ${issue.line}</small>
                </div>`;
            }
        }
        if (result.vulnerabilities && result.vulnerabilities.length > 0) {
            html += '<h3>🔒 安全漏洞</h3>';
            for (const vuln of result.vulnerabilities) {
                html += `<div class="vulnerability">
                    <strong>${vuln.type}:</strong> ${vuln.description}
                    <br><small>严重程度: ${vuln.severity}</small>
                </div>`;
            }
        }
        if (result.suggestions && result.suggestions.length > 0) {
            html += '<h3>💡 改进建议</h3>';
            for (const suggestion of result.suggestions) {
                html += `<div class="suggestion">
                    ${suggestion.description}
                </div>`;
            }
        }
        return html || '<p>✅ 没有发现问题。</p>';
    }
    async dispose() {
        // 停止Augment监听
        if (this.augmentWatcher) {
            this.augmentWatcher.stop();
            this.augmentWatcher = null;
        }
        // 调用父类清理
        await super.dispose();
    }
    getAugmentCommands() {
        return this.augmentCommands;
    }
}
exports.EnhancedAgentSystemManager = EnhancedAgentSystemManager;
//# sourceMappingURL=enhancedAgentSystemManager-old.js.map