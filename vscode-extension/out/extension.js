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
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const agentStatusProvider_1 = require("./providers/agentStatusProvider");
const taskQueueProvider_1 = require("./providers/taskQueueProvider");
const resultsProvider_1 = require("./providers/resultsProvider");
const configurationManager_1 = require("./core/configurationManager");
const notificationManager_1 = require("./core/notificationManager");
const commandManager_1 = require("./core/commandManager");
const eventBus_1 = require("./core/eventBus");
const augmentActivityWatcher_1 = require("./augment/augmentActivityWatcher");
const augmentCommandProcessor_1 = require("./augment/augmentCommandProcessor");
const enhancedAgentSystemManager_1 = require("./core/enhancedAgentSystemManager");
async function activate(context) {
    console.log('AgentScope Multi-Agent Workflow extension is now active!');
    // 初始化核心组件
    const eventBus = new eventBus_1.EventBus();
    const configManager = new configurationManager_1.ConfigurationManager();
    const notificationManager = new notificationManager_1.NotificationManager();
    // 使用增强的智能体系统管理器（支持Augment集成）
    const agentSystemManager = new enhancedAgentSystemManager_1.EnhancedAgentSystemManager(eventBus, configManager, notificationManager);
    // 初始化Augment集成组件
    const augmentWatcher = new augmentActivityWatcher_1.AugmentActivityWatcher();
    const augmentProcessor = new augmentCommandProcessor_1.AugmentCommandProcessor();
    // 初始化视图提供者
    const agentStatusProvider = new agentStatusProvider_1.AgentStatusProvider(agentSystemManager, eventBus);
    const taskQueueProvider = new taskQueueProvider_1.TaskQueueProvider(agentSystemManager, eventBus);
    const resultsProvider = new resultsProvider_1.ResultsProvider(agentSystemManager, eventBus);
    // 注册视图
    vscode.window.registerTreeDataProvider('agentscope.agentStatus', agentStatusProvider);
    vscode.window.registerTreeDataProvider('agentscope.taskQueue', taskQueueProvider);
    vscode.window.registerTreeDataProvider('agentscope.results', resultsProvider);
    // 初始化命令管理器
    const commandManager = new commandManager_1.CommandManager(agentSystemManager, eventBus, notificationManager);
    // 注册基础命令
    const commands = [
        vscode.commands.registerCommand('agentscope.startAgentSystem', () => commandManager.startAgentSystem()),
        vscode.commands.registerCommand('agentscope.stopAgentSystem', () => commandManager.stopAgentSystem()),
        vscode.commands.registerCommand('agentscope.analyzeProject', (uri) => commandManager.analyzeProject(uri)),
        vscode.commands.registerCommand('agentscope.qualityCheck', (uri) => commandManager.qualityCheck(uri)),
        vscode.commands.registerCommand('agentscope.securityScan', (uri) => commandManager.securityScan(uri)),
        vscode.commands.registerCommand('agentscope.showDashboard', () => commandManager.showDashboard(context)),
        vscode.commands.registerCommand('agentscope.configureAgents', () => commandManager.configureAgents()),
        vscode.commands.registerCommand('agentscope.viewTaskHistory', () => commandManager.viewTaskHistory()),
        vscode.commands.registerCommand('agentscope.refreshAgentStatus', () => agentStatusProvider.refresh()),
        vscode.commands.registerCommand('agentscope.refreshTaskQueue', () => taskQueueProvider.refresh()),
        vscode.commands.registerCommand('agentscope.refreshResults', () => resultsProvider.refresh())
    ];
    // 添加Augment集成命令
    const augmentCommands = agentSystemManager.getAugmentCommands();
    commands.push(...augmentCommands);
    // 添加到订阅列表
    context.subscriptions.push(...commands);
    // 监听配置变化
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('agentscope')) {
            configManager.reloadConfiguration();
            agentSystemManager.updateConfiguration();
        }
    }));
    // 监听文件变化（如果启用了自动分析）
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(document => {
        const config = vscode.workspace.getConfiguration('agentscope');
        if (config.get('analysis.autoRun')) {
            commandManager.autoAnalyzeFile(document.uri);
        }
    }));
    // 设置状态栏
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.text = "$(robot) AgentScope";
    statusBarItem.tooltip = "AgentScope Multi-Agent Workflow";
    statusBarItem.command = 'agentscope.showDashboard';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
    // 监听系统状态变化
    eventBus.on('systemStatusChanged', (status) => {
        vscode.commands.executeCommand('setContext', 'agentscope.systemActive', status === 'active');
        if (status === 'active') {
            statusBarItem.text = "$(robot) AgentScope ✓";
            statusBarItem.backgroundColor = undefined;
        }
        else if (status === 'error') {
            statusBarItem.text = "$(robot) AgentScope ✗";
            statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        }
        else {
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
exports.activate = activate;
function deactivate() {
    console.log('AgentScope Multi-Agent Workflow extension is being deactivated');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map