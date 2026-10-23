/**
 * Augment命令处理器 - 将Augment指令转换为AgentScope任务
 */

import * as vscode from 'vscode';
import { AugmentActivity } from './augmentActivityWatcher';

export interface AgentScopeTask {
    id: string;
    type: string;
    title: string;
    description: string;
    parameters: any;
    priority: number;
    metadata?: any;
}

export interface ParsedIntent {
    type: string;
    parameters: any;
    confidence: number;
    target_files: string[];
    analysis_types: string[];
}

/**
 * Augment命令处理器
 */
export class AugmentCommandProcessor {
    private nlpPatterns: Map<string, RegExp[]> = new Map([
        ['code_analysis', [
            /分析.*代码/i,
            /检查.*文件/i,
            /analyze.*code/i,
            /review.*file/i,
            /代码.*分析/i,
            /文件.*检查/i,
            /look\s+at\s+this\s+code/i,
            /what\s+does\s+this\s+do/i,
            /explain\s+this\s+function/i,
            /解释.*函数/i,
            /这个.*代码.*做什么/i,
            /帮我.*看看.*代码/i
        ]],
        ['security_scan', [
            /安全.*扫描/i,
            /漏洞.*检测/i,
            /security.*scan/i,
            /vulnerability.*check/i,
            /安全.*检查/i,
            /漏洞.*分析/i,
            /check.*security/i,
            /find.*vulnerabilities/i,
            /sql.*injection/i,
            /xss.*attack/i,
            /硬编码.*密码/i,
            /hardcoded.*password/i,
            /安全.*问题/i,
            /security.*issues/i
        ]],
        ['quality_check', [
            /质量.*检查/i,
            /代码.*质量/i,
            /quality.*check/i,
            /code.*quality/i,
            /质量.*分析/i,
            /代码.*规范/i,
            /check.*style/i,
            /lint.*code/i,
            /format.*code/i,
            /代码.*风格/i,
            /编码.*规范/i,
            /best.*practices/i,
            /最佳.*实践/i
        ]],
        ['refactor_suggestion', [
            /重构.*建议/i,
            /优化.*代码/i,
            /refactor.*suggestion/i,
            /optimize.*code/i,
            /代码.*优化/i,
            /重构.*方案/i,
            /improve.*this/i,
            /make.*better/i,
            /clean.*up/i,
            /simplify.*code/i,
            /改进.*代码/i,
            /简化.*逻辑/i
        ]],
        ['documentation', [
            /生成.*文档/i,
            /添加.*注释/i,
            /generate.*documentation/i,
            /add.*comments/i,
            /文档.*生成/i,
            /注释.*添加/i,
            /document.*this/i,
            /write.*docs/i,
            /create.*readme/i,
            /api.*documentation/i,
            /写.*文档/i,
            /创建.*说明/i
        ]],
        ['performance_analysis', [
            /性能.*分析/i,
            /performance.*analysis/i,
            /optimize.*performance/i,
            /性能.*优化/i,
            /slow.*code/i,
            /bottleneck/i,
            /瓶颈.*分析/i,
            /效率.*检查/i
        ]],
        ['test_analysis', [
            /测试.*分析/i,
            /test.*analysis/i,
            /check.*tests/i,
            /测试.*覆盖/i,
            /test.*coverage/i,
            /unit.*test/i,
            /单元.*测试/i,
            /测试.*用例/i
        ]]
    ]);
    
    constructor() {}
    
    async processActivity(activity: AugmentActivity): Promise<AgentScopeTask | null> {
        try {
            // 1. 解析活动内容
            const intent = this.parseIntent(activity.content);
            if (!intent) return null;
            
            // 2. 获取当前上下文
            const context = await this.getCurrentContext();
            
            // 3. 合并活动上下文
            const mergedContext = { ...context, ...activity.context };
            
            // 4. 创建任务
            const task: AgentScopeTask = {
                id: `augment_${Date.now()}`,
                type: intent.type,
                title: this.generateTaskTitle(intent, activity),
                description: activity.content,
                parameters: {
                    ...intent.parameters,
                    ...mergedContext,
                    target_files: intent.target_files,
                    analysis_types: intent.analysis_types,
                    source: activity.source,
                    original_activity: activity
                },
                priority: this.determinePriority(intent.type, intent.confidence),
                metadata: {
                    augment_activity: activity,
                    parsed_intent: intent,
                    processing_timestamp: Date.now()
                }
            };
            
            return task;
            
        } catch (error) {
            console.error('Failed to process Augment activity:', error);
            return null;
        }
    }
    
