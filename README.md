# bailing-amazon-skills

> **作者**：[bailing](https://github.com/Bailing-01) ｜ 公众号「Bailing跨境」
>
> 亚马逊官方讲师 · 第三方卖家 10 年 · 前 10 亿级卖家运营经理 · 美国 PMP 项目认证
>
> 开发过多款亚马逊相关课程，目前致力于用 AI 把亚马逊的所有工作流全部自动化。

亚马逊所有sop基本功 Ai化

新增：
- `bid-placement-optimization/` — 竞价策略与广告位加价优化（旧本地编号 skill-1789097410191）：保本约束下给出底价与广告位溢价建议，只生成建议、不自动改广告
- `amazon-listing-copy/` — 亚马逊 Listing 文案撰写（标题、五点、商品描述、Search Terms 和后台属性），五步采数后写稿
- `kepu-mg-video/` — 商业知识科普动画：原曲卡拍、字幕渐进、柱图与公式因果演示，含定价利润/TACoS教学模型与本地验算脚本
- `asin-risk-monitor/` — Listing/ASIN 风险监控本地骨架（无真实 ASIN 行、无 out/ 扫描产物）
- `skills/asin-listing-risk-monitor/` — 配套监控流程 skill
- `third-party/` — 五个第三方广告技能（带上游 MIT 许可证和署名）。入口说明、亚马逊用法和平台边界见下方专节；总表在 `THIRD_PARTY.md`。

---

## 第三方广告技能

原有技能仍在仓库根目录，或少数在 `skills/` 下：一个文件夹一份 `SKILL.md`。这次没有改那些目录。

第三方快照放在 `third-party/<name>/`，避免和 Bailing 原创技能混放。每个目录的入口 `SKILL.md` 是本仓库写的亚马逊使用说明；上游原文在 `upstream/`，许可证在该目录的 `LICENSE`。详见 `third-party/README.md` 与 `THIRD_PARTY.md`。

| 目录 | 亚马逊卖家用来做什么 | 实际平台（边界） |
| --- | --- | --- |
| `third-party/master-skill/` | 把「亚马逊短视频素材诊断」或 Sponsored Brands 视频创意蒸馏成行业判断框架，再交给已有亚马逊广告技能落地 | 上游是行业 Master OS **生成器**（[swaylq/master-skill](https://github.com/swaylq/master-skill)），不连接任何广告 API。上游随附的 `short-video-ads-master` 只是一份不完整的中国平台（巨量/千川）生成样本，不是亚马逊诊断产品 |
| `third-party/ocean-watch/` | 卖家自己还有抖音/千川账户时，预检巨量计划、查素材和报表 | **巨量引擎 / 巨量千川 / 巨量星图**（[westng/ocean-watch](https://github.com/westng/ocean-watch)）。不是亚马逊广告，也不是领星。写入默认只预检。约 200MB 预编译二进制未收录 |
| `third-party/marketingskills-paid-ads/` | 借用站外投放的预算、审计和素材判断，结论以建议形式交回 `sp-sb-sd/` 与 `bid-placement-optimization/` | 只收录 [marketingskills](https://github.com/coreyhaines31/marketingskills) 的 `ads` 与 `ad-creative`。平台是 Google、Meta、LinkedIn、TikTok、X。其余技能（含 CRO、SEO、文案）留在上游 |
| `third-party/meta-ads-library/` | 用类目词或竞品品牌看 Facebook / Instagram 正在投的公开广告，抽出可迁移的钩子和 CTA | **Meta Ad Library**（[hyperfx-ai/marketing-skills](https://github.com/hyperfx-ai/marketing-skills) 的 `skills/meta-ads-library`）。不创建亚马逊广告。上游另有 `amazon-ads` 技能，本次故意未收录 |
| `third-party/marketing-agent/` | 诊断站外账户为什么波动（素材疲劳、浪费花费、预算），站外改动先出预检 | [GoMarble marketing-agent](https://github.com/gomarble-ai/marketing-agent)：Meta、Google、TikTok、LinkedIn、Microsoft Ads，以及 GA4、Shopify 等。不是亚马逊广告 API。改账户默认 dry-run，仓库内无 token |

五个上游许可证都是 MIT。版权仍归 swaylq、westng、Corey Haines、hyperfx.ai、GoMarble。

---

## 关于作者

我是 bailing：亚马逊官方讲师，第三方卖家 10 年，前 10 亿级卖家运营经理，美国 PMP 项目认证，开发过多款亚马逊相关课程。目前致力于用 AI 把亚马逊的所有工作流全部自动化。

GitHub 放能直接用的 Skill，更多实战复盘先发公众号「Bailing跨境」；也可以直接加我微信，备注「GitHub」。

<table>
  <tr>
    <td align="center" width="50%">
      <strong>公众号｜Bailing跨境</strong><br><br>
      亚马逊实战复盘、踩坑与 AI 提效<br><br>
      <img src="./assets/oa-qr.jpg" width="200" alt="微信公众号 Bailing跨境 二维码">
    </td>
    <td align="center" width="50%">
      <strong>个人微信｜bailing</strong><br><br>
      同行交流、合作、Skill 共建<br><br>
      <img src="./assets/wechat-qr.jpg" width="200" alt="bailing 个人微信二维码">
    </td>
  </tr>
</table>
