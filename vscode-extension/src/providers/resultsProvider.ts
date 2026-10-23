import * as vscode from 'vscode';
import { AgentSystemManager } from '../core/agentSystemManager';
import { EventBus } from '../core/eventBus';

export interface AnalysisResult {
    id: string;
    title: string;
    type: 'code-analysis' | 'security-scan' | 'quality-check' | 'project-analysis' | 'augment-task';
    status: 'success' | 'warning' | 'error' | 'info';
    agent: string;
    timestamp: Date;
    summary: string;
    details?: any;
    filePath?: string;
    lineNumber?: number;
    severity?: 'low' | 'medium' | 'high' | 'critical';
    recommendations?: string[];
}

export class ResultsProvider implements vscode.TreeDataProvider<AnalysisResult> {
    private _onDidChangeTreeData: vscode.EventEmitter<AnalysisResult | undefined | null | void> = new vscode.EventEmitter<AnalysisResult | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AnalysisResult | undefined | null | void> = this._onDidChangeTreeData.event;

    private results: AnalysisResult[] = [];
    private maxResults = 100; // 最大保存结果数量

    constructor(
        private agentSystemManager: AgentSystemManager,
        private eventBus: EventBus
    ) {
        this.setupEventListeners();
        this.loadInitialResults();
    }

    private setupEventListeners(): void {
        this.eventBus.on('analysisCompleted', (result: AnalysisResult) => {
            this.addResult(result);
        });

        this.eventBus.on('augmentTaskCompleted', (taskData: any) => {
            const result: AnalysisResult = {
                id: taskData.id || Date.now().toString(),
                title: taskData.title || 'Augment Task',
                type: 'augment-task',
                status: taskData.success ? 'success' : 'error',
                agent: 'Augment Integration',
                timestamp: new Date(),
                summary: taskData.summary || 'Augment task completed',
                details: taskData.details,
                filePath: taskData.filePath,
                recommendations: taskData.recommendations
            };
            this.addResult(result);
        });

        this.eventBus.on('systemStatusChanged', () => {
            this.loadInitialResults();
        });
    }

    private async loadInitialResults(): Promise<void> {
        try {
            // 从后端获取分析结果
            // const response = await this.agentSystemManager.sendRequest('/api/results');
            const response = null; // 暂时禁用，避免编译错误
            if (response && Array.isArray(response.results)) {
                this.results = response.results.map((result: any) => ({
                    id: result.id,
                    title: result.title || 'Analysis Result',
                    type: result.type || 'code-analysis',
                    status: result.status || 'info',
                    agent: result.agent || 'Unknown Agent',
                    timestamp: new Date(result.timestamp || Date.now()),
                    summary: result.summary || 'No summary available',
                    details: result.details,
                    filePath: result.file_path,
                    lineNumber: result.line_number,
                    severity: result.severity,
                    recommendations: result.recommendations
                }));
                this.refresh();
            }
        } catch (error) {
            console.error('Failed to load analysis results:', error);
            this.results = [];
            this.refresh();
        }
    }

    private addResult(result: AnalysisResult): void {
        this.results.unshift(result); // 新结果添加到开头
        
        // 限制结果数量
        if (this.results.length > this.maxResults) {
            this.results = this.results.slice(0, this.maxResults);
        }
        
        this.refresh();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: AnalysisResult): vscode.TreeItem {
        const item = new vscode.TreeItem(element.title, vscode.TreeItemCollapsibleState.None);
        
        // 设置图标
        switch (element.status) {
            case 'success':
                item.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('charts.green'));
                break;
            case 'warning':
                item.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('charts.yellow'));
                break;
            case 'error':
                item.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('charts.red'));
                break;
            case 'info':
                item.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('charts.blue'));
                break;
        }

        // 设置描述
        const timeAgo = this.getTimeAgo(element.timestamp);
        item.description = `${element.agent} • ${timeAgo}`;
        
        // 设置标签
        if (element.severity) {
            item.label = `${element.title} [${element.severity.toUpperCase()}]`;
        }

        // 设置工具提示
        const tooltipContent = [
            `**${element.title}**`,
            `**Type:** ${element.type}`,
            `**Status:** ${element.status}`,
            `**Agent:** ${element.agent}`,
            `**Time:** ${element.timestamp.toLocaleString()}`,
            element.severity ? `**Severity:** ${element.severity}` : '',
            element.filePath ? `**File:** ${element.filePath}` : '',
            element.lineNumber ? `**Line:** ${element.lineNumber}` : '',
            '',
            `**Summary:** ${element.summary}`
        ].filter(Boolean);

        if (element.recommendations && element.recommendations.length > 0) {
            tooltipContent.push('', '**Recommendations:**');
            element.recommendations.forEach(rec => {
                tooltipContent.push(`• ${rec}`);
            });
        }

        item.tooltip = new vscode.MarkdownString(tooltipContent.join('\n\n'));

        // 设置上下文值
        item.contextValue = `result-${element.type}-${element.status}`;

        // 设置命令
        item.command = {
            command: 'agentscope.showResultDetails',
            title: 'Show Details',
            arguments: [element]
        };

        return item;
    }

    getChildren(element?: AnalysisResult): Thenable<AnalysisResult[]> {
        if (!element) {
            // 返回根级别的结果，按时间排序（新的在前）
            return Promise.resolve(
                this.results.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
            );
        }
        
        return Promise.resolve([]);
    }

    getParent(element: AnalysisResult): vscode.ProviderResult<AnalysisResult> {
        return null;
    }

    // 辅助方法
    private getTimeAgo(date: Date): string {
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }

    // 公共方法
    public getResultCount(): number {
        return this.results.length;
    }

    public getResultsByType(type: string): AnalysisResult[] {
        return this.results.filter(r => r.type === type);
    }

    public getResultsByStatus(status: string): AnalysisResult[] {
        return this.results.filter(r => r.status === status);
    }

    public getResultsBySeverity(severity: string): AnalysisResult[] {
        return this.results.filter(r => r.severity === severity);
    }

    public clearResults(): void {
        this.results = [];
        this.refresh();
    }

    public clearResultsByType(type: string): void {
        this.results = this.results.filter(r => r.type !== type);
        this.refresh();
    }

    public exportResults(): string {
        return JSON.stringify(this.results, null, 2);
    }

    public getResultById(id: string): AnalysisResult | undefined {
        return this.results.find(r => r.id === id);
    }
}
