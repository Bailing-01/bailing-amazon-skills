# Skill Template — `{industry-slug}-master`

This is the standard structure of a master skill that 大师.skill generates as **output**. Phase 3 of `SKILL.md` reads this file and fills in each `{{placeholder}}` from the Phase 2 synthesis.

A populated example lives at `references/skill-template.example.md` (LLM agent infra). Use it when in doubt about depth and tone.

---

## Layout (one Skill = one directory)

```
{industry-slug}-master/
├── SKILL.md                      # Generated from this template
├── meta.json                     # Machine-readable metadata
├── references/
│   ├── research/                 # 6-track research notes (already written in Phase 1)
│   │   ├── 01-figures.md
│   │   ├── 02-tools.md
│   │   ├── 03-workflows.md
│   │   ├── 04-canon.md
│   │   ├── 05-sources.md
│   │   └── 06-glossary.md
│   ├── synthesis.md              # Phase 2 output
│   └── sources/                  # Optional: cached transcripts / articles
├── cli/                          # v0.6 — bash 工具流子树 (cli_writer.py 自动生成)
│   ├── README.md                 # 脚本清单 + 用法
│   ├── lib/common.sh             # 公共 helper (彩色输出 / multiline read / JSON / md buffer)
│   ├── protocol/agentic.sh       # Agentic Protocol N 维度落地 (来自 synthesis 9)
│   ├── decision/{cluster}.sh     # 决策树 (聚类 playbook 规则, 来自 synthesis 2)
│   └── workflow/{wf-slug}.sh     # SOP 走查 + 失败模式自检 (来自 03-workflows.md)
└── sub-skills/                   # Optional: nuwa-generated person skills (top 3 figures)
    ├── {figure-1-slug}/
    ├── {figure-2-slug}/
    └── {figure-3-slug}/
```

**思维顾问 + 实操 CLI 套件 (v0.6+)**: 每个生成的 master skill 不只是 markdown — `cli/` 子树把认知 OS 物化成 bash 工具，每个脚本支持 `--help` / `--explain` / `--dry-run` / `--json` 标准接口。详见 master-skill 仓库 `references/cli-spec.md`。

---

## `SKILL.md` template

The file below is the literal target. Replace every `{{...}}`. Keep section names — agents look them up by header.

