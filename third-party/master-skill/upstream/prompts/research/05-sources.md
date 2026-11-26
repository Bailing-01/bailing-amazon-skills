# Track 05 — Sources Research Subagent

> Phase 1 wave 1 的第 2 路 subagent。SKILL.md Phase 1 调用本文件作为子任务模板。

## 你的任务

调研「{industry}」（locale={locale}）行业的 **持续信息源** ——这一行的资深人订阅 / 听 / 跟的渠道。

具体覆盖（按重要性）：
- Newsletter / Substack（个人或机构定期长稿）
- Podcast（深度访谈 / 圆桌 / 长 talk）
- Conference / 行业大会（年度或多次）
- Community / 社区（Discord / Slack / 专属论坛 / X 圈）
- Dataset / Benchmark（如适用 — AI / 量化金融 / 医疗影像类行业才有）

输出**不是 awesome-X URL 列表**。输出是 **「这一行的资深人**实际订阅**的渠道」+「值不值得跟 + 为什么 + 投入产出比」**，让 Phase 2 直接整合进生成 skill 的 [Sources — 信息源](../../references/skill-template.md) 节，并支持 master skill 诚实边界中「想跟最新动态，去这几处」的指引。

## 输出位置

```
{skill_dir}/references/research/05-sources.md
```

文件存在则覆盖。

## Source Manifest 引用规范 (iter 24, 强制)

详见 `prompts/research/_source_id_manifest.md`. 摘要:

1. 文件最前面写 `## Source Manifest` 表 (source_id / url / bucket / last_checked / author / note). 黑名单 URL 进表即报错; `mp.weixin.qq.com` 文章是黑名单 (但公众号的「频道身份」可作为本 track source 列表的 URL)
2. 每个 source 的 `投入产出比`, `Audience tier`, `Decay risk` 等 claim 末尾挂 `evidence: [Sxxx]`
3. URL 用 `python3 {master_skill_dir}/tools/research/source_verifier.py classify <URL>` 跑一遍取 bucket
4. Phase 4 跑 `tools/research/quality_check.py` item 13 + 14 + 15 + 16 验证
5. 冷僻行业: 大型行业会议 sponsor + sessions list + 协会会员 newsletter 作 surrogate_primary 补充

## Wave 1 加成（独立 track）

本 track 在 Phase 1 wave 1 启动，**搜索路径独立**，不依赖其他 track 输出。Wave 1 跑完后输出会作为 seed 喂给：
- Wave 2 Track 01 (figures) — newsletter 作者 / podcast 嘉宾 / conference keynote 直接是 figures 候选
- Wave 2 Track 02 (tools) — newsletter / podcast 反复评测的工具直接是 tools 候选

**这是本 track 的策略价值**：sources 是 figures + tools 的 cheapest discovery channel。本 track 调研充分 → wave 2 启动门槛降低。

## 6 步流程

### Step 1: Sources 候选清单（Wide Net）

撒大网，**目标 25-40 个候选 (跨 5 类型合并)，floor 15，<10 触发冷僻协议**。

#### 候选来源（按权重）

1. **行业大佬公开订阅 / 推荐的列表**：
   - Twitter/X bio + pinned thread 中提到的 newsletter
   - podcast 嘉宾互相 cross-recommend
   - blog post「我每周读什么」类
2. **行业经典 newsletter / podcast 主自己的「subscribed list」公开**（少数，但权重最高）
3. **GitHub awesome-X 中的 podcasts / newsletters 节**（再次过滤 ≥ 3 endorsement）
4. **Google search「{industry} newsletter」「best {industry} podcast」按发布日期 last year 排序**
5. **大型行业会议（如 KubeCon / ICML / NeurIPS / 36氪 WISE 等）的赞助商列表 + sessions list**
6. **行业专属社区的 sticky 帖子 / FAQ 中提到的 sources**

```
搜索词模板：
- en: "best {industry} newsletters", "top {industry} podcasts 2025-2026", "where to follow {industry}"
- zh-CN: "{中文行业名} 必读 newsletter"、"{中文行业名} 播客推荐"、"{中文行业名} 信息源"
- 避免：「20 个必看」类 SEO 农场
```

#### Locale-specific 候选源池

| Locale | 优先池 |
|--------|-------|
| en | Substack, Beehiiv, Patreon-paid, X-thread aggregators, podcast indexes (podchaser / listenotes) |
| zh-CN | 小宇宙（podcast）, 微信公众号 RSS-able 部分, 知识星球, 即刻，少数派, 36氪, 极客公园 |

注意：zh-CN locale 公众号本身**不是** Track 04 / Track 06 中黑名单的 source — 公众号作为 newsletter 渠道是合法的（一些 figures 的主要发声渠道），只是**不能引用公众号文章作为知识真伪的来源**（Track 06 黑名单）。**Track 05 收 source 名单 ≠ Track 06 引用文章内容**，两件事不同。

