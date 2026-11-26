# Track 03 — Workflows Research Subagent

> Phase 1 wave 3 的最后一路 subagent。SKILL.md Phase 1 调用本文件作为子任务模板。

## 你的任务

调研「{industry}」（locale={locale}）行业的 **当前工作流 / SOP / 方法论 / pipeline** ——这一行的资深人在日常工作中实际怎么干活。

输出不是教科书流程图（那是 textbook 的工作）。输出是 **「入门 SOP」+「资深路径」+「近期工作流变化」+ 时效锚点**，让 Phase 2 能直接整合进生成 skill 的 [工作流 / Pipeline](../../references/skill-template.md) 节。

工作流是 master skill **衰减最快** 的部分（见 extraction-framework.md § 八）。本 track 的输出**强制要求**每个 workflow 有 `last_updated` 日期 + 触发变化的事件。

## 输出位置

```
{skill_dir}/references/research/03-workflows.md
```

文件存在则覆盖。

## Source Manifest 引用规范 (iter 24, 强制)

详见 `prompts/research/_source_id_manifest.md`. 摘要:

1. 文件最前面写 `## Source Manifest` 表 (source_id / url / bucket / last_checked / author / note). 黑名单 URL 进表即报错
2. 每个 workflow 的 `Trigger`, `Output`, `资深差异` (skip/optimize/add) 末尾挂 `evidence: [Sxxx]`
3. URL 用 `python3 {master_skill_dir}/tools/research/source_verifier.py classify <URL>` 跑一遍, 取 bucket
4. Phase 4 跑 `tools/research/quality_check.py` item 13 + 14 + 15 + 16 验证
5. 冷僻行业: 监管 / 立法文件 + 行业协会 SOP 做 surrogate_primary; 招聘 JD 的 responsibility 列表反推 workflow 步骤

## Wave 3 加成（用 Wave 1 + Wave 2 全部产出做 seed）

本 track 在 Phase 1 wave 3 启动，**已经能从前两 wave 拿到所有 seed 信号**：
- Track 01 (figures) 中长访谈 / podcast 提到的「我做 X 时通常这样走」叙事
- Track 02 (tools) 中每个工具的「典型使用场景」字段直接对应一段 SOP 步骤
- Track 04 (canon) 中经典著作 / 课程描述的标准流程
- Track 05 (sources) 中近期 newsletter / podcast 讨论的「工作流变了什么」
- Track 06 (glossary) 中行业术语暗含的标准化流程（如「敏捷 sprint」「VAT 一站式申报」「投流 ABCD 测试」）

Wave 1 + Wave 2 通常贡献 **15-30 个 workflow 片段** 作为 seed。实际工作是把碎片拼成完整的「入门 SOP」+「资深路径」。

如果前两 wave 完成度不足（< 5 seed） → 警告但继续，纯 web search 兜底。

## 6 步流程

### Step 1: Workflow 候选清单（Wide Net）

撒大网，**目标 6-12 个 workflow，floor 4，<3 触发冷僻协议**。

#### Workflow 边界判定（重要 — iter 8 finding 修正）

不是每个候选都是 workflow。3 类相似但不同的东西必须区分：

| 类型 | 判定 | 归属 |
|------|------|------|
| **Workflow** | 从 trigger 到 output 的**完整闭环**，3-7 步可名词化 | 本 track |
| **决策树 / Decision tree** | 「在 X 情况下选 Y vs Z」的一次性判断，无连续步骤 | 推回 Track 02 (tools) |
| **Micro-improvement** | 单步优化（如「sync → streaming」「batch size 调优」） | 不进任何 track，最多在 Phase 2.6 反模式节作 hint |

判定问题：「这是从一个状态到另一个状态的连续动作链吗？」是 → workflow。「这是一次选择吗？」是 → 决策树。「这是单步优化技巧吗？」是 → micro-improvement。

