# Third-party notices

The five advertising skills under `third-party/` are vendored from other authors. They are not original work by Bailing. Each snapshot keeps the upstream MIT license. The `SKILL.md` next to each `ATTRIBUTION.md` is a wrapper written in this repository so an Amazon seller can see what the skill is for and which ad platform it actually talks to.

| Directory | Upstream | Copyright | License | Commit |
| --- | --- | --- | --- | --- |
| `third-party/master-skill/` | https://github.com/swaylq/master-skill | swaylq | MIT | `3dd8a77bcf2d6c415a30e8d2093d3b09823ea136` |
| `third-party/ocean-watch/` | https://github.com/westng/ocean-watch | westng | MIT | `88be540b3bfff0e74daaf2e9b354cbca62a3127a` |
| `third-party/marketingskills-paid-ads/` | https://github.com/coreyhaines31/marketingskills | Corey Haines | MIT | `8fd2fcade2fd6629026e9dfe6d133b55b36968b9` |
| `third-party/meta-ads-library/` | https://github.com/hyperfx-ai/marketing-skills (`skills/meta-ads-library`) | hyperfx.ai | MIT | `463e5026e5db09123f99e668622bf5e3879c08bf` |
| `third-party/marketing-agent/` | https://github.com/gomarble-ai/marketing-agent | GoMarble | MIT | `3e58349a6d29076c474a3c3b32b5afe2a3b8cdcd` |

Per-directory detail, including files left out on purpose, is in each folder's `ATTRIBUTION.md`.

Platform limits, short version:

- **master-skill** generates an industry operating skill. It does not call Amazon Ads, Lingxing, or Ocean Engine. The checked-in `short-video-ads-master` prototype is a partial China-platform (巨量/千川) sample, which is why a tweet can call it short-video ads while the repository description is a Master OS generator.
- **ocean-watch** calls the Ocean Engine Marketing API (巨量营销, 巨量千川, 巨量星图). It is not an Amazon Ads or Lingxing client. Prebuilt binaries were not vendored.
- **marketingskills-paid-ads** contains only `skills/ads` and `skills/ad-creative` from that monorepo. The other skills stay upstream. Platforms in those two skills are Google, Meta, LinkedIn, TikTok, and X.
- **meta-ads-library** reads the public Meta Ad Library through Hyper MCP. The upstream `amazon-ads` skill was not copied.
- **marketing-agent** is the GoMarble performance-marketing plugin. Account changes default to preflight / dry-run. No tokens are stored in this tree. Amazon Ads is not a connected platform.

Existing skill folders in this repository were not modified, except `README.md` and this notice.