**Locale=global 的处理规则** (iter 13 新增): 当 industry 本身是 global / 跨语言时（如 LLM agent infra），**每个 type 至少 retain 1-2 个非英文 sources**（如果存在 high-quality non-en source），明确标 `geographic_focus: zh-CN | jp | ko 等`。这避免 global locale 退化为 en-only。但要警告用户：「非英文圈 sources 的 deep-fluency 期望，agent 可能不达标，需用户自己评估」。

### Step 2: 信源黑名单（针对 Track 05 特殊）

| Locale | 永不收录 |
|--------|---------|
| 通用 | 完全 marketing 推送（无内容 / 全是 promo）的 newsletter |
| 通用 | AI 合成内容 / 完全转载的「AI 摘要」podcast |
| 通用 | 已停更 > 6 月（newsletter）、停更 > 12 月（podcast）、最近一届已 > 24 月（conference） |
| zh-CN | 「日更 / 周更 但内容是知乎答案搬运」的公众号 |
| en | "AI summary podcasts" 完全用 NotebookLM / 类似工具自动生成 |

### Step 3: 每个 Source 的标准数据结构

```markdown
### {{type-icon}} {{N. Source 名称}}

- **Type**: newsletter / podcast / conference / community / dataset
- **URL**: {{primary URL}}
- **Author / Host / Maintainer**: {{name}} (与 Track 01 figures 关联，如适用)
- **Cadence**: weekly / biweekly / monthly / annually / rolling / paused (with date)
- **Last activity**: {{YYYY-MM-DD}} (最近一次发布 / 录制 / 召开)
- **Audience tier**: beginner / practitioner / senior / mixed
  - beginner = 入门讲解
  - practitioner = 在职工程师 / 专业人士的实操内容
  - senior = 资深 + 反思 + 战略级别
  - mixed = 故意覆盖多 tier
- **One-liner**: {{value prop in 1 sentence — 这个 source 凭什么进 retain？例：「Latent Space podcast — 长访谈每集 1.5h+，嘉宾覆盖 LLM era 主流框架 founders + 工程师，AI engineering 视角的 anchor」}}
- **典型每期内容**: 一段 80-150 字描述
- **投入产出比**: high / medium / low + 概率锚 (iter 13 修正)
  - **high** = ≥ 80% 期 / 集 / issue 给从业者带来 actionable insight，从业者必跟
  - **medium** = 50-80% 期有信号
  - **low** = < 50% 期有从业者级信号（仍可订阅但作 ambient awareness, 不必每期看）

  概率不是精确预测，是评级锚 — 让评估者快速校准而非凭直觉判断
- **Paywall** (iter 13 新增): `none` / `paywall: $X/month` / `paywall: $X one-time`
  - 付费源仅 retain if 内容 unique 且没有免费替代
  - 标 paywall 必须明确价格 + 是否 worth it 的简短判断 (1-2 句)
- **签名内容**: 1-2 个最有代表性的 episodes / issues / talks（带 URL）
- **Endorsement evidence**: ≥ 2 处独立背书（figure 推荐 / 跨 source 引用 / 行业 newsletter 互相推荐）
  - 标 type: `figure_long` / `figure_short` / `cross_source` / `community_consensus`
- **替代品**: 类似主题的 alternative source
- **最近变化** (近 6 个月): 如有 — host 换 / 主题转向 / 收费 / 暂停 / 复活
- **可信度**: high / medium / low
- **Decay risk**: low / medium / high
  - **high** = 12 月内可能停更 / 转向（个人 newsletter 默认 medium-high）
  - **medium** = 12-24 月内可能 host 换或主题大变
  - **low** = 已是行业基础设施（NeurIPS / 36氪 这种机构级 source）
```

### Step 4: 判定标准（mechanical filter）

每个候选 4 项打 ✅/⚠️/❌：

- **真实背书**: ≥ 2 处独立背书（不算自己的 marketing）
- **Active**: 在「最近活动 阈值」内（newsletter < 3 月停更, podcast < 6 月停更, conference 最近一届 < 24 月）
- **独特价值**: 不是已 retained 的某 source 的低质替代（同一个圈子的 newsletter 互相覆盖度太高时只留 top 1-2）
- **可访问性**: 中文用户能访问 / 英文用户能访问（按 locale 判断）。如果是付费墙，标 `paywall` 但保留 if 内容独特价值高

判定:
- 全 ✅ → KEEP, high
- 3 ✅ → KEEP, medium
- 2 ✅ → BORDERLINE, KEEP only if 该 type 当前 retained < 5
- ≤ 1 ✅ → DROP

### Step 5: 总览表

```markdown
## 总览（按 type 分组）

### Newsletter / Substack — {{N}} 个
| Source | Cadence | Tier | 投入产出 | One-liner |

### Podcast — {{N}} 个
| Source | Cadence | Host | 投入产出 | One-liner |

### Conference — {{N}} 个
| Conference | 频率 | 下届 | One-liner |

### Community — {{N}} 个
| Community | Platform | 规模 | One-liner |

### Dataset / Benchmark — {{N}} 个 (optional, 非所有行业适用)
| Dataset | URL | Maintainer | One-liner |
```

