/**
 * VS Code插件优化方案
 * 基于审计结果的深度Augment集成和性能优化
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { WebSocket } from 'ws';

// Augment集成相关接口
interface AugmentActivity {
    type: 'command' | 'output' | 'file_change';
    content: string;
    context: any;
    timestamp: number;
}

interface AugmentCommand {
    command: string;
    args: any;
    source: string;
}

interface AgentScopeTask {
    id: string;
    type: string;
    description: string;
    parameters: any;
    priority: number;
}

/**
 * Augment活动监听器
 * 实现对Augment Agent活动的实时监听
 */
class AugmentActivityWatcher {
    private outputChannels: Map<string, vscode.OutputChannel> = new Map();
    private fileWatcher: vscode.FileSystemWatcher | null = null;
    private commandWatcher: vscode.Disposable | null = null;
    private isActive: boolean = false;
    
    constructor(private onActivity: (activity: AugmentActivity) => void) {}
    
    async start(): Promise<void> {
        if (this.isActive) return;
        
        this.isActive = true;
        console.log('Starting Augment activity watcher...');
        
        // 1. 监听输出通道
        await this.setupOutputChannelMonitoring();
        
        // 2. 监听文件系统变化
        await this.setupFileSystemMonitoring();
        
        // 3. 监听命令执行
        await this.setupCommandMonitoring();
        
        // 4. 监听文档变化（可能包含Augment生成的内容）
        await this.setupDocumentMonitoring();
    }
    
    stop(): void {
        if (!this.isActive) return;
        
        this.isActive = false;
        console.log('Stopping Augment activity watcher...');
        
        // 清理资源
        this.outputChannels.clear();
        
        if (this.fileWatcher) {
            this.fileWatcher.dispose();
            this.fileWatcher = null;
        }
        
        if (this.commandWatcher) {
            this.commandWatcher.dispose();
            this.commandWatcher = null;
        }
    }
    
    private async setupOutputChannelMonitoring(): Promise<void> {
        // 监听可能的Augment输出通道
        const augmentChannelNames = [
            'Augment',
            'AI Assistant', 
            'Code Assistant',
            'GitHub Copilot'
        ];
        
        for (const channelName of augmentChannelNames) {
            try {
                const channel = vscode.window.createOutputChannel(channelName);
                this.outputChannels.set(channelName, channel);
                
                // 注意：VS Code API不直接支持监听输出通道内容
                // 这里需要使用其他方法，如文件监听或扩展间通信
                
            } catch (error) {
                console.warn(`Failed to monitor output channel ${channelName}:`, error);
            }
        }
    }
    
    private async setupFileSystemMonitoring(): Promise<void> {
        // 监听可能包含Augment指令的文件
        const augmentFilePattern = '**/*.{augment,ai,assistant}';
        
        this.fileWatcher = vscode.workspace.createFileSystemWatcher(augmentFilePattern);
        
        this.fileWatcher.onDidCreate(async (uri) => {
            await this.handleAugmentFile(uri, 'created');
        });
        
        this.fileWatcher.onDidChange(async (uri) => {
            await this.handleAugmentFile(uri, 'changed');
        });
    }
    
    private async setupCommandMonitoring(): Promise<void> {
        // 监听可能的Augment相关命令
        const augmentCommands = [
            'augment.analyze',
            'augment.suggest',
            'augment.refactor',
            'github.copilot.generate',
            'ai.assistant.analyze'
        ];
        
        // 注册命令拦截器
        const disposables: vscode.Disposable[] = [];
        
        for (const commandName of augmentCommands) {
            try {
                const disposable = vscode.commands.registerCommand(
                    `agentscope.intercept.${commandName}`,
                    (...args) => this.handleAugmentCommand(commandName, args)
                );
                disposables.push(disposable);
            } catch (error) {
                console.warn(`Failed to register command interceptor for ${commandName}:`, error);
            }
        }
        
        this.commandWatcher = vscode.Disposable.from(...disposables);
    }
    
    private async setupDocumentMonitoring(): Promise<void> {
        // 监听文档变化，检测可能的Augment生成内容
        vscode.workspace.onDidChangeTextDocument(async (event) => {
            if (!this.isActive) return;
            
            const changes = event.contentChanges;
            for (const change of changes) {
                if (this.isAugmentGeneratedContent(change.text)) {
                    const activity: AugmentActivity = {
                        type: 'output',
                        content: change.text,
                        context: {
                            document: event.document.uri.toString(),
                            range: change.range,
                            source: 'document_change'
                        },
                        timestamp: Date.now()
                    };
                    
                    this.onActivity(activity);
                }
            }
        });
    }
    
