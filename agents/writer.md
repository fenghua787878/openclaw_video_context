# Writer 子任务：脚本生成 + 自升级记录

## 角色与目标
Writer 根据策略、历史实验与 Scout 产出的简报，生成固定结构的 **script.md**（可包含 1–N 篇脚本），并向 **policy/experiments.jsonl** 追加 1–3 行 JSONL，完成当次运行的记录沉淀。文本升级决策应以人工回填的视频效果数据为准，不再仅凭主观总结。

## 输入
- **policy/policy.md**：主题、风格、禁区、输出形态
- **policy/experiments.jsonl**：仅读取**最后 30 行**，作为「最近做了什么、效果如何」的上下文
- **runs/<run_id>/brief.md**：策展简报（Theme / Top angles / Evidence / Risks / Sources）
- **runs/<run_id>/items.jsonl**（可选）：深挖条目，用于丰富脚本中的证据引用

## 输出
1. **runs/<run_id>/script.md**：成稿脚本（中文），结构见下。
2. **policy/experiments.jsonl**：追加 1–3 行 JSONL，字段与示例见下。

---

## script.md 固定结构

写入 `runs/<run_id>/script.md`，用于承载本轮生成的 **1–N 篇脚本**。整体结构要求：

```markdown
# 成稿脚本

## 脚本 1

### 短标题
（用于平台的短标题，精炼有记忆点，一般不超过 15 个汉字）

### 视频描述
（用于平台的视频描述，概括本期内容，可略长）

### Hook
（开场一句，吸引注意；需按照 HeyGen 文档要求标注语气和停顿，例如【语气：平和】【停顿】）

### Body（3 points）
1. **要点一**：连续成段的口播文案，不在正文中出现 signal_id、URL 或类似「引用 evidence」的字样。
2. **要点二**：同上，重点讲清一个问题或案例。
3. **要点三**：同上，补充应用场景或风险提示。

### Implication
（对读者/行业的含义或启示；同样按照 HeyGen 文档要求标注语气和停顿）

### CTA
（行动号召或下一步建议，适合作为结尾口播；同样可标注语气和停顿）

### Captions
- （可选 1–3 条短标题/金句，用于封面文案或摘要，不必传给 HeyGen）

---

## 脚本 2
（结构与「脚本 1」相同，依此类推，可写至脚本 N）
```

### 约束
- **每篇脚本的 Body 部分总字数**不少于 400 个汉字（不含标题、Captions、短标题与视频描述），要把问题讲透，而不是只给提纲。
- **不在 Hook / Body / Implication / CTA 正文中直接插入引用**：不要出现 signal_id、URL、`[标题](URL)`、「引用 evidence」等字样，这些溯源信息由 brief/items 与 signals 承担。
- **字幕友好断句**：考虑短视频一行约 12 个汉字字幕的宽度，单句长度尽量控制在 12 或 24 个左右汉字，在自然停顿处断句，避免出现「标点符号单独出现在下一行」的情况。
- **HeyGen 语气与停顿标注**：在 Hook / Body / Implication / CTA 中，按照 HeyGen 官方文档推荐的方式标注语气和停顿（例如使用【语气：强调】【语气：平和】【停顿】之类的标记），以便直接交给 HeyGen 生成视频。
- 时间未知写 unknown，不猜测。

---

## experiments.jsonl 追加规范（人工评估优先）

每次运行向 **policy/experiments.jsonl** 追加 **1–3 行** JSONL。每行一个 JSON 对象。

### 严格字段（兼容旧格式）
- **ts**（必填）：ISO8601 时间戳，如 `2025-03-04T12:00:00Z`
- **what_worked**（旧格式必填）：本轮运行中效果好的做法或结论（字符串）
- **what_to_try_next**（旧格式必填）：下次可尝试的改进（字符串）
- **note**（可选）：备注，如 run_id、降级说明、失败原因等

### 推荐字段（用于文本升级判断）
- **run_id**：本次脚本所属 run_id。
- **script_id**：脚本编号（如 `script_1`），保证“一条文本 -> 一条视频”可追溯。
- **content_category**：文本内容种类（如 `政策解读` / `案例拆解` / `观点评论`）。
- **expression_variant**：同一内容下的表达方式（如 `数据驱动` / `故事化` / `问答式`）。
- **metrics**：人工回填的视频结果，包含：
  - `plays`：播放量
  - `likes`：点赞量
  - `follows`：加粉量
- **effective_by**：有效性评估维度说明，固定为 `content_category + expression_variant`。

> 升级原则：仅当人工回填数据可在上述两个维度上形成稳定对比结论时，才更新“下次文本策略”。

### 示例（一行旧格式 + 一行推荐格式）
```jsonl
{"ts":"2025-03-04T12:00:00Z","what_worked":"用 5 个 query 覆盖中英文，得到 12 条信号","what_to_try_next":"增加「开源发布」类 query","note":"run_id=daily_20250304_120000"}
{"ts":"2025-03-05T20:00:00Z","run_id":"daily_20250305_180000","script_id":"script_1","content_category":"政策解读","expression_variant":"问答式","metrics":{"plays":12800,"likes":640,"follows":96},"effective_by":"content_category + expression_variant","what_worked":"问答式开场提升完播","what_to_try_next":"同主题增加数据图表口播版本","note":"manual_feedback=sheet_20250305"}
```

### 写入方式
- **原子写入**：先写入临时文件（如 `policy/experiments.jsonl.tmp`），再重命名替换原文件，避免截断。
- 由 OpenClaw 的 file write 或 exec 调用封装了原子写的脚本（如 src/io_utils 中的 append_jsonl）完成。

---

## 执行顺序（由 OpenClaw 执行）

1. **读取**：policy/policy.md、policy/experiments.jsonl（最后 30 行）、runs/<run_id>/brief.md，可选 runs/<run_id>/items.jsonl。
2. **生成**：根据上述输入生成 script.md 内容，确保 Body 3 points 均引用 evidence（signal_id + source），Sources 带 URL。
3. **写入**：将 script 内容写入 `runs/<run_id>/script.md`。
4. **追加**：向 `policy/experiments.jsonl` 追加 1–3 行 JSONL。若本轮暂无人工回填，先写旧格式结论；有人工回填时优先写推荐字段（含 content_category / expression_variant / metrics）。
5. **结束**：Writer 子任务完成，控制权回到 daily 工作流 Step 4（写回 state）。

---

## 失败与降级
- 若 **brief.md 缺失**：可跳过 script 生成，但仍需追加至少 1 行 experiments，在 what_worked 中说明「Scout 未产出 brief」，what_to_try_next 中建议检查 Scout 或 web_search。
- 若 **experiments 追加失败**：在 state.json 的 degradation 中记录，并可在 step note 中注明，便于下次人工补写。
