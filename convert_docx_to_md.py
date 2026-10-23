#!/usr/bin/env python3
"""
将Word文档转换为Markdown格式
"""

import os
import re
from pathlib import Path
from docx import Document
import docx2txt

def clean_text(text):
    """清理文本格式"""
    # 移除多余的空行
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    # 移除行首行尾空格
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines)

def extract_text_with_formatting(docx_path):
    """提取Word文档内容并保持基本格式"""
    try:
        # 使用docx2txt提取基本文本
        text = docx2txt.process(docx_path)
        
        # 使用python-docx获取更详细的格式信息
        doc = Document(docx_path)
        
        formatted_content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                # 检查是否是标题
                if paragraph.style.name.startswith('Heading'):
                    level = int(paragraph.style.name.split()[-1]) if paragraph.style.name.split()[-1].isdigit() else 1
                    formatted_content.append('#' * level + ' ' + paragraph.text.strip())
                else:
                    # 检查是否是列表项
                    if paragraph.text.strip().startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                        formatted_content.append('- ' + paragraph.text.strip().lstrip('•-*').strip())
                    else:
                        formatted_content.append(paragraph.text.strip())
                
                formatted_content.append('')  # 添加空行
        
        # 处理表格
        for table in doc.tables:
            formatted_content.append('\n| 列1 | 列2 | 列3 |')
            formatted_content.append('|-----|-----|-----|')
            
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text.strip())
                formatted_content.append('| ' + ' | '.join(row_data) + ' |')
            
            formatted_content.append('')
        
        return clean_text('\n'.join(formatted_content))
        
    except Exception as e:
        print(f"处理文档时出错: {e}")
        # 如果格式化提取失败，使用简单文本提取
        return clean_text(docx2txt.process(docx_path))

def convert_docx_to_markdown(docx_path, output_dir="docs/wx_docs"):
    """将单个Word文档转换为Markdown"""
    docx_path = Path(docx_path)
    output_dir = Path(output_dir)
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成输出文件名
    md_filename = docx_path.stem + '.md'
    md_path = output_dir / md_filename
    
    print(f"正在转换: {docx_path.name} -> {md_filename}")
    
    try:
        # 提取文档内容
        content = extract_text_with_formatting(docx_path)
        
        # 添加文档头部信息
        header = f"""# {docx_path.stem}

> 原始文档: {docx_path.name}
> 转换时间: {Path().cwd()}
> 文档类型: 西安智慧教育平台文档

---

"""
        
        # 写入Markdown文件
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(header + content)
        
        print(f"✅ 转换完成: {md_path}")
        return md_path
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return None

def main():
    """主函数"""
    # 处理西安目录下的文档
    xian_dir = Path("docs/西安")
    
    if not xian_dir.exists():
        print("❌ 西安目录不存在")
        return
    
    # 查找所有Word文档
    docx_files = list(xian_dir.glob("*.docx"))
    
    if not docx_files:
        print("❌ 未找到Word文档")
        return
    
    print(f"📄 找到 {len(docx_files)} 个Word文档")
    
    converted_files = []
    
    # 转换每个文档
    for docx_file in docx_files:
        md_file = convert_docx_to_markdown(docx_file, "docs/wx_docs")
        if md_file:
            converted_files.append(md_file)
    
    print(f"\n🎉 转换完成! 共转换 {len(converted_files)} 个文档:")
    for md_file in converted_files:
        print(f"  - {md_file}")
    
    # 创建索引文件
    create_index_file(converted_files)

def create_index_file(md_files):
    """创建文档索引"""
    index_content = """# 西安智慧教育平台文档

本目录包含西安智慧教育平台相关的技术文档。

## 文档列表

"""
    
    for md_file in md_files:
        filename = md_file.name
        title = md_file.stem
        index_content += f"- [{title}](./{filename})\n"
    
    index_content += """
## 文档说明

这些文档包含了西安智慧教育平台的详细技术规范，包括：

1. **系统架构设计**: 平台的整体架构和技术选型
2. **性能指标**: 系统并发数及性能相关指标
3. **安全规范**: 系统安全设计和实现要求

## 使用建议

在分析系统性能时，请仔细阅读相关文档，特别注意：

- 系统并发处理能力
- 性能指标要求
- 扩展性设计
- 安全性要求

"""
    
    index_path = Path("docs/wx_docs/README.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"📋 创建索引文件: {index_path}")

if __name__ == "__main__":
    main()