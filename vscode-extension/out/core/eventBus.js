"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NamespacedEventBus = exports.EventBus = void 0;
class EventBus {
    constructor() {
        this.subscriptions = new Map();
        this.subscriptionCounter = 0;
        this.eventHistory = [];
        this.maxHistorySize = 100;
        this.isDestroyed = false;
    }
    /**
     * 订阅事件
     * @param eventType 事件类型
     * @param handler 事件处理器
     * @param options 订阅选项
     * @returns 订阅ID
     */
    on(eventType, handler, options = {}) {
        if (this.isDestroyed) {
            throw new Error('EventBus has been destroyed');
        }
        const subscription = {
            id: `sub_${++this.subscriptionCounter}`,
            eventType,
            handler: handler,
            once: options.once || false,
            priority: options.priority || 0
        };
        if (!this.subscriptions.has(eventType)) {
            this.subscriptions.set(eventType, []);
        }
        const subs = this.subscriptions.get(eventType);
        subs.push(subscription);
        // 按优先级排序（优先级高的先执行）
        subs.sort((a, b) => b.priority - a.priority);
        return subscription.id;
    }
    /**
     * 订阅事件（只执行一次）
     * @param eventType 事件类型
     * @param handler 事件处理器
     * @param priority 优先级
     * @returns 订阅ID
     */
    once(eventType, handler, priority = 0) {
        return this.on(eventType, handler, { once: true, priority });
    }
    /**
     * 取消订阅
     * @param subscriptionId 订阅ID
     * @returns 是否成功取消
     */
    off(subscriptionId) {
        if (this.isDestroyed) {
            return false;
        }
        for (const [eventType, subs] of this.subscriptions.entries()) {
            const index = subs.findIndex(sub => sub.id === subscriptionId);
            if (index !== -1) {
                subs.splice(index, 1);
                // 如果没有订阅者了，删除事件类型
                if (subs.length === 0) {
                    this.subscriptions.delete(eventType);
                }
                return true;
            }
        }
        return false;
    }
    /**
     * 取消指定事件类型的所有订阅
     * @param eventType 事件类型
     * @returns 取消的订阅数量
     */
    offAll(eventType) {
        if (this.isDestroyed) {
            return 0;
        }
        const subs = this.subscriptions.get(eventType);
        if (!subs) {
            return 0;
        }
        const count = subs.length;
        this.subscriptions.delete(eventType);
        return count;
    }
    /**
     * 发送事件
     * @param eventType 事件类型
     * @param data 事件数据
     * @param metadata 事件元数据
     */
    async emit(eventType, data, metadata = {}) {
        if (this.isDestroyed) {
            return;
        }
        const eventData = {
            type: eventType,
            data,
            metadata: {
                timestamp: new Date(),
                source: metadata.source,
                correlationId: metadata.correlationId || this.generateCorrelationId()
            }
        };
        // 添加到历史记录
        this.addToHistory(eventData);
        const subs = this.subscriptions.get(eventType);
        if (!subs || subs.length === 0) {
            return;
        }
        // 创建副本以避免在处理过程中修改原数组
        const subsToProcess = [...subs];
        const onceSubscriptions = [];
        // 并行执行所有处理器
        const promises = subsToProcess.map(async (sub) => {
            try {
                await sub.handler(data);
                if (sub.once) {
                    onceSubscriptions.push(sub.id);
                }
            }
            catch (error) {
                console.error(`Error in event handler for ${eventType}:`, error);
                // 发送错误事件
                this.emit('eventHandlerError', {
                    originalEvent: eventType,
                    subscriptionId: sub.id,
                    error: error instanceof Error ? error.message : String(error)
                }, { source: 'EventBus' });
            }
        });
        await Promise.all(promises);
        // 移除一次性订阅
        onceSubscriptions.forEach(id => this.off(id));
    }
    /**
     * 同步发送事件
     * @param eventType 事件类型
     * @param data 事件数据
     * @param metadata 事件元数据
     */
    emitSync(eventType, data, metadata = {}) {
        if (this.isDestroyed) {
            return;
        }
        const eventData = {
            type: eventType,
            data,
            metadata: {
                timestamp: new Date(),
                source: metadata.source,
                correlationId: metadata.correlationId || this.generateCorrelationId()
            }
        };
        // 添加到历史记录
        this.addToHistory(eventData);
        const subs = this.subscriptions.get(eventType);
        if (!subs || subs.length === 0) {
            return;
        }
        const onceSubscriptions = [];
        for (const sub of subs) {
            try {
                const result = sub.handler(data);
                // 如果返回Promise，警告用户应该使用emit而不是emitSync
                if (result && typeof result.then === 'function') {
                    console.warn(`Async handler detected for ${eventType}. Consider using emit() instead of emitSync()`);
                }
                if (sub.once) {
                    onceSubscriptions.push(sub.id);
                }
            }
            catch (error) {
                console.error(`Error in sync event handler for ${eventType}:`, error);
            }
        }
        // 移除一次性订阅
        onceSubscriptions.forEach(id => this.off(id));
    }
    /**
     * 等待特定事件
     * @param eventType 事件类型
     * @param timeout 超时时间（毫秒）
     * @param condition 条件函数
     * @returns Promise，解析为事件数据
     */
    waitFor(eventType, timeout, condition) {
        return new Promise((resolve, reject) => {
            let timeoutId;
            let subscriptionId;
            const cleanup = () => {
                if (timeoutId) {
                    clearTimeout(timeoutId);
                }
                this.off(subscriptionId);
            };
            subscriptionId = this.once(eventType, (data) => {
                if (!condition || condition(data)) {
                    cleanup();
                    resolve(data);
                }
            });
            if (timeout) {
                timeoutId = setTimeout(() => {
                    cleanup();
                    reject(new Error(`Timeout waiting for event: ${eventType}`));
                }, timeout);
            }
        });
    }
    /**
     * 检查是否有订阅者
     * @param eventType 事件类型
     * @returns 是否有订阅者
     */
    hasListeners(eventType) {
        const subs = this.subscriptions.get(eventType);
        return subs ? subs.length > 0 : false;
    }
    /**
     * 获取订阅者数量
     * @param eventType 事件类型
     * @returns 订阅者数量
     */
    listenerCount(eventType) {
        const subs = this.subscriptions.get(eventType);
        return subs ? subs.length : 0;
    }
    /**
     * 获取所有事件类型
     * @returns 事件类型数组
     */
    eventTypes() {
        return Array.from(this.subscriptions.keys());
    }
    /**
     * 获取事件历史
     * @param eventType 可选的事件类型过滤
     * @param limit 限制数量
     * @returns 事件历史数组
     */
    getHistory(eventType, limit) {
        let history = this.eventHistory;
        if (eventType) {
            history = history.filter(event => event.type === eventType);
        }
        if (limit && limit > 0) {
            history = history.slice(-limit);
        }
        return [...history];
    }
    /**
     * 清空事件历史
     */
    clearHistory() {
        this.eventHistory = [];
    }
    /**
     * 获取统计信息
     * @returns 统计信息对象
     */
    getStats() {
        const subscriptionsByType = {};
        let totalSubscriptions = 0;
        for (const [eventType, subs] of this.subscriptions.entries()) {
            subscriptionsByType[eventType] = subs.length;
            totalSubscriptions += subs.length;
        }
        return {
            totalSubscriptions,
            eventTypes: this.subscriptions.size,
            historySize: this.eventHistory.length,
            subscriptionsByType
        };
    }
    /**
     * 销毁事件总线
     */
    destroy() {
        this.subscriptions.clear();
        this.eventHistory = [];
        this.isDestroyed = true;
    }
    addToHistory(eventData) {
        this.eventHistory.push(eventData);
        // 限制历史记录大小
        if (this.eventHistory.length > this.maxHistorySize) {
            this.eventHistory = this.eventHistory.slice(-this.maxHistorySize);
        }
    }
    generateCorrelationId() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
    /**
     * 设置最大历史记录大小
     * @param size 最大大小
     */
    setMaxHistorySize(size) {
        this.maxHistorySize = Math.max(0, size);
        if (this.eventHistory.length > this.maxHistorySize) {
            this.eventHistory = this.eventHistory.slice(-this.maxHistorySize);
        }
    }
    /**
     * 创建命名空间事件总线
     * @param namespace 命名空间
     * @returns 命名空间事件总线
     */
    namespace(namespace) {
        return new NamespacedEventBus(this, namespace);
    }
}
exports.EventBus = EventBus;
/**
 * 命名空间事件总线
 */
