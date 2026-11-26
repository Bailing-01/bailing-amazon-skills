---
name: 行业 Master OS 生成器
description: >-
  上游是 swaylq/master-skill：输入一个细分行业，调研六轨并生成「行业 Master OS」skill。
  它不是短视频素材诊断产品，也不连接亚马逊广告、领星或巨量引擎。
  当卖家要把「亚马逊短视频素材诊断」或「Sponsored Brands 视频创意」蒸馏成可复用的行业判断框架时使用。
  账户调价、否词和广告结构仍交给本仓库已有的亚马逊广告技能。
---

# 行业 Master OS 生成器（亚马逊 / 短视频用法）

本文件是 Bailing 写的使用说明，不是上游作品。上游原文、许可证和作者在 `upstream/` 与 `ATTRIBUTION.md`。

## 上游实际是什么

[swaylq/master-skill](https://github.com/swaylq/master-skill) 是一个**行业 Master OS 生成器**（MIT，作者 swaylq）。给定一个细分行业，它按六轨调研——行业人物、工具地图、工作流、知识正典、信息源、术语标准——再写成一个可安装的行业 skill。执行步骤以 `upstream/SKILL.md` 为准。

公开传播里出现过「Short Video Ads Master / 短视频素材诊断」这个名字。仓库里与之对应的是**生成样本** `upstream/prototypes/short-video-ads-master/`，不是这个仓库的产品定义。该样本的 `intake.json` 写明行业是 **short-video paid advertising (China platforms) / 短视频投流**，焦点是巨量引擎信息流和电商直播，触发词含「巨量引擎」「千川」。样本 README 也写了：多数调研轨是占位，只有工作流轨相对完整。把它当成亚马逊素材诊断器，或当成已经接好的广告 API，都是误读。

## 平台边界

| 能做 | 不能做 |
| --- | --- |
| 把一个窄行业蒸馏成思维框架、playbook 和工作流 | 读取或修改任何广告账户 |
| 为亚马逊短视频创意问题生成一份行业 skill | 调用 Amazon Ads、领星、Helium 10、巨量引擎、Meta、Google、TikTok 的 API |
| 指向已生成的中国平台短视频投流样本，供对照 | 把该样本的巨量/千川口径套到亚马逊 ACoS |

巨量千川的真实账户操作用 `third-party/ocean-watch/`。亚马逊 SP/SB/SD 结构和竞价用仓库根目录的 `sp-sb-sd/` 与 `bid-placement-optimization/`。

## 亚马逊卖家怎么用

1. 先读 `upstream/SKILL.md`，按其中的 Phase 0–5 执行。工具脚本在 `upstream/tools/`，模板在 `upstream/references/` 与 `upstream/prompts/`。不要改这些上游文件来假装它已经是亚马逊技能。
2. 行业粒度要窄。可用的行业名示例：`亚马逊短视频素材诊断`、`Amazon Sponsored Brands video creative`、`跨境品牌短视频完播与点击诊断`。不要用「电商」或「广告」这种过宽的词。
3. 告诉生成器：交付物是判断框架（钩子、前三秒、完播、点击、与详情页是否一致），不是自动改价，也不是拉报表。
4. 生成结果只作为创意与brief的思考操作系统。需要改亚马逊竞价或广告结构时，把结论交给已有亚马逊技能，由那些技能给出建议清单。
5. 若问题其实是巨量/千川账户里的计划、素材和报表，停用本技能，改用 `third-party/ocean-watch/`。`short-video-ads-master` 只是中国平台的不完整样本。

## 版权

遵守上游规则：不把整本书、完整字幕或长段原文写进生成的 skill。只保留结构化摘要、来源信息和极短引用。其余 80 个行业原型没有收录，名单见 `OMITTED_PROTOTYPES.txt`。
