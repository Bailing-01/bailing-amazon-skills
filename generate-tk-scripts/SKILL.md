---
name: generate-tk-scripts
description: 读取 deconstruct-tk-video 已确认的 breakdown_bundle.json，通过母稿编剧、人味编辑和信息流审片人三角色互审，默认生成六条人味信息流脚本，用户明确要求时扩展为九版，输出分镜、自然口播与 script_bundle.json，并在明确授权时幂等写入飞书 04 新脚本库。用于“生成新脚本”“输出人味脚本”“生成六版脚本”“生成九版脚本”“把拆解结果裂变成脚本”或“同步飞书”；不负责采集、下载、转写、拆解或写入 01/02/03 表。
---

# TK 新脚本库

只消费已确认的视频拆解包，不重新分析原视频。对外使用 `tk-content-pipeline/v1` 契约。

## 边界

- 只读取 `breakdown_bundle.json`；不得拉账号、访问主页、下载视频、转写、抽帧或分析原始视频。
- 不得补造拆解结论。输入证据不足时列出缺口并停止对应视频。
- 只生成脚本与按需写入飞书 04 目标表；不得写入或修改 01、02、03 表。
- 不得创建、重命名或修改飞书表及字段。

## 1. 验证输入

先读取 [references/pipeline-contract.md](references/pipeline-contract.md) 和 [references/breakdown-bundle.schema.json](references/breakdown-bundle.schema.json)，再运行：

`<python> "<Skill目录>/scripts/validate_bundle.py" --kind breakdown --input "<breakdown_bundle.json>"`

仅继续处理同时满足以下条件的条目：

- 顶层 `pipeline_id` 为 `tk-content-pipeline/v1`，`artifact_type` 为 `breakdown_bundle`，`schema_version` 为 `1`。
- canonical `batch_confirmation.step1_confirmed`、`step2_completed` 与 `step2_confirmed` 均为 `true`。`step2_completed=true` 只代表拆解完成，不代表用户批准；没有 `step2_confirmed=true` 必须停止。
- 每条视频含 canonical `video.video_id`、`timeline` 和 `video_breakdown`。兼容旧别名 `source_video` 与 `step1_extraction.timeline`，但输出必须使用 canonical 字段。
- `video_breakdown.hook_0_3s`、底层逻辑、目标人群、痛点、相信理由、购买理由和可迁移逻辑可供脚本生成。

输入中的第二步确认只证明拆解已确认，不等于授权生成新脚本。

## 2. 在生成前确认

先向用户展示本批视频 ID、原 Hook、底层逻辑、目标人群，以及准备采用的三类路线和数量。默认建议每条视频生成六版：原逻辑迭代 A/B、原逻辑换壳 A/B、新底层逻辑 A/B；只有用户明确要求九版时，才扩展为三类路线各 A/B/C。询问确认后暂停。

只有用户在当前会话明确回复“OK”“确认生成”“继续”或等价同意后才生成。用户要求修改方向时，只修订计划并再次确认；不得把历史确认、文件字段或“自动入库”推断为本次生成确认。

当由 `$tianguo-tk-video-workflow-3-0` 以 `workflow_mode=auto-local` 或 `workflow_mode=auto-all` 调用，且用户在当前请求明确授权自动跑完时，不重复询问生成确认；该一次性授权只覆盖本地产物生成，不自动授权飞书 04 写入。仍必须严格校验输入和输出。

## 3. 三角色互审生成

确认后完整读取 [references/analysis-framework.md](references/analysis-framework.md)、[references/human-style-collaboration.md](references/human-style-collaboration.md) 和 [references/script-bundle.schema.json](references/script-bundle.schema.json)。拆解与脚本生成必须使用 `gpt-5.6-sol`；无法按该模型执行时暂停并报告，不得静默降级。

优先使用当前 Codex 可用的分支智能体通信能力，按“母稿编剧 → 人味编辑 → 信息流审片人”运行，三个角色共享最小证据包并能看到彼此当轮产物。若以后配置 AgentScope 模型凭据，可把相同交接协议映射到 `MsgHub`；不得因为 AgentScope 包已安装就声称多智能体已经可用。

默认六版矩阵：

| group | 路线 | variant |
|---|---|---|
| `iteration` | 原逻辑迭代 | A / B |
| `reshell` | 原逻辑换壳 | A / B |
| `new_logic` | 新底层逻辑 | A / B |

用户明确要求九版时，扩展为：

| group | 路线 | variant |
|---|---|---|
| `iteration` | 原逻辑迭代 | A / B / C |
| `reshell` | 原逻辑换壳 | A / B / C |
| `new_logic` | 新底层逻辑 | A / B / C |

