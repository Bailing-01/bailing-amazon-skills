---
name: deconstruct-tk-video
description: 对本地 MP4/MOV/WebM/M4V、单条公开 TikTok 链接或 collect-tk-account 生成的 account_manifest.json 执行跨平台环境检查、下载、FFprobe、音频转写、语义抽帧、覆盖验收、第一步整批内容提取确认、第二步十项证据化拆解、重复素材聚类、候选评分与可迁移元素沉淀，并输出 tk-content-pipeline/v1 的 breakdown_bundle.json 和 Markdown。用于 TK/TikTok 视频转写、翻译、竞品拆解、Hook 对照、素材分析或为下游脚本生成准备拆解数据；不生成九版脚本，不写入飞书。
---

# 最新104｜TK视频拆解

<!-- workflow:tk-content-pipeline/v1 local-input tiktok-input account-manifest semantic-frames coverage-audit step1-batch-confirm step2-ten-part hook-comparison duplicate-clustering candidate-elements breakdown-bundle no-script-generation no-lark-write -->

严格执行“两步整批确认制”：先完成全部入选视频的第一步内容提取，统一请求一次确认并暂停；只有用户明确回复“OK”或同意继续，才执行第二步拆解。批量任务不得逐条暂停。

当由 `$tianguo-tk-video-workflow-3-0` 以 `workflow_mode=auto-local` 或 `workflow_mode=auto-all` 调用，且用户在当前请求明确授权自动跑完时，将该一次性授权视为两步整批确认，不重复等待“OK”。仍必须完成环境检查、证据覆盖验收和本 Skill 的 JSON 校验；遇到缺失、失败或不确定证据时立即停在当前阶段。

## 边界

- 接受单个本地视频、单条公开 TikTok 视频 URL，或 `account_manifest.json`。
- 拒绝把 TikTok 账号主页当作单视频输入；账号拉取交给 `collect-tk-account`。
- 只输出内容提取、十项拆解、候选元素、评分和重复聚类。
- 不生成九版脚本、完整新脚本或纯口播成品；相关请求交给 `generate-tk-scripts`。
- 不调用飞书工具，不写入飞书/Base；入库交给 `archive-tk-materials`。

开始前完整读取 [references/runtime.md](references/runtime.md)、[references/breakdown-framework.md](references/breakdown-framework.md) 和 [references/output-schema.md](references/output-schema.md)。

## 1. 确定输入与任务目录

为每次任务确定独立工作目录，保留中间缓存和最终产物。

- 本地文件：扩展名只接受 `.mp4`、`.mov`、`.webm`、`.m4v`。
- 单条链接：域名必须是 TikTok，且链接指向单条公开视频。
- 账号清单：要求顶层 `pipeline_id: tk-content-pipeline/v1`、`artifact_type: account_manifest` 和 `videos[]`。规范字段为 `video_id`、`source_url`、`local_path`、`published_at`、`metrics`、`rank`、`account`、`acquisition`；兼容旧别名 `id`、`url`、`video` 及扁平互动指标。

账号清单中的下载或处理失败项不得伪造拆解结果；放入最终 `skipped_videos` 并保留错误原因。
单个本地文件没有 TikTok ID 时，最终使用 `LOCAL-{视频SHA256前12位}` 作为稳定 `video_id`。

## 2. 检查运行环境

先确定本 Skill 的绝对目录，再运行：

- Windows：`powershell -ExecutionPolicy Bypass -File "<Skill目录>\scripts\check-environment.ps1"`
- macOS：`bash "<Skill目录>/scripts/check-environment.sh"`

本地文件查看 `local_video_ready`；单条 URL 或清单内需要补下载时查看 `tiktok_link_ready`。未就绪时可运行平台 `setup-windows.ps1` 或 `setup-macos.sh`，随后必须重新检查。仍缺 FFmpeg 或转写后端时停止并报告；不得用整片密集抽帧代替语音转写。

## 3. 准备视频、转写与语义帧

### 单条输入

- Windows：`powershell -ExecutionPolicy Bypass -File "<Skill目录>\scripts\prepare-video.ps1" -Source "<本地视频或TikTok链接>" -WorkDir "<任务目录>" -Model small`
- macOS：`bash "<Skill目录>/scripts/prepare-video.sh" "<本地视频或TikTok链接>" "<任务目录>" small`

Windows 公开链接固定执行以下失败恢复链：

| 触发条件 | 一线动作 | 仍失败时 |
|---|---|---|
| `gallery-dl` 下载成功 | 读取同一 `video_id` 的视频并进入原分析缓存 | 不调用备用通道 |
| `gallery-dl` 返回非零，包括 `403 Forbidden`、JavaScript challenge 或 `No results` | 自动调用一次无 Cookie 公开备用通道，只传递当前公开 URL；核对返回 ID、HTTPS TikTok CDN、文件大小和 FFprobe 音视频流 | 报告主下载退出码与备用失败原因，保留任务目录并请求本地视频 |

备用文件先写入 `.partial.mp4`；所有校验通过后才移动为正式 MP4。不得读取浏览器 Cookie、自动登录、把非 TikTok CDN 当成视频源，或在双路失败后继续转写。macOS 当前不调用该备用通道；`gallery-dl` 失败时安全停止并请求本地视频。

### 账号清单

使用专用 Python 环境运行跨平台批处理；它一次加载 Whisper，顺序转写缺失视频：

- Windows：`%LOCALAPPDATA%\tianguo-video\python-env\Scripts\python.exe "<Skill目录>\scripts\prepare-account-manifest.py" "<account_manifest.json>" --work-dir "<任务目录>" --model small`
- macOS：`~/Library/Caches/tianguo-video/python-env/bin/python "<Skill目录>/scripts/prepare-account-manifest.py" "<account_manifest.json>" --work-dir "<任务目录>" --model small`

