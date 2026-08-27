#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"

for path in \
  "SKILL.md" \
  "agents/openai.yaml" \
  "references/runtime.md" \
  "references/breakdown-framework.md" \
  "references/output-schema.md" \
  "scripts/prepare-video.ps1" \
  "scripts/prepare-video.sh" \
  "scripts/prepare-account-manifest.py" \
  "scripts/cluster-transcripts.py" \
  "scripts/validate-breakdown-bundle.py" \
  "scripts/extract-semantic-frames.py"; do
  [[ -f "$root/$path" ]]
done

for token in \
  "tk-content-pipeline/v1" \
  "account-manifest" \
  "step1-batch-confirm" \
  "step2-ten-part" \
  "hook-comparison" \
  "duplicate-clustering" \
  "candidate-elements" \
  "breakdown_bundle.json" \
  "不生成九版脚本" \
  "不调用飞书工具"; do
  grep -Fq "$token" "$root/SKILL.md"
done

grep -Fq 'name: deconstruct-tk-video' "$root/SKILL.md"
grep -Fq 'display_name: "最新104｜TK视频拆解"' "$root/agents/openai.yaml"
grep -Fq '$deconstruct-tk-video' "$root/agents/openai.yaml"
[[ ! -e "$root/references/lark-base-config.json" ]]
[[ ! -e "$root/references/analysis-framework.md" ]]
printf '{"skill_valid":true}\n'
