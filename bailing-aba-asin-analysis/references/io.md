# IO 契约

## 1. 路径协议

运行期落盘走 `scripts/linkfox_paths.py`（原样复制自 `_shared/linkfox_paths.py`）：

| 类型 | 调用 |
|------|------|
| 中间数据 | `resolve_data_path(slug, ts)` |
| 最终报告 | `resolve_report_path(slug, ts, ext)` |
| 媒体 | `resolve_media_path(slug, ts, ext)` |

根目录选择与回退以权威 helper 实现为准；禁止硬编码 `/tmp` 或手工拼 root。

## 2. response_io.py（大响应暂存）

**run（执行+落盘）**：
```bash
python scripts/response_io.py run \
    --script scripts/run_pipeline.py --out-dir <session data dir> --label S2_S4_pipeline \
    '{"file_path":"...","asin":"...","brand":"..."}'
```
- 大参数（多文件路径等）改用 `--params-file <路径>`
- run 把 stdout 全量落盘，返回轻量预览

**read（按需投影）**：
```bash
python scripts/response_io.py read <文件> --fields "weekly_trend,keyword_gaps" --format jsonl --limit 5
```

## 3. 传输层

最终报告经 `linkfox-report-generator` 的 inject_report.py 落盘，路径由该 skill 返回。
agent 在对话中输出报告路径即可。

## 4. 载荷

run_pipeline.py 输出 JSON 结构：
- `weekly_trend`: 数组，每条含 date/market_*/asin_*/ctr_gap/conv_gap
- `keyword_gaps`: 数组，每条含 query/asin_impressions/asin_ctr/market_ctr/ctr_gap/asin_conv/market_conv/conv_gap/quadrant/quadrant_label
- `root_analysis`: 数组，每条含 root/query_count/asin_impressions/asin_ctr/market_ctr/ctr_gap/asin_conv/market_conv/conv_gap
- `quadrant_summary`: 对象，Q1-Q4 各含 count/impressions/clicks/purchases/ctr/conv
- `ad_structure`: 数组，6个广告活动建议
- `negation`: 对象，含 exact(精准否定) 和 phrase_candidates(词组否定候选)
- `q1_keywords`/`q2_keywords`/`q3_keywords`/`q4_keywords`: 各象限Top关键词明细
