# Phase 2 — Synthesis (提炼)

> Phase 2 的执行剧本。SKILL.md Phase 2 调用本文件。

## 跨步骤硬规矩 (iter 27 — codex 审计后强化)

### A. 数字 / deadline / 拒审率 必带来源 + 日期 + 置信度

任何 `%` / 具体数字 / `YYYY-MM-DD` deadline / 价格 / 拒审率 在 synthesis 出现, 必满足以下之一:

- (a) 紧跟 source_id (e.g. `12% 拒审 (T03-S017)`)
- (b) 标注业内估计来源 (e.g. `拒绝率 20-40% 业内估计 / Apple 不公开`)
- (c) 引官方原文 URL (e.g. `Apple 公开 90% < 24h, developer.apple.com/app-store/review/`)
- (d) 注明置信度 (e.g. `需 self-verify / 第三方数据观察 / Capgo 数据 / 业内估`)

**反模式**: 编 specific 数字 (e.g. `98% < 48h` / `40% reject` / `800+ 备案` / `$299 org`) 没源 = hallucination risk. codex 一审就抓 — 见 ios-app-launch prototype 2026-05-10 codex 审计.

### B. Agentic Protocol §9 维度互斥性

§9 的 5-7 个研究维度**必互斥, 不 overlap**. 反模式:
- "学派语境" + "学派分歧识别" 重复 (前者识别用户在哪派, 后者 6 派对照 — 都涉及派别)
- "区域语境" + "国内合规派" 重叠 (区域 = CN 自动触发国内合规)
- "stage 边界" + "时效新鲜度" 边界模糊 (老 stage 不一定意味老攻略)

**自检**: 5 维度能否独立产出**不同**结论? 若 A 结论 = B 结论, 合并. 不要为凑数硬切.

---

## 你的任务

读 6 轨 research notes (`{skill_dir}/references/research/01-06.md`)，按 [extraction-framework.md](../references/extraction-framework.md) 的方法论提炼出**行业 Master OS** 的 9 个组件，写到 `{skill_dir}/references/synthesis.md`，作为 Phase 3 的输入。

输出**不是 research 笔记的复盘**（那 Phase 1.5 已经做了）。输出是**可运行的认知操作系统**：心智模型 / playbook / 工具栈 / 工作流 / 表达 DNA / 质量基准 / 智识谱系 / 诚实边界 / Agentic Protocol。

## 输入位置

```
{skill_dir}/references/research/
  ├── 01-figures.md
  ├── 02-tools.md
  ├── 03-workflows.md
  ├── 04-canon.md
  ├── 05-sources.md
  └── 06-glossary.md
```

每个文件**末尾的「Phase 2 接口」段是你最重要的入口** — 各 track 已经为你筛好了候选信号。

## 输出位置

```
{skill_dir}/references/synthesis.md
```

文件存在则覆盖。

## 9 步执行（对应 SKILL.md Phase 2.1-2.9）

### Step 0: 候选清单准备 (跨 track 收集)

读完所有 6 轨 research，**先扫描各 track 的「Phase 2 接口」段**，汇集候选信号到 `{skill_dir}/references/synthesis-candidates.md`：

```markdown
# Synthesis Candidates (raw)

## 候选心智模型 (target 15-30)
| Candidate | 出现于 tracks | 出现 figures 数 | 类型 | 备注 |
|-----------|-------------|----------------|------|------|
| {{candidate 1}} | 01,03,04 | A/C/E/F (4) | cross-track | ... |
| ... |

## 候选 playbook 规则 (target 10-20)
| Pattern | 来源 |

## 候选工具流派分裂 (智识谱系)
| Split | A 派代表 | B 派代表 |

## 候选反模式
| Anti-pattern | 来源 |

## 候选时效信号 (诚实边界用)
| Signal | 来源 | Decay 强度 |

## 候选 Agentic Protocol 维度
| 维度 | 推导自哪个 mental model |
```

**候选数门槛与行业类型挂钩**（iter 18 修正）：

