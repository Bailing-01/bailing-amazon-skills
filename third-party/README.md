# Third-party advertising skills

本仓库原有技能放在仓库根目录（一个文件夹加一份 `SKILL.md`），另有少数在 `skills/` 下。那些目录是 Bailing 的技能，这次没有改。

这里的五个目录是带上游许可证的第三方快照。每个目录仍是「一个技能文件夹 + 入口 `SKILL.md`」：

- 入口 `SKILL.md` 和 `ATTRIBUTION.md` 是本仓库写的亚马逊使用说明和署名，不是上游原文。
- `LICENSE` 与 `upstream/LICENSE` 是上游 MIT 许可证原文。
- `upstream/` 里的文件按署名文件中的 commit 原样复制，除了各目录 `NOT_VENDORED.txt` / `OMITTED_PROTOTYPES.txt` 写明跳过的部分。

| 目录 | 上游 | 亚马逊场景 | 实际平台 |
| --- | --- | --- | --- |
| `master-skill/` | [swaylq/master-skill](https://github.com/swaylq/master-skill) | 把「亚马逊短视频素材诊断」蒸馏成行业判断框架 | 不连接广告 API。生成器，不是诊断产品 |
| `ocean-watch/` | [westng/ocean-watch](https://github.com/westng/ocean-watch) | 卖家另有抖音/千川账户时预检巨量计划 | 巨量引擎 / 千川 / 星图。不是亚马逊，也不是领星 |
| `marketingskills-paid-ads/` | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) 的 `ads` 与 `ad-creative` | 站外预算、审计和素材判断，再交回亚马逊技能 | Google、Meta、LinkedIn、TikTok、X |
| `meta-ads-library/` | [hyperfx-ai/marketing-skills](https://github.com/hyperfx-ai/marketing-skills) 的 `skills/meta-ads-library` | 查同类目 Facebook/Instagram 公开广告的钩子 | Meta Ad Library。不含上游的 `amazon-ads` |
| `marketing-agent/` | [gomarble-ai/marketing-agent](https://github.com/gomarble-ai/marketing-agent) | 诊断站外账户波动，改账户前先预检 | Meta、Google、TikTok、LinkedIn、Microsoft、GA4、Shopify 等。不是亚马逊广告 |

总署名见仓库根目录 `THIRD_PARTY.md`。