    private parseIntent(content: string): ParsedIntent | null {
        // 计算每种意图类型的匹配分数
        const scores: { [key: string]: number } = {};
        
        for (const [intentType, patterns] of this.nlpPatterns) {
            let score = 0;
            for (const pattern of patterns) {
                if (pattern.test(content)) {
                    score += 1;
                }
            }
            scores[intentType] = score;
        }
        
        // 找到得分最高的意图类型
        const bestIntent = Object.keys(scores).reduce((a, b) => 
            scores[a] > scores[b] ? a : b
        );
        
        if (scores[bestIntent] === 0) {
            return null; // 没有匹配的意图
        }
        
        // 提取参数和目标文件
        const parameters = this.extractParameters(content, bestIntent);
        const targetFiles = this.extractTargetFiles(content);
        const analysisTypes = this.determineAnalysisTypes(content, bestIntent);
        const confidence = this.calculateConfidence(content, bestIntent, scores[bestIntent]);
        
        return {
            type: bestIntent,
            parameters,
            confidence,
            target_files: targetFiles,
            analysis_types: analysisTypes
        };
    }
    
    private extractParameters(content: string, intentType: string): any {
        const parameters: any = {};
        
        // 提取文件路径
        const fileMatch = content.match(/(?:文件|file)[:：]\s*([^\s]+)/i);
        if (fileMatch) {
            parameters.file_path = fileMatch[1];
        }
        
        // 提取目录
        const dirMatch = content.match(/(?:目录|directory)[:：]\s*([^\s]+)/i);
        if (dirMatch) {
            parameters.directory = dirMatch[1];
        }
        
        // 提取语言
        const langMatch = content.match(/(?:语言|language)[:：]\s*([^\s]+)/i);
        if (langMatch) {
            parameters.language = langMatch[1];
        }
        
        // 根据意图类型提取特定参数
        if (intentType === 'security_scan') {
            if (content.includes('SQL注入') || content.includes('sql injection')) {
                parameters.scan_types = ['sql_injection'];
            }
            if (content.includes('XSS')) {
                parameters.scan_types = [...(parameters.scan_types || []), 'xss'];
            }
            if (content.includes('硬编码') || content.includes('hardcoded')) {
                parameters.scan_types = [...(parameters.scan_types || []), 'hardcoded_secrets'];
            }
        }
        
        if (intentType === 'quality_check') {
            if (content.includes('复杂度') || content.includes('complexity')) {
                parameters.check_types = ['complexity'];
            }
            if (content.includes('规范') || content.includes('style')) {
                parameters.check_types = [...(parameters.check_types || []), 'style'];
            }
        }
        
        return parameters;
    }
    
    private extractTargetFiles(content: string): string[] {
        const targetFiles: string[] = [];
        
        // 从内容中提取文件路径
        const filePatterns = [
            /([a-zA-Z_][a-zA-Z0-9_]*\.py)/g,
            /([a-zA-Z_][a-zA-Z0-9_]*\.js)/g,
            /([a-zA-Z_][a-zA-Z0-9_]*\.ts)/g,
            /([a-zA-Z_][a-zA-Z0-9_]*\.java)/g,
            /([a-zA-Z_][a-zA-Z0-9_]*\.cpp)/g,
            /([a-zA-Z_][a-zA-Z0-9_]*\.c)/g,
            /([a-zA-Z_][a-zA-Z0-9_]*\.go)/g,
            /([a-zA-Z_][a-zA-Z0-9_]*\.rs)/g
        ];
        
        for (const pattern of filePatterns) {
            const matches = content.match(pattern);
            if (matches) {
                targetFiles.push(...matches);
            }
        }
        
        // 去重
        return [...new Set(targetFiles)];
    }
    
    private determineAnalysisTypes(content: string, intentType: string): string[] {
        const analysisTypes: string[] = [];
        
        // 基于意图类型的默认分析类型
        switch (intentType) {
            case 'security_scan':
                analysisTypes.push('security', 'vulnerability');
                break;
            case 'quality_check':
                analysisTypes.push('quality', 'style', 'complexity');
                break;
            case 'code_analysis':
                analysisTypes.push('structure', 'dependencies', 'metrics');
                break;
            case 'refactor_suggestion':
                analysisTypes.push('refactor', 'optimization');
                break;
            case 'documentation':
                analysisTypes.push('documentation', 'comments');
                break;
            default:
                analysisTypes.push('general');
        }
        
        // 根据内容细化分析类型
        const contentLower = content.toLowerCase();
        
        if (contentLower.includes('sql注入') || contentLower.includes('sql injection')) {
            analysisTypes.push('sql_injection');
        }
        
        if (contentLower.includes('xss')) {
            analysisTypes.push('xss');
        }
        
        if (contentLower.includes('复杂度') || contentLower.includes('complexity')) {
            analysisTypes.push('complexity');
        }
        
        if (contentLower.includes('性能') || contentLower.includes('performance')) {
            analysisTypes.push('performance');
        }
        
        if (contentLower.includes('测试') || contentLower.includes('test')) {
            analysisTypes.push('testing');
        }
        
        if (contentLower.includes('架构') || contentLower.includes('architecture')) {
            analysisTypes.push('architecture');
        }
        
        // 去重
        return [...new Set(analysisTypes)];
    }
    
