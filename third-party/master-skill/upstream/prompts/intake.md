# Phase 0A — Industry Intake

> Phase 0A 的具体执行剧本。SKILL.md Phase 0A 调用本文件。

## 你的任务

通过有节制的对话收集 6 项信息，然后产出一个 `intake.json`，作为 Phase 0.5 创建目录 + Phase 1 启动 6 轨调研 swarm 的输入。

**节奏要求**：**「最多 2 轮」的起点是「拿到合格粒度的 industry 之后」**。如果用户给的 industry 太宽（如「AI」「电商」），先用 1-2 轮收窄，**再**走标准 2-轮节奏（其余 5 项）。收窄过程不计入「2 轮」预算。

不要变成问卷，不要每条都追问，用户主动说的不要重问。

---

## 6 项必收集信息

### 1. industry（必填）

**问什么**：「你做的具体细分是什么？」（中英文都接受）

**好答案 vs 坏答案**：

| ✅ 好（够细，能调研） | ❌ 坏（太宽，必须收窄） |
|------------------|--------------------|
| LLM agent infra | AI |
| 跨境电商运营 | 电商 |
| 短视频投流 | 营销 |
| 足踝外科 | 医疗 |
| RAG 系统设计 | 大模型 |

**用户给坏答案时的反推话术**：
> "{industry} 范围有点宽，做出来的 master skill OS 会稀薄得没用。能不能再具体一点？例如：你日常遇到的问题主要在 {推测可能的子方向 1} / {子方向 2} / {子方向 3} 哪一块？"

如果用户坚持要做宽行业 → 警告一次后接受，但在 SKILL.md 诚实边界里写明「本 skill 跨度较宽，深度受限」。

### 1.1 title（必填，由 agent 生成）

`industry` 字段确认合格粒度后，agent 立即生成一个 **4-12 codepoint 的 zh-CN 短标题** 作为目录卡片 / 详情页 H1 的主显示。规则：

- 长度 4-12 codepoint（ASCII 与 zh-CN 各算 1；例：`中医诊疗`=4，`LLM agent 基建`=12，`AI agent 变现`=12）
- 不带括号 / 不带破折号 / 不带斜杠 / 不带长英文描述
- 优先 zh-CN；允许 `AI` / `LLM` / `iOS` / `SEO` 等行业固定缩写
- 不复读 slug，但要凝练表达行业本质

| Industry | Title |
|---|---|
| LLM agent infra | LLM agent 基建 |
| 中医诊疗 (Traditional Chinese Medicine) | 中医诊疗 |
| 中国网站备案 | ICP 备案 |
| Cybersecurity Red Team | 红队渗透 |
| Software Architecture | 软件架构 |
| iOS App Launch | iOS 上架 |

生成后展示给用户：「title 我打算用 `<title>`，OK?」用户改一字也可以，但 codepoint 数仍要落在 4-12 区间。`skill_writer.parse_intake()` 会硬性校验长度 + banned chars，违反就 retry Phase 0。

### 2. focus（可选，默认 `comprehensive`，**支持组合**）

**问什么**：「你想要全景画像，还是某个角度优先？技术 / 商业 / 学术 / 操作？」

| Focus | 含义 | 调研偏向 |
|-------|------|---------|
| `comprehensive` | 全景 | 6 轨等权 |
| `technical` | 技术视角 | Track 02 (tools) + 03 (workflows) 加权 |
| `business` | 商业视角 | Track 01 (figures) + 05 (sources) 加权 |
| `academic` | 学术视角 | Track 04 (canon) + 06 (glossary 中的标准) 加权 |
| `operational` | 实操视角 | Track 03 (workflows) 重权，4 + 6 次之 |

用户没主动说 → 默认 `comprehensive`。

**组合 focus（重要）**：用户经常会说「操作 + 商业」「技术 + 学术」这种组合视角，要支持。intake.json 用 primary/secondary 结构存储：

```json
"focus": { "primary": "operational", "secondary": "business" }
```

或单值时：

```json
"focus": "comprehensive"
```

调研偏向用 primary 加权，secondary 次之。`comprehensive` 不能作为 primary 之外的 secondary（无意义）。

### 3. locale（可选，默认 "global"）

