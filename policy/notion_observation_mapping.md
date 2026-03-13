# Notion 文本升级观测字段映射

目标数据库：`openclaw / 文本升级与观测 / 文本升级观测`

## 工具约定（来自 tool.md）
- 调用方式：`调用 notion [command]`
- API Key：配置于 `scripts/notion_tool.py`
- Default Page：`311cecbc-fbf4-80d3-afa3-c3482fcb6532`（openclaw功能和任务列表）

## 字段映射（Writer -> Notion）
- `文本ID`：`<run_id>_<script_id>`
- `文本正文`：`runs/<run_id>/script.md` 中对应脚本正文
- `内容方向`：`content_category`
- `表达方式`：`expression_variant`
- `播放量`：人工填写（发布后）
- `点赞量`：人工填写（发布后）
- `粉丝量`：人工填写（发布后）

## Writer 使用方式
1. 本轮脚本生成后先写入 `文本ID/文本正文/内容方向/表达方式`。
2. 播放、点赞、粉丝字段允许为空或 0，等待人工回填。
3. 下轮生成前，读取最近已填数值记录，按以下优先级比较策略有效性：
   - 同一 `内容方向` 下比较不同 `表达方式`
   - 再比较不同 `内容方向` 的整体表现
4. 若样本不足（某组合小于 3 条），不做硬性升级，只记录观察。

## 建议命令模板（示意）
- 读取最近人工回填记录：`调用 notion query_database 文本升级观测 sort=最近编辑 desc filter=播放量>0`
- 写入本轮脚本记录：`调用 notion create_page 文本升级观测 {文本ID, 文本正文, 内容方向, 表达方式}`

> 具体 command 参数以运行器中 notion 工具的实际实现为准；本文件只约束字段与流程。

## 自动化写入建议
- 推荐先运行：`python tools/exec/sync_script_to_notion.py --run-id <run_id> --content-category <内容方向> --expression-variant <表达方式>`
- 该脚本会把 Notion 命令写入：`runs/<run_id>/notion_sync_commands.txt`
- 再逐条执行其中的 `调用 notion [command]`，确保每个脚本都写入数据库。
