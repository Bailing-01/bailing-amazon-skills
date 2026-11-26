# Attribution — GoMarble marketing-agent

This directory is a vendored snapshot plus a Bailing-written wrapper. It is not original work by Bailing.

| | |
| --- | --- |
| Upstream | https://github.com/gomarble-ai/marketing-agent |
| Author / copyright | GoMarble |
| License | MIT. Text is `LICENSE` and `upstream/LICENSE` (identical). |
| Commit | `3e58349a6d29076c474a3c3b32b5afe2a3b8cdcd` (2026-10-13) |
| What it is | A performance-marketing plugin (skills plus one remote MCP connector) for Claude, Codex, and ChatGPT. Account data is reached through the user's GoMarble OAuth session. |

## What was copied

The full tree at that commit, under `upstream/`: `.claude-plugin/`, `.codex-plugin/`, `.github/`, `.mcp.json`, `skills/`, `scripts/`, `installer/`, `assets/`, `package.json`, `README.md`, `LICENSE`, `.gitignore`.

No `.env`, credential file, or example token was in the upstream tree, and none was added.

The wrapper `SKILL.md` beside this file was written for this repository. It defaults every account-changing action to preflight / dry-run. Upstream skill files were not rewritten.

## Platform limit

Upstream channels are Meta, Google, TikTok, LinkedIn, Microsoft Ads, GA4, Shopify, and the other sources named in `upstream/README.md`. Amazon Ads is not one of them. This copy does not add an Amazon or Lingxing client.
