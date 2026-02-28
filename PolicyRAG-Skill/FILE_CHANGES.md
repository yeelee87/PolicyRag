# 文件变化处理指南

PolicyRAG Skill 支持动态文件变化，当您在 `ragfiles` 文件夹中添加、修改或删除文件时，系统会自动检测并更新索引。

## 变量约定

```bash
export SKILL_ROOT="/path/to/PolicyRAG-Skill"
export RAG_SOURCE_DIR="/path/to/source-files"
export RAG_DATA_DIR="${RAG_DATA_DIR:-$SKILL_ROOT/data}"
export RAG_FLOWS_DIR="${RAG_FLOWS_DIR:-$RAG_DATA_DIR/flows_v2}"
export RAG_INDEX_CACHE_DIR="${RAG_INDEX_CACHE_DIR:-$SKILL_ROOT/.cache/index}"
```

## 核心机制

### 1. 哈希检测
系统通过计算文件的哈希值（文件名 + 大小 + 修改时间）来检测变化：

```python
# 检测流程
1. 扫描目录中的所有流程文件
2. 计算每个文件的哈希值
3. 对比缓存中的哈希值
4. 识别新增/修改/删除的文件
```

### 2. 索引缓存
索引数据持久化存储，避免重复计算：

```
缓存位置：${RAG_INDEX_CACHE_DIR}/
├── flow_index_cache.json      # 流程数据
├── flow_index_metadata.json   # 文件哈希元数据
└── flow_embeddings.npz        # Embedding 向量
```

### 3. 增量更新
只重新计算发生变化的文件，而非全部重建。

---

## 使用场景

### 场景1：添加新的审批流程表

**步骤：**

```bash
# 1. 将新的 Excel 文件放入目录
cp 新审批表.xlsx ${RAG_SOURCE_DIR}/采购RCM与walkthrough/权责文件/

# 2. 转换为 JSON 格式
python ${SKILL_ROOT}/scripts/convert_excel.py \
    "${RAG_SOURCE_DIR}/采购RCM与walkthrough/权责文件/新审批表.xlsx" \
    "${RAG_FLOWS_DIR}"

# 3. 测试检索（会自动检测新文件并更新索引）
python ${SKILL_ROOT}/scripts/search_flows.py "新流程查询"
```

**预期行为：**
```
ℹ️ 检测到文件变化: 0 修改, 1 新增, 0 删除
ℹ️ 找到 4 个流程文件
ℹ️ 已加载 80 个流程
ℹ️ 正在计算 embedding（这可能需要一些时间）...
...
✅ 索引更新完成：共 80 个流程
```

---

### 场景2：修改现有审批表

**步骤：**

```bash
# 1. 直接修改 Excel 文件（如添加新流程）
# 2. 重新转换
python scripts/convert_excel.py "审批表.xlsx" "${RAG_FLOWS_DIR}"

# 3. 下次检索时自动更新
python scripts/search_flows.py "查询"
```

**预期行为：**
```
ℹ️ 检测到文件变化: 1 修改, 0 新增, 0 删除
ℹ️ 正在计算 embedding（这可能需要一些时间）...
...
```

---

### 场景3：删除旧文件

直接删除文件即可，系统会自动从索引中移除：

```bash
rm ${RAG_FLOWS_DIR}/旧文件_v2.json

# 下次检索时自动检测
python scripts/search_flows.py "查询"
```

**预期行为：**
```
ℹ️ 检测到文件变化: 0 修改, 0 新增, 1 删除
ℹ️ 从缓存加载：XX 个流程
```

---

### 场景4：批量导入

如果您有大量文件需要导入：

```bash
# 1. 批量转换所有 Excel 文件
for file in /path/to/excel/*.xlsx; do
    python scripts/convert_excel.py "$file" "${RAG_FLOWS_DIR}"
done

# 2. 手动重建索引（避免首次检索超时）
python scripts/index_manager.py build --force

# 3. 验证
python scripts/index_manager.py stats
```

---

## OpenClaw 集成中的文件变化

当用户在飞书中添加新文件时，subagent 调用会自动处理：

```python
# Subagent 任务示例
task: """
用户可能刚刚添加了新的 Excel 审批表文件。

1. 首先检查 ${RAG_FLOWS_DIR}/ 下是否有新的文件
2. 如果有未转换的 .xlsx 文件，先运行 convert_excel.py 转换
3. 然后运行 search_flows.py 进行检索

注意：如果检测到文件变化，检索可能需要 30-60 秒更新索引。
"""
```

---

## 性能优化建议

### 1. 预建索引
如果您知道将要添加大量文件，可以提前建立索引：

```bash
# 批量转换后预建索引
python scripts/index_manager.py build --force

# 这样用户查询时就能秒级响应
python scripts/search_flows.py "查询"  # 1-3 秒响应
```

### 2. 定期维护
建议定期清理旧的缓存文件：

```bash
# 查看索引统计
python scripts/index_manager.py stats

# 如果缓存过大，可以清除后重建
python scripts/index_manager.py clear
python scripts/index_manager.py build
```

### 3. 监控文件变化
可以在 OpenClaw 中设置定时任务检查新文件：

```bash
# 每小时检查一次新文件
0 * * * * /usr/bin/python3 ${SKILL_ROOT}/scripts/index_manager.py build
```

---

## 故障排查

### 问题：检测到变化但没有更新

**可能原因：**
- 文件权限问题
- 磁盘空间不足

**解决：**
```bash
# 检查缓存目录权限
ls -la ${RAG_INDEX_CACHE_DIR}/

# 强制重建
python scripts/index_manager.py build --force
```

### 问题：索引损坏

**症状：**
- 检索结果异常
- 报错 "缓存数据不完整"

**解决：**
```bash
# 清除并重建
python scripts/index_manager.py clear
python scripts/index_manager.py build
```

### 问题：新文件未被检测

**可能原因：**
- 文件命名格式不匹配（需要 `*_v2.json` 或 `*_flows.json`）

**解决：**
```bash
# 检查文件命名
ls ${RAG_FLOWS_DIR}/*.json

# 重命名后重新检测
mv 新文件.json 新文件_v2.json
```

---

## 技术细节

### 哈希计算
```python
def _get_file_hash(self, filepath: Path) -> str:
    stat = filepath.stat()
    content = f"{filepath.name}-{stat.st_size}-{stat.st_mtime}"
    return hashlib.md5(content.encode()).hexdigest()
```

### 缓存格式
- **flow_index_cache.json**: 流程数据（文本）
- **flow_embeddings.npz**: NumPy 压缩格式存储 embedding 向量
- **flow_index_metadata.json**: 文件哈希和更新时间

### 内存使用
- 63 个流程的索引约占用 5-10MB 内存
- 缓存文件约占用 2-5MB 磁盘空间
