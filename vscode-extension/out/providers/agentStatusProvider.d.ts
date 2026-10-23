import * as vscode from 'vscode';
import { AgentSystemManager, AgentStatus } from '../core/agentSystemManager';
import { EventBus } from '../core/eventBus';
export declare class AgentStatusItem extends vscode.TreeItem {
    readonly agentStatus: AgentStatus;
    readonly collapsibleState: vscode.TreeItemCollapsibleState;
    constructor(agentStatus: AgentStatus, collapsibleState: vscode.TreeItemCollapsibleState);
    private getTooltip;
    private getDescription;
    private getIcon;
}
export declare class AgentMetricItem extends vscode.TreeItem {
    readonly label: string;
    readonly value: string;
    readonly description?: string | undefined;
    constructor(label: string, value: string, description?: string | undefined);
}
export declare class AgentStatusProvider implements vscode.TreeDataProvider<AgentStatusItem | AgentMetricItem> {
    private agentSystemManager;
    private eventBus;
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<AgentStatusItem | AgentMetricItem | undefined | null | void>;
    private agents;
    private refreshInterval;
    constructor(agentSystemManager: AgentSystemManager, eventBus: EventBus);
    private setupEventListeners;
    private startAutoRefresh;
    private updateAgentStatus;
    refresh(): Promise<void>;
    getTreeItem(element: AgentStatusItem | AgentMetricItem): vscode.TreeItem;
    getChildren(element?: AgentStatusItem | AgentMetricItem): Thenable<(AgentStatusItem | AgentMetricItem)[]>;
    private getAgentItems;
    private getMetricItems;
    getAgentCount(): number;
    getActiveAgentCount(): number;
    getIdleAgentCount(): number;
    getErrorAgentCount(): number;
    getAgentByRole(role: string): AgentStatus | undefined;
    getAgentById(agentId: string): AgentStatus | undefined;
    getSystemHealth(): {
        status: 'healthy' | 'warning' | 'error';
        message: string;
        details: any;
    };
    dispose(): void;
}
//# sourceMappingURL=agentStatusProvider.d.ts.map