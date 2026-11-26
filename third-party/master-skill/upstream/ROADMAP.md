# Roadmap

## v0.1 — Draft ✅

- [x] `SKILL.md` v0.1：agent-facing 工作流规约，5 phases + 3 质量关卡
- [x] `README.md`：项目意图 + 触发词 + 安装方式
- [x] `.gitignore`：secrets / 生成产物

## v0.2 — Templates & Prompts ✅

- [x] `references/skill-template.md`：生成产物的 SKILL.md 标准结构
- [x] `references/extraction-framework.md`：提炼方法论
- [x] `prompts/intake.md`：Phase 0 行业澄清问卷
- [x] `prompts/research/01-figures.md` 至 `06-glossary.md`：6 个 subagent 的 task 模板
- [x] `prompts/synthesis.md`：Phase 2 提炼指引
- [x] `prompts/quality_check.md`：Phase 4 验证 rubric

## v0.3 — Tooling ✅

- [x] `tools/skill_writer.py`：从临时 meta + content 文件生成完整 skill 目录
- [x] `tools/research/merge_research.py`：合并 6 轨调研 → Phase 1.5 摘要
- [x] `tools/research/quality_check.py`：Phase 4 机械 rubric runner
- [x] `tools/transcribe/youtube.sh`：yt-dlp 多语言字幕优先级
- [x] `tools/transcribe/srt_to_transcript.py`：SRT/VTT → 干净文本
- [x] `tools/install.py`：装到 Claude Code / OpenClaw / Codex / Hermes (含 `--host all`)

## v0.4 — Polish & Self-correction ✅

- [x] skill_writer 注入 synthesis body 到 SKILL.md（self-contained 输出）
- [x] skill_writer 自动从 research/ 计算 primary_source_ratio
- [x] Time-decay Registry 显式标记 (`last_updated` + `decay_risk`)
- [x] Adaptive cold floor (industry-type 多项式)
- [x] Cross-track contradiction detection (heuristic)
- [x] Voice-check 部分机械 surrogate (Tier-1 jargon counting)
- [x] Tool-tier 02-tools.md fallback parsing
- [x] VTT NOTE multi-line block 正确过滤
- [x] install --host all 多宿主一键 install
- [x] 版本 drift 警告

## v1.0 — End-to-end Validated ✅

- [x] LLM agent infra prototype 真实跑通 Phase 0 → 4
- [x] Phase 4 mechanical rubric verdict: PASS (10 pass / 1 partial / 0 fail)
- [x] Repo 公开
- [x] 至少 1 个真实行业的 sample skill 进入 prototypes/

## v0.6 — CLI tool stream (用户方向 2026-05-02) ✅

生成的 `{industry}-master.skill` 不只是 markdown，还包含可被 bash 调用的 CLI scripts：

- [x] `references/cli-spec.md`：完整 spec (目录布局 + 三类脚本 + 标准接口)
- [x] `tools/cli_writer.py`：从 synthesis 解析 + emit cli/ subtree
- [x] Section 9 Agentic Protocol → `cli/protocol/agentic.sh`
- [x] Section 2 Playbook 聚类 → `cli/decision/{cluster}.sh` (含 general-playbook 兜底)
- [x] research/03-workflows.md SOP → `cli/workflow/{slug}.sh`
- [x] 标准接口 `--help` / `--explain` / `--dry-run` / `--json` 全部实现
- [x] skill_writer create 默认调 cli_writer (新增 `--no-cli` 旁路)
- [x] 模板 + prompts 同步, 引导 synthesis 输出 CLI-friendly 格式
- [x] 验证 prototype 1 (LLM agent infra): 11 scripts emitted, all bash -n pass
- [x] 验证 prototype 2 (跨境电商, zh-CN): 5 scripts emitted, general-playbook 兜底成功

## v1.1 — Cross-skill composition + Increment ✅

