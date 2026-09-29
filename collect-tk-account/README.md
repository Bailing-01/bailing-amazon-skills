# collect-tk-account

> **作者**：[bailing](https://github.com/Bailing-01) ｜ 公众号「Bailing跨境」
>
> 亚马逊官方讲师 · 第三方卖家 10 年 · 前 10 亿级卖家运营经理 · 美国 PMP 项目认证
>
> 开发过多款亚马逊相关课程，目前致力于用 AI 把亚马逊的所有工作流全部自动化。

## 这个 Skill 做什么

TK 账号采集：采集公开 TikTok 账号主页视频，默认取执行日前 30 天内播放量 Top 10。  
做纯 MP4 过滤、视频 ID 去重、排名缓存，下载原视频和公开元数据，输出 tk-content-pipeline/v1 的 account_manifest.json。  
不做转写、抽帧、内容分析、脚本生成或飞书入库。

## 怎么用

触发词：提供 TikTok/TK 账号主页并要求拉账号、采集竞品视频、下载近期爆款、为视频拆解准备批量输入

安装：把本文件夹复制到你的 Agent skills 目录即可（完整说明见 `SKILL.md`）。

```bash
git clone https://github.com/Bailing-01/bailing-amazon-skills.git
# Claude Code；Codex / Hermes 等换成对应的 skills 目录
cp -r bailing-amazon-skills/collect-tk-account ~/.claude/skills/
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
