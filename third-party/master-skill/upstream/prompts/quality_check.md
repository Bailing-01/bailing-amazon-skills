# Phase 4 — Quality Check (验证)

> Phase 4 的执行剧本。SKILL.md Phase 4 调用本文件。

## 你的任务

Phase 3 写出的 `{skill_dir}/SKILL.md` 是否真的有用？通过 4 项独立测试验证：4.1 已知 / 4.2 边缘 / 4.3 风格 / 4.4 通过标准。**必须用子 agent 跑测试**（避免自评偏差）。

输出: `{skill_dir}/references/quality-check-report.md`，含 PASS / PARTIAL / FAIL 评级 + 不通过项的修复建议。

## 输入位置

```
{skill_dir}/SKILL.md                           # 待测试 skill
{skill_dir}/references/synthesis.md            # Phase 2 输出, 含心智模型 / playbook 等
{skill_dir}/references/research/               # 6 轨原始 research, 用来生成测试题
```

## 输出位置

```
{skill_dir}/references/quality-check-report.md
```

文件存在则覆盖。

## 4 项测试

### 4.1 已知测试 (Sanity Check)

**目的**: 验证 skill 在行业有共识答案的问题上输出方向是否正确。

**测试设计**:
1. **Ground truth 来源跨 Track 1+3+4** (iter 18 修正): 不只从 Track 04 canon。具体优先：
   - Track 01 figures 在长访谈中给出**直接回答**的具体问题（最高权重）
   - Track 03 workflows 中显式描述「这种情况下应该 X」的具体场景
   - Track 04 canon 经典著作中给出**明确判断**的问题
   挑 3 个**业内已有共识答案**的问题
2. 每题应**用 Track 04 中的答案作为 ground truth** （不要凭你自己印象）
3. 题目要求：
   - 不能太简单（"什么是 RAG?" — 太定义题）
   - 不能太开放（"AI 行业怎么发展?" — 没共识答案）
   - 应是「有正确答案的实操判断」（"在 X 场景下选 vector DB 还是 Vespa?"）

**spawn 子 agent 跑测试**:
```
spawn 子 agent 任务:
- 加载 SKILL.md (待测试 skill, 不要看 synthesis.md / research/ — 模拟真实用户场景)
- 回答以下 3 题:
  1. {{question 1}}
  2. {{question 2}}
  3. {{question 3}}
- 每题答案 200-400 字
- 输出到 /tmp/quality-check/sanity-answers.md
```

**评估标准** (主 agent 对比 ground truth):
- ✅ PASS: 3/3 题方向正确（细节差异允许）
- ⚠️ PARTIAL: 2/3 题正确（标注哪一题偏离 + 偏离原因）
- ❌ FAIL: ≤ 1/3 题正确

**FAIL 的修复路径**:
- 偏离来自心智模型选错 → 回 Phase 2.1 调整
- 偏离来自 Agentic Protocol 没触发研究 → 回 Phase 2.9 加该问题对应的研究维度
- 偏离来自表达 DNA 学到的 register 错 → 回 Phase 2.5 调整

### 4.2 边缘测试 (Edge Case)

**目的**: 验证 skill 在没有标准答案的场景下能否「合理推断 + 标注不确定性」。

**测试设计**:
1. 设计 1 个题目：**这个行业的 figures 没有公开讨论过但与心智模型相关**的新问题
2. 题目特征：
   - 跨场景应用（举例：「LLM agent infra」master 拿到「医疗诊断 agent 怎么设计 HITL?」— 不是核心场景但相关）
   - 或时效新（举例：「2026-Q4 刚出的 X 框架要不要采用?」— skill 训练时不存在）
   - 或反方向（举例：「为什么我们不应该用 RAG?」— 经典正向问题的反面）

**spawn 子 agent 跑测试** (同 4.1 模式)

**评估标准**:
- ✅ PASS: 答案显式调用 ≥ 2 个心智模型 + 显式 hedging（"基于 X 模型推断..., 但 Y 因素未知, 需进一步研究"）
- ⚠️ PARTIAL: 答案调用心智模型但没 hedging (答得太确定)
- ❌ FAIL: 斩钉截铁直接给答案，无 hedging，或完全跑偏

