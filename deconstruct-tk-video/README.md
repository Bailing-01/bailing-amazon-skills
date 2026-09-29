# deconstruct-tk-video

> **作者**：[bailing](https://github.com/Bailing-01) ｜ 公众号「Bailing跨境」
>
> 亚马逊官方讲师 · 第三方卖家 10 年 · 前 10 亿级卖家运营经理 · 美国 PMP 项目认证
>
> 开发过多款亚马逊相关课程，目前致力于用 AI 把亚马逊的所有工作流全部自动化。

## 这个 Skill 做什么

TK 视频拆解：输入本地视频、单条公开 TikTok 链接或 account_manifest.json，完成环境检查、下载、转写、语义抽帧和覆盖验收。  
先整批确认内容提取，再做十项证据化拆解、重复素材聚类、候选评分和可迁移元素沉淀，输出 breakdown_bundle.json 和 Markdown。  
不生成九版脚本，不写入飞书。

## 怎么用

触发词：TK/TikTok 视频转写、翻译、竞品拆解、Hook 对照、素材分析、为下游脚本生成准备拆解数据

安装：把本文件夹复制到你的 Agent skills 目录即可（完整说明见 `SKILL.md`）。

```bash
git clone https://github.com/Bailing-01/bailing-amazon-skills.git
# Claude Code；Codex / Hermes 等换成对应的 skills 目录
cp -r bailing-amazon-skills/deconstruct-tk-video ~/.claude/skills/
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