**问什么**：「你主要在哪个语言区 / 地域工作？」

可选值：`zh-CN`、`en`、`ja`、`ko`、`global`。

- 选 `zh-CN` → 信源池切到 B 站 / 小宇宙 / 36氪 / 极客公园 / 晚点 / 财新 / 虎嗅 / 机器之心；**永远排除知乎、微信公众号、百度百科**
- 选 `en` → 信源池切到 X / YouTube / Substack / arXiv / Hacker News / 行业 podcast
- 选 `global` → 双语并行，但要警告用户：「双语可能在某些维度（特别是 Track 04 canon）出现严重失衡」

**关键判断**：
- 用户用中文沟通且没指定 → 默认 `zh-CN`，因为 master skill 最终要他用
- 用户用英文沟通且没指定 → 默认 `en`
- 用户做的是国际市场（如跨境电商） → 主动建议 `global`

### 4. profile（可选，默认 "practitioner"）

**问什么**：「你跟这个行业的关系？从业者 / 学习中 / 投资视角 / 服务咨询？」

| Profile | 影响 |
|---------|------|
| `practitioner` | master skill 假设用户已有基本背景，措辞可以专业 |
| `learner` | master skill 多解释黑话、补充入门路径 |
| `investor` | master skill 重点放在 Track 01 (figures) + 05 (sources)，强化「信号 vs 噪音」识别 |
| `consultant` | master skill 强调跨子领域 + 客户翻译能力 |

### 5. local_materials（强烈推荐询问）

**问什么**：「你手上有这行的一手素材吗？行业报告 PDF / 内部文档 / 你写过的文章 / 长访谈 transcript / 视频字幕？有的话直接丢给我，比网上搜到的二手转述质量高得多。」

**为什么必问**：用户提供的一手素材在信源优先级中权重最高（见 `references/extraction-framework.md` § 七）。漏问就是放着免费的高质量信号不要。

**用户的可能回答**：
- "有" → 切换到**本地语料模式**，把素材路径或内容收集到 `intake.local_materials_paths` 数组
- "没有" → 切换到**纯网络搜索模式**
- "只有 X 类" → 混合模式，标注哪些 track 由本地素材覆盖

### 6. existing_skill_check（自动执行）

**何时执行**：`industry` 字段确认合格粒度**之后**立即执行（在问 focus / profile 之前）。比其他 4 项更早，因为如果是 update 路径，后续 5 项的取值方式都不同（继承自老 skill 而非全新收集）。

**做什么**（不要问用户）：检查 `~/.claude/skills/` 下是否已有 `{slug}-master/` 目录。

- 已存在 → 询问用户：「我看到你装过 `{slug}-master`，上次调研日期 `{date}`。要新建一个版本，还是 update 老的？」
- 不存在 → 默认新建路径

如果路径环境不是 Claude Code（例如 OpenClaw / Codex / Hermes），按 SKILL.md 的 HOST_SKILLS_ROOT 解析规则去对应路径检查。

### Slug 生成规则（必须）

`industry` 字段拿到后，立即生成 `slug`（kebab-case）：

| Industry input | Slug |
|---------------|------|
| `LLM agent infra` (English) | `llm-agent-infra` |
| `跨境电商运营` (Chinese) | `cross-border-ecom-ops` |
| `Foot and Ankle Surgery` | `foot-ankle-surgery` |
| `RAG 系统设计` (mixed) | `rag-system-design` |

规则：
1. **默认 agent 自动翻译**中文 / 混合输入到英文 kebab-case，再去掉空格、特殊符号。
2. **用户可覆盖**：「用 X 当 slug」「slug 写成 Y」，agent 接受用户给的覆盖（前提是不冲突且符合 kebab-case 规范）。
3. 翻译时**保留行业专有缩写**（LLM、RAG、API、SOC、SaaS 等不展开）。
4. 长度建议 ≤ 25 char，超出时简化（`cross-border-e-commerce-operations` → `cross-border-ecom-ops`）。
5. 翻译完展示给用户确认：「我用 `llm-agent-infra` 作 slug，OK？」

---

## 对话节奏剧本

### 标准节奏（用户给的信息全 / 半全）

