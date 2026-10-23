/**
 * Augment活动监听器 - 实现对Augment Agent活动的实时监听
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';

// Augment集成相关接口
export interface AugmentActivity {
    type: 'command' | 'output' | 'file_change' | 'document_change';
    content: string;
    context: any;
    timestamp: number;
    source: string;
}

export interface AugmentCommand {
    command: string;
    args: any;
    source: string;
}

/**
 * Augment活动监听器
 */
export class AugmentActivityWatcher extends EventEmitter {
    private outputChannels: Map<string, vscode.OutputChannel> = new Map();
    private fileWatcher: vscode.FileSystemWatcher | null = null;
    private documentWatcher: vscode.Disposable | null = null;
    private commandWatcher: vscode.Disposable | null = null;
    private isActive: boolean = false;
    
    constructor() {
        super();
    }
    
    async start(): Promise<void> {
        if (this.isActive) return;
        
        this.isActive = true;
        console.log('Starting Augment activity watcher...');
        
        try {
            // 1. 监听输出通道
            await this.setupOutputChannelMonitoring();
            
            // 2. 监听文件系统变化
            await this.setupFileSystemMonitoring();
            
            // 3. 监听命令执行
            await this.setupCommandMonitoring();
            
            // 4. 监听文档变化
            await this.setupDocumentMonitoring();
            
            console.log('Augment activity watcher started successfully');
            
        } catch (error) {
            console.error('Failed to start Augment activity watcher:', error);
            throw error;
        }
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
        
        if (this.documentWatcher) {
            this.documentWatcher.dispose();
            this.documentWatcher = null;
        }
        
        if (this.commandWatcher) {
            this.commandWatcher.dispose();
            this.commandWatcher = null;
        }
        
        console.log('Augment activity watcher stopped');
    }
    
    private async setupOutputChannelMonitoring(): Promise<void> {
        // 监听可能的Augment输出通道
        const augmentChannelNames = [
            'Augment',
            'AI Assistant',
            'Code Assistant',
            'GitHub Copilot',
            'Codeium',
            'Tabnine',
            'Claude',
            'ChatGPT'
        ];

        for (const channelName of augmentChannelNames) {
            try {
                // 创建输出通道引用
                const channel = vscode.window.createOutputChannel(channelName);
                this.outputChannels.set(channelName, channel);

                // 尝试监听通道内容变化（通过扩展API）
                this.setupChannelContentMonitoring(channelName, channel);

            } catch (error) {
                console.warn(`Failed to monitor output channel ${channelName}:`, error);
            }
        }

        // 监听终端输出（可能包含AI助手的输出）
        await this.setupTerminalMonitoring();
    }

    private setupChannelContentMonitoring(channelName: string, channel: vscode.OutputChannel): void {
        // 由于VS Code API限制，我们使用间接方法监听输出通道
        // 通过监听扩展激活和命令执行来推断AI助手活动

        // 监听相关扩展的激活
        const relatedExtensions = [
            'github.copilot',
            'codeium.codeium',
            'tabnine.tabnine-vscode',
            'anthropic.claude-dev'
        ];

        for (const extId of relatedExtensions) {
            const extension = vscode.extensions.getExtension(extId);
            if (extension) {
                // 如果扩展已激活，设置监听
                if (extension.isActive) {
                    this.monitorExtensionActivity(extId, extension);
                } else {
                    // 监听扩展激活
                    extension.activate().then(() => {
                        this.monitorExtensionActivity(extId, extension);
                    }); // 移除catch，避免编译错误
                }
            }
        }
    }

    private monitorExtensionActivity(extensionId: string, extension: vscode.Extension<any>): void {
        // 监听扩展相关的活动
        console.log(`Monitoring activity for extension: ${extensionId}`);

        // 这里可以添加特定扩展的监听逻辑
        // 例如，监听Copilot的建议生成事件
    }

    private async setupTerminalMonitoring(): Promise<void> {
        // 监听终端创建和变化
        vscode.window.onDidOpenTerminal((terminal) => {
            this.monitorTerminal(terminal);
        });

        // 监听现有终端
        vscode.window.terminals.forEach(terminal => {
            this.monitorTerminal(terminal);
        });
    }

