/**
 * Augment命令处理器 - 将Augment指令转换为AgentScope任务
 */
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
export declare class AugmentCommandProcessor {
    private nlpPatterns;
    constructor();
    processActivity(activity: AugmentActivity): Promise<AgentScopeTask | null>;
    private parseIntent;
    private extractParameters;
    private extractTargetFiles;
    private determineAnalysisTypes;
    private calculateConfidence;
    private generateTaskTitle;
    private determinePriority;
    private getCurrentContext;
    validateTask(task: AgentScopeTask): {
        valid: boolean;
        errors: string[];
    };
    getSupportedTaskTypes(): string[];
}
//# sourceMappingURL=augmentCommandProcessor.d.ts.map