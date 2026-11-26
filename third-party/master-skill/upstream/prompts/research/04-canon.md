# Track 04 — Canon Research Subagent

> Phase 1 wave 1 的第 1 路 subagent。SKILL.md Phase 1 调用本文件作为子任务模板。

## 你的任务

调研「{industry}」（locale={locale}）行业的 **知识正典** ——这一行的资深人都读过 / 学过 / 引用过的核心文本和概念。

具体覆盖：
- 必读书 + 论文 + 课程（≥ 3 个独立来源都点过）
- 行业核心 20-30 个概念（不是黑话 — 那是 Track 06 的工作）
- 智识谱系种子（这一行的思想是从哪里继承下来的）

输出**不是 awesome-X 推荐列表**（那是 SEO 农场的工作）。输出是 **「真正读过的人名单」+「为什么读」+「读完得到什么」**，让 Phase 2 能直接整合进生成 skill 的 [Canon — 知识正典](../../references/skill-template.md) 节。

## 输出位置

```
{skill_dir}/references/research/04-canon.md
```

文件存在则覆盖。

## Source Manifest 引用规范 (iter 24, 强制)

详见 `prompts/research/_source_id_manifest.md`. 摘要:

1. 文件最前面写 `## Source Manifest` 表 (source_id / url / bucket / last_checked / author / note). 黑名单 URL 进表即报错
2. 每条经典 / 论文的 `必读理由`, `争议`, `继承关系` 末尾挂 `evidence: [Sxxx]`
3. URL (DOI / arXiv / 出版社 / 课程主页) 用 `python3 {master_skill_dir}/tools/research/source_verifier.py classify <URL>` 跑一遍取 bucket; 学术黑灰产平台 / Sci-Hub-style 是黑名单
4. Phase 4 跑 `tools/research/quality_check.py` item 13 + 14 + 15 + 16 验证
5. 冷僻行业: 大学课程 syllabus reading list + 行业协会推荐 + 监管引用文献 作 surrogate_primary, 把 canon 维度补回

## Wave 1 加成（独立 track，无 wave 依赖）

本 track 在 Phase 1 wave 1 启动，搜索路径**最独立**：直接看 Goodreads / arXiv / 大学课程页 / 行业经典书单，不依赖其他 track 的输出。Wave 1 跑完后，本 track 的输出会作为 seed 喂给 Wave 2 的 figures（核心作者）+ tools（书 / 课程教的工具）。

但反过来：如果用户提供了本地素材（书 PDF / 课程 transcript / 大量笔记） → 本 track 应**优先消化本地一手素材**，再用网络搜索补缺口。一手书 / 课程材料的信息密度比任何网络二手转述都高。

## 6 步流程

### Step 1: Canon 候选清单（Wide Net）

撒大网，**目标 30-50 个候选 (书 + 论文 + 课程 + 概念合并)，floor 20，<15 触发冷僻协议**。

#### 候选来源（按权重）

1. **用户提供的本地素材**（最高权重）：直接吸收。一本书的章节标题 + 索引页 + 推荐书单页就是免费的相邻 canon 候选源
2. **行业经典出版社的目录**（O'Reilly / Manning / MIT Press / arXiv 顶级研究组 / 各大学出版社）
3. **行业大会的 keynote 引用 / 学术 review paper 的参考文献节**：这些通常是真正被读过的列表
4. **开源 community-maintained 书单**（GitHub awesome-X 中的 books 节，但**只取被 ≥ 3 人 endorse 的**，避免 SEO）
5. **大学公开课程大纲**（MIT OCW / Stanford / Coursera）：reading list 通常质量很高

#### 候选类型分类

将候选分入 4 类：

| 类型 | 例 | 时效 |
|------|------|------|
| **Textbook / 系统性著作** | Chip Huyen "Designing Machine Learning Systems" | low decay (5-10 年稳定) |
| **Seminal paper** | "Attention Is All You Need" / ReAct / RAG | low decay（不会过时，但理解可能加深） |
| **Course** | Stanford CS224N / Karpathy NN-zero-to-hero / DeepLearning.AI specializations | medium decay (3-5 年更新一次) |
| **Core concept** | Self-attention / RAG / Tool use / Cot reasoning | low decay（概念本身稳定） |

```
搜索词模板：
- en: "best {industry} books / textbooks / papers"、"required reading {industry}"、"X syllabus"
- zh-CN: "{中文行业名} 经典书单"、"{中文行业名} 必读"、"X 课程大纲"
- 避免：「2025 必读」类时效 SEO 农场
```

### Step 2: 信源黑名单

| Locale | 永不引用 |
|--------|---------|
| zh-CN | 知乎 / 微信公众号 / 百度百科 / CSDN（除原作者）/ 「读书会」自营销文章 |
| en | Medium SEO 「best X book」/ Goodreads 单评 / Amazon 影响力作者推销文 |
| 通用 | AI 合成书评 / 内容农场 / 厂商出版的「客户成功手册」 |

### Step 3: 每个 Canon 候选的标准数据结构