    private calculateConfidence(content: string, intentType: string, matchCount: number): number {
        let confidence = 0.5; // 基础置信度
        
        // 根据匹配数量调整
        confidence += matchCount * 0.15;
        
        // 根据内容长度调整
        if (content.trim().length < 10) {
            confidence -= 0.2;
        } else if (content.trim().length > 50) {
            confidence += 0.1;
        }
        
        // 根据参数完整性调整
        const parameters = this.extractParameters(content, intentType);
        if (Object.keys(parameters).length > 0) {
            confidence += 0.1;
        }
        
        // 根据目标文件明确性调整
        const targetFiles = this.extractTargetFiles(content);
        if (targetFiles.length > 0) {
            confidence += 0.1;
        }
        
        return Math.min(Math.max(confidence, 0.0), 1.0);
    }
    
    private generateTaskTitle(intent: ParsedIntent, activity: AugmentActivity): string {
        const typeMap: { [key: string]: string } = {
            'code_analysis': '代码分析',
            'security_scan': '安全扫描',
            'quality_check': '质量检查',
            'refactor_suggestion': '重构建议',
            'documentation': '文档生成'
        };
        
        const typeTitle = typeMap[intent.type] || '代码分析';
        const contentPreview = activity.content.substring(0, 30);
        
        return `${typeTitle}: ${contentPreview}${activity.content.length > 30 ? '...' : ''}`;
    }
    
    private determinePriority(intentType: string, confidence: number): number {
        // 基础优先级
        const priorityMap: { [key: string]: number } = {
            'security_scan': 1,      // 高优先级
            'code_analysis': 2,      // 中优先级
            'quality_check': 2,      // 中优先级
            'refactor_suggestion': 3, // 低优先级
            'documentation': 3       // 低优先级
        };
        
        let priority = priorityMap[intentType] || 2;
        
        // 根据置信度调整
        if (confidence > 0.8) {
            priority = Math.max(1, priority - 1);
        } else if (confidence < 0.6) {
            priority = Math.min(3, priority + 1);
        }
        
        return priority;
    }
    
    private async getCurrentContext(): Promise<any> {
        const context: any = {};
        
        // 获取当前活动编辑器
        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor) {
            context.current_file = activeEditor.document.uri.fsPath;
            context.language = activeEditor.document.languageId;
            context.selection = {
                start: { 
                    line: activeEditor.selection.start.line, 
                    character: activeEditor.selection.start.character 
                },
                end: { 
                    line: activeEditor.selection.end.line, 
                    character: activeEditor.selection.end.character 
                }
            };
            
            // 获取选中的文本
            if (!activeEditor.selection.isEmpty) {
                context.selected_text = activeEditor.document.getText(activeEditor.selection);
            }
        }
        
        // 获取工作区信息
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            context.workspace_root = workspaceFolder.uri.fsPath;
            context.workspace_name = workspaceFolder.name;
        }
        
        // 获取项目类型信息
        if (workspaceFolder) {
            const packageJson = vscode.Uri.joinPath(workspaceFolder.uri, 'package.json');
            const requirementsTxt = vscode.Uri.joinPath(workspaceFolder.uri, 'requirements.txt');
            const cargoToml = vscode.Uri.joinPath(workspaceFolder.uri, 'Cargo.toml');
            
            try {
                await vscode.workspace.fs.stat(packageJson);
                context.project_type = 'javascript';
            } catch {
                try {
                    await vscode.workspace.fs.stat(requirementsTxt);
                    context.project_type = 'python';
                } catch {
                    try {
                        await vscode.workspace.fs.stat(cargoToml);
                        context.project_type = 'rust';
                    } catch {
                        context.project_type = 'unknown';
                    }
                }
            }
        }
        
        return context;
    }
    
    // 公共方法：验证任务参数
    public validateTask(task: AgentScopeTask): { valid: boolean; errors: string[] } {
        const errors: string[] = [];
        
        if (!task.id) {
            errors.push('Task ID is required');
        }
        
        if (!task.type) {
            errors.push('Task type is required');
        }
        
        if (!task.description) {
            errors.push('Task description is required');
        }
        
        if (task.priority < 1 || task.priority > 3) {
            errors.push('Task priority must be between 1 and 3');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    }
    
    // 公共方法：获取支持的任务类型
    public getSupportedTaskTypes(): string[] {
        return Array.from(this.nlpPatterns.keys());
    }
}
