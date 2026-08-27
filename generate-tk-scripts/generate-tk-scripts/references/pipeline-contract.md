# TK 内容管线 v1 契约

## 输入

只接受 JSON 文件：

- `pipeline_id`: 固定 `tk-content-pipeline/v1`
- `artifact_type`: 固定 `breakdown_bundle`
- `schema_version`: 固定整数 `1`
- canonical `batch_confirmation.step1_confirmed`: 必须为 `true`
- canonical `batch_confirmation.step2_completed`: 必须为 `true`
- canonical `batch_confirmation.step2_confirmed`: 必须为 `true`，表示用户已批准拆解结果
- `videos[]`: 至少一条已确认视频拆解

每条 canonical `videos[]` 至少包含：

- `video.video_id`
- `timeline[]`
- `video_breakdown`

推荐同时保留 `transcript`、`frames`、`elements`、`scores`、`duplicate_cluster` 和 `step2_base_row`。兼容读取旧别名 `source_video` 与 `step1_extraction.timeline`；兼容只用于迁移，生成输出必须规范化。

`video_breakdown` 应提供：

- `underlying_logic`
- `video_type`
- `retention_method`
- `hook_0_3s.original_copy`
- `hook_0_3s.optimized_copy`
- `hook_0_3s.key_changes`
- `hook_0_3s.intended_retention_effect`
- `audience`
- `pain`
- `result`
- `belief_and_action`
- `element_coordination`
- `transferable_logic`

拒绝条件：

- 第二步未确认；
- pipeline/artifact/schema 不匹配；
- 缺少 video ID、时间线或拆解；
- 原 Hook、底层逻辑、受众或相信/购买路径不足以支撑脚本；
- 输入只是原始视频、链接、转写或帧文件。

## 生成确认

canonical `batch_confirmation.step1_confirmed=true + step2_completed=true + step2_confirmed=true` 才代表拆解已完成并获用户批准。`step2_completed=true` 单独出现时必须停止。旧包只有 `step2_confirmed=true` 可兼容读取并警告缺少进度字段。上述文件状态仍不等于生成授权，生成 Skill 必须在当前会话另行获得用户明确确认，且不得把该确认写回输入文件充当用户授权。

## 输出

`script_bundle.json` 顶层：

- `pipeline_id`: `tk-content-pipeline/v1`
- `artifact_type`: `script_bundle`
- `schema_version`: `1`
- `generated_at`: RFC 3339 时间
- `source_breakdown`: 输入文件路径或稳定标识
- `videos[]`: canonical `video_id` 与 `scripts[6]` 或 `scripts[9]`

默认每个视频包含六个 `(group, variant)` 组合：

- `iteration`: A/B；ID 中使用 `ITER`
- `reshell`: A/B；ID 中使用 `RESHELL`
- `new_logic`: A/B；ID 中使用 `NEWLOGIC`

用户明确要求九版时扩展为：

- `iteration`: A/B/C；ID 中使用 `ITER`
- `reshell`: A/B/C；ID 中使用 `RESHELL`
- `new_logic`: A/B/C；ID 中使用 `NEWLOGIC`

每条脚本至少包含：

- `script_id`
- `group`, `route`, `variant`
- `test_variable`, `shell_direction`, `new_purchase_path`
- `fixed_invariants`
- `hook_comparison`
- `segments`
- `final_voiceover`
- `estimated_duration_seconds`
- `duration_note`
- `humanity_review`：人味、信息流和销售三项审片分及返修记录

不同 group 的专属方向字段：

- `iteration.test_variable` 非空；另两项为空字符串。
- `reshell.shell_direction` 非空；另两项为空字符串。
- `new_logic.new_purchase_path` 非空；另两项为空字符串。

脚本 ID 格式：

`SC-{video_id}-{ITER|RESHELL|NEWLOGIC}-{A|B|C}`

`final_voiceover` 的规范化值必须等于所有 `segments[].voiceover` 依次无分隔拼接后的规范化值。规范化只折叠空白，不改标点或文字。
