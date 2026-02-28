#!/usr/bin/env python3
"""
Environment check script for PolicyRAG Skill.

Usage:
    python check_env.py
"""

import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_FLOWS_DIR = Path(os.getenv("RAG_FLOWS_DIR", str(SKILL_ROOT / "data" / "flows_v2")))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def check_ollama() -> bool:
    """Check Ollama service and embedding model."""
    print("\n🔍 Checking Ollama service...")
    try:
        import requests

        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        data = resp.json()
        models = [m.get("name", "") for m in data.get("models", [])]

        print(f"  ✅ Ollama is reachable: {OLLAMA_URL}")
        if "qwen3-embedding:latest" in str(models):
            print("  ✅ qwen3-embedding:latest is installed")
        else:
            print("  ⚠️  qwen3-embedding:latest not found")
            print(f"     Available models: {models[:5]}")
            print("     Install with: ollama pull qwen3-embedding:latest")
        return True
    except Exception as exc:
        print(f"  ❌ Cannot reach Ollama: {exc}")
        print("     Start it with: ollama serve")
        return False


def check_python_deps() -> bool:
    """Check Python dependencies."""
    print("\n🔍 Checking Python dependencies...")
    required = ["numpy", "requests"]
    optional = ["pandas", "xlrd", "openpyxl"]
    ok = True

    for pkg in required:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} is missing")
            ok = False

    for pkg in optional:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg} (optional)")
        except ImportError:
            print(f"  ⚠️  {pkg} is missing (optional)")

    if not ok:
        print("\n  Install dependencies with:")
        print("  pip install numpy requests pandas xlrd openpyxl")
    return ok


def check_skill_files() -> bool:
    """Check required skill files exist."""
    print("\n🔍 Checking skill files...")
    required_files = [
        "SKILL.md",
        "scripts/rag_system.py",
        "scripts/search_flows.py",
        "scripts/split_doc.py",
        "scripts/convert_excel.py",
        "scripts/index_manager.py",
    ]
    ok = True
    for rel in required_files:
        p = SKILL_ROOT / rel
        if p.exists():
            print(f"  ✅ {rel}")
        else:
            print(f"  ❌ {rel} not found")
            ok = False
    return ok


def check_data_files() -> bool:
    """Check flow data directory and files."""
    print("\n🔍 Checking flow data...")
    flows_dir = DEFAULT_FLOWS_DIR
    if not flows_dir.exists():
        print(f"  ⚠️  Flow directory not found: {flows_dir}")
        print("     Set RAG_FLOWS_DIR or create ./data/flows_v2")
        return False

    json_files = list(flows_dir.glob("*_flows.json")) + list(flows_dir.glob("*_v2.json"))
    if not json_files:
        print(f"  ⚠️  No flow JSON files found in: {flows_dir}")
        return False

    print(f"  ✅ Found {len(json_files)} flow files in {flows_dir}")
    for f in json_files[:8]:
        print(f"     - {f.name}")
    if len(json_files) > 8:
        print("     - ...")
    return True


def test_search() -> bool:
    """Run a minimal search test."""
    print("\n🔍 Testing search pipeline...")
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from rag_system import OllamaClient, ApprovalFlowSearcher

        embedder = OllamaClient()
        searcher = ApprovalFlowSearcher(embedder)
        searcher.load_flows(str(DEFAULT_FLOWS_DIR))
        if not searcher.flows:
            print("  ⚠️  No flows loaded, skip search test")
            return False

        results = searcher.search("采购申请", top_k=1)
        if results:
            sim, flow = results[0]
            print(f"  ✅ Search test passed (similarity: {sim:.2%})")
            print(f"     Top match: {flow.get('流程名称', 'N/A')}")
            return True
        print("  ⚠️  Search returned no result")
        return False
    except Exception as exc:
        print(f"  ❌ Search test failed: {exc}")
        return False


def main() -> int:
    print("=" * 60)
    print("PolicyRAG Skill - Environment Check")
    print("=" * 60)
    print(f"Skill root: {SKILL_ROOT}")
    print(f"Default flows dir: {DEFAULT_FLOWS_DIR}")

    checks = {
        "Ollama service": check_ollama(),
        "Python dependencies": check_python_deps(),
        "Skill files": check_skill_files(),
        "Flow data": check_data_files(),
    }

    if all(checks.values()):
        checks["Search test"] = test_search()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, ok in checks.items():
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}: {name}")

    if all(checks.values()):
        print("\nAll checks passed.")
        return 0
    print("\nSome checks failed. Review the messages above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
