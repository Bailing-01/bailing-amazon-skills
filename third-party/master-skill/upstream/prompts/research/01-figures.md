# Track 01 — Figures Research Subagent

> Phase 1 的第 1 路 subagent。SKILL.md Phase 1 调用本文件作为子任务模板。

## 你的任务

调研「{industry}」（locale={locale}）行业的 **top 10-15 思想领袖** ——这一行的资深人在长访谈 / podcast / Conference talk / 公开讨论里被反复提及的人物。

你不是在做名人榜。你在帮 master skill 的下一阶段（Phase 2 提炼）找到**这个行业的认知操作系统的承载者**。

## 输出位置

```
{skill_dir}/references/research/01-figures.md
```

文件存在则覆盖。

## Source Manifest 引用规范 (iter 24, 强制)

详见 `prompts/research/_source_id_manifest.md`. 摘要:

1. 文件最前面写 `## Source Manifest` 表 (source_id / url / bucket / last_checked / author / note). 黑名单 URL 进表即报错
2. 每条 claim 后挂 `evidence: [Sxxx]`
3. URL 用 `python3 {master_skill_dir}/tools/research/source_verifier.py classify <URL>` 跑一遍, 取 bucket
4. Phase 4 跑 `tools/research/quality_check.py` item 13 (URL 一手机械验证 ≥ 50%) + item 14 (无黑名单) + item 15 (freshness ≥ 70%) + item 16 (claim 引用 ≥ 2 source_ids)
5. 冷僻行业 (`cold_detector` verdict = `cold_deep_mode`): 用 Surrogate Sources Policy (协会理事列表 / 课程 syllabus / 监管 / JD / vendor docs) 把 figures / canon 维度补回, 但严格标 `bucket: surrogate_primary`, 不冒充 primary

## 6 步流程

### Step 1: 候选清单（Wide Net）

先撒大网，列 **目标 20-30 个候选，floor 15，<10 触发冷僻协议**。来源（按权重）：

> **Wave 2 加成**：本 track 在 Phase 1 wave 2 启动，**已经能从 wave 1 拿到 seed 候选**（Track 04 canon 的核心作者 + Track 05 sources 的常驻嘉宾）。Wave 1 输出通常贡献 8-15 个 seed candidates，让你撒大网更具针对性而非凭空猜。如果 wave 1 输出不足（< 5 seed），先回头检查 wave 1 是否完成，避免在 figures track 浪费时间盲搜。


1. **行业最大几家公司的创始人 / 关键工程师 / 关键产品经理**（公司选择参考 Track 02 工具栈调研结果，没有就先用直觉）
2. **核心著作 / 论文的作者**（Track 04 知识正典调研结果）
3. **被 ≥ 3 个候选反复点名 / 引用的人**（second-order 推荐）
4. **行业专属 podcast / conference 的常驻嘉宾**（Track 05 信息源调研结果）
5. **active 输出的从业者**（最近 6 个月有公开内容输出，不是退休 / 沉默已久）

如果调研启动时 Track 02 / 04 / 05 还没数据（并行 swarm 启动状态），先用 web search 兜底：

```
搜索词模板（按 locale 调整）：
- en: "{industry} thought leaders"、"{industry} top researchers 2025"、"who to follow {industry}"
- zh-CN: "{中文行业名} 大佬"、"{中文行业名} 专家"、"{中文行业名} 必关注"
- 避免：博客榜单、付费推广榜、训练营导师列表
```

### Step 2: 筛选到 10-15 (Quality Gate)

从候选池筛 10-15。每位候选给 4 项打 ✅ / ⚠️ / ❌：

- **跨场景影响**：在 ≥ 2 个公开来源中被独立提及（不算自营销 / 自家公司 PR）
- **可调研性**：至少有 1 篇长访谈 / 1 个 podcast 长 talk / 1 篇长文，能拿到至少 30 分钟以上的连续输出
- **当前 active**：近 12 个月有过公开输出，或仍在公司活跃岗位
- **非纯销售**：纯 marketing / LinkedIn 帖子机器不进任何 track

**判定规则**：
- 全 ✅ (4/4) → KEEP, 卡片可信度 high
- 3 ✅ + 1 ❌ → KEEP, 可信度 medium，在卡片中说明缺哪一项
- 2 ✅ + 2 任一组合 → BORDERLINE → KEEP only if 候选不足（< 12 retained）, 可信度标 medium 并标注边缘
- ≤ 1 ✅ → DROP

**学术 figures 特例（iter 4 修正）**：纯学术（仅有 paper 输出，无工程实践 / 长访谈）→ 进 Track 04 (canon) 不进本 track。但**学术 + 工程双角色**（如 ReAct 作者后来在 Princeton + Google 内部做工程）→ 进本 track，标注 `dual_role: "academic + engineering"`。判断标准：是否有 ≥ 1 篇长访谈或 conference talk 谈实践（不是纯论文 talk）。

