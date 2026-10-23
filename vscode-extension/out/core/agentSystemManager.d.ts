import { EventBus } from './eventBus';
import { ConfigurationManager } from './configurationManager';
import { NotificationManager } from './notificationManager';
export interface AgentStatus {
    agentId: string;
    role: string;
    status: string;
    currentTask?: string;
    lastUpdate: string;
    performanceMetrics: Record<string, number>;
}
export interface TaskInfo {
    id: string;
    type: string;
    title: string;
    description: string;
    status: string;
    agentId?: string;
    createdAt: string;
    completedAt?: string;
    priority: number;
}
export interface TaskResult {
    taskId: string;
    status: string;
    result?: any;
    error?: string;
    executionTime?: number;
    completedAt?: string;
    artifacts?: string[];
}
export declare class AgentSystemManager {
    private eventBus;
    private configManager;
    private notificationManager;
    private httpClient;
    private wsClient;
    private isConnected;
    private reconnectAttempts;
    private maxReconnectAttempts;
    private reconnectInterval;
    private agents;
    private tasks;
    private results;
    constructor(eventBus: EventBus, configManager: ConfigurationManager, notificationManager: NotificationManager);
    private createHttpClient;
    private setupEventListeners;
    updateConfiguration(): void;
    connect(): Promise<boolean>;
    disconnect(): void;
    private attemptReconnect;
    private handleWebSocketMessage;
    private updateAgentStatus;
    private updateTask;
    private updateTaskResult;
    private handleSystemNotification;
    getAgents(): Promise<AgentStatus[]>;
    submitTask(task: Omit<TaskInfo, 'id' | 'status' | 'createdAt'>): Promise<string>;
    getTaskResult(taskId: string): Promise<TaskResult | null>;
    cancelTask(taskId: string): Promise<boolean>;
    analyzeProject(projectPath: string): Promise<string>;
    qualityCheck(filePath: string): Promise<string>;
    securityScan(filePath: string): Promise<string>;
    getCachedAgents(): AgentStatus[];
    getCachedTasks(): TaskInfo[];
    getCachedResults(): TaskResult[];
    getTaskById(taskId: string): TaskInfo | undefined;
    getResultById(taskId: string): TaskResult | undefined;
    isSystemConnected(): boolean;
}
//# sourceMappingURL=agentSystemManager.d.ts.map