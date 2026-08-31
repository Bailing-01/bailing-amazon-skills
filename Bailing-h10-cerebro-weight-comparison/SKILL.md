---
name: Bailing-h10-cerebro-weight-comparison
description: H10 Cerebro多ASIN关键词权重对比分析：读取多个Cerebro反查表，按可配置公式计算广告/自然/总权重，输出含4个Sheet的格式化Excel和HTML分析报告。当用户提到权重对比、Cerebro权重、ASIN权重分析、广告权重、自然权重、关键词权重差距、权重查询时触发。即使只说"对比这几个ASIN的权重"也应触发；单ASIN反查分析不触发（走productivity skill）。
---

## 适用与不适用

多ASIN关键词权重对比分析工具。输入多个H10 Cerebro反查xlsx文件，端到端输出：格式化Excel（含总权重对比/权重对比/各ASIN Top30/关键词差距分析4个Sheet）+ HTML分析报告。适用于：竞品对标——给定2-5个ASIN的Cerebro数据，量化对比广告权重、自然权重、总权重差距，定位核心关键词竞争差异。

不适用：单ASIN Cerebro四维度分析（走 `productivity` skill）；实时ASIN关键词反查（走 `linkfox-sif-asin-keywords`）。

## 输入参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| files | dict | 无（必填） | ASIN→xlsx路径映射，至少2个 |
| rank_cutoff | int | 40 | 排名截断位，排名≥此值时权重为0；美国站40，部分市场可达60 |
| formula | str | exponential | 权重公式：linear / exponential / power |
| alpha | float | 0.15 | 指数衰减系数，仅formula=exponential时生效 |
| power_exp | float | 1.5 | 幂函数指数，仅formula=power时生效 |

## 流水线

### 执行编排

L1{S1} → L2{S2}

### 流水线

| 步骤 | 做什么（一句话） | 调用 | 依赖 | 用途 | 详情 |
|------|----------------|------|------|------|------|
| S1 计算权重+输出Excel | 读取多个Cerebro xlsx，按公式计算三方权重，输出格式化Excel(4 Sheet)+JSON数据 | `scripts/run_pipeline.py` | 无 | 供S2报告消费 | `references/steps/S1.md` |
| S2 生成HTML报告 | 读取S1的JSON，写HTML片段，调inject_report生成最终报告 | `linkfox-report-generator` | S1 | 交付用户 | `references/steps/S2.md` |

## 报告产物

报告章节与数据来源（样式由 linkfox-report-generator 接管，本 skill 只备数据）：

- KPI概览：三ASIN总权重、总搜索量、共有关键词数、最大权重差距（来自S1 JSON summaries）
- 整体权重对比：柱状图+对比卡片，三ASIN广告/自然/总权重（来自S1 JSON summaries）
- 关键词覆盖分布：广告排名词数、自然排名词数、共有/独有词数（来自S1 JSON summaries）
- TOP20高权重关键词对比表（来自S1 JSON full_table_top100）
- 核心关键词差距分析：共有词按差距排序TOP15（来自S1 JSON comparison_top50）
- 各ASIN TOP10关键词（来自S1 JSON top30_per_asin）
- 竞争研判与建议：SWOT + 行动建议（agent基于S1数据生成）

元信息：生成时间、参数快照（rank_cutoff/formula/alpha）、数据来源ASIN清单。

> ⚠ 生成报告必须先阅读 SKILL `linkfox-report-generator` 并遵循其规范：样式、排版、md/html 导出、元信息块统统由它负责，本 skill 不得复制报告样式或 html 模板。

## 执行自检

- [ ] Excel文件成功生成且包含4个Sheet（总权重对比/权重对比/各ASIN Top30/关键词差距分析）
- [ ] HTML报告成功生成且包含所有章节
- [ ] 权重计算覆盖每个ASIN的广告排名和自然排名
- [ ] 参数快照（rank_cutoff/formula/alpha）已写入报告头

## 已知局限

- 数据时效性取决于Cerebro导出时间，非实时
- 权重公式为经验模型，α参数需按品类调优
- 不含Cerebro原始表中的"相关性"维度（Cerebro单ASIN导出无此字段，如需四维度分析走 `productivity` skill）
- 仅支持H10 Cerebro导出格式（Table sheet，23列）；不兼容其他工具导出