    private async handleAugmentFile(uri: vscode.Uri, action: string): Promise<void> {
        try {
            const content = await fs.promises.readFile(uri.fsPath, 'utf-8');
            
            const activity: AugmentActivity = {
                type: 'file_change',
                content: content,
                context: {
                    file: uri.toString(),
                    action: action,
                    source: 'file_system'
                },
                timestamp: Date.now()
            };
            
            this.onActivity(activity);
            
        } catch (error) {
            console.error(`Failed to read Augment file ${uri.fsPath}:`, error);
        }
    }
    
    private async handleAugmentCommand(commandName: string, args: any[]): Promise<void> {
        const activity: AugmentActivity = {
            type: 'command',
            content: `Command: ${commandName}`,
            context: {
                command: commandName,
                args: args,
                source: 'command_execution'
            },
            timestamp: Date.now()
        };
        
        this.onActivity(activity);
    }
    
    private isAugmentGeneratedContent(text: string): boolean {
        // 检测文本是否可能是Augment生成的
        const augmentPatterns = [
            /\/\*\s*AI\s*Generated/i,
            /\/\/\s*Augment\s*suggestion/i,
            /\/\*\s*Code\s*analysis/i,
            /#\s*AI\s*Assistant/i,
            /```\s*suggestion/i
        ];
        
        return augmentPatterns.some(pattern => pattern.test(text));
    }
}

/**
 * Augment命令处理器
 * 将Augment指令转换为AgentScope任务
 */
class AugmentCommandProcessor {
    private nlpPatterns: Map<string, RegExp[]> = new Map([
        ['code_analysis', [
            /分析.*代码/i,
            /检查.*文件/i,
            /analyze.*code/i,
            /review.*file/i
        ]],
        ['security_scan', [
            /安全.*扫描/i,
            /漏洞.*检测/i,
            /security.*scan/i,
            /vulnerability.*check/i
        ]],
        ['quality_check', [
            /质量.*检查/i,
            /代码.*质量/i,
            /quality.*check/i,
            /code.*quality/i
        ]]
    ]);
    
    async processActivity(activity: AugmentActivity): Promise<AgentScopeTask | null> {
        try {
            // 1. 解析活动内容
            const intent = this.parseIntent(activity.content);
            if (!intent) return null;
            
            // 2. 获取当前上下文
            const context = await this.getCurrentContext();
            
            // 3. 创建任务
            const task: AgentScopeTask = {
                id: `augment_${Date.now()}`,
                type: intent.type,
                description: activity.content,
                parameters: {
                    ...intent.parameters,
                    ...context,
                    source: activity.context.source,
                    original_activity: activity
                },
                priority: this.determinePriority(intent.type)
            };
            
            return task;
            
        } catch (error) {
            console.error('Failed to process Augment activity:', error);
            return null;
        }
    }
    
    private parseIntent(content: string): { type: string; parameters: any } | null {
        for (const [intentType, patterns] of this.nlpPatterns) {
            for (const pattern of patterns) {
                if (pattern.test(content)) {
                    return {
                        type: intentType,
                        parameters: this.extractParameters(content, intentType)
                    };
                }
            }
        }
        
        return null;
    }
    
    private extractParameters(content: string, intentType: string): any {
        const parameters: any = {};
        
        // 提取文件路径
        const fileMatch = content.match(/(?:文件|file)[:：]\s*([^\s]+)/i);
        if (fileMatch) {
            parameters.file_path = fileMatch[1];
        }
        
        // 提取目录
        const dirMatch = content.match(/(?:目录|directory)[:：]\s*([^\s]+)/i);
        if (dirMatch) {
            parameters.directory = dirMatch[1];
        }
        
        // 根据意图类型提取特定参数
        if (intentType === 'security_scan') {
            if (content.includes('SQL注入') || content.includes('sql injection')) {
                parameters.scan_types = ['sql_injection'];
            }
            if (content.includes('XSS')) {
                parameters.scan_types = [...(parameters.scan_types || []), 'xss'];
            }
        }
        
        return parameters;
    }
    
    private async getCurrentContext(): Promise<any> {
        const context: any = {};
        
        // 获取当前活动编辑器
        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor) {
            context.current_file = activeEditor.document.uri.fsPath;
            context.language = activeEditor.document.languageId;
            context.selection = activeEditor.selection;
        }
        
        // 获取工作区信息
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            context.workspace_root = workspaceFolder.uri.fsPath;
        }
        
        // 获取Git信息
        try {
            const gitExtension = vscode.extensions.getExtension('vscode.git');
            if (gitExtension?.isActive) {
                // 获取Git状态信息
                context.git_branch = 'main'; // 简化实现
            }
        } catch (error) {
            // Git信息获取失败，忽略
        }
        
        return context;
    }
    
    private determinePriority(intentType: string): number {
        const priorityMap: { [key: string]: number } = {
            'security_scan': 1,      // 高优先级
            'code_analysis': 2,      // 中优先级
            'quality_check': 2,      // 中优先级
            'documentation': 3       // 低优先级
        };
        
        return priorityMap[intentType] || 2;
    }
}

/**
 * 增强的AgentScope系统管理器
 * 集成Augment监听和处理能力
 */
class EnhancedAgentSystemManager {
    private augmentWatcher: AugmentActivityWatcher | null = null;
    private commandProcessor: AugmentCommandProcessor;
    private backendConnection: WebSocket | null = null;
    private isConnected: boolean = false;
    
    constructor(
        private eventBus: any,
        private configManager: any,
        private notificationManager: any
    ) {
        this.commandProcessor = new AugmentCommandProcessor();
    }
    
    async initialize(): Promise<void> {
        console.log('Initializing enhanced AgentScope system...');
        
        // 1. 建立后端连接
        await this.connectToBackend();
        
        // 2. 启动Augment监听
        await this.startAugmentIntegration();
        
        // 3. 设置事件处理
        this.setupEventHandlers();
    }
    
    async dispose(): Promise<void> {
        console.log('Disposing enhanced AgentScope system...');
        
        // 停止Augment监听
        if (this.augmentWatcher) {
            this.augmentWatcher.stop();
            this.augmentWatcher = null;
        }
        
        // 关闭后端连接
        if (this.backendConnection) {
            this.backendConnection.close();
            this.backendConnection = null;
        }
    }
    
    private async connectToBackend(): Promise<void> {
        const config = this.configManager.getConfiguration();
        const backendUrl = `ws://${config.backend.host}:${config.backend.port}/ws`;
        
        try {
            this.backendConnection = new WebSocket(backendUrl);
            
            this.backendConnection.on('open', () => {
                this.isConnected = true;
                console.log('Connected to AgentScope backend');
                this.eventBus.emit('backendConnected');
            });
            
            this.backendConnection.on('close', () => {
                this.isConnected = false;
                console.log('Disconnected from AgentScope backend');
                this.eventBus.emit('backendDisconnected');
            });
            
            this.backendConnection.on('message', (data) => {
                this.handleBackendMessage(JSON.parse(data.toString()));
            });
            
            this.backendConnection.on('error', (error) => {
                console.error('Backend connection error:', error);
                this.eventBus.emit('backendError', error);
            });
            
        } catch (error) {
            console.error('Failed to connect to backend:', error);
            throw error;
        }
    }
    
    private async startAugmentIntegration(): Promise<void> {
        this.augmentWatcher = new AugmentActivityWatcher(
            (activity) => this.handleAugmentActivity(activity)
        );
        
        await this.augmentWatcher.start();
        console.log('Augment integration started');
    }
    
    private async handleAugmentActivity(activity: AugmentActivity): Promise<void> {
        try {
            console.log('Detected Augment activity:', activity.type, activity.content.substring(0, 100));
            
            // 1. 处理活动，转换为任务
            const task = await this.commandProcessor.processActivity(activity);
            if (!task) return;
            
            // 2. 发送任务到后端
            await this.sendTaskToBackend(task);
            
            // 3. 显示通知
            this.notificationManager.showInfo(
                `Augment指令已处理: ${task.description.substring(0, 50)}...`
            );
            
            // 4. 触发事件
            this.eventBus.emit('augmentTaskCreated', task);
            
        } catch (error) {
            console.error('Failed to handle Augment activity:', error);
            this.notificationManager.showError(`处理Augment指令失败: ${error.message}`);
        }
    }
    
    private async sendTaskToBackend(task: AgentScopeTask): Promise<void> {
        if (!this.isConnected || !this.backendConnection) {
            throw new Error('Backend not connected');
        }
        
        const message = {
            type: 'create_task',
            data: task
        };
        
        this.backendConnection.send(JSON.stringify(message));
    }
    
    private handleBackendMessage(message: any): void {
        switch (message.type) {
            case 'task_completed':
                this.handleTaskCompleted(message.data);
                break;
            case 'task_failed':
                this.handleTaskFailed(message.data);
                break;
            case 'agent_status_update':
                this.handleAgentStatusUpdate(message.data);
                break;
            default:
                console.log('Unknown backend message type:', message.type);
        }
    }
    
    private handleTaskCompleted(taskData: any): void {
        console.log('Task completed:', taskData.task_id);
        
        // 显示结果通知
        this.notificationManager.showInfo(
            `任务完成: ${taskData.title}`,
            '查看结果',
            () => this.showTaskResults(taskData)
        );
        
        // 触发事件
        this.eventBus.emit('taskCompleted', taskData);
    }
    
    private handleTaskFailed(taskData: any): void {
        console.error('Task failed:', taskData.task_id, taskData.error);
        
        this.notificationManager.showError(
            `任务失败: ${taskData.title} - ${taskData.error}`
        );
        
        this.eventBus.emit('taskFailed', taskData);
    }
    
    private handleAgentStatusUpdate(statusData: any): void {
        this.eventBus.emit('agentStatusUpdate', statusData);
    }
    
    private async showTaskResults(taskData: any): Promise<void> {
        // 创建结果显示面板
        const panel = vscode.window.createWebviewPanel(
            'agentscope.results',
            `分析结果: ${taskData.title}`,
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );
        
        // 生成结果HTML
        panel.webview.html = this.generateResultsHTML(taskData);
    }
    
    private generateResultsHTML(taskData: any): string {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>AgentScope 分析结果</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .result-section { margin-bottom: 20px; }
                .issue { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 5px 0; }
                .vulnerability { background: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; margin: 5px 0; }
                .suggestion { background: #d1ecf1; border: 1px solid #bee5eb; padding: 10px; margin: 5px 0; }
            </style>
        </head>
        <body>
            <h1>分析结果: ${taskData.title}</h1>
            <div class="result-section">
                <h2>任务信息</h2>
                <p><strong>任务ID:</strong> ${taskData.task_id}</p>
                <p><strong>类型:</strong> ${taskData.type}</p>
                <p><strong>状态:</strong> ${taskData.status}</p>
            </div>
            
            <div class="result-section">
                <h2>分析结果</h2>
                ${this.formatAnalysisResults(taskData.result)}
            </div>
        </body>
        </html>
        `;
    }
    
    private formatAnalysisResults(result: any): string {
        let html = '';
        
        if (result.issues && result.issues.length > 0) {
            html += '<h3>发现的问题</h3>';
            for (const issue of result.issues) {
                html += `<div class="issue">
                    <strong>${issue.type}:</strong> ${issue.message}
                    <br><small>文件: ${issue.file}, 行: ${issue.line}</small>
                </div>`;
            }
        }
        
        if (result.vulnerabilities && result.vulnerabilities.length > 0) {
            html += '<h3>安全漏洞</h3>';
            for (const vuln of result.vulnerabilities) {
                html += `<div class="vulnerability">
                    <strong>${vuln.type}:</strong> ${vuln.description}
                    <br><small>严重程度: ${vuln.severity}</small>
                </div>`;
            }
        }
        
        if (result.suggestions && result.suggestions.length > 0) {
            html += '<h3>改进建议</h3>';
            for (const suggestion of result.suggestions) {
                html += `<div class="suggestion">
                    ${suggestion.description}
                </div>`;
            }
        }
        
        return html || '<p>没有发现问题。</p>';
    }
    
    private setupEventHandlers(): void {
        // 监听配置变化
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('agentscope')) {
                this.handleConfigurationChange();
            }
        });
    }
    
    private async handleConfigurationChange(): Promise<void> {
        console.log('Configuration changed, updating system...');
        
        // 重新连接后端（如果配置改变）
        if (this.backendConnection) {
            this.backendConnection.close();
            await this.connectToBackend();
        }
    }
}

export { EnhancedAgentSystemManager, AugmentActivityWatcher, AugmentCommandProcessor };