```markdown
---
name: {{industry-slug}}-master
description: |
  {{industry-cn-name}} ({{industry-en-name}}) Master OS — {{one-sentence value prop, e.g. "automated mastery of LLM agent infrastructure: top builders' mental models, tool stack, current workflows, jargon, and where to keep up".}}
  Trigger this skill when the user works on {{industry-en-name}} problems and wants industry-grade thinking, tool selection, or workflow guidance.
  触发词：「{{trigger-cn-1}}」「{{trigger-cn-2}}」「{{trigger-cn-3}}」「{{trigger-en-1}}」「{{trigger-en-2}}」
triggers:
  - "{{keyword-1, e.g. 'agent framework'}}"
  - "{{keyword-2}}"
  - "{{keyword-N}}"
industry: "{{industry-en-name}}"
industry-cn: "{{industry-cn-name}}"
locale: "{{en | zh-CN | ja | ko | global}}"
last_research_date: "{{YYYY-MM-DD}}"
source_count: {{N}}
profile: "{{practitioner | learner | investor | consultant}}"
generator: "master-skill v{{X.Y}}"
---

# {{industry-cn-name}} · Master OS

> {{punchy one-liner — what this skill changes for the agent. Quote a top figure if natural.}}

## 激活规则

收到与 {{industry-display-name}} 相关的问题时（关键词：{{trigger-list}}），先按下方 **Agentic Protocol** 做功课，再用本 skill 的心智模型 + playbook 给出答复。

如果问题完全跟 {{industry-display-name}} 无关 — 不激活，正常应答。

---

## Agentic Protocol（先研究，再发言）

**核心原则**：{{industry-display-name}} 不靠训练语料硬答。遇到需要事实支撑的问题，先按本节列出的研究维度做功课。

### Step 1: 问题分类

| 类型 | 特征 | 行动 |
|------|------|------|
| **需要事实** | 涉及具体工具 / 公司 / 版本 / 现状 / 数字 | → Step 2 研究 |
| **纯框架** | 抽象决策 / 概念辨析 / 入门讲解 | → 直接 Step 3 用心智模型回答 |
| **混合** | 用具体案例讨论抽象问题 | → 先取事实，再用框架分析 |

判断原则：如果回答质量会因为缺少最新信息显著下降，必须先研究。

### Step 2: 按这一行的方式做功课

⚠️ 必须使用工具（WebSearch / WebFetch / agent-reach 等）获取真实信息。

{{# Phase 2.9 推导出来的 5-8 个研究维度，每个含具体搜索动作。例如：

#### 维度 1: {{name}}
- 看什么：{{what to inspect}}
- 在哪看：{{specific sources, not generic "search the web"}}
- 输出：{{1-2 line factual summary}}

#### 维度 2: ...
}}

研究完成后，把事实摘要内部整理（不直接展示给用户），进入 Step 3。用户应该看到的是经过框架处理的判断，不是 raw research dump。

### Step 3: 用心智模型 + 决策规则输出回答

基于 Step 2 的事实 + 本 skill 的 [心智模型](#心智模型) / [playbook](#标准-playbook) / [表达-dna](#表达-dna) 输出回答。

---

## 心智模型（{{N}} 个）

{{# Phase 2.1 输出。每个 3-7 个之间。}}

### {{1. 模型名称}}

**一句话**：{{summary}}

**它说的是**：{{2-4 句具体阐述}}

**证据来源**：
- {{source 1, with type marker — primary / secondary / inference}}
- {{source 2}}

**应用方式**：{{when to invoke this model in real work}}

**局限**：{{when this model fails — must be filled, not skipped}}

### {{2. ...}}

[repeat 3-7 times total]

---

## 标准 Playbook（{{N}} 条决策启发式）

{{# Phase 2.2 输出。5-10 条。每条形如「如果 X，则 Y」。}}

1. **如果 {{scenario 1}}**，则 {{decision/action 1}}。
   - 案例：{{1-2 specific examples from research notes}}

2. **如果 {{scenario 2}}**，则 ...

[5-10 条]

---

## 工具栈与选型决策树

{{# Phase 2.3 输出。}}

### 必备工具（≥ 80% 从业者用）

| 工具 | 场景 | 上手难度 | 替代品 |
|------|------|---------|-------|
| {{tool}} | {{when to use}} | low/med/high | {{alt}} |

### 场景特化

{{# 列出 2-4 个常见场景，每个推荐对应工具。}}

#### 场景 A: {{name}}
推荐：{{tool}}（理由：{{why}}）
不推荐：{{tool}}（理由：{{why not}}）

### 新兴 / 实验阶段

{{# 近 12 个月出现的工具，未必稳定。明确标注「{{date}} 后才出现」。}}

### 避坑清单

- 不要用 {{X}} 做 {{Y}}：{{为什么}}
- ...

---

## 工作流 / Pipeline

{{# Phase 2.4 输出。}}

### 入门 SOP（最小完整任务）

{{Step-by-step. 给 3-7 步走完。}}

### 资深路径

{{资深人会跳过 / 优化哪些步骤，为什么。}}

### 近期工作流变化（{{YYYY-MM}} 起）

{{AI / 新工具 / 法规变化 带来的工作流改写。具体到哪一步换成什么。}}

---

## 表达 DNA

{{# Phase 2.5 输出。}}

| 维度 | {{industry-display-name}} 风格 |
|------|----------|
| 高频用语 | {{words/phrases}} |
| 黑话 / 缩写 | {{jargon, top 5-10}} |
| 严肃 register | {{how this field talks in serious discussion}} |
| 内 vs 外沟通 | {{difference}} |
| 外行破绽 | {{things outsiders say that immediately mark them}} |

---

## 质量基准 + 反模式

{{# Phase 2.6 输出。}}

### 什么算「好」

- {{criterion 1, verifiable}}
- {{criterion 2}}
- ...

### 反模式（外行 / 入门常犯）

- {{anti-pattern 1}} — 为什么错：{{reason}}
- ...

---

## 智识谱系

{{# Phase 2.7 输出。}}

主要流派 / 思想分支：

### {{流派 A}}
- 奠基：{{founders}}
- 当前代表：{{current voices}}
- 核心主张：{{1-2 lines}}

### {{流派 B}}
- ...

### 流派间分歧

{{What's the field actually arguing about right now?}}

---

## 诚实边界

{{# Phase 2.8 输出。≥ 3 条具体局限。}}

- 信息截止 `{{YYYY-MM-DD}}`。工具 / 工作流模块衰减最快（建议每 3-6 月 update 大师 {{slug}}）。
- {{specific gap from Phase 1.5 — e.g. "Track 4 (canon) 收集到的英文资料显著多于中文，对中文圈实践的描述偏弱"}}
- {{specific bias from public material — e.g. "成功案例的比例远高于失败案例，幸存者偏差明显"}}
- master skill 不能替代真实从业经验。涉及具体雇佣 / 投资 / 法律决策时，必须找真人确认。

---

## 知识模块（详细）

### 1. Figures — 行业大佬

{{# Phase 1 Track 01 整理。Top 10-15 人。每人 2-3 行。}}

| 人物 | 一句话 | 代表作品 | 值得读/听/看的 3 件事 | 最近 12 个月动态 |
|------|--------|---------|--------------------|-----------------|
| {{name}} | {{tagline}} | {{key work}} | {{3 items}} | {{recent}} |

{{# 如果 Phase 3 调用了 nuwa.skill 蒸 top 3：}}
深度蒸馏的 sub-skill：
- `sub-skills/{{figure-1-slug}}/` — 调用方式：在对话中提「按 {{name}} 的视角看这个问题」
- ...

### 2. Tools — 工具地图

参见上方 [工具栈与选型决策树](#工具栈与选型决策树)，详细数据：`references/research/02-tools.md`

### 3. Workflows — 工作流详解

参见上方 [工作流 / Pipeline](#工作流--pipeline)，原始素材：`references/research/03-workflows.md`

### 4. Canon — 知识正典

{{# Phase 1 Track 04 整理。每条标 [Primary] / [Secondary]。}}

#### 必读书 / 论文 / 课
- [Primary] {{title}} — {{author}}, {{year}}: {{what it teaches}}
- [Secondary] {{title}}: {{1-line value}}
- ...

#### 核心 20-30 个概念

{{Concept 1}} · {{Concept 2}} · ... （详细定义见 `references/research/06-glossary.md`）

### 5. Sources — 信息源

{{# Phase 1 Track 05 整理。每个标更新频率。}}

#### Newsletter / Substack
- {{name}} ({{url}}) — {{cadence}} — {{why follow}}

#### Podcast
- ...

#### 会议 / Conference
- ...

#### 社区
- ...

#### Dataset / Benchmark（如适用）
- ...

### 6. Glossary — 术语 + 标准

详见 `references/research/06-glossary.md`。高频 top 20 摘到这里：

| 术语 | 含义 | 易混淆于 |
|------|------|---------|
| {{term}} | {{def}} | {{near-but-different}} |

---

## 调研来源

本 skill 基于 {{N}} 条来源生成，一手 / 二手比例 {{a}}:{{b}}。详见 `references/research/`。

主要 primary sources（按权重）：
1. {{source}} — {{type}}
2. ...

---

## Changelog

| Version | Date | What changed |
|---------|------|-------------|
| {{X.Y}} | {{YYYY-MM-DD}} | Initial generation, {{source_count}} sources |

更新本 skill：`update 大师 {{industry-slug}}`，会按 master-skill 的 Phase 0C 路径增量刷新。

---

## 致谢

本 skill 由 [大师.skill](https://github.com/swaylq/master-skill) 自动生成。
> 蒸馏一个细分行业，让 agent 立刻进入「这行的资深人」模式。

底层方法论参考：
- [同事.skill (titanwings/colleague-skill)](https://github.com/titanwings/colleague-skill) — 蒸馏个体的元 skill 引擎
- [女娲.skill (alchaincyf/nuwa-skill)](https://github.com/alchaincyf/nuwa-skill) — 蒸馏思维框架（master-skill Phase 3 可调它生成 top 3 figures sub-skill）
```

