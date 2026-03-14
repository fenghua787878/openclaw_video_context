# Daily Workflow — Content Loop 主编排

## Execution Contract

### Task Scope
本文件只定义当前 run 的主编排流程。  
本步骤必须作为独立任务执行，不得自动继承其他任务目标。

### Context Boundary
仅允许使用以下上下文：

1. 本文件正文
2. 当前 run 显式读取的输入文件
3. `agents/scout.md` 与 `agents/writer.md` 的正文
4. 当前步骤工具调用返回的结果
5. 当前 run 已落盘的中间产物

明确禁止使用：

1. 历史会话中的旧任务
2. 未显式读取的工作区其他文档
3. MEMORY、HEARTBEAT 或类似历史文件中的旧信息
4. 因为“之前做过类似任务”而自动补入的步骤

若信息不足：

- 不得用历史上下文补足
- 不得自行假设
- 直接在 `state.json` 中记录 `MISSING_INPUT`

### Capability Policy
当前 run 只允许使用以下已批准工具：

1. **`v_to_B` / `v_to_b_search`**：搜索 tool（Brave Search API，经 v2ray）  
   示例调用：`调用 v_to_B [query]`（或等价的结构化参数 `query/count/freshness`）
2. **`notion`**：Notion 数据库读写 tool  
   示例调用：`调用 notion [command]`
3. **`email_send`**：邮件发送 tool  
   示例调用：`调用 email_send [recipient] [subject] [content]`

规则：

- 若当前环境中已有被批准的能力可完成任务，直接使用，不再搜索、测试、安装或建议其他同类 skill / tool。
- 仅当现有能力明确失败，且失败原因已记录时，才允许进入 fallback。
- 未经明确要求，不得安装新 skill、启用新 plugin、配置新 provider。
- 不得因为“也许更合适”而替换已批准能力。

### Output Discipline
只输出本 workflow 要求的产物。  
不要附加额外建议、历史总结、关联任务、未来步骤，除非本文件明确要求。

---

## Goal
完成一轮可追溯的内容闭环，并在需要时发送邮件通知。

本轮至少要尝试生成：

- `runs/<run_id>/state.json`
- `runs/<run_id>/signals.json`
- `runs/<run_id>/items.jsonl`
- `runs/<run_id>/brief.md`
- `runs/<run_id>/script.md`
- `policy/experiments.jsonl`

在通知启用时，再尝试生成：

- `runs/<run_id>/notification.md`
- 发送结果记录到 `state.json`

---

## Inputs

显式读取以下文件：

- `policy/policy.md`
- `policy/experiments.jsonl`（若存在）
- `policy/notifications.json`（若存在）
- `agents/scout.md`
- `agents/writer.md`
- Notion「openclaw -> 文本升级与观测 -> 文本升级观测」数据库（若运行器已配置 Notion 能力）

---

## Steps

### Step 0 — 初始化 run

1. 生成 `run_id`
2. 创建目录：`runs/<run_id>/`
3. 初始化 `state.json`，至少包含：
   - `run_id`
   - `started_at`
   - `status='running'`
   - `steps=[]`
   - `degradation=[]`

若初始化失败：

- 立即停止后续步骤
- 将本轮状态标记为 `failed`

### Step 1 — 读取策略与通知配置

1. 读取 `policy/policy.md`
2. 若 `policy/experiments.jsonl` 存在，则读取最近若干条经验记录
3. 通过 Notion 工具读取「文本升级观测」中最近已有人工填写播放/点赞/粉丝量的记录（调用形式：`调用 notion [command]`）
4. 若 `policy/notifications.json` 存在，则读取：
   - `enabled`（可选，缺省视为 `true`）
   - 收件人列表（必填，至少 1 个）
   - 主题模板
   - 是否仅在 success / degraded_success 时发送

若 `policy/notifications.json` 不存在：

- 视为本轮通知默认关闭
- 不得因此判定本轮失败

若 `policy/notifications.json` 存在但配置不完整（例如无收件人）：

- 将通知步骤记为 `skipped`
- 在 `state.degradation` 中记录 `notifications_config_invalid`
- 不得因此影响主流程产物

### Step 2 — 执行 Scout

执行 `agents/scout.md`，要求：

1. 搜索主路径使用 **`v_to_b_search`**
2. 搜索调用应显式提供：
   - `query`
   - `count`
   - `freshness`
3. 搜索结果需尽量归一化为信号列表
4. 尽量生成：
   - `signals.json`
   - `items.jsonl`
   - `brief.md`
5. 所有证据尽量带 URL；时间未知写 `unknown`

#### Scout fallback

当 `v_to_b_search` 明确失败时：

