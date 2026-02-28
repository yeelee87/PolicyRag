# OpenClaw 集成配置

## 变量约定（先配置）

```bash
export SKILL_ROOT="/path/to/PolicyRAG-Skill"
export RAG_DATA_DIR="${RAG_DATA_DIR:-$SKILL_ROOT/data}"
export RAG_FLOWS_DIR="${RAG_FLOWS_DIR:-$RAG_DATA_DIR/flows_v2}"
export RAG_INDEX_CACHE_DIR="${RAG_INDEX_CACHE_DIR:-$SKILL_ROOT/.cache/index}"
```

## 触发关键词配置

在 OpenClaw 的 AGENTS.md 中添加以下内容：

```markdown
## 🔑 Keyword Triggers for PolicyRAG Skill

### "检索这份文件" / "检索制度" / "审批流程"
**触发条件：** 用户消息包含以下关键词之一：
- "检索这份文件"
- "检索制度"
- "审批流程"
- "怎么审批"
- "申请流程"
- "需要什么审批"

**检索范围：**
- 审批流程：`${RAG_FLOWS_DIR}/` 下的流程数据
- 制度文件：已分割的制度文档（可选）

**动作流程：**
1. 创建 subagent（使用 Kimi 主模型）
2. Subagent 调用 search_flows.py 脚本进行检索
3. 脚本内部使用 qwen3-embedding:latest 计算相似度
4. 返回格式化结果（含流程图和分支展示）

**Subagent 任务参数：**
```python
task: """
使用 search_flows.py 检索审批流程：
1. 运行：python ${SKILL_ROOT}/scripts/search_flows.py '<用户查询>'
2. 脚本会自动：
   - 加载 flows_v2 目录下的所有流程
   - 计算 query 与流程的 embedding 相似度
   - 找到最佳匹配的三级流程
   - 列出该三级流程下的所有四级分支
   - 生成 ASCII 审批流程图
3. 将脚本的输出结果返回给用户
"""
mode: "run"
timeout: 120  # 首次加载 embedding 需要时间
```

**示例调用：**
```bash
# 用户查询：供应商解冻
python ${SKILL_ROOT}/scripts/search_flows.py '供应商解冻'

# 用户查询：预付款申请
python ${SKILL_ROOT}/scripts/search_flows.py '预付款申请'
```

**脚本特点：**
- ✅ 自动分组：三级流程 → 四级分支
- ✅ 可视化：ASCII 流程图展示审批节点
- ✅ 本地运行：Ollama embedding，零 API 成本
- ✅ 智能提示：多个分支时列出所有选项

**注意：**
- 首次运行需要加载所有 embedding，约 10-30 秒
- 相似度阈值 0.5，低于此值返回建议列表
- 流程数据位于 `${RAG_FLOWS_DIR}/`
- 确保 Ollama 服务已启动且包含 qwen3-embedding:latest

---

### "分割文档" / "文档拆分"
**触发条件：** 用户消息包含 "分割文档" 或 "文档拆分"

**动作流程：**
```python
task: """
使用 split_doc.py 分割文档：
1. 运行：python ${SKILL_ROOT}/scripts/split_doc.py '<输入文件>' '<输出目录>' [部门] [分类]
2. 脚本会：
   - 使用 qwen3-embedding 进行语义分析
   - 将文档分割为语义相关的块
   - 生成带 YAML frontmatter 的 Markdown 文件
   - 创建索引导航文件
3. 返回分割结果和文件列表
"""
mode: "run"
timeout: 180
```

---

### "转换审批表" / "Excel转换"
**触发条件：** 用户消息包含 "转换审批表" 或 "Excel转换"

**动作流程：**
```python
task: """
使用 convert_excel.py 转换 Excel 审批表：
1. 运行：python ${SKILL_ROOT}/scripts/convert_excel.py '<Excel文件>' '<输出目录>'
2. 脚本会：
   - 解析 Excel 中的多级流程结构
   - 识别审批节点层级（①②③④）
   - 区分"审核"与"审批"
   - 生成结构化的 JSON 文件
3. 返回转换结果
"""
mode: "run"
timeout: 60
```
```

## Skill 注册

将 skill 注册到 OpenClaw：

```bash
# 方法1：复制到 OpenClaw skills 目录
cp -r ${SKILL_ROOT} ${HOME}/.openclaw/skills/

# 方法2：创建软链接
ln -s ${SKILL_ROOT} ${HOME}/.openclaw/skills/policy-rag-skill
```

然后重启 OpenClaw Gateway 或执行刷新 skills 命令。

## 环境检查

确保以下环境就绪：

```bash
# 1. 检查 Ollama 服务
curl http://localhost:11434/api/tags

# 2. 检查 qwen3-embedding 模型
ollama list | grep qwen3-embedding

# 3. 检查流程数据目录
ls ${RAG_FLOWS_DIR}/

# 4. 测试检索功能
python ${SKILL_ROOT}/scripts/search_flows.py "采购申请"
```

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| Ollama 连接失败 | 运行 `ollama serve` 启动服务 |
| 模型未找到 | 运行 `ollama pull qwen3-embedding:latest` |
| 流程数据不存在 | 先运行 convert_excel.py 转换 Excel 文件 |
| 检索结果为空 | 检查 flows_v2 目录是否有 *_flows.json 文件 |
| 首次运行慢 | 正常现象，首次需要加载 embedding 模型 |

## 更新日志

- **2026-02-25**: 创建统一的 PolicyRAG Skill
  - 整合文档分割、Excel 转换、流程检索功能
  - 全部基于本地 qwen3-embedding
  - 支持 OpenClaw subagent 调用
