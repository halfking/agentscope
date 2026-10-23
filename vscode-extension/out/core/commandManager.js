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
exports.CommandManager = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const dashboardPanel_1 = require("../panels/dashboardPanel");
class CommandManager {
    constructor(agentSystemManager, eventBus, notificationManager) {
        this.agentSystemManager = agentSystemManager;
        this.eventBus = eventBus;
        this.notificationManager = notificationManager;
    }
    async startAgentSystem() {
        try {
            await this.notificationManager.showProgress('Starting AgentScope System...', async (progress) => {
                progress.report({ message: 'Connecting to backend...', increment: 20 });
                const connected = await this.agentSystemManager.connect();
                if (!connected) {
                    throw new Error('Failed to connect to backend');
                }
                progress.report({ message: 'Loading agents...', increment: 40 });
                await this.agentSystemManager.getAgents();
                progress.report({ message: 'System ready', increment: 40 });
            });
            await this.notificationManager.showInfo('AgentScope system started successfully');
        }
        catch (error) {
            const action = await this.notificationManager.showConnectionError(error?.message || String(error));
            if (action === 'Retry') {
                await this.startAgentSystem();
            }
            else if (action === 'Configure') {
                await vscode.commands.executeCommand('workbench.action.openSettings', 'agentscope');
            }
            else if (action === 'Show Logs') {
                this.notificationManager.showOutputChannel();
            }
        }
    }
    async stopAgentSystem() {
        try {
            this.agentSystemManager.disconnect();
            await this.notificationManager.showInfo('AgentScope system stopped');
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to stop system: ${error}`);
        }
    }
    async analyzeProject(uri) {
        try {
            if (!this.agentSystemManager.isSystemConnected()) {
                await this.notificationManager.showWarning('AgentScope system is not connected');
                return;
            }
            let projectPath;
            if (uri) {
                projectPath = uri.fsPath;
            }
            else {
                // 使用当前工作区
                const workspaceFolders = vscode.workspace.workspaceFolders;
                if (!workspaceFolders || workspaceFolders.length === 0) {
                    await this.notificationManager.showWarning('No workspace folder is open');
                    return;
                }
                projectPath = workspaceFolders[0].uri.fsPath;
            }
            const taskId = await this.agentSystemManager.analyzeProject(projectPath);
            await this.notificationManager.showInfo(`Project analysis started`, {
                detail: `Task ID: ${taskId}`,
                actions: ['Show Dashboard', 'Dismiss']
            });
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to start project analysis: ${error}`);
        }
    }
    async qualityCheck(uri) {
        try {
            if (!this.agentSystemManager.isSystemConnected()) {
                await this.notificationManager.showWarning('AgentScope system is not connected');
                return;
            }
            let filePath;
            if (uri) {
                filePath = uri.fsPath;
            }
            else {
                // 使用当前活动编辑器
                const activeEditor = vscode.window.activeTextEditor;
                if (!activeEditor) {
                    await this.notificationManager.showWarning('No file is currently open');
                    return;
                }
                filePath = activeEditor.document.uri.fsPath;
            }
            // 检查文件类型
            const ext = path.extname(filePath).toLowerCase();
            const supportedExtensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs'];
            if (!supportedExtensions.includes(ext)) {
                await this.notificationManager.showWarning(`File type ${ext} is not supported for quality check`);
                return;
            }
            const taskId = await this.agentSystemManager.qualityCheck(filePath);
            await this.notificationManager.showInfo(`Quality check started`, {
                detail: `File: ${path.basename(filePath)}\nTask ID: ${taskId}`,
                actions: ['Show Dashboard', 'Dismiss']
            });
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to start quality check: ${error}`);
        }
    }
    async securityScan(uri) {
        try {
            if (!this.agentSystemManager.isSystemConnected()) {
                await this.notificationManager.showWarning('AgentScope system is not connected');
                return;
            }
            let filePath;
            if (uri) {
                filePath = uri.fsPath;
            }
            else {
                const activeEditor = vscode.window.activeTextEditor;
                if (!activeEditor) {
                    await this.notificationManager.showWarning('No file is currently open');
                    return;
                }
                filePath = activeEditor.document.uri.fsPath;
            }
            const taskId = await this.agentSystemManager.securityScan(filePath);
            await this.notificationManager.showInfo(`Security scan started`, {
                detail: `File: ${path.basename(filePath)}\nTask ID: ${taskId}`,
                actions: ['Show Dashboard', 'Dismiss']
            });
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to start security scan: ${error}`);
        }
    }
    async showDashboard(context) {
        try {
            dashboardPanel_1.DashboardPanel.createOrShow(context, this.agentSystemManager, this.eventBus);
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to show dashboard: ${error}`);
        }
    }
    async configureAgents() {
        try {
            const quickPick = vscode.window.createQuickPick();
            quickPick.title = 'Configure AgentScope';
            quickPick.placeholder = 'Select configuration option';
            quickPick.items = [
                {
                    label: '$(settings-gear) Backend Settings',
                    description: 'Configure backend connection',
                    detail: 'Host, port, and protocol settings'
                },
                {
                    label: '$(robot) Agent Settings',
                    description: 'Enable/disable agents',
                    detail: 'Code Manager, Compliance Auditor, System Architect'
                },
                {
                    label: '$(brain) LLM Settings',
                    description: 'Configure LLM provider and model',
                    detail: 'OpenAI, Anthropic, SiliconFlow, etc.'
                },
                {
                    label: '$(search) Analysis Settings',
                    description: 'Configure analysis behavior',
                    detail: 'Auto-run, exclude patterns'
                },
                {
                    label: '$(bell) Notification Settings',
                    description: 'Configure notification level',
                    detail: 'Error, warning, info, debug'
                },
                {
                    label: '$(export) Export Configuration',
                    description: 'Export current configuration',
                    detail: 'Save configuration to file'
                },
                {
                    label: '$(import) Import Configuration',
                    description: 'Import configuration from file',
                    detail: 'Load configuration from file'
                },
                {
                    label: '$(refresh) Reset to Defaults',
                    description: 'Reset all settings to defaults',
                    detail: 'This will clear all custom settings'
                }
            ];
            quickPick.onDidChangeSelection(async (selection) => {
                if (selection.length > 0) {
                    const selected = selection[0];
                    quickPick.hide();
                    switch (selected.label) {
                        case '$(settings-gear) Backend Settings':
                            await vscode.commands.executeCommand('workbench.action.openSettings', 'agentscope.backend');
                            break;
                        case '$(robot) Agent Settings':
                            await vscode.commands.executeCommand('workbench.action.openSettings', 'agentscope.agents');
                            break;
                        case '$(brain) LLM Settings':
                            await vscode.commands.executeCommand('workbench.action.openSettings', 'agentscope.llm');
                            break;
                        case '$(search) Analysis Settings':
                            await vscode.commands.executeCommand('workbench.action.openSettings', 'agentscope.analysis');
                            break;
                        case '$(bell) Notification Settings':
                            await vscode.commands.executeCommand('workbench.action.openSettings', 'agentscope.notifications');
                            break;
                        case '$(export) Export Configuration':
                            await this.exportConfiguration();
                            break;
                        case '$(import) Import Configuration':
                            await this.importConfiguration();
                            break;
                        case '$(refresh) Reset to Defaults':
                            await this.resetConfiguration();
                            break;
                    }
                }
            });
            quickPick.show();
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to show configuration: ${error}`);
        }
    }
    async viewTaskHistory() {
        try {
            if (!this.agentSystemManager.isSystemConnected()) {
                await this.notificationManager.showWarning('AgentScope system is not connected');
                return;
            }
            // 这里可以实现任务历史查看功能
            // 暂时显示一个信息消息
            await this.notificationManager.showInfo('Task history feature coming soon', {
                actions: ['Show Dashboard', 'Dismiss']
            });
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to show task history: ${error}`);
        }
    }
    async autoAnalyzeFile(uri) {
        try {
            if (!this.agentSystemManager.isSystemConnected()) {
                return; // 静默失败，不显示通知
            }
            const filePath = uri.fsPath;
            const ext = path.extname(filePath).toLowerCase();
            // 只对支持的文件类型进行自动分析
            const supportedExtensions = ['.py', '.js', '.ts', '.java'];
            if (!supportedExtensions.includes(ext)) {
                return;
            }
            // 检查排除模式
            // 这里需要从配置管理器获取排除模式
            // 暂时硬编码一些常见的排除模式
            const excludePatterns = ['node_modules', '__pycache__', '.git', 'dist', 'build'];
            const shouldExclude = excludePatterns.some(pattern => filePath.includes(pattern));
            if (shouldExclude) {
                return;
            }
            // 启动质量检查
            await this.agentSystemManager.qualityCheck(filePath);
            // 显示简短的通知
            this.notificationManager.showDebug(`Auto-analysis started for ${path.basename(filePath)}`);
        }
        catch (error) {
            // 自动分析失败时只记录到日志，不显示错误通知
            this.notificationManager.showDebug(`Auto-analysis failed for ${uri.fsPath}: ${error}`);
        }
    }
    async exportConfiguration() {
        try {
            const config = vscode.workspace.getConfiguration('agentscope');
            const configData = {
                backend: {
                    host: config.get('backend.host'),
                    port: config.get('backend.port'),
                    protocol: config.get('backend.protocol')
                },
                agents: {
                    codeManager: { enabled: config.get('agents.codeManager.enabled') },
                    complianceAuditor: { enabled: config.get('agents.complianceAuditor.enabled') },
                    systemArchitect: { enabled: config.get('agents.systemArchitect.enabled') }
                },
                llm: {
                    provider: config.get('llm.provider'),
                    model: config.get('llm.model')
                },
                analysis: {
                    autoRun: config.get('analysis.autoRun'),
                    excludePatterns: config.get('analysis.excludePatterns')
                },
                notifications: {
                    level: config.get('notifications.level')
                },
                dashboard: {
                    autoOpen: config.get('dashboard.autoOpen')
                }
            };
            const configJson = JSON.stringify(configData, null, 2);
            const uri = await this.notificationManager.showSaveDialog({
                defaultUri: vscode.Uri.file('agentscope-config.json'),
                filters: {
                    'JSON files': ['json']
                }
            });
            if (uri) {
                await vscode.workspace.fs.writeFile(uri, Buffer.from(configJson, 'utf8'));
                await this.notificationManager.showInfo('Configuration exported successfully');
            }
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to export configuration: ${error}`);
        }
    }
    async importConfiguration() {
        try {
            const uris = await this.notificationManager.showOpenDialog({
                canSelectFiles: true,
                canSelectFolders: false,
                canSelectMany: false,
                filters: {
                    'JSON files': ['json']
                }
            });
            if (!uris || uris.length === 0) {
                return;
            }
            const configData = await vscode.workspace.fs.readFile(uris[0]);
            const configJson = Buffer.from(configData).toString('utf8');
            const config = JSON.parse(configJson);
            // 更新配置
            const vsConfig = vscode.workspace.getConfiguration('agentscope');
            if (config.backend) {
                await vsConfig.update('backend.host', config.backend.host, vscode.ConfigurationTarget.Global);
                await vsConfig.update('backend.port', config.backend.port, vscode.ConfigurationTarget.Global);
                await vsConfig.update('backend.protocol', config.backend.protocol, vscode.ConfigurationTarget.Global);
            }
            if (config.agents) {
                await vsConfig.update('agents.codeManager.enabled', config.agents.codeManager?.enabled, vscode.ConfigurationTarget.Global);
                await vsConfig.update('agents.complianceAuditor.enabled', config.agents.complianceAuditor?.enabled, vscode.ConfigurationTarget.Global);
                await vsConfig.update('agents.systemArchitect.enabled', config.agents.systemArchitect?.enabled, vscode.ConfigurationTarget.Global);
            }
            if (config.llm) {
                await vsConfig.update('llm.provider', config.llm.provider, vscode.ConfigurationTarget.Global);
                await vsConfig.update('llm.model', config.llm.model, vscode.ConfigurationTarget.Global);
            }
            if (config.analysis) {
                await vsConfig.update('analysis.autoRun', config.analysis.autoRun, vscode.ConfigurationTarget.Global);
                await vsConfig.update('analysis.excludePatterns', config.analysis.excludePatterns, vscode.ConfigurationTarget.Global);
            }
            if (config.notifications) {
                await vsConfig.update('notifications.level', config.notifications.level, vscode.ConfigurationTarget.Global);
            }
            if (config.dashboard) {
                await vsConfig.update('dashboard.autoOpen', config.dashboard.autoOpen, vscode.ConfigurationTarget.Global);
            }
            await this.notificationManager.showInfo('Configuration imported successfully');
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to import configuration: ${error}`);
        }
    }
    async resetConfiguration() {
        try {
            const confirmed = await this.notificationManager.confirmAction('Reset all AgentScope settings to defaults?', 'This will clear all your custom configuration settings.', 'Reset', 'Cancel');
            if (!confirmed) {
                return;
            }
            const config = vscode.workspace.getConfiguration('agentscope');
            // 重置所有配置项
            const resetPromises = [
                config.update('backend.host', undefined, vscode.ConfigurationTarget.Global),
                config.update('backend.port', undefined, vscode.ConfigurationTarget.Global),
                config.update('backend.protocol', undefined, vscode.ConfigurationTarget.Global),
                config.update('agents.codeManager.enabled', undefined, vscode.ConfigurationTarget.Global),
                config.update('agents.complianceAuditor.enabled', undefined, vscode.ConfigurationTarget.Global),
                config.update('agents.systemArchitect.enabled', undefined, vscode.ConfigurationTarget.Global),
                config.update('llm.provider', undefined, vscode.ConfigurationTarget.Global),
                config.update('llm.model', undefined, vscode.ConfigurationTarget.Global),
                config.update('analysis.autoRun', undefined, vscode.ConfigurationTarget.Global),
                config.update('analysis.excludePatterns', undefined, vscode.ConfigurationTarget.Global),
                config.update('notifications.level', undefined, vscode.ConfigurationTarget.Global),
                config.update('dashboard.autoOpen', undefined, vscode.ConfigurationTarget.Global)
            ];
            await Promise.all(resetPromises);
            await this.notificationManager.showInfo('Configuration reset to defaults');
        }
        catch (error) {
            await this.notificationManager.showError(`Failed to reset configuration: ${error}`);
        }
    }
}
exports.CommandManager = CommandManager;
//# sourceMappingURL=commandManager.js.map