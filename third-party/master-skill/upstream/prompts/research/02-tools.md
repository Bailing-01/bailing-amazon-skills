# Track 02 — Tools Research Subagent

> Phase 1 wave 2 的第 2 路 subagent。SKILL.md Phase 1 调用本文件作为子任务模板。

## 你的任务

调研「{industry}」（locale={locale}）行业的 **工具栈** ——这一行的资深人在日常工作中实际使用的工具集合，并提炼**选型决策树**。

输出不是工具目录（那是 awesome-X 列表的工作）。输出是 **三层结构（必备 / 场景特化 / 新兴）+ 选型决策树 + 避坑清单**，让 Phase 2 能直接整合进生成 skill 的 [工具栈与选型决策树](../../references/skill-template.md) 节。

## 输出位置

```
{skill_dir}/references/research/02-tools.md
```

文件存在则覆盖。

## Source Manifest 引用规范 (iter 24, 强制)

详见 `prompts/research/_source_id_manifest.md`. 摘要:

1. 文件最前面写 `## Source Manifest` 表 (source_id / url / bucket / last_checked / author / note). 黑名单 URL 进表即报错
2. 每条 claim (工具的 `投入产出比` / `适合 / 不适合` / `避坑` 等) 后挂 `evidence: [Sxxx]`
3. URL 用 `python3 {master_skill_dir}/tools/research/source_verifier.py classify <URL>` 跑一遍, 取 bucket
4. Phase 4 跑 `tools/research/quality_check.py` item 13 + 14 + 15 + 16 验证
5. 冷僻行业: vendor docs 是 verified_primary; 行业大会 sponsor list / 招聘 JD 作 surrogate_primary 补充

## Wave 2 加成（从 wave 1 拿 seed）

本 track 在 Phase 1 wave 2 启动，**已经能从 wave 1 拿到 seed 工具候选**：
- Track 04 (canon) 中点名的工具（书 / 论文 / 课程教的工具）
- Track 05 (sources) 中频繁被讨论 / 评测 / 对比的工具（podcast 嘉宾 / newsletter 推荐过的）
- Track 06 (glossary) 中提到的标准化工具 / 行业必装

Wave 1 通常贡献 5-15 个 seed tools。Wave 1 输出不足（< 3 seed）→ 先回头检查 wave 1 是否完成，避免在 tools track 浪费时间盲搜。

## 6 步流程

### Step 1: 候选清单（Wide Net）

撒大网，**目标 25-40 个候选工具，floor 20，<15 触发冷僻协议**。来源（按权重）：

1. **Wave 1 seed**（前述）
2. **GitHub trending + topic 页**：每个 industry 都有特定 topic。例：`https://github.com/topics/llm-agent`、`https://github.com/topics/cross-border-ecommerce`
3. **行业专属对比文章**：搜「{industry} tool comparison」「{industry} stack」「best X for Y」，**优先实战工程师 / 资深从业者写的**（不是 SEO 农场）
4. **行业会议 / 大会的赞助商列表 + 演示工具**：B 站 / YouTube 找近 12 个月的核心 conference talk，看他们用什么工具 demo
5. **行业关键人物在公开输出中提到的工具**：Track 01 figures 的长访谈 / blog 中实际用的工具（高权重，因为有真实从业者背书）

```
搜索词模板（按 locale 调整）：
- en: "best {industry} tools 2026", "{industry} stack survey", "what {role} actually use"
- zh-CN: "{中文行业名} 工具栈"、"{中文行业名} 必备工具"、"X vs Y 选型"
- 避免：「10 大工具」「2025 必装」这类 SEO 农场标题
```

### Step 2: 信源黑名单（按 locale）

| Locale | 永不引用 |
|--------|---------|
| zh-CN | CSDN（除原作者），博客园 SEO 转载，知乎付费回答下的「广告答」，公众号 |
| en | Medium SEO 农场，G2 / Capterra 付费推广，AI 合成 review 站 |
| 通用 | 工具厂商自家 PR / 案例（可作为 reference 但权重低） |

### Step 3: 三层分类 + 每层质量门槛

每个候选必须分入以下三层之一：

#### 必备层（≥ 80% 从业者用）

证据要求 **任一**：
- ≥ 3 个独立 source（行业人长访谈 / 评测 / case study）都点到这个工具
- 行业大型 survey / state-of-X report 显示 ≥ 50% 采用率
- GitHub stars > **行业自适应基准**（不是硬编码值）：取本次候选池中所有有 stars 数据的工具的**中位数 ×2**作为「必备层 stars 阈值」。例如，LLM agent infra 候选中位数约 3k → 必备阈值 6k；冷僻 vertical 中位数 200 → 必备阈值 400。这避免了硬编码「LLM=5k / 跨境电商=1k」这种跨行业差距太大的表

#### 场景特化层（特定子方向用）

