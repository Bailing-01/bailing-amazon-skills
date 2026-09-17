---
name: COSMO 市场分析
description: >-
  当用户要对 Cerebro/COSMO 属性表做市场分析、人群与属性流量汇总、头部长尾共性、HTML 市场报告时使用。依赖已有 keyword-cosmo-attribute CSV；不负责 Cerebro 反查打标本身（走 bailing-cerebro-keyword-analysis）。
---

# COSMO 市场分析

## 适用与不适用

**适用**：已有 `keyword-cosmo-attribute-*-v41.csv`（含中文 COSMO 属性列），需要市场流量汇总、头部长尾共性、数学洞察、HTML + Excel 交付。

**不适用**：
- 原始 Cerebro 反查打标 → 走 `bailing-cerebro-keyword-analysis`
- 仅查单个关键词搜索量 / 不做属性汇总

## 输入

| 参数 | 说明 |
|------|------|
| input CSV | COSMO 属性表（序号/关键词/搜索量/… + 目标人群等属性列） |
| title / category | 报告标题与品类名（可选） |
| output-dir | 产物目录 |

属性列支持：`目标人群, 修饰/价值, 购买场所, 季节/节日, 场景/活动, 产地/文化, 通用/品类, 成分/材质, 痛点/需求, 产品形态, 使用部位, 功效, 风格属性`。多标签 `a|b` **搜索量等分**。

## 执行步骤

1. **确认输入**：用户提供或上游产出的 `keyword-cosmo-attribute-*-v41.csv`；空搜索量当 0，`-` 为未标。
2. **跑脚本**（优先 `/workspace/venv-ads/bin/python`）：

```bash
/workspace/venv-ads/bin/python \
  /home/box/agent-data/amazon-skills/bailing-amazon-skills/skills/productivity/bailing-cosmo-market-analysis/scripts/build_cosmo_market_report.py \
  --input <cosmo-v41.csv> \
  --output-dir <dir> \
  --title "智能马桶盖 COSMO 市场分析" \
  --category "智能马桶盖"
```

3. **交付产物**（均在 `--output-dir`）：
   - `cosmo-market-report-{slug}.html` — 自包含可视化报告
   - `cosmo-market-workbook-{slug}.xlsx` — 说明 / 词明细(AutoFilter) / 维度汇总 / 副表 / 洞察 / 交叉 / 蓝海
   - `cosmo-keyword-detail-{slug}.csv`、`cosmo-dim-summary.csv`、`cosmo-insights.txt`
4. **口头总结**：从 `洞察` sheet 或控制台 Top insights 中挑 **5 条最硬结论**（必须带真实数字，禁止编造）。

口径与章节细节见 `references/market-report.md`。

## 分析模块清单

1. 总览 KPI（词数、总搜索量、人群覆盖率、各维填充率）
2. 各 COSMO 维度流量副表（词数/搜索量/中位/占比/Top词）
3. 头部（前 4% 词）vs 长尾（后 80% 词量）属性共性
4. 数学洞察：P50/P90、头部集中度、共现交叉、蓝海×搜索量、低填充率警告
5. HTML 离线可视化（inline SVG / 表，无 CDN）
6. Excel 可筛选工作簿

## 成功自检

- [ ] HTML 与 xlsx 均生成且非空
- [ ] 洞察数字可在 CSV 复现
- [ ] 填充率 <5% 的维有警告文案
- [ ] 向用户口头给出 5 条硬结论
