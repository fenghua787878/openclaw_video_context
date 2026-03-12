# Content Loop — OpenClaw-first 内容生成闭环

以 **OpenClaw 为控制面（control plane）** 的内容生成闭环设计：围绕“信号发现 → 内容采集 → 策展简报 → 脚本生成 → 落盘 → 经验记录”构建一条可追溯、可降级、可替换执行器的工作流。

> 当前状态：本项目目前是 **OpenClaw-first 的应用设计 + 目录约定 + 运行约定**。  
> `workflows/`、`agents/`、`policy/`、`runs/`、`schemas/` 的职责已经明确；  
> 具体运行命令、工具名称（如 `web_search` / `web_fetch`）以及插件接入方式，需以实际 OpenClaw 版本与本机运行环境为准。

## 项目定位

### 这是什么

这是一个把 **编排逻辑** 与 **执行逻辑** 分开的内容应用：

- **编排层**：由 `workflows/daily.md` 组织每日闭环步骤。
- **任务层**：由 `agents/scout.md` 与 `agents/writer.md` 分别承担“发现/整理”和“成稿/复盘”。
- **执行层**：搜索、抓取、读写文件、可选脚本执行，由运行环境原生工具或 `tools/exec/` 过渡脚本完成。
- **产物层**：所有运行结果落入 `runs/<run_id>/`，并将经验追加到 `policy/experiments.jsonl`。

### 这不是什么

当前阶段，它**不是**：

- 一个已经完全实现并验证完毕的 GUI 产品；
- 一个必须依赖某个固定搜索提供方的系统；
- 一个以 Bash 为主控制器的脚本项目；
- 一个强绑定某个 OpenClaw 内置命令名或工具名的官方模板。

## 术语说明

- **主入口**：本项目约定的唯一编排入口，即 `workflows/daily.md`。
- **workflow**：负责编排步骤、输入输出、停止条件、降级规则。
- **agent**：负责完成某一类子任务的说明文档，如 Scout / Writer。
- **control plane**：决定“下一步做什么”。
- **execution plane**：负责“具体怎么做”，如搜索、抓取、写文件、执行脚本。
- **degradation**：当某一步能力缺失或失败时，采用降级输出并在 `state.json` 中记录原因。

## 目录结构

```text
content_loop/
├── README.md
├── APP_OVERVIEW.md
├── .gitignore
├── workflows/
│   └── daily.md                 # 必须：总编排工作流（唯一主入口）
├── agents/
│   ├── scout.md                 # 必须：信号发现 → 采集 → 简报
│   └── writer.md                # 必须：脚本生成 + experiments 追加
├── policy/
│   ├── policy.md                # 必须：主题、风格、禁区、评分偏好
│   ├── experiments.jsonl        # 必须：每次运行追加经验记录
│   └── notifications.json       # 可选：后续接入邮件/消息通知时使用
├── runs/
│   └── <run_id>/                # 必须：每次运行的产物目录
├── schemas/
│   ├── state.schema.json
│   ├── signals.schema.json
│   ├── item.schema.json
│   ├── brief.schema.json
│   └── script.schema.json
├── tools/
│   └── exec/                    # 可选：运行环境能力不足时的过渡执行器
│       ├── fetch_sources.py
│       ├── fetch_sources_searxng.py
│       ├── fetch_content.py
│       └── maintain_proxy.sh
└── src/
    ├── __init__.py
    ├── run_id.py
    ├── io_utils.py
    ├── schemas.py
    ├── normalize.py
    └── curate.py
```

### 各目录职责

