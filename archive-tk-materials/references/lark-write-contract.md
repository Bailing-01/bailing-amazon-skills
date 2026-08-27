# 飞书写入契约

## 顺序

始终按 `01 原视频库 → 02 竞品拆解库 → 03 OXY适配元素库` 串行写入。先写或查到 01 的 `record_id`，再构造 02 的 `关联原视频`。

## 真正的幂等 upsert

`lark-cli base +record-upsert` 只有传入 `--record-id` 才更新；它不会按业务键查重。对每张表执行：

1. 读取真实字段结构和 select 选项。
2. 按业务键批量搜索现有记录，建立 `business_key → record_id` 映射。
3. 将写入计划拆成 create 与 update。
4. create 使用 `+record-batch-create`；update 使用 `+record-batch-update`。
5. 每批最多 200 条，同一表批次串行。
6. `01 原视频库` 每条记录写入同一个批次执行时间到 `本批更新时间`；`发布时间`只保存视频自身发布时间。
7. 批次完成后检查 `视频ID`、`拆解ID`、`元素ID`，不得留下业务键为空的记录。

## 只读与特殊字段

- 不写 formula、lookup、系统字段；02 的 `综合评分`、`学习价值` 固定只读。
- `视频预览` 是附件，使用 `+record-upload-attachment`。
- `关联原视频` 是 link，CellValue 为 `[{"id":"<01 record_id>"}]`。
- select 单选传字符串，多选传字符串数组；只允许真实存在的选项。
- 日期使用 `YYYY-MM-DD HH:mm:ss`，number 使用 JSON number。

## 错误恢复

- `1254104`：缩小到不超过 200 条。
- `1254291`：只重试冲突批次并保持串行。
- `1254045`：重新读取字段，不猜名称。
- `1254015`：按真实字段类型重建 CellValue。
- `ignored_fields/READONLY`：移除只读字段，不原样重试。
- `91403`：停止并进入权限恢复，不循环切换身份。
