# Source ID Manifest 引用规范 (iter 24)

> 本文件是六轨 research 共用的 source_ids 规范, 各 track 的 0X-*.md 通过 reference 导入.

## 为什么改

iter 24 把 [Primary]/[Secondary]/[Reference] 自标升级为 **机械可验证 source_ids**, 让 Phase 4 的 `tools/research/source_verifier.py` 能批量校验:
- 每个 source 一个 ID `S001`, `S002` ...
- URL 用 `tools/research/source_verifier.py classify` 跑一遍, 落 bucket (verified_primary / secondary / reference / blacklisted)
- claim 末尾标 `evidence: [S001, S003]`, 让 Phase 2 提炼 / Phase 4 反向核对都能 trace
- 黑名单 URL **绝对不能** 出现 `bucket=blacklisted` (zh-CN: 知乎 / 公众号 / 百度百科 / CSDN; en: G2 / Capterra), 出现就拒入文件

## Manifest 格式 (写在文件最前面, 在「总览表」之前)

```markdown
## Source Manifest

| source_id | url | bucket | last_checked | author/host | one-line note |
|-----------|-----|--------|--------------|-------------|---------------|
| T01-S001 | https://arxiv.org/abs/2305.12345 | verified_primary | 2026-05-04 | Jane Doe | 2023 ReAct 论文, 工程化 baseline |
| T01-S002 | https://www.latent.space/p/agent-2024 | verified_primary | 2026-05-04 | Latent Space | swyx 长 talk + 嘉宾对谈 |
| T02-S001 | https://github.com/microsoft/autogen | verified_primary | 2026-05-04 | Microsoft Research | 主流 multi-agent framework |
| T06-S004 | https://en.wikipedia.org/wiki/Function_calling | secondary | 2026-05-04 | — | 术语入门定义 |
| T01-S017 | https://www.aofas.org/about/officers | surrogate_primary | 2026-05-04 | AOFAS | 协会 fellow 列表 — 推断隐性 figure 池 |
| ... |
```

**字段规则**:
- `source_id`: `T<NN>-S<NNN>` — 全局唯一格式, 前缀 `T01..T06` 对应六轨 (T01=figures / T02=tools / T03=workflows / T04=canon / T05=sources / T06=glossary). 例: `T01-S001` = figures track 第 1 个 source. 这样 synthesis.md 引用 `evidence: [T01-S003, T05-S012]` 一眼能看出来源轨道, 不会混
- `bucket`: 一定是 `verified_primary` / `secondary` / `reference` / `blacklisted` / `dead` / `surrogate_primary` 之一 (前 5 个由 `source_verifier.py classify` 给, 第 6 个 `surrogate_primary` 是冷僻行业 deep mode 时人工标的, 见下面 Surrogate Sources Policy 节). 跑 `source_verifier.py classify <URL>` 取自动结果, 然后**只能升级 surrogate_primary**, 不能私自降级或跳过黑名单
- `url`: 一手必须有 URL (一手 = 实际可点开的链接). 没 URL 的 figure 名片型条目, 用 `manifest:none` 占位 + 在 `note` 字段说明 ("无公开 URL, 仅书面卡片")
- `last_checked`: `YYYY-MM-DD`, agent 自己访问/确认的日期 (不是 source 的发布日期 — 那是另一个事). 用于 Phase 4 freshness check
- `author/host`: 主创 / 平台 / 机构, ≤ 30 char
- `one-line note`: 30 字以内, 这条 source 的独有价值

## Claim → evidence 的引用方式

正文中每条 claim 后挂 `evidence: [Txx-Sxxx, Tyy-Syyy]`:

```markdown
- **核心一句话**: 「LangChain 把 agent 从论文概念推到工程化标准」 (evidence: [T01-S001, T01-S007])
- **代表作**: ReAct 框架 (Yao et al, 2023) — agent reasoning + acting 经典 paradigm (evidence: [T04-S001])
- **行业共识 (consensus)**: 工具临时性 (mental model) — 跨多人多轨证据 (evidence: [T01-S001, T01-S007, T05-S012])
```

**Phase 2 心智模型**: 必须 ≥ 2 个不同 source_id (跨 track 更好); 单源仅作 playbook.

不挂 evidence 的 claim 在 Phase 4 会被 `tools/research/quality_check.py check_claim_evidence_coverage()` 标记 (Q2 consensus 卡门也要查).

## 黑名单 / surrogate 规矩

- 黑名单 URL 进 manifest 即报错; 想改用 surrogate (协会 / 监管 / syllabus / JD), 标 `bucket: surrogate_primary` 并在 note 写明 (Q5 deep mode 要点)
- 死链 (HEAD 4xx/5xx) 标 `bucket: dead`, Phase 4 提示替换
- 同一 URL 跨 track 用同 ID 是 OK 的, agent 看到重复时合并到 source_pool (架构层 Q6)

## Migration 节奏

