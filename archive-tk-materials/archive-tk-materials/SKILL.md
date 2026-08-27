---
name: archive-tk-materials
description: 将 collect-tk-account 的 account_manifest.json 与 deconstruct-tk-video 的 breakdown_bundle.json 校验、映射并按当前使用者的本机绑定幂等沉淀到飞书 Base 的 01 原视频库、02 竞品拆解库和 03 元素库。用于用户要求素材入库、批量沉淀竞品账号、补写拆解结果、同步可迁移元素或重跑失败批次；不负责拉取账号、转写拆解视频、生成新脚本或写入 04 新脚本库。
---

# TK 素材沉淀

将采集和拆解产物转成可审计的飞书写入计划，再按业务键串行 upsert。只处理 `tk-content-pipeline/v1`，只写 `01`、`02`、`03` 三张表。

## 输入与职责边界

- 读取 `account_manifest.json`：原视频、账号、公开指标和本地视频路径。
- 读取 `breakdown_bundle.json`：`video/transcript/timeline/video_breakdown/elements/scores/duplicate_cluster` 领域对象；本 Skill 负责映射飞书字段。
- 不接受原始视频作为分析输入；缺少拆解时调用 `$deconstruct-tk-video`。
- 不生成脚本；需要默认六版、明确九版脚本和 `04 新脚本库` 时调用 `$generate-tk-scripts`。
- 用户只要求预览时停在写入计划，不连接飞书。

必须先读取 [references/pipeline-contract.md](references/pipeline-contract.md) 和 [references/lark-write-contract.md](references/lark-write-contract.md)。[references/lark-base-config.json](references/lark-base-config.json) 只是可分享的空白示例，不能当作真实目标。真实目标从 `--lark-config`、`TIANGEGE_TK_LARK_CONFIG`，或 Windows 当前用户的 `%LOCALAPPDATA%\tiangege-tiktok-workflow\lark-destination.json` 读取。字段映射读取 [references/lark-step2-breakdown-mapping.json](references/lark-step2-breakdown-mapping.json) 和 [references/lark-element-table-fields.json](references/lark-element-table-fields.json)。

## 执行流程

### 1. 验证并生成写入计划

运行：

```powershell
& "<python>" "<Skill目录>\scripts\build-write-plan.py" `
  --account-manifest "<account_manifest.json>" `
  --breakdown-bundle "<breakdown_bundle.json>" `
  --lark-config "<可选：当前使用者的 lark-destination.json>" `
  --output "<write-plan.json>"
```

单条视频任务可以省略账号清单；脚本会从拆解包构造 `01` 行。未提供参数时只查找当前操作系统用户的默认私有路径。没有本机绑定仍可生成本地计划，但必须得到 `target.binding_status=unbound`、`safe_to_write=false` 和空 `table_id`；不得连接飞书，也不得回退到 Skill 作者或其他机器的目标库。验证失败时停止，不得猜测缺失的 `video_id`、业务键或表 ID。

### 2. 预览与确认

报告三个表各自的新增候选数、更新候选数、跳过数、空指标数和异常数。展示绑定状态、配置路径、目标 Base 名称及三张表名称。只有 `binding_status=bound`、`safe_to_write=true` 且用户明确要求自动入库或确认写入后，才执行飞书写操作。

当由 `$tiangege-tiktok-video-workflow-4-0` 以 `workflow_mode=auto-all` 调用，且用户在当前请求明确要求“自动入库/同步飞书”时，可跳过再次人工确认，直接进入真实结构核对与幂等写入；其他模式仍停在写入计划。即使获得授权，缺少当前使用者的本机绑定也必须停在本地产物。

### 3. 读取真实结构

遵循 `lark-base`，默认使用 `--as user`：

1. 只用当前使用者私有配置中的 `base_token` 和真实 `table_id`；共享 Skill 中的示例值无效。
2. 对三张表分别运行 `lark-cli base +field-list`，核对字段类型、只读字段及 select 选项。
3. 按业务键搜索现有记录，得到 `record_id`；不得把 `+record-upsert` 误当成按业务键自动查重。
4. 关联字段必须先取得 `01 原视频库` 的真实 `record_id`。

### 4. 串行幂等写入

严格按 `01 → 02 → 03`：

- `01 原视频库`：按 `视频ID` 查重，只写原视频、公开指标和本次执行的 `本批更新时间`；该字段表示采集/回传批次时间，不等于视频自身的 `发布时间`。
- `02 竞品拆解库`：按 `拆解ID = BD-{video_id}` 查重，维护 `关联原视频`；`综合评分`、`学习价值` 永不写入。
- 配置中的 `elements` 表：按 `元素ID` 查重；相同 ID 更新，不创建重复元素。
- 新记录用 `+record-batch-create`，已有记录用 `+record-batch-update`；每批最多 200 条，同一表连续批次必须串行。
- 附件使用 `+record-upload-attachment`，不得作为普通 CellValue 写入。
- 后台指标未由用户提供时保持 `null`，不得写 `0` 或声称已验证。
- 遇到 `1254291` 只对当前批次短暂等待后重试；其他错误记录到失败清单，不重复整批写入。

### 5. 验收

以写入返回为主；返回不足或用户要求核验时，按三个业务键抽查读回。每批写入后必须检查三张表是否出现业务键为空的记录；当前批次若产生空记录，停止后续写入并报告，不能把空行留在有效批次之间。输出：成功创建、成功更新、跳过、失败、`ignored_fields`、待补附件和重试项。出现只读字段被忽略时，从 payload 移除，不得原样重试。

## 固定规则

- `02 竞品拆解库` 是唯一拆解主表；默认不写历史表 `02 竞品拆解评分库` 和 `02A 竞品拆解人工总览`。
- `原视频中文内容` 必须是完整中文转写或完整翻译，不得写摘要。
- select 只写真实已存在选项；不匹配的值进入人工复核清单。
- 公开数据只能生成“候选”元素；私有点击率、加购率、转化率无证据时留空。
- 批量产物同时保留机器可读 JSON，确保失败后可按表、批次和业务键恢复。
- 不删除记录、不改表结构、不创建字段，除非用户明确提出并单独确认。

## 交付格式

返回写入计划路径、个人绑定状态与配置路径、目标 Base、三个表的结果统计、失败清单路径，以及是否完成读回核验。明确声明本 Skill 没有写入 `04 新脚本库`。