**FAIL 的修复**:
- 缺 hedging → Phase 2.8 诚实边界写得不够 / 不显著 → 回 Phase 2.8
- 跑偏 → Agentic Protocol 没指引「这一行该研究什么」→ 回 Phase 2.9

### 4.3 风格测试 (Voice Check)

**目的**: 验证 skill 写出的内容能否被识别为「这一行人写的」，不是通用 ChatGPT 味。

**测试设计**:
1. 让 skill 用 100 字写一段「这一行的最近趋势」
2. **盲测对照**: 找 3 段真实从业者写的短稿作 reference (iter 18 修正 — 明确选样规则)：
   - 1 段从 Track 01 figures 长访谈 transcript 中节选（80-150 字段落，最能体现 register）
   - 1 段从 Track 05 sources 中 top podcast / newsletter 一篇近 3 个月的内容节选
   - 1 段从 Track 04 canon 中现代 textbook 章节首段
   都是**真实从业者** 的语言，避免选 SEO blog post 或营销内容

**spawn 子 agent 跑测试** (同 4.1 模式)

**评估标准** (主 agent 比较):
- ✅ PASS: 与真实从业者短稿在 register / 用词 / 结构上**接近**（用了 ≥ 3 个 Track 06 中的 Tier 1 术语 / 拒绝了 ≥ 1 个厂商话术）
- ⚠️ PARTIAL: 用对了部分术语但 register 偏通用
- ❌ FAIL: 读起来像 ChatGPT 默认 register（"In summary..." / "It's important to note..." 这种）

**FAIL 的修复**:
- 表达 DNA 没学到 → 回 Phase 2.5 重新提炼，加多 outsider-tell + 厂商话术拒绝清单 → 重 Phase 3 写

### 4.4 通过标准 (rubric 直查)

直接对 SKILL.md 跑机械检查：

| 检查项 | 通过标准 | 不通过标志 |
|------|---------|-----------|
| 心智模型数 | 3-7 | < 3 (薄) 或 > 10 (没提炼) |
| 心智模型局限字段 | 100% 填了 | 任何一个只写优点没局限 |
| Playbook 数 | 5-10 | < 5 或 > 15 |
| Playbook 案例 | 每条 ≥ 1 案例 | 抽象规则无案例 |
| 工具三层覆盖 | 必备 ≥ 3 / 场景化 ≥ 5 / 新兴 ≥ 2 | 任一为 0（除非冷僻协议生效）|
| 工作流入门-资深差异 | ≥ 80% workflows 有 ≥ 2 资深差异点 | 多数 workflow 无差异点 |
| 表达 DNA 辨识度 | 通过 4.3 voice check | 4.3 fail |
| 诚实边界 | ≥ 3 条具体局限 | ≤ 2 条 / 全是「不能替代真人」泛话 |
| 一手来源比例 | ≥ 50% | 主要二手转述 |
| Agentic Protocol 维度 | 3-10 | ≤ 2 / 通用「搜索相关信息」 |
| 时效性标注 | 工具 + 工作流 + 法规节都有 last_updated | 任一为空 |
| 多 figure 共识门槛 | 心智模型每个有 ≥ 2 个 figures 证据 | 单 figure 个人观点冒充行业 OS |

不通过项数:
- 0-2 不通过 → ⚠️ PARTIAL，可修后通过
- 3+ 不通过 → ❌ FAIL，需要回到 Phase 2 / Phase 3 实质修订

---

## quality-check-report.md 格式

