# IO 契约

---

## 1. 路径协议

运行期落盘一律走 `scripts/linkfox_paths.py`（原样复制自 `linkfoxagent-v2/_shared/linkfox_paths.py`，不改）：

| 类型 | 必须调用 |
|------|----------|
| 中间数据 | `resolve_data_path(slug, ts)` |
| 最终 JSON / 报告 | `resolve_report_path(slug, ts, ext)` |
| 媒体 | `resolve_media_path(slug, ts, ext)` |

根目录选择、不可写回退、session 目录和元信息登记全部以权威 helper 的实现及返回值为准；业务脚本不得手工拼 `<cwd>/linkfox/...`，不得硬编码 `/tmp`、`/var/tmp`、`~` 或其他绝对路径。权威 helper 自动回退到 home/TMPDIR 不属于违规。路径规范变化时只改 `_shared`，再重新复制到产物。

## 2. response_io.py（大请求 / 大响应双向暂存）

只有两个子命令。**主脚本约定**：从 `argv[1]` 接 JSON 参数包；结果整体为一个 JSON 值写 stdout；日志/错误走 stderr；非零 exit code 表示失败。LinkFox 官方 skill 主脚本天然遵循；第三方工具补一个 thin wrapper（解析 argv[1] → 调工具 → print JSON）放 `scripts/`。

**run（执行 + 落盘，响应不进上下文）**：

```bash
python scripts/response_io.py run \
    --script <主脚本路径> --out-dir <由 linkfox_paths 派生的 session data 目录> --label S<N>_<verb> [--timeout 300] \
    '<JSON 参数包>'            # 小请求行内；大请求改 --params-file <路径>（二者互斥）
```

- `--out-dir` 仅是 `response_io.py` 的内部参数，不是用户可配置输出目录；必须由 `linkfox_paths.session_root()` 选定的 session 根目录派生出 `data/`，不得从 cwd、环境假设或字符串常量手工拼根目录。
- 参数满足任一 → 用 `--params-file`：大数组（几百个 ASIN/词）/ 长文本 / **直接来自上游落盘文件**（用上游 `read --format json` 投影生成参数文件，别读进上下文再拼字符串）。
- run 把主脚本 stdout 全量落盘，只返回轻量预览（schema + 首条样例 + 文件路径）。
- 预览含 `_error`（exit_code 非 0 / timed_out）时先读 `_error.stderr_snippet` 排错——落盘文件可能为空或不完整，不要拿去做下游决策。

**read（按需投影，永远只取下游消费的字段）**：

```bash
python scripts/response_io.py read <文件> --fields "<field_a>,<field_b>" --format <json|jsonl|csv|table> [--limit N] [--offset M]
# 复杂投影用 --path "<JMESPath>"（需 pip install jmespath）
```

预览只是 schema + 截断样例，不是完整数据；字段级判断必须经 `read`。`read` 不带 `--fields`/`--path` 整读文件视为违规（会把落盘的意义整个抵消）。

## 3. 传输层（stdout → 前端）

最终交付经 stdout 的 `Saved full response:` 行通知 acpx-bridge（其余日志行不受影响）：

**结构化 JSON（推荐）**：文件必须真实存在、绝对路径、文件名匹配 `linkfox-<slug>-<数字>.json`：

```python
if not os.path.isfile(abs_json_path):
    raise RuntimeError(f"output file not found: {abs_json_path}")
print(f"Saved full response: {abs_json_path} ({size_bytes} bytes)")
```

**媒体数组**（png/jpg/jpeg/gif/webp/bmp/svg/mp4/webm/mov/mp3/wav）：先写入内容、逐项校验存在，再输出绝对路径 JSON 数组：

```python
missing = [p for p in abs_media_paths if not os.path.isfile(p)]
if missing:
    raise RuntimeError(f"media file not found: {missing[0]}")
print("Saved full response: " + json.dumps(abs_media_paths, ensure_ascii=False))
```

禁止输出占位符路径（`<YYYY-MM-DD>`、`linkfox-generated-media-*` 之类）；`resolve_media_path()` 只分配路径不写文件。

## 4. 载荷层（JSON 文件内容）

### 4.1 报告 HTML

需要精美报告时由 SKILL.md「报告产物」章节 handoff 给 `linkfox-report-generator`；不要在 JSON 里写 blocks / 自拼 HTML。
