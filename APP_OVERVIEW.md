# Content Loop — 系统设计概览

本文档说明本项目的架构约定、数据契约、失败模式与工程拆分原因。  
重点不是描述某个 OpenClaw 官方实现细节，而是说明：**在本项目中，如何把 OpenClaw 用作控制面（control plane）**。

## 1. 本项目中的 OpenClaw 角色

在本项目设计中，OpenClaw 被视为**控制面**，而不是具体执行器本身。

它主要负责：

- 解释 `workflows/daily.md` 的步骤顺序；
- 决定何时调用 `agents/scout.md` 与 `agents/writer.md`；
- 组织输入输出路径；
- 执行停止条件与降级规则；
- 驱动产物落盘与状态记录。

需要特别说明的是：

- `daily.md` 是**本项目约定的唯一主入口**；
- “是否支持直接执行 Markdown 文件”取决于当前运行器能力；
- `openclaw run workflows/daily.md` 是一种可能的启动形式，但不应被理解为所有环境中的固定官方命令。

## 2. Control Plane vs Execution Plane

### Control Plane（控制面）

本项目中的控制面负责回答：**下一步做什么**。

其职责包括：

- 按顺序运行 workflow；
- 调用 Scout / Writer 两类 agent；
- 判断某步成功、失败还是跳过；
- 决定是否进入降级模式；
- 规定产物路径与状态记录方式。

控制面应尽量保持在 Markdown workflow / agent 文档中，而不是散落在 Bash 或 Python 主函数里。

### Execution Plane（执行面）

执行面负责回答：**具体怎么做**。

其能力可能来自：

- 运行环境提供的原生搜索能力；
- 运行环境提供的原生抓取能力；
- 文件读写能力；
- 可选的 exec 调用（Python / Shell）；
- `tools/exec/*` 提供的过渡脚本。

执行面产物统一落盘到：

- `runs/<run_id>/`
- `policy/experiments.jsonl`

这样拆分的直接收益是：**在不改变 workflow / agent 结构的前提下，可以替换执行器实现。**

## 3. 主入口与步骤约定

### 主入口约定

本项目约定：

- `workflows/daily.md` 是唯一主入口；
- 顶层 shell、cron、外部调度器，只负责触发，不负责主流程编排；
- workflow 中应明确每一步的输入、输出、降级条件和停止条件。

### 步骤约定

推荐的主流程为：

1. 初始化 run_id 与目录；
2. 读取 `policy/policy.md`；
3. 执行 `agents/scout.md`；
4. 执行 `agents/writer.md`；
5. 写入状态总结；
6. 结束本轮运行。

其中：

- **Scout** 负责：信号发现、初步采集、策展简报；
- **Writer** 负责：读取 brief 与 policy、生成 script、追加 experiments。

## 4. 数据契约与产物说明

| 产物 | 路径 | 说明 |
|------|------|------|
| state | `runs/<run_id>/state.json` | 本轮运行状态、step 状态、degradation、summary |
| signals | `runs/<run_id>/signals.json` | 信号数组：`id/title/url/source/published_at/reason/score` |
| items | `runs/<run_id>/items.jsonl` | 深挖结果，每行 JSON：`signal_id/url/content/reliability/notes` |
| brief | `runs/<run_id>/brief.md` | 策展简报：Theme / Top angles / Evidence / Risks / Sources |
| script | `runs/<run_id>/script.md` | 成稿脚本：标题 / Hook / Body / Implication / CTA / Captions |
| experiments | `policy/experiments.jsonl` | 每次追加 1–3 行：`ts / what_worked / what_to_try_next / note` |

约束如下：

- 所有证据应尽量可追溯到 URL；
- 时间未知统一写 `unknown`；
- JSON 产物应符合 `schemas/` 中对应 schema；
- 即使部分步骤失败，也应尽量先写出 `state.json`。

## 5. 运行状态定义

建议在 `state.json` 中区分以下运行结果：

