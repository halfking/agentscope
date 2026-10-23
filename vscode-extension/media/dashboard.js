// AgentScope Dashboard JavaScript

(function() {
    'use strict';

    // VS Code API
    const vscode = acquireVsCodeApi();

    // 状态管理
    let systemStatus = 'disconnected';
    let agents = [];
    let tasks = [];
    let results = [];

    // DOM元素
    let statusIndicator, statusText, toggleSystemBtn;
    let agentList, taskList, resultsList;
    let taskModal, resultModal;

    // 初始化
    document.addEventListener('DOMContentLoaded', function() {
        initializeElements();
        setupEventListeners();
        requestInitialData();
    });

    function initializeElements() {
        // 状态元素
        statusIndicator = document.getElementById('status-indicator');
        statusText = document.getElementById('status-text');
        toggleSystemBtn = document.getElementById('toggle-system');

        // 列表元素
        agentList = document.getElementById('agent-list');
        taskList = document.getElementById('task-list');
        resultsList = document.getElementById('results-list');

        // 模态框元素
        taskModal = document.getElementById('task-modal');
        resultModal = document.getElementById('result-modal');
    }

    function setupEventListeners() {
        // 系统控制按钮
        toggleSystemBtn.addEventListener('click', toggleSystem);

        // 刷新按钮
        document.getElementById('refresh-btn').addEventListener('click', () => {
            vscode.postMessage({ command: 'refresh' });
        });

        // 新任务按钮
        document.getElementById('new-task-btn').addEventListener('click', showTaskModal);

        // 导出结果按钮
        document.getElementById('export-btn').addEventListener('click', () => {
            vscode.postMessage({ command: 'exportResults' });
        });

        // 快捷操作按钮
        document.getElementById('analyze-project-btn').addEventListener('click', () => {
            showQuickTaskDialog('code_analysis', 'Project Analysis');
        });

        document.getElementById('quality-check-btn').addEventListener('click', () => {
            showQuickTaskDialog('quality_check', 'Quality Check');
        });

        document.getElementById('security-scan-btn').addEventListener('click', () => {
            showQuickTaskDialog('security_scan', 'Security Scan');
        });

        document.getElementById('test-analysis-btn').addEventListener('click', () => {
            showQuickTaskDialog('test_analysis', 'Test Analysis');
        });

        // 任务表单提交
        document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);

        // 模态框关闭
        document.getElementById('cancel-task-btn').addEventListener('click', hideTaskModal);
        document.getElementById('close-result-btn').addEventListener('click', hideResultModal);

        // 点击模态框外部关闭
        taskModal.addEventListener('click', (e) => {
            if (e.target === taskModal) hideTaskModal();
        });

        resultModal.addEventListener('click', (e) => {
            if (e.target === resultModal) hideResultModal();
        });
    }

    function requestInitialData() {
        vscode.postMessage({ command: 'refresh' });
    }

    // 消息处理
    window.addEventListener('message', event => {
        const message = event.data;

        switch (message.command) {
            case 'updateDashboard':
                updateDashboard(message.data);
                break;
            case 'updateAgents':
                updateAgents(message.data);
                break;
            case 'updateTasks':
                updateTasks(message.data);
                break;
            case 'updateResults':
                updateResults(message.data);
                break;
            case 'taskSubmitted':
                handleTaskSubmitted(message.data);
                break;
            case 'taskCancelled':
                handleTaskCancelled(message.data);
                break;
            case 'showTaskResult':
                showTaskResult(message.data);
                break;
        }
    });

    function updateDashboard(data) {
        systemStatus = data.systemStatus;
        agents = data.agents || [];
        tasks = data.tasks || [];
        results = data.results || [];

        updateSystemStatus();
        updateAgents(agents);
        updateTasks(tasks);
        updateResults(results);
    }

    function updateSystemStatus() {
        statusIndicator.className = `status-indicator ${systemStatus}`;
        
        switch (systemStatus) {
            case 'connected':
                statusText.textContent = 'Connected';
                toggleSystemBtn.textContent = 'Stop System';
                toggleSystemBtn.className = 'btn btn-danger';
                break;
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                toggleSystemBtn.textContent = 'Start System';
                toggleSystemBtn.className = 'btn btn-primary';
                break;
            case 'error':
                statusText.textContent = 'Error';
                toggleSystemBtn.textContent = 'Restart System';
                toggleSystemBtn.className = 'btn btn-warning';
                break;
        }
    }

    function updateAgents(agentData) {
        agents = agentData;
        agentList.innerHTML = '';

        if (agents.length === 0) {
            agentList.innerHTML = '<div class="empty-state">No agents available</div>';
            return;
        }

        agents.forEach(agent => {
            const agentElement = createAgentElement(agent);
            agentList.appendChild(agentElement);
        });
    }

    function createAgentElement(agent) {
        const div = document.createElement('div');
        div.className = `agent-item ${agent.status}`;
        
        const statusIcon = getStatusIcon(agent.status);
        const successRate = agent.performance_metrics?.success_rate 
            ? (agent.performance_metrics.success_rate * 100).toFixed(1) + '%'
            : 'N/A';

        div.innerHTML = `
            <div class="agent-header">
                <span class="agent-icon">${statusIcon}</span>
                <span class="agent-name">${agent.role}</span>
                <span class="agent-status">${agent.status}</span>
            </div>
            <div class="agent-details">
                <div class="agent-metric">
                    <span class="metric-label">Success Rate:</span>
                    <span class="metric-value">${successRate}</span>
                </div>
                ${agent.current_task ? `
                    <div class="agent-current-task">
                        <span class="task-label">Current Task:</span>
                        <span class="task-id">${agent.current_task}</span>
                    </div>
                ` : ''}
                <div class="agent-updated">
                    Last updated: ${formatTimestamp(agent.last_update)}
                </div>
            </div>
        `;

        return div;
    }

    function updateTasks(taskData) {
        tasks = taskData;
        taskList.innerHTML = '';

        if (tasks.length === 0) {
            taskList.innerHTML = '<div class="empty-state">No tasks in queue</div>';
            return;
        }

        tasks.forEach(task => {
            const taskElement = createTaskElement(task);
            taskList.appendChild(taskElement);
        });
    }

    function createTaskElement(task) {
        const div = document.createElement('div');
        div.className = `task-item ${task.status}`;
        
        const priorityClass = getPriorityClass(task.priority);
        const statusIcon = getTaskStatusIcon(task.status);

        div.innerHTML = `
            <div class="task-header">
                <span class="task-icon">${statusIcon}</span>
                <span class="task-title">${task.title}</span>
                <span class="task-priority ${priorityClass}">P${task.priority}</span>
            </div>
            <div class="task-details">
                <div class="task-type">${task.type}</div>
                <div class="task-time">
                    Created: ${formatTimestamp(task.created_at)}
                    ${task.completed_at ? `<br>Completed: ${formatTimestamp(task.completed_at)}` : ''}
                </div>
                <div class="task-actions">
                    ${task.status === 'pending' || task.status === 'running' ? `
                        <button class="btn btn-sm btn-danger" onclick="cancelTask('${task.task_id}')">Cancel</button>
                    ` : ''}
                    ${task.status === 'completed' ? `
                        <button class="btn btn-sm btn-primary" onclick="viewTaskResult('${task.task_id}')">View Result</button>
                    ` : ''}
                </div>
            </div>
        `;

        return div;
    }

    function updateResults(resultData) {
        results = resultData;
        resultsList.innerHTML = '';

        if (results.length === 0) {
            resultsList.innerHTML = '<div class="empty-state">No results available</div>';
            return;
        }

        results.forEach(result => {
            const resultElement = createResultElement(result);
            resultsList.appendChild(resultElement);
        });
    }

    function createResultElement(result) {
        const div = document.createElement('div');
        div.className = `result-item ${result.status}`;
        
        const statusIcon = getTaskStatusIcon(result.status);
        const executionTime = result.execution_time ? `${result.execution_time.toFixed(2)}s` : 'N/A';

        div.innerHTML = `
            <div class="result-header">
                <span class="result-icon">${statusIcon}</span>
                <span class="result-task-id">${result.task_id}</span>
                <span class="result-status">${result.status}</span>
            </div>
            <div class="result-details">
                <div class="result-time">
                    Execution Time: ${executionTime}
                </div>
                ${result.completed_at ? `
                    <div class="result-completed">
                        Completed: ${formatTimestamp(result.completed_at)}
                    </div>
                ` : ''}
                ${result.error ? `
                    <div class="result-error">
                        Error: ${result.error}
                    </div>
                ` : ''}
                <div class="result-actions">
                    <button class="btn btn-sm btn-primary" onclick="viewTaskResult('${result.task_id}')">View Details</button>
                </div>
            </div>
        `;

        return div;
    }

    // 系统控制
    function toggleSystem() {
        if (systemStatus === 'connected') {
            vscode.postMessage({ command: 'stopSystem' });
        } else {
            vscode.postMessage({ command: 'startSystem' });
        }
    }

    // 任务管理
    function showTaskModal() {
        taskModal.classList.remove('hidden');
    }

    function hideTaskModal() {
        taskModal.classList.add('hidden');
        document.getElementById('task-form').reset();
    }

    function showQuickTaskDialog(taskType, taskTitle) {
        document.getElementById('task-type').value = taskType;
        document.getElementById('task-title').value = taskTitle;
        showTaskModal();
    }

    function handleTaskSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const taskData = {
            type: formData.get('task-type'),
            title: formData.get('task-title'),
            description: formData.get('task-description'),
            priority: parseInt(formData.get('task-priority')),
            parameters: {}
        };

        vscode.postMessage({ 
            command: 'submitTask', 
            data: taskData 
        });
    }

    function handleTaskSubmitted(data) {
        if (data.success) {
            hideTaskModal();
            showNotification('Task submitted successfully', 'success');
        } else {
            showNotification(`Failed to submit task: ${data.error}`, 'error');
        }
    }

    function cancelTask(taskId) {
        if (confirm('Are you sure you want to cancel this task?')) {
            vscode.postMessage({ 
                command: 'cancelTask', 
                taskId: taskId 
            });
        }
    }

    function handleTaskCancelled(data) {
        if (data.success) {
            showNotification('Task cancelled successfully', 'success');
        } else {
            showNotification(`Failed to cancel task: ${data.error}`, 'error');
        }
    }

    function viewTaskResult(taskId) {
        vscode.postMessage({ 
            command: 'viewTaskResult', 
            taskId: taskId 
        });
    }

    function showTaskResult(result) {
        const content = document.getElementById('result-content');
        content.innerHTML = `
            <div class="result-detail">
                <h4>Task ID: ${result.task_id}</h4>
                <p><strong>Status:</strong> ${result.status}</p>
                ${result.execution_time ? `<p><strong>Execution Time:</strong> ${result.execution_time.toFixed(2)}s</p>` : ''}
                ${result.completed_at ? `<p><strong>Completed:</strong> ${formatTimestamp(result.completed_at)}</p>` : ''}
                ${result.error ? `<div class="error-message"><strong>Error:</strong> ${result.error}</div>` : ''}
                ${result.result ? `
                    <div class="result-data">
                        <strong>Result:</strong>
                        <pre>${JSON.stringify(result.result, null, 2)}</pre>
                    </div>
                ` : ''}
                ${result.artifacts && result.artifacts.length > 0 ? `
                    <div class="result-artifacts">
                        <strong>Artifacts:</strong>
                        <ul>
                            ${result.artifacts.map(artifact => `<li>${artifact}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        resultModal.classList.remove('hidden');
    }

    function hideResultModal() {
        resultModal.classList.add('hidden');
    }

    // 工具函数
    function getStatusIcon(status) {
        switch (status) {
            case 'idle': return '🟢';
            case 'busy': return '🟡';
            case 'error': return '🔴';
            default: return '⚪';
        }
    }

    function getTaskStatusIcon(status) {
        switch (status) {
            case 'pending': return '⏳';
            case 'running': return '🔄';
            case 'completed': return '✅';
            case 'failed': return '❌';
            case 'cancelled': return '⏹️';
            default: return '❓';
        }
    }

    function getPriorityClass(priority) {
        if (priority <= 2) return 'priority-high';
        if (priority <= 5) return 'priority-normal';
        return 'priority-low';
    }

    function formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // 全局函数（供HTML调用）
    window.cancelTask = cancelTask;
    window.viewTaskResult = viewTaskResult;

})();
