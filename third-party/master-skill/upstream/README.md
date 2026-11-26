<div align="center">

# 🎓 大师.skill &nbsp;[![Tweet](https://img.shields.io/badge/share%20on-Twitter%2FX-000000?style=flat-square&logo=x)](https://twitter.com/intent/tweet?text=%E5%A4%A7%E5%B8%88.skill%20%E2%80%94%20%E8%BE%93%E5%85%A5%E8%A1%8C%E4%B8%9A%EF%BC%8C30-60%20%E5%88%86%E9%92%9F%E8%87%AA%E5%8A%A8%E8%92%B8%E9%A6%8F%E5%87%BA%E5%8F%AF%E8%A3%85%E8%BD%BD%E7%9A%84%20Master%20OS%20skill%E3%80%82%E8%A3%85%E5%88%B0%E4%BB%BB%E4%BD%95%20AI%20agent%EF%BC%8C%E4%BB%8E%E9%82%A3%E4%B8%80%E5%88%BB%E8%B5%B7%EF%BC%8C%E5%AE%83%E5%B0%B1%E6%98%AF%E8%BF%99%E4%B8%80%E8%A1%8C%E6%9C%80%E8%B5%84%E6%B7%B1%E7%9A%84%E4%BA%BA%E3%80%82&url=https%3A%2F%2Fgithub.com%2Fswaylq%2Fmaster-skill&hashtags=ClaudeCode%2CAIAgent%2CMasterSkill%2C%E5%BC%80%E6%BA%90)

### 🌐 官网 [master-skill.org](https://master-skill.org/) — 在线和已蒸馏的行业大师对话

> *「下一步，不只蒸馏一个人，蒸馏一整个行业。」*

