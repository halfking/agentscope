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
export declare class ConfigurationManager {
    private static readonly CONFIG_SECTION;
    private configuration;
    private disposables;
    constructor();
    private loadConfiguration;
    private setupConfigurationWatcher;
    reloadConfiguration(): void;
    getConfiguration(): AgentScopeConfiguration;
    getBackendConfig(): BackendConfig;
    getAgentConfig(): AgentConfig;
    getLLMConfig(): LLMConfig;
    getAnalysisConfig(): AnalysisConfig;
    getNotificationConfig(): NotificationConfig;
    getDashboardConfig(): DashboardConfig;
    updateConfiguration(section: string, value: any): Promise<void>;
    isAgentEnabled(agentType: keyof AgentConfig): boolean;
    shouldAutoRunAnalysis(): boolean;
    shouldAutoOpenDashboard(): boolean;
    getExcludePatterns(): string[];
    getNotificationLevel(): string;
    getBackendUrl(): string;
    getWebSocketUrl(): string;
    validateConfiguration(): string[];
    resetToDefaults(): Promise<void>;
    exportConfiguration(): string;
    importConfiguration(configJson: string): Promise<void>;
    getConfigurationSchema(): any;
    dispose(): void;
}
//# sourceMappingURL=configurationManager.d.ts.map