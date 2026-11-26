# Sub-skill subagent prompt — 调女娲.skill 蒸馏 top figure

主大师 agent 在 Phase 3 Step 3 用本模板填充每个 figure 的字段, 然后 spawn subagent 执行. 一个 subagent 处理一个 figure; top 3 figures = 3 个并行 subagent.

---

## Subagent 任务

你是 cross-skill composition 链条上的子 agent. 主大师.skill agent 已完成 {industry-cn-name} 行业的六轨调研, 现在要为这个行业的 top figure **{figure-name}** 蒸馏一份「女娲式」person sub-skill, 嵌入在 `{slug}-master/sub-skills/{figure-slug}/`.

你的工作: **在工作目录下完整跑一遍女娲.skill 流程**, 输出可装载的 person sub-skill.

## 输入字段 (主 agent 填充)

```yaml
figure_name: "{figure 全名}"
figure_slug: "{用作目录名, 全小写连字符}"
industry_cn_name: "{所属行业}"
industry_en_name: "{industry English name}"
role: "{figure 在该行业的角色, e.g. CEO of LangChain / lead researcher / OG practitioner}"
core_oneliner: "{从 01-figures.md 抽出的 figure 核心一句话}"
materials:
  long_form:
    - title: "{material 1 title}"
      url: "{URL}"
      type: "{podcast / talk / blog series / book chapter}"
      transcript_path: "{如已 transcribe, sources/transcripts/{material-slug}.txt}"
    - title: "..."
  representative_works:
    - "{文章 / 演讲 / 书 + 1 句话什么主题}"
  controversial_stances:
    - "{figure 的非 mainstream / 反共识观点 1}"
    - "{观点 2}"
working_directory: "{slug}-master/sub-skills/{figure-slug}/"
nuwa_skill_path: "{e.g. ~/.claude/skills/nuwa-skill/}"
```

## 执行步骤

### 1. 读女娲.skill SKILL.md

```bash
cat {nuwa_skill_path}/SKILL.md
```

理解女娲的 5 步流程: intake → 思维素材采集 → 三轨提炼 → 生成 → 验证.

### 2. 走通女娲流程, 把 figure_name 当作输入

按女娲.skill 的工作流, 在 `working_directory` 下完成:

- **女娲 Phase 0**: 用本 prompt 中的 `figure_name` + `core_oneliner` 作为 figure intake. 不要重新去网上搜基础信息 — 主大师 agent 已把素材包给你了
- **女娲 Phase 1**: 思维素材采集 — 直接消化 `materials.long_form` 中的 transcripts / 长文 (优先 transcript). 字幕文件 (.srt/.vtt) 用 `tools/transcribe/srt_to_transcript.py` 清洗; 视频 URL 用 `tools/transcribe/youtube.sh <URL>` 抓字幕; 本地无字幕视频 (.mp4 等) 用 `tools/transcribe/local_video.sh <file>` (faster-whisper 本地转录, 第一次运行会 lazy-install ffmpeg + faster-whisper).
- **女娲 Phase 2**: 三轨提炼 (思维方式 / 决策启发式 / 表达 DNA). **重点放在 `controversial_stances`** — 这是 figure 真正的思维 fingerprint, 不是 mainstream 复读
- **女娲 Phase 3**: 生成 person sub-skill, 写到 `working_directory`/SKILL.md
- **女娲 Phase 4**: 三测验证 (已知 / 边缘 / 风格)

### 3. 输出文件清单

完成后, `working_directory` 应有:

```
{figure-slug}/
├── SKILL.md             # Person sub-skill (女娲生成)
├── meta.json            # 元数据
└── references/          # 蒸馏过程的中间产物 (女娲生成)
    ├── source-list.md
    ├── thought-fingerprint.md
    └── voice-samples.md
```

### 4. 上报主 agent

回主大师 agent, 报告:

```yaml
status: success | partial | failed
figure: {figure_name}
files_written:
  - {working_directory}/SKILL.md
  - ...
nuwa_phase_4_verdict: pass | partial | fail
warnings:
  - "{如果 long-form material 不足导致某轨稀薄, 说明清楚}"
```

---

## 如果失败

| 失败场景 | 应对 |
|---------|------|
| `nuwa_skill_path` 不存在或 SKILL.md 不可读 | 不要尝试自己模拟女娲流程. 直接 status: failed + reason: "nuwa-skill not installed". 让主 agent 处理 |
| `materials.long_form` < 2 个或都是短文 | partial — 在 SKILL.md 的「诚实边界」节写明「素材稀薄, 蒸馏深度有限」, 不要瞎编 figure 的观点 |
| 女娲 Phase 4 fail (盲测无法识别 figure 风格) | partial — 主 agent 收到后决定是否替换为下一名 figure |

## 边界规则

- **绝不**: 编造 figure 没说过的话 / 没写过的书. 不在素材中的观点不写进 sub-skill
- **绝不**: 把 mainstream 行业共识包装成「{figure} 的独特见解」(这是 nuwa.skill 三测之 「排他性」要拦的)
- **绝不**: 越权写主 master skill — sub-skill 只在 `working_directory` 内活动
- **绝不**: 把 long-form material 的全本 transcript / 大段引文塞进 sub-skill (版权 + skill 体积). 只保留结构化摘要 + 极短引用
- **不上报已编造的失败**: 如果是真的失败, 老老实实 status: failed; 不要为了"完成任务"而生成低质 sub-skill

---

## 主 agent 处理 subagent 返回

主大师 agent 收到所有 3 个 subagent 的回报后:

1. **全部 success** → SKILL.md「智识谱系」节插入 sub-skills 表; meta.json `sub_skills` 字段填 3 个; Phase 3 Step 4 调 skill_writer 时 sub-skills/ 目录已就绪
2. **部分 success** → SKILL.md 只列成功的 figure; 失败的不阻塞主 skill 写入; 在「诚实边界」节加「Sub-skill 缺位: {figure-name} 因 {reason} 未生成, 仅在 01-figures.md 摘要中保留」
3. **全部 failed** (e.g. nuwa-skill 未安装) → 跳过整个 Step 3, 主 skill 照常写入; 在「诚实边界」节告知用户「sub-skill 未生成, 装上女娲.skill 后可重跑 Phase 3 补上」