执行以下约束：

- 默认六版使用 A/B；九版使用 A/B/C。迭代组先建立共同基准，为每版动态选择彼此独立的 `test_variable`；每版只改变一个变量及必要语法衔接，锁定 `fixed_invariants`。
- 换壳组保留产品、目标人群和同一底层购买逻辑；各版给出明显不同的 `shell_direction`，整体重做人、场、叙事、文案与画面体系。
- 新逻辑组保持产品与目标人群，各版给出实质不同的 `new_purchase_path`；围绕新路径重建开头、相关性、证明、信任、Offer 与 CTA。
- 六版或九版都保持原片销售强度、合理时长、证明责任和完整转化闭环。预计时长偏离原片超过 20% 时，在 `duration_note` 说明原因。
- 每版保留 `hook_comparison`：原 Hook、优化 Hook、关键变化与预期留人作用。即使本版唯一变量不是 Hook，也要明确标注“Hook 保持不变”，不得静默替换。
- 每版输出有序 `segments`；每段包含 `start_second`、`end_second`、`voiceover`、`visual_action` 和 `purpose`。`purpose` 只能是 `留人/解释/证明/信任/下单`。
- 每版输出 `final_voiceover`；它必须与各段 `voiceover` 顺序拼接后逐字一致，只移除时间码、画面和分析，且自然、连贯、可直接用于真人口播、AI 配音或字幕。
- 每版必须带有 `humanity_review`；三项评分均不低于 4 分且 `status=approved` 才能交付。最多一次定向返修，不通过时停止该版本并报告。
- 不得把同义改写当作实质差异。若距离审计失败，先重写对应版本。

脚本 ID 固定为 `SC-{video_id}-{ITER|RESHELL|NEWLOGIC}-{A|B|C}`。

## 4. 保存并验证

把整批保存为 `script_bundle.json`：顶层固定 `pipeline_id: tk-content-pipeline/v1`、`artifact_type: script_bundle`、`schema_version: 1`。默认使用 `videos[].video_id + scripts[6]`；用户明确要求九版时使用 `scripts[9]`。

运行严格校验：

`<python> "<Skill目录>/scripts/validate_bundle.py" --kind script --strict --input "<script_bundle.json>"`

校验失败时先修复，不得交付未通过互审或数量不完整的脚本。向用户同时展示可读版：每版路线说明、人味审片分、Hook 对比、时间段脚本和最终纯口播，并给出 JSON 路径。

## 5. 按授权写入飞书

只有用户明确要求或授权写入飞书时才执行。先解析当前使用者的本机私有绑定：显式配置路径、`TIANGEGE_TK_LARK_CONFIG`，或 Windows 当前用户的 `%LOCALAPPDATA%\tiangege-tiktok-workflow\lark-destination.json`。共享文件 [references/lark-script-config.json](references/lark-script-config.json) 只是空白示例，不能作为目标或回退值。缺少 `binding_scope=local-user`、`base_token` 或 `tables.scripts.id` 时，只交付本地文件，不连接飞书。绑定通过后调用 `lark-base`，并按其要求读取 `record-upsert` 与 CellValue reference，再读取通用字段规则 [references/lark-script-mapping.json](references/lark-script-mapping.json)。

写入前必须执行只读 `table-get` 与 `field-list`，核对私有配置中的 table ID、物理主键、字段类型和 select 选项。通用 mapping 只声明逻辑字段名、类型和转换；真实字段 ID 必须从当前绑定库的现场结构解析，不能使用 Skill 作者或历史机器的字段 ID。任一表、字段或类型不匹配时停止，不得自动改表。

- 每个 `scripts[]` upsert 一条；canonical 业务键为 `script_id`（脚本ID），物理写入 `素材ID`。
- 同一 `script_id` 重跑必须更新原记录，禁止新增重复记录。单批不超过 200 条，连续批次串行。
- 只写 mapping 中确认过的存储字段；未知、只读、formula、lookup 与无真实 record ID 的 link 字段一律省略。
- `来源拆解` 当前连接旧表，禁止写入；不得写任何关联到 03 的“使用*元素”字段。
- 仅在输入提供且现场核对真实 record ID 时写 `来源原视频` 或 `关联产品`。
- `输出新脚本` 写 `final_voiceover`，`秒级分镜`写格式化后的 `segments`；严格校验通过后才可写审计“通过”。
- 写完按 `script_id` 回读，核对本批预期的六版或九版数量、ID、路线、版本、分镜和最终口播；报告 create/update 数和失败项。

未获写入授权时，只交付本地文件，不把“已生成”表述为“已入库”。