| 行业类型 | 最小候选数 | 例 |
|---------|----------|------|
| Technical (LLM agent infra / cloud infra / RAG) | ≥ 15 | 公开内容多，门槛高 |
| Academic (CV / 神经科学 / 生物信息) | ≥ 12 | paper-driven, 理论密度高 |
| Vertical 实操 (跨境电商 / 短视频投流) | ≥ 8 | 操作多，公开理论少 |
| Regulated specialized (足踝外科 / 量化金融) | ≥ 5 | 闭源主导，公开材料受限 |

候选低于阈值 → 信号薄弱，要么补 Phase 1 research，要么进入冷僻领域协议（Phase 2.8 诚实边界明确标注）。
候选 > 30 → 重复 / 雷同太多，先合并同类项再走三重验证。

### Step 1: 心智模型提炼 (对应 SKILL.md Phase 2.1)

按 [extraction-framework.md § 一](../references/extraction-framework.md) 的三重验证 (PASS / PARTIAL / FAIL) 评估每个候选：

- 验证 1 (跨场景复现): ≥ 2 子场景 + ≥ 2 独立 figures
- 验证 2 (生成力): 能推断行业人对新问题的立场
- 验证 3 (排他性): 仅在这一行特别成立

**候选 → 评级矩阵**：
- ✅✅✅ → 心智模型, KEEP
- ✅✅⚠️ (验证 3 PARTIAL) → 行业放大版心智模型，KEEP 但描述强制捕捉「放大程度」
- 任一 ❌ + 其他 ✅ ≥ 2 → 决策启发式, 推到 Step 2
- ≤ 1 ✅ → 行业八股, DROP (最多 glossary 一笔)

**目标产出**: 3-7 个心智模型。每个含：
- 名称
- 一句话描述
- ≥ 2 处来源证据 — **必须以 `evidence: [Txx-Sxxx, Tyy-Syyy]` 形式挂出 source_ids** (来自六轨 Source Manifest, 见 `prompts/research/_source_id_manifest.md`). 跨 track 引用更佳, 体现共识跨场景
- 应用方式 (when to invoke)
- 局限 (mandatory — 不写就降级)

**evidence 引用示例**:

```markdown
### 1.1 工具临时性 (mental model)
- **一句话**: 「LLM agent framework 6-12 月被模型 native 化能力吃掉一层, 选型时按『能不能在一个周末剥掉』判断」
- **应用方式**: 面对新框架/新工具, 先问「6 个月后这个能力会不会被模型 native」
- **局限**: 仅适用于被模型能力曲线快速吃掉的层 (LLM agent infra / RAG framework / prompt eng tools); 对底层基础设施 (kubernetes / db) 不成立
- **evidence**: [T01-S001, T01-S007, T05-S012]  # ≥ 2 跨人物 + ≥ 1 跨 track
```

`tools/research/quality_check.py` item 16 会扫所有 mental model, 不挂 ≥ 2 个 source_id 的会被标 fail (cross-source consensus rule 不达标 → 降级 playbook).

**反模式 (DROP 这些常见陷阱)**:
- 「关注用户体验」「先做 MVP」「数据驱动」 → 通用商业道理 (验证 3 ❌)
- 「{X} 行业重视质量」 → 没排他性
- 「专家经验很重要」 → 没生成力

### Step 2: Playbook 提炼 (Phase 2.2)

= 行业内的「快速决策规则」。形如「如果 {场景}，则 {决策方向}」。

**来源** (按权重):
- Step 1 中验证未通过但 ≥ 2 ✅ 的候选 (从心智模型降级)
- Track 03 workflows 中跨多 workflow 反复出现的步骤模式
- Track 01 figures 在长访谈中说过的「我做这种决定的标准是 X」

**质量门槛** (每条必满足):
1. 场景具体（不是「重要决策时...」，而是「**当你面对从 0 到 1 的工具选型且产品需求不稳定时**...」）
2. 决策方向明确（「**默认选 X，除非满足 Y 才考虑 Z**」）
3. 至少 1-2 个具体案例
4. 可被新情况触发，不只适用于原始案例

**目标产出**: 5-10 条。少于 5 提炼不够; 超过 10 没区分主次。

