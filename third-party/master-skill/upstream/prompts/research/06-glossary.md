# Track 06 — Glossary Research Subagent

> Phase 1 wave 1 的第 3 路 subagent。SKILL.md Phase 1 调用本文件作为子任务模板。

## 你的任务

调研「{industry}」（locale={locale}）行业的 **术语 + 标准 + 法规 + 认证** ——这一行的资深人在写 / 说 / 谈判 / 合规中实际用的语言体系。

具体覆盖：
- 高频黑话 / 缩写（行业内人秒懂、外行听不懂的词）
- 标准化术语（行业有官方定义的概念）
- 法规 / 合规框架（必须遵守的法律法规）
- 认证 / 资质（行业认可的执业 / 产品 / 团队认证）
- 外行破绽（外行常说错 / 用错的词）

输出**不是百度百科**。输出是 **「这个词在这一行的实际用法 + 跟相邻行业的细微差别 + 外行误用 vs 内行用法」**，让 Phase 2 直接整合进生成 skill 的 [Glossary — 术语 + 标准](../../references/skill-template.md) 节，并支持「行业表达 DNA」节的 outsider-tell 提取。

## 输出位置

```
{skill_dir}/references/research/06-glossary.md
```

文件存在则覆盖。

## Source Manifest 引用规范 (iter 24, 强制)

详见 `prompts/research/_source_id_manifest.md`. 摘要:

1. 文件最前面写 `## Source Manifest` 表 (source_id / url / bucket / last_checked / author / note). 厂商话术 / SEO 农场是黑名单
2. 每个术语的 `Insider def`, `Outsider tell`, `是否被错位包装` 等 claim 末尾挂 `evidence: [Sxxx]`
3. URL (官方 spec / 标准发布机构 / textbook chapter) 用 `python3 {master_skill_dir}/tools/research/source_verifier.py classify <URL>` 跑一遍取 bucket
4. Phase 4 跑 `tools/research/quality_check.py` item 13 + 14 + 15 + 16 验证
5. 冷僻行业: 监管 / 立法机构原文 + 大学课程 lecture notes + 协会词典作 surrogate_primary, 标 `bucket: verified_primary` 仅限 gov / standards body / official spec

## Wave 1 加成（独立 track）

本 track 在 Phase 1 wave 1 启动，**搜索路径独立**。但与 Track 04 (canon) 强相关：
- canon 中的 textbook / paper 是术语第一手定义来源
- canon 的核心概念（Tier 1）是 glossary 的强 candidate

策略：优先消化 canon 的术语集合，再用 web 搜「{industry} terminology」「{industry} jargon」补 missing。

输出会作为 seed 喂给：
- Wave 2 Track 02 (tools) — 标准 / 认证经常对应特定工具（如「ISO 27001」对应安全审计工具）
- Wave 3 Track 03 (workflows) — 法规变化是工作流变化的核心触发事件

## 6 步流程

### Step 1: Glossary 候选清单（Wide Net）

撒大网，**目标 60-120 个候选词，floor 40，<25 触发冷僻协议**。

**注意：词数比例与行业类型强相关**：
- 技术类（LLM agent infra / RAG / SaaS）：术语 + 缩写多，标准 + 法规少
- 法规重的（医疗 / 金融 / 跨境电商）：标准 + 法规 + 认证占大头
- 学术类（计算机视觉 / 神经科学）：术语 + 概念命名严格，认证少
- 创意 / 内容（短视频 / 文案）：黑话和 register 多，正式标准少

#### 候选来源（按权重）

1. **Track 04 (canon) 的核心概念清单**：直接作为 Tier 1 术语 seed
2. **行业入门书 / 第一章「术语表」附录**（textbook 末尾的 glossary 是最高质量来源）
3. **行业标准化机构 / 监管机构网站**（ISO / NIST / FDA / 国家市场监督管理总局 等的术语数据库）
4. **行业专属 Wikipedia 词条 + 「See Also」 link 网络**（avoid百度百科 - blacklisted）
5. **行业新人入职文档** / 行业新人 onboarding 系列文章（很多 senior 写的「the lingo of X you must know」）
6. **行业内人吐槽外行的 thread / 长 post**（揭示「外行破绽」)

```
搜索词模板：
- en: "{industry} terminology", "{industry} acronyms glossary", "{industry} standards [year]"
- zh-CN: "{中文行业名} 术语"、"{中文行业名} 黑话"、"{中文行业名} 标准 法规"
```

### Step 2: 候选分类

将候选分入 5 类：