- **success**：`signals`、`brief`、`script` 均成功生成；
- **degraded_success**：产物生成完成，但依赖了 snippet、fallback 或低可靠度抓取；
- **partial_success**：至少完成了部分关键产物，例如 `signals` 或 `brief`，但未完成最终 script；
- **failed**：关键步骤中断，连最小闭环产物都未形成；
- **skipped**：某一步按规则被跳过，而非异常失败。

这个状态定义的意义在于：后续不需要只靠人工阅读日志来判断本轮结果。

## 6. Failure Modes 与 Degradation

### 6.1 无原生搜索能力

行为建议：

- 优先改走 `tools/exec/fetch_sources_searxng.py` 或 `tools/exec/fetch_sources.py`；
- 若仍无法得到真实信号，则将对应步骤标记为 `failed` 或 `skipped`；
- 在 `state.degradation` 中记录原因；
- 不应默认用编造数据填充 `signals.json`。

### 6.2 无原生抓取能力或部分抓取失败

行为建议：

- 用搜索 snippet 作为临时 items；
- 标记 `reliability=low`、`notes=fetch_failed`；
- 在 `state.degradation` 中记录 fallback；
- 允许 Scout 继续生成 brief，Writer 基于 brief 继续工作。

### 6.3 Scout 失败

行为建议：

- 尽量保留 `state.json` 与已有中间产物；
- 若没有 `brief.md`，Writer 可跳过 script 生成；
- 仍建议追加至少 1 行 `experiments.jsonl`，说明失败点与后续尝试方向。

### 6.4 Writer 失败

行为建议：

- 若 Scout 已完成，则保留 `signals.json`、`items.jsonl`、`brief.md`；
- 将 script step 标记为 `failed`；
- 在 `summary` 或 `degradation` 中写清原因。

### 6.5 experiments 追加失败

行为建议：

- 不影响本轮主产物保存；
- 在 `state.degradation` 中单独记录，便于补写或重跑。

总体原则：**单步失败不拖垮整轮；能写的产物尽量落盘，不能写的要把原因写清。**

## 7. 为什么拆成 workflow + agents

拆分的本质，不是为了目录整齐，而是为了把：

- **编排逻辑**（workflow）
- **任务说明**（agents）
- **执行实现**（tools / src / plugins）

三者解耦。

这样做有四个直接好处：

### 7.1 复用

Scout 与 Writer 可以在其他 workflow 中复用，例如：

- 只跑信号发现；
- 从已有 brief 直接生成 script；
- 将 Writer 接到别的内容源后面。

### 7.2 迭代

可以单独修改 `agents/scout.md` 或 `agents/writer.md` 的内容标准，而不必重写 `daily.md` 的编排逻辑。

### 7.3 替换

后续无论替换：

- 搜索提供方；
- 抓取实现；
- 模板渲染器；
- 插件或脚本执行器；

都不应要求重写主 workflow。

### 7.4 可维护性

后续维护者可以快速区分：

- 哪些文件定义“流程”；
- 哪些文件定义“任务”；
- 哪些文件只是“实现方式”。

## 8. 原生工具与过渡执行器的关系

本文中经常使用 `web_search` / `web_fetch` 两个名字，含义应理解为：

- **示意性的原生搜索/抓取能力名称**；
- 不是对所有 OpenClaw 版本、所有运行环境都成立的固定命名；
- 如果当前环境没有这些原生能力，应由 `tools/exec/*` 承担过渡职责。

因此，本项目更强调的是：

- workflow 层声明“需要搜索”“需要抓取”；
- execution plane 决定由谁来完成这些动作。

## 9. Non-goals

当前阶段不以以下目标为重点：

- 设计 GUI 或前端页面；
- 建立复杂数据库与后台服务；
- 强绑定某一个外部搜索 API；
- 把 Bash 提升为主编排器；
- 把 `experiments.jsonl` 做成复杂评估平台；
- 假设通知系统已经接通并默认可用。

## 10. 一句话总结

这套设计的核心不是“用 OpenClaw 调几个脚本”，而是：

**把内容闭环中的“做什么”固定在 workflow / agents 中，把“怎么做”留给原生工具、脚本或插件实现，从而让系统具备可替换、可降级、可追溯的工程特性。**
