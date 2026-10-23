import * as vscode from 'vscode';
import { AgentSystemManager } from './agentSystemManager';
import { EventBus } from './eventBus';
import { NotificationManager } from './notificationManager';
export declare class CommandManager {
    private agentSystemManager;
    private eventBus;
    private notificationManager;
    constructor(agentSystemManager: AgentSystemManager, eventBus: EventBus, notificationManager: NotificationManager);
    startAgentSystem(): Promise<void>;
    stopAgentSystem(): Promise<void>;
    analyzeProject(uri?: vscode.Uri): Promise<void>;
    qualityCheck(uri?: vscode.Uri): Promise<void>;
    securityScan(uri?: vscode.Uri): Promise<void>;
    showDashboard(context: vscode.ExtensionContext): Promise<void>;
    configureAgents(): Promise<void>;
    viewTaskHistory(): Promise<void>;
    autoAnalyzeFile(uri: vscode.Uri): Promise<void>;
    private exportConfiguration;
    private importConfiguration;
    private resetConfiguration;
}
//# sourceMappingURL=commandManager.d.ts.map