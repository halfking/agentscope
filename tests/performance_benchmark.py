#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope多智能体编程工作流 - 性能基准测试
测试优化架构的性能表现
"""

import asyncio
import time
import statistics
import json
import sys
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# 使用独立测试组件
sys.path.append(str(Path(__file__).parent))
from test_optimized_integration_standalone import (
    MockOptimizedSpecializedAgent, MockAgentScopeWorkflowManager,
    MockAugmentIntegrationHub, MockAugmentMessage, MockAugmentEventType,
    AgentRole, TaskType, AgentTask
)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation: str
    execution_times: List[float]
    memory_usage: List[float]
    success_rate: float
    throughput: float  # 每秒操作数
    
    @property
    def avg_execution_time(self) -> float:
        return statistics.mean(self.execution_times) if self.execution_times else 0
    
    @property
    def p95_execution_time(self) -> float:
        return statistics.quantiles(self.execution_times, n=20)[18] if len(self.execution_times) >= 20 else self.avg_execution_time
    
    @property
    def min_execution_time(self) -> float:
        return min(self.execution_times) if self.execution_times else 0
    
    @property
    def max_execution_time(self) -> float:
        return max(self.execution_times) if self.execution_times else 0


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        self.results: Dict[str, PerformanceMetrics] = {}
        self.test_data = self._generate_test_data()
    
    def _generate_test_data(self) -> Dict[str, Any]:
        """生成测试数据"""
        return {
            "small_tasks": [
                AgentTask(
                    id=f"small_task_{i}",
                    type=TaskType.CODE_ANALYSIS,
                    title=f"小型任务 {i}",
                    description="分析单个函数",
                    parameters={"file_path": f"/test/small_{i}.py", "lines": 50}
                ) for i in range(10)
            ],
            "medium_tasks": [
                AgentTask(
                    id=f"medium_task_{i}",
                    type=TaskType.SECURITY_SCAN,
                    title=f"中型任务 {i}",
                    description="扫描整个模块",
                    parameters={"file_path": f"/test/medium_{i}.py", "lines": 500}
                ) for i in range(10)
            ],
            "large_tasks": [
                AgentTask(
                    id=f"large_task_{i}",
                    type=TaskType.COMPREHENSIVE_ANALYSIS,
                    title=f"大型任务 {i}",
                    description="分析整个项目",
                    parameters={"directory": f"/test/large_project_{i}", "files": 100}
                ) for i in range(5)
            ],
            "augment_messages": [
                MockAugmentMessage(
                    event_type=MockAugmentEventType.CODE_ANALYSIS_REQUEST,
                    content=f"请分析文件 test_{i}.py 的代码质量",
                    context={"current_file": f"/test/test_{i}.py"},
                    source="benchmark",
                    timestamp=time.time()
                ) for i in range(20)
            ]
        }
    
    async def setup_test_environment(self):
        """设置测试环境"""
        # 创建工作流管理器
        workflow_manager = MockAgentScopeWorkflowManager()
        
        # 创建多个智能体实例
        agents = []
        for i in range(3):  # 创建3个代码管理员
            agent = MockOptimizedSpecializedAgent(
                name=f"CodeManager_{i}",
                role=AgentRole.CODE_MANAGER,
                supported_tasks=[TaskType.CODE_ANALYSIS, TaskType.COMPREHENSIVE_ANALYSIS]
            )
            agents.append(agent)
            await workflow_manager.register_agent(agent)
        
        for i in range(2):  # 创建2个合规审核员
            agent = MockOptimizedSpecializedAgent(
                name=f"ComplianceAuditor_{i}",
                role=AgentRole.COMPLIANCE_AUDITOR,
                supported_tasks=[TaskType.SECURITY_SCAN, TaskType.QUALITY_CHECK]
            )
            agents.append(agent)
            await workflow_manager.register_agent(agent)
        
        # 创建Augment集成中心
        augment_hub = MockAugmentIntegrationHub(workflow_manager)
        await augment_hub.start()
        
        return {
            "workflow_manager": workflow_manager,
            "augment_hub": augment_hub,
            "agents": agents
        }
    
    async def benchmark_single_task_execution(self, env) -> PerformanceMetrics:
        """基准测试：单任务执行性能"""
        print("🏃 基准测试：单任务执行性能...")
        
        agent = env["agents"][0]
        execution_times = []
        success_count = 0
        
        # 测试小型任务
        for task in self.test_data["small_tasks"]:
            start_time = time.time()
            try:
                result = await agent.execute_task(task)
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
                if result.status.value == "completed":
                    success_count += 1
            except Exception as e:
                print(f"任务执行失败: {e}")
        
        success_rate = success_count / len(self.test_data["small_tasks"])
        throughput = len(self.test_data["small_tasks"]) / sum(execution_times) if execution_times else 0
        
        metrics = PerformanceMetrics(
            operation="single_task_execution",
            execution_times=execution_times,
            memory_usage=[],  # 简化版本不测试内存
            success_rate=success_rate,
            throughput=throughput
        )
        
        print(f"  ✅ 平均执行时间: {metrics.avg_execution_time:.3f}s")
        print(f"  ✅ 成功率: {metrics.success_rate:.2%}")
        print(f"  ✅ 吞吐量: {metrics.throughput:.2f} tasks/s")
        
        return metrics
    
    async def benchmark_concurrent_task_execution(self, env) -> PerformanceMetrics:
        """基准测试：并发任务执行性能"""
        print("🏃 基准测试：并发任务执行性能...")
        
        agents = env["agents"]
        execution_times = []
        success_count = 0
        
        # 并发执行中型任务
        start_time = time.time()
        tasks = []
        
        for i, task in enumerate(self.test_data["medium_tasks"]):
            agent = agents[i % len(agents)]  # 轮询分配智能体
            tasks.append(agent.execute_task(task))
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_execution_time = time.time() - start_time
            
            for result in results:
                if not isinstance(result, Exception) and result.status.value == "completed":
                    success_count += 1
                    execution_times.append(result.execution_time)
        
        except Exception as e:
            print(f"并发执行失败: {e}")
        
        success_rate = success_count / len(self.test_data["medium_tasks"])
        throughput = len(self.test_data["medium_tasks"]) / total_execution_time if total_execution_time > 0 else 0
        
        metrics = PerformanceMetrics(
            operation="concurrent_task_execution",
            execution_times=execution_times,
            memory_usage=[],
            success_rate=success_rate,
            throughput=throughput
        )
        
        print(f"  ✅ 平均执行时间: {metrics.avg_execution_time:.3f}s")
        print(f"  ✅ 成功率: {metrics.success_rate:.2%}")
        print(f"  ✅ 吞吐量: {metrics.throughput:.2f} tasks/s")
        
        return metrics
    
    async def benchmark_workflow_management(self, env) -> PerformanceMetrics:
        """基准测试：工作流管理性能"""
        print("🏃 基准测试：工作流管理性能...")
        
        workflow_manager = env["workflow_manager"]
        execution_times = []
        success_count = 0
        
        # 测试工作流创建和执行
        for task in self.test_data["large_tasks"]:
            start_time = time.time()
            try:
                workflow_id = await workflow_manager.create_workflow(task)
                status = await workflow_manager.get_workflow_status(workflow_id)
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
                
                if status and status["status"] == "completed":
                    success_count += 1
            except Exception as e:
                print(f"工作流执行失败: {e}")
        
        success_rate = success_count / len(self.test_data["large_tasks"])
        throughput = len(self.test_data["large_tasks"]) / sum(execution_times) if execution_times else 0
        
        metrics = PerformanceMetrics(
            operation="workflow_management",
            execution_times=execution_times,
            memory_usage=[],
            success_rate=success_rate,
            throughput=throughput
        )
        
        print(f"  ✅ 平均执行时间: {metrics.avg_execution_time:.3f}s")
        print(f"  ✅ 成功率: {metrics.success_rate:.2%}")
        print(f"  ✅ 吞吐量: {metrics.throughput:.2f} workflows/s")
        
        return metrics
    
    async def benchmark_augment_integration(self, env) -> PerformanceMetrics:
        """基准测试：Augment集成性能"""
        print("🏃 基准测试：Augment集成性能...")
        
        augment_hub = env["augment_hub"]
        execution_times = []
        success_count = 0
        
        # 设置结果捕获
        processed_messages = []
        def capture_result(data):
            processed_messages.append(data)
        
        augment_hub.register_event_callback("message_processed", capture_result)
        
        # 测试Augment消息处理
        start_time = time.time()
        for message in self.test_data["augment_messages"]:
            try:
                response = await augment_hub.process_augment_message(message)
                if response["status"] == "queued":
                    success_count += 1
            except Exception as e:
                print(f"Augment消息处理失败: {e}")
        
        # 等待所有消息处理完成
        max_wait = 10  # 10秒超时
        for _ in range(max_wait * 10):
            if len(processed_messages) >= success_count:
                break
            await asyncio.sleep(0.1)
        
        total_execution_time = time.time() - start_time
        
        # 计算执行时间
        for _ in range(success_count):
            execution_times.append(total_execution_time / success_count)
        
        success_rate = success_count / len(self.test_data["augment_messages"])
        throughput = len(self.test_data["augment_messages"]) / total_execution_time if total_execution_time > 0 else 0
        
        metrics = PerformanceMetrics(
            operation="augment_integration",
            execution_times=execution_times,
            memory_usage=[],
            success_rate=success_rate,
            throughput=throughput
        )
        
        print(f"  ✅ 平均执行时间: {metrics.avg_execution_time:.3f}s")
        print(f"  ✅ 成功率: {metrics.success_rate:.2%}")
        print(f"  ✅ 吞吐量: {metrics.throughput:.2f} messages/s")
        
        return metrics
    
    async def benchmark_memory_efficiency(self, env) -> PerformanceMetrics:
        """基准测试：内存效率"""
        print("🏃 基准测试：内存效率...")
        
        agent = env["agents"][0]
        execution_times = []
        
        # 测试长期记忆存储和检索
        start_time = time.time()
        
        # 存储大量数据到长期记忆
        for i in range(100):
            await agent.long_term_memory.store(
                "benchmark_test",
                f"key_{i}",
                {"data": f"test_data_{i}", "index": i, "timestamp": time.time()}
            )
        
        # 检索数据
        retrieved_count = 0
        for i in range(100):
            data = await agent.long_term_memory.get("benchmark_test", f"key_{i}")
            if data:
                retrieved_count += 1
        
        total_time = time.time() - start_time
        execution_times.append(total_time)
        
        success_rate = retrieved_count / 100
        throughput = 200 / total_time  # 100次存储 + 100次检索
        
        metrics = PerformanceMetrics(
            operation="memory_efficiency",
            execution_times=execution_times,
            memory_usage=[],
            success_rate=success_rate,
            throughput=throughput
        )
        
        print(f"  ✅ 总执行时间: {total_time:.3f}s")
        print(f"  ✅ 数据检索成功率: {success_rate:.2%}")
        print(f"  ✅ 内存操作吞吐量: {throughput:.2f} ops/s")
        
        return metrics
    
    async def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("🚀 开始运行性能基准测试...")
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 设置测试环境
            env = await self.setup_test_environment()
            
            # 运行基准测试
            self.results["single_task"] = await self.benchmark_single_task_execution(env)
            self.results["concurrent_task"] = await self.benchmark_concurrent_task_execution(env)
            self.results["workflow_management"] = await self.benchmark_workflow_management(env)
            self.results["augment_integration"] = await self.benchmark_augment_integration(env)
            self.results["memory_efficiency"] = await self.benchmark_memory_efficiency(env)
            
            # 生成报告
            self.generate_performance_report()
            
            return True
            
        except Exception as e:
            print(f"\n❌ 基准测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # 清理
            if 'env' in locals():
                await env["augment_hub"].stop()
    
    def generate_performance_report(self):
        """生成性能报告"""
        print("\n" + "="*80)
        print("📊 性能基准测试报告")
        print("="*80)
        
        # 总体性能概览
        print("\n🎯 总体性能概览:")
        total_operations = sum(len(m.execution_times) for m in self.results.values())
        avg_success_rate = statistics.mean([m.success_rate for m in self.results.values()])
        avg_throughput = statistics.mean([m.throughput for m in self.results.values()])
        
        print(f"  • 总操作数: {total_operations}")
        print(f"  • 平均成功率: {avg_success_rate:.2%}")
        print(f"  • 平均吞吐量: {avg_throughput:.2f} ops/s")
        
        # 详细性能指标
        print("\n📈 详细性能指标:")
        for operation, metrics in self.results.items():
            print(f"\n  🔹 {operation.replace('_', ' ').title()}:")
            print(f"    - 平均执行时间: {metrics.avg_execution_time:.3f}s")
            print(f"    - P95执行时间: {metrics.p95_execution_time:.3f}s")
            print(f"    - 最小执行时间: {metrics.min_execution_time:.3f}s")
            print(f"    - 最大执行时间: {metrics.max_execution_time:.3f}s")
            print(f"    - 成功率: {metrics.success_rate:.2%}")
            print(f"    - 吞吐量: {metrics.throughput:.2f} ops/s")
        
        # 性能评级
        print("\n⭐ 性能评级:")
        self.evaluate_performance()
        
        # 保存报告到文件
        self.save_report_to_file()
    
    def evaluate_performance(self):
        """评估性能等级"""
        # 基于预设基准评估性能
        benchmarks = {
            "single_task": {"target_time": 0.1, "target_success": 0.95},
            "concurrent_task": {"target_time": 0.2, "target_success": 0.90},
            "workflow_management": {"target_time": 0.5, "target_success": 0.95},
            "augment_integration": {"target_time": 0.3, "target_success": 0.85},
            "memory_efficiency": {"target_throughput": 50, "target_success": 0.95}
        }
        
        grades = []
        for operation, metrics in self.results.items():
            if operation in benchmarks:
                benchmark = benchmarks[operation]
                
                # 评估执行时间
                time_score = 100 if metrics.avg_execution_time <= benchmark.get("target_time", 1.0) else 50
                
                # 评估成功率
                success_score = 100 if metrics.success_rate >= benchmark.get("target_success", 0.9) else 50
                
                # 评估吞吐量（如果有目标）
                throughput_score = 100
                if "target_throughput" in benchmark:
                    throughput_score = 100 if metrics.throughput >= benchmark["target_throughput"] else 50
                
                # 综合评分
                overall_score = (time_score + success_score + throughput_score) / 3
                grades.append(overall_score)
                
                grade = "A" if overall_score >= 90 else "B" if overall_score >= 70 else "C"
                print(f"    {operation.replace('_', ' ').title()}: {grade} ({overall_score:.0f}分)")
        
        # 总体评级
        overall_grade = statistics.mean(grades) if grades else 0
        final_grade = "A" if overall_grade >= 90 else "B" if overall_grade >= 70 else "C"
        print(f"\n  🏆 总体评级: {final_grade} ({overall_grade:.0f}分)")
        
        if final_grade == "A":
            print("  🎉 优秀！系统性能表现卓越")
        elif final_grade == "B":
            print("  👍 良好！系统性能满足要求")
        else:
            print("  ⚠️ 需要优化！建议进行性能调优")
    
    def save_report_to_file(self):
        """保存报告到文件"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "results": {
                operation: {
                    "avg_execution_time": metrics.avg_execution_time,
                    "p95_execution_time": metrics.p95_execution_time,
                    "min_execution_time": metrics.min_execution_time,
                    "max_execution_time": metrics.max_execution_time,
                    "success_rate": metrics.success_rate,
                    "throughput": metrics.throughput,
                    "operation_count": len(metrics.execution_times)
                }
                for operation, metrics in self.results.items()
            }
        }
        
        report_file = Path("performance_benchmark_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 性能报告已保存到: {report_file}")


async def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    success = await benchmark.run_all_benchmarks()
    
    if success:
        print("\n🌟 性能基准测试完成！")
        sys.exit(0)
    else:
        print("\n⚠️ 性能基准测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
