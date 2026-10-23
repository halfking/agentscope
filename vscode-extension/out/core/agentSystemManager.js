"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AgentSystemManager = void 0;
const ws_1 = __importDefault(require("ws"));
const axios_1 = __importDefault(require("axios"));
class AgentSystemManager {
    constructor(eventBus, configManager, notificationManager) {
        this.eventBus = eventBus;
        this.configManager = configManager;
        this.notificationManager = notificationManager;
        this.wsClient = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000;
        this.agents = new Map();
        this.tasks = new Map();
        this.results = new Map();
        this.httpClient = this.createHttpClient();
        this.setupEventListeners();
    }
    createHttpClient() {
        const config = this.configManager.getBackendConfig();
        const baseURL = `${config.protocol}://${config.host}:${config.port}`;
        return axios_1.default.create({
            baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    setupEventListeners() {
        this.eventBus.on('configurationChanged', () => {
            this.updateConfiguration();
        });
    }
    updateConfiguration() {
        this.httpClient = this.createHttpClient();
        if (this.isConnected) {
            this.disconnect();
            setTimeout(() => this.connect(), 1000);
        }
    }
    async connect() {
        try {
            // 首先测试HTTP连接
            await this.httpClient.get('/health');
            // 建立WebSocket连接
            const config = this.configManager.getBackendConfig();
            const wsUrl = `ws://${config.host}:${config.port}/ws`;
            this.wsClient = new ws_1.default(wsUrl);
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
                this.wsClient.on('message', (data) => {
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
        }
        catch (error) {
            console.error('Failed to connect to AgentScope backend:', error);
            this.eventBus.emit('systemStatusChanged', 'error');
            throw error;
        }
    }
    disconnect() {
        if (this.wsClient) {
            this.wsClient.close();
            this.wsClient = null;
        }
        this.isConnected = false;
        this.eventBus.emit('systemStatusChanged', 'disconnected');
    }
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.notificationManager.showWarning(`Connection lost. Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => {
                this.connect().catch(error => {
                    console.error('Reconnection failed:', error);
                });
            }, this.reconnectInterval);
        }
        else {
            this.notificationManager.showError('Failed to reconnect to AgentScope backend');
        }
    }
    handleWebSocketMessage(data) {
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
        }
        catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    updateAgentStatus(agentStatus) {
        this.agents.set(agentStatus.agentId, agentStatus);
        this.eventBus.emit('agentStatusUpdated', agentStatus);
    }
    updateTask(task) {
        this.tasks.set(task.id, task);
        this.eventBus.emit('taskUpdated', task);
    }
    updateTaskResult(result) {
        this.results.set(result.taskId, result);
        this.eventBus.emit('taskResultUpdated', result);
    }
    handleSystemNotification(notification) {
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
    async getAgents() {
        try {
            const response = await this.httpClient.get('/api/agents');
            const agents = response.data;
            // 更新本地缓存
            agents.forEach((agent) => {
                this.agents.set(agent.agentId, agent);
            });
            return agents;
        }
        catch (error) {
            console.error('Failed to get agents:', error);
            throw error;
        }
    }
    async submitTask(task) {
        try {
            const response = await this.httpClient.post('/api/tasks', task);
            const taskId = response.data.taskId;
            this.notificationManager.showInfo(`Task submitted: ${task.title}`);
            return taskId;
        }
        catch (error) {
            console.error('Failed to submit task:', error);
            this.notificationManager.showError(`Failed to submit task: ${task.title}`);
            throw error;
        }
    }
    async getTaskResult(taskId) {
        try {
            const response = await this.httpClient.get(`/api/tasks/${taskId}/result`);
            return response.data;
        }
        catch (error) {
            console.error('Failed to get task result:', error);
            return null;
        }
    }
    async cancelTask(taskId) {
        try {
            await this.httpClient.delete(`/api/tasks/${taskId}`);
            this.notificationManager.showInfo('Task cancelled');
            return true;
        }
        catch (error) {
            console.error('Failed to cancel task:', error);
            this.notificationManager.showError('Failed to cancel task');
            return false;
        }
    }
    async analyzeProject(projectPath) {
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
    async qualityCheck(filePath) {
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
    async securityScan(filePath) {
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
    getCachedAgents() {
        return Array.from(this.agents.values());
    }
    getCachedTasks() {
        return Array.from(this.tasks.values());
    }
    getCachedResults() {
        return Array.from(this.results.values());
    }
    getTaskById(taskId) {
        return this.tasks.get(taskId);
    }
    getResultById(taskId) {
        return this.results.get(taskId);
    }
    isSystemConnected() {
        return this.isConnected;
    }
}
exports.AgentSystemManager = AgentSystemManager;
//# sourceMappingURL=agentSystemManager.js.map