#!/usr/bin/env python3
"""
审批流程快速检索脚本 - OpenClaw Subagent 调用入口
支持索引缓存，避免每次重新计算 embedding

Usage:
    python search_flows.py "查询内容"
    python search_flows.py "采购200万以上怎么审批" --force-update
    
Example:
    python search_flows.py "预付款白名单供应商申请"
"""

import sys
import os
import argparse
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_system import OllamaClient, ApprovalFlowSearcher, log
from index_manager import FlowIndexManager

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_DATA_DIR = Path(os.getenv("RAG_DATA_DIR", str(SKILL_ROOT / "data")))
FLOWS_DIR = os.getenv("RAG_FLOWS_DIR", str(DEFAULT_DATA_DIR / "flows_v2"))


def main():
    parser = argparse.ArgumentParser(description="审批流程检索")
    parser.add_argument("query", help="查询内容")
    parser.add_argument("--flows-dir", default=FLOWS_DIR, help="流程数据目录")
    parser.add_argument("--force-update", action="store_true", help="强制更新索引")
    parser.add_argument("--rebuild", action="store_true", help="重建索引")
    
    args = parser.parse_args()
    
    # 检查 Ollama
    try:
        import requests
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    except Exception as e:
        print(f"❌ 无法连接 Ollama: {e}")
        print("请确保 Ollama 服务已启动: ollama serve")
        sys.exit(1)
    
    # 初始化
    embedder = OllamaClient(OLLAMA_URL)
    
    # 使用索引管理器（支持缓存）
    index_manager = FlowIndexManager(args.flows_dir, embedder)
    
    # 构建或更新索引
    log("正在检查索引...")
    index_manager.build_or_update_index(force_rebuild=(args.rebuild or args.force_update))
    
    # 创建检索器（使用索引管理器的数据）
    searcher = ApprovalFlowSearcher(embedder)
    searcher.flows = index_manager.flows
    searcher.flow_embeddings = index_manager.flow_embeddings
    searcher.level3_groups = index_manager.level3_groups
    
    print()
    answer = searcher.answer(args.query)
    print(answer)


if __name__ == "__main__":
    main()
