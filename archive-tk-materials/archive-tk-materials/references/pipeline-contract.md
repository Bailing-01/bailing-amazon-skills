# TK 内容管线交接契约 v1

所有交接 JSON 顶层必须包含：

```json
{"pipeline_id":"tk-content-pipeline/v1","artifact_type":"account_manifest|breakdown_bundle"}
```

## account_manifest

顶层使用 `account`、`selection`、`videos`。每条 `videos[]` 至少包含：

```json
{
  "video_id": "",
  "source_url": "",
  "local_path": "",
  "published_at": "",
  "metrics": {"plays": null, "likes": null, "comments": null, "shares": null},
  "rank": null,
  "account": "",
  "acquisition": {"status": "ready|failed", "error": null}
}
```

兼容旧输入的 `url`、`plays`、`likes`、`comments`、`shares` 扁平字段，但输出必须规范化。

## breakdown_bundle

顶层使用 `videos`。每条至少包含 `video`、`transcript`、`timeline`、`video_breakdown`、`elements`、`scores` 和 `duplicate_cluster`。为兼容早期产物，也可读取 `source_video.video_id`、`step1_extraction.timeline` 与可选 `step2_base_row`，但新输出必须提供 canonical 的 `video` 与顶层 `timeline`。完整中文内容从 `transcript.full_chinese` 读取；不得用摘要替代。缺失私有指标用 JSON `null`。素材沉淀 Skill 负责把这一领域模型确定性映射为飞书字段，视频拆解 Skill 不需要输出飞书行对象。

## 业务键

- 原视频：`video_id`
- 拆解：`BD-{video_id}`
- 元素：`{video_id}|{start}-{end}|{module}|{content_fingerprint}`

禁止用数组序号、标题或模型生成的描述充当业务键。
