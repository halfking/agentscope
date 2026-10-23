import * as vscode from 'vscode';
import { AgentSystemManager } from './core/agentSystemManager';
import { AgentStatusProvider } from './providers/agentStatusProvider';
import { TaskQueueProvider } from './providers/taskQueueProvider';
import { ResultsProvider } from './providers/resultsProvider';
import { DashboardPanel } from './panels/dashboardPanel';
import { ConfigurationManager } from './core/configurationManager';
import { NotificationManager } from './core/notificationManager';
import { CommandManager } from './core/commandManager';
import { EventBus } from './core/eventBus';
import { AugmentActivityWatcher } from './augment/augmentActivityWatcher';
import { AugmentCommandProcessor } from './augment/augmentCommandProcessor';
import { EnhancedAgentSystemManager } from './core/enhancedAgentSystemManager';

export async function activate(context: vscode.ExtensionContext) {
    console.log('AgentScope Multi-Agent Workflow extension is now active!');

    // 初始化核心组件
    const eventBus = new EventBus();
    const configManager = new ConfigurationManager();
    const notificationManager = new NotificationManager();

    // 使用增强的智能体系统管理器（支持Augment集成）
    const agentSystemManager = new EnhancedAgentSystemManager(
        eventBus,
        configManager,
        notificationManager
    );

    // 初始化Augment集成组件
    const augmentWatcher = new AugmentActivityWatcher();
    const augmentProcessor = new AugmentCommandProcessor();
    
    // 初始化视图提供者
    const agentStatusProvider = new AgentStatusProvider(agentSystemManager, eventBus);
    const taskQueueProvider = new TaskQueueProvider(agentSystemManager, eventBus);
    const resultsProvider = new ResultsProvider(agentSystemManager, eventBus);
    
    // 注册视图
    vscode.window.registerTreeDataProvider('agentscope.agentStatus', agentStatusProvider);
    vscode.window.registerTreeDataProvider('agentscope.taskQueue', taskQueueProvider);
    vscode.window.registerTreeDataProvider('agentscope.results', resultsProvider);
    
    // 初始化命令管理器
    const commandManager = new CommandManager(
        agentSystemManager,
        eventBus,
        notificationManager
    );
    
    // 注册基础命令
    const commands = [
        vscode.commands.registerCommand('agentscope.startAgentSystem', () =>
            commandManager.startAgentSystem()
        ),
        vscode.commands.registerCommand('agentscope.stopAgentSystem', () =>
            commandManager.stopAgentSystem()
        ),
        vscode.commands.registerCommand('agentscope.analyzeProject', (uri?: vscode.Uri) =>
            commandManager.analyzeProject(uri)
        ),
        vscode.commands.registerCommand('agentscope.qualityCheck', (uri?: vscode.Uri) =>
            commandManager.qualityCheck(uri)
        ),
        vscode.commands.registerCommand('agentscope.securityScan', (uri?: vscode.Uri) =>
            commandManager.securityScan(uri)
        ),
        vscode.commands.registerCommand('agentscope.showDashboard', () =>
            commandManager.showDashboard(context)
        ),
        vscode.commands.registerCommand('agentscope.configureAgents', () =>
            commandManager.configureAgents()
        ),
        vscode.commands.registerCommand('agentscope.viewTaskHistory', () =>
            commandManager.viewTaskHistory()
        ),
        vscode.commands.registerCommand('agentscope.refreshAgentStatus', () =>
            agentStatusProvider.refresh()
        ),
        vscode.commands.registerCommand('agentscope.refreshTaskQueue', () =>
            taskQueueProvider.refresh()
        ),
        vscode.commands.registerCommand('agentscope.refreshResults', () =>
            resultsProvider.refresh()
        )
    ];

    // 添加Augment集成命令
    const augmentCommands = agentSystemManager.getAugmentCommands();
    commands.push(...augmentCommands);
    
    // 添加到订阅列表
    context.subscriptions.push(...commands);
    
    // 监听配置变化
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('agentscope')) {
                configManager.reloadConfiguration();
                agentSystemManager.updateConfiguration();
            }
        })
    );
    
    // 监听文件变化（如果启用了自动分析）
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(document => {
            const config = vscode.workspace.getConfiguration('agentscope');
            if (config.get('analysis.autoRun')) {
                commandManager.autoAnalyzeFile(document.uri);
            }
        })
    );
    
    // 设置状态栏
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Left, 
        100
    );
    statusBarItem.text = "$(robot) AgentScope";
    statusBarItem.tooltip = "AgentScope Multi-Agent Workflow";
    statusBarItem.command = 'agentscope.showDashboard';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
    
    // 监听系统状态变化
    eventBus.on('systemStatusChanged', (status: string) => {
        vscode.commands.executeCommand('setContext', 'agentscope.systemActive', status === 'active');
        
        if (status === 'active') {
            statusBarItem.text = "$(robot) AgentScope ✓";
            statusBarItem.backgroundColor = undefined;
        } else if (status === 'error') {
            statusBarItem.text = "$(robot) AgentScope ✗";
            statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        } else {
            statusBarItem.text = "$(robot) AgentScope";
            statusBarItem.backgroundColor = undefined;
        }
    });
    
    // 自动启动系统（如果配置了）
    const config = vscode.workspace.getConfiguration('agentscope');
    if (config.get('dashboard.autoOpen')) {
        setTimeout(() => {
            commandManager.startAgentSystem();
        }, 2000);
    }
    
    console.log('AgentScope extension activation completed');
}

export function deactivate() {
    console.log('AgentScope Multi-Agent Workflow extension is being deactivated');
}
