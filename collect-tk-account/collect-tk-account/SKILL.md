---
name: collect-tk-account
description: 采集公开 TikTok 账号主页的视频素材，默认筛选执行日前 30 天内按播放量排名的 Top 10，完成纯 MP4 过滤、视频 ID 去重、排名缓存、原视频与公开元数据下载，并输出 tk-content-pipeline/v1 的 account_manifest.json。用于用户提供 TikTok/TK 账号主页并要求拉账号、采集竞品视频、下载近期爆款或为后续视频拆解准备批量输入时；不用于转写、抽帧、内容分析、脚本生成或飞书入库。
---

# TK 账号采集

只完成账号级公开素材采集，并以 `account_manifest.json` 作为下游唯一交接物。不得转写、抽帧、分析内容、生成脚本或写入飞书。

## 执行流程

1. 确认输入是公开 TikTok 账号主页，格式如 `https://www.tiktok.com/@account`；单条视频、本地文件和私密主页不走本 Skill。
2. 确认任务工作区。默认使用用户指定目录；未指定时，在当前工作目录创建清晰命名的任务目录，不写入 Skill 目录。
3. 在 Windows 运行：

   ```powershell
   powershell -ExecutionPolicy Bypass -File "<Skill目录>\scripts\collect-tiktok-account.ps1" -ProfileUrl "<主页链接>" -WorkDir "<任务工作区>" -Days 30 -Top 10
   ```

4. 用户明确要求刷新公开数据时追加 `-Refresh`；否则复用 20 小时内的主页缓存。用户改变 `Days` 或 `Top` 时传入对应参数。
5. 读取脚本输出及 `<任务工作区>/account_manifest.json`，核对账号、筛选窗口、排序口径、选中数量和每条下载状态。
6. 运行交付验证：

   ```powershell
   powershell -ExecutionPolicy Bypass -File "<Skill目录>\scripts\validate-account-manifest.ps1" -ManifestPath "<任务工作区>\account_manifest.json"
   ```

7. 只有验证通过才把清单交给视频拆解 Skill。报告清单绝对路径、成功/缓存/失败数量和失败原因；不要声称失败视频已下载。

## 固定采集规则

- 先过滤 `type=video` 且 `extension=mp4`，再按 `video_id` 去重；轮播、图片、封面、字幕和音频资源不得进入榜单。
- 仅保留执行时刻向前 `Days` 天内发布的视频，默认 30 天；按公开播放量降序排列，播放量相同则按发布时间降序、视频 ID 升序稳定排序。
- 默认 Top 10；不足 10 条时全部保留。排名从 1 连续编号。
- 主页全部唯一 MP4 元数据缓存到 `profile-cache`，默认有效 20 小时；缓存命中时只重新执行本地窗口过滤和排序。
- 原视频保存到 `videos/<video_id>.mp4`。已有且至少 1024 字节的文件记为 `cached`；新下载记为 `downloaded`；失败记为 `failed` 并保留错误，不中断其他视频。
- 遇到登录、地区、验证码、私密或风控限制时如实报告；不得伪造账号数据、指标、路径或下载成功状态。
- 公开指标只能按采集时快照保存。真实 `0` 保留为 `0`；缺失或不可解析的 `plays`、`likes`、`comments`、`shares` 写为 `null`，不得伪装成 0，也不得推断点击率、转化率或内容表现原因。排名时仅把 `plays=null` 临时视为最低值。

## 交接契约

输出必须严格符合 [references/account-manifest.schema.json](references/account-manifest.schema.json)，不得增加未定义字段：

- 顶层固定为 `pipeline_id`、`artifact_type`、`generated_at`、`account`、`selection`、`videos`；其中 `pipeline_id` 为 `tk-content-pipeline/v1`，`artifact_type` 为 `account_manifest`。
- `account` 固定包含 `platform`、`handle`、`profile_url`；`platform` 为 `tiktok`。
- `selection` 固定包含 `days`、`top`、`metric`、`cache_status`；`metric` 为 `plays`，缓存状态使用 `hit`、`miss`、`refresh` 或 `scan_failed`。
- 每条 `videos[]` 固定包含 `video_id`、`source_url`、`local_path`、`published_at`、`metrics`、`rank`、`account` 和 `acquisition`。
- `metrics` 固定包含 `plays`、`likes`、`comments`、`shares`，每项只允许非负整数或 `null`；`acquisition` 固定包含 `status`、`error`。
- `acquisition.status` 只允许 `downloaded`、`cached`、`failed`；失败时 `local_path` 必须为 `null`，且 `acquisition.error` 必须有值。
- 下游只能消费 `acquisition.status` 为 `downloaded` 或 `cached` 且本地文件存在的条目。主页扫描失败时清单使用 `selection.cache_status=scan_failed`、`videos=[]`，并以非零退出码及终端错误说明原因。

## 边界

本 Skill 到 `account_manifest.json` 即停止。即使用户同时要求拆解、素材沉淀或脚本生成，也只完成并交接本阶段，再由相应 Skill 继续处理。
