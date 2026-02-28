#!/usr/bin/env python3
"""
文档智能分割脚本 - OpenClaw Subagent 调用入口

Usage:
    python split_doc.py <input_file> [output_dir] [department] [category]
    
Example:
    python split_doc.py "/path/to/采购管理制度.md" "./output" "供应链中心" "供应链-采购管理"
"""

import sys
import os
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_system import OllamaClient, SmartDocumentSplitter

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./split_output"
    department = sys.argv[3] if len(sys.argv) > 3 else "供应链中心"
    category = sys.argv[4] if len(sys.argv) > 4 else "供应链-采购管理"
    
    # 检查 Ollama
    try:
        import requests
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        print("✅ Ollama 连接成功")
    except Exception as e:
        print(f"❌ 无法连接 Ollama: {e}")
        print("请确保 Ollama 服务已启动: ollama serve")
        sys.exit(1)
    
    # 构建文档信息
    doc_info = {
        "title": Path(input_file).stem,
        "department": department,
        "category": category,
        "tags": ["制度"],
        "effective_date": "2025-01-01"
    }
    
    # 执行分割
    embedder = OllamaClient(OLLAMA_URL)
    splitter = SmartDocumentSplitter(embedder)
    
    files = splitter.split_document(input_file, output_dir, doc_info)
    
    print(f"\n✅ 分割完成！共生成 {len(files)} 个文件")
    print(f"📁 输出目录: {output_dir}")


if __name__ == "__main__":
    main()
