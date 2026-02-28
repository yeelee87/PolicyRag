---
name: "PolicyRAG Skill"
description: |
  PolicyRAG Skill - 基于本地 qwen3-embedding 的文档处理与检索系统。
  功能包括：
  1. 文档智能分割（Word/Markdown）- 基于语义相似度自动分块
  2. Excel 审批流程转换 - 将审批权责表转换为结构化数据
  3. 审批流程检索 - 语义检索审批流程，支持分支流程展示
  4. 制度文件检索 - 语义检索制度文档
  
  使用场景：
  - 用户需要分割长文档为语义相关的块
  - 用户需要转换 Excel 审批表为可检索格式
  - 用户查询"采购200万以上怎么审批"等审批流程问题
  - 用户查询制度条款、适用范围、注意事项
  - 关键词触发："检索这份文件"、"检索制度"、"审批流程"、"制度查询"
tools:
  - name: split_document
    description: 智能分割文档（Markdown/Word）为语义相关的块
    parameters:
      - name: input_file
        type: string
        description: 输入文件路径（.md 或 .docx）
        required: true
      - name: output_dir
        type: string
        description: 输出目录路径
        required: true
      - name: doc_info
        type: object
        description: 文档元信息（title, department, category, tags, effective_date）
        required: false
    script: scripts/rag_system.py
    entry_point: main
    
  - name: convert_excel_flows
    description: 转换 Excel 审批权责表为结构化 JSON
    parameters:
      - name: excel_file
        type: string
        description: Excel 文件路径
        required: true
      - name: output_dir
        type: string
        description: 输出目录路径
        required: true
    script: scripts/rag_system.py
    entry_point: main
    
  - name: search_approval_flows
    description: 语义检索审批流程
    parameters:
      - name: query
        type: string
        description: 用户查询内容
        required: true
      - name: flows_dir
        type: string
        description: 流程数据目录（默认 ${RAG_FLOWS_DIR}）
        required: false
    script: scripts/rag_system.py
    entry_point: main
    
  - name: index_documents
    description: 为制度文件建立语义索引
    parameters:
      - name: docs_dir
        type: string
        description: 制度文件目录
        required: true
      - name: index_dir
        type: string
        description: 索引输出目录
        required: true
    script: scripts/rag_system.py
    entry_point: main
    
  - name: search_documents
    description: 语义检索制度文件
    parameters:
      - name: query
        type: string
        description: 用户查询内容
        required: true
      - name: index_dir
        type: string
        description: 索引目录路径
        required: true
    script: scripts/rag_system.py
    entry_point: main
---

# PolicyRAG Skill

基于本地 qwen3-embedding 的智能文档处理与检索系统。

## 功能概述

### 1. 文档智能分割
使用本地 qwen3-embedding 模型进行语义分块，适用于：
- 长制度文档的智能拆分
- 基于语义相似度合并相关段落
- 自动生成 YAML frontmatter 和索引

### 2. Excel 审批流程转换
将 Excel 审批权责表转换为结构化数据：
- 解析多级流程结构（一级→二级→三级→四级）
- 识别审批节点层级（①②③④）
- 区分"审核"与"审批"
- 处理并行审批（相同数字）

### 3. 审批流程语义检索
基于 embedding 的审批流程智能检索：
- 支持自然语言查询
- 自动分组三级流程下的四级分支
- 可视化 ASCII 流程图
- 多分支时列出所有选项

### 4. 制度文件检索
对分割后的制度文档进行语义检索

## 使用指南

### 文档分割

```python
# 使用 split_document 工具
input_file: "/path/to/采购管理制度.md"
output_dir: "/path/to/output/采购管理制度_split"
doc_info:
  title: "采购管理制度"
  department: "供应链中心"
  category: "供应链-采购管理"
  tags: ["采购", "制度"]
  effective_date: "2025-01-01"
```

输出：
- 01_总则.md、02_采购申请.md ... 等分割文件
- 00_制度总览.md 索引导航

### Excel 转换

```python
# 使用 convert_excel_flows 工具
excel_file: "/path/to/采购管理_审批权责表.xlsx"
output_dir: "/path/to/flows_output"
```

输出：
- 采购管理_审批权责表_flows.json（结构化流程数据）

### 审批流程检索

```python
# 使用 search_approval_flows 工具
query: "采购200万以上怎么审批"
flows_dir: "${RAG_FLOWS_DIR}"
```