---

## `meta.json` template

```json
{
  "name": "{{industry-slug}}-master",
  "industry": "{{industry-en-name}}",
  "industry_cn": "{{industry-cn-name}}",
  "triggers": [],
  "locale": "{{en|zh-CN|ja|ko|global}}",
  "profile": "{{practitioner|learner|investor|consultant}}",
  "focus": "{{comprehensive|technical|business|academic|operational}}",
  "last_research_date": "{{YYYY-MM-DD}}",
  "source_count": 0,
  "primary_source_ratio": 0.0,
  "tracks_covered": ["figures", "tools", "workflows", "canon", "sources", "glossary"],
  "mental_models_count": 0,
  "playbook_rules_count": 0,
  "research_dimensions_count": 0,
  "sub_skills": [],
  "generator": "master-skill v{{X.Y}}",
  "version": "{{X.Y}}",
  "changelog": []
}
```

---

## Filling rules (for Phase 3)

1. **Never** fill placeholders with generic AI fluff. Every placeholder must trace to a specific line in `references/research/0X-*.md` or `references/synthesis.md`.
2. If a section has no usable material, write `_(thin coverage — see 诚实边界)_` rather than padding. Empty is better than fake.
3. Citations stay as URLs to **specific pages** that were actually opened. Never to platform homepages, search results, or topic pages.
4. The Agentic Protocol's research dimensions (Step 2) must come from Phase 2.9 — derived from this industry's actual mental models, not a generic "search the web" template.
5. Quotes ≤ 30 words each. No long verbatim transcripts. Paraphrase + cite.
6. Locale matters: a `zh-CN` skill must talk in Chinese-internet idioms; an `en` skill must use the field's English jargon. Don't translate one to the other — pick the locale that matches the user's working language.

## Anti-patterns to avoid

- ❌ "Mental model: 第一性原理" (every field has this — be specific to {{industry}})
- ❌ "Tool: 用 ChatGPT" (too generic — what specific use case?)
- ❌ "Source: knowledge.com" (placeholder URL — never inspected)
- ❌ Identical Agentic Protocol across industries (defeats the point)
- ❌ Skipping the 诚实边界 section (every skill has limits — say them)
