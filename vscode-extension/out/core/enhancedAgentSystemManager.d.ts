/**
 * 增强的智能体系统管理器 - 集成Augment监听和处理能力
 */
import * as vscode from 'vscode';
import { AgentSystemManager } from './agentSystemManager';
export declare class EnhancedAgentSystemManager extends AgentSystemManager {
    private augmentWatcher;
    private augmentProcessor;
    private augmentEnabled;
    constructor(eventBus: any, configManager: any, notificationManager: any);
    initialize(): Promise<void>;
    private initializeAugmentIntegration;
    private handleAugmentActivity;
    private sendAugmentTaskToBackend;
    private registerAugmentCommands;
    private enableAugmentIntegration;
    private disableAugmentIntegration;
    private detectCurrentAugmentActivity;
    private processAugmentCommand;
    private showAugmentStatus;
    protected handleBackendMessage(message: any): void;
    private handleAugmentTaskCompleted;
    private handleAugmentTaskFailed;
    private showAugmentTaskResults;
    private generateAugmentResultsHTML;
    private formatAugmentAnalysisResults;
    dispose(): Promise<void>;
    private augmentCommands;
    getAugmentCommands(): vscode.Disposable[];
}
//# sourceMappingURL=enhancedAgentSystemManager.d.ts.map