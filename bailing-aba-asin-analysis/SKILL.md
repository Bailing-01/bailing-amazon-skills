---
name: bailing-aba-asin-analysis
description: ABA品牌分析ASIN视图搜索词份额报告深度诊断：大盘趋势对比、词根拆解、四象限分群与广告结构建议。当用户提到ABA分析、搜索词份额诊断、ASIN搜索词报告、ABA关键词分析、搜索词展示量份额、ASIN impression share时触发。即使只说"分析这份ABA报表"也应触发；单条关键词查询不触发。
---

## 适用与不适用

输入4周ABA品牌分析ASIN视图搜索词展示量份额报告Excel，输出深度诊断HTML报告。适用：定期ABA报告诊断、关键词表现盘点、广告结构优化建议。

不适用：单条关键词查询（直接用ABA查询工具）；非ABA格式报表（需先转为标准格式）；仅需原始数据导出不需分析。

## 输入参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| file_path | string | 无（必填） | ABA搜索词份额报告Excel文件路径 |
| asin | string | 无 | 目标ASIN（用于报告标题，选填） |
| brand | string | 无 | 品牌名（用于品牌词识别，选填，不填则自动检测） |

## 执行编排

L1{S1} → L2{S2-S4} → L3{S5}

S1是数据导入校验；S2-S4是确定性加工链（由run_pipeline.py一次执行）；S5是报告生成（handoff linkfox-report-generator）。

### 流水线

| 步骤 | 做什么 | 调用 | 依赖 | 用途 | 详情 |
|------|--------|------|------|------|------|
| S1 导入校验 | 读取Excel确认字段结构与周次 | agent 判断 | 无 | 传file_path给S2 | `references/steps/S1.md` |
| S2-S4 数据加工 | 大盘趋势+关键词Gap+词根拆解+四象限+广告结构，一次执行 | `scripts/run_pipeline.py` | S1 | 全部数据供S5报告消费 | `references/steps/S2-S4.md` |
| S5 生成报告 | 基于加工数据生成HTML诊断报告 | `linkfox-report-generator` | S2-S4 | 交付给用户 | `references/steps/S5.md` |

## 报告产物

报告章节与数据来源（样式由 linkfox-report-generator 接管）：

- KPI概览：总展现/点击/购买/转化率，来自S2-S4汇总
- 大盘周度趋势：展现/CTR/转化率周度对比折线图，来自S2 weekly_trend
- 逐关键词Gap分析：ASIN vs大盘CTR/转化率差距表，来自S3 keyword_gaps
- 词根拆解：Top词根展现/CTR Gap/Conv Gap柱状图，来自S3 root_analysis
- 四象限分群：Q1-Q4散点图+明细表，来自S4 quadrant_summary
- 广告结构建议：6个广告活动卡片+否定词清单，来自S4 ad_structure
- SWOT+行动项：综合研判，来自S2-S4数据由agent语义加工

元信息：生成时间/数据周期/ASIN/品牌/参数快照。

> ⚠ 生成报告必须先阅读 SKILL `linkfox-report-generator` 并遵循其规范：样式、排版、md/html 导出、元信息块统统由它负责，本 skill 不得复制报告样式或 html 模板。

## 执行自检

- [ ] run_pipeline.py 输出含 weekly_trend 且 len ≥ 2
- [ ] keyword_gaps 每条含 ctr_gap 和 conv_gap
- [ ] quadrant_summary 四个象限均有 count > 0
- [ ] 报告每章节有数据来源标注

## 已知局限

- 词根映射表为预定义+品牌自动检测，非品类无关的通用NLP分词；遇到全新品类需手动扩展ROOT_MAP
- 四象限分类的竞品词/不相关词列表为预定义，可能遗漏未覆盖的竞品品牌
- 数据依赖ABA报告格式（34列标准字段），非标准格式需先转换
- 需要已挂载 `linkfox-report-generator` 生成HTML报告；未挂载时可通过技能广场或 https://skill.linkfox.com/ 安装
