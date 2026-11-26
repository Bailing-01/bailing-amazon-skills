# Attribution — marketingskills paid ads

This directory is a partial vendored snapshot plus a Bailing-written wrapper. It is not original work by Bailing, and it is not the whole marketingskills project.

| | |
| --- | --- |
| Upstream | https://github.com/coreyhaines31/marketingskills |
| Author / copyright | Corey Haines |
| License | MIT. Text is `LICENSE` and `upstream/LICENSE` (identical). |
| Commit | `8fd2fcade2fd6629026e9dfe6d133b55b36968b9` (2026-11-23) |
| What was copied | `skills/ads/` (paid-ads strategy) and `skills/ad-creative/` (the creative skill `ads` routes to), including their `references/`, `evals/`, and `assets/`. |

`ad-creative` references `../assets/` and `../../ads/references/...`. Those links only work because both skill folders were copied under `upstream/skills/` with their original relative layout.

The wrapper `SKILL.md` beside this file was written for this repository.

## Intentionally not vendored

The rest of the monorepo: the other 51 skill directories, `tools/`, docs, evals at the repo root, tests, scripts, and `VERSIONS.md`. Names of omitted skills are in `NOT_VENDORED.txt`. Use the upstream repository for those. No Amazon Ads API wrapper was added; the vendored playbooks are Google, Meta, LinkedIn, TikTok, and X.
