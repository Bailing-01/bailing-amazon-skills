---
name: GoMarble 效果广告诊断
description: >-
  上游 gomarble-ai/marketing-agent：通过 GoMarble 的 OAuth MCP，诊断 Meta、Google、TikTok、LinkedIn、Microsoft Ads 以及 GA4、Shopify 等账户。
  不连接亚马逊广告 API，也不要把结论直接写成亚马逊改价。
  任何会改广告账户的动作默认停在预检 / dry-run。不要把 token 写入仓库。
---

# GoMarble 效果广告诊断（默认只预检）

本文件是 Bailing 写的使用说明，优先级高于 `upstream/skills/` 里任何「用户点头就可以改账户」的句子。上游项目、许可证和作者见 `ATTRIBUTION.md`。

## 它连接的平台

GoMarble MCP：`https://apps.gomarble.ai/mcp-api/mcp`（见 `upstream/.mcp.json`，只有 OAuth 元数据地址，没有密钥）。上游 README 列出的渠道包括：

- 广告：Meta Ads、Google Ads、TikTok Ads、LinkedIn Ads、Microsoft Ads
- 站点与店铺：GA4、Shopify、Klaviyo、Search Console、Facebook / Instagram 主页、impact.com
- 其他：Snowflake（只读查询）、Google Drive、广告资料库

这个清单里没有 Amazon Ads，也没有领星。不要从本技能发起 Amazon Advertising API 调用。

上游技能在 `upstream/skills/`。常见入口：`diagnose-performance`、`analyse-creative`、`clean-wasted-spend`、`shift-budget`、`launch-campaigns`、`manage-campaigns`、`build-reports`。细节以各目录的 `SKILL.md` 为准。

## 亚马逊卖家怎么用

用它解释**站外**账户为什么变了：哪个素材疲劳、哪类搜索词在浪费、预算该在 Meta/Google/TikTok 之间怎么看。输出是事实、假设和缺失数据。

若结论要影响亚马逊广告，写成建议，交给 `sp-sb-sd/` 与 `bid-placement-optimization/`。不要把 Google 的非品牌 ROAS 或 Meta 的 CPA 门槛直接当成亚马逊 ACoS 规则。

## 改账户：默认预检

分析、素材解读、竞品研究和报表保持只读。

下列动作一律先停在 preflight / dry-run，展示「当前值 → 拟变更 → 预期影响」，然后停下：

- 新建、复制、暂停、启用、删除广告或广告组
- 改预算、出价、tCPA、受众、否定词、素材或落地页
- `launch-campaigns`、`shift-budget`、`manage-campaigns`、`clean-wasted-spend` 里的执行步骤
- 定时 agent 的启用

默认不要调用写入、execute、submit 或 apply 工具。用户看完这一次预检并明确说「执行这一条」之后，才可以按上游 GoMarble 自己的审批再往下走；上游仍要求人工批准，新广告默认暂停。没有这条明确指令时，到预检为止。

不要把 OAuth token、刷新令牌、示例密钥或 `.env` 写进仓库或对话摘录。连接在用户自己的 GoMarble 登录里完成。
