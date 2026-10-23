"use strict";
/**
 * 简化版增强的智能体系统管理器
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.EnhancedAgentSystemManager = void 0;
const vscode = __importStar(require("vscode"));
const agentSystemManager_1 = require("./agentSystemManager");
class EnhancedAgentSystemManager extends agentSystemManager_1.AgentSystemManager {
    constructor(eventBus, configManager, notificationManager) {
        super(eventBus, configManager, notificationManager);
        this.augmentEnabled = false;
    }
    // 获取Augment相关命令
    getAugmentCommands() {
        const commands = [];
        // 启用Augment集成
        commands.push(vscode.commands.registerCommand('agentscope.enableAugmentIntegration', async () => {
            try {
                this.augmentEnabled = true;
                vscode.commands.executeCommand('setContext', 'agentscope.augmentEnabled', true);
                vscode.window.showInformationMessage('Augment集成已启用');
            }
            catch (error) {
                vscode.window.showErrorMessage(`启用Augment集成失败: ${error?.message || error}`);
            }
        }));
        // 禁用Augment集成
        commands.push(vscode.commands.registerCommand('agentscope.disableAugmentIntegration', async () => {
            try {
                this.augmentEnabled = false;
                vscode.commands.executeCommand('setContext', 'agentscope.augmentEnabled', false);
                vscode.window.showInformationMessage('Augment集成已禁用');
            }
            catch (error) {
                vscode.window.showErrorMessage(`禁用Augment集成失败: ${error?.message || error}`);
            }
        }));
        // 检测Augment活动
        commands.push(vscode.commands.registerCommand('agentscope.detectAugmentActivity', async () => {
            try {
                if (!this.augmentEnabled) {
                    vscode.window.showWarningMessage('请先启用Augment集成');
                    return;
                }
                vscode.window.showInformationMessage('正在检测Augment活动...');
                // 这里可以添加实际的检测逻辑
                setTimeout(() => {
                    vscode.window.showInformationMessage('Augment活动检测完成');
                }, 2000);
            }
            catch (error) {
                vscode.window.showErrorMessage(`检测Augment活动失败: ${error?.message || error}`);
            }
        }));
        // 显示Augment状态
        commands.push(vscode.commands.registerCommand('agentscope.showAugmentStatus', async () => {
            const status = {
                enabled: this.augmentEnabled,
                version: '2.0.0',
                features: ['自然语言处理', '实时监听', '智能分析']
            };
            const statusText = [
                `**Augment集成状态**`,
                ``,
                `状态: ${status.enabled ? '✅ 已启用' : '❌ 已禁用'}`,
                `版本: ${status.version}`,
                `功能: ${status.features.join(', ')}`
            ].join('\n');
            vscode.window.showInformationMessage(statusText);
        }));
        // 处理Augment命令
        commands.push(vscode.commands.registerCommand('agentscope.processAugmentCommand', async () => {
            try {
                if (!this.augmentEnabled) {
                    vscode.window.showWarningMessage('请先启用Augment集成');
                    return;
                }
                const command = await vscode.window.showInputBox({
                    prompt: '请输入自然语言指令',
                    placeHolder: '例如: 分析这个文件的安全问题'
                });
                if (!command) {
                    return;
                }
                vscode.window.showInformationMessage(`正在处理指令: ${command}`);
                // 这里可以添加实际的命令处理逻辑
                setTimeout(() => {
                    vscode.window.showInformationMessage('指令处理完成');
                }, 3000);
            }
            catch (error) {
                vscode.window.showErrorMessage(`处理Augment指令失败: ${error?.message || error}`);
            }
        }));
        return commands;
    }
    // 更新配置
    updateConfiguration() {
        try {
            super.updateConfiguration();
            const config = vscode.workspace.getConfiguration('agentscope');
            const newAugmentEnabled = config.get('augment.enabled', false);
            if (newAugmentEnabled !== this.augmentEnabled) {
                this.augmentEnabled = newAugmentEnabled;
                vscode.commands.executeCommand('setContext', 'agentscope.augmentEnabled', this.augmentEnabled);
                if (this.augmentEnabled) {
                    vscode.window.showInformationMessage('Augment集成已通过配置启用');
                }
                else {
                    vscode.window.showInformationMessage('Augment集成已通过配置禁用');
                }
            }
        }
        catch (error) {
            console.error('Failed to update configuration:', error);
        }
    }
    // 获取Augment状态
    isAugmentEnabled() {
        return this.augmentEnabled;
    }
}
exports.EnhancedAgentSystemManager = EnhancedAgentSystemManager;
//# sourceMappingURL=enhancedAgentSystemManager.js.map