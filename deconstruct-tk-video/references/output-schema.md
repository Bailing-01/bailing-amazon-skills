# `breakdown_bundle.json` 接口规范

## 目录

1. 顶层契约
2. 单条视频对象
3. 时间轴与证据
4. 拆解、元素、评分与聚类
5. 约束

## 顶层契约

```json
{
  "pipeline_id": "tk-content-pipeline/v1",
  "artifact_type": "breakdown_bundle",
  "schema_version": 1,
  "generated_at": "2026-08-14T00:00:00Z",
  "source_manifest": null,
  "batch_confirmation": {
    "mode": "single",
    "step1_confirmed": true,
    "confirmed_at": "2026-08-14T00:00:00Z",
    "step2_completed": true,
    "step2_confirmed": false
  },
  "videos": [],
  "skipped_videos": []
}
```

批量输入时 `source_manifest` 写入 `account_manifest.json` 的绝对路径，`mode` 写 `batch`。`videos` 只放完成证据验收和拆解的项目；下载、转写或证据验收失败项放入 `skipped_videos`，至少包含规范化 `video` 与明确 `error`。

`step2_completed=true` 只表示十项拆解已经生成。首次交付固定使用 `step2_confirmed=false`；用户审核并明确确认后，由总工作流幂等改为 `true` 并写入 `step2_confirmed_at`。不得根据第一步确认或文件存在推断第二步已确认。

## 单条视频对象

```json
{
  "status": "completed",
  "video": {
    "video_id": "",
    "source_url": "",
    "local_path": "",
    "account": {"platform": "tiktok", "handle": "", "profile_url": ""},
    "published_at": "",
    "duration_seconds": null,
    "metrics": {"plays": null, "likes": null, "comments": null, "shares": null}
  },
  "transcript": {
    "language": "",
    "backend": "faster-whisper",
    "full_original": "",
    "full_chinese": "",
    "segments": [
      {"start": 0, "end": 3, "source": "speech", "source_text": "", "zh": ""}
    ]
  },
  "timeline": [
    {
      "start": 0,
      "end": 3,
      "source_text": "",
      "zh": "",
      "visual": "",
      "visual_text": [],
      "evidence_frame_ids": []
    }
  ],
  "frames": {
    "index_path": "",
    "cap": {},
    "coverage_audit": {
      "machine_status": "",
      "visual_status": "passed",
      "warnings": [],
      "checks": []
    },
    "evidence": [
      {
        "frame_id": "F001",
        "timestamp": 0.5,
        "file": "",
        "reasons": ["opening"],
        "quality_status": "accepted",
        "observations": [],
        "supports": []
      }
    ]
  },
  "video_breakdown": {},
  "elements": [],
  "scores": {},
  "duplicate_cluster": {}
}
```

`video` 和 `timeline` 是四个 Skill 之间的规范字段。消费者可兼容历史别名 `source_video` 与 `step1_extraction.timeline`，但新输出不要依赖别名。

单个本地文件没有 TikTok 视频 ID 时，使用 `LOCAL-{视频SHA256前12位}` 作为稳定 `video_id`，不得留空或使用随机 ID。

## 时间轴与证据

- `full_chinese` 必须是完整中文转写或完整中文翻译，不能用摘要替代。
- 原视频为中文时，分段 `zh` 可写“同原文”，但 `full_chinese` 仍写完整可复制文本。
- `frames.cap` 保留 `frames.json.cap`；`machine_status` 保留机器审计状态；完成逐帧目视验收后才可写 `visual_status: passed`。
- `frames.evidence[].file` 使用绝对路径或相对 `breakdown_bundle.json` 可解析的路径。
- 黑屏、闪白、模糊或转场帧不得为 `accepted` 证据。

## 拆解、元素、评分与聚类

`video_breakdown` 固定包含：

```json
{
  "underlying_logic": "",
  "video_type": {"primary": "", "compound": [], "shell": [], "basis": ""},
  "retention_method": "",
  "hook_0_3s": {
    "original_copy": "",
    "optimized_copy": "",
    "key_changes": "",
    "intended_retention_effect": "",
    "visual": "",
    "subtitle": "",
    "action": "",
    "shot": "",
    "product_visible": false,
    "continuation_3_6s": "",
    "reason": "",
    "evidence_frame_ids": []
  },
  "audience": "",
  "pain": {"surface": "", "deep": ""},
  "result": {"direct": "", "final_feeling": ""},
  "belief_and_action": {"belief_reason": "", "buy_now_reason": ""},
  "element_coordination": "",
  "transferable_logic": ""
}
```

元素格式：

```json
{
  "element_id": "EL-{video_id}-{module}-{start_ms}",
  "start": 0,
  "end": 3,
  "module": "Hook",
  "subtype": "",
  "copy": "",
  "visual": "",
  "shell": {
    "person": "",
    "scene": "",
    "delivery": "",
    "subtitle": "",
    "shot": "",
    "composition": "",
    "material_type": ""
  },
  "candidate_metric": "retention",
  "status": "candidate",
  "attribution_confidence": "low",
  "backend_metric": null,
  "evidence_frame_ids": []
}
```

评分格式：

```json
{
  "scale": "0-5",
  "hook": 0,
  "pain": 0,
  "trust_conversion": 0,
  "transferability": 0,
  "overall": 0,
  "evidence_basis": [],
  "missing_backend_metrics": ["retention_rate", "ctr", "add_to_cart_rate", "conversion_rate"]
}
```

聚类格式：

```json
{
  "cluster_id": "DC-001",
  "master_video_id": "",
  "relationship": "unique",
  "similar_video_ids": [],
  "review_status": "semantic_reviewed",
  "review_note": ""
}
```

## 约束

- 最终文件名固定为 `breakdown_bundle.json`，同时输出对应 Markdown 报告。
- 所有视频共用一次第一步批量确认；不得逐条暂停。
- 不生成九版脚本、完整新脚本或纯口播成品。
- 不调用飞书工具，不写任何飞书/Base 表，不输出飞书行对象。
- 未提供后台指标时保持 `null`；公开数据只能生成候选结论。
- 最终运行 `scripts/validate-breakdown-bundle.py`；失败时先修复再交付。
