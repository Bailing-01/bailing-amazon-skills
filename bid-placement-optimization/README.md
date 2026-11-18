# bid-placement-optimization

> **作者**：[bailing](https://github.com/Bailing-01) ｜ 公众号「Bailing跨境」
>
> 亚马逊官方讲师 · 第三方卖家 10 年 · 前 10 亿级卖家运营经理 · 美国 PMP 项目认证
>
> 开发过多款亚马逊相关课程，目前致力于用 AI 把亚马逊的所有工作流全部自动化。

## 这个 Skill 做什么

竞价策略与广告位加价优化：在保本约束下整理底价、动态竞价和广告位溢价，避免「动态竞价 × 广告位加价」叠乘后最高应价失控。

只生成调价建议，不自动改广告、不调用广告接口、不登录 Seller Central。是否执行由使用人自行决定。

正文中的「Bailing 11-17 口径」按原作者口径保留，未改写公式、百分比或踩坑记录。

## 输入与输出

输入（缺利润或转化率时按正文写「无数据」，不套用其他产品的保本线）：

- 单件广告前利润、预估转化率；与目标 ACoS 对照时还需要售价
- 现有基础出价、动态竞价模式、广告位溢价
- Placement 报告中 Top of Search / Rest of Search / Product Pages 的 spend、sales、CPC、CVR、ACoS

输出：

- 本周调价清单：目标 | 旧价 | 新价 | 理由 | 预期观察期
- 广告位变更：活动 | ToS/PP 溢价旧→新
- 风控摘要：叠加后的 Max Eligible Exposure

## 本地编号

本目录对应旧本地编号 `skill-1789097410191`（竞价策略与广告位加价优化）。规则、公式、示例、百分比和踩坑记录与该编号正文一致。

正文里的 `budget-pacing`、`campaign-structure` 是原步骤中的分流名称，不是本仓库链接；本次只导入本 Skill。

## 怎么用

触发词：调出价、动态竞价 up/down、Top of Search 广告位溢价、最高可接受 CPC。完整规则见 `SKILL.md`。

```bash
git clone https://github.com/Bailing-01/bailing-amazon-skills.git
# Claude Code；Codex / Hermes 等换成对应的 skills 目录
cp -r bailing-amazon-skills/bid-placement-optimization ~/.claude/skills/
```

---

## 关于作者

我是 bailing：亚马逊官方讲师，第三方卖家 10 年，前 10 亿级卖家运营经理，美国 PMP 项目认证，开发过多款亚马逊相关课程。目前致力于用 AI 把亚马逊的所有工作流全部自动化。

GitHub 放能直接用的 Skill，更多实战复盘先发公众号「Bailing跨境」；也可以直接加我微信，备注「GitHub」。

<table>
  <tr>
    <td align="center" width="50%">
      <strong>公众号｜Bailing跨境</strong><br><br>
      亚马逊实战复盘、踩坑与 AI 提效<br><br>
      <img src="../assets/oa-qr.jpg" width="200" alt="微信公众号 Bailing跨境 二维码">
    </td>
    <td align="center" width="50%">
      <strong>个人微信｜bailing</strong><br><br>
      同行交流、合作、Skill 共建<br><br>
      <img src="../assets/wechat-qr.jpg" width="200" alt="bailing 个人微信二维码">
    </td>
  </tr>
</table>
