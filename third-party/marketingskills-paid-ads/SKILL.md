---
name: 站外付费广告策略与创意
description: >-
  收录 Corey Haines marketingskills 里的 paid ads 技能（skills/ads）和它引用的广告创意技能（skills/ad-creative）。
  平台是 Google、Meta、LinkedIn、TikTok、X，不是亚马逊广告。
  当卖家要借用这套站外投放的预算、审计和素材判断，再交回本仓库的亚马逊广告技能落地时使用。
  只给建议，不自动改任何广告账户。
---

# 站外付费广告策略与创意

本文件是 Bailing 写的使用说明。上游原文在 `upstream/skills/`，许可证和作者见 `ATTRIBUTION.md`。

## 收录了什么

来自 [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)（MIT，Corey Haines）的两个技能，以及它们目录内的 references、evals 和 ad-creative 的本地模板。二者互相用相对路径引用，所以必须一起放在 `upstream/skills/` 下。

| 技能 | 上游文件 | 用途 |
| --- | --- | --- |
| `ads` | `upstream/skills/ads/SKILL.md` | 付费广告是否值得做、渠道与预算、CPA 升高时怎么判断、关停或保留 |
| `ad-creative` | `upstream/skills/ad-creative/SKILL.md` | 标题、正文、钩子和素材角度；`ads` 把写文案指到这里 |

先读上游 `SKILL.md`，再按它的 Reference Routing 打开同目录 `references/`。缺数据时沿用上游规则：标成 MISSING，不要估一个数。

## 平台边界

上游覆盖的是 **Google Ads、Meta、LinkedIn、TikTok、X**。playbook 里的 CPA、学习期、Andromeda、RSA、PMax 阈值是这些平台的口径。

不要把这些阈值当成亚马逊 ACoS、TACoS 或广告位溢价规则。亚马逊 SP/SB/SD 的结构和竞价建议用仓库根目录的 `sp-sb-sd/` 与 `bid-placement-optimization/`。本目录没有亚马逊广告 API，也不要补一个。

## 亚马逊卖家怎么用

1. 把问题说成站外判断：这条 Meta/Google/TikTok 素材或预算决策，对亚马逊详情页和广告创意有什么可迁移的结论。
2. 用 `ads` 做策略、审计和周检；用 `ad-creative` 写钩子和短视频脚本假设。假设必须写明指标、对照和预期方向。
3. 结论落到亚马逊时，只输出建议清单（改什么、为什么、观察多久）。真正的亚马逊调价和架构交给已有技能。
4. 账户侧动作保持「草案」：写清当前状态、拟议变更、预期影响和回滚。不要调用会改 Google/Meta/LinkedIn/TikTok 账户的写入工具，除非用户在看完该草案后点名执行这一条。

## 没有收录的上游内容

整个 marketingskills 仓库大约六万 star，技能远不止广告。`conversion-tracking`、`cro`、`copywriting`、`ab-testing`、`analytics`、`attribution` 以及 `tools/` 集成文档都没有复制。上游技能里指向它们的链接在本副本中打不开，请回到 https://github.com/coreyhaines31/marketingskills 。完整未收录名单在 `NOT_VENDORED.txt`。
