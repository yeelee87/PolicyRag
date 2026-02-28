# PolicyRAG Skill

基于本地 qwen3-embedding 的智能文档处理与检索系统，集成文档分割、Excel 审批流程转换和语义检索功能。

## 功能特性

| 功能 | 描述 | 状态 |
|------|------|------|
| 📄 文档智能分割 | 基于语义相似度自动分块 | ✅ |
| 📊 Excel 审批转换 | 将审批权责表转为结构化数据 | ✅ |
| 🔍 审批流程检索 | 语义检索 63 个审批流程 | ✅ |
| 📚 制度文件检索 | 语义检索分割后的制度文档 | ✅ |
| 🤖 OpenClaw 集成 | 支持关键词触发 subagent | ✅ |

## 快速开始

### 0. 配置环境变量（推荐）

```bash
export SKILL_ROOT="/path/to/PolicyRAG-Skill"
export RAG_DATA_DIR="${RAG_DATA_DIR:-$SKILL_ROOT/data}"
export RAG_FLOWS_DIR="${RAG_FLOWS_DIR:-$RAG_DATA_DIR/flows_v2}"
export RAG_INDEX_CACHE_DIR="${RAG_INDEX_CACHE_DIR:-$SKILL_ROOT/.cache/index}"
export RAG_EMBED_CACHE_DIR="${RAG_EMBED_CACHE_DIR:-$SKILL_ROOT/.cache/embed_cache}"
```

### 1. 环境检查

```bash
cd "$SKILL_ROOT"
python3 scripts/check_env.py
```

### 2. 审批流程检索

```bash
# 直接查询
python3 scripts/search_flows.py "采购200万以上怎么审批"

# 或使用统一入口
python3 scripts/rag_system.py search "预付款白名单供应商申请"
```

### 3. 文档智能分割

```bash
# 分割 Markdown 文档
python3 scripts/split_doc.py "/path/to/采购管理制度.md" "./output"

# 或使用统一入口
python3 scripts/rag_system.py split "/path/to/采购管理制度.md" "./output"
```

### 4. Excel 审批表转换

```bash
# 转换 Excel 文件
python3 scripts/convert_excel.py "/path/to/审批权责表.xlsx" "./flows"

# 或使用统一入口
python3 scripts/rag_system.py convert "/path/to/审批权责表.xlsx" "./flows"
```

## 目录结构

```
policy-rag-skill/
├── SKILL.md                          # OpenClaw Skill 配置
├── openclaw-integration.md           # OpenClaw 集成指南
├── scripts/
│   ├── rag_system.py                 # 核心模块（统一入口）
│   ├── search_flows.py               # 审批流程检索（subagent 入口）
│   ├── split_doc.py                  # 文档分割（subagent 入口）
│   ├── convert_excel.py              # Excel 转换（subagent 入口）
│   └── check_env.py                  # 环境检查
└── README.md                         # 本文件
```

## 数据目录

```
${RAG_DATA_DIR}/
├── flows_v2/                         # 审批流程数据
│   ├── 供应商管理_审批权责表_v2.json
│   ├── 招标管理_审批权责表改_v2.json
│   └── 采购管理_审批权责表2025年修订版_v2.json
├── 测试输出/                          # 分割后的制度文档
└── ...
```

## OpenClaw 集成

### 触发关键词

当用户在飞书/Discord 等渠道发送包含以下关键词的消息时，自动调用本 skill：

- `"检索这份文件"`
- `"检索制度"`
- `"审批流程"`
- `"怎么审批"`
- `"申请流程"`

### Subagent 调用示例

```python
task: """
使用 search_flows.py 检索审批流程：
1. 运行：python ${SKILL_ROOT}/scripts/search_flows.py '<用户查询>'
2. 将脚本的输出结果返回给用户
"""
mode: "run"
timeout: 120
```

详见 [openclaw-integration.md](openclaw-integration.md)

## 技术栈

- **Embedding 模型**: `qwen3-embedding:latest`（本地 Ollama）
- **相似度计算**: 余弦相似度
- **语义阈值**: 0.75（分割）、0.5（检索）
- **流程数量**: 63 个审批流程，30 个三级分组

## 审批流程数据来源

| 文件 | 流程数量 | 状态 |
|------|---------|------|
| 供应商管理_审批权责表.xlsx | 16 个流程 | ✅ |
| 招标管理_审批权责表改.xlsx | 8 个流程 | ✅ |
| 采购管理_审批权责表2025年修订版.xlsx | 39 个流程 | ✅ |

## 常见查询示例

**审批流程：**
- "预付款白名单供应商申请"
- "采购200万以上怎么审批"
- "品类采购策略审批"
- "直管企业IT采购"
- "供应商解冻流程"
- "紧急采购申请"

**制度文件：**
- "采购申请需要哪些材料"
- "预付款的比例限制"
- "招标的适用范围"

## 注意事项

1. **首次运行**：加载 embedding 模型需要 10-30 秒
2. **Ollama 依赖**：确保 Ollama 服务已启动
   ```bash
   ollama serve
   ```
3. **模型安装**：确保已安装 qwen3-embedding
   ```bash
   ollama pull qwen3-embedding:latest
   ```

## 文件变化处理

### 自动检测

系统会自动检测文件变化并更新索引：

```bash
# 查看索引状态
python scripts/index_manager.py stats

# 手动重建索引
python scripts/index_manager.py build --force

# 清除缓存
python scripts/index_manager.py clear
```

### 添加新文件

**新增审批流程：**
```bash
# 1. 转换新的 Excel 审批表
python scripts/convert_excel.py "/path/to/新审批表.xlsx" "${RAG_FLOWS_DIR}"

# 2. 测试检索（会自动更新索引）
python scripts/search_flows.py "测试新流程"
```

**新增制度文档：**
```bash
# 1. 分割文档
python scripts/split_doc.py "/path/to/新制度.md" "${RAG_DATA_DIR}/"

# 2. 建立索引
python scripts/rag_system.py index "/path/to/分割后文档" "./index"
```

### 性能对比

| 场景 | 响应时间 | 说明 |
|------|---------|------|
| 文件无变化 | 1-3 秒 | 从缓存加载 |
| 新增/修改文件 | 30-60 秒 | 自动重建索引 |
| 首次运行 | 30-60 秒 | 建立索引 |

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| Ollama 连接失败 | 运行 `ollama serve` |
| 模型未找到 | 运行 `ollama pull qwen3-embedding:latest` |
| 流程数据不存在 | 运行 `convert_excel.py` 转换 |
| 检索结果为空 | 检查 `flows_v2` 目录是否有 `*_v2.json` |
| 索引损坏 | 运行 `index_manager.py clear` 清除缓存 |

## 更新日志

### 2026-02-25
- 创建统一的 PolicyRAG Skill
- 整合文档分割、Excel 转换、流程检索功能
- 全部基于本地 qwen3-embedding
- 支持 OpenClaw subagent 调用
- 63 个审批流程，30 个三级分组

## License

内部使用