1. 先在 `state.degradation` 中记录失败原因
2. 再按显式 fallback 尝试：
   - `tools/exec/fetch_sources_searxng.py`
   - `tools/exec/fetch_sources.py`
3. 若仍失败：
   - 将 Scout step 记为 `failed`
   - 尽量保留已生成中间产物

不得因为搜索失败而自动寻找、安装、配置其他同类搜索 skill / tool。

### Step 3 — 执行 Writer

执行 `agents/writer.md`，要求：

1. 读取 `brief.md`
2. 结合 `policy/policy.md`
3. 参考 `policy/experiments.jsonl` 的最近经验
4. 若可用，参考 Notion「文本升级观测」中的人工效果数据
5. 生成 `script.md`（Body 小标题必须自定义，不得固定为“要点一/二/三”）
6. 对照最近历史脚本与 Notion 记录做新鲜度去重：相似稿件重写或删除，仅保留新增事实充分的版本
7. 向 `policy/experiments.jsonl` 追加本轮经验记录
8. 先执行 `python tools/exec/sync_script_to_notion.py --run-id <run_id> --content-category <内容方向> --expression-variant <表达方式>` 生成逐条写入命令（落盘到 `runs/<run_id>/notion_sync_commands.txt`）
9. 再逐条执行上述命令（调用形式：`调用 notion [command]`），把本轮脚本写入「文本升级观测」

若 `brief.md` 缺失：

- 可将 Writer step 记为 `skipped` 或 `failed`
- 但仍应尝试追加至少 1 条经验记录，说明失败点

### Step 4 — 生成通知正文（可选）

仅当以下条件同时满足时进入本步：

1. `policy/notifications.json` 存在，且未显式关闭通知（`enabled` 缺省按 `true` 处理）
2. 配置中存在有效收件人（至少 1 个）
3. 本轮已有可发送内容，且优先使用 `script.md` 全文作为邮件正文
4. 本轮状态满足通知策略要求

本步要求：

1. 生成 `runs/<run_id>/notification.md`
2. 形成邮件内容，默认结构如下（要求可直接发送）：
   - 开头：本轮主题/标题 + 结果状态（success/degraded 等）
   - 正文：`runs/<run_id>/script.md` 的完整全文（不是摘要）
   - 结尾：必要的补充说明（如降级原因、来源说明）
3. 若邮件服务对正文长度有限制：
   - 优先保留全文并按「上/下」两封拆分发送；
   - 或保留全文并改为纯文本格式发送；
   - 不得在未说明的情况下自动截断为摘要。

若通知条件不满足：

- 将本步记为 `skipped`

### Step 5 — 调用 邮件发送

仅当 Step 4 已生成 `notification.md`，且通知未被显式关闭（`enabled=false`）并存在有效收件人时，才调用 **`邮件发送`**。

调用时显式提供：

- `to='xxx@example.com'`
- `subject='测试邮件'`
- `content='这是一封测试邮件'`

实际运行中，应将以上示例值替换为：

- `to`：来自 `policy/notifications.json` 的收件人
- `subject`：本轮通知主题
- `content`：`notification.md` 全文内容（其中应包含 `script.md` 全文）

#### Email fallback

当 `email_send` 失败时：

1. 不阻塞主产物保存
2. 保留 `notification.md`
3. 在 `state.degradation` 中记录 `email_send_unavailable` 或具体错误
4. 将通知步骤标记为 `failed` 或 `degraded_success`

不得因为邮件失败而自动寻找、安装、配置其他发信 skill / tool。

### Step 6 — 写入最终状态

更新 `state.json`：

- 写入每个 step 的状态
- 写入 degradation 记录
- 写入 summary
- 将 run 状态归类为：
  - `success`
  - `degraded_success`
  - `partial_success`
  - `failed`
  - `skipped`

建议判定规则：

- `signals`、`brief`、`script` 均成功，则至少为 `success`
- 若主产物成功，但搜索或通知走了 fallback，则为 `degraded_success`
- 若只完成部分关键产物，则为 `partial_success`
- 若关键步骤中断且最小闭环未形成，则为 `failed`

---

## Stop Conditions

出现以下任一情况可停止：

1. `run_id` 或目录初始化失败
2. 无法写入 `state.json`
3. 必需输入完全缺失且无法继续
4. 工作流已到最后一步

---

## Self-check Before Finish

输出前确认：

- 未引用未授权历史上下文
- 未混入 memory / heartbeat 内容
- 未把旧任务要求带入当前 run
- 搜索仅使用了 `v_to_b_search` 或显式 fallback
- 发信仅使用了 `email_send` 或保留为未发送状态
- 未因为“也许更合适”而引入新 skill / tool
