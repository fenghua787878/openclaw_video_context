# Writer 子任务：脚本生成 + 自升级记录

## 角色与目标
Writer 根据策略、历史实验与 Scout 产出的简报，生成固定结构的 **script.md**（可包含 1–N 篇脚本），并向 **policy/experiments.jsonl** 追加 1–3 行 JSONL，完成当次运行的记录沉淀。文本升级决策应以人工回填的视频效果数据为准，不再仅凭主观总结。

## 输入
- **模型配置（推荐）**：`qwen3-max-2026-01-23` 与 `Claude Sonnet 4.5`，用于双模型并行生成两份候选脚本。
- **policy/policy.md**：主题、风格、禁区、输出形态
- **policy/experiments.jsonl**：仅读取**最后 30 行**，作为「最近做了什么、效果如何」的上下文
- **runs/<run_id>/brief.md**：策展简报（Theme / Top angles / Evidence / Risks / Sources）
- **runs/<run_id>/items.jsonl**（可选）：深挖条目，用于丰富脚本中的证据引用
- **Notion：openclaw 页面 -> 文本升级与观测 -> 文本升级观测（推荐）**：使用 `调用 notion [command]` 读取最近人工回填记录，作为本轮表达方式选择依据

## 输出
1. **runs/<run_id>/script.md**：成稿脚本（中文），结构见下。
2. **policy/experiments.jsonl**：追加 1–3 行 JSONL，字段与示例见下。
3. **Notion 数据库新增行（推荐）**：将本轮每篇脚本写入「文本ID、文本正文、播放量、点赞量、粉丝量、内容方向、表达方式」字段，播放相关数值由人工后续补填。

---

## 双模型生成要求（新增）
- 最终成稿阶段应分别调用以下模型各生成 1 份脚本：
  1. `qwen3-max-2026-01-23`
  2. `Claude Sonnet 4.5`
- 两份脚本都应写入同一个 `runs/<run_id>/script.md`，建议使用如下分段：
  - `## 候选 A（qwen3-max-2026-01-23）`
  - `## 候选 B（Claude Sonnet 4.5）`
- 两份候选都必须满足本文件对结构、字数、合规、去重与新鲜度的要求。
- 若其中一个模型调用失败：
  - 保留另一份候选并继续流程；
  - 在 `policy/experiments.jsonl` 的 note 中记录失败模型与原因；
  - 在 `state.degradation` 记录 `model_generation_partial`。

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
1. **（自定义小标题）**：连续成段的口播文案，不在正文中出现 signal_id、URL 或类似「引用 evidence」的字样。
2. **（自定义小标题）**：同上，重点讲清一个问题或案例。
3. **（自定义小标题）**：同上，补充应用场景或风险提示。

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

### 结构去模板化要求（避免千篇一律）
- 禁止在每篇脚本中固定使用“**要点一 / 要点二 / 要点三**”作为三段标题。
- 每篇脚本必须使用与主题贴合的自定义小标题，例如“监管红线在哪里”“企业最容易踩的坑”“本周新增变化”。
- 同一 run 内不同脚本的小标题不可完全重复；连续两轮 run 的同类主题也应避免重复同一组小标题。
- 在不改变固定大结构（Hook / Body / Implication / CTA）的前提下，允许变化叙事顺序（结论前置、案例前置、风险前置）。

### 新鲜度与去重要求（避免重复旧内容）
- Writer 生成前必须先检查最近历史：
  - 本地最近脚本：`runs/*/script.md`（至少最近 10 轮）
  - Notion「文本升级观测」中最近已发布文本（若可用）
- 若候选脚本与历史脚本在“短标题 + 核心观点 + 3 个小标题”上高度相似，则视为重复，必须重写。
- 相同政策主题允许继续追踪，但必须引入“新增事实/新增时间点/新增案例”之一，否则不得再次生成。
- 若无法找到足够新鲜信号，应减少产出篇数，不要用改写旧文凑数。

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