- **新跑 industry**: Phase 1 各 track subagent 必须用本规范输出 manifest + evidence
- **老 industry update**: refresh 时, agent 先把 [Primary]/[Secondary] 自标 → source_ids 转写, 再重跑 verifier 校验
- 兼容: quality_check.py 仍接受老 [Primary] 格式 (item 9), 但加了 item 13 (URL 机械验证) 作为更可靠的指标

---

# Surrogate Sources Policy (Q5 deep mode)

> 本节用于冷僻行业 (cold_detector verdict = cold_deep_mode / cold_too_thin) 的 fallback 来源策略.

冷僻行业 (figures<5 / sources<5 / canon<8 / verified_primary<40%) 的特征: 网上公开素材薄, 但**不一定是真"冷"** — 通常是**专业 / 闭源 / 区域性 / 新兴**, 一手资料藏在非公开渠道里. 单纯降阈值会得到稀薄的 SKILL.md.

正确路径: 用 surrogate sources 把厚度堆回来, **但严格标注 surrogate 而非 primary**, 让 SKILL.md 诚实边界节能告诉用户「这部分是从 surrogate 推出来的, 不是直接从 figure 嘴里听到的」.

## 可接受的 surrogate 类别

| Surrogate type | 适用 track | 标注方式 | 使用场景 |
|---------------|-----------|---------|---------|
| **行业协会 / 学会** (AOFAS, ACM, 中华医学会 等) 的官网 + 期刊 | 01 / 04 / 06 | bucket: `surrogate_primary`, note 写「行业协会」 | figure 太少时, 协会理事 / fellow 列表是隐性 figure 池 |
| **监管 / 立法文件** (gov 域名) | 03 / 04 / 06 | bucket: `verified_primary` (这些本来就是一手) | 强监管行业 (法律 / 医疗 / 金融) 的 ground truth |
| **大学课程 syllabus / lecture notes** (.edu 域名) | 04 / 06 | bucket: `surrogate_primary`, note 写「课程 syllabus」 | canon 不足时, syllabus 的 reading list 是隐性 canon |
| **招聘 JD (大厂 / niche 公司)** | 02 / 03 | bucket: `surrogate_primary`, note 写「JD 推断」 | 工作流 / 工具栈不足时, JD 列出的 stack + responsibility 是间接观察 |
| **会议 sponsor list + sessions list** | 01 / 02 / 05 | bucket: `surrogate_primary`, note 写「会议 sponsor」 | sources 不足时, 大会 sponsor 是 active 工具供应商 |
| **供应商 / vendor docs** (品牌官网) | 02 / 06 | bucket: `verified_primary` (这是 vendor 一手) | 必备工具识别 — 但 mental model 不能仅靠 vendor 一面之词, 要 ≥ 2 source consensus |
| **内部素材 (用户提供)** | 全部 | bucket: `verified_primary`, note 写「user-provided」, 不放具体 URL 在 manifest 中 (隐私) | local_materials.mode = mixed/local-first 时的最高权重 source |

## 黑名单 surrogate (绝不替代 primary)

- LinkedIn 公司主页 / SEO 农场榜单 / Quora 答案 — **不是** surrogate, 是噪音
- AI 自动总结站 (notebooklm-style summaries 网) — 内容来源不可追溯
- 个人公众号 / 知乎专栏 (除非作者本人是该 figure, 否则仍黑名单)
- 厂商 PR 通稿 (businesswire / prnewswire 等) — 永远不进 manifest

## 标注示例

```markdown
| S017 | https://www.aofas.org/about/officers | surrogate_primary | 2026-05-04 | AOFAS | 协会 fellow 列表 — 推断隐性 figure 池 |
| S018 | https://www.npc.gov.cn/.../民法典 | verified_primary | 2026-05-04 | 全国人大 | 法律 ground truth — 立法机构原文 |
| S019 | https://stanford.edu/cs329a/syllabus | surrogate_primary | 2026-05-04 | Stanford CS329A | 课程 reading list 推断 canon |
| S020 | (user-provided 内部 SOP) | verified_primary | 2026-05-04 | (anonymized) | 用户内部素材 — 不在网上, 权重高 |
```

## SKILL.md 诚实边界节怎么写

冷僻 + deep mode 跑完, SKILL.md 「诚实边界」节要明说:

```markdown
- **数据厚度**: figures 维度 N (低于一般阈值 5), 部分 figures 通过 surrogate (协会理事列表 / 大会 keynote
  spk) 间接识别, **未直接听到他们公开发声**. 提炼出的 mental model 在 figures 一致性维度上比丰满行业弱.
- **Surrogate 比例**: source_pool 中 X% 是 surrogate_primary 而非 verified_primary, 主要来自 {协会 / 监管 /
  syllabus / JD}. 用户在使用 SKILL.md 时, mental_model 节的 claim 要做二次校验.
```

不写诚实边界 = 把薄数据冒充丰满 OS, 是质量红线.