```
USER: 我做 LLM agent infra，给我做一个 master skill
ASSISTANT:
  → industry: "LLM agent infra" ✓
  → 推断 locale: en（用户用中文沟通但行业是 global 英文圈，建议 global）
  → focus / profile / local_materials 缺
  → 一次问完三项

ASSISTANT 回复:
"收到。「LLM agent infra」是好粒度。补三件事：
 1) 你想要全景，还是聚焦某一面？(技术/商业/学术/操作)
 2) 你跟这个行业的关系？(从业者/学习中/投资/咨询)
 3) 手上有没有一手素材？长访谈 transcript / 内部文档 / 行业报告 PDF / 你自己写过的东西。有就 paste 路径或内容；没有我走纯网络搜索。"

USER: 全景，从业者，没素材
ASSISTANT: 「确认：industry=LLM agent infra, focus=comprehensive, locale=global, profile=practitioner, local_materials=none。开始 Phase 0.5 创建目录。」
```

### 用户给坏粒度时的剧本

```
USER: 帮我做个 AI 行业的 master skill
ASSISTANT:
  → industry: "AI" — 太宽，必须收窄

ASSISTANT 回复:
「『AI』太宽了，蒸出来的 OS 会稀薄到没用。能不能再具体一点？例如：
 - LLM 应用层：agent infra / RAG / prompt eng / fine-tuning / eval
 - 模型层：开源模型训练 / RL / multimodal / efficient inference
 - 商业 / 投资视角：AI infra 投资 / AI 产品分析
 - 你的实际工作偏哪一块？」

USER: 主要做 agent
ASSISTANT: 「LLM agent infra？还是 vertical agent 应用（如 coding agent / browser agent）？这两个调研路径很不同。」

USER: agent infra
ASSISTANT: 收 industry=LLM agent infra，继续问其他 5 项
```

### 用户拒绝细化的边界

```
USER: 我就做 AI 行业的 master skill，不要再问了
ASSISTANT:
  → 接受 industry="AI"，但记一笔 warn

ASSISTANT 回复:
「OK，industry=AI（注意：跨度大，OS 提炼会稀薄，会在最终 skill 的『诚实边界』节明确标注本 skill 跨度受限）。继续问其他几项...」
```

---

## 输出 — `intake.json`

收集完 6 项后，生成（Phase 0.5 立即用）：

```json
{
  "industry": "LLM agent infra",
  "industry_cn": "LLM agent 基础设施",
  "industry_en": "LLM agent infra",
  "title": "LLM agent 基建",
  "slug": "llm-agent-infra",
  "focus": "comprehensive",
  "locale": "global",
  "profile": "practitioner",
  "local_materials": {
    "mode": "none | local-first | local-only | mixed",
    "paths": [],
    "covered_tracks": []
  },
  "existing_skill": {
    "found": false,
    "path": null,
    "last_research_date": null,
    "decision": "new | update"
  },
  "warnings": []
}
```

字段规则：
- `slug`：industry 转 kebab-case，去掉空格 / 特殊字符。例：`LLM agent infra` → `llm-agent-infra`、`跨境电商运营` → `cross-border-ecom-ops`
- `title`：4-12 codepoint zh-CN 短标题（catalog UI 主显示），不带括号 / 破折号 / 斜杠
- `industry_cn`：如果 locale 是 zh-CN 必填，否则可选
- `local_materials.mode`：见 SKILL.md Phase 1 的模式判断表
- `warnings`：用户拒绝细化、locale 不平衡、existing skill 但要求新建等需要在最终 SKILL.md 诚实边界节复述的事

确认完毕展示给用户：

```
确认：
  industry: LLM agent infra
  focus: comprehensive
  locale: global
  profile: practitioner
  local_materials: none
  existing_skill: 无
  warnings: 无

进入 Phase 0.5（创建目录）→ Phase 1（六轨调研）。预计调研时间 30-60 分钟。
```

**确认触发词**（用户必须显式说一个，不能是默默不回应或模糊回复）：
- 中文：「确认」「ok」「开始」「go」「上」「可以」
- 英文：「confirm」「ok」「go」「start」「looks good」

用户回复触发词 → 进入 Phase 0.5。
用户要改 → 改完再确认一次再进。
用户回复模糊（「嗯」「好像可以」「应该没问题」）→ 不算确认，再问一次「这样对吗？回一个『确认』就开始」。