**筛掉的常见类型**：
- ❌ LinkedIn influencers（高频发帖但实质内容低）
- ❌ 付费课程导师（除非他们也有原创性公开输出）
- ❌ 已退休 / 已离开此领域 5 年以上的人（可作为 "founders" 单列在 Phase 2 接口）
- ❌ AI 合成内容创作者（"AI thinkers" 营销账号）

### Step 3: 信源黑名单（按 locale）

| Locale | 永不引用 |
|--------|---------|
| zh-CN | 知乎、微信公众号、百度百科、CSDN（除原作者本人）、博客园 |
| en | LinkedIn 文章正文（标题可索引）、Medium SEO 农场、内容农场 sites |
| 通用 | AI summary 站（无原文链接的）、PR 通稿网站 |

### Step 4: 每位 Figure 的标准数据结构

调研每位时收集以下字段（缺则空），**写进** `01-figures.md`：

```markdown
### {{1. 姓名 / 中文名}}

- **One-liner**: {{这个人在这一行的独特贡献，一句话。例：「LangChain 创始人，把 agent framework 从论文概念推到工程化标准」}}
- **核心身份**: {{当前 role / company；如果换过多家，标注最相关的 1-2 个}}
- **代表作品**: {{1-3 件 — 书 / 论文 / 项目 / 系列产品}}
- **值得读 / 听 / 看的 3 件事**:
  - 📖 {{长文 / 论文标题 + URL}}
  - 🎙️ {{podcast 集 / 长访谈 + URL}}
  - 🎬 {{conference talk / 长视频 + URL}}
  - （如果某类没有，留空，标注「⚠️ 无 / 未找到」）
- **核心思想关键词** (3-5 个): {{他反复强调的概念，将进入 Phase 2 候选心智模型清单}}
- **voice_samples** (iter 26 强制 — 系统升级 voice DNA): 收集这位 figure 在不同 register 下的**完整对话片段或独白原话**, 至少 3 段, 标 source_id 和「原话/转述」:
  - 客户解释样本 (≥ 1 段, 50-150 字): figure 怎么把行业术语翻译给客户. 例: 「不可抗辩条款 ≠ 必赔, 它只解决告知问题, 不替你扛理赔范围. 您朋友说的『2 年免死金牌』是民间简化版」(source: 谷主 podcast E52, 转述)
  - 同业讨论样本 (≥ 1 段, 30-100 字): figure 在私下 / 内训 / 同业访谈里怎么说话. 例: 「这个 case 7-3 是阳性, 走人工核保大概率加费 30-50%」(source: 江立辉明亚内训, 转述)
  - 监管 / 专业讨论样本 (≥ 1 段, 50-150 字): figure 在公开场合谈监管 / 标准 / 学术问题时的语言. 例: 「2024 利率切换的本质是把利差损风险显性化, 监管不是要打压寿险, 是要让定价更接近真实利率」(source: 13 个精算师公众号, 原话)
  - 标注规则: 每段后写 `(source: T0X-SXXX, 原话 | 转述 | 推断)`. 「推断」必须诚实标, 不能伪装成原话
  - **没找到 voice_samples → 写「⚠️ 暂未找到 ≥ 30 字直接原话片段」**, 不要编. Phase 4 voice check 会因此降级 voice_confidence 到 low
- **sub_skill_candidate**: `true` / `false` + 一句理由
  - `true` 标准：有 ≥ 30 min 长访谈材料 + 思想体系自洽 + 在行业中影响力前 5 + 用户的 focus 与其领域对齐
  - `false` 也可以解释为「重要但不够独立成 sub-skill」（例：靠工程产品输出而非个人思想）
  - 该字段供 Phase 3 Step 3 决定是否调用 nuwa.skill 蒸馏成独立 sub-skill
- **dual_role**（可选）: `"academic + engineering"` 或 `"founder + thinker"` 等组合标签
- **最近 12 个月动态**: {{2025-{month} 之后的关键发言 / 项目 / 立场变化}}
- **争议 / 批评**: {{如有 — 业内对其 1-2 个常见反驳。不写就是没找到，不要避而不谈}}
- **来源** (≥ 3 条):
  - [Primary] {{他自己写的 / 说的}}: {{URL, title, collected: YYYY-MM-DD}}
  - [Secondary] {{别人写他的}}: {{URL, title}}
  - [Reference] {{他被引用的地方}}: {{URL, title}}
- **可信度自评**: high / medium / low + 一句话理由（low 必须给理由）
```

### Step 5: 总览表

文件开头放一个总览表，便于 Phase 2 提炼时快速扫：