- [x] Phase 3 Step 3 详 spec：调 [女娲.skill](https://github.com/alchaincyf/nuwa-skill) 蒸馏 top 3 figures → 嵌入 sub-skills/
- [x] `prompts/sub-skill-figures.md`：subagent 调女娲的 prompt template
- [x] `tools/update_skill.py`：plan / archive / mark-in-progress / finalize 四 action
- [x] 衰减速度按 track 自动检测 (per-track refresh_at_months 表)
- [x] update 流程支持 changelog 追加

## v1.2 — Cluster 自动学 + cron + 5 个行业样本 ✅

- [x] cli_writer cluster keywords 自动从 synthesis 学习 (mental models + playbook + protocol 加权抽词频)
- [x] 中英 stopword 过滤, 中文 character n-gram, 英文 word-level
- [x] cluster anchor 保留原文 (中文 anchor 显示中文 topic_title, 文件名走 topic-N 兜底)
- [x] tools/update_skill.py schedule action — 生成 macOS launchd plist + Linux cron 一行
- [x] 检查频率按 skill 最高 decay 模块自动决定 (high → 周, medium → 月, low → 季)
- [x] 小红书运营 prototype (内容运营行业)
- [x] SEO 专家 prototype (半技术行业)
- [x] 恋爱高手 prototype (软技能 / 非工作类行业)

## v1.3 — 8 个行业样本横切覆盖 ✅

- [x] 短视频投流 master skill (商业 + 算法投放)
- [x] 足踝外科 master skill (医疗强监管)
- [x] 法律 master skill / 中国法 (法律强监管)

8 个 prototype 横切覆盖技术 / 商业 / 内容运营 / 软技能 / 医疗 / 法律。

## v1.4 — 质量工程升级 + 第 9 个行业 ✅ (2026-05-05)

iter 24-26 集中 14 项 Q1-Q6 改造, 把 "agent 自报一手率" 替换为机械验证.

- [x] Source Manifest convention (T01-S001 全局 source_id + URL 5 桶分类)
- [x] 16 项 quality_check rubric (含 URL 验真 / 黑名单 / 一致性 / claim 反查)
- [x] source_verifier (zh-CN + en 黑白名单 / blacklist hard-block)
- [x] source_manifest 一致性 gate (declared > auto without surrogate note → violation)
- [x] claim_verifier (反查 SKILL.md 每条结论是否在原文有支撑)
- [x] cold_detector --stage wave1|full (行业冷僻自动兜底)
- [x] 8 个 collectors (github / arxiv / RSS / podcast + 4 surrogate: regulator / association / JD / syllabus)
- [x] 4 个 ingest 工具 (PDF / EPUB / PPTX → JSONL chunks)
- [x] transcribe 升级 (faster-whisper + pyannote diarize + transcript_scorer + extract_mentions)
- [x] skill_writer atomic write + bounded backup prune
- [x] 4 轮 codex 独立审计每轮 fix
- [x] 第 9 个行业 prototype: insurance-broker-cn-master (73 sources / 91.8% 一手 / 0 黑名单 / 16 项 14 满分 1 部分 0 失败 PASS)
- [x] README 重写 — 删除中英混杂 + 开发术语, "蒸不出垃圾" banner

## v1.5 — 第 10 个行业 + 学派分歧蒸馏 ✅ (2026-05-08)

第一个半敏感 + 学派分歧大行业蒸出来, 验证大师.skill 框架对"同盘多派给不同结论"行业的处理能力.

- [x] bazi-metaphysics-master prototype (八字命理 + 玄学算命)
  - 6 轨调研 1183 行, 125 manifest URLs, 72.8% 一手, 0 黑名单
  - synthesis 379 行, 6 心智模型 + 10 决策规则 + 12 对话样本 (4 register) + 5 流派矩阵
  - SKILL.md 426 行 + cli/ (1 protocol + 4 decision)
  - 3 sub-skills 跨派对位 (段建业盲派 530 / 倪海厦五术 463 / 梁湘润子平学科化 373)
  - 4 项质检全部 PASS (rubric / claim / manifest / self_test)
- [x] 学派分歧保留, 不平均化 — 子平 / 盲派 / 五术 / 新派 / 学院派 5 派 6 维度对照矩阵
- [x] 大陆法律语境 — 治安管理处罚法 27 条 2026-01-01 新版 W8 商业合规决策树
- [x] source_verifier 加 4 个 zh-CN 古籍 archive 主源 (ctext.org / guoxuedashi.net / zh.wikisource.org / archive.org) — 永久工具改进, 命理 + 中医 + 历史 canon 通用
- [x] README_en.md 同步至 v1.4 / v1.5
- [x] /tmp/normalize_headers.py + /tmp/fix_manifest.py 临时 helper (cold_detector 期望 ### 头 / manifest bucket auto-fix)

## v1.6 — 第 11 + 12 个行业, skip_sub_skills flag 验证 ✅ (2026-05-09 → 05-10)

跨两个新行业, 验证 master-skill 框架对"量大水分高 + 学派多互相挑衅" 和 "platform-specific + 政策 12 月强制 deadline" 的处理.

- [x] 第 11 个行业: monetize-agents (用 AI agent 赚钱) — 2026-05-09
  - 6 轨调研 1337 行 / 154 manifest URLs / 61% 一手 / 0 黑名单
  - synthesis 442 行 (我手写, 因 spawn agent stalled 600s — 第二次手写经验)
  - 5 派对照 (B2B SaaS / Indie / 咨询 / VC / 国内) 互相挑衅 → 蒸馏不平均化
  - 3 跨派人物 sub-skill 1274 行: Bret Taylor + Pieter Levels + Hamel Husain
  - 4 项质检 PASS (quality 12/2/0/1, claim 16/0/0, manifest 0 violation, self_test 0 issues)

- [x] 第 12 个行业: ios-app-launch (iOS 应用上架) — 2026-05-10
  - 6 轨调研 1227 行 / 169 manifest URLs / 70.4% 一手 / 0 黑名单
  - synthesis 465 行 (我手写, 第三次手写, 模式确立)
  - 6 派对照 (Apple 官方 / Indie / 大厂 release eng / ASO / 反 Apple / 国内合规)
  - 双合规体系 (海外 Apple 单家 vs 国内 4 件套 ICP+算法备案+游戏版号+8-10 应用市场)
  - 政策强制 deadlines: Privacy Manifest 2024-05-01 / Anti-steering 2024-01 / DMA 2024-03-07 / iOS 26 SDK 2026-04-28 / Age Rating 5 档 2026-01-31
  - **跳人物 sub-skill** (用户指示, 验证 skip_sub_skills flag): 节省 1 cron 周期, 总产出仍完整
  - 4 项质检 PASS (quality 13/1/0/1, claim 16/0/0, manifest 0 violation, self_test 0 issues, 12 prototype + tools 全过)

### 12 个行业横切覆盖 (v1.6 后)

| # | 行业 | 类别 | 语言 | 学派多样性 |
|---|------|------|------|-----------|
| 1 | LLM agent infra | 技术 | 英文 | 中 |
| 2 | 跨境电商运营 | 商业 | 中文 | 中 |
| 3 | 小红书运营 | 内容运营 | 中文 | 低 |
| 4 | 短视频投流 | 商业 + 算法 | 中文 | 低 |
| 5 | SEO 专家 | 半技术 | 中文 | 低 |
| 6 | 恋爱高手 | 软技能 | 中文 | 高 (Gottman / EFT / Esther Perel) |
| 7 | 足踝外科 | 医疗强监管 | 中文 | 中 |
| 8 | 中国法律执业 | 法律强监管 | 中文 | 中 (民法 / 刑法 / 普法) |
| 9 | 保险经纪人 | 金融强监管 | 中文 | 中 (平安系 / 明亚 / 测评派) |
| 10 | 八字命理 / 玄学算命 | 传统文化半敏感 | 中文 | **高 (5 派同盘不同结论)** |
| 11 | 用 AI agent 赚钱 | 新兴商业 | 全球 | **高 (5 派互相挑衅)** |
| 12 | iOS 应用上架 | 平台 specific 政策高变化 | 全球 + 中文 | **高 (6 派对照矩阵)** |

后 3 个 (10/11/12) 都是"学派分歧 = 行业特征"的 high-divergence 行业, 验证 master-skill 框架对 high-divergence 行业的健壮性.

## v1.7 — SkillOpt 整合 + 第 13 个行业 ✅ (2026-05-27)

从 [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) 借鉴 5 个机制, 让蒸馏管线可以自我进化:

- [x] **SLOW_UPDATE 保护区** (`skill_writer.py`) — 生成的 SKILL.md 自动标记低衰减区域 (心智模型 / 表达 DNA / 智识谱系), 增量更新时 patch editor 跳过, 核心 OS 不被快更冲散
- [x] **Validation Gate** (`tools/research/validation_gate.py`) — Phase 4 accept/reject 门控, 加权评分区分 critical failure 一票否决 与 partial 可接受降级
- [x] **Patch Editor** (`tools/patch_editor.py`) — 4 种结构化编辑操作, 每步检测是否落入保护区
- [x] **Meta Skill Memory** (`tools/meta_skill.py`) — 跨蒸馏学习记忆 (`meta_skill_memory.json`)
- [x] **DL 类比框架** — skill=权重 / patch=梯度 / edit budget=学习率 / SLOW_UPDATE=frozen layers
- [x] 第 13 个行业端到端验证: 公务员考试培训 — 171 来源 / gate ACCEPT 0.90 / 3 个 SLOW_UPDATE 区域成功注入

## v1.8 — 深度蒸馏扩容 43 → 72 行业 ✅ (2026-05-18 → 07-04)

deep-distill 流水线连续运转六周+, 从 13 个样本扩到 72 个, README 分类扩到 12 大类:

- [x] 新增 29 个行业 (v1.7 后): 家庭教育指导 / Figma 转 PSD / 研学营地教育 / AI 短剧 / 语音转文字 ASR / K12 体育培训 / 德州扑克策略 / Web 线上展览 / 侍酒师与葡萄酒 / 调香师与香水 / 管理咨询 / B2B 大客户销售 / 临床诊断思维 / 小红书 & 推特 & 知乎 AI 自媒体博主 / UBNT 企业 Wi-Fi / 个人投资理财 / 音乐制作混音 / 摄影 / 产品 UX 设计 / 投行并购 / 网文写作 / 加密链上交易 / 医疗美容 / 半导体制造工艺 / AIGC 创作工作流 / 广告外包公司绩效管理 / 亚马逊管理之道 等
- [x] 新大类: 手艺 / 品鉴 / 生活方式 (调香 / 侍酒 / 音乐制作 / 摄影 / 德扑)
- [x] `self_test.py` 全量回归: 72 prototypes + 工具冒烟 0 issues
  - cold_detector 接受 `output/` 子目录调用 (向上解析 prototype root), error 报告回显 stage
  - scriptwriting 调研留痕归位到标准位置 (`{proto}/references/`)
  - ceo-master 3 个人物 sub-skill 补齐 frontmatter (name / description / triggers)
  - 2 个早期深蒸样本 (ceo / game-design) 调研档未入库 → meta.json `research_trail: false` 诚实标注, self_test 报 informational 不计 issue
  - SKILL.md 中标注「待生成」的 sub-skill 前向引用不再误报为断链
- [x] GitHub Actions CI: push/PR 自动跑 self_test

## v1.x — 计划中

- [ ] Phase 1 子 agent 主动用 brave-search / agent-reach
- [ ] 调 web-article-reader 精读关键文章
- [ ] cli_writer 生成的 cluster 中文 anchor 加 transliteration (eg 「合规」→ "compliance")

## v2.x — Distribution

- [ ] 多语言 README (中英日韩)
- [ ] 与 dot-skill / nuwa-skill 互相引用
- [ ] PyPI 打包 `master-skill` 命令
- [ ] GitHub Action: 自动 update 已 fork 的 industry skill repos

---

## 非目标（明确不做）

- **不做行业实操工具**：master skill 是「认知操作系统」，不是 RPA。比如蒸馏「跨境电商」不会包含「自动登录 Amazon Seller Central」
- **不做版权侵权**：不存全本书 / 完整字幕 / 长段原文。只保留结构化摘要 + 来源元数据 + 极短引用
- **不做行业新闻聚合**：master skill 不是 newsfeed。最新动态以「指向哪些信息源」的形式存在，不直接搬内容