不要在没拿到明确触发词时擅自进入 Phase 0.5 — 用户后续若发现起点错了，回滚成本很高（已写进 skill 目录的内容要回滚）。

---

## 反模式

- ❌ 一次问 6 个问题（用户跑掉）
- ❌ 用户已说的还在重复问（让用户烦）
- ❌ 不警告坏粒度直接接受（输出垃圾 skill）
- ❌ 不问 local_materials（错过最高质量信号）
- ❌ 把 intake 写成问卷格式（不是 form，是对话）

---

## Cold deep-mode 二次 intake (iter 24, Q5b)

**触发条件**: Phase 1 wave 1 跑完后, 主大师 agent 跑 `tools/research/cold_detector.py --skill-dir <skill_dir>`. 如果 verdict 是 `cold_deep_mode` 或 `cold_too_thin` (exit 1 或 2), 不能继续走 wave 2 — 必须先回到用户做二次 intake.

**工具调用**:

```bash
# Wave 1 → Wave 2 之间检查 (只看 canon / sources / glossary)
python3 {master_skill_dir}/tools/research/cold_detector.py --skill-dir {skill_dir} --stage wave1
# exit 0  → normal,    继续 wave 2
# exit 1  → cold_deep_mode, 暂停, 跑下面的二次 intake
# exit 2  → cold_too_thin,  暂停 + 主动建议改 industry 范围 (见下面)
```

> `{master_skill_dir}` = master-skill 仓库根的 `skill/` 目录 (e.g. `~/master-skill/skill/`),
> 不是生成行业 skill 的 `{skill_dir}`. 工具住在 master 仓库, 不复制到行业 skill (避免每个行业都拖一份).
> Phase 1 wave 3 之后建议再跑一次 `--stage full`, 这次会把 figures / tools / workflows 也算进去.

### Deep-mode 二次 intake 话术

```
ASSISTANT (cold_deep_mode):
「我跑了一遍 wave 1, {industry} 这一行的公开材料偏薄
({trigger 列表 — 例如: figures 只找到 4 / canon 只 6 / verified_primary 35%}).
继续走 wave 2 + 网络搜会越搜越偏 SEO 农场, 蒸出来的 OS 厚度会受限.

我建议先停一下, 问你 3 件事 — 你给一个能挖深的素材就比我在网上扫 1000 篇高质量:

1) 你公司 / 团队 / 你自己有没有内部 wiki / SOP / 操作手册? 粘贴 1-2 个核心文档就行
2) 你订阅 / 关注的 niche channel — Slack 群 / Discord / 微信群 / 公众号 / X 私圈? 给我 2-3 个名字
3) 你做过的实战 case study (匿名化即可) — 比如「我去年帮 X 客户解决 Y 问题, 走的是 Z 路径」, 1-2 个

任意一项有就好. 不全有也行, 我会照常推进, 但 SKILL.md 的诚实边界节会标明数据厚度.」
```

### Cold_too_thin (≥ 3 thresholds 触发) 额外路径

```
ASSISTANT (cold_too_thin):
「{industry} 这一行公开材料**非常薄** (3+ 维度都不足). 即使你给我内部资料, 我也会
在最终 SKILL.md 的诚实边界节明确标「跨度有限 / 厚度受限」, 否则会误导后来用户.

两个方向你选一个:
A) 接受这个限制, 我们做出来一份诚实标记弱点的 skill — 还是有用, 但**不要期望**
   像 'LLM agent infra' 这种公开材料丰富的领域那种厚度
B) 把 industry 改宽一点 — 比如 '{建议的临近更宽行业}' (但仍贴近你的实际工作),
   能蒸出更厚的 OS, 你再在使用时收窄到当前细分

回 A / B / 或继续给我 3 件内部材料强行走 A.」
```

### 用户回内部素材时的处理

- 全部按 `local_materials.mode = mixed` 处理, paths 写入 intake.json
- 标 `cold_deep_mode_engaged: true` 在 intake.json 顶层
- 重新启动 wave 2 之前**先**让用户素材进 source pool — 它们权重最高 (verified_primary)
- 跑 surrogate collectors (见 prompts/research/*.md 的 Surrogate Sources Policy 节)