**CLI 化暗示 (v0.6+)**: 每条规则需用 `**如果 X**, 则 Y` 或 `**情景描述**, 行动` 的明确句式（粗体 + 逗号分隔）。Phase 3 的 `cli_writer.py` 会从这里抽取规则并按主题（framework / eval / RAG / observability / debug）聚类成 `cli/decision/{cluster}.sh` 决策树脚本。**句式越规整，抽取越准；模糊散文式描述会让 CLI 抽不到。**

### Step 3: 工具栈集成 (Phase 2.3) — 注意：本步是「集成」非「提炼」

直接消化 Track 02 的三层结构（必备 / 场景特化 / 新兴）+ 选型决策树。**主要工作是验证一致性**：

- 必备层 ≥ 3 个？数量太少 → 行业可能没成熟工具生态，回头看 Track 02 是否漏抓
- 选型决策树 5-10 节点 + 每节点有证据？不达标 → 让 Track 02 补完
- 避坑清单 ≥ 5 条？

**这一步主要是 sanity check，不是重新提炼**。Track 02 已经做了大部分工作。

### Step 4: 工作流集成 (Phase 2.4) — 注意：本步是「集成」非「提炼」

直接消化 Track 03 的「入门 SOP / 资深路径 / 近期变化」分组。验证：

- 每个 workflow 的入门 SOP 与资深路径是否分清?
- 资深差异（skip/optimize/add）至少 2 类 + ≥ 2 instances?
- 「近期变化」字段填了 (有变化 OR 明确「稳态」)?

**这一步同样主要 sanity check**。

### Step 5: 表达 DNA 提炼 (Phase 2.5)

按 [extraction-framework.md § 五](../references/extraction-framework.md) + Track 06 的 outsider-tell + Track 01 长访谈 register 综合：

| 维度 | 来源 |
|------|------|
| 高频用语 / 黑话 | Track 06 Tier 1 术语 + Track 01 figures 反复用的词 |
| 严肃 register | Track 01 长访谈 + Track 04 textbook 的语气 |
| 内 vs 外沟通差异 | Track 06 outsider-tell 反推 |
| 外行破绽 | Track 06 outsider-tell top 10 直接用 |
| 厂商话术拒绝 | Track 06 「行业拒绝的厂商话术」直接用 |

**关键约束**: 不模拟某个具体 figure，模拟「这一行的资深人聚一起讨论时的 register」。多人融合。

#### Step 5b: 对话样本库 (iter 26 强制 — codex 三审 P1 #4 voice check 反馈)

之前 voice check 盲测 partial 的根因是 §5 只列术语词表, 不给 in-context 对话样本. subagent 写「师兄、执业证悬、我们俩都背锅」靠 LLM 常识脑补, 不是靠 SKILL.md 给的语料. **修复: synthesis.md 必须输出对话样本库 4 类 × 各 ≥ 2 段**, 每段 ≥ 30 字, 来源是 Track 01 figures 的 voice_samples 字段:

```markdown
## 5.X 对话样本库 (industry voice 实战语料)

### 5.X.1 客户版 (面客解释 / 教育)
- 「{50-150 字 figure 原话或转述, 涉及监管 / 产品 / 健康告知 / 利率等}」(source: T01-SXXX, 原话 | 转述, 客户场景: 重疾选择/利率切换/...)
- 「...」(source: ...)

### 5.X.2 同业版 (私下 / 内训 / 同业访谈)
- 「{30-100 字, 短句 + 行业黑话 + 直接判断}」(source: T01-SXXX, ...)
- ...

### 5.X.3 监管 / 专业版 (公开场合谈标准 / 学术 / 监管解读)
- 「{50-150 字, 有引用 + 数据}」(source: T01-SXXX, ...)
- ...

### 5.X.4 反例版 (这一行的资深人**绝不会**这样说的话, 错位 / 被错位包装的销售话术)
- 「{反例话术原文}」(source: T06 outsider-tell / 厂商话术拒绝, why 反例: ...)
- ...
```