每个候选 workflow 是一个**完整的从 0 到结果的 pipeline**。例（LLM agent infra）：

- "Build a production-ready RAG agent from scratch"
- "Add observability + eval to an existing agent"
- "Migrate from prompt-based to graph-based agent"
- "Choose between hosted vs self-hosted vector DB"
- "Productionize a multi-agent system"
- "Audit + fix a failing agent in prod"

每个候选必须能拆成 **3-7 个具体步骤**，每步骤可名词化（不是 "do good engineering"）。

来源（按权重）：

1. **前两 wave seed**（前述）
2. **行业经典著作 / 课程的工作流章节**（Track 04）
3. **真实工程师写的「我们怎么做 X」长 blog post**（≥ 30 min 阅读量）
4. **行业 conference talk 中的 "lessons learned" 演讲**（B 站 / YouTube 长 talk）
5. **公司 engineering blog 中的 case study**（Anthropic / OpenAI / Vercel / Spotify 等）

```
搜索词模板：
- en: "how we built {scenario}", "production {industry} workflow", "lessons from running {X}"
- zh-CN: "我们是怎么做 {场景}"、"{行业} 完整流程"、"踩坑 + 复盘"
- 避免：「7 步搞定 X」类 SEO 农场标题
```

### Step 2: 每个 Workflow 的标准数据结构

```markdown
### {{N. Workflow 名称（动作 + 对象）}}

- **One-liner**: {{这个 workflow 解决什么问题，从什么状态到什么状态}}
- **Trigger**: 什么时候启动这个 workflow（业务 / 技术触发条件）
- **Output**: 跑完这个 workflow 后的具体产出
- **入门 SOP（minimum viable steps）**:
  1. {{step 1}}: {{what / who does it / inputs / outputs}}
  2. {{step 2}}: ...
  ...（3-7 步）
  - **每一步如果跳过会发生什么**: {{具体后果，必须填 — 没具体后果就证明这步不必要，从 SOP 里删掉}}
- **资深路径（差异点）**：分 3 种类型 (`skip` / `optimize` / `add`) 标注，便于 Phase 2 接口统计差异类型分布
  - **skip**: 资深人会**跳过** {{steps}}: {{为什么 — 经验告诉他们这步通常不必要}}
  - **optimize**: 资深人会**优化** {{steps}}: {{怎么优化}}
  - **add**: 资深人会**额外做** {{steps}}: {{初学者忽略但资深人不会跳的事}}
  - 不是每个 workflow 都有全部 3 种类型 — 但至少有 2 种 + 总计 ≥ 2 处差异才算 retained 合格
- **近期变化**（近 12 个月）：
  - {{YYYY-MM 起，由 X 触发，原本 step Y 变成了 Z}}
  - 触发事件类型: 新模型 / 新工具 / 法规变化 / 行业事件 / 标准更新
  - 当前采用率（如有数据）: {{X% 的从业者已经切换到新流程}}
  - **稳态 workflow 的合法填法**（iter 8 finding 修正）：legacy / mature 行业的多数 workflow 5-10 年无重大变化，明确填 `近 12 个月: 无重大变化（行业稳态，最近一次显著变化是 YYYY 的 X 事件）`，**这是合法的**，不是缺漏。这种 workflow 应标 decay risk: low
- **典型耗时**:
  - 入门 SOP: {{N hours / days / weeks}}
  - 资深路径: {{N hours / days / weeks}}
- **关键工具（与 Track 02 关联）**:
  - {{tool}}（必备 / 场景特化 / 新兴）
- **关键人物（与 Track 01 关联）**:
  - {{figure}} 在 {{long-form material}} 中详细谈过这个 workflow
- **常见失败模式**:
  - {{failure 1}}: 触发原因 + 怎么避免
  - {{failure 2}}: ...
  - **CLI 化暗示 (v0.6+)**: 这些失败模式会被 `cli_writer.py` 抽进 `cli/workflow/{slug}.sh` 的「失败模式自检」环节，每个 failure 都会变成 user 必须确认的 yes/no 检查项。**写法要 actionable**（不是「demo 不稳」而是「Build with Chroma in dev, then struggle migrating to Pinecone — wastes 1-2 weeks」）。
- **来源** (≥ 3):
  - [Primary] 工程师 / 公司 blog 第一手描述: {{URL, collected: YYYY-MM-DD}}
  - [Secondary] 教程 / 二手转述: {{URL}}
  - [Reference] Track 01 figure 在 podcast 中提到: {{URL}}
- **Last_updated**: YYYY-MM-DD（基于 source 中最新一份 first-hand description 的日期）
- **Decay risk**: low / medium / high
  - **high** = 12 月内会因模型 / 工具升级显著改写（默认所有 LLM 时代的 agent workflow）
  - **medium** = 12-24 月会有显著优化路径出现
  - **low** = 已经稳态化的工作流（基础设施类、合规类）
```

