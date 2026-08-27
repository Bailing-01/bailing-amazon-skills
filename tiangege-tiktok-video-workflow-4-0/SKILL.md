---
name: tiangege-tiktok-video-workflow-4-0
description: Use when 用户要求从公开 TikTok/TK 账号、单条公开视频、本地视频、account_manifest.json、breakdown_bundle.json 或 script_bundle.json 开始、继续或恢复完整 TK 内容生产任务，且目标涉及素材拆解、素材沉淀、新脚本生成或飞书同步。
---

# 田哥哥 TikTok 视频工作流 4.0

## 总则

只负责编排 `$collect-tk-account`、`$deconstruct-tk-video`、`$archive-tk-materials` 和 `$generate-tk-scripts`。阶段实现、字段映射、脚本规则和校验器仍由各阶段 Skill 负责；阶段间只交接 `tk-content-pipeline/v1` JSON。

开始时完整读取 [references/workflow-contract.md](references/workflow-contract.md)，随后只加载当前阶段 Skill。完整工作流的规范产物为 `account_manifest.json`、`breakdown_bundle.json`、可选 `write-plan.json` 和 `script_bundle.json`。

## 运行模式

从用户当前请求识别并固定本批模式，不在中途自行扩大权限：

| 模式 | 本地自动范围 | 飞书写入 |
|---|---|---|
| `review`（默认） | 在内容提取、拆解和脚本路线确认门暂停 | 每个写入范围单独授权 |
| `auto-local` | 自动完成采集、拆解、素材写入计划和默认六版脚本 | 不连接飞书 |
| `auto-all` | 与 `auto-local` 相同 | 仅按当前请求明确的“同步飞书/自动入库”范围写入 |

“自动跑完”“一键完成”选择 `auto-local`；只有当前请求同时明确要求自动执行和“同步飞书/自动入库”时才选择 `auto-all`。自动模式仍必须在环境、证据、模型、JSON 契约或外部接口失败时停止。

## 路由

| 当前输入或状态 | 执行阶段 | 规范产物 |
|---|---|---|
| 公开 TikTok 账号主页 | `$collect-tk-account` | `account_manifest.json` |
| 本地 MP4/MOV/WebM/M4V、单条公开视频 | `$deconstruct-tk-video` | `breakdown_bundle.json`、`breakdown_report.md` |
| `account_manifest.json` | `$deconstruct-tk-video` | `breakdown_bundle.json`、`breakdown_report.md` |
| 已完成但未确认的 `breakdown_bundle.json` | 第二步审核确认 | 已确认的 `breakdown_bundle.json` |
| 已确认的 `breakdown_bundle.json`，目标含素材沉淀 | `$archive-tk-materials` | `write-plan.json`，按授权写入飞书 01/02/03 |
| 已确认的 `breakdown_bundle.json`，目标含脚本 | `$generate-tk-scripts` | `script_bundle.json`，按授权写入飞书 04 新脚本库 |
| 已严格校验的 `script_bundle.json` | 恢复或验收 | 本地交付；仅按授权处理飞书 04 |

账号主页先采集再拆解；本地视频和单条视频跳过采集。短链接先解析真实内容类型；发现 TikTok Photo Mode 时，只有已安装正式的页码证据 schema、验证器和 105/106 映射才可继续，否则保存完整图片、音频和元数据后停止，禁止伪造视频 `breakdown_bundle.json`。

已有规范 JSON 时从对应阶段恢复，不重新执行已验证通过的上游。

## 确认与授权

### 1. 内容提取确认

`review` 模式下，`$deconstruct-tk-video` 完成整批第一步内容提取后暂停。用户明确回复“OK”“下一步”或等价确认后，才执行十项拆解。自动模式将当前请求的一次性本地自动授权视为本批确认。

### 2. 拆解确认

十项拆解首次完成时保持 `batch_confirmation.step2_confirmed=false`。`review` 模式展示摘要并等待当前批次确认；确认后使用已验证的 Python 运行：

`scripts/confirm-breakdown.py "<breakdown_bundle.json绝对路径>"`

脚本必须先调用 104 完整校验器，再幂等盖章。重新读取并核对 `step2_confirmed=true` 后，才能进入 105 或 106。自动模式也必须运行同一盖章脚本，不得只在文字中假定已确认。

### 3. 脚本路线确认

`$generate-tk-scripts` 先展示视频 ID、原 Hook、底层逻辑、目标人群、路线和数量。默认六版：原逻辑迭代 A/B、原逻辑换壳 A/B、新底层逻辑 A/B；只有用户明确要求九版时，才扩展为三类路线各 A/B/C。

