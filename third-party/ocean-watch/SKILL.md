---
name: 巨量引擎与千川盯盘
description: >-
  上游 westng/ocean-watch 通过巨量引擎官方 Marketing API 处理巨量营销、巨量千川和巨量星图的授权、素材、计划和报表。
  本技能只面向 Ocean Engine，不连接亚马逊广告或领星，也不提供亚马逊 API 封装。
  当跨境卖家同时投放抖音/千川、需要在巨量账户里预检计划时使用。账户写入默认停在预检。
---

# 巨量引擎 / 千川 / 星图（不是亚马逊广告）

本文件是 Bailing 写的使用说明。上游项目、许可证和作者见 `ATTRIBUTION.md` 与 `upstream/`。

## 它连接的平台

Ocean Watch 只通过**巨量引擎开放平台**工作：

| 上游技能 | 渠道 | 路径 |
| --- | --- | --- |
| 巨量营销 | Ocean Engine Marketing | `upstream/skills/ads-plan-monitor/SKILL.md` |
| 巨量千川 | Qianchuan | `upstream/skills/qc-plan-monitor/SKILL.md` |
| 巨量星图 | Xingtu / Star Map（账号授权；计划和报表 API 上游尚未接入） | `upstream/skills/xt-plan-monitor/SKILL.md` |

官方 API 主机是 `api.oceanengine.com` 与千川/星图对应的 Ocean Engine OAuth 地址。凭据由上游设计存放在系统钥匙串（macOS Keychain、Windows DPAPI 或 Linux Secret Service），不要写进仓库、聊天记录或 `.env`。

## 亚马逊卖家什么时候用

卖家在抖音、千川或星图有自己的投放账户，希望查询素材、预检计划或看巨量口径的消耗 / GMV / ROI 时，使用本技能，并按上表进入对应的上游 SKILL。

亚马逊 Sponsored Products、Sponsored Brands、Sponsored Display 的结构和竞价，用仓库根目录的 `sp-sb-sd/` 与 `bid-placement-optimization/`。不要把千川计划、ROI2 或抖音作品预检翻译成亚马逊 campaign，也不要发明一个 Amazon Ads 或领星客户端。这个目录里没有那样的代码。

中国平台短视频的行业思维框架（不连账户）在 `third-party/master-skill/`，那也不是巨量 API。

## 写入默认只预检

与上游安全边界一致，本仓库默认更严：

- 查询账户、素材、模板、计划详情和报表可以做。
- 创建、追加、删除、改预算、改 ROI、改状态，先出预检结果：当前值、拟变更、预期影响。
- 默认不要提交在线写入，不要加 `--submit`，不要调用执行类入口。
- 只有用户在看完**这一次**预检之后，明确要求执行这一条变更，才可以按上游技能继续；上游本身仍要求确认后才提交。
- 示例配置里的 `REPLACE_WITH_*` 保持占位。不要把真实 app secret、token 或广告主密钥提交进 git。

## 本副本缺少的运行时

`bin/ocean-watch-launcher` 会按系统去找 `.codex-plugin/bin/` 下的预编译二进制。这五个平台二进制（约 200MB）没有放进本仓库，原因见 `NOT_VENDORED.txt`。需要 CLI/MCP 时，从 [上游仓库](https://github.com/westng/ocean-watch) 或 [Releases](https://github.com/westng/ocean-watch/releases) 取得对应二进制，放到 `upstream/.codex-plugin/bin/`。Go 源码在 `upstream/runtime/`。
