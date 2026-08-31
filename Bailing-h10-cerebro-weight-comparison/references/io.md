# IO 契约

## 1. 路径协议

运行期落盘走 `scripts/linkfox_paths.py`：

| 类型 | 调用 |
|------|------|
| 中间数据/JSON | `resolve_data_path(slug, ts)` |
| 报告 HTML | `resolve_report_path(slug, ts, ext)` |

根目录选择、session 目录和元信息登记以 helper 返回值为准。

## 2. 脚本调用

```bash
python scripts/run_pipeline.py '<JSON 参数包>'
```

参数包示例：
```json
{"files": {"B0CQYTNNW7": "/path/a.xlsx", "B0D9HMJ252": "/path/b.xlsx"}, "rank_cutoff": 40, "formula": "exponential", "alpha": 0.15}
```

脚本 stdout 输出 `Saved full response: <path> (<bytes>)` 格式，bridge 自动识别。

## 3. 输出 JSON 结构

```json
{
  "asins": ["B0CQYTNNW7", "B0D9HMJ252"],
  "params": {"rank_cutoff": 40, "formula": "exponential", "alpha": 0.15, "power_exp": 1.5},
  "formula_desc": "W = SV * 39 * e^(-0.15 * (Rank-1))",
  "summaries": {"ASIN": {"total_keywords": N, "total_weight": N, ...}},
  "top30_per_asin": {"ASIN": [{keyword, search_volume, ad_weight, ...}]},
  "common_keywords_count": N,
  "unique_keywords_count": {"ASIN": N},
  "comparison_top50": [{keyword, ASIN_total_weight, weight_gap, ...}],
  "full_table_top100": [{keyword, ASIN_sv, ASIN_sp_rank, ASIN_total_weight, ...}]
}
```

## 4. 报告 HTML

需要报告时 handoff 给 `linkfox-report-generator`；不在 JSON 里自拼 HTML。