### Notion 回填闭环（推荐）
- 写入时机：`script.md` 生成后，先运行 `tools/exec/sync_script_to_notion.py` 产生命令，再按脚本逐条写入 Notion 数据库「文本升级观测」（调用格式：`调用 notion [command]`）。
- 字段映射：
  - `文本ID` <- `run_id + script_id`
  - `文本正文` <- 脚本正文（建议含短标题与 Hook）
  - `内容方向` <- `content_category`
  - `表达方式` <- `expression_variant`
  - `播放量/点赞量/粉丝量` <- 先置空或 0，由人工发布后填写
- 读取时机：下次 Writer 开始前，优先通过 Notion 工具读取最近人工已填数值的记录（调用格式：`调用 notion [command]`），用于比较不同内容方向与表达方式的效果。

### 表达方式候选池（用于 A/B 尝试）
默认从以下 8 种表达方式中选择，避免每次随意命名导致不可比：
1. **问答式**：先抛常见问题，再逐段回答。
2. **结论前置**：第一句先给判断，再给依据。
3. **故事化**：用一个真实场景引入，再抽象出规则。
4. **数据驱动**：用数字、比例、趋势组织论证。
5. **清单式**：按 3–5 条 checklist 展开。
6. **对比式**：合规与违规、国内与境外、旧规与新规对照。
7. **步骤式**：按执行顺序给操作路径（第 1 步/第 2 步）。
8. **风险揭示式**：先讲代价与后果，再给规避建议。

选择规则：
- 同一 `content_category` 下，连续至少测试 2–3 种 `expression_variant` 才做优劣判断。
- 单次判断优先看 `粉丝量`，再看 `点赞量`，最后看 `播放量`。
- 若样本量不足（例如每种表达 <3 条），只记录观察，不升级默认策略。

### 写入方式
- **原子写入**：先写入临时文件（如 `policy/experiments.jsonl.tmp`），再重命名替换原文件，避免截断。
- 由 OpenClaw 的 file write 或 exec 调用封装了原子写的脚本（如 src/io_utils 中的 append_jsonl）完成。

---

## 执行顺序（由 OpenClaw 执行）

1. **读取**：policy/policy.md、policy/experiments.jsonl（最后 30 行）、runs/<run_id>/brief.md，可选 runs/<run_id>/items.jsonl。
2. **双模型生成**：分别调用 `qwen3-max-2026-01-23` 与 `Claude Sonnet 4.5` 生成两份候选脚本。
3. **汇总写入**：将两份候选统一写入 `runs/<run_id>/script.md`（候选 A / 候选 B）。
4. **追加**：向 `policy/experiments.jsonl` 追加 1–3 行 JSONL。若本轮暂无人工回填，先写旧格式结论；有人工回填时优先写推荐字段（含 content_category / expression_variant / metrics）。
5. **生成 Notion 写入命令**：执行 `python tools/exec/sync_script_to_notion.py --run-id <run_id> --content-category <内容方向> --expression-variant <表达方式>`，输出 `runs/<run_id>/notion_sync_commands.txt`。
6. **回填到 Notion（推荐）**：逐条执行 `notion_sync_commands.txt` 中的 `调用 notion [command]`，将本轮脚本基础信息写入「文本升级观测」数据库，供人工填写播放效果。
7. **新鲜度复核**：对照最近脚本与 Notion 历史，删除或重写重复度高的候选脚本，仅保留“新鲜事实充分”的版本。
8. **结束**：Writer 子任务完成，控制权回到 daily 工作流 Step 4（写回 state）。

---

## 失败与降级
- 若 **brief.md 缺失**：可跳过 script 生成，但仍需追加至少 1 行 experiments，在 what_worked 中说明「Scout 未产出 brief」，what_to_try_next 中建议检查 Scout 或 web_search。
- 若 **experiments 追加失败**：在 state.json 的 degradation 中记录，并可在 step note 中注明，便于下次人工补写。