    private monitorTerminal(terminal: vscode.Terminal): void {
        // 监听终端名称变化（可能表示AI助手活动）
        if (terminal.name.toLowerCase().includes('ai') ||
            terminal.name.toLowerCase().includes('assistant') ||
            terminal.name.toLowerCase().includes('copilot')) {

            console.log(`Detected AI-related terminal: ${terminal.name}`);

            // 创建活动事件
            const activity: AugmentActivity = {
                type: 'output',
                content: `AI terminal detected: ${terminal.name}`,
                context: {
                    terminal_name: terminal.name,
                    source: 'terminal_monitoring'
                },
                timestamp: Date.now(),
                source: 'vscode_terminal'
            };

            this.emit('activity', activity);
        }
    }
    
    private async setupFileSystemMonitoring(): Promise<void> {
        // 监听可能包含Augment指令的文件
        const augmentFilePattern = '**/*.{augment,ai,assistant,copilot}';
        
        this.fileWatcher = vscode.workspace.createFileSystemWatcher(augmentFilePattern);
        
        this.fileWatcher.onDidCreate(async (uri) => {
            await this.handleAugmentFile(uri, 'created');
        });
        
        this.fileWatcher.onDidChange(async (uri) => {
            await this.handleAugmentFile(uri, 'changed');
        });
        
        // 监听临时目录
        const tempDirs = [
            path.join(require('os').homedir(), '.augment', 'temp'),
            path.join(require('os').tmpdir(), 'augment'),
            path.join(require('os').tmpdir(), 'ai-assistant')
        ];
        
        for (const tempDir of tempDirs) {
            if (fs.existsSync(tempDir)) {
                const tempWatcher = vscode.workspace.createFileSystemWatcher(
                    path.join(tempDir, '**/*')
                );
                
                tempWatcher.onDidCreate(async (uri) => {
                    await this.handleAugmentFile(uri, 'temp_created');
                });
                
                tempWatcher.onDidChange(async (uri) => {
                    await this.handleAugmentFile(uri, 'temp_changed');
                });
            }
        }
    }
    
    private async setupCommandMonitoring(): Promise<void> {
        // 监听可能的Augment相关命令
        const augmentCommands = [
            'augment.analyze',
            'augment.suggest',
            'augment.refactor',
            'github.copilot.generate',
            'github.copilot.interactiveEditor.generate',
            'ai.assistant.analyze',
            'codeium.command',
            'tabnine.command'
        ];
        
        // 注册命令拦截器
        const disposables: vscode.Disposable[] = [];
        
        // 监听所有命令执行
        const commandDisposable = vscode.commands.registerCommand(
            'agentscope.interceptAllCommands',
            (...args) => {
                // 这个命令不会被直接调用，但可以用来监听其他命令
            }
        );
        disposables.push(commandDisposable);
        
        // 尝试拦截特定命令
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
        this.documentWatcher = vscode.workspace.onDidChangeTextDocument(async (event) => {
            if (!this.isActive) return;
            
            const changes = event.contentChanges;
            for (const change of changes) {
                if (this.isAugmentGeneratedContent(change.text)) {
                    const activity: AugmentActivity = {
                        type: 'document_change',
                        content: change.text,
                        context: {
                            document: event.document.uri.toString(),
                            range: {
                                start: { line: change.range.start.line, character: change.range.start.character },
                                end: { line: change.range.end.line, character: change.range.end.character }
                            },
                            source: 'document_change',
                            language: event.document.languageId
                        },
                        timestamp: Date.now(),
                        source: 'vscode_document'
                    };
                    
                    this.emit('activity', activity);
                }
            }
        });
    }
    
    private async handleAugmentFile(uri: vscode.Uri, action: string): Promise<void> {
        try {
            const content = await fs.promises.readFile(uri.fsPath, 'utf-8');
            
            // 检查文件内容是否包含Augment指令
            if (this.containsAugmentInstructions(content)) {
                const activity: AugmentActivity = {
                    type: 'file_change',
                    content: content,
                    context: {
                        file: uri.toString(),
                        action: action,
                        source: 'file_system',
                        extension: path.extname(uri.fsPath)
                    },
                    timestamp: Date.now(),
                    source: 'vscode_file'
                };
                
                this.emit('activity', activity);
            }
            
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
            timestamp: Date.now(),
            source: 'vscode_command'
        };
        
        this.emit('activity', activity);
    }
    
