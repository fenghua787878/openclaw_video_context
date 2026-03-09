# Scout 子任务：信号发现 → 内容采集 → 策展简报

## 角色与目标
Scout 负责从公开信息中发现信号、深挖部分链接、并产出结构化简报，供 Writer 生成脚本。所有输出落盘到 **`runs/<run_id>/`**，且不编造事实（URL 必带，时间未知写 unknown）。

## 固定参数
- **signals_target**：10（目标信号条数，可略多勿少）
- **deep_dive_target**：4（深挖条数，允许 3–5）

## 输入
- `policy/policy.md`（主题、风格、评分偏好）@
- `run_id` 与 `runs/<run_id>/` 路径
- OpenClaw 提供的全局 skill **`v_to_b`**（优先用于所有网络搜索）、以及工具 **web_search**、**web_fetch**（当 `v_to_b` 不可用时降级，或仅用 snippet）

---

## Step A：信号发现（web_search）

### 动作
- 根据 policy 主题，构造 **3–5 个** 搜索 query 模板（如「XXX 最新发布」「XXX 技术解读 2025」）。
- **优先使用全局 skill `v_to_b` 通过 Brave Search API 执行上述 query**，从结果中筛选出至少 **signals_target=10** 条信号。
- 仅当 `v_to_b` skill 在当前会话中不可用、调用失败或明显无法返回有效结果时，才回退到 OpenClaw 自带的 **web_search** 工具完成同样的搜索。
- 每条信号需包含：可点击的 URL、标题、来源、入选理由；若有发布日期则填，否则填 `unknown`。

### 输出格式：signals.json
严格按下列字段写入 `runs/<run_id>/signals.json`（JSON 数组）：

```json
[
  {
    "id": "sig_001",
    "title": "文章或页面标题",
    "url": "https://...",
    "source": "来源名称或域名",
    "published_at": "2025-03-01 或 unknown",
    "reason": "入选理由",
    "score": 7.5
  }
]
```

- **id**：唯一标识，如 sig_001, sig_002 …
- **title**：字符串
- **url**：必填，有效 URL
- **source**：字符串（站点或作者）
- **published_at**：日期或 `unknown`
- **reason**：简短入选理由
- **score**：0–10 数字

### 工具
- 由 OpenClaw **优先调用全局 skill `v_to_b`** 执行 3–5 次查询（通过本地 v2ray 代理访问 Brave Search API），再汇总、去重、打分后写入 `signals.json`。
- 若 `v_to_b` skill 在当前会话中不可见、不符合资格或连续调用失败，则**降级**为使用内置 **web_search** 工具执行相同查询。
- 若连 web_search 也不可用，则本 Step 视为失败：不再使用 `tools/exec/fetch_sources.py` 或 mock 数据填充，由父工作流在 `state.json` 的 `steps` 与 `degradation` 中记录失败原因，并决定本轮是否终止或仅写入失败结论到 experiments。

---

## Step B：深挖并写 items.jsonl

### 动作
- 从 signals 中选取 **deep_dive_target=4**（3–5 条均可）条，优先高 score、一手来源。
- 对每条选中信号的 URL 调用 **web_fetch** 获取正文（或摘要）。
- 若 **web_fetch 失败或不可用**：使用该信号在搜索中的 **snippet** 作为 content，并设置 `reliability=low`、`notes=fetch_failed`。
- 每条结果写成 **items.jsonl** 的一行（一行一个 JSON 对象）。

### 输出格式：items.jsonl
每行一个 JSON，写入 `runs/<run_id>/items.jsonl`：

```json
{"signal_id":"sig_001","url":"https://...","title":"...","content":"正文或 snippet","reliability":"high","notes":"","fetched_at":"2025-03-04T12:00:00Z"}
```

- **signal_id**：对应 signals.json 中的 id
- **url**：同信号
- **title**：可来自信号或页面
- **content**：正文或 snippet（抓取失败时用 snippet）
- **reliability**：`high`（成功抓取）| `medium` | `low`（仅 snippet 时必为 low）
- **notes**：抓取失败时填 `fetch_failed`
- **fetched_at**：ISO8601 或 unknown

### 工具
- 由 OpenClaw 调用 **web_fetch** 对每个 URL 拉取内容；解析正文后写入 items.jsonl。
- 若无 web_fetch，可 exec 调用 `tools/exec/fetch_content.py`；若工具也不可用，则仅用 snippet，reliability=low，notes=fetch_failed。

---

## Step C：写 brief.md（策展简报）

### 动作
- 基于 signals.json + items.jsonl，归纳一个 **Theme**，列出 **Top angles**（3–5 点），每条角度引用 **Evidence**（signal_id + source），并写 **Risks**（可选）、**Sources**（带 URL 的列表）。
- 输出为中文，结构固定如下。

### 输出格式：brief.md
写入 `runs/<run_id>/brief.md`，固定结构：

```markdown
# 策展简报

## Theme
（一句话主题）

## Top angles
1. （角度一，可引用 signal_id / source）
2. （角度二）
...

## Evidence
- （要点）：signal_id / source / URL
- ...

## Risks
- （可选风险或不确定性）

## Sources
- [标题](URL)
- ...
```

- 每个证据必须能对应到 signals/items 中的 signal_id 或 source，并带 URL。
- 时间未知处写 unknown，不猜测。

### 工具
- 由 OpenClaw 根据前述 signals + items 内容生成 brief，再 **file write** 到 `runs/<run_id>/brief.md`。
- 若 Step B 全部为 reliability=low，在 brief 中可简短注明「部分证据仅来自摘要，未完整抓取」。

---

## 抓取失败降级（汇总）
- 当 web_fetch 对某 URL 失败或不可用时：
  - 使用该信号在搜索中的 **snippet** 作为 content。
  - 在 items.jsonl 中该条设置 **reliability=low**、**notes=fetch_failed**。
- 在父工作流 `state.json` 的 **degradation** 中记录一条：例如 `{"step":"scout_fetch","reason":"web_fetch unavailable","fallback":"snippet only"}`。

---

## 产出清单
| 产出 | 路径 |
|------|------|
| 信号列表 | `runs/<run_id>/signals.json` |
| 深挖条目 | `runs/<run_id>/items.jsonl` |
| 策展简报 | `runs/<run_id>/brief.md` |
