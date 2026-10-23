#!/usr/bin/env node

/**
 * 测试VS Code插件与后端服务的连接
 */

const axios = require('axios');
const WebSocket = require('ws');

const BACKEND_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

async function testHttpConnection() {
    console.log('🔍 测试HTTP连接...');
    
    try {
        // 测试健康检查
        const healthResponse = await axios.get(`${BACKEND_URL}/health`);
        console.log('✅ 健康检查:', healthResponse.data);
        
        // 测试系统状态
        const statusResponse = await axios.get(`${BACKEND_URL}/api/status`);
        console.log('✅ 系统状态:', statusResponse.data);
        
        // 测试配置
        const configResponse = await axios.get(`${BACKEND_URL}/api/config`);
        console.log('✅ 系统配置:', configResponse.data);
        
        return true;
    } catch (error) {
        console.error('❌ HTTP连接失败:', error.message);
        return false;
    }
}

async function testWebSocketConnection() {
    console.log('\n🔍 测试WebSocket连接...');
    
    return new Promise((resolve) => {
        const ws = new WebSocket(WS_URL);
        
        ws.on('open', () => {
            console.log('✅ WebSocket连接已建立');
            
            // 发送测试消息
            ws.send(JSON.stringify({
                type: 'test',
                message: 'Hello from test client'
            }));
        });
        
        ws.on('message', (data) => {
            try {
                const message = JSON.parse(data.toString());
                console.log('✅ 收到WebSocket消息:', message);
            } catch (error) {
                console.log('✅ 收到WebSocket数据:', data.toString());
            }
            
            ws.close();
            resolve(true);
        });
        
        ws.on('error', (error) => {
            console.error('❌ WebSocket连接失败:', error.message);
            resolve(false);
        });
        
        ws.on('close', () => {
            console.log('🔌 WebSocket连接已关闭');
        });
        
        // 设置超时
        setTimeout(() => {
            if (ws.readyState === WebSocket.CONNECTING) {
                console.error('❌ WebSocket连接超时');
                ws.close();
                resolve(false);
            }
        }, 5000);
    });
}

async function testApiEndpoints() {
    console.log('\n🔍 测试API端点...');
    
    try {
        // 测试代码分析端点
        const analyzeResponse = await axios.post(`${BACKEND_URL}/api/analyze`);
        console.log('✅ 代码分析端点:', analyzeResponse.data);
        
        // 测试质量检查端点
        const qualityResponse = await axios.post(`${BACKEND_URL}/api/quality-check`);
        console.log('✅ 质量检查端点:', qualityResponse.data);
        
        // 测试安全扫描端点
        const securityResponse = await axios.post(`${BACKEND_URL}/api/security-scan`);
        console.log('✅ 安全扫描端点:', securityResponse.data);
        
        // 测试Augment处理端点
        const augmentResponse = await axios.post(`${BACKEND_URL}/api/augment/process`);
        console.log('✅ Augment处理端点:', augmentResponse.data);
        
        return true;
    } catch (error) {
        console.error('❌ API端点测试失败:', error.message);
        return false;
    }
}

async function main() {
    console.log('🚀 开始测试VS Code插件与后端服务的连接\n');
    
    // 测试HTTP连接
    const httpOk = await testHttpConnection();
    
    // 测试WebSocket连接
    const wsOk = await testWebSocketConnection();
    
    // 测试API端点
    const apiOk = await testApiEndpoints();
    
    console.log('\n📊 测试结果总结:');
    console.log(`HTTP连接: ${httpOk ? '✅ 正常' : '❌ 失败'}`);
    console.log(`WebSocket连接: ${wsOk ? '✅ 正常' : '❌ 失败'}`);
    console.log(`API端点: ${apiOk ? '✅ 正常' : '❌ 失败'}`);
    
    if (httpOk && wsOk && apiOk) {
        console.log('\n🎉 所有连接测试通过！VS Code插件应该能够正常连接到后端服务。');
        console.log('\n📋 下一步操作:');
        console.log('1. 在VS Code中按 Ctrl+Shift+P 打开命令面板');
        console.log('2. 输入 "AgentScope: Start Agent System" 并执行');
        console.log('3. 或者点击状态栏的 "$(robot) AgentScope" 按钮');
        console.log('4. 或者使用快捷键 Ctrl+Shift+A 打开仪表板');
    } else {
        console.log('\n❌ 连接测试失败，请检查后端服务是否正常运行。');
    }
}

// 检查是否安装了依赖
try {
    require('axios');
    require('ws');
    main().catch(console.error);
} catch (error) {
    console.log('📦 正在安装测试依赖...');
    const { execSync } = require('child_process');
    try {
        execSync('npm install axios ws', { stdio: 'inherit' });
        console.log('✅ 依赖安装完成，重新运行测试...\n');
        main().catch(console.error);
    } catch (installError) {
        console.error('❌ 依赖安装失败:', installError.message);
        console.log('请手动安装: npm install axios ws');
    }
}