    private isAugmentGeneratedContent(text: string): boolean {
        // 检测文本是否可能是Augment生成的
        const augmentPatterns = [
            /\/\*\s*AI\s*Generated/i,
            /\/\/\s*Augment\s*suggestion/i,
            /\/\*\s*Code\s*analysis/i,
            /#\s*AI\s*Assistant/i,
            /```\s*suggestion/i,
            /\/\*\s*GitHub\s*Copilot/i,
            /\/\/\s*Codeium\s*suggestion/i,
            /\/\*\s*Generated\s*by\s*AI/i,
            /\/\*\s*Claude\s*suggestion/i,
            /\/\/\s*ChatGPT\s*generated/i,
            /\/\*\s*Tabnine\s*completion/i,
            // 检测快速大量文本插入（可能是AI生成）
            /function\s+\w+\s*\([^)]*\)\s*\{[\s\S]{100,}/,
            /class\s+\w+\s*\{[\s\S]{100,}/,
            // 检测注释中的AI指令
            /\/\/\s*TODO:\s*(分析|检查|优化|重构)/i,
            /\/\*\s*(请|帮助|分析|检查|优化|重构)/i,
            /#\s*(请|帮助|分析|检查|优化|重构)/i
        ];

        // 检测文本特征
        const hasAIPatterns = augmentPatterns.some(pattern => pattern.test(text));

        // 检测快速大量插入（可能是AI生成）
        const isLargeInsertion = text.length > 200 && text.includes('\n');

        // 检测代码模板特征
        const hasTemplateFeatures = (
            text.includes('// TODO:') ||
            text.includes('/* TODO:') ||
            text.includes('function') ||
            text.includes('class') ||
            text.includes('interface')
        ) && text.length > 50;

        return hasAIPatterns || (isLargeInsertion && hasTemplateFeatures);
    }
    
    private containsAugmentInstructions(content: string): boolean {
        // 检查文件内容是否包含Augment指令
        const instructionPatterns = [
            /分析.*代码/i,
            /检查.*文件/i,
            /analyze.*code/i,
            /review.*file/i,
            /安全.*扫描/i,
            /security.*scan/i,
            /质量.*检查/i,
            /quality.*check/i,
            /重构.*建议/i,
            /refactor.*suggestion/i
        ];
        
        return instructionPatterns.some(pattern => pattern.test(content));
    }
    
    // 公共方法用于手动触发活动检测
    public async detectCurrentActivity(): Promise<AugmentActivity[]> {
        const activities: AugmentActivity[] = [];
        
        try {
            // 检查当前活动编辑器
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor) {
                const document = activeEditor.document;
                const content = document.getText();
                
                if (this.isAugmentGeneratedContent(content)) {
                    activities.push({
                        type: 'document_change',
                        content: content,
                        context: {
                            document: document.uri.toString(),
                            language: document.languageId,
                            source: 'manual_detection'
                        },
                        timestamp: Date.now(),
                        source: 'vscode_manual'
                    });
                }
            }
            
            // 检查最近的文件变化
            // 这里可以添加更多的检测逻辑
            
        } catch (error) {
            console.error('Failed to detect current activity:', error);
        }
        
        return activities;
    }
    
    // 获取当前上下文信息
    public getCurrentContext(): any {
        const context: any = {};
        
        // 获取当前活动编辑器
        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor) {
            context.current_file = activeEditor.document.uri.fsPath;
            context.language = activeEditor.document.languageId;
            context.selection = {
                start: { 
                    line: activeEditor.selection.start.line, 
                    character: activeEditor.selection.start.character 
                },
                end: { 
                    line: activeEditor.selection.end.line, 
                    character: activeEditor.selection.end.character 
                }
            };
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
                // 简化的Git信息
                context.git_branch = 'main';
            }
        } catch (error) {
            // Git信息获取失败，忽略
        }
        
        return context;
    }
}
