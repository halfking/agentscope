import * as vscode from 'vscode';

export interface BackendConfig {
    host: string;
    port: number;
    protocol: 'http' | 'https';
}

export interface AgentConfig {
    codeManager: {
        enabled: boolean;
    };
    complianceAuditor: {
        enabled: boolean;
    };
    systemArchitect: {
        enabled: boolean;
    };
}

export interface LLMConfig {
    provider: string;
    model: string;
}

export interface AnalysisConfig {
    autoRun: boolean;
    excludePatterns: string[];
}

export interface NotificationConfig {
    level: 'error' | 'warning' | 'info' | 'debug';
}

export interface DashboardConfig {
    autoOpen: boolean;
}

export interface AgentScopeConfiguration {
    backend: BackendConfig;
    agents: AgentConfig;
    llm: LLMConfig;
    analysis: AnalysisConfig;
    notifications: NotificationConfig;
    dashboard: DashboardConfig;
}

export class ConfigurationManager {
    private static readonly CONFIG_SECTION = 'agentscope';
    private configuration: AgentScopeConfiguration;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.configuration = this.loadConfiguration();
        this.setupConfigurationWatcher();
    }

    private loadConfiguration(): AgentScopeConfiguration {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIG_SECTION);

        return {
            backend: {
                host: config.get<string>('backend.host', 'localhost'),
                port: config.get<number>('backend.port', 8000),
                protocol: config.get<'http' | 'https'>('backend.protocol', 'http')
            },
            agents: {
                codeManager: {
                    enabled: config.get<boolean>('agents.codeManager.enabled', true)
                },
                complianceAuditor: {
                    enabled: config.get<boolean>('agents.complianceAuditor.enabled', true)
                },
                systemArchitect: {
                    enabled: config.get<boolean>('agents.systemArchitect.enabled', false)
                }
            },
            llm: {
                provider: config.get<string>('llm.provider', 'openai'),
                model: config.get<string>('llm.model', 'gpt-4')
            },
            analysis: {
                autoRun: config.get<boolean>('analysis.autoRun', false),
                excludePatterns: config.get<string[]>('analysis.excludePatterns', [
                    'node_modules/**',
                    '**/*.min.js',
                    '**/__pycache__/**'
                ])
            },
            notifications: {
                level: config.get<'error' | 'warning' | 'info' | 'debug'>('notifications.level', 'info')
            },
            dashboard: {
                autoOpen: config.get<boolean>('dashboard.autoOpen', true)
            }
        };
    }

    private setupConfigurationWatcher() {
        const disposable = vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration(ConfigurationManager.CONFIG_SECTION)) {
                this.reloadConfiguration();
            }
        });

        this.disposables.push(disposable);
    }

    public reloadConfiguration(): void {
        const oldConfig = { ...this.configuration };
        this.configuration = this.loadConfiguration();

        // 检查关键配置是否发生变化
        const backendChanged = (
            oldConfig.backend.host !== this.configuration.backend.host ||
            oldConfig.backend.port !== this.configuration.backend.port ||
            oldConfig.backend.protocol !== this.configuration.backend.protocol
        );

        if (backendChanged) {
            vscode.window.showInformationMessage(
                'Backend configuration changed. Please restart the connection.',
                'Restart Connection'
            ).then(selection => {
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

    public getConfiguration(): AgentScopeConfiguration {
        return { ...this.configuration };
    }

    public getBackendConfig(): BackendConfig {
        return { ...this.configuration.backend };
    }

    public getAgentConfig(): AgentConfig {
        return { ...this.configuration.agents };
    }

    public getLLMConfig(): LLMConfig {
        return { ...this.configuration.llm };
    }

    public getAnalysisConfig(): AnalysisConfig {
        return { ...this.configuration.analysis };
    }

    public getNotificationConfig(): NotificationConfig {
        return { ...this.configuration.notifications };
    }

    public getDashboardConfig(): DashboardConfig {
        return { ...this.configuration.dashboard };
    }

    public async updateConfiguration(section: string, value: any): Promise<void> {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIG_SECTION);
        await config.update(section, value, vscode.ConfigurationTarget.Global);
    }

    public isAgentEnabled(agentType: keyof AgentConfig): boolean {
        return this.configuration.agents[agentType].enabled;
    }

    public shouldAutoRunAnalysis(): boolean {
        return this.configuration.analysis.autoRun;
    }

    public shouldAutoOpenDashboard(): boolean {
        return this.configuration.dashboard.autoOpen;
    }

    public getExcludePatterns(): string[] {
        return [...this.configuration.analysis.excludePatterns];
    }

    public getNotificationLevel(): string {
        return this.configuration.notifications.level;
    }

    public getBackendUrl(): string {
        const { protocol, host, port } = this.configuration.backend;
        return `${protocol}://${host}:${port}`;
    }

    public getWebSocketUrl(): string {
        const { host, port } = this.configuration.backend;
        return `ws://${host}:${port}/ws`;
    }

    public validateConfiguration(): string[] {
        const errors: string[] = [];

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

    public async resetToDefaults(): Promise<void> {
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

    public exportConfiguration(): string {
        return JSON.stringify(this.configuration, null, 2);
    }

    public async importConfiguration(configJson: string): Promise<void> {
        try {
            const importedConfig = JSON.parse(configJson) as Partial<AgentScopeConfiguration>;
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

        } catch (error) {
            vscode.window.showErrorMessage(`Failed to import configuration: ${error}`);
            throw error;
        }
    }

    public getConfigurationSchema(): any {
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

    public dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.disposables = [];
    }
}