#### Books / 系统性著作

```markdown
### 📖 {{N. 书名}}

- **Author / 作者**: {{name}}（与 Track 01 figures 关联，如适用）
- **Year**: {{first published}} / latest edition: {{YYYY}}
- **Type**: textbook / monograph / popular science / collected essays
- **One-liner**: {{这本书在这一行的位置 — 一句话。例：「LLM agent infra 的 CoT / ReAct / Tool Use 三件套的工程化指南」}}
- **核心论点 (3-5)**: 这本书的主要 takeaways
- **读完得到什么**: {{读者读完应该能做什么 / 知道什么}}
- **难度**: 入门 / 进阶 / 高阶专家
- **Endorsement evidence**: 至少 3 处独立 endorsement，**每条标 type**（影响权重）：
  - `[type: figure_long]` figure A 在 ≥30min podcast / blog 中具体推荐 + 给理由 — **权重最高**
  - `[type: figure_short]` figure 短推（tweet / quick mention）— 权重中
  - `[type: course_syllabus]` 大学 / 公开课程 reading list — 权重中
  - `[type: conf_citation]` conference talk slide / 引用 — 权重中
  - `[type: blog_secondary]` 第三方教程 / 推荐文章 — 权重低
  Endorsement 总数要求 ≥ 3，但**至少 1 条必须是 `figure_long` 或 `course_syllabus`**（避免全是 short / blog 这种轻量推荐就过关）
- **是否被新版 supersede**（iter 9 finding 修正）：如果同作者 / 同主题在 ≤ 4 年内出了显著更新版本（≠ 简单 reprint）→ 标 `superseded_by: {{new title + year}}` 并 DROP 老版条目；除非老版的教学路径仍有独立价值（例：旧版讲的是 pre-LLM era 的核心方法，新版没覆盖）。判定：写一句「为什么旧版仍值得读」，写不出来就 DROP
- **替代品**: 类似主题但 alternative 视角的书
- **如果可以只读 1 章**: 推荐 chapter
- **可信度**: high / medium / low
- **Decay risk**: low / medium / high
```

#### Seminal Papers

```markdown
### 📄 {{N. 论文标题}}

- **Authors**: {{names}}
- **Venue + Year**: {{conference / journal, YYYY}}
- **arXiv / DOI**: {{URL}}
- **One-liner**: {{这篇论文在这一行被引用的核心贡献}}
- **核心 idea**: 1-2 句
- **为什么经典**: {{被 ≥ N citations / 被纳入 N 课程 / 被 N 个开源框架直接实现}}
- **如何读**: 是从头读到尾？跳读哪几节？
- **读完得到什么**:
- **Endorsement evidence**: 同 books
- **后续 / 扩展论文**: 1-3 个 follow-up
- **可信度 / Decay risk**: 同 books
```

#### Courses

```markdown
### 🎓 {{N. 课程名}}

- **Lecturer**: {{name}}（与 Track 01 关联）
- **Institution**: {{}}
- **Format**: 讲座视频 / 互动 lab / 阅读 + 讨论 / **rolling**（持续更新而非一次性）
- **Duration**: {{N hours / weeks}}（rolling 格式填 "rolling, ~N hours / month new content"）
- **Year + 最近更新**: {{YYYY-MM}}（rolling 格式填 `rolling, last 3 months key content: {{摘要}}`）
- **One-liner**:
- **完整路径 vs 关键章节**: 完整学完 vs 只看 X / Y / Z 章节的差异
- **难度 / 先修要求**:
- **Endorsement evidence**:
- **Last_updated**: {{YYYY-MM}}（课程最近更新的时间，重要因为课程衰减比书快）
- **可信度 / Decay risk**:
```

#### Core Concepts

```markdown
### 💡 {{N. 概念名}}

- **Tier** (iter 9 finding 修正): `tier-1` (核心，所有从业者必懂，10-15 个) / `tier-2` (周边，资深者熟知，5-15 个)
- **One-liner**: 一句话定义
- **来源** (支持单 / 多 origin):
  - 单一来源：`{{paper / book / 人 + 年份}}`
  - 多 origin（如 RAG 这种「主奠基论文 + 后续显著扩展」）：列 `[primary]` + 1-3 个 `[significant follow-up]`
- **关联概念**: 与之相邻 / 相对 / 相辅的概念
- **行业内的当前理解 vs 原始定义**: 是否有演化？
- **为什么进入 canon**: 这个概念解决了什么问题，为什么大家都在用
- **常见误用**: 外行 / 入门常见的理解错误
- **Endorsement evidence**: ≥ 3 处使用 / 引用
```

### Step 4: 判定标准（mechanical filter）

每个候选 4 项打 ✅/⚠️/❌：

- **跨人物 endorsement**: ≥ 3 个独立 figures / 来源 / 课程都点过这一项
- **可读性 / 可获取性**: 用户能在合理价格 / 时间内得到（书可买，paper 在 arXiv，课程公开 — 不是只在某收费 platform 内）
- **核心论点清晰**: 能用 3-5 句话说出 takeaway 而不只是「重要」
- **不是 textbook 形式但内容已被 textbook 取代**: 如果有更新更好的 textbook 涵盖了同样内容，旧的可降级