批处理输出 `prepared_media_manifest.json`。若处理两条以上视频，再运行：

`<专用Python> "<Skill目录>/scripts/cluster-transcripts.py" "<任务目录>/prepared_media_manifest.json"`

聚类脚本只给出候选关系；第二步必须结合画面、产品和文案语义复核。

## 4. 完成证据覆盖验收

固定顺序为 FFprobe、16 kHz 单声道音频、带时间戳转写、语义抽帧、目视验收。读取每条视频的 `metadata.json`、`transcript.json` 和完整 `frames.json`，并逐张查看已抽取关键帧。

必须核对：

1. 前 3 秒最大间隔约 0.5 秒，最后 3 秒最大间隔约 1 秒；
2. 场景变化、口播主题变化、产品首次出现、证明、价格/折扣/赠品和 CTA；
3. 顶部标题、中部产品或证明、底部字幕和购买区域；
4. 口播中的“你看”、前后对比、数字、折扣和购买指令是否有画面支撑；
5. 黑屏、闪白、模糊或转场叠帧不得作为证据。

读取 `frames.json.cap`、`coverage_audit` 和每帧 `quality_status`。存在覆盖缺口时只在缺口附近补帧：每个片段最多 8 张，最多 3 个片段。不得整片按 1–2 秒重复抽帧。完成所有 `required_visual_checks` 后，才在输出对象中写 `frames.coverage_audit.visual_status: passed`；未通过时禁止进入第二步。

## 5. 第一步：整批内容提取

对全部可用视频一次完成以下三个板块，并写入 `<任务目录>/step1_extraction.md`。

### 一、视频基础信息

- 视频 ID、来源、时长、分辨率、编码和音轨；
- 原始语言、内容形式；
- 口播、字幕和画面是否清晰，以及转写后端。

### 二、文案与画面提取

按文案、动作或画面意义变化分段：

| 时间段 | 原文 | 中文翻译 | 画面内容 | 证据帧 |
|---|---|---|---|---|
| 00:00–00:03 | 原语言文案 | 自然中文 | 实际人物、产品、场景和动作 | F001 |

- 保留原文并生成自然中文；原视频为中文时，分段可写“同原文”。
- 同时沉淀完整 `transcript.full_original` 和完整可复制的 `transcript.full_chinese`，不得用摘要代替。
- 分别标注口播、画面字幕和其他画面文字；冲突时分别保留。
- 画面只写实际看到的内容，不在第一步做营销分析。
- 无法确认时标注 `[听不清]` 或 `[字幕无法确认]`，不得猜测。

### 三、整批确认

列出完成、跳过、待补证据的视频 ID，然后输出并暂停：

> 第一步整批视频内容提取已完成。回复“OK”进入第二步视频拆解；如不满意，请指出视频 ID、时间段和需要修改的内容。

用户未确认前不得输出十项拆解、候选评分或迁移结论。

## 6. 第二步：十项证据化拆解

用户确认第一步后，按 [references/breakdown-framework.md](references/breakdown-framework.md) 对每条视频输出固定十项：底层逻辑、视频类型、留人方式、Hook、目标人群、痛点、结果、信任与行动、元素协同、可迁移逻辑。

强制要求：

- 每个关键判断引用时间段或证据帧；证据不足时明确标注。
- `hook_0_3s` 同时保留原 Hook 和一个优化 Hook 候选，列明关键变化与预期留人效果；不得用优化版覆盖原版。
- 严格区分“相信产品有效”和“愿意现在购买”。
- 优化 Hook 只是局部候选，不得扩写为完整新脚本。

## 7. 元素、聚类与评分

同一轮拆解直接生成 `elements`，不要先写长报告再重复分析。按 `Hook / 痛点 / 转折 / 产品切入 / 产品机制 / 卖点 / 信任证明 / Offer / CTA` 切分，并保留证据帧。

复核重复候选：完全重复只深拆母版；同 Hook 只复用 Hook；同脚本换产品时只复用结构，重新核对产品机制、证明与转化理由。每条视频保留母版和变体 ID。

按 0–5 分输出 `hook`、`pain`、`trust_conversion`、`transferability` 和加权 `overall`。公开播放或互动只能作为候选信号；留存率、CTR、加购率、转化率未由用户提供时保持 `null`，不得填 0 或写成已验证。

## 8. 保存并验证交付物

同时输出：

- `<任务目录>/breakdown_bundle.json`：严格服从 `tk-content-pipeline/v1` 和 [references/output-schema.md](references/output-schema.md)；
- `<任务目录>/breakdown_report.md`：包含第一步内容、第二步十项拆解、Hook 对照、聚类、评分和候选元素摘要。

首次交付拆解包时必须写 `batch_confirmation.step2_completed=true` 与 `batch_confirmation.step2_confirmed=false`。完成拆解不等于用户已审核第二步，不得预先写成 `true`。当本 Skill 由总工作流调用时，第二步确认与盖章由 `$tianguo-tk-video-workflow-3-0` 管理。

`breakdown_bundle.videos[]` 的规范字段使用 `video` 和 `timeline`；不要依赖历史别名。最终执行：

`<专用Python> "<Skill目录>/scripts/validate-breakdown-bundle.py" "<任务目录>/breakdown_bundle.json"`

验证失败时修复后重跑。交付时列出完成和跳过视频、输出路径、覆盖审计状态及缺失的后台指标。不要追加脚本生成或飞书写入。
