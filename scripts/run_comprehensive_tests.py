#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试运行脚本 - 自动化运行所有测试套件
"""

import asyncio
import json
import logging
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.vscode_plugin_test_suite import VSCodePluginTestSuite
from tests.augment_integration_test_suite import AugmentIntegrationTestSuite
from tests.test_performance import TestSystemIntegrationPerformance


class ComprehensiveTestRunner:
    """综合测试运行器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 测试套件
        self.test_suites = {}
        self.test_results = {}
        
        # 配置
        self.backend_url = self.config.get("backend_url", "http://localhost:8000")
        self.run_performance_tests = self.config.get("run_performance_tests", True)
        self.run_vscode_tests = self.config.get("run_vscode_tests", True)
        self.run_augment_tests = self.config.get("run_augment_tests", True)
        
        self.logger.info("Comprehensive test runner initialized")
    
    async def setup_test_environment(self):
        """设置测试环境"""
        self.logger.info("Setting up comprehensive test environment...")
        
        try:
            # 检查后端服务是否运行
            await self._ensure_backend_running()
            
            # 初始化测试套件
            if self.run_vscode_tests:
                self.test_suites["vscode"] = VSCodePluginTestSuite(self.backend_url)
            
            if self.run_augment_tests:
                self.test_suites["augment"] = AugmentIntegrationTestSuite(self.backend_url)
            
            if self.run_performance_tests:
                self.test_suites["performance"] = TestSystemIntegrationPerformance()
            
            self.logger.info("Test environment setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            raise
    
    async def _ensure_backend_running(self):
        """确保后端服务正在运行"""
        import requests
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                self.logger.info("Backend service is running")
                return
        except requests.RequestException:
            pass
        
        self.logger.info("Starting backend service...")
        
        # 启动后端服务
        backend_process = subprocess.Popen([
            sys.executable, "-m", "agentscope_integration.main",
            "--host", "localhost",
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务启动
        for _ in range(30):
            try:
                response = requests.get(f"{self.backend_url}/health", timeout=5)
                if response.status_code == 200:
                    self.logger.info("Backend service started successfully")
                    return
            except requests.RequestException:
                pass
            
            await asyncio.sleep(2)
        
        raise RuntimeError("Failed to start backend service")
    
    async def run_unit_tests(self) -> Dict[str, Any]:
        """运行单元测试"""
        self.logger.info("Running unit tests...")
        
        try:
            # 运行pytest
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/test_agents.py",
                "tests/test_mcp_integration.py",
                "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            success = result.returncode == 0
            
            return {
                "test_type": "unit_tests",
                "status": "passed" if success else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": 0  # pytest会在输出中显示时间
            }
            
        except Exception as e:
            return {
                "test_type": "unit_tests",
                "status": "error",
                "error": str(e),
                "duration": 0
            }
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """运行集成测试"""
        self.logger.info("Running integration tests...")
        
        integration_results = {}
        
        # VS Code插件测试
        if "vscode" in self.test_suites:
            self.logger.info("Running VS Code plugin tests...")
            start_time = time.time()
            
            try:
                vscode_result = await self.test_suites["vscode"].run_all_tests()
                vscode_result["duration"] = time.time() - start_time
                integration_results["vscode"] = vscode_result
                
            except Exception as e:
                integration_results["vscode"] = {
                    "status": "error",
                    "message": f"VS Code tests failed: {e}",
                    "duration": time.time() - start_time
                }
        
        # Augment集成测试
        if "augment" in self.test_suites:
            self.logger.info("Running Augment integration tests...")
            start_time = time.time()
            
            try:
                augment_result = await self.test_suites["augment"].run_all_tests()
                augment_result["duration"] = time.time() - start_time
                integration_results["augment"] = augment_result
                
            except Exception as e:
                integration_results["augment"] = {
                    "status": "error",
                    "message": f"Augment tests failed: {e}",
                    "duration": time.time() - start_time
                }
        
        return {
            "test_type": "integration_tests",
            "status": "completed",
            "results": integration_results,
            "total_duration": sum(r.get("duration", 0) for r in integration_results.values())
        }
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """运行性能测试"""
        if not self.run_performance_tests or "performance" not in self.test_suites:
            return {
                "test_type": "performance_tests",
                "status": "skipped",
                "message": "Performance tests disabled"
            }
        
        self.logger.info("Running performance tests...")
        
        try:
            start_time = time.time()
            
            # 运行性能测试
            performance_suite = self.test_suites["performance"]
            
            # 端到端性能测试
            e2e_result = await performance_suite.test_end_to_end_performance()
            
            # 压力测试
            stress_result = await performance_suite.test_stress_test()
            
            duration = time.time() - start_time
            
            return {
                "test_type": "performance_tests",
                "status": "completed",
                "results": {
                    "end_to_end": e2e_result,
                    "stress_test": stress_result
                },
                "duration": duration
            }
            
        except Exception as e:
            return {
                "test_type": "performance_tests",
                "status": "error",
                "message": f"Performance tests failed: {e}",
                "duration": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("Starting comprehensive test execution...")
        
        overall_start_time = time.time()
        
        try:
            # 设置测试环境
            await self.setup_test_environment()
            
            # 运行各类测试
            test_results = {}
            
            # 1. 单元测试
            self.logger.info("=== Running Unit Tests ===")
            test_results["unit"] = await self.run_unit_tests()
            
            # 2. 集成测试
            self.logger.info("=== Running Integration Tests ===")
            test_results["integration"] = await self.run_integration_tests()
            
            # 3. 性能测试
            self.logger.info("=== Running Performance Tests ===")
            test_results["performance"] = await self.run_performance_tests()
            
            # 生成综合报告
            overall_duration = time.time() - overall_start_time
            report = self._generate_comprehensive_report(test_results, overall_duration)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Comprehensive test execution failed: {e}")
            return {
                "status": "error",
                "message": f"Test execution failed: {e}",
                "duration": time.time() - overall_start_time
            }
    
    def _generate_comprehensive_report(self, test_results: Dict[str, Any], 
                                     overall_duration: float) -> Dict[str, Any]:
        """生成综合测试报告"""
        report = {
            "test_execution_summary": {
                "start_time": time.time() - overall_duration,
                "end_time": time.time(),
                "total_duration": overall_duration,
                "test_suites_run": len(test_results)
            },
            "results": test_results,
            "overall_status": "unknown",
            "summary_statistics": {},
            "recommendations": []
        }
        
        # 计算总体状态
        all_passed = True
        any_errors = False
        
        for test_type, result in test_results.items():
            if result.get("status") == "error":
                any_errors = True
                all_passed = False
            elif result.get("status") == "failed":
                all_passed = False
        
        if any_errors:
            report["overall_status"] = "error"
        elif all_passed:
            report["overall_status"] = "passed"
        else:
            report["overall_status"] = "failed"
        
        # 计算统计信息
        stats = {
            "total_test_suites": len(test_results),
            "passed_suites": 0,
            "failed_suites": 0,
            "error_suites": 0,
            "skipped_suites": 0
        }
        
        for result in test_results.values():
            status = result.get("status", "unknown")
            if status == "passed" or status == "completed":
                stats["passed_suites"] += 1
            elif status == "failed":
                stats["failed_suites"] += 1
            elif status == "error":
                stats["error_suites"] += 1
            elif status == "skipped":
                stats["skipped_suites"] += 1
        
        report["summary_statistics"] = stats
        
        # 生成建议
        recommendations = []
        
        if stats["failed_suites"] > 0:
            recommendations.append("Some test suites failed. Review failed tests and fix issues before deployment.")
        
        if stats["error_suites"] > 0:
            recommendations.append("Test execution errors occurred. Check test environment and dependencies.")
        
        if overall_duration > 600:  # 10分钟
            recommendations.append("Test execution took longer than expected. Consider optimizing test performance.")
        
        if not recommendations:
            recommendations.append("All tests passed successfully. System is ready for deployment.")
        
        report["recommendations"] = recommendations
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str = None):
        """保存测试报告"""
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f"test_reports/comprehensive_test_report_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Test report saved to: {output_file}")
    
    def print_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST EXECUTION REPORT")
        print("="*80)
        
        summary = report["test_execution_summary"]
        stats = report["summary_statistics"]
        
        print(f"Execution Time: {summary['total_duration']:.1f} seconds")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print(f"Test Suites Run: {summary['test_suites_run']}")
        
        print(f"\nResults Summary:")
        print(f"  Passed: {stats['passed_suites']}")
        print(f"  Failed: {stats['failed_suites']}")
        print(f"  Errors: {stats['error_suites']}")
        print(f"  Skipped: {stats['skipped_suites']}")
        
        print(f"\nDetailed Results:")
        for test_type, result in report["results"].items():
            status = result.get("status", "unknown")
            duration = result.get("duration", 0)
            
            status_icon = {
                "passed": "✅",
                "completed": "✅", 
                "failed": "❌",
                "error": "⚠️",
                "skipped": "⏭️"
            }.get(status, "❓")
            
            print(f"  {status_icon} {test_type.title()}: {status} ({duration:.1f}s)")
        
        print(f"\nRecommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        print("="*80)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Run comprehensive AgentScope tests")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--output", help="Output report path")
    parser.add_argument("--no-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--no-vscode", action="store_true", help="Skip VS Code tests")
    parser.add_argument("--no-augment", action="store_true", help="Skip Augment tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # 应用命令行参数
    config["run_performance_tests"] = not args.no_performance
    config["run_vscode_tests"] = not args.no_vscode
    config["run_augment_tests"] = not args.no_augment
    
    # 运行测试
    runner = ComprehensiveTestRunner(config)
    report = await runner.run_all_tests()
    
    # 保存和显示报告
    runner.save_report(report, args.output)
    runner.print_summary(report)
    
    # 设置退出码
    if report["overall_status"] == "passed":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