检索逻辑：
1. 加载 flows_dir 下的所有 *_flows.json 文件
2. 计算 query 与每个流程的 embedding 相似度
3. 返回最佳匹配及同三级流程下的所有分支
4. 生成 ASCII 流程图展示审批路径

### 制度文件检索

```python
# 先建立索引
index_documents:
  docs_dir: "/path/to/split_documents"
  index_dir: "/path/to/index"

# 再检索
search_documents:
  query: "预付款申请流程"
  index_dir: "/path/to/index"
```

## 数据目录结构

```
${RAG_DATA_DIR}/
├── flows_v2/                    # 审批流程数据
│   ├── 供应商管理_审批权责表_flows.json
│   ├── 招标管理_审批权责表改_flows.json
│   └── 采购管理_审批权责表2025年修订版_flows.json
├── 测试输出/                     # 分割后的制度文档
│   └── 会计制度_2025_split/
│       ├── 00_制度总览.md
│       ├── 01_总则.md
│       └── ...
└── index/                       # 制度文件索引
    └── document_index.json
```

## 技术栈

- **Embedding 模型**: qwen3-embedding:latest（本地 Ollama）
- **相似度计算**: 余弦相似度
- **语义阈值**: 0.75（低于此值视为新主题）
- **检索阈值**: 0.5（低于此值返回建议列表）

## 常见查询示例

**审批流程查询：**
- "预付款白名单供应商申请"
- "采购200万以上怎么审批"
- "品类采购策略审批"
- "直管企业IT采购"
- "供应商解冻流程"

**制度文件查询：**
- "采购申请需要哪些材料"
- "预付款的比例限制"
- "招标的适用范围"

## 注意事项

1. **首次运行**：加载 embedding 模型需要 10-30 秒
2. **文件变化**：新增或修改流程文件后，下次检索会自动更新索引（约需 30-60 秒）
3. **Ollama 依赖**：确保 Ollama 服务已启动且包含 qwen3-embedding:latest
4. **多分支流程**：当三级流程下有多个四级分支时，会列出所有选项供用户选择
5. **适用范围**：检索结果包含适用范围信息，帮助用户确认流程是否适用

## 与 OpenClaw 集成

当用户在飞书/Discord 等渠道发送消息包含以下关键词时，自动调用本 skill：

- "检索这份文件"
- "检索制度"
- "审批流程"
- "怎么审批"
- "申请流程"

Subagent 调用示例：
```python
task: """
使用 search_flows.py 检索审批流程：
1. 运行：python ${SKILL_ROOT}/scripts/search_flows.py '<用户查询>'
2. 脚本会自动检测文件变化并更新索引（如有新增/修改的流程文件）
3. 将脚本的完整输出结果返回给用户

注意：如果最近添加了新的 Excel 审批表文件，首次检索可能需要 30-60 秒建立索引。
"""
mode: "run"
timeout: 120  # 文件未变化时秒级响应，有变化时可能需要更长时间
```

## 文件变化处理

### 自动检测机制

索引管理器会自动检测文件变化：

```
自动检测流程：
1. 计算每个流程文件的哈希值（内容 + 修改时间）
2. 对比缓存中的哈希值
3. 如有变化，自动重建受影响的索引
```

### 支持的文件操作

| 操作 | 支持情况 | 处理方式 |
|------|---------|---------|
| 新增流程文件 | ✅ | 自动检测并添加 |
| 修改现有文件 | ✅ | 自动检测并更新 |
| 删除文件 | ✅ | 自动从索引移除 |
| 批量导入 | ✅ | 下次检索时自动处理 |

### 添加新文件的流程

**1. 新增 Excel 审批表**
```bash
# 1. 将新 Excel 文件放入目录并转换
python scripts/convert_excel.py "/path/to/新审批表.xlsx" "${RAG_FLOWS_DIR}"

# 2. 下次检索时自动更新索引
python scripts/search_flows.py "测试查询"
```

**2. 新增制度文档**
```bash
# 1. 分割新文档
python scripts/split_doc.py "/path/to/新制度.md" "${RAG_DATA_DIR}/新制度目录"

# 2. 建立索引（如果是新类型）
python scripts/rag_system.py index "${RAG_DATA_DIR}/新制度目录" "./index"
```

### 性能说明

| 场景 | 响应时间 | 说明 |
|------|---------|------|
| 文件无变化 | 1-3 秒 | 从缓存加载 |
| 新增/修改文件 | 10-60 秒 | 重新计算 embedding |
| 首次运行 | 30-60 秒 | 计算所有 embedding |

缓存位置：`${RAG_INDEX_CACHE_DIR}/`