证据要求 **同时**：
- ≥ 2 个 source 提到「在 X 场景下 Y 优于通用方案」
- 至少 1 个真实 production case study（不是 toy demo）
- 明确的「适合 / 不适合」分界场景，能写进决策树分支

#### 新兴 / 实验阶段（近 12 个月出现 / 起势）

证据要求 **同时**：
- 出现时间 ≤ 12 个月（GitHub 创建日期 / 首个版本发布 / 首次公开提及）
- ≥ 2 个早期采用者（业内有名字的工程师 / 团队公开提到使用）
- 标注 `stability: experimental`，明确「6 个月后可能不存在」

**不进任何层的候选**：
- 1-2 个 source 提到但无 production case
- 工具厂商自身 PR 说服力强但社区采用率低
- Already deprecated / archived（GitHub archived flag, 维护停滞 > 12 月）

### Step 4: 每个工具的标准数据结构

```markdown
### {{N. 工具名}}

- **One-liner**: {{这个工具解决什么核心问题，一句话。例：「Vespa — production-grade hybrid retrieval engine, 适合 hyrbid sparse-dense + filtering 复杂场景」}}
- **Tier**: 必备 / 场景特化 / 新兴
- **Maintainer / Owner**: {{org or person + URL}}
- **License**: {{open / proprietary + 具体 license}}
- **Maturity signals**:
  - GitHub stars: {{N}} (last checked: YYYY-MM-DD)
  - First public release: {{YYYY-MM-DD}}
  - Last commit: {{relative, e.g. "3 days ago"}}
  - Activity: {{healthy / declining / archived}}
- **典型使用场景** (针对场景特化层): {{1-3 个具体场景，每个 1 句}}
  - **CLI 化暗示 (v0.6+)**: 在 Phase 2 synthesis 阶段，「典型使用场景」+ 工具的「选型决策树」(Step 5) 会被组合进 playbook 规则，进而被 `cli_writer.py` 抽到 `cli/decision/*.sh`。**场景描述越具体（例：「production-grade hybrid retrieval, scale > 1M docs」），决策树越可执行**；不要写「适合各种 RAG 场景」这种笼统话。
- **不适合 / 替代方案**: {{什么时候**不**该用 + 替代品}}
- **生产案例** (≥ 1 真实 production case for 场景特化 / 必备 tier):
  - {{Company / Team}} 用它做 {{what}}: {{URL or reference}}
- **维护者背景** (sub_skill_link): 与 Track 01 (figures) 中的 {{name}} 关联（如适用）
- **近期变化** (近 12 个月): {{重要 release / breaking change / 战略转向，如有}}
- **来源** (≥ 3):
  - [Primary] {{tool docs / official blog post}}: {{URL, collected: YYYY-MM-DD}}
  - [Secondary] {{第三方对比 / case study}}: {{URL}}
  - [Reference] {{Track 01 figure 提到的地方}}: {{URL}}
- **可信度**: high / medium / low
- **Decay risk**: low / medium / high (附概率锚点)
  - **high** = 12 个月内被显著改变 / 取代的概率 > 40%（新兴层默认 high）
  - **medium** = 12-24 个月内被显著改变的概率 20-40%
  - **low** = 24+ 个月内被显著改变的概率 < 20%（已成行业基础设施，3+ 年稳定）

  概率不是精确预测，是评级锚点 — 让评估者「这个工具在 18 个月后还能用吗？」时有具体校准。
```

### Step 5: 选型决策树（重要 — 这是 Phase 2 的关键输出）

不要列「工具 A 适合 X，B 适合 Y」这种没有比较的清单。**构造一棵决策树**，从「用户的核心问题是什么」分支：

```markdown
## 选型决策树

### 决策树 A: 你的核心目标是什么？

#### Branch 1: {{快速验证想法 / demo 阶段}}
→ 推荐: {{tool}}（理由 1-2 句）
→ 不推荐: {{tool}}（理由：通常是「太重」「学习成本高」「rotation cost 高」）
→ 真实案例: {{2-3 个 YC / 知名团队的选型决策}}
   - 找不到具体公开案例时不要编造，标 `[no public case found, based on stack-pattern analysis from {N} similar adoption signals]` 并降级该 branch 的可信度

#### Branch 2: {{已有 PMF, 需要 production-grade}}
##### Branch 2a: 主要瓶颈在 {{scenario A}}
→ 推荐: {{tool}}
→ 替代: {{tool}}（不推荐的话写理由）
##### Branch 2b: 主要瓶颈在 {{scenario B}}
→ ...

#### Branch 3: {{规模化阶段, 特定瓶颈}}
→ ...
```

每个分支必须能从 research 笔记追溯到证据。决策树**节点数量 5-10**：少了不够区分场景，多了没人记得住。

### Step 6: 避坑清单 + 总览表 + Phase 2 接口

#### 避坑清单（≥ 5 条）

从 source 中抓「业内人吐槽 / case study 失败 / blog post 复盘」中的常见错误选型：

```markdown
- ❌ 不要用 {{X}} 做 {{Y}}：{{原因 + 案例链接}}
- ❌ 不要把 {{X}} 当成 {{Y}}：{{常见误解}}
- ...
```

#### 总览表

文件开头放总览，便于 Phase 2 提炼快速扫：

```markdown
## 总览（按 tier 分组）

### 必备（{{N}} 个）
| 工具 | 一句话 | Decay | Sources |
|------|--------|-------|---------|
| ... |

### 场景特化（{{N}} 个）
...

### 新兴（{{N}} 个）
...
```

#### Phase 2 接口

文件末尾：

```markdown
## Phase 2 提炼提示

**反复出现 ≥ 3 source 都强调的「工具选型原则」**（候选 playbook 规则）:
- {{原则 1}} (出现于: source X / Y / Z)
- ...

**显著的工具流派分裂**（候选 智识谱系条目）:
- {{流派 A: 厚框架派}}（代表工具: A, B; 代表人物: 与 Track 01 关联）vs {{流派 B: 薄框架派}}（...）

**新兴工具信号**:
- 当前活跃 / 上升的新工具数: {{N}}
- 出现 → 主流 速度估计: {{个月}} (基于 history pattern)

**冷僻 / 信号薄弱**:
- 必备层 < 3 个？ 必备层证据 < 50% 采用率？ 新兴层 0 个？
- 任一为真 → Phase 2.8 诚实边界标注「工具栈维度信号薄弱」
```

---

## 时效性硬规矩

工具栈是 master skill 衰减最快的部分。**每个工具卡片必须有 `last_checked: YYYY-MM-DD`**，**且每个 maturity signal（GitHub stars / commit activity / market share）必须有具体日期**。

不接受：「stars: ~10k」「actively maintained」这种无日期表述。
接受：「stars: 9.8k (2026-05-01)」「last commit: 2 days ago (2026-05-01)」。

理由：master skill 的 update 流程（SKILL.md Phase 0C）按距今多久决定刷哪一节。tools 节如果没具体日期就没法判断什么时候过期。

---

## 失败处理

| 情况 | 处理 |
|------|------|
| Web search 返回大量「10 大工具」SEO 农场 | 切到 GitHub topics 页 + 行业专属 newsletter / podcast 嘉宾推荐 |
| GitHub topic 页本身就稀疏（< 20 repo） | 行业冷僻信号，标注后改用「行业专属 conference 演示工具列表」+「Track 01 figures 长访谈中实际用过的工具」兜底 |
| 大量工具 last_commit > 6 月 | 行业可能已经稳态化（不是衰退）。在 Phase 2 接口标注「工具栈进入稳态期，新兴层数量少」，不算调研失败 |
| 主流工具背后是闭源 / 不公开 | 标 `license: proprietary` + 「来源：第三方使用 case study」，可信度可降 medium |
| 调研超时（5 分钟无新增有效来源） | 不死磕，按当前数据出文件，标记 "{N} candidates explored, {M} retained" 给 Phase 1.5 review |

---

## 与其他 Track 的协作

- **Wave 1 → Track 02**：从 Track 04 (canon) / 05 (sources) / 06 (glossary) 拿 seed 工具
- **Track 02 → Track 01**：找出工具的 maintainer / 关键 commit 人 → 候选 figures（如不在 Track 01 已 retained 列表，提交给 Track 01 重新 walk）
- **Track 02 → Track 03**：工具的「典型使用场景」直接成为 Track 03 (workflows) 的 SOP 步骤候选
- **Track 02 → Phase 2.1**：「工具流派分裂」直接进入心智模型候选清单（如「thin framework vs thick framework」）

如果 wave 间发现矛盾（Track 04 说 X 是必读但 Track 02 找不到 X 工具的 production case），保留矛盾给 Phase 1.5 用户裁决。

---

## 质量自检（提交前）

- [ ] 候选数 ≥ 20？（< 15 触发冷僻协议）
- [ ] 三层都有内容？必备层 ≥ 3 / 场景特化层 ≥ 5 / 新兴层 ≥ 2（极冷僻行业可松到 1/2/0）
- [ ] 每个工具有 `last_checked` 日期 + 至少 1 个 maturity signal 带具体日期？
- [ ] 选型决策树 5-10 个节点？每个节点有具体证据 / 案例？
- [ ] 避坑清单 ≥ 5 条？
- [ ] 一手来源（tool docs / official blog / Track 01 figure 直接引用）≥ 50%？
- [ ] Decay risk 字段每个工具都标了？
- [ ] Phase 2 接口部分填了？

任一不通过 → 补完再提交。**不要**把不完整的 `02-tools.md` 提交给 Phase 1.5 / Phase 2。