**voice_confidence 计算**:
- ≥ 2 段 / 类 × 4 类 = 8 段, 60% 标 `(原话)` → `voice_confidence: high`
- 4-7 段, 多数标 `(转述)` → `voice_confidence: medium`
- < 4 段 OR 多数标 `(推断)` → `voice_confidence: low` → quality_check item 7 不能 pass, **诚实边界节必须明示「voice 维度信号薄弱, 主 SKILL.md 风格输出靠 LLM 默认而非真行业语料」**

**关键**: 不能编. 没找到原话就标 `(转述)` 或 `(推断)`. 写进 SKILL.md §5 时把每段都带上 source_id, 让用户回溯.

**Cross-skill consistency**: 4 类对话样本要让人能区分「哪段像 figure A 说的」「哪段像 figure B 说的」 — 流派分裂在表达层也应体现. 不是把所有 figure 的 voice 调和成一个平均 register.

### Step 6: 质量基准 + 反模式 (Phase 2.6)

- **什么算「好」**: 3-5 条具体可验证的基准。来源: Track 03 资深差异点 + Track 04 canon 反复强调的标准
- **反模式**: 5-10 条外行 / 入门常犯错。来源: Track 06 outsider-tell + Track 03 失败模式

### Step 7: 智识谱系 (Phase 2.7)

按 [extraction-framework.md § 六](../references/extraction-framework.md) 处理流派分歧：

- 主要流派 / 学派 (≥ 2)
- 各派奠基人物 + 代表作 (从 Track 04 canon)
- 当前代表 (从 Track 01 figures)
- 核心分歧 (从 Track 02 工具流派 + Track 06 标准之争)

**关键**: 保留分歧而非抹平。「双方都对」是没营养的废话。

### Step 8: 诚实边界 (Phase 2.8)

按 [extraction-framework.md § 七 + § 八](../references/extraction-framework.md) 综合：

- 信息截止 `{research_date}`，工具 / 工作流模块衰减最快（每 3-6 月建议 update）
- 各 track 的薄弱维度（Phase 1.5 review 中的标注）
- 信源失衡（中英文 / 一手二手）
- 行业是否闭源 / 公开材料受限
- 法规 / 标准近期变化的预期影响（喂从 Track 06）
- **数字 / 拒审率 / deadline 必带来源 + 置信度** (iter 27 强制, codex 审计后加): synthesis 里所有 `%` / `$` / 具体数字 / 法律日期都需 source_id 或 caveat (业内估计 / Apple 不公开 / 第三方观察 等). 任何 `X% reject` / `Y deadline` / `$Z price` 没标 source = hallucination risk

**至少 3 条具体局限**。「不能替代真人」太宽泛，不算合格。

### Step 9: Agentic Protocol 推导 (Phase 2.9)

按 [extraction-framework.md § 九](../references/extraction-framework.md)：从每个心智模型反推「这个模型让人首先关注什么」，凝结成研究维度。

**数量**: 3-10 个，按行业复杂度（简单 3-5 / 标准 5-7 / 复杂 7-10）。

每个维度三段：
- **看什么** — 具体到能否被搜索动作触发
- **在哪看** — 具体 source 而非「网上搜」
- **输出格式** — 1-2 句结构化结论，便于 Step 3 调用

**反模式**:
- ❌ 「搜索相关信息」(没具体到搜索动作)
- ❌ 跨行业相同的研究维度 (失去 Agentic Protocol 的核心价值 — 这一行的特定研究方式)
- ❌ 维度数量超过心智模型数 ×2 (Agentic Protocol 应该精炼，不是穷举)
- ❌ 维度 overlap (e.g. "学派语境" + "学派分歧识别" 重复 — 都涉及派别). **自检见跨步骤硬规矩 §B**: 5 维度能否独立产出不同结论? 若 A 结论 = B 结论, 合并
- ❌ 维度推不出独立结论 (A 维度结论 = B 维度结论 → 应该合并, 不要硬切)

**CLI 化暗示 (v0.6+)**: Phase 3 的 `cli_writer.py` 会把 Section 9 的所有维度直接编排进 `cli/protocol/agentic.sh` 交互脚本（每个维度一个分节问询用户）。所以「看什么 / 在哪看 / 输出格式」三段是脚本必填字段，不可省略。**输出格式越具体，user 拿到的报告就越能用**（不要写成「相关信息」「合理结论」这类空话）。