| 类型 | 示例 (LLM agent infra) | 典型来源 |
|------|----------------------|---------|
| **Term / 术语** | RAG, ReAct, CoT, hybrid retrieval | Canon Tier 1 + 入门书 |
| **Acronym / 缩写** | LLM, RLHF, MoE, KV cache | Inline in technical content |
| **Standard / 标准** | OpenAPI, MCP, OpenAI Tool Calling spec | 标准化机构 + 大厂规范 |
| **Regulation / 法规** | EU AI Act, China 生成式 AI 暂行办法 | 政府 + 法律事务所长稿 |
| **Certification / 认证** | (LLM agent infra 行业目前几乎没有正式认证) | (此行业空) |

**注意：不是每个行业都覆盖 5 类**。LLM agent infra 几乎无认证；医疗器械几乎无非法规外的标准；短视频投流没有法规但黑话极多。Phase 2 接口要明确报告「本行业在 {缺失类型} 上 N/A」。

### Step 3: 信源黑名单

| Locale | 永不引用 |
|--------|---------|
| zh-CN | 百度百科、知乎答主自定义术语解释 |
| en | Quora answers (除非作者认证), AI-generated definition sites |
| 通用 | 厂商对自家产品名称的「术语化」营销（如 Salesforce 把所有 CRM 概念包装成「Customer 360」） |

### Step 4: 每个 Glossary entry 的标准数据结构

```markdown
### {{N. 术语原文}} — {{中译 / 英译, 如适用}}

- **Type**: term / acronym / standard / regulation / certification (支持 multi-type, 例 `term + acronym` 用于 RAG, CoT 这种既是术语又是缩写的)
- **Tier**: tier-1 (核心，所有从业者必懂，30-50 个) / tier-2 (周边，资深者熟知，30-70 个)
- **Definition (insider)**: 1 句这一行内人对它的实际理解
- **Definition (outsider-friendly)**: 1-2 句让外行也能 get gist 的版本
- **Etymology / 来源**: 这个词从哪里来（如适用 — 缩写展开 / 标准发布机构 / 法规年份）
- **常见误用 (outsider-tell)**: 外行 / 入门常见的错误用法 — 是行业表达 DNA 的金矿
  - **Tier 1 必填**, Tier 2 推荐填 (iter 13 修正)
  - 误用类型 1 `semantic_tell`: {{外行说 X 时通常意思是 Y, 但内行的 X 意思是 Z}}
  - 误用类型 2 `pronunciation_tell` (针对 acronyms): {{发音错 / 重音错}}，例 SQL "sequel" vs "S-Q-L"; RAG "rag" 一个音节 vs "R-A-G" 三个字母
  - 误用类型 3 `usage_tell`: {{用错语境 / 与相邻概念混用}}
  - 误用类型 4 `register_tell`: {{严肃 vs 轻松场合用错 register}}
- **关联术语**: 1-3 个相邻 / 相对 / 相辅术语（hyperlinked）
- **是否被错位包装** (iter 13 修正): 厂商有没有把这个标准 / 概念混淆 / 收编到自家产品命名中 — **每条 claim 必须 source link**, 不能凭印象（避免污染 master skill）。例: 「Pinecone 营销文章中把 RAG 等同于 vector DB」+ source URL
- **变化历史** (regulation / certification 必填): 法规修订时间线 / 认证版本演变
- **Source** ≥ 2:
  - [Primary] official spec / 标准发布机构 / 监管文件: URL + collected date
  - [Secondary] textbook chapter / 长 blog 解释 / Wikipedia 词条: URL
- **可信度**: high / medium / low
- **Decay risk**: low / medium / high
  - **high** = 法规 / 标准在 12 月内可能修订；新兴术语定义不稳定
  - **medium** = 24 月内可能演化
  - **low** = 已稳定 5+ 年的核心术语 / 法规
```

### Step 5: 判定标准（mechanical filter）

每个候选 4 项打 ✅/⚠️/❌：

- **行业内必备**: ≥ 3 处行业内 source 使用 / 解释这个术语（不算 SEO 农场和百度百科）
- **定义稳定**: 行业内对它的理解一致（< 20% 内部分歧）— 内部分歧大的术语标 `disputed: <两派理解>`
- **不是厂商专用术语**: 单一厂商造的、未被行业广泛接受的词不进 retain
- **有 outsider-tell**: 至少能填出 1 个外行常见误用 — 如果填不出，说明这个词外行也能正确理解，不是行业特异术语，考虑 DROP

判定:
- 全 ✅ → KEEP, tier-1 候选
- 3 ✅ → KEEP, tier-2
- 2 ✅ → BORDERLINE, KEEP only if 该 type 当前 retained < 适配 floor
- ≤ 1 ✅ → DROP

### Step 6: 总览表 + Phase 2 接口

#### 总览表

