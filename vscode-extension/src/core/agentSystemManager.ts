import * as vscode from 'vscode';
import WebSocket from 'ws';
import axios, { AxiosInstance } from 'axios';
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

export class AgentSystemManager {
    private httpClient: AxiosInstance;
    private wsClient: WebSocket | null = null;
    private isConnected = false;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectInterval = 5000;
    
    private agents: Map<string, AgentStatus> = new Map();
    private tasks: Map<string, TaskInfo> = new Map();
    private results: Map<string, TaskResult> = new Map();
    
    constructor(
        private eventBus: EventBus,
        private configManager: ConfigurationManager,
        private notificationManager: NotificationManager
    ) {
        this.httpClient = this.createHttpClient();
        this.setupEventListeners();
    }
    
    private createHttpClient(): AxiosInstance {
        const config = this.configManager.getBackendConfig();
        const baseURL = `${config.protocol}://${config.host}:${config.port}`;
        
        return axios.create({
            baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    
    private setupEventListeners() {
        this.eventBus.on('configurationChanged', () => {
            this.updateConfiguration();
        });
    }
    
    public updateConfiguration() {
        this.httpClient = this.createHttpClient();
        if (this.isConnected) {
            this.disconnect();
            setTimeout(() => this.connect(), 1000);
        }
    }
    
    public async connect(): Promise<boolean> {
        try {
            // 首先测试HTTP连接
            await this.httpClient.get('/health');
            
            // 建立WebSocket连接
            const config = this.configManager.getBackendConfig();
            const wsUrl = `ws://${config.host}:${config.port}/ws`;
            
            this.wsClient = new WebSocket(wsUrl);
            
            return new Promise((resolve, reject) => {
                if (!this.wsClient) {
                    reject(new Error('WebSocket client not initialized'));
                    return;
                }
                
                this.wsClient.on('open', () => {
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.eventBus.emit('systemStatusChanged', 'active');
                    this.notificationManager.showInfo('Connected to AgentScope backend');
                    resolve(true);
                });
                
                this.wsClient.on('message', (data: WebSocket.Data) => {
                    this.handleWebSocketMessage(data);
                });
                
                this.wsClient.on('close', () => {
                    this.isConnected = false;
                    this.eventBus.emit('systemStatusChanged', 'disconnected');
                    this.attemptReconnect();
                });
                
                this.wsClient.on('error', (error) => {
                    console.error('WebSocket error:', error);
                    this.eventBus.emit('systemStatusChanged', 'error');
                    reject(error);
                });
                
                // 设置连接超时
                setTimeout(() => {
                    if (!this.isConnected) {
                        reject(new Error('Connection timeout'));
                    }
                }, 10000);
            });
            
        } catch (error) {
            console.error('Failed to connect to AgentScope backend:', error);
            this.eventBus.emit('systemStatusChanged', 'error');
            throw error;
        }
    }
    
    public disconnect() {
        if (this.wsClient) {
            this.wsClient.close();
            this.wsClient = null;
        }
        this.isConnected = false;
        this.eventBus.emit('systemStatusChanged', 'disconnected');
    }
    
    private attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.notificationManager.showWarning(
                `Connection lost. Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
            );
            
            setTimeout(() => {
                this.connect().catch(error => {
                    console.error('Reconnection failed:', error);
                });
            }, this.reconnectInterval);
        } else {
            this.notificationManager.showError('Failed to reconnect to AgentScope backend');
        }
    }
    
    private handleWebSocketMessage(data: WebSocket.Data) {
        try {
            const message = JSON.parse(data.toString());
            
            switch (message.type) {
                case 'agent_status_update':
                    this.updateAgentStatus(message.data);
                    break;
                case 'task_update':
                    this.updateTask(message.data);
                    break;
                case 'task_result':
                    this.updateTaskResult(message.data);
                    break;
                case 'system_notification':
                    this.handleSystemNotification(message.data);
                    break;
                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    private updateAgentStatus(agentStatus: AgentStatus) {
        this.agents.set(agentStatus.agentId, agentStatus);
        this.eventBus.emit('agentStatusUpdated', agentStatus);
    }
    
    private updateTask(task: TaskInfo) {
        this.tasks.set(task.id, task);
        this.eventBus.emit('taskUpdated', task);
    }
    
    private updateTaskResult(result: TaskResult) {
        this.results.set(result.taskId, result);
        this.eventBus.emit('taskResultUpdated', result);
    }
    
    private handleSystemNotification(notification: any) {
        const { level, message } = notification;
        switch (level) {
            case 'error':
                this.notificationManager.showError(message);
                break;
            case 'warning':
                this.notificationManager.showWarning(message);
                break;
            case 'info':
                this.notificationManager.showInfo(message);
                break;
        }
    }
    
    // API方法
    public async getAgents(): Promise<AgentStatus[]> {
        try {
            const response = await this.httpClient.get('/api/agents');
            const agents = response.data;
            
            // 更新本地缓存
            agents.forEach((agent: AgentStatus) => {
                this.agents.set(agent.agentId, agent);
            });
            
            return agents;
        } catch (error) {
            console.error('Failed to get agents:', error);
            throw error;
        }
    }
    
    public async submitTask(task: Omit<TaskInfo, 'id' | 'status' | 'createdAt'>): Promise<string> {
        try {
            const response = await this.httpClient.post('/api/tasks', task);
            const taskId = response.data.taskId;
            
            this.notificationManager.showInfo(`Task submitted: ${task.title}`);
            return taskId;
        } catch (error) {
            console.error('Failed to submit task:', error);
            this.notificationManager.showError(`Failed to submit task: ${task.title}`);
            throw error;
        }
    }
    
    public async getTaskResult(taskId: string): Promise<TaskResult | null> {
        try {
            const response = await this.httpClient.get(`/api/tasks/${taskId}/result`);
            return response.data;
        } catch (error) {
            console.error('Failed to get task result:', error);
            return null;
        }
    }
    
    public async cancelTask(taskId: string): Promise<boolean> {
        try {
            await this.httpClient.delete(`/api/tasks/${taskId}`);
            this.notificationManager.showInfo('Task cancelled');
            return true;
        } catch (error) {
            console.error('Failed to cancel task:', error);
            this.notificationManager.showError('Failed to cancel task');
            return false;
        }
    }
    
    public async analyzeProject(projectPath: string): Promise<string> {
        const task = {
            type: 'code_analysis',
            title: 'Project Analysis',
            description: `Analyze project structure and dependencies for: ${projectPath}`,
            parameters: {
                project_path: projectPath,
                analysis_type: 'comprehensive'
            },
            priority: 5
        };
        
        return this.submitTask(task);
    }
    
    public async qualityCheck(filePath: string): Promise<string> {
        const task = {
            type: 'quality_check',
            title: 'Code Quality Check',
            description: `Perform quality analysis for: ${filePath}`,
            parameters: {
                file_path: filePath,
                check_types: ['static_analysis', 'coding_standards']
            },
            priority: 3
        };
        
        return this.submitTask(task);
    }
    
    public async securityScan(filePath: string): Promise<string> {
        const task = {
            type: 'security_scan',
            title: 'Security Vulnerability Scan',
            description: `Scan for security vulnerabilities in: ${filePath}`,
            parameters: {
                file_path: filePath,
                scan_types: ['vulnerability_scan', 'secret_detection']
            },
            priority: 1
        };
        
        return this.submitTask(task);
    }
    
    // 获取缓存数据
    public getCachedAgents(): AgentStatus[] {
        return Array.from(this.agents.values());
    }
    
    public getCachedTasks(): TaskInfo[] {
        return Array.from(this.tasks.values());
    }
    
    public getCachedResults(): TaskResult[] {
        return Array.from(this.results.values());
    }
    
    public getTaskById(taskId: string): TaskInfo | undefined {
        return this.tasks.get(taskId);
    }
    
    public getResultById(taskId: string): TaskResult | undefined {
        return this.results.get(taskId);
    }
    
    public isSystemConnected(): boolean {
        return this.isConnected;
    }
}