```markdown
# Quality Check Report — {{industry-slug}}-master

- **Skill version**: v{{X.Y}}
- **Check date**: {{YYYY-MM-DD}}
- **Subagent runs**: 4.1 ({{N}} questions) / 4.2 (1 question) / 4.3 (1 sample)

## 4.1 Sanity check

### 题 1: {{question}}
- Ground truth (来自 Track 04, source: {{citation}}): {{...}}
- Skill answer: {{first 200 chars + 「[full answer in /tmp/...]」}}
- Verdict: ✅ / ⚠️ / ❌
- Reasoning: {{why}}

### 题 2: ...

### Aggregate: ✅ / ⚠️ / ❌

## 4.2 Edge case

### 题: {{question}}
- Skill answer: {{first 200 chars}}
- Hedging检测: ✅ / ❌
- 调用 mental models: {{count + names}}
- Verdict: ✅ / ⚠️ / ❌

## 4.3 Voice check

### 测试 prompt: 「写 100 字关于 {{industry}} 最近趋势」
- Skill output: {{full 100 字}}
- Reference samples (3 段真实从业者): [link to /tmp/...]
- Tier 1 术语用量: {{N}} 个 (target ≥ 3)
- 厂商话术拒绝: {{count}} 个 (target ≥ 1)
- Register 接近度: ✅ / ⚠️ / ❌

## 4.4 Mechanical rubric (16 项, iter 24)

跑 `tools/research/quality_check.py check --skill-dir <skill_dir>` 自动出全表. 16 项分组:

| 组 | 项 | 检查 |
|----|-----|------|
| 结构 (1-4) | 1 | 心智模型数 (3-7) |
| | 2 | 心智模型局限 100% 填 |
| | 3 | Playbook 数 (5-10) |
| | 4 | Playbook 案例 ≥ 1 |
| 内容 (5-8) | 5 | 工具三层覆盖 |
| | 6 | 工作流入门-资深差异 ≥ 80% |
| | 7 | 表达 DNA 辨识度 |
| | 8 | 诚实边界 ≥ 3 条 |
| 来源 (9, 13-16) | 9 | 一手来源 ≥ 50% (自报) |
| | 13 | URL 一手机械验证 ≥ 50% (manifest 优先) |
| | 14 | 无黑名单 URL |
| | 15 | freshness 标注 ≥ 70% |
| | 16 | claim → evidence ≥ 2 source_ids (T01-S001 格式) |
| 维度 (10-12) | 10 | Agentic Protocol 维度 (3-10) |
| | 11 | 时效性标注完整 |
| | 12 | 多 figure 共识门槛 |

每项 status ∈ pass / partial / fail / needs_subagent / skipped.

不通过项数: {{N}}

## 总评级

- **总评级**: ✅ PASS / ⚠️ PARTIAL / ❌ FAIL
- **修复建议** (如 PARTIAL 或 FAIL):
  - {{问题 1}} → {{回到 Phase X 修}}
  - {{问题 2}} → {{...}}

## 迭代上限

如果总评级 FAIL → 回 Phase 2 修订。**最多 2 轮迭代**。仍不通过 → 在诚实边界明确标注薄弱维度，交付当前最优版本，不无限打磨。

---

## 重要：subagent 隔离

Phase 4 的 4.1 / 4.2 / 4.3 必须用**独立 subagent** 跑测试，原因：

- 主 agent 已经看过 synthesis.md + research notes，知道「正确答案」会偏向自评
- subagent **只加载 SKILL.md**，模拟真实用户场景
- 主 agent 负责评分（ground truth 来自 Track 04 / 用户提供）

如果主 agent 自己跑测试 → 等同于学生自己改卷子，结果不可信。

---

## 与 Phase 5 (Refinement) 的衔接

Phase 4 通过 → 进 Phase 5 双 agent 精炼。
Phase 4 PARTIAL → 修后再跑一次 Phase 4。
Phase 4 FAIL → 回 Phase 2 / 3 重做。

每轮 Phase 4 结果都追加到 `quality-check-report.md`，用 `## Run N (YYYY-MM-DD HH:MM)` 分节。

---

## 质量自检（提交前）

- [ ] 4.1 出了 3 题 + ground truth 来自 Track 04 (不是凭印象)?
- [ ] 4.1 / 4.2 / 4.3 都用了独立 subagent 跑?
- [ ] 4.4 mechanical rubric 12 项全跑过?
- [ ] 报告含每项 verdict + 修复建议?
- [ ] 总评级明确 (PASS / PARTIAL / FAIL)?
- [ ] 迭代次数标了 (Run 1 / Run 2)?

任一不通过 → 补完再提交给 Phase 5。
