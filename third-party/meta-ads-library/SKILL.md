---
name: Meta 广告资料库竞品调研
description: >-
  上游 hyperfx-ai/marketing-skills 的 skills/meta-ads-library：通过 Hyper MCP 检索 Meta Ad Library 里的 Facebook / Instagram 公开广告。
  用于亚马逊选品和素材前，看同类目站外在投什么钩子和 CTA。
  不查询亚马逊广告，不创建亚马逊广告活动，也不是领星或亚马逊 API。
---

# Meta 广告资料库（竞品公开广告）

本文件是 Bailing 写的使用说明。上游技能原文在 `upstream/skills/meta-ads-library/SKILL.md`，许可证见 `ATTRIBUTION.md`。

## 它连接的平台

只读 **Meta Ad Library**（Facebook 与 Instagram 的公开广告）via Hyper MCP。连接器地址在 `upstream/.mcp.json`：`https://backend.hyperfx.ai/mcp/`。该文件没有密钥。登录和 toolkit 开关在 Hyper 账户里完成，不要把 token 写进本仓库。

上游技能要求启用 `meta_ads_library` toolkit。工具名以 `upstream/skills/meta-ads-library/SKILL.md` 为准，包括 `meta_ad_library_ads_search`、`meta_ad_library_ads_get`、`meta_ad_library_ads_search_enriched`。只使用公开广告，不要尝试绕过访问控制。

## 亚马逊卖家怎么用

1. 用亚马逊在售商品的类目词或竞品品牌词搜索，国家优先用目标站点（`US`、`DE`、`UK` 等），`active_status` 用 `active`。
2. 汇总再下结论：哪些钩子、CTA、优惠在重复出现，并附上 `ad_library_url`。单条广告不算趋势。
3. 把可迁移的角度写成亚马逊素材 brief（主图视频、SB 视频、站外引流帖）。落地到亚马逊广告结构和竞价时，改用 `sp-sb-sd/` 与 `bid-placement-optimization/`。
4. 本技能不创建、不暂停、不改预算。`search_enriched` 会多打页面联系方式，只在用户明确要联系方式时使用，并遵守 Meta 公开库与当地营销合规。

## 没有收录的同仓库技能

[hyperfx-ai/marketing-skills](https://github.com/hyperfx-ai/marketing-skills) 里还有 `amazon-ads`、`meta-ads`、`google-ads`、`tiktok-ads` 等目录。按本次范围只收录 `meta-ads-library`。`amazon-ads` 没有复制，因此这里不能、也不要假装能创建 Sponsored Products。名单见 `NOT_VENDORED.txt`。