```markdown
## 总览（按 type 分组）

### Tier 1 — 核心必懂 ({{N}} 个，目标 30-50)
| 术语 | Type | Insider def | Outsider tell | Last_updated |

### Tier 2 — 周边熟知 ({{N}} 个，目标 30-70)
| 术语 | Type | Insider def | Last_updated |

### Standards / Regulations / Certifications 时间轴 (iter 13 修正：仅近 5 年内有显著变化的进表)
| 名称 | Issued | Last revised | Decay |
| (长期稳定的 standard / regulation 不进时间轴, 只在主条目记 issued 年份) |

### 行业「外行破绽」高亮 ({{N}} 条最容易暴露的)
| 误用 | 内行实际意思 | 出现频率 |
```

#### Phase 2 接口

```markdown
## Phase 2 提炼提示

**「行业表达 DNA」直接素材**（喂给 Phase 2.5 expression-DNA 提炼）:
- 高频黑话 top 10: ...
- 行业拒绝的厂商话术 top 5: ... （拒绝 → 反映行业的「价值观 + 反模式」）
- 外行破绽 top 10 (insider-only spotting tells): ...

**「智识谱系」线索**（喂给 Phase 2.7 智识谱系）:
- 标准 / 法规的演变路径暗示行业的范式更替（例：「OpenAPI v2 → OpenAPI v3」反映 API 设计哲学的变化）
- 多 standard 互相竞争 / fragmenting → 流派之争的硬件层

**「时效性」信号**（喂给 Phase 2.8 诚实边界）:
- 有 N 个法规 / 标准在过去 12 月内有修订 → master skill 时效衰减信号
- 列出预计 12 月内会变的标准 / 法规

**「工作流变化触发」种子**（喂给 wave 3 Track 03）:
- 法规 / 标准的最新修订是 workflow 变化的最重要触发源
- 列出近 12 月修订的标准 / 法规 + 它们影响的 workflow 假设

**冷僻 / 信号薄弱**:
- 总术语数 < 25? Tier 1 < 15? 有 outsider-tell 的术语 < 50%?
- 任一为真 → Phase 2.8 标注「glossary 维度信号薄弱，可能行业较新或闭源主导」
```

---

## 时效性硬规矩

Glossary 的 decay 速度与 type 强相关：

| Type | 典型 decay | 必须有 |
|------|-----------|--------|
| Term / 术语 | low (核心术语极慢) | first-seen 年份估算 |
| Acronym | low | full-form 展开 |
| Standard | medium (大版本 3-5 年) | issued + last_revised 日期 |
| Regulation | medium-high (政策驱动 2-5 年) | issued + last_revised + 影响范围 |
| Certification | medium | 版本号 + last_updated |

**Standards / Regulations / Certifications 必须填日期字段**。Master skill 的 update 流程会按法规修订日期触发刷新。

---

## 失败处理

| 情况 | 处理 |
|------|------|
| 行业很新（<3 年），术语还在形成 | 标 "Pre-canonical glossary"。重点抓 Track 01 figures 反复使用的词 + 让 senior 在 podcast 中**澄清** 的术语 |
| 行业是闭源 / 专业 (e.g. 量化金融、军工) | 公开 glossary 极有限。明确写「主要术语在内部 wiki / 培训材料中，公开材料受限」+ 收集**反向**（外人吐槽的术语 / 论坛抱怨术语墙） |
| 多 source 对同一术语定义冲突 | 标 `disputed`，并列两派理解 + 各自 source。不要强行统一 |
| 法规跨地域差异巨大（如 cross-border ec 的 EU vs US vs CN） | 按地域分别记录，标 `geographic-specific: EU / US / CN` |
| 调研超时（5 分钟无新增有效来源） | 不死磕，按当前数据出文件 |

---

## 与其他 Track 的协作

- **Track 04 (canon) → Track 06**: canon Tier 1 概念直接 seed Track 06 Tier 1 术语
- **Track 06 → wave 2 Track 02 (tools)**: 标准 / 认证名称对应特定工具
- **Track 06 → wave 3 Track 03 (workflows)**: 法规修订是 workflow 变化最重要的触发事件
- **Track 06 → Phase 2.5 (表达 DNA)**: outsider-tell 是表达 DNA 节的核心素材
- **Track 06 ↔ Track 01 (figures)**: figures 在长访谈中**澄清的术语** + figures **拒绝使用的厂商话术**双向印证

---

## 质量自检（提交前）

- [ ] 候选数 ≥ 40？（< 25 触发冷僻协议）
- [ ] 5 个 type 按行业类型有合理分布？(空 type 标 N/A 而非缺漏)
- [ ] Tier 1 ≥ 15? Tier 2 + Tier 1 总和 ≥ 40?
- [ ] Tier 1 术语**全部**填了 outsider-tell? Tier 2 至少 50% 填了?
- [ ] Standards / Regulations / Certifications 都有日期字段?
- [ ] Disputed 术语正确标注（不强行统一）?
- [ ] Phase 2 接口（行业表达 DNA / 智识谱系 / 时效信号 / workflow 触发种子 / 冷僻信号）填了？

任一不通过 → 补完再提交。
