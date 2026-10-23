import * as vscode from 'vscode';
import { AgentSystemManager, AgentStatus, TaskInfo, TaskResult } from '../core/agentSystemManager';
import { EventBus } from '../core/eventBus';

export class DashboardPanel {
    public static currentPanel: DashboardPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(
        extensionContext: vscode.ExtensionContext,
        agentSystemManager: AgentSystemManager,
        eventBus: EventBus
    ) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        if (DashboardPanel.currentPanel) {
            DashboardPanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'agentscope.dashboard',
            'AgentScope Dashboard',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionContext.extensionUri, 'media'),
                    vscode.Uri.joinPath(extensionContext.extensionUri, 'out', 'media')
                ]
            }
        );

        DashboardPanel.currentPanel = new DashboardPanel(
            panel,
            extensionContext,
            agentSystemManager,
            eventBus
        );
    }

    private constructor(
        panel: vscode.WebviewPanel,
        private readonly extensionContext: vscode.ExtensionContext,
        private readonly agentSystemManager: AgentSystemManager,
        private readonly eventBus: EventBus
    ) {
        this._panel = panel;
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.html = this.getWebviewContent();
        this.setupWebviewMessageHandling();
        this.setupEventListeners();
        
        // 初始化数据
        this.updateDashboard();
    }

    private setupWebviewMessageHandling() {
        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'refresh':
                        await this.updateDashboard();
                        break;
                    case 'startSystem':
                        await this.startSystem();
                        break;
                    case 'stopSystem':
                        await this.stopSystem();
                        break;
                    case 'submitTask':
                        await this.submitTask(message.data);
                        break;
                    case 'cancelTask':
                        await this.cancelTask(message.taskId);
                        break;
                    case 'viewTaskResult':
                        await this.viewTaskResult(message.taskId);
                        break;
                    case 'exportResults':
                        await this.exportResults();
                        break;
                }
            },
            null,
            this._disposables
        );
    }

    private setupEventListeners() {
        this.eventBus.on('systemStatusChanged', () => {
            this.updateDashboard();
        });

        this.eventBus.on('agentStatusUpdated', () => {
            this.updateAgentStatus();
        });

        this.eventBus.on('taskUpdated', () => {
            this.updateTaskQueue();
        });

        this.eventBus.on('taskResultUpdated', () => {
            this.updateResults();
        });
    }

    private async updateDashboard() {
        const systemStatus = this.agentSystemManager.isSystemConnected() ? 'connected' : 'disconnected';
        const agents = this.agentSystemManager.getCachedAgents();
        const tasks = this.agentSystemManager.getCachedTasks();
        const results = this.agentSystemManager.getCachedResults();

        this._panel.webview.postMessage({
            command: 'updateDashboard',
            data: {
                systemStatus,
                agents,
                tasks,
                results,
                timestamp: new Date().toISOString()
            }
        });
    }

    private async updateAgentStatus() {
        const agents = this.agentSystemManager.getCachedAgents();
        this._panel.webview.postMessage({
            command: 'updateAgents',
            data: agents
        });
    }

    private async updateTaskQueue() {
        const tasks = this.agentSystemManager.getCachedTasks();
        this._panel.webview.postMessage({
            command: 'updateTasks',
            data: tasks
        });
    }

    private async updateResults() {
        const results = this.agentSystemManager.getCachedResults();
        this._panel.webview.postMessage({
            command: 'updateResults',
            data: results
        });
    }

    private async startSystem() {
        try {
            await this.agentSystemManager.connect();
            vscode.window.showInformationMessage('AgentScope system started successfully');
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to start system: ${error}`);
        }
    }

    private async stopSystem() {
        this.agentSystemManager.disconnect();
        vscode.window.showInformationMessage('AgentScope system stopped');
    }

    private async submitTask(taskData: any) {
        try {
            const taskId = await this.agentSystemManager.submitTask(taskData);
            this._panel.webview.postMessage({
                command: 'taskSubmitted',
                data: { taskId, success: true }
            });
        } catch (error) {
            this._panel.webview.postMessage({
                command: 'taskSubmitted',
                data: { success: false, error: (error as any)?.message || String(error) }
            });
        }
    }

    private async cancelTask(taskId: string) {
        try {
            const success = await this.agentSystemManager.cancelTask(taskId);
            this._panel.webview.postMessage({
                command: 'taskCancelled',
                data: { taskId, success }
            });
        } catch (error) {
            this._panel.webview.postMessage({
                command: 'taskCancelled',
                data: { taskId, success: false, error: (error as any)?.message || String(error) }
            });
        }
    }

    private async viewTaskResult(taskId: string) {
        const result = this.agentSystemManager.getResultById(taskId);
        if (result) {
            this._panel.webview.postMessage({
                command: 'showTaskResult',
                data: result
            });
        }
    }

    private async exportResults() {
        const results = this.agentSystemManager.getCachedResults();
        const exportData = {
            timestamp: new Date().toISOString(),
            results: results
        };

        const saveUri = await vscode.window.showSaveDialog({
            defaultUri: vscode.Uri.file('agentscope-results.json'),
            filters: {
                'JSON files': ['json']
            }
        });

        if (saveUri) {
            const content = JSON.stringify(exportData, null, 2);
            await vscode.workspace.fs.writeFile(saveUri, Buffer.from(content, 'utf8'));
            vscode.window.showInformationMessage('Results exported successfully');
        }
    }

    private getWebviewContent(): string {
        const scriptUri = this._panel.webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionContext.extensionUri, 'media', 'dashboard.js')
        );
        const styleUri = this._panel.webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionContext.extensionUri, 'media', 'dashboard.css')
        );

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentScope Dashboard</title>
    <link href="${styleUri}" rel="stylesheet">
</head>
<body>
    <div id="app">
        <header class="dashboard-header">
            <h1>AgentScope Multi-Agent Workflow</h1>
            <div class="system-status">
                <span id="status-indicator" class="status-indicator disconnected"></span>
                <span id="status-text">Disconnected</span>
                <button id="toggle-system" class="btn btn-primary">Start System</button>
            </div>
        </header>

        <main class="dashboard-main">
            <div class="dashboard-grid">
                <!-- Agent Status Panel -->
                <section class="panel agent-status-panel">
                    <h2>Agent Status</h2>
                    <div id="agent-list" class="agent-list">
                        <!-- Agents will be populated here -->
                    </div>
                </section>

                <!-- Task Queue Panel -->
                <section class="panel task-queue-panel">
                    <h2>Task Queue</h2>
                    <div class="task-controls">
                        <button id="new-task-btn" class="btn btn-secondary">New Task</button>
                        <button id="refresh-btn" class="btn btn-secondary">Refresh</button>
                    </div>
                    <div id="task-list" class="task-list">
                        <!-- Tasks will be populated here -->
                    </div>
                </section>

                <!-- Results Panel -->
                <section class="panel results-panel">
                    <h2>Analysis Results</h2>
                    <div class="results-controls">
                        <button id="export-btn" class="btn btn-secondary">Export Results</button>
                        <button id="clear-results-btn" class="btn btn-secondary">Clear</button>
                    </div>
                    <div id="results-list" class="results-list">
                        <!-- Results will be populated here -->
                    </div>
                </section>

                <!-- Quick Actions Panel -->
                <section class="panel quick-actions-panel">
                    <h2>Quick Actions</h2>
                    <div class="quick-actions">
                        <button id="analyze-project-btn" class="btn btn-action">Analyze Project</button>
                        <button id="quality-check-btn" class="btn btn-action">Quality Check</button>
                        <button id="security-scan-btn" class="btn btn-action">Security Scan</button>
                        <button id="test-analysis-btn" class="btn btn-action">Test Analysis</button>
                    </div>
                </section>
            </div>
        </main>

        <!-- Task Creation Modal -->
        <div id="task-modal" class="modal hidden">
            <div class="modal-content">
                <h3>Create New Task</h3>
                <form id="task-form">
                    <div class="form-group">
                        <label for="task-type">Task Type:</label>
                        <select id="task-type" required>
                            <option value="code_analysis">Code Analysis</option>
                            <option value="quality_check">Quality Check</option>
                            <option value="security_scan">Security Scan</option>
                            <option value="test_analysis">Test Analysis</option>
                            <option value="architecture_review">Architecture Review</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="task-title">Title:</label>
                        <input type="text" id="task-title" required>
                    </div>
                    <div class="form-group">
                        <label for="task-description">Description:</label>
                        <textarea id="task-description" rows="3"></textarea>
                    </div>
                    <div class="form-group">
                        <label for="task-priority">Priority:</label>
                        <select id="task-priority">
                            <option value="1">Critical</option>
                            <option value="3">High</option>
                            <option value="5" selected>Normal</option>
                            <option value="7">Low</option>
                        </select>
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Create Task</button>
                        <button type="button" id="cancel-task-btn" class="btn btn-secondary">Cancel</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Result Detail Modal -->
        <div id="result-modal" class="modal hidden">
            <div class="modal-content large">
                <h3>Task Result Details</h3>
                <div id="result-content">
                    <!-- Result details will be populated here -->
                </div>
                <div class="form-actions">
                    <button id="close-result-btn" class="btn btn-secondary">Close</button>
                </div>
            </div>
        </div>
    </div>

    <script src="${scriptUri}"></script>
</body>
</html>`;
    }

    public dispose() {
        DashboardPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}