`review` 模式等待用户明确回复“OK”“确认生成”“继续”或等价确认后生成。`auto-local` 和 `auto-all` 将当前请求的一次性本地自动授权视为生成确认，但不等于飞书 04 写入授权。

拆解语义判断和脚本生成要求显式使用 `gpt-5.6-sol`。Skill 文本本身不能切换模型；交接时必须记录并核对 `required_model: gpt-5.6-sol` 与实际执行单元。无法验证或调用该模型时暂停，不得静默降级。

### 4. 飞书写入授权

素材与脚本是两个独立写入范围：

- `$archive-tk-materials` 只处理 01/02/03；先生成 `write-plan.json`，再按当前授权写入。
- `$generate-tk-scripts` 只处理 04 新脚本库；必须先得到严格校验通过的 `script_bundle.json`，再按当前授权写入。

所有飞书目标必须来自当前操作系统使用者的本机私有绑定：显式配置路径、`TIANGEGE_TK_LARK_CONFIG`，或 Windows 的 `%LOCALAPPDATA%\tiangege-tiktok-workflow\lark-destination.json`。Skill 安装目录只能带空白示例，不能携带作者的真实 Base 地址、token、table ID 或 field ID。当前机器没有有效绑定时，`review`、`auto-local` 和 `auto-all` 都只输出本地产物；即使已有写入授权，也不得连接飞书或回退到作者目标库。

`review` 模式下，用户必须明确说“写入飞书”“同步飞书”“自动入库”并指向当前批次和范围。“一个入口完成”“下一步”“继续”“赶时间”均不等于外部写入授权。`auto-all` 只使用当前请求已明确的写入范围；未覆盖的表保持只读。

## 下游选择

`step2_confirmed=true` 后按目标执行：

1. 只要素材库：调用 105，终点为本地写入计划或飞书 01/02/03。
2. 只要新脚本：调用 106，终点为 `script_bundle.json` 或按授权写入飞书 04。
3. 完整工作流：105 与 106 分别消费同一个已确认拆解包；任何一支失败不伪造另一支结果。

106 必须严格校验脚本数量、ID、分镜连续性、`final_voiceover` 逐字一致和 `humanity_review`。默认六版，不得擅自扩展为九版。

## 阶段交接

每次交接必须报告：运行模式、当前阶段、已验证输入、规范产物绝对路径、完成/跳过数量、失败项、实际模型、下一确认门或授权门。

下游先验证上游 JSON；不得从 Markdown 反推缺失字段。环境、下载、转写、视觉覆盖、JSON 契约、模型路由、飞书结构或权限任一失败时，停在当前阶段并保留可恢复产物。

## 快速检查

| 检查项 | 必须满足 |
|---|---|
| 管线 | `tk-content-pipeline/v1` |
| 顺序 | 103 采集 → 104 拆解 → 105 素材沉淀 / 106 脚本生成 |
| 拆解门槛 | 视觉覆盖通过，`step2_confirmed=true` |
| 脚本数量 | 默认六版；明确要求九版才生成九版 |
| 语义模型 | `gpt-5.6-sol`，失败不降级 |
| 本地产物 | `breakdown_bundle.json`、可选 `write-plan.json`、`script_bundle.json` |
| 飞书范围 | 105 只写 01/02/03；106 只写 04 |
| 目标绑定 | 只认当前使用者的本机私有配置；无绑定只输出本地 |

## 常见错误

- 把账号主页直接送入单视频拆解：先调用 `$collect-tk-account`。
- 把 Photo Mode 当 MP4：先识别内容类型；缺少正式页码契约时停止。
- 文件存在就视为完成：必须运行对应阶段校验器。
- 把 `step2_completed=true` 当作用户确认：只有 `step2_confirmed=true` 才能进入 105 或 106。
- 把拆解确认当作脚本生成确认：`review` 模式必须先展示路线和数量。
- 默认生成九版：默认只生成六版，九版需要明确要求。
- 只在 SKILL.md 写 `gpt-5.6-sol` 就声称已路由：必须核对实际执行单元。
- 把 01/02/03 授权扩大到 04，或反向扩大：两个写入范围分别核对。
- 把 Skill 自带示例当真实飞书目标，或无绑定时回退到作者库：必须停止外部写入，只交付本地文件。

## 示例

用户：“自动跑完这个 TikTok 视频，先不要写飞书。”

执行：固定 `workflow_mode=auto-local` → 104 提取、拆解、校验和盖章 → 105 生成本地 `write-plan.json` → 106 使用 `gpt-5.6-sol` 生成并严格校验默认六版 `script_bundle.json` → 报告本地产物并停止，不连接飞书。
