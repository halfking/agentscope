"use strict";
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
exports.ConfigurationManager = void 0;
const vscode = __importStar(require("vscode"));
class ConfigurationManager {
    constructor() {
        this.disposables = [];
        this.configuration = this.loadConfiguration();
        this.setupConfigurationWatcher();
    }
    loadConfiguration() {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIG_SECTION);
        return {
            backend: {
                host: config.get('backend.host', 'localhost'),
                port: config.get('backend.port', 8000),
                protocol: config.get('backend.protocol', 'http')
            },
            agents: {
                codeManager: {
                    enabled: config.get('agents.codeManager.enabled', true)
                },
                complianceAuditor: {
                    enabled: config.get('agents.complianceAuditor.enabled', true)
                },
                systemArchitect: {
                    enabled: config.get('agents.systemArchitect.enabled', false)
                }
            },
            llm: {
                provider: config.get('llm.provider', 'openai'),
                model: config.get('llm.model', 'gpt-4')
            },
            analysis: {
                autoRun: config.get('analysis.autoRun', false),
                excludePatterns: config.get('analysis.excludePatterns', [
                    'node_modules/**',
                    '**/*.min.js',
                    '**/__pycache__/**'
                ])
            },
            notifications: {
                level: config.get('notifications.level', 'info')
            },
            dashboard: {
                autoOpen: config.get('dashboard.autoOpen', true)
            }
        };
    }
    setupConfigurationWatcher() {
        const disposable = vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration(ConfigurationManager.CONFIG_SECTION)) {
                this.reloadConfiguration();
            }
        });
        this.disposables.push(disposable);
    }
    reloadConfiguration() {
        const oldConfig = { ...this.configuration };
        this.configuration = this.loadConfiguration();
        // 检查关键配置是否发生变化
        const backendChanged = (oldConfig.backend.host !== this.configuration.backend.host ||
            oldConfig.backend.port !== this.configuration.backend.port ||
            oldConfig.backend.protocol !== this.configuration.backend.protocol);
        if (backendChanged) {
            vscode.window.showInformationMessage('Backend configuration changed. Please restart the connection.', 'Restart Connection').then(selection => {
                if (selection === 'Restart Connection') {
                    vscode.commands.executeCommand('agentscope.restartConnection');
                }
            });
        }
        // 发送配置变更事件
        vscode.commands.executeCommand('agentscope.configurationChanged', {
            oldConfig,
            newConfig: this.configuration
        });
    }
    getConfiguration() {
        return { ...this.configuration };
    }
    getBackendConfig() {
        return { ...this.configuration.backend };
    }
    getAgentConfig() {
        return { ...this.configuration.agents };
    }
    getLLMConfig() {
        return { ...this.configuration.llm };
    }
    getAnalysisConfig() {
        return { ...this.configuration.analysis };
    }
    getNotificationConfig() {
        return { ...this.configuration.notifications };
    }
    getDashboardConfig() {
        return { ...this.configuration.dashboard };
    }
    async updateConfiguration(section, value) {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIG_SECTION);
        await config.update(section, value, vscode.ConfigurationTarget.Global);
    }
    isAgentEnabled(agentType) {
        return this.configuration.agents[agentType].enabled;
    }
    shouldAutoRunAnalysis() {
        return this.configuration.analysis.autoRun;
    }
    shouldAutoOpenDashboard() {
        return this.configuration.dashboard.autoOpen;
    }
    getExcludePatterns() {
        return [...this.configuration.analysis.excludePatterns];
    }
    getNotificationLevel() {
        return this.configuration.notifications.level;
    }
    getBackendUrl() {
        const { protocol, host, port } = this.configuration.backend;
        return `${protocol}://${host}:${port}`;
    }
    getWebSocketUrl() {
        const { host, port } = this.configuration.backend;
        return `ws://${host}:${port}/ws`;
    }
    validateConfiguration() {
        const errors = [];
        // 验证后端配置
        if (!this.configuration.backend.host) {
            errors.push('Backend host is required');
        }
        if (this.configuration.backend.port <= 0 || this.configuration.backend.port > 65535) {
            errors.push('Backend port must be between 1 and 65535');
        }
        // 验证LLM配置
        if (!this.configuration.llm.provider) {
            errors.push('LLM provider is required');
        }
        if (!this.configuration.llm.model) {
            errors.push('LLM model is required');
        }
        // 验证排除模式
        for (const pattern of this.configuration.analysis.excludePatterns) {
            if (typeof pattern !== 'string' || pattern.trim() === '') {
                errors.push(`Invalid exclude pattern: ${pattern}`);
            }
        }
        return errors;
    }
    async resetToDefaults() {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIG_SECTION);
        // 重置所有配置项到默认值
        const resetPromises = [
            config.update('backend.host', undefined, vscode.ConfigurationTarget.Global),
            config.update('backend.port', undefined, vscode.ConfigurationTarget.Global),
            config.update('backend.protocol', undefined, vscode.ConfigurationTarget.Global),
            config.update('agents.codeManager.enabled', undefined, vscode.ConfigurationTarget.Global),
            config.update('agents.complianceAuditor.enabled', undefined, vscode.ConfigurationTarget.Global),
            config.update('agents.systemArchitect.enabled', undefined, vscode.ConfigurationTarget.Global),
            config.update('llm.provider', undefined, vscode.ConfigurationTarget.Global),
            config.update('llm.model', undefined, vscode.ConfigurationTarget.Global),
            config.update('analysis.autoRun', undefined, vscode.ConfigurationTarget.Global),
            config.update('analysis.excludePatterns', undefined, vscode.ConfigurationTarget.Global),
            config.update('notifications.level', undefined, vscode.ConfigurationTarget.Global),
            config.update('dashboard.autoOpen', undefined, vscode.ConfigurationTarget.Global)
        ];
        await Promise.all(resetPromises);
        vscode.window.showInformationMessage('Configuration reset to defaults');
    }
    exportConfiguration() {
        return JSON.stringify(this.configuration, null, 2);
    }
    async importConfiguration(configJson) {
        try {
            const importedConfig = JSON.parse(configJson);
            const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIG_SECTION);
            // 更新配置
            if (importedConfig.backend) {
                await config.update('backend.host', importedConfig.backend.host, vscode.ConfigurationTarget.Global);
                await config.update('backend.port', importedConfig.backend.port, vscode.ConfigurationTarget.Global);
                await config.update('backend.protocol', importedConfig.backend.protocol, vscode.ConfigurationTarget.Global);
            }
            if (importedConfig.agents) {
                await config.update('agents.codeManager.enabled', importedConfig.agents.codeManager?.enabled, vscode.ConfigurationTarget.Global);
                await config.update('agents.complianceAuditor.enabled', importedConfig.agents.complianceAuditor?.enabled, vscode.ConfigurationTarget.Global);
                await config.update('agents.systemArchitect.enabled', importedConfig.agents.systemArchitect?.enabled, vscode.ConfigurationTarget.Global);
            }
            if (importedConfig.llm) {
                await config.update('llm.provider', importedConfig.llm.provider, vscode.ConfigurationTarget.Global);
                await config.update('llm.model', importedConfig.llm.model, vscode.ConfigurationTarget.Global);
            }
            if (importedConfig.analysis) {
                await config.update('analysis.autoRun', importedConfig.analysis.autoRun, vscode.ConfigurationTarget.Global);
                await config.update('analysis.excludePatterns', importedConfig.analysis.excludePatterns, vscode.ConfigurationTarget.Global);
            }
            if (importedConfig.notifications) {
                await config.update('notifications.level', importedConfig.notifications.level, vscode.ConfigurationTarget.Global);
            }
            if (importedConfig.dashboard) {
                await config.update('dashboard.autoOpen', importedConfig.dashboard.autoOpen, vscode.ConfigurationTarget.Global);
            }
            vscode.window.showInformationMessage('Configuration imported successfully');
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to import configuration: ${error}`);
            throw error;
        }
    }
    getConfigurationSchema() {
        return {
            type: 'object',
            properties: {
                backend: {
                    type: 'object',
                    properties: {
                        host: { type: 'string', default: 'localhost' },
                        port: { type: 'number', default: 8000 },
                        protocol: { type: 'string', enum: ['http', 'https'], default: 'http' }
                    }
                },
                agents: {
                    type: 'object',
                    properties: {
                        codeManager: {
                            type: 'object',
                            properties: {
                                enabled: { type: 'boolean', default: true }
                            }
                        },
                        complianceAuditor: {
                            type: 'object',
                            properties: {
                                enabled: { type: 'boolean', default: true }
                            }
                        },
                        systemArchitect: {
                            type: 'object',
                            properties: {
                                enabled: { type: 'boolean', default: false }
                            }
                        }
                    }
                },
                llm: {
                    type: 'object',
                    properties: {
                        provider: { type: 'string', default: 'openai' },
                        model: { type: 'string', default: 'gpt-4' }
                    }
                },
                analysis: {
                    type: 'object',
                    properties: {
                        autoRun: { type: 'boolean', default: false },
                        excludePatterns: {
                            type: 'array',
                            items: { type: 'string' },
                            default: ['node_modules/**', '**/*.min.js', '**/__pycache__/**']
                        }
                    }
                },
                notifications: {
                    type: 'object',
                    properties: {
                        level: {
                            type: 'string',
                            enum: ['error', 'warning', 'info', 'debug'],
                            default: 'info'
                        }
                    }
                },
                dashboard: {
                    type: 'object',
                    properties: {
                        autoOpen: { type: 'boolean', default: true }
                    }
                }
            }
        };
    }
    dispose() {
        this.disposables.forEach(d => d.dispose());
        this.disposables = [];
    }
}
exports.ConfigurationManager = ConfigurationManager;
ConfigurationManager.CONFIG_SECTION = 'agentscope';
//# sourceMappingURL=configurationManager.js.map