- **workflows/**：只负责编排，不负责实现搜索/抓取细节。
- **agents/**：只描述子任务目标、输入、输出、检查项。
- **policy/**：保存主题偏好、风格要求、禁区与实验记录。
- **runs/**：保存每轮运行的状态与产物，便于审计与复盘。
- **schemas/**：定义 JSON 契约，便于校验与自动化处理。
- **tools/exec/**：仅作为运行环境缺少原生工具能力时的过渡层。
- **src/**：放共享工具函数，供脚本或未来插件实现复用。

## 当前实现状态

### 已明确的设计与约定

- 以 `workflows/daily.md` 作为唯一主入口。
- 以 Scout / Writer 作为核心子任务拆分。
- 以 `runs/<run_id>/` 保存全量产物。
- 以 `policy/experiments.jsonl` 记录每次运行的复盘经验。
- 若已配置 Notion 能力，同步把脚本写入「文本升级观测」数据库，人工回填播放/点赞/粉丝效果。
- 以 schema 约束 JSON 产物格式。

### 依赖实际环境确认的部分

- 是否支持“直接以 Markdown 文件作为可执行工作流入口”；
- 具体命令是否为 `openclaw run workflows/daily.md`；
- 是否存在原生搜索/抓取能力；
- 原生工具名是否恰好为 `web_search` / `web_fetch`；
- 是否可以直接在 workflow 中调用本地 Python / Shell 执行器。

### 预留扩展项

- `policy/notifications.json`：用于后续接入邮件、WeCom 等通知；
- `tools/exec/*`：在无原生工具能力时作为过渡方案；
- 多 provider 搜索/抓取实现；
- 多 renderer 的 brief / script 模板体系。

## 最小运行前提

要跑通 MVP，至少应满足以下之一：

### 方案 A：运行器原生支持

运行器能够：

- 读取 Markdown workflow；
- 在步骤中执行 agent 文档；
- 进行本地文件读写；
- 最好具备原生搜索与抓取能力。

### 方案 B：运行器 + 过渡脚本

若运行器不具备完整原生能力，则至少应允许：

- 读取 Markdown workflow；
- 调用 `tools/exec/*.py` 或 `*.sh`；
- 读写 `runs/` 与 `policy/` 目录；
- 通过脚本自行完成搜索、抓取与内容提取。

## 快速开始

### 1）配置策略

编辑 `policy/policy.md`，设置：

- 主题范围；
- 内容风格；
- 禁区与风险边界；
- 评分偏好；
- 输出形态。

### 2）确认运行环境

先确认当前运行环境是否支持以下能力：

- 以 Markdown 作为工作流入口；
- 在 workflow 中执行 `agents/*.md`；
- 本地文件读写；
- 原生搜索/抓取，或可调用 `tools/exec/*` 过渡脚本。

### 3）运行一次闭环

本项目约定以 `workflows/daily.md` 作为唯一主入口。  
若当前 OpenClaw 运行器支持“直接执行 Markdown 工作流文件”，可类似如下方式启动：

```bash
openclaw run workflows/daily.md
```

实际命令名、参数格式、是否支持该模式，需以你本机安装版本与运行器能力为准。

### 4）查看产物

一次运行完成后，重点查看：

- `runs/<run_id>/state.json`：本轮状态、失败点、降级项；
- `runs/<run_id>/signals.json`：信号列表；
- `runs/<run_id>/items.jsonl`：深挖结果；
- `runs/<run_id>/brief.md`：策展简报；
- `runs/<run_id>/script.md`：成稿脚本；
- `runs/<run_id>/notification.md`：通知正文（邮件正文默认应包含 script.md 全文，可直接发送）；
- `policy/experiments.jsonl`：经验记录追加情况。

> `policy/notifications.json` 目前应视为**预留配置项**，除非你已经接入实际通知链路，否则不应默认理解为“配置后即可自动发送”。

## 运行约定

### 主入口约定

- 本项目约定 `workflows/daily.md` 为唯一主入口；
- 任何定时器、CLI 包装器、crontab，都应只负责“何时触发”，不应承担主流程编排。

### 子任务约定

- Step 2：执行 `agents/scout.md`，负责信号发现、初步采集、生成简报；
- Step 3：执行 `agents/writer.md`，负责读取 policy / experiments / brief，生成脚本并追加经验记录。

### 产物约定

每轮运行至少应尝试写入：

- `state.json`
- `signals.json`
- `items.jsonl`
- `brief.md`
- `script.md`
- `policy/experiments.jsonl`

其中允许部分失败，但失败原因必须尽可能写入 `state.json`。

## 降级策略

| 情况 | 行为 |
|------|------|
| 无原生搜索能力 | 可改走 `tools/exec/fetch_sources_searxng.py` 或 `tools/exec/fetch_sources.py`；若仍不可用，则在 state 中标记相应 step 为 failed / skipped |
| 无原生抓取能力 | 仅使用搜索 snippet 生成 items，并标注 `reliability=low`、`notes=fetch_failed` |
| Scout 某步失败 | 尽量保留 `state.json` 与已有中间产物，并写清失败原因 |
| Writer 某步失败 | 尽量追加至少 1 行 experiments，说明本轮失败点与后续尝试方向 |
| experiments 追加失败 | 在 `state.degradation` 中记录，便于补写或重跑 |

## tools/exec 说明（过渡层）

这些脚本不是主编排器，只是在运行器原生能力不足时提供过渡方案。

- **fetch_sources.py**：输入关键词，输出 signals.json 或 stdout；可用于 mock、占位或最小搜索链路。
- **fetch_sources_searxng.py**：通过本地 SearXNG 实例执行搜索。
- **fetch_content.py**：对 URL 列表抓取正文并输出 items.jsonl。
- **sync_script_to_notion.py**：把 `runs/<run_id>/script.md` 拆分成逐条 Notion 写入命令，写入 `runs/<run_id>/notion_sync_commands.txt`。
- **maintain_proxy.sh**：检查代理连通性，供外网访问依赖场景使用。

> 若你的 OpenClaw 运行环境已经提供成熟的原生搜索/抓取工具，则优先使用原生能力。本文中的 `web_search` / `web_fetch` 只是**示意名称**，不代表所有环境都使用这两个固定名字。

## MVP 边界

当前 MVP 的目标是：

- 形成一条可运行、可落盘、可复盘的内容闭环；
- 明确 control plane / execution plane 的职责边界；
- 能在运行器能力不同的情况下平稳降级。

当前 MVP **不以以下能力为目标**：

- GUI 页面；
- 复杂用户权限系统；
- 自动邮件发送已默认可用；
- 数据库与后台服务必选；
- 将 Bash 作为主工作流控制层。

## Roadmap

- **短期**：优先跑通 Markdown workflow + 原生工具 / 过渡脚本。
- **中期**：将 `tools/exec` 的关键能力迁移为插件或统一工具接口。
- **长期**：支持多 provider、多模板、多输出渠道，并持续用 `experiments.jsonl` 驱动改进（以人工回填的播放量/点赞量/加粉量为主要升级依据，按 content_category 与 expression_variant 两维度评估）。

## 约束与原则

- 不编造事实：所有信号与证据都应带 URL。
- 时间未知统一写 `unknown`。
- 单步失败不应拖垮整轮；能落盘的产物尽量落盘。
- Bash 只作为可选执行器，不作为主工作流编排器。
- workflow / agents 定义“做什么”，执行器定义“怎么做”。
