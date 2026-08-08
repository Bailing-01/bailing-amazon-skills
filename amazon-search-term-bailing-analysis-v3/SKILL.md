---
name: amazon-search-term-bailing-analysis-v3
description: 亚马逊SP广告搜索词展示量份额报告全流程分析V3：广告结构+搜索词帕累托+多周期对比分析。支持双周期份额变化、排名升降、新增/消失关键词、ACOS趋势对比。V3新增C2长尾深度分析（点击次数分布+词根关联分析），并将周期对比作为核心功能。当用户提到搜索词份额分析、展示量份额报告、多周期对比、份额变化、排名趋势、搜索词Bailing分析时触发。即使只说"对比分析这两份广告报表"也应触发；一次性单点查询不触发。
---

## 适用与不适用（V3）

对亚马逊SP广告「搜索词展示量份额报告」Excel做端到端分析，产出广告结构+搜索词帕累托合并HTML报告。V3新增C2长尾深度分析与周期对比核心功能。适用于：定期广告复盘、搜索词份额审计、关键词优先级梳理、投放层级效率诊断。

不适用：单ASIN流量词反查（用 linkfox-sif-asin-keywords）；关键词搜索量查询（用 linkfox-aba-intelligent-query）；纯Listing优化（用 linkfox-listing-master-test）。

## 输入参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| excel_path | string | 无（必填） | 当前周期Excel文件路径 |
| excel_prev_path | string | 无（可选） | 上一周期Excel文件路径（传入则启用双周期对比） |
| period_label | string | 当前周期 | 当前周期标签 |
| prev_period_label | string | 上周期 | 上一周期标签 |
| cvr_good | float | 0.15 | CVR优秀阈值（≥此值=优秀） |
| cvr_normal | float | 0.12 | CVR正常阈值（≥此值=正常，<cvr_low=偏低） |
| cvr_low | float | 0.08 | CVR偏低阈值（<此值=偏低） |
| share_voice | float | 0.01 | 有声量份额阈值（≥此值=有声量） |
| share_good | float | 0.05 | 份额好阈值（≥此值=好） |
| share_excellent | float | 0.10 | 份额非常好阈值（≥此值=非常好） |
| top_pct | float | 0.04 | 帕累托头部占比（默认前4%） |
| c2_click_threshold | int | 6 | C2关键词判定"充分非转化"的最小点击数（≥此值视为数据充分） |

## 执行编排

L1{S1} → L2{S2} → L3{S3} → L4{S4} → L5{S5}

S1→S2→S3 为确定性链（读取Excel→结构提取→搜索词聚合），打包进 `scripts/run_analysis.py` 一次执行；S4 为报告生成（调用 linkfox-report-generator）；S5 为交付。

## 流水线

| 步骤 | 做什么（一句话） | 调用 | 依赖 | 用途 | 详情 |
|------|----------------|------|------|------|------|
| S1 读取Excel | 读取原始报告sheet，按列映射提取全部行 | `scripts/run_analysis.py` | 无 | 供S2/S3消费 | `references/steps/S1.md` |
| S2 结构提取 | 提取广告组合→活动→投放层级，按产品拆分 | `scripts/run_analysis.py` | S1 | 进入报告模块一 | `references/steps/S2.md` |
| S3 搜索词聚合 | 按产品+搜索词聚合，帕累托+份额分级+长尾分类 | `scripts/run_analysis.py` | S1 | 进入报告模块二 | `references/steps/S3.md` |
| S3.5 C2 深度分析 | C2长尾深度分析：点击次数分布+词根关联分析 | `scripts/run_analysis.py` | S3 | 进入报告模块二 | `references/steps/S3.md` |
| S4 生成报告 | 将S2+S3+S3.5数据写成HTML片段，注入模板落盘 | `linkfox-report-generator` | S2,S3,S3.5 | 最终交付物 | `references/steps/S4.md` |
| S5 交付 | 输出报告路径 | agent | S4 | 用户获取报告 | `references/steps/S5.md` |
| S6 周期对比 | 双周期对比分析（份额/排名/CPC/ACOS变化+新增/消失词） | `scripts/run_analysis.py --excel-prev` | S1-S3 | 进入报告模块三 | `references/steps/S6.md` |

## 报告产物

报告章节与数据来源（样式由 linkfox-report-generator 接管，本 skill 只备数据）：

- **模块一：广告结构分析**（一~六）
  - 报表结构总览：组合数/活动数/投放数/搜索词数/花费/订单/CVR（来自S2）
  - 按产品拆分广告活动层对比：CVR/CPA/花费占比（来自S2）
  - 投放层Top N详情（来自S2）
  - 落实到活动/投放层级的建议（agent基于S2数据生成）
- **模块二：关键词分析**（七~十二，中间有模块分隔标题）
  - 帕累托分析：前20%/4%核心词订单贡献占比（来自S3）
  - 头部4%核心词详表：订单/CVR/份额/排名/CPA/市场量+份额&CVR评价（来自S3）
  - 份额分级：≥10%非常好/≥5%好/≥1%有声量/<1%弱（来自S3）
  - 长尾80%分类归组：7类（来自S3）
  - C2 深度分析：点击次数分布（1次/2-5次/6+次）+ 词根关联分析（共享词根 vs 独特词根）+ C2 细分行动矩阵（来自S3.5）
  - 搜索词维度行动建议（agent基于S3数据生成）
- **模块三：周期对比分析**（十三~十五，中间有模块分隔标题）
  - 广告组合环比总览：花费/订单/CVR/ACOS/CPC 的 before-after 对比+变化方向标注（来自S6）
  - 头部核心词环比对比：份额/排名/订单的 before-after 对比+显著变化标注（来自S6）
  - ACOS 变化 & 新增/消失关键词：ACOS恶化Top5/改善Top5/新增关键词Top5（来自S6）
  - 环比行动建议（agent基于S6数据生成）

元信息：生成时间（ISO 8601）/ 参数快照 / 数据来源清单 / 局限性说明。

> ⚠ 生成报告必须先阅读 SKILL `linkfox-report-generator` 并遵循其规范：样式、排版、md/html 导出、元信息块统统由它负责，本 skill 不得复制报告样式或 html 模板。

## 执行自检

- [ ] S1读取Excel成功，行数>0
- [ ] S2提取到至少1个广告组合
- [ ] S3帕累托计算完成，头部4%词数≥1
- [ ] S3.5 C2 深度分析完成，输出点击分布和词根关联数据
- [ ] 报告每章节有数据来源（无来源标"暂无数据"）
- [ ] 报告模块编号连续（一~十五），中间有模块分隔标题，模块三仅在启用周期对比时出现

## 已知局限

- Excel列映射基于2026年亚马逊后台导出格式，若亚马逊调整列顺序需更新 `scripts/run_analysis.py` 中的 `COL` 常量
- CVR/份额阈值默认值基于mascara品类经验，其他品类可能需要调整参数
- 长尾分类中的品牌词识别依赖硬编码列表，新增品牌需手动添加
- 不含销售额的ACOS计算（部分报告可能不提供销售额列）
- 报告中的"建议"部分需要agent基于数据做语义判断，不是纯确定性输出
- C2 词根分析基于英文 3+ 字符词根提取，非英语搜索词（如西班牙语）可能被归为独特词根