### Step 3: 判定标准（必须满足才进入 retain 列表）

每个 workflow 候选 4 项打 ✅/⚠️/❌：

- **完整性**：从 trigger 到 output 闭环，3-7 步可名词化（不是「写好代码」「优化性能」这种抽象动词）
- **可追溯性**：≥ 3 条来源（其中 ≥ 1 是一手 — 工程师 / 公司 blog）
- **入门 vs 资深差异化**：能填出至少 2 处资深差异点（跳过 / 优化 / 额外）；填不出说明这个 workflow 还不够成熟到形成「资深路径」
- **时效锚点**：能给出 last_updated 日期 + 至少 1 个近期变化（或明确写「workflow 已稳态，近 12 月无重大变化」）

判定：
- 全 ✅ → KEEP, 可信度 high
- 3 ✅ → KEEP, medium，标注缺哪一项
- 2 ✅ → BORDERLINE, only KEEP if retained < 6, 标 edge
- ≤ 1 ✅ → DROP

### Step 4: 入门 SOP vs 资深路径区分（Track 03 特有的核心动作）

extraction-framework.md § 四 强调：**入门 SOP 和资深路径必须分开记录**。

入门 SOP = "怎样能把这件事做完"。
资深路径 = "怎样能少做几步且更好地做完"。

**判断 step 是否进入 入门 SOP**：问「这步如果跳过会发生什么？」。必须有具体可验证的后果（数据丢失 / 合规风险 / 后续步骤失败 / 客户投诉）。

**判断 step 是否资深差异点**：寻找「资深人 5+ 年经验告诉他们这步通常不必要」或「这步的精确跳过条件」。

如果 workflow 没有明显的「资深差异」可记录 → 这个 workflow 可能太新（新兴 < 12 月）或太基础（每个人都这么做）。前者是有趣信号，后者考虑从 retain 中 drop。

### Step 5: 总览表

```markdown
## 总览（按 decay risk 分组）

### High decay (12-month-class) — {{N}} 个
| Workflow | Trigger | Output | Last_updated | 资深差异 |
|---------|---------|--------|-------------|---------|

### Medium decay — {{N}} 个
...

### Low decay — {{N}} 个
...
```

### Step 6: Phase 2 接口

文件末尾：

```markdown
## Phase 2 提炼提示

**反复出现 ≥ 3 个 workflow 都包含的步骤**（候选 playbook 通则）:
- {{step pattern 1}} 出现于 workflows: A / B / C → 候选「如果 X，则 Y」playbook
- {{step pattern 2}} ...

**入门 SOP 和资深路径之间最大的差距**（候选 心智模型）:
- 入门 SOP 平均长度 N 步，资深路径压缩到 M 步 → 推断这一行的资深人特别擅长 {{某种判断 / 优化 / 跳过}}
- 例：「资深人都会跳过 step X」→ 心智模型候选「不要在 X 阶段过度设计 / 优化 / 验证」

**近期工作流变化的根本原因**:
- 触发变化的事件类型分布: {{N 个 workflow 因新模型变 / N 个因新工具 / N 个因法规}}
- 主要驱动力 → Phase 2 时识别行业的「外部驱动力」（影响 心智模型 + 反模式）

**冷僻 / 信号薄弱**:
- workflow 数 < 4？ 一手 source < 50%？ 资深差异点缺失 > 50% workflows？
- 任一为真 → Phase 2.8 诚实边界标注「workflow 维度信号薄弱」
```

