#!/usr/bin/env python3
"""
Excel 审批表转换脚本 - OpenClaw Subagent 调用入口

Usage:
    python convert_excel.py <excel_file> [output_dir]
    
Example:
    python convert_excel.py "/path/to/采购管理_审批权责表.xlsx" "./flows_output"
"""

import sys
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_system import ApprovalFlowConverter


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    excel_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./flows_output"
    
    converter = ApprovalFlowConverter()
    flows = converter.convert(excel_file, output_dir)
    
    if flows:
        print(f"\n📋 第一个流程示例：")
        sample = flows[0]
        print(f"   流程名称: {sample['流程名称']}")
        print(f"   审批路径: {sample['审批路径']}")
        print(f"   最终审批: {sample['最终审批人']}")


if __name__ == "__main__":
    main()