判定:
- 全 ✅ → KEEP, 可信度 high
- 3 ✅ → KEEP, medium
- 2 ✅ → BORDERLINE, only KEEP if retained < 8（books / papers）or < 5（courses）
- ≤ 1 ✅ → DROP

### Step 5: 总览表

```markdown
## 总览（按类型分组）

### Textbook / 系统性著作（必读 N / 推荐 M）
| 书名 | 作者 | 难度 | Endorsement | 一句话 |

### Seminal Papers（必读 N）
| 论文 | 年 | 核心 idea | Endorsement |

### Courses（必看 N / 推荐 M）
| 课程 | 讲师 | 格式 | Last_updated | 一句话 |

### Core Concepts（20-30 个）
| 概念 | 一句话定义 | 来源 |
```

### Step 6: Phase 2 接口

```markdown
## Phase 2 提炼提示

**反复出现 ≥ 3 个 canon 都讨论的核心 idea**（候选行业心智模型）:
- {{idea 1}} 出现于: book A / paper B / course C → 候选心智模型
- {{idea 2}} ...

**智识谱系种子**:
- {{流派 A}} 的奠基: {{book / paper / lecturer}}
- {{流派 A}} 的当前代表: 与 Track 01 figure {{name}} 关联
- {{流派 B}} 的奠基: ...
- 主要分歧: {{什么是 still-debated within the canon}}

**核心概念 → 候选 playbook**:
- 概念 X 暗示的判断方式: 「如果遇到 X 类问题，则按 Y 思路」
- ...

**冷僻 / 信号薄弱**:
- 必读书 < 3 个？ paper < 5 个？ 课程 < 2 个？ 概念 < 15 个？
- Endorsement evidence ≥ 3 处的项 < 50%？
- 任一为真 → Phase 2.8 诚实边界标注「canon 维度信号薄弱，可能因为行业较年轻或闭源主导」
```

---

## 时效性硬规矩

Canon 的衰减比 tools / workflows 慢得多，但**课程 (courses)** 必须强制有 `last_updated` 日期。

不接受：「这门课很经典」「Karpathy 的 NN-zero-to-hero」（无年份 — 2022 版和 2025 版差距巨大）。
接受：「Karpathy NN-zero-to-hero, last_updated 2024-12, covers GPT-2 → Llama-3 architecture」。

理由：master skill 的 update 流程会按 last_updated 决定课程节是否要刷新。

---

## 失败处理

| 情况 | 处理 |
|------|------|
| 行业太新（<5 年），无 textbook | 标 "Pre-canonical era". 改为收集「最有代表性的 paper / blog series」 |
| 行业过于工程化（无学术出版） | 收集「公开的 SOP / handbook / 公司 engineering blog 系列」作为 surrogate canon |
| 行业闭源主导（如对冲基金、军工） | 在文件开头明确「公开 canon 不能代表行业完整知识体」+ 收集**反向**：业内人公开吐槽「教科书没教什么」 |
| 课程链接失效 / 视频被下架 | 标 "[unavailable as of YYYY-MM-DD, possibly archived elsewhere]"，不删除条目 |
| 大量「{年} 必读」SEO 文章 | 切到 reading list（公开课大纲）+ 行业 figures 在长访谈中提到的书 |
| 调研超时（5 分钟无新增有效来源） | 不死磕，按当前数据出文件 |

---

## 与其他 Track 的协作

- **本 track（Wave 1）输出 → Wave 2 Track 01 figures**：核心作者 / paper authors / course lecturers 直接成为 figures 候选
- **本 track → Wave 2 Track 02 tools**：书 / 课程教的工具直接成为 tools 候选
- **本 track → Wave 3 Track 03 workflows**：经典著作描述的 workflow 直接成为 workflows 候选
- **本 track → Phase 2.7 智识谱系**: 直接组装

如果 Track 01 / 02 后续找出的 figures / tools 不在本 track 覆盖范围 → **本 track 的 canon 列表可能太窄**，应该补。Phase 1.5 review 时检查这一致性。

---

## 质量自检（提交前）

- [ ] 候选数 ≥ 20？（< 15 触发冷僻协议）
- [ ] 4 个类型 (book / paper / course / concept) 都有内容？比例不强求均衡（学术行业 paper 多，工程行业 book 多）
- [ ] 每个 book / paper 有 ≥ 3 处 endorsement evidence？
- [ ] 每个 course 有 last_updated 日期？
- [ ] 每个 concept 有「来源」字段（追溯第一次提出这个概念的人）？
- [ ] 一手 endorsement（figures 直接推荐 / 课程 syllabus 列入）≥ 50%？
- [ ] Phase 2 接口（核心 idea + 智识谱系 + 候选 playbook + 冷僻信号）填了？

任一不通过 → 补完再提交。
