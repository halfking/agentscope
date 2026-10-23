import * as vscode from 'vscode';
import { AgentSystemManager } from '../core/agentSystemManager';
import { EventBus } from '../core/eventBus';
export declare class DashboardPanel {
    private readonly extensionContext;
    private readonly agentSystemManager;
    private readonly eventBus;
    static currentPanel: DashboardPanel | undefined;
    private readonly _panel;
    private _disposables;
    static createOrShow(extensionContext: vscode.ExtensionContext, agentSystemManager: AgentSystemManager, eventBus: EventBus): void;
    private constructor();
    private setupWebviewMessageHandling;
    private setupEventListeners;
    private updateDashboard;
    private updateAgentStatus;
    private updateTaskQueue;
    private updateResults;
    private startSystem;
    private stopSystem;
    private submitTask;
    private cancelTask;
    private viewTaskResult;
    private exportResults;
    private getWebviewContent;
    dispose(): void;
}
//# sourceMappingURL=dashboardPanel.d.ts.map