```markdown
## 总览（按行业影响力排序）

| # | 姓名 | 核心身份 | 一句话贡献 | 值得读/听/看 | 来源数 |
|---|------|---------|----------|------------|-------|
| 1 | {{name}} | {{role}} | {{tagline}} | 📖🎙️🎬 | {{N}} |
| ... |
```

### Step 6: Phase 2 接口准备

文件末尾写一个 Phase 2 友好的 hint：

```markdown
## Phase 2 提炼提示

**反复出现 ≥ 3 个 figures 都谈到的关键词**（候选行业心智模型）:
- {{keyword 1}} (出现于 figures: A / C / E)
- {{keyword 2}} (...)

**显著分歧 / 流派分裂**:
- {{流派 A}}（代表: A, B）vs {{流派 B}}（代表: C, D）

**冷僻领域信号**:
- 总 figure 数 < 10？
- 多数 figure 长访谈材料 < 30 min？
- 标记 "可信度 low" 的 figure 比例 > 30%？
- 任一为真 → 在 Phase 2.8（诚实边界）明确告知用户「figures 维度信息薄弱」
```

---

## 音视频处理（重要）

行业 figures 的最高价值材料经常是 podcast / conference talk / YouTube 长访谈。处理流程：

1. **优先：抓字幕** (工具住在 master-skill 仓库, 不在生成的行业 skill 内)
   ```bash
   bash {master_skill_dir}/tools/transcribe/youtube.sh "{url}" "{skill_dir}/sources/transcripts/"
   # 然后清洗 .srt → .txt (或加 --jsonl 输出结构化时间戳/speaker/word_count)
   python3 {master_skill_dir}/tools/transcribe/srt_to_transcript.py "{skill_dir}/sources/transcripts/<slug>.srt" "{skill_dir}/sources/transcripts/<slug>.txt"
   ```
   字幕抓不到 → 用 `{master_skill_dir}/tools/transcribe/local_video.sh <video.mp4>` (本地转录, 第一次运行会 lazy-install ffmpeg + faster-whisper). 长访谈想 dial up 信号 → 跑完后链 `transcript_scorer.py --top 50` 抽 actionable 段落.

2. **次选：搜 transcript 站**
   - en: podcastnotes.org, transcripts.byanker.com, descript blog
   - zh: 小宇宙节目页 (有的有官方文字稿)、B 站 CC 字幕

3. **不到 30 分钟材料 → 标 "可信度 low"**：30 分钟以下不足以建立思维框架认知

4. **绝不做的事**：
   - 不要把完整 transcript paste 进 `01-figures.md`（版权风险 + 文件过大）
   - 不要超过 30 字的连续引用 — 用结构化摘要 + 链接代替

---

## 质量自检（提交前）

- [ ] 候选清单确实 20-30 候选 → 筛选到 10-15？（少于 10 标 "冷僻领域"）
- [ ] 每位 figure ≥ 3 条来源（一手 + 二手 + 引用）？
- [ ] 一手来源 (Primary) 占比 ≥ 50%？
- [ ] 没有用任何信源黑名单中的来源？
- [ ] 「最近 12 个月动态」字段填了 ≥ 80% figures？（信息过时是这一 track 的最大风险）
- [ ] Phase 2 接口部分（关键词 + 分歧 + 冷僻信号）填了？
- [ ] 「可信度自评」每位都给了？低可信度的有解释？

任一不通过 → 补完再交，**不要**把不完整的 `01-figures.md` 提交给 Phase 2。

---

## 失败处理

| 情况 | 处理 |
|------|------|
| Web search 反复返回同一批 SEO 农场结果 | 切换搜索语言、加 site: 限定（site:youtube.com / site:substack.com）、找该领域专属 newsletter / podcast 嘉宾名单 |
| 行业极冷僻（找不到 ≥ 5 个人） | 在文件开头写「冷僻领域协议生效，仅找到 N 位」，并在 Phase 2 接口部分明确告知后续 phase |
| 用户提供本地素材覆盖了部分 figures | 标 "[Source: user-provided]"，权重 = Primary，不再去网络补 |
| 调研超时（5 分钟无新增有效来源） | 不死磕，按当前数据出文件，标记 "{N} candidates explored, {M} retained" 给 Phase 1.5 review |

---

## 与其他 Track 的协作

- **Track 02 (tools)** 找出的关键工具的开发者 / 维护者 → 候选 figures
- **Track 04 (canon)** 找出的必读书 / 论文作者 → 候选 figures
- **Track 05 (sources)** 找出的核心 podcast 常驻嘉宾 → 候选 figures
- 反向：本 track 找出的 figures 提到的工具 / 观点 → 反馈给对应 Track 加权候选

如果各 Track 在 Phase 1 末发现彼此信号有矛盾（A track 说 X 是核心，本 track 没找到 X），保留矛盾，由 Phase 1.5 关卡用户裁决。
