---
name: bailing-cerebro-keyword-analysis
description: H10 Cerebro 反查报表关键词分析：动态属性发现 + 四维度评估 + 总结报告。从关键词数据中自动发现产品类目与属性标签，按流量等级/蓝海度/ABA垄断/相关性四维度拆分，输出 V4.1 CSV + 四维度总结报告。当用户提到 Cerebro 分析、关键词拆分、反查报表分析、关键词四维度评估时触发。即使只说"帮我分析这份反查报表"也应触发；单维度查询不触发。
---

# Bailing Cerebro 关键词分析

## 适用与不适用

对 Helium10 Cerebro 反查 xlsx 做关键词拆分 + 四维度评估 + 总结报告。动态发现产品属性标签（不预设品类），按流量等级(S/A/B/C/D)、蓝海度(竞品数5档)、ABA垄断度(转化份额6档)、相关性(竞品表现4档)四个维度拆分关键词，输出一份 CSV + 一份总结报告。

不适用：只看搜索量排名等单维度查询；非 Cerebro 格式的关键词报表。

## 输入参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| xlsx_path | string | 必填 | Cerebro 反查 xlsx 文件路径 |
| asin | string | 从文件名提取 | 目标 ASIN，用于报告标题 |

## 流水线

执行编排：L1{S1} → L2{S2} → L3{S3}

全链为确定性管道，由 `scripts/run_full_analysis.py` 一键执行。

| 步骤 | 动作 | 调用 | 依赖 | 用途 | 详情 |
|------|------|------|------|------|------|
| S1 | 读取 xlsx + 动态属性发现 | run_full_analysis.py | xlsx_path | 提取关键词 + 词频分析 + 构建动态属性树 | `references/steps/S1.md` |
| S2 | V4.1 打标 + 四维度评估 | 内部计算 | S1 | 11维属性打标 + 流量/蓝海/ABA/相关性 → CSV | `references/steps/S2.md` |
| S3 | 总结报告生成 | run_full_analysis.py | S2 | 四维度总结分析 → JSON → HTML报告 | `references/steps/S3.md` |

## 输出文件

| 文件 | 说明 |
|------|------|
| `keyword-cosmo-attribute-{ASIN}-v41.csv` | V4.1 全量 CSV（23列：序号/关键词/原分类/11维属性/搜索量/流量等级/竞品数/蓝海度/ABA转化份额/准入难度/竞品表现得分/相关性等级/推荐行动） |
| `analysis-stats-{ASIN}.json` | 四维度统计JSON（供报告生成） |

agent 拿到 JSON 后调 `linkfox-report-generator` 生成 HTML 总结报告，报告结构：

1. **大盘概览** — 关键词总数、核心词Top10、属性维度命中分布
2. **维度一：流量等级** — S/A/B/C/D 分布 + 各等级 Top 关键词
3. **维度二：蓝海程度** — 蓝海/温和/一般/激烈/极激烈 占比 + 蓝海词清单
4. **维度三：ABA垄断度** — 友好/一般/高/很高/极激烈 分布 + 高垄断词清单
5. **维度四：相关性** — 高/中/弱/不相关 分布 + 高相关精准词清单
6. **行动建议** — 捡漏(优先)/主推/防守/否定/观察 分布 + 各行动 Top 词

⚠ 生成 HTML 报告必须先阅读 SKILL `linkfox-report-generator` 并遵循其规范。

## 执行自检

1. CSV 列数验证（防错位）
2. 动态属性树覆盖：至少 3 个维度命中 > 0
3. 品牌词过滤：is_brand=True → 推荐行动=否定

## 局限性

- 通用种子词库覆盖常见跨品类词汇；极冷门品类可能需 agent 补充
- 蓝海度/准入难度阈值沿用固定口径，不可自行修改
- `assets/neck-care-attribute-tree.json` 保留为参考样例，不再作为默认加载
