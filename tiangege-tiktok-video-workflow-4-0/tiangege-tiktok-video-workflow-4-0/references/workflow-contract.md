# 田哥哥 TikTok 视频工作流 4.0 契约

## 1. 范围

4.0 是 103、104、105、106 的总控，只做输入路由、模式固定、确认、授权、JSON 交接、恢复和验收。阶段实现由四个原 Skill 负责。

| 阶段 | Skill | 输入 | 输出 |
|---|---|---|---|
| 103 账号采集 | `collect-tk-account` | 公开账号主页 | `account_manifest.json` |
| 104 视频拆解 | `deconstruct-tk-video` | 本地/单条视频或账号清单 | `breakdown_bundle.json`、`breakdown_report.md` |
| 105 素材沉淀 | `archive-tk-materials` | 已确认拆解包，可选账号清单 | `write-plan.json`、飞书 01/02/03 结果 |
| 106 脚本生成 | `generate-tk-scripts` | 已确认拆解包 | `script_bundle.json`、按授权写入飞书 04 |

完整本地终点为严格校验通过的 `script_bundle.json`；素材沉淀与脚本生成是已确认拆解包的两个独立下游。

## 2. 运行模式

| 模式 | 确认行为 | 外部写入 |
|---|---|---|
| `review` | 内容提取、拆解、脚本路线分别等待确认 | 每个写入范围分别授权 |
| `auto-local` | 当前请求的一次性自动授权覆盖本地确认 | 禁止连接飞书 |
| `auto-all` | 与 `auto-local` 相同 | 只写当前请求明确授权的 01/02/03/04 范围 |

“自动跑完”“一键完成”只选择 `auto-local`。只有当前请求同时明确要求自动执行和“同步飞书/自动入库”时才选择 `auto-all`。模式和终点必须写入阶段交接，不能中途扩大。

## 3. 规范交接

- 所有规范 JSON 使用 `pipeline_id: tk-content-pipeline/v1`。
- 103→104：只交接验证通过的 `account_manifest.json`。
- 104→105：只交接验证通过且 `batch_confirmation.step2_confirmed=true` 的 `breakdown_bundle.json`。
- 104→106：同样只交接验证通过且 `step2_confirmed=true` 的 `breakdown_bundle.json`。
- 106 输出 `artifact_type: script_bundle`、`schema_version: 1` 的 `script_bundle.json`。
- Markdown 只供人工审核，不是下游机器输入。
- 始终传递绝对路径，不把任务产物写进 Skill 安装目录。

拆解语义判断和 106 脚本生成的交接必须包含 `required_model: gpt-5.6-sol`。Skill 标签不能证明实际模型；无法确认执行单元时停止。

## 4. 状态机

| 状态 | 可执行动作 |
|---|---|
| 第一步未确认 | `review` 只展示整批内容提取并等待；自动模式按当前授权继续 |
| `step2_completed=true`、`step2_confirmed=false` | 展示拆解摘要；确认或自动授权后运行盖章脚本并读回 |
| `step2_confirmed=true` | 可按目标进入 105、106 或两者 |
| 106 路线未确认 | `review` 展示默认六版或明确九版计划并等待 |
| `script_bundle.json` 严格校验通过 | 本地脚本交付完成；可按授权处理飞书 04 |
| 写入计划完成、无飞书授权 | 停止，不连接飞书 |
| 当前会话有明确飞书授权 | 只在授权范围内核对真实结构并幂等写入 |
| 当前机器未绑定个人 Base | 只生成本地产物；所有模式都禁止连接飞书 |

第一步确认、第二步确认、脚本生成确认、01/02/03 写入授权和飞书 04 写入授权互不替代。旧批次、历史授权、文件存在、赶时间或含糊的“继续”不得用于扩大范围。

## 5. 脚本契约

- 默认六版：原逻辑迭代 A/B、原逻辑换壳 A/B、新底层逻辑 A/B。
- 只有用户明确要求九版时，扩展为三类路线各 A/B/C。
- 生成前由 `generate-tk-scripts` 验证 canonical 拆解字段并展示路线。
- 生成与拆解语义判断必须使用 `gpt-5.6-sol`；失败时暂停，不得降级。
- 最终运行严格脚本校验；数量、ID、路线、时间轴、`final_voiceover` 和 `humanity_review` 任一失败都不得交付或入库。
- 飞书 04 写入由 106 独立管理；105 不得写 04。

## 6. 恢复

1. 发现 `account_manifest.json`：先运行 103 校验器；通过后从 104 继续。
2. 发现 `breakdown_bundle.json`：先运行 104 校验器，再读取确认状态。
3. `step2_confirmed=true` 且缺少 `script_bundle.json`：按目标进入 105、106 或两者。
4. 发现 `write-plan.json`：重新核对源 JSON 和真实飞书结构；只有当前写入授权仍明确时才写入。
5. 发现 `script_bundle.json`：先运行 106 严格校验；通过后不重新生成，只做本地交付或按授权处理飞书 04。
6. 任一校验失败：修复当前阶段，不回滚已验证产物，不伪造下游文件。
7. 飞书部分失败：只按表、批次和业务键重跑失败项。

## 7. 内容类型边界

短链接必须先解析真实 `post_type`。现有正式契约以视频时间轴为准；TikTok Photo Mode 只有在页码证据 schema、验证器、105 映射和 106 输入映射全部存在并通过测试后，才能进入标准下游。否则只保留完整图片、音频、元数据和失败报告，不生成伪造的视频拆解包或脚本包。

## 8. 飞书边界

- 目标库使用当前操作系统用户的私有配置：显式路径、`TIANGEGE_TK_LARK_CONFIG`，或 Windows `%LOCALAPPDATA%\tiangege-tiktok-workflow\lark-destination.json`。
- Skill 目录只提供空白示例；不得包含作者真实 Base 地址、token、table ID 或 field ID，也不得作为无绑定机器的回退目标。
- 105 使用私有配置中的 01、02、03；106 单独使用同一配置中的 04。
- 每个写入阶段都重新读取真实表结构、字段类型和 select 选项。
- 01→02→03 串行写入；04 只在脚本严格校验和独立授权后写入。
- 按业务键区分 create/update，不创建空分隔行，不删除记录，不改表结构。
- 私有后台指标没有证据时保持 `null`，不得用 0 代替缺失。
- 完成后读回业务键、关联关系、数量和当前批次空值，再报告成功、更新、跳过和失败数。

## 9. 失败报告

失败时必须给出：运行模式、失败阶段、失败原因、已完成产物绝对路径、未执行范围、可恢复入口、实际模型和需要用户采取的动作。局部成功不得描述为整条工作流完成。
