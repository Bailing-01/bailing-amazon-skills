# ASIN Listing 风险监控骨架

本目录是本地、无网络的日常记录与检查骨架；当前 CSV **不含** Amazon 实时指标与真实 ASIN 行。缺数据必须写 `无数据`，不要猜排名、花费、曝光、点击或评论数。

Companion skill：`skills/asin-listing-risk-monitor`（仓库内）或工作流名 `asin-listing-risk-monitor`。

## 克隆与开始
```bash
git clone https://github.com/Bailing-01/bailing-amazon-skills.git
cd bailing-amazon-skills/asin-risk-monitor
```
1. 在 `config/asins.csv` 填入店铺、站点、ASIN/SKU 和关键词（关键词用 `|` 分隔）。
2. 每天从 Seller Central、Helium 或紫鸟手工粘贴/抄录到 `daily/` CSV，并填写 `source`。SP-API 就绪前不做自动抓取。
3. 用 `templates/daily_report.md` 输出短报告：结论、动作项、无数据清单。
4. 打开 `index.html`，选择对应 CSV 文件即可在浏览器本地查看；文件不会上传。

默认跨站点集合：US / CA / MX / UK / DE / FR（`daily/cross_site.csv` 用 `us_change`、`ca_status`、`mx_status`、`eu_status` 汇总；EU 可在 note 标注 UK/DE/FR 细分）。

## 脚本
```bash
python3 scripts/scan_forbidden.py listing.txt
cat listing.txt | python3 scripts/scan_forbidden.py -
python3 scripts/scan_forbidden.py listing.txt --lexicon lexicon/forbidden_terms.csv
python3 scripts/diff_neg_reviews.py daily/neg_reviews_old.csv daily/neg_reviews_new.csv --asin B000000000
```

## 规则与上下文
- 不发明任何 Amazon 实时数据；没有来源或无法核实时填 `无数据`。
- 违禁词命中只是人工复核线索，不等于最终政策判定；结合类目、语境、站点规则处理。
- 本公开骨架不含 `out/` 扫描产物与真实 ASIN 行；请在本地私有目录保存真实扫描。
- 初始词库覆盖成人、药品/功效、农药/杀虫剂式表达，以及美妆/化妆品和卫浴坐便器常见高风险宣称；请按实际类目补充。

## 待提供信息
开始填报至少需要：**1 个 ASIN + 店铺 + marketplace 列表**，最好同时提供 SKU、父 ASIN、核心关键词和可核验的数据来源。