---

## 时效性硬规矩

工作流是 master skill 衰减最快的部分。**每个 workflow 卡片必须有 `last_updated`** + **至少 1 个近期变化字段** + **触发事件类型标注**。

不接受：「最近行业有变化」「现在大家都在用 X」这种无日期 / 无具体事件描述。
接受：「2025-Q4 起，由 Anthropic Tool Use API 的 native function calling 推动，原 step 4「自定义 retry 逻辑」可省略」。

理由：master skill 的 update 流程（SKILL.md Phase 0C）按距今多久 + 触发事件类型决定刷不刷新。Workflow 节是首要刷新对象。

---

## 失败处理

| 情况 | 处理 |
|------|------|
| Wave 1+2 seed < 5 | 警告但继续。纯 web search 兜底，重点搜「engineering blog + workflow / pipeline + {industry}」 |
| 候选 workflow 太抽象（「写好代码」「优化体验」） | 推回，要求具体 trigger / output / 步骤可名词化。抽象 workflow 不进 retain |
| 资深差异点几乎找不到（多 workflows） | 行业可能太新（成熟资深从业者少）。在 Phase 2 接口标注「行业资深差异不显著，资深 SOP = 入门 SOP + 5-10% 优化」 |
| 多 workflow 互相矛盾（A blog 说步骤 X 必做，B 工程师说 X 已废弃） | 保留矛盾，Phase 1.5 用户裁决。通常代表行业正经历 workflow 跃迁 |
| 全是 high-decay workflows，没有 stable 的 | 行业还在快速演化期。在 Phase 2.8（诚实边界）明确警告「本 skill 工作流模块 6 个月内大概率全面过时，强烈建议每 3 月跑 update」 |
| 调研超时（5 分钟无新增有效来源） | 不死磕，按当前数据出文件 |

---

## 与其他 Track 的协作

- **Wave 1+2 → Track 03**：从前两 wave 全部抽 seed
- **Track 03 → Phase 2.2 (playbook)**：跨 workflow 的共同步骤直接成为 playbook 候选
- **Track 03 → Phase 2.4 (workflow section)**：直接组装入门 SOP + 资深路径
- **Track 03 → Phase 2.8 (诚实边界)**：decay risk 标注直接进入 honesty section（「本 skill 工作流节预计衰减最快」）

如果发现 Track 02 找出的某工具其实在所有 workflow 中都是 step X 的关键工具但没被分类到必备层 → 反馈给 Track 02 重新评级。反向：Track 03 提到工具但 Track 02 没收录的 → 反馈 Track 02 补充。

---

## 质量自检（提交前）

- [ ] Workflow 数量 ≥ 4？（< 3 触发冷僻协议）
- [ ] 每个 workflow 有完整 12 字段卡 + last_updated 日期？
- [ ] 入门 SOP 和资深路径分开了？≥ 80% workflows 都有 ≥ 2 处资深差异点？
- [ ] 近期变化字段 ≥ 60% workflows 都填了？（要么是变化，要么明确写「稳态」）
- [ ] 一手来源（工程师 / 公司 blog）占比 ≥ 50%？
- [ ] Decay risk 字段每个 workflow 都标了？
- [ ] 总览表按 decay 分组？
- [ ] Phase 2 接口（共同步骤 + 入门资深差距 + 变化触发分布 + 冷僻信号）填了？

任一不通过 → 补完再提交。
