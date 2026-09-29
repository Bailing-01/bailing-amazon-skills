# asin-listing-risk-monitor

> **作者**：[bailing](https://github.com/Bailing-01) ｜ 公众号「Bailing跨境」
>
> 亚马逊官方讲师 · 第三方卖家 10 年 · 前 10 亿级卖家运营经理 · 美国 PMP 项目认证
>
> 开发过多款亚马逊相关课程，目前致力于用 AI 把亚马逊的所有工作流全部自动化。

## 这个 Skill 做什么

ASIN Listing 风险监控：按站点检查关键词可搜索性与自然 / 广告位、广告开关与花费信号、差评较昨日变化、标题/五点/A+ 违禁词。  
对比 US 与 CA/MX/EU 的变化扩散，输出简短结论 + 行动项；缺失字段写「无数据」。配套本地骨架见仓库根目录 `asin-risk-monitor/`。

## 怎么用

触发词：检查 Amazon Listing / ASIN 风险（关键词、广告、差评、违禁词、跨站点 US/CA/MX/EU 扩散）

安装：把本文件夹复制到你的 Agent skills 目录即可（完整说明见 `SKILL.md`）。

```bash
git clone https://github.com/Bailing-01/bailing-amazon-skills.git
# Claude Code；Codex / Hermes 等换成对应的 skills 目录
cp -r bailing-amazon-skills/skills/asin-listing-risk-monitor ~/.claude/skills/
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
      <img src="../../assets/oa-qr.jpg" width="200" alt="微信公众号 Bailing跨境 二维码">
    </td>
    <td align="center" width="50%">
      <strong>个人微信｜bailing</strong><br><br>
      同行交流、合作、Skill 共建<br><br>
      <img src="../../assets/wechat-qr.jpg" width="200" alt="bailing 个人微信二维码">
    </td>
  </tr>
</table>