---

## 输出文件结构

`synthesis.md` 的格式：

```markdown
# {{industry}} Master OS — Synthesis

> Phase 2 提炼结果。Phase 3 (skill writeup) 直接消化本文件。

## 1. 心智模型 (3-7 个)
### 1.1 {{name}}
[name / 一句话 / 证据 / 应用 / 局限]
...

## 2. 标准 Playbook (5-10 条)
...

## 3. 工具栈与选型决策树
[直接 reference Track 02 输出 + 一致性 sanity-check 摘要]

## 4. 工作流 / Pipeline
[直接 reference Track 03 输出 + 一致性 sanity-check 摘要]

## 5. 表达 DNA

## 6. 质量基准 + 反模式

## 7. 智识谱系

## 8. 诚实边界

## 9. Agentic Protocol — 研究维度
### 9.1 {{dimension 1}}
- 看什么:
- 在哪看:
- 输出格式:
...

## 元数据
- Synthesis date: {{YYYY-MM-DD}}
- Source counts: {{from Phase 1.5 review}}
- Cumulative findings issues: {{any unresolved cross-track contradictions}}
```

---

## 失败 / 边界处理

| 情况 | 处理 |
|------|------|
| 候选 < 15 (Step 0) | 信号薄弱，回 Phase 1.5 review，问用户是否补 research |
| 0 个候选三重通过验证 | 整个行业可能极冷僻 / 闭源 / 太新。**STOP**，向用户报告：「无心智模型可提炼。可能 (a) 行业刻意闭源 / (b) 行业过于新尚未形成 OS / (c) research 不充分。要怎么办？」 |
| 心智模型只有 1-2 个 | 冷僻协议生效，扩大诚实边界 |
| Track 间数据矛盾未在 Phase 1.5 解决 | 在 synthesis.md 顶部明确标注「跨 track 矛盾未解决：A 说 X，B 说 Y。需 Phase 2.5 review 时用户裁决」 |
| Agentic Protocol 维度推不出来 | 心智模型可能不够具体 — 退回 Step 1 重新精炼 |

---

## 与 Phase 5 (Refinement) 的衔接

Phase 2 → Phase 2.5 用户确认 → Phase 3 写出 SKILL.md → Phase 4 quality check (mechanical + subagent) → Phase 5 双 agent 精炼。

Phase 5 入口条件 (iter 18 新增): Phase 4 verdict ≥ PARTIAL（不接受 FAIL）+ 用户在 Phase 4 报告中确认「值得精炼」。Phase 5 是 polish layer，不修复 substantive 问题。FAIL 必须先回 Phase 2 / Phase 3。

## 与 Phase 2.5 (User Checkpoint) 的衔接

Phase 2 完成后，Phase 2.5 必须暂停展示提炼摘要给用户确认。本文件的输出**专门设计为**摘要友好：

- 9 个组件按节排列，便于摘要
- 每个心智模型 / playbook 有「一句话」字段，直接组合成摘要
- 「元数据」段列出 source counts + 未解决矛盾，让用户判断是否值得继续

---

## 质量自检（提交前）

- [ ] Step 0 候选清单 ≥ 15? `synthesis-candidates.md` 已写?
- [ ] Step 1 心智模型 3-7 个? 每个有 ≥ 2 处证据 + 局限?
- [ ] Step 2 playbook 5-10 条? 每条有具体场景 + 决策 + 案例?
- [ ] Step 3-4 工具栈 + 工作流的 sanity check 通过?
- [ ] Step 5 表达 DNA 包含 outsider-tell + 厂商话术拒绝?
- [ ] Step 6-8 质量基准 / 智识谱系 / 诚实边界都填了?
- [ ] Step 9 Agentic Protocol 3-10 个维度? 每个有「看什么 / 在哪看 / 输出格式」?
- [ ] 元数据段有 synthesis date + source counts?

任一不通过 → 补完再提交给 Phase 2.5 review。
