export type EventHandler<T = any> = (data: T) => void | Promise<void>;
export interface EventSubscription {
    id: string;
    eventType: string;
    handler: EventHandler;
    once: boolean;
    priority: number;
}
export interface EventMetadata {
    timestamp: Date;
    source?: string;
    correlationId?: string;
}
export interface EventData<T = any> {
    type: string;
    data: T;
    metadata: EventMetadata;
}
export declare class EventBus {
    private subscriptions;
    private subscriptionCounter;
    private eventHistory;
    private maxHistorySize;
    private isDestroyed;
    /**
     * 订阅事件
     * @param eventType 事件类型
     * @param handler 事件处理器
     * @param options 订阅选项
     * @returns 订阅ID
     */
    on<T = any>(eventType: string, handler: EventHandler<T>, options?: {
        once?: boolean;
        priority?: number;
    }): string;
    /**
     * 订阅事件（只执行一次）
     * @param eventType 事件类型
     * @param handler 事件处理器
     * @param priority 优先级
     * @returns 订阅ID
     */
    once<T = any>(eventType: string, handler: EventHandler<T>, priority?: number): string;
    /**
     * 取消订阅
     * @param subscriptionId 订阅ID
     * @returns 是否成功取消
     */
    off(subscriptionId: string): boolean;
    /**
     * 取消指定事件类型的所有订阅
     * @param eventType 事件类型
     * @returns 取消的订阅数量
     */
    offAll(eventType: string): number;
    /**
     * 发送事件
     * @param eventType 事件类型
     * @param data 事件数据
     * @param metadata 事件元数据
     */
    emit<T = any>(eventType: string, data: T, metadata?: Partial<EventMetadata>): Promise<void>;
    /**
     * 同步发送事件
     * @param eventType 事件类型
     * @param data 事件数据
     * @param metadata 事件元数据
     */
    emitSync<T = any>(eventType: string, data: T, metadata?: Partial<EventMetadata>): void;
    /**
     * 等待特定事件
     * @param eventType 事件类型
     * @param timeout 超时时间（毫秒）
     * @param condition 条件函数
     * @returns Promise，解析为事件数据
     */
    waitFor<T = any>(eventType: string, timeout?: number, condition?: (data: T) => boolean): Promise<T>;
    /**
     * 检查是否有订阅者
     * @param eventType 事件类型
     * @returns 是否有订阅者
     */
    hasListeners(eventType: string): boolean;
    /**
     * 获取订阅者数量
     * @param eventType 事件类型
     * @returns 订阅者数量
     */
    listenerCount(eventType: string): number;
    /**
     * 获取所有事件类型
     * @returns 事件类型数组
     */
    eventTypes(): string[];
    /**
     * 获取事件历史
     * @param eventType 可选的事件类型过滤
     * @param limit 限制数量
     * @returns 事件历史数组
     */
    getHistory(eventType?: string, limit?: number): EventData[];
    /**
     * 清空事件历史
     */
    clearHistory(): void;
    /**
     * 获取统计信息
     * @returns 统计信息对象
     */
    getStats(): {
        totalSubscriptions: number;
        eventTypes: number;
        historySize: number;
        subscriptionsByType: Record<string, number>;
    };
    /**
     * 销毁事件总线
     */
    destroy(): void;
    private addToHistory;
    private generateCorrelationId;
    /**
     * 设置最大历史记录大小
     * @param size 最大大小
     */
    setMaxHistorySize(size: number): void;
    /**
     * 创建命名空间事件总线
     * @param namespace 命名空间
     * @returns 命名空间事件总线
     */
    namespace(namespace: string): NamespacedEventBus;
}
/**
 * 命名空间事件总线
 */
export declare class NamespacedEventBus {
    private parentBus;
    private namespace;
    constructor(parentBus: EventBus, namespace: string);
    private getNamespacedType;
    on<T = any>(eventType: string, handler: EventHandler<T>, options?: {
        once?: boolean;
        priority?: number;
    }): string;
    once<T = any>(eventType: string, handler: EventHandler<T>, priority?: number): string;
    off(subscriptionId: string): boolean;
    emit<T = any>(eventType: string, data: T, metadata?: Partial<EventMetadata>): Promise<void>;
    emitSync<T = any>(eventType: string, data: T, metadata?: Partial<EventMetadata>): void;
    waitFor<T = any>(eventType: string, timeout?: number, condition?: (data: T) => boolean): Promise<T>;
    hasListeners(eventType: string): boolean;
    listenerCount(eventType: string): number;
}
//# sourceMappingURL=eventBus.d.ts.map