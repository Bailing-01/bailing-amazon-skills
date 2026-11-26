# Attribution — ocean-watch

This directory is a vendored snapshot plus a Bailing-written wrapper. It is not original work by Bailing.

| | |
| --- | --- |
| Upstream | https://github.com/westng/ocean-watch |
| Author / copyright | westng |
| License | MIT. Text is `LICENSE` and `upstream/LICENSE` (identical). |
| Commit | `88be540b3bfff0e74daaf2e9b354cbca62a3127a` (2026-11-26) |
| What it is | A Codex / Claude skill and local MCP for Ocean Engine Marketing, Qianchuan (巨量千川), and Xingtu (巨量星图). It speaks the official Ocean Engine API. |

The wrapper `SKILL.md` beside this file was written for this repository. It states the Ocean Engine boundary and the preflight default. It is not an upstream file, and it does not add an Amazon Ads or Lingxing client.

## What was copied

The repository source at that commit, under `upstream/`, excluding the prebuilt binaries listed in `NOT_VENDORED.txt`: skills, Go runtime, docs, scripts, host adapters, contracts, license, and the launcher script.

## What was not copied

Five platform runtimes under `.codex-plugin/bin/` (darwin amd64/arm64, linux amd64/arm64, windows amd64). See `NOT_VENDORED.txt`.

Upstream also credits [F2](https://github.com/Johnserf-Seed/f2) for public Douyin metadata parsing and the [Ocean Engine Go SDK](https://github.com/oceanengine/ad_open_sdk_go). Those projects are dependencies, not re-licensed here.