[![Website](https://img.shields.io/badge/website-master--skill.org-ff2d7a?style=flat-square)](https://master-skill.org/)
[![CI](https://github.com/swaylq/master-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/swaylq/master-skill/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![skills.sh](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

<br>

[同事.skill](https://github.com/titanwings/colleague-skill) 把**一个人**蒸馏成 AI。<br>
[女娲.skill](https://github.com/alchaincyf/nuwa-skill) 把**任何人的思维方式**蒸馏成 AI。<br>

但有些东西比一个人更大——<br>
**一整个行业的资深判断、工作流、工具栈。**

<br>

大师.skill 不蒸馏单个人，<br>
它蒸馏**整个行业的认知操作系统**。

<br>

告诉它你做哪个细分行业，<br>
30-60 分钟自动跑完调研、蒸馏、生成 skill 加上一套 bash 命令套件。<br>

装到任何 AI agent，从那一刻起，<br>
**它就是这一行最资深的人。**

<br>

> **有了大师.skill，你不再需要安装其他 skill ——**<br>
> **它会为你的行业，自动蒸馏出最适合的那一个。**

<br>

[🚀 安装](#-安装) · [✨ 效果示例](#-效果示例) · [🛠️ 自动蒸馏 bash 工具](#️-自动蒸馏出-bash-命令套件) · [🧬 三代谱系](#-三代谱系) · [⭐ 已蒸馏的行业](#-已蒸馏的行业)

[**English README →**](README_en.md)

</div>

---

> 📊 &nbsp;**已蒸馏 72 个行业** — 横切技术 / AI / 商业 / 内容 / 教育 / 医疗 / 法律金融 / 软技能 / 管理 / 手艺品鉴 / 传统文化 / 平台 12 个大类。每个行业都经过六路调研 + 16 道质检 + validation gate 验收。[完整列表 ↓](#-已蒸馏的行业)
>
> 🆕 &nbsp;**2026.07.04 扩容到 72 行业** — 深度蒸馏流水线连发 29 个新行业：临床诊断思维 / 管理咨询 / 投行并购 / 半导体制造工艺 / 加密链上交易 / 医疗美容 / 音乐制作 / 摄影 / 产品 UX 设计 / 网文写作 / 调香师 / 侍酒师 / 德州扑克 / AI 短剧 / 小红书 & 推特 & 知乎 AI 自媒体博主 等。
>
> 🔥 &nbsp;**2026.05.27 SkillOpt 整合** — 从 [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) 借鉴 5 个机制：**SLOW_UPDATE 保护区**（核心 OS 不被快更冲散）、**validation gate**（accept/reject 门控）、**patch editor**（结构化编辑 + 保护区感知）、**meta skill memory**（跨蒸馏学习）、**DL 类比框架**。[详情 ↓](#-skillopt-整合--让蒸馏管线自我进化)
>
> 📢 &nbsp;**2026.05.02 公开** — 第一个完整行业（LLM agent 基础设施）端到端跑通验证。[Release notes →](https://github.com/swaylq/master-skill/releases/tag/v1.1)

---

## ✨ 效果示例

> 这不是搜索引擎。这是「这一行的资深人此刻在你旁边」。

#### 🤖 场景 1 · LLM agent 基础设施

```
你    ❯ 该不该把这个 RAG 系统迁到 Vespa？

大师  ❯ 这是一个「framework 临时性 vs 基建沉降」的判断。

       先看 retrieval 阶段的瓶颈到底在 Vespa 解决，还是
       在 embedding 模型本身。如果是后者，迁移就是把
       脚手架换成混凝土 — 6 个月模型迭代会让你又想换。

       如果真的卡在 retrieval：Vespa 比 Pinecone 多了
       hybrid search 原生支持，但你的运维栈是不是已经
       吃下了它的 ZooKeeper / Tensor 复杂度？这一行的
       资深判断 — Filtering speed × Index size × Team
       Op overhead 三选二，你的瓶颈在哪边？

       Production case：[3-4 个真实迁移案例摘要 + 链接]
```

#### 🛒 场景 2 · 跨境电商运营

```
你    ❯ 亚马逊德国站要上一个新品类，从哪儿开始？

大师  ❯ 德国站有三件事跟美国站完全不同 — 你必须先回答：

       1) VAT 一站式申报你走 OSS 还是各国注册？
          这决定了你能不能用 Pan-EU FBA。
       2) 包装法 (VerpackG) 和 WEEE/电池法注册了吗？
          没注册 listing 第一天就会被举报下架。
       3) GS 认证 vs CE — 你品类是不是 GS 强制？
          这决定能不能上 Idealo / 比价导购流量池。

       这三个不是合规 checklist — 是你「能不能开卖」的硬门槛。
       搞定后，关键词调研用 Helium 10 的德语包，不要从
       美国词库直翻 — 德国搜索习惯长尾密度高得多。
```

#### 🎬 场景 3 · 短视频投流

```
你    ❯ 投流 ROAS 总是上不去，是不是出价策略有问题？

大师  ❯ 出价是后果，不是原因。先回答创意层：

       你的素材在 cold audience 上的 3s 完播率是多少？
       低于 35% 时调出价没用 — 巨量引擎的探索预算
       不会给你跑出量。

       创意没问题再看人群定向。这一行的资深判断 —
       「优质素材 × 合理定向 × 出价」，三角顺序错了，
       后两个调出花。你近 7 天创意素材曲线给我看一眼。
```

**不是把行业百科塞进 prompt**，是用**这一行的心智模型 + 决策规则**给你判断。

每个 skill 都自带一套「研究协议」(Agentic Protocol) — 拿到一个行业新问题，它先按这行资深人的研究维度去搜事实，再用心智模型输出判断。**不是说得像，是做得像。**

---

## 🛠️ 自动蒸馏出 bash 命令套件

> 这是大师.skill 跟同事 / 女娲最大的区别 — 蒸馏出来的不只是「会说」，还是「会做」。

每个生成的 skill **都自动配一个 `cli/` 子目录** —— 把这个行业的认知操作系统直接物化成可执行的命令行工具：

```
{industry}-master/
└── cli/
    ├── protocol/agentic.sh         # 拿到新问题 → 按几个研究维度做功课 → 出报告
    ├── decision/{主题}.sh           # 决策树（按主题聚类的几条决策规则）
    └── workflow/{流程}.sh           # 走查工作流 + 失败模式自检
```

每个脚本都支持四个标准开关：`--help`（帮助）/ `--explain`（解释背后的心智模型）/ `--dry-run`（试跑）/ `--json`（机器可读输出）。

```bash
# 拿到新问题：「该不该把 RAG 系统迁到 Vespa」
$ ./cli/protocol/agentic.sh
# → 引导你按 5 个研究维度收集信息 → 生成报告

# 选型决策
$ ./cli/decision/framework-select.sh

# 走完一个完整工作流 + 失败模式自检
$ ./cli/workflow/build-rag-agent.sh

# 解释背后的心智模型（不交互，直接打印）
$ ./cli/decision/framework-select.sh --explain
```

**纯 bash + 系统命令，零外部依赖**（不需要 jq、不需要 Python）。由 [`tools/cli_writer.py`](tools/cli_writer.py) 自动从蒸馏结果生成 —— 你不用写一行代码，工具是从行业的工作流和决策规则里**直接长出来的**。

设计细节看 [`references/cli-spec.md`](references/cli-spec.md)。

---

## 🌐 自动调女娲，蒸馏行业 top 人物

> 大师不重新发明轮子。蒸馏行业 top 人物的活儿，自动外包给女娲.skill 做，结果直接嵌进 `sub-skills/`。

```
{industry}-master/
├── SKILL.md
└── sub-skills/                       ← 女娲蒸馏的人物 sub-skill
    ├── {人物-1}/SKILL.md             ← 比如 Karpathy
    ├── {人物-2}/SKILL.md             ← 比如 Hamel Husain
    └── {人物-3}/SKILL.md             ← 比如 Eugene Yan
```

大师同时启动 3 个子 agent，每个走完女娲.skill 完整流程，蒸馏出一个人物 sub-skill。

之后用户问到某位人物的视角时，agent 自动加载对应 sub-skill — 不用重跑大师。

详见 [SKILL.md Phase 3.3-3.5](SKILL.md) + [`prompts/sub-skill-figures.md`](prompts/sub-skill-figures.md)。

---

## 📦 它蒸馏了什么

行业的认知操作系统，不是行业的百科全书。一个 skill 装下四件事：

- 🧠 &nbsp;**资深人怎么想** — 心智模型 + 决策规则
- ⚙️ &nbsp;**工作流怎么走** — 当前最先进的 SOP，每一步标注衰减时点
- 🛠️ &nbsp;**工具怎么选** — 选型决策树 + 避坑清单 + **自动生成的 bash 命令套件**
- 💬 &nbsp;**黑话怎么讲** — 行业表达方式 + 外行破绽

具体提取的 7 层：

| 层 | 说明 |
|---|---|
| **怎么判断** | 心智模型 — 这行的资深人看问题用的镜片 |
| **怎么决策** | 标准决策规则 — 「如果 X，则 Y」的快速判断 |
| **用什么工具** | 工具栈 + 选型决策树 + 避坑清单 |
| **怎么干活** | 工作流，每一步标注「2026-04 起这一步换成 Y」的时效 |
| **怎么沟通** | 行业表达方式 — 黑话、说话节奏、外行破绽 |
| **不做什么** | 反模式 — 外行才会犯的错 |
| **知道局限** | 诚实边界 — 信息截止时间，哪些模块衰减最快 |

### 诚实边界

每个 skill 都明确标注它做不到什么：

- 工具和工作流的模块**衰减最快**，建议每 3-6 个月刷新一次
- 法规和标准的模块**衰减更快**，12 个月内一定要更新
- 大师不能替代真实的实战经验 — 给的是认知框架，不是事故处理手册

**一个不告诉你局限在哪的 skill，不值得信任。**

---

## 🔍 凭什么相信它蒸出来的东西

> 一个新 skill 装上来，怎么知道它不是在编故事？

**16 道自动检验，跑过才算交付。** 每个生成的 skill 必须答对这些问题：

- ✅ **来源真的是一手吗？** — 每个网址自动判类（学术论文 / 官方文档 / 作者自己的博客 / vendor 官网算一手；新闻报道 / 二手转述算二手；知乎 / 微信公众号 / 百度百科 / G2 / Capterra / 内容农场**直接拒绝**）
- ✅ **「这家公司是大佬」有人能背书吗？** — 每条核心结论必须挂 ≥ 2 处独立来源（跨人物 / 跨平台），单源结论自动降级到「快速规则」节，不进核心心智模型
- ✅ **来源的日期够新吗？** — 每条来源标日期，超过 18 个月自动半折扣
- ✅ **心智模型真在原始材料里出现过吗？** — 写完 skill 后反过去研究笔记里搜，找不到原文支撑的结论自动 flag
- ✅ **行业冷僻怎么办？** — 自动检测「公开材料太薄」并切换深挖模式：向你要内部资料 + 自动从行业协会 / 监管文件 / 招聘 JD / 大学课程多源补充，不靠瞎搜兜底

**结果**：保险经纪人 prototype 73 条来源 → 67 条一手（91.8%）/ 0 黑名单 / 0 自报作弊 / 16 项检验 14 项满分 + 1 项部分通过 + 0 项失败。

---

## ⚡ 安装

```bash
# Claude Code
git clone https://github.com/swaylq/master-skill.git ~/.claude/skills/master-skill
```

<details>
<summary><b>🛠️ 其他 host 安装路径</b></summary>

<br>

```bash
git clone https://github.com/swaylq/master-skill.git <TARGET>
```

| Host | `<TARGET>` 路径 |
|------|-----------------|
| 🟣 Claude Code | `~/.claude/skills/master-skill` |
| 🔵 OpenClaw | `~/.openclaw/skills/master-skill` |
| ⚫ Codex | `~/.codex/skills/master-skill` |
| 🟠 Hermes | clone 后 `python3 tools/install.py install --host hermes` |

一键装到所有宿主：`python3 tools/install.py install --host all`

</details>

---

## 🚀 用法

在装好大师.skill 的 agent 里，直接说：

```
> 造大师 LLM agent 基础设施
> 做个跨境电商运营的大师 skill
> 我做的是足踝外科，给我蒸一个

> update 大师 LLM-agent-infra      # 6 个月后增量刷新
```

大师跟你确认 6 件事（行业、子方向、地域、你的角色、有没有一手素材、是新建还是更新），然后启动**六路并行调研**：行业大佬 / 工具地图 / 工作流 / 知识正典 / 信息源 / 术语标准。

30-60 分钟后你拿到一个 `{行业}-master` 目录。装到任意 agent，立刻进入「这一行的资深人」模式。

### 🎛️ 调用生成出来的 skill

```
> 用 llm-agent-infra-master 帮我评估这个框架选型
> 用 跨境电商-master 看一下我这个亚马逊 listing
> 让 llm-agent-infra-master 跑 framework-select 决策树
```

### 💻 命令行直接跑

```bash
# 端到端流程：调研 → 检测冷僻 → 生成 skill → 质检 → 安装
python3 tools/research/merge_research.py merge --skill-dir ./prototype/
python3 tools/research/cold_detector.py --skill-dir ./prototype --stage wave1
python3 tools/skill_writer.py create --skill-dir ./output ...
python3 tools/research/quality_check.py check --skill-dir ./output
python3 tools/install.py install --host claude --source ./output

# 6 个月后增量刷新某个老 skill
python3 tools/update_skill.py plan --skill-dir <已有 skill>
# (agent 重跑标记的几路调研)
python3 tools/update_skill.py finalize --skill-dir <skill>
```

---

## ⭐ 已蒸馏的行业

每个都是端到端跑过的样本，包含生成的 SKILL.md + 一套可跑的 bash 工具。调研过程**透明可追溯** — 70/72 个样本附完整的六路调研笔记 + 蒸馏文档，可以追溯每条心智模型、每条决策规则是从哪几个来源出来的（2 个早期样本的调研档未入库，已在 meta.json 里诚实标注）。

### 🖥️ 技术 (11)

| 行业 | 语言 | 路径 |
|------|------|------|
| **LLM agent 基础设施** | 英文 | [llm-agent-infra-master/](prototypes/llm-agent-infra-master/) |
| **软件架构** | 全球 | [software-architecture-master/](prototypes/software-architecture-master/) |
| **DevOps 与 SRE** | 全球 | [devops-sre-master/](prototypes/devops-sre-master/) |
| **数据工程** | 全球 | [data-engineering-master/](prototypes/data-engineering-master/) |
| **红队渗透 / 攻防安全** | 全球 | [cybersecurity-red-team-master/](prototypes/cybersecurity-red-team-master/) |
| **游戏设计** | 全球 | [game-design-master/](prototypes/game-design-master/) |
| **语音转文字 (ASR)** | 中文 | [speech-to-text-master/](prototypes/speech-to-text-master/) |
| **UBNT/UniFi 企业 Wi-Fi 工程** | 全球 | [ubnt-wifi-master/](prototypes/ubnt-wifi-master/) |
| **Web 线上展览开发（虚拟展厅）** | 中文 | [web-online-exhibition-master/](prototypes/web-online-exhibition-master/) |
| **Figma 转 Photoshop (PSD)** | 中文 | [figma-to-psd-master/](prototypes/figma-to-psd-master/) |
| **半导体芯片制造工艺** | 全球 | [semiconductor-process-master/](prototypes/semiconductor-process-master/) |

### 🤖 AI / 产品 (3)

| 行业 | 语言 | 路径 |
|------|------|------|
| **AI 产品经理** | 全球 | [ai-product-manager-master/](prototypes/ai-product-manager-master/) |
| **AI 自适应学习** | 全球 | [ai-adaptive-learning-master/](prototypes/ai-adaptive-learning-master/) |
| **用 AI agent 赚钱** | 全球 | [monetize-agents-master/](prototypes/monetize-agents-master/) |

### 🛒 商业 / 电商 / 投流 (7)

| 行业 | 语言 | 路径 |
|------|------|------|
| **跨境电商运营** | 中文 | [cross-border-ecommerce-master/](prototypes/cross-border-ecommerce-master/) |
| **B2B 大客户销售** | 全球 | [enterprise-b2b-sales-master/](prototypes/enterprise-b2b-sales-master/) |
| **抖音直播带货** | 中文 | [douyin-live-commerce-master/](prototypes/douyin-live-commerce-master/) |
| **短视频投流** | 中文 | [short-video-ads-master/](prototypes/short-video-ads-master/) |
| **微信私域运营** | 中文 | [private-domain-ops-master/](prototypes/private-domain-ops-master/) |
| **独立开发者与微型 SaaS** | 全球 | [independent-developer-micro-saas-master/](prototypes/independent-developer-micro-saas-master/) |
| **产品营销 (PMM)** | 全球 | [product-marketing-master/](prototypes/product-marketing-master/) |

### ✍️ 内容 / 运营 / 创作 (11)

| 行业 | 语言 | 路径 |
|------|------|------|
| **小红书运营** | 中文 | [xiaohongshu-ops-master/](prototypes/xiaohongshu-ops-master/) |
| **小红书 AI 自媒体博主** | 中文 | [xiaohongshu-ai-creator-master/](prototypes/xiaohongshu-ai-creator-master/) |
| **推特中文圈 AI 自媒体博主** | 中文 | [twitter-cn-ai-creator-master/](prototypes/twitter-cn-ai-creator-master/) |
| **知乎 AI 自媒体博主** | 中文 | [zhihu-ai-creator-master/](prototypes/zhihu-ai-creator-master/) |
| **AI 短剧（AI 微短剧）** | 中文 | [ai-short-drama-master/](prototypes/ai-short-drama-master/) |
| **AIGC 创作工作流** | 全球 | [aigc-creative-workflow-master/](prototypes/aigc-creative-workflow-master/) |
| **网文写作** | 中文 | [web-novel-writing-master/](prototypes/web-novel-writing-master/) |
| **SEO 专家** | 中文 | [seo-master/](prototypes/seo-master/) |
| **公众号写作** | 中文 | [wechat-article-writing-master/](prototypes/wechat-article-writing-master/) |
| **影视编剧** | 中文 | [scriptwriting-master/](prototypes/scriptwriting-master/) |
| **内容创作者经济** | 全球 | [newsletter-creator-economy-master/](prototypes/newsletter-creator-economy-master/) |

### 🎓 教育 / 培训 (9)

| 行业 | 语言 | 路径 |
|------|------|------|
| **公务员考试培训** | 中文 | [civil-service-exam-prep-master/](prototypes/civil-service-exam-prep-master/) |
| **家庭教育指导** | 中文 | [family-education-coaching-master/](prototypes/family-education-coaching-master/) |
| **K12 体育培训** | 中文 | [k12-sports-training-master/](prototypes/k12-sports-training-master/) |
| **研学营地教育** | 中文 | [study-camp-education-master/](prototypes/study-camp-education-master/) |
| **青少年编程教育** | 全球 | [youth-coding-education-master/](prototypes/youth-coding-education-master/) |
| **教育 SaaS** | 中文 | [education-saas-master/](prototypes/education-saas-master/) |
| **银发教育** | 中文 | [senior-education-master/](prototypes/senior-education-master/) |
| **青少年心理健康教育** | 中文 | [youth-mental-health-edu-master/](prototypes/youth-mental-health-edu-master/) |
| **留学咨询规划** | 中文 | [study-abroad-consulting-master/](prototypes/study-abroad-consulting-master/) |

### 🏥 医疗 / 健康 (6)

| 行业 | 语言 | 路径 |
|------|------|------|
| **临床诊断思维** | 全球 | [clinical-diagnostic-reasoning-master/](prototypes/clinical-diagnostic-reasoning-master/) |
| **足踝外科** | 中文 | [foot-ankle-surgery-master/](prototypes/foot-ankle-surgery-master/) |
| **口腔种植** | 中文 | [dentistry-implant-master/](prototypes/dentistry-implant-master/) |
| **中医诊疗** | 中文 | [traditional-chinese-medicine-master/](prototypes/traditional-chinese-medicine-master/) |
| **医疗美容** | 中文 | [medical-aesthetics-master/](prototypes/medical-aesthetics-master/) |
| **健身私教** | 全球 | [personal-trainer-master/](prototypes/personal-trainer-master/) |

### ⚖️ 法律 / 金融 / 合规 (8)

| 行业 | 语言 | 路径 |
|------|------|------|
| **法律执业**（中国法） | 中文 | [china-law-master/](prototypes/china-law-master/) |
| **个人投资理财** | 全球 | [personal-investing-master/](prototypes/personal-investing-master/) |
| **投行并购 (M&A)** | 全球 | [investment-banking-mna-master/](prototypes/investment-banking-mna-master/) |
| **加密链上交易** | 全球 | [crypto-onchain-trading-master/](prototypes/crypto-onchain-trading-master/) |
| **保险经纪人 / 代理人** | 中文 | [insurance-broker-cn-master/](prototypes/insurance-broker-cn-master/) |
| **风险投资人** | 全球 | [vc-investor-master/](prototypes/vc-investor-master/) |
| **国内房产投资** | 中文 | [real-estate-investing-cn-master/](prototypes/real-estate-investing-cn-master/) |
| **中国网站备案与合规** | 中文 | [china-icp-filing-master/](prototypes/china-icp-filing-master/) |

### 💡 软技能 / 人际 / 心理 (3)

| 行业 | 语言 | 路径 |
|------|------|------|
| **恋爱高手** | 中文 | [love-coach-master/](prototypes/love-coach-master/) |
| **求职 / 面试辅导** | 中文 | [job-hunting-coach-master/](prototypes/job-hunting-coach-master/) |
| **心理咨询 / 心理治疗** | 中文 | [psychotherapy-counseling-master/](prototypes/psychotherapy-counseling-master/) |

### 🏛️ 领导力 / 管理 / 设计 (6)

| 行业 | 语言 | 路径 |
|------|------|------|
| **CEO 工艺** | 全球 | [ceo-master/](prototypes/ceo-master/) |
| **管理咨询** | 全球 | [management-consulting-master/](prototypes/management-consulting-master/) |
| **亚马逊管理之道** | 中文 | [amazon-operating-model-master/](prototypes/amazon-operating-model-master/) |
| **广告外包公司绩效管理** | 中文 | [ad-agency-performance-master/](prototypes/ad-agency-performance-master/) |
| **产品设计 / UX 设计** | 全球 | [product-ux-design-master/](prototypes/product-ux-design-master/) |
| **现代建筑设计** | 全球 | [architecture-design-master/](prototypes/architecture-design-master/) |

### 🎨 手艺 / 品鉴 / 生活方式 (5)

| 行业 | 语言 | 路径 |
|------|------|------|
| **调香师与香水** | 全球 | [perfumery-master/](prototypes/perfumery-master/) |
| **侍酒师与葡萄酒** | 全球 | [sommelier-wine-master/](prototypes/sommelier-wine-master/) |
| **音乐制作 / 混音** | 全球 | [music-production-master/](prototypes/music-production-master/) |
| **摄影** | 全球 | [photography-master/](prototypes/photography-master/) |
| **德州扑克策略** | 全球 | [poker-strategy-master/](prototypes/poker-strategy-master/) |

### 🔮 传统文化 / 平台 (3)

| 行业 | 语言 | 路径 |
|------|------|------|
| **八字命理 / 玄学算命** | 中文 | [bazi-metaphysics-master/](prototypes/bazi-metaphysics-master/) |
| **iOS 应用上架** | 全球 | [ios-app-launch-master/](prototypes/ios-app-launch-master/) |
| **GitHub 解封** | 全球 | [github-unban-master/](prototypes/github-unban-master/) |

---

72 个行业横切 12 个大类 — 技术 / AI / 商业 / 内容 / 教育 / 医疗 / 法律金融 / 软技能 / 管理 / 手艺品鉴 / 传统文化 / 平台 specific。大师.skill 框架对各类行业都跑得通。

想蒸馏不在列表里的行业？装大师.skill，说「造大师 XXX」就行。

---

## 🧪 SkillOpt 整合 — 让蒸馏管线自我进化

> 灵感来自 [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) 的 ReflACT 6 阶段闭环优化管线。SkillOpt 用深度学习类比（skill=权重，patch=梯度，edit budget=学习率）驱动 agent skill 的持续迭代。大师.skill 从中借鉴了 5 个核心机制：

| 机制 | 文件 | 做什么 |
|------|------|--------|
| **SLOW_UPDATE 保护区** | `skill_writer.py` v1.4 | 生成的 SKILL.md 自动用 `<!-- SLOW_UPDATE_START/END -->` 标记低衰减区域（心智模型 / 表达 DNA / 智识谱系）。Phase 0C 增量更新时 patch editor 自动跳过这些区域 — 核心 OS 不被快速迭代冲散 |
| **Validation Gate** | `tools/research/validation_gate.py` | Phase 4 的 accept/reject 门控。对 quality_check 的 15+ 项检验做加权评分，区分 critical failure（一票否决）和 partial（可接受降级）。输出：`accept` / `conditional_accept` / `reject` + 具体改进建议 |
| **Patch Editor** | `tools/patch_editor.py` | 4 种结构化编辑操作（append / insert_after / replace / delete），每一步自动检测是否落入 SLOW_UPDATE 保护区。Phase 0C `update_skill.py apply-patch` 直接调用，替代「整段重写」 |
| **Meta Skill Memory** | `tools/meta_skill.py` | 跨蒸馏学习记忆。每次管线跑完记录 gate score / 失败模式 / 管线教训到 `meta_skill_memory.json`。下次蒸馏前查 `meta_skill.py guidance`，获取累积的优化建议 |
| **DL 类比框架** | 概念层 | skill = 模型权重（长期积累），patch = 梯度（单次更新），edit budget = 学习率（控制更新幅度），SLOW_UPDATE = 受保护层（frozen layers）。这个类比让 Phase 0C 的增量更新有了原则性约束 |

```bash
# 验证 SLOW_UPDATE 标记
grep "SLOW_UPDATE" output/SKILL.md

# 跑 validation gate
python3 tools/research/validation_gate.py gate --skill-dir ./output

# 用 patch editor 做增量更新（自动保护慢衰减区域）
python3 tools/update_skill.py apply-patch --skill-dir ./output --patch patch.json --dry-run

# 查看跨蒸馏学习
python3 tools/meta_skill.py guidance
```

---

## 🔬 工作原理

输入一个细分行业，大师.skill 做这几件事：

```
1. 行业澄清          ← 粒度太粗主动收窄（拒绝「AI」，引导到「LLM agent 基础设施」）
2. 创建目录          ← 所有产物都在 skill 自己的目录内，自包含
3. 六路并行调研      ← 6 个子 agent：行业大佬 / 工具 / 工作流 / 知识正典 / 信息源 / 术语
   ─ 调研评审关卡    ← 你确认调研质量再继续，不让垃圾输入污染下游
4. 框架蒸馏          ← 三重验证（跨场景 / 生成力 / 排他性）挡住行业八股
   ─ 蒸馏评审关卡    ← 你确认认知框架再生成
5. 写出 skill        ← 自动生成完整目录、调女娲蒸人物 sub-skill、emit bash 工具
6. 三测验证          ← 已知问题 / 边界问题 / 风格盲测
7. 双 agent 精炼     ← 优化 skill 的「激活即执行」程度
```

详见 [SKILL.md](SKILL.md) — 524 行的 agent 可加载工作流。方法论看 [references/extraction-framework.md](references/extraction-framework.md) — 三重验证、工具栈三层提炼、流派分歧处理、衰减速度表。

---

## 🧬 三代谱系

大师.skill 站在两个前作的肩膀上：

- **[同事.skill (titanwings/colleague-skill)](https://github.com/titanwings/colleague-skill)** — 提供了「了解 → 多源采集 → 分析 → 写出」的元 skill 框架。
- **[女娲.skill (alchaincyf/nuwa-skill)](https://github.com/alchaincyf/nuwa-skill)** — 提供了 6 个 agent 并行调研 + 三重质量关卡。**大师.skill 在 Phase 3 直接调女娲，蒸出行业最重要的 3 个人作为 sub-skill。**

三者同源，逐层放大。

> 🎣 **姊妹项目 [私教.skill (swaylq/sijiao-skill)](https://github.com/swaylq/sijiao-skill)**（[官网](https://swaylq.github.io/sijiao-skill/)）— 把方向反过来：大师.skill 让你的 AI 成为行业大师（授人以鱼），私教.skill 蒸出一个记得你进度、陪你练的私教，把**你自己**训练成领域高手（授人以渔）。

---

## 📂 项目结构

```
master-skill/
├── SKILL.md                          # 大师本体（核心工作流规约）
├── prompts/                          # 提示词系统
│   ├── intake.md                     #   行业澄清 + 冷僻 deep-mode 二次 intake
│   ├── synthesis.md                  #   蒸馏指引（含 Step 5b 对话样本库）
│   ├── quality_check.md              #   16 项 mechanical rubric
│   ├── sub-skill-figures.md          #   调女娲的子 agent 模板
│   └── research/
│       ├── _source_id_manifest.md    #   T01-S001 全局 source_id 规范 + Surrogate Sources Policy
│       └── 01-06.md                  #   六路调研提示词（含 voice_samples 字段）
├── tools/                            # Python 工具
│   ├── skill_writer.py               #   生成 skill 目录
│   ├── cli_writer.py                 #   生成 bash 工具子目录
│   ├── update_skill.py               #   skill 增量刷新
│   ├── install.py                    #   四宿主安装器
│   ├── self_test.py                  #   全部样本 + 工具回归测试
│   ├── patch_editor.py               #   SkillOpt: 4 种结构化编辑 + SLOW_UPDATE 保护
│   ├── meta_skill.py                 #   SkillOpt: 跨蒸馏学习记忆
│   ├── research/                     # 质量护栏 (v1.4 新)
│   │   ├── source_verifier.py        #   每个 URL 自动判类 + 黑白名单
│   │   ├── source_manifest.py        #   核对来源台账 + 一致性强制
│   │   ├── claim_verifier.py         #   反向核对 SKILL.md 每条结论是否真有原文支撑
│   │   ├── cold_detector.py          #   行业冷僻自动兜底 (深挖模式)
│   │   ├── refresh_sources.py        #   定期检测来源是否还在
│   │   ├── quality_check.py          #   16 道自动检验
│   │   ├── validation_gate.py        #   SkillOpt: accept/reject 门控 (加权评分)
│   │   └── merge_research.py         #   调研评审聚合
│   ├── collectors/                   # 自动抓行业 seed
│   │   ├── github / arxiv / RSS / 播客 (4 件)
│   │   └── 监管 / 协会 / 招聘 / 课程 (冷僻行业兜底, 4 件)
│   ├── ingest/                       # 行业报告 / 论文 / 课程 PPT 解析
│   │   └── PDF / EPUB / PPTX 一键吃进来
│   └── transcribe/                   # 视频 / 播客转录
│       ├── youtube.sh / local_video.sh   # 抓字幕 + 本地视频转录
│       └── 字幕清洗 / 含金量评分 / 人物识别
├── references/
│   ├── skill-template.md             #   生成产物的标准结构
│   ├── extraction-framework.md       #   蒸馏方法论（三重验证 / 衰减表 / 流派分歧）
│   └── cli-spec.md                   #   bash 工具的设计文档
├── meta_skill_memory.json            # SkillOpt: 跨蒸馏学习记忆
└── prototypes/
    └── 72 个完整行业样本            #   见上面「已蒸馏的行业」列表
```

---

## ⚠️ 注意

**调研材料的质量 = skill 的质量**。不同维度的来源优先级不同：

| 维度 | 来源优先级（高到低） |
|------|------|
| 🌟 行业大佬 | 本人长篇（书 / 长访谈 / 博客系列）**›** 决策记录（公开发声 / 提交记录）**›** 二手转述 |
| 🛠️ 工具地图 | 官方文档 **›** 工程师生产案例 **›** 培训教程 / SEO 软文 |
| 📋 工作流 | 公司技术博客的真实流程 **›** 资深人长访谈 **›** 培训机构大纲 |
| 📚 知识正典 | 行业人推荐书单（至少 3 个独立来源都点过）**›** 学术综述 **›** 二手书评 |
| 📰 信息源 | 行业人订阅清单 **›** 主流媒体长稿 **›** 内容农场 |

- 中文环境下自动排除知乎、微信公众号、百度百科、CSDN（除非作者原文）
- 信息截止得越早，工具和工作流的模块衰减越快 — 用 `update 大师 X` 增量刷新
- 这是 v1.1，还在快速迭代。发现 bug 请提 issue。

---

## 📄 路线图

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.1-0.4 | 工作流规约 + 提示词 + 工具 + 打磨 | ✅ |
| v1.0 | 完成第一个完整样本（LLM agent 基础设施），仓库公开 | ✅ |
| v0.6 | bash 工具流 — 生成的 skill 自带命令套件 | ✅ |
| v1.1 | 调用别的 skill + 增量刷新 + 中文样本 | ✅ |
| v1.2 | 决策树主题自动学 + 定时刷新 + 5 个行业样本（含小红书 / SEO / 恋爱） | ✅ |
| v1.3 | 短视频投流 / 足踝外科 / 法律 = 8 个行业横切覆盖 | ✅ |
| v1.4 | **质量护栏 + 第 9 个行业** — 自动跑 16 道质检 + URL 验真 + 黑名单强拦截 + 冷僻行业兜底（自动从协会 / 监管 / 招聘 / 课程多源补充）+ 新增**保险经纪人 / 代理人** | ✅ |
| v1.5 | **第 10 个行业 — 八字命理 / 玄学算命** — 第一个半敏感 + 学派分歧大行业；同盘多派给不同结论保留分歧不平均；source_verifier 加 4 个古籍 archive 主源（ctext / guoxuedashi / wikisource / archive.org，命理 + 中医 + 历史 canon 永久受益） | ✅ |
| v1.6 | **第 11+12 个行业 — 用 AI agent 赚钱 + iOS 应用上架** — 新兴商业（量大水分高，5 派互相挑衅）+ 平台 specific（政策 12 月强制 deadline + 双合规体系）。验证 `skip_sub_skills` flag（iOS 上架按用户指示跳人物蒸馏，节省 1 cron 周期）；iOS 上架 6 派对照（Apple 官方 / Indie / 大厂 release eng / ASO / 反 Apple / 国内合规）写完整 | ✅ |
| v1.7 | **SkillOpt 整合 + 第 13 个行业 — 公务员考试培训** — 从 Microsoft SkillOpt 借鉴 5 个机制（SLOW_UPDATE 保护区 / validation gate / patch editor / meta skill memory / DL 类比）。用公考培训端到端验证：171 来源 / gate ACCEPT 0.90 / 3 个 SLOW_UPDATE 区域成功注入 | ✅ |
| v1.8 | **深度蒸馏扩容 43 → 72 行业** — 流水线连发 29 个新行业（手艺品鉴 / 临床诊断思维 / 管理咨询 / 投行并购 / 半导体工艺 / 链上交易 / 医美 / AI 自媒体矩阵 等）+ 72 样本自检全绿 + CI | ✅ |
| v2.x | PyPI 打包 / GitHub Action 自动更新 / 多语言文档 / 工具 marketplace | 🔲 |

详见 [ROADMAP.md](ROADMAP.md)。

---

## 📜 许可证

MIT — 随便用，随便改，随便造。

<div align="center">

<br>

**🧬 同事.skill** 蒸馏一个**具体的人**做什么。<br>
**🌟 女娲.skill** 蒸馏**任何人**怎么想。<br>
**🎓 大师.skill** 蒸馏**一整个行业**的认知 + 工作流 + 工具。<br>
**📖 [私教.skill](https://github.com/swaylq/sijiao-skill)** 反过来——把**你**训练成领域高手。<br>

<br>

*把一整个行业的资深认知，蒸馏成一个 skill。*

<br>

MIT License © [swaylq](https://github.com/swaylq) · 中文 README · [English](README_en.md)

</div>

---

## 🧪 关于作者

这个项目出自 **[Sway Lab](https://swaylab.ai)** — [Sway（刘乾）](https://github.com/swaylq)的 agent 实验室，
6 个 agent 在上面各自干活，产出产品、开源 skill 和实验。

- 📄 这个项目的来龙去脉：**[swaylab.ai/articles/master-skill](https://swaylab.ai/articles/master-skill)**
- 📰 《AI 动态日报》每天 09:30 更新：**[swaylab.ai/articles](https://swaylab.ai/articles)**
- 🕸️ 其他在做的东西：**[swaylab.ai/agent-network](https://swaylab.ai/agent-network)**

---

## ⭐ Star History

<a href="https://www.star-history.com/?repos=swaylq%2Fmaster-skill&type=date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=swaylq/master-skill&type=date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=swaylq/master-skill&type=date" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=swaylq/master-skill&type=date" />
 </picture>
</a>