### Step 6: Phase 2 接口

```markdown
## Phase 2 提炼提示

**「这一行的资深人订阅最多的 top 3 sources」**:
- {{name 1}} (出现于 ≥3 figures 公开推荐 / cross-source 引用)
- ...
→ 进入 master skill 「Sources — 信息源」节的 highlights

**「这一行最近的话题热度」**（候选信号 — 用于 Phase 2.4 近期工作流变化）:
- 最近 3 个月被 ≥3 sources 反复讨论的主题:
  - {{topic 1}} (sources A / B / C)
  - {{topic 2}} ...
- **精度依赖**（iter 13 新增）: 该字段的精度依赖**source content 是否被深度爬取**。如果只列 source 不爬最新内容（默认行为），明确标 `topic-heat: incomplete, sources listed but content not crawled`。如果用 fetch / browser-skill 爬了具体 episode title / issue title，标 `topic-heat: high-confidence (N sources × M items inspected)`。

**新 figures 发现**（喂给 wave 2 Track 01）:
- 有些 newsletter 作者 / podcast 嘉宾**还没出现在 wave 1 其他 track**，但在多 source 中被多次提及 → 标记为 figure 候选

**新 tools 发现**（喂给 wave 2 Track 02）:
- 多 source 反复评测的工具但 wave 1 其他 track 没收录 → 标记为 tool 候选

**冷僻 / 信号薄弱**:
- newsletter < 3? podcast < 3? conference < 1?
- 有效 endorsement source < 50%?
- 任一为真 → Phase 2.8 诚实边界标注「sources 维度信号薄弱」
```

---

## 时效性硬规矩

Sources 的衰减速度与 type 强相关：

| Type | 典型 decay | 必须有 |
|------|-----------|--------|
| Personal newsletter | 6-12 月（host 倦怠 / 收费 / 停更高发） | last_published_date |
| Institutional newsletter | 24-36 月（机构会维持） | last_published_date |
| Personal podcast | 12 月停更高发 | last_episode_date + episode count |
| Institutional podcast | 24+ 月稳定 | last_episode_date |
| Conference | 年度 / 双年度，时效低 | last_edition_date + next_edition_date |
|  | (iter 13 修正) next edition 间隔 > 18 月时降级 retain 优先级 — 用户难以等到 |
| Community | 与 platform 命运绑定（X / Discord / WeChat 群） | active_member_estimate |
| Dataset | release 一次后稳定，但 maintenance 可能停 | last_update_date |

**每个 source 卡片必须有对应的时间字段**。这是 master skill update 流程能跑的前提。

---

## 失败处理

| 情况 | 处理 |
|------|------|
| Newsletter 最近 3 月停更 | Drop 或保留 + 标 `[paused, last activity YYYY-MM]`，看是否有迹象短暂 hiatus 还是永久停更 |
| Podcast 嘉宾推荐但听众基础小 | 保留 borderline，标「niche, primarily senior practitioner audience」 |
| 大型 conference 但去年改名 / 拆分 | 标「split into A + B since YYYY」，retain 二者作为后续候选 |
| zh-CN locale 但找不到中文 source | 标注 locale gap, 同时收录英文 source 但标注「primary, en-only」 |
| Dataset / Benchmark 在 LLM 类等行业很重要，在传统行业完全没有 | 该字段空着合法，标注 "N/A for this industry" |

---

## 与其他 Track 的协作

- **Wave 1 → Wave 2 关键 seed**: 这是 Track 01 (figures) 启动时**最重要的 seed 来源**。本 track 调研充分时，Track 01 撒大网阶段成本大幅降低
- **Wave 1 → Wave 2 Track 02 (tools)**: newsletter / podcast 反复评测的工具直接喂给 Track 02
- **本 track ↔ Track 04 (canon)**: 经典著作作者通常有 newsletter / podcast — 双向引用
- **本 track → Phase 2.8 诚实边界**: 在 master skill 的「想跟最新动态」指引中直接列出 top 3 sources

如果发现某个工具 / figure 仅在本 track 出现而其他 track 都没收录 → 反馈给对应 track 补充候选。

---

## 质量自检（提交前）

- [ ] 候选数 ≥ 15？（< 10 触发冷僻协议）
- [ ] 5 个 type 有合理覆盖？（newsletter ≥ 3, podcast ≥ 3, conference ≥ 1, community ≥ 1, dataset 可空）
- [ ] 每个 source 都有 cadence 字段 + last activity 日期？
- [ ] 投入产出比 字段每条都标了？
- [ ] 至少 1 个 figure_long 或 cross_source 类型 endorsement 在每个 retained source 上？
- [ ] Phase 2 接口（top 3 sources + 最近话题热度 + 新 figure / tool 候选 + 冷僻信号）填了？
- [ ] **新 figure / 新 tool 候选**反馈给了 wave 2 启动？

任一不通过 → 补完再提交。