class NamespacedEventBus {
    constructor(parentBus, namespace) {
        this.parentBus = parentBus;
        this.namespace = namespace;
    }
    getNamespacedType(eventType) {
        return `${this.namespace}:${eventType}`;
    }
    on(eventType, handler, options = {}) {
        return this.parentBus.on(this.getNamespacedType(eventType), handler, options);
    }
    once(eventType, handler, priority = 0) {
        return this.parentBus.once(this.getNamespacedType(eventType), handler, priority);
    }
    off(subscriptionId) {
        return this.parentBus.off(subscriptionId);
    }
    async emit(eventType, data, metadata = {}) {
        return this.parentBus.emit(this.getNamespacedType(eventType), data, { ...metadata, source: metadata.source || this.namespace });
    }
    emitSync(eventType, data, metadata = {}) {
        return this.parentBus.emitSync(this.getNamespacedType(eventType), data, { ...metadata, source: metadata.source || this.namespace });
    }
    waitFor(eventType, timeout, condition) {
        return this.parentBus.waitFor(this.getNamespacedType(eventType), timeout, condition);
    }
    hasListeners(eventType) {
        return this.parentBus.hasListeners(this.getNamespacedType(eventType));
    }
    listenerCount(eventType) {
        return this.parentBus.listenerCount(this.getNamespacedType(eventType));
    }
}
exports.NamespacedEventBus = NamespacedEventBus;
//# sourceMappingURL=eventBus.js.map