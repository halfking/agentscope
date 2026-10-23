/**
 * Augment活动监听器 - 实现对Augment Agent活动的实时监听
 */
/// <reference types="node" />
import { EventEmitter } from 'events';
export interface AugmentActivity {
    type: 'command' | 'output' | 'file_change' | 'document_change';
    content: string;
    context: any;
    timestamp: number;
    source: string;
}
export interface AugmentCommand {
    command: string;
    args: any;
    source: string;
}
/**
 * Augment活动监听器
 */
export declare class AugmentActivityWatcher extends EventEmitter {
    private outputChannels;
    private fileWatcher;
    private documentWatcher;
    private commandWatcher;
    private isActive;
    constructor();
    start(): Promise<void>;
    stop(): void;
    private setupOutputChannelMonitoring;
    private setupChannelContentMonitoring;
    private monitorExtensionActivity;
    private setupTerminalMonitoring;
    private monitorTerminal;
    private setupFileSystemMonitoring;
    private setupCommandMonitoring;
    private setupDocumentMonitoring;
    private handleAugmentFile;
    private handleAugmentCommand;
    private isAugmentGeneratedContent;
    private containsAugmentInstructions;
    detectCurrentActivity(): Promise<AugmentActivity[]>;
    getCurrentContext(): any;
}
//# sourceMappingURL=augmentActivityWatcher.d.ts.map