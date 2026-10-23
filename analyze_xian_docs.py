#!/usr/bin/env python3
"""
分析西安智慧教育大平台文档中的性能指标
"""

import os
import re
from pathlib import Path
from docx import Document
import docx2txt

def extract_performance_metrics(text):
    """提取性能相关指标"""
    metrics = {
        "并发数": [],
        "用户数": [],
        "响应时间": [],
        "吞吐量": [],
        "TPS": [],
        "QPS": [],
        "CPU": [],
        "内存": [],
        "存储": [],
        "带宽": [],
        "可用性": [],
        "性能指标": []
    }
    
    # 定义匹配模式
    patterns = {
        "并发数": [
            r'并发.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:个|人|次|万|千)?',
            r'同时.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:个|人|次|万|千)?.*?用户',
            r'concurrent.*?(\d+(?:,\d+)*(?:\.\d+)?)',
        ],
        "用户数": [
            r'用户.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:个|人|万|千)',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:万|千)?\s*用户',
            r'users?.*?(\d+(?:,\d+)*(?:\.\d+)?)',
        ],
        "响应时间": [
            r'响应时间.*?(\d+(?:\.\d+)?)\s*(?:秒|ms|毫秒|s)',
            r'response.*?time.*?(\d+(?:\.\d+)?)\s*(?:ms|s|秒)',
            r'延迟.*?(\d+(?:\.\d+)?)\s*(?:秒|ms|毫秒)',
        ],
        "吞吐量": [
            r'吞吐量.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:次/秒|/s|tps|qps)',
            r'throughput.*?(\d+(?:,\d+)*(?:\.\d+)?)',
        ],
        "TPS": [
            r'TPS.*?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?:事务|transaction).*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:次/秒|/s)',
        ],
        "QPS": [
            r'QPS.*?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?:查询|query).*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:次/秒|/s)',
        ],
        "CPU": [
            r'CPU.*?(\d+(?:\.\d+)?)\s*(?:%|核|个)',
            r'处理器.*?(\d+(?:\.\d+)?)\s*(?:%|核|个)',
        ],
        "内存": [
            r'内存.*?(\d+(?:\.\d+)?)\s*(?:GB|MB|G|M)',
            r'RAM.*?(\d+(?:\.\d+)?)\s*(?:GB|MB|G|M)',
            r'memory.*?(\d+(?:\.\d+)?)\s*(?:GB|MB|G|M)',
        ],
        "存储": [
            r'存储.*?(\d+(?:\.\d+)?)\s*(?:TB|GB|T|G)',
            r'硬盘.*?(\d+(?:\.\d+)?)\s*(?:TB|GB|T|G)',
            r'storage.*?(\d+(?:\.\d+)?)\s*(?:TB|GB|T|G)',
        ],
        "带宽": [
            r'带宽.*?(\d+(?:\.\d+)?)\s*(?:Mbps|Gbps|M|G)',
            r'bandwidth.*?(\d+(?:\.\d+)?)\s*(?:Mbps|Gbps|M|G)',
        ],
        "可用性": [
            r'可用性.*?(\d+(?:\.\d+)?)\s*%',
            r'availability.*?(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%.*?可用',
        ]
    }
    
    # 搜索各种指标
    for metric_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end].strip()
                
                metrics[metric_type].append({
                    "value": match.group(1),
                    "context": context,
                    "full_match": match.group(0)
                })
    
    # 查找性能相关的表格和段落
    performance_keywords = [
        "性能指标", "系统性能", "技术指标", "配置要求", "硬件配置",
        "软件配置", "系统要求", "技术参数", "性能参数", "运行环境"
    ]
    
    for keyword in performance_keywords:
        pattern = rf'.{{0,100}}{keyword}.{{0,200}}'
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            metrics["性能指标"].append({
                "keyword": keyword,
                "context": match.group(0).strip()
            })
    
    return metrics

def analyze_document(doc_path):
    """分析单个文档"""
    print(f"\n📄 分析文档: {doc_path.name}")
    
    try:
        # 提取文本内容
        text = docx2txt.process(doc_path)
        
        # 使用python-docx获取更详细信息
        doc = Document(doc_path)
        
        # 提取表格内容
        table_content = []
        for table in doc.tables:
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text.strip())
                if any(row_data):  # 只保存非空行
                    table_content.append(" | ".join(row_data))
        
        # 合并文本和表格内容
        full_text = text + "\n" + "\n".join(table_content)
        
        # 提取性能指标
        metrics = extract_performance_metrics(full_text)
        
        return {
            "file_name": doc_path.name,
            "metrics": metrics,
            "full_text": full_text,
            "table_content": table_content
        }
        
    except Exception as e:
        print(f"❌ 处理文档时出错: {e}")
        return None

def compare_metrics(doc1_result, doc2_result):
    """对比两个文档的指标"""
    print("\n" + "="*80)
    print("📊 性能指标对比分析")
    print("="*80)
    
    comparison = {}
    
    # 对比各项指标
    for metric_type in doc1_result["metrics"].keys():
        doc1_values = doc1_result["metrics"][metric_type]
        doc2_values = doc2_result["metrics"][metric_type]
        
        if doc1_values or doc2_values:
            comparison[metric_type] = {
                "doc1": doc1_values,
                "doc2": doc2_values,
                "differences": []
            }
            
            # 分析差异
            if len(doc1_values) != len(doc2_values):
                comparison[metric_type]["differences"].append(
                    f"数量不同: 文档1有{len(doc1_values)}个, 文档2有{len(doc2_values)}个"
                )
            
            # 比较具体数值
            doc1_nums = []
            doc2_nums = []
            
            for item in doc1_values:
                if isinstance(item, dict) and "value" in item:
                    try:
                        num = float(item["value"].replace(",", ""))
                        doc1_nums.append(num)
                    except:
                        pass
            
            for item in doc2_values:
                if isinstance(item, dict) and "value" in item:
                    try:
                        num = float(item["value"].replace(",", ""))
                        doc2_nums.append(num)
                    except:
                        pass
            
            if doc1_nums and doc2_nums:
                if set(doc1_nums) != set(doc2_nums):
                    comparison[metric_type]["differences"].append(
                        f"数值不同: 文档1={doc1_nums}, 文档2={doc2_nums}"
                    )
    
    return comparison

def generate_report(doc1_result, doc2_result, comparison):
    """生成对比报告"""
    report = []
    
    report.append("# 西安智慧教育大平台性能指标对比分析报告\n")
    
    # 文档基本信息
    report.append("## 📋 文档信息\n")
    report.append(f"- **文档1**: {doc1_result['file_name']}")
    report.append(f"- **文档2**: {doc2_result['file_name']}\n")
    
    # 详细对比
    report.append("## 📊 性能指标详细对比\n")
    
    for metric_type, data in comparison.items():
        if data["doc1"] or data["doc2"]:
            report.append(f"### {metric_type}\n")
            
            # 文档1的指标
            if data["doc1"]:
                report.append("#### 文档1 (原版):")
                for item in data["doc1"]:
                    if isinstance(item, dict):
                        if "value" in item:
                            report.append(f"- **{item['value']}** - {item['context']}")
                        elif "context" in item:
                            report.append(f"- {item['context']}")
                report.append("")
            
            # 文档2的指标
            if data["doc2"]:
                report.append("#### 文档2 (专家修改版):")
                for item in data["doc2"]:
                    if isinstance(item, dict):
                        if "value" in item:
                            report.append(f"- **{item['value']}** - {item['context']}")
                        elif "context" in item:
                            report.append(f"- {item['context']}")
                report.append("")
            
            # 差异分析
            if data["differences"]:
                report.append("#### 🔍 差异分析:")
                for diff in data["differences"]:
                    report.append(f"- {diff}")
                report.append("")
            else:
                report.append("#### ✅ 无明显差异\n")
    
    # 总结
    report.append("## 📈 总结\n")
    
    total_metrics_doc1 = sum(len(data["doc1"]) for data in comparison.values())
    total_metrics_doc2 = sum(len(data["doc2"]) for data in comparison.values())
    total_differences = sum(len(data["differences"]) for data in comparison.values())
    
    report.append(f"- **文档1总指标数**: {total_metrics_doc1}")
    report.append(f"- **文档2总指标数**: {total_metrics_doc2}")
    report.append(f"- **发现差异数**: {total_differences}")
    
    if total_differences > 0:
        report.append(f"\n⚠️ **发现{total_differences}处差异，建议重点关注专家修改版的变更内容。**")
    else:
        report.append("\n✅ **两个版本在性能指标方面基本一致。**")
    
    return "\n".join(report)

def main():
    """主函数"""
    docs_dir = Path("docs/西安")
    
    if not docs_dir.exists():
        print("❌ docs/西安 目录不存在")
        return
    
    # 查找Word文档
    docx_files = list(docs_dir.glob("*.docx"))
    
    if len(docx_files) != 2:
        print(f"❌ 期望找到2个Word文档，实际找到{len(docx_files)}个")
        return
    
    print("🚀 开始分析西安智慧教育大平台文档...")
    
    # 分析两个文档
    doc1_result = analyze_document(docx_files[0])
    doc2_result = analyze_document(docx_files[1])
    
    if not doc1_result or not doc2_result:
        print("❌ 文档分析失败")
        return
    
    # 对比分析
    comparison = compare_metrics(doc1_result, doc2_result)
    
    # 生成报告
    report = generate_report(doc1_result, doc2_result, comparison)
    
    # 保存报告
    report_path = Path("docs/西安/性能指标对比分析报告.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 分析完成！报告已保存到: {report_path}")
    
    # 显示简要结果
    print("\n📊 简要结果:")
    for metric_type, data in comparison.items():
        if data["differences"]:
            print(f"  🔍 {metric_type}: 发现差异")
        elif data["doc1"] or data["doc2"]:
            print(f"  ✅ {metric_type}: 无差异")

if __name__ == "__main__":
    main()
