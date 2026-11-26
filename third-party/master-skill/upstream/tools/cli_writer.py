#!/usr/bin/env python3
"""cli_writer.py — emit cli/ subtree for a generated master skill.

Reads:
  - synthesis.md (Section 2 Playbook + Section 9 Agentic Protocol + Section 1 mental models)
  - research/03-workflows.md (workflow SOP + failure modes)

Writes (under {skill_dir}/cli/):
  - lib/common.sh
  - protocol/agentic.sh
  - decision/{cluster}.sh (one per playbook cluster with >=1 rule)
  - workflow/{slug}.sh (one per workflow)
  - README.md (index)

Usage:
  python3 tools/cli_writer.py emit \
    --skill-dir prototypes/llm-agent-infra-master/output \
    --synthesis prototypes/llm-agent-infra-master/references/synthesis.md \
    --workflows prototypes/llm-agent-infra-master/references/research/03-workflows.md \
    --industry-cn "LLM agent 基础设施"

Pure stdlib. Atomic writes. Fail loud on missing inputs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

# 中英 stopword. 过滤聚类抽词时无意义的连接词 / 助词.
STOPWORDS_ZH = {
    "如果", "那么", "需要", "可以", "应该", "必须", "建议", "默认", "选择", "考虑", "看到", "面对",
    "这个", "那个", "这种", "这样", "那样", "之后", "之前", "上线", "之间", "情况", "时候", "做完",
    "什么", "怎么", "为什么", "如何", "或者", "比如", "例如", "包含", "包括", "会让", "可能",
    "本人", "我们", "他们", "你们", "自己", "不能", "不要", "不是", "就是", "没有", "已经", "还是",
}

STOPWORDS_EN = {
    "the", "and", "for", "with", "in", "on", "at", "of", "to", "is", "are", "was", "were",
    "be", "been", "being", "a", "an", "or", "if", "then", "as", "by", "from", "this", "that",
    "your", "you", "we", "us", "our", "their", "they", "it", "its", "i", "me", "my",
    "have", "has", "had", "do", "does", "did", "will", "would", "should", "could", "may",
    "can", "must", "not", "no", "yes",
}

# Hardcoded fallback (LLM agent infra 专属). 仅当从 synthesis 抽不出有意义的 anchor 时使用.
BUILTIN_FALLBACK_KEYWORDS = {
    "framework-select": [
        "framework", "thin framework", "thick framework", "orchestration",
        "multi-agent", "agent project", "agent 协作", "thin", "thick",
    ],
    "eval-strategy": [
        "eval", "llm-as-judge", "human-validated", "benchmark",
        "regression", "eval set",
    ],
    "rag-design": ["rag", "vector", "hybrid", "retrieval", "embedding", "index"],
    "observability": ["trace", "ship", "production-grade", "instrument", "monitoring"],
    "debug-iteration": ["react loop", "tool design", "tool calling", "fail", "debug"],
    "demo-prod": ["demo", "production", "1 day", "6 weeks"],
}

# 兼容旧调用 (test 等). 实际 cluster_rules 改用动态学习.
CLUSTER_KEYWORDS = BUILTIN_FALLBACK_KEYWORDS


# ---------- Atomic write helpers ----------

def atomic_write(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        if executable:
            mode = os.stat(tmp_path).st_mode
            os.chmod(tmp_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def slugify(s: str, maxlen: int = 32) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")[:maxlen]
    return s or "untitled"


def bash_escape_quoted(s: str) -> str:
    """Escape string for safe inclusion in bash double-quoted array element."""
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")
    s = s.replace("\n", " ")
    return s


# ---------- Synthesis parsing ----------

def parse_synthesis(synthesis_path: Path) -> dict:
    text = synthesis_path.read_text(encoding="utf-8")
    out = {"playbook": [], "protocol": [], "mental_models": []}

    sec2 = _section(text, r"^## 2\.")
    if sec2:
        # Rules use various connectors: 则 / 先...再 / 必须 / imperative.
        # Lenient pattern: \d+. **<bold>**[,，]? <rest until line end>
        # iter44 (quant-trading 2026-09-02): the old pattern required the rule to
        # OPEN with a bold clause and treated that clause as the whole condition.
        # The synthesis prompt's canonical shape is `**如果**X，**则**Y`, so the
        # non-greedy `\*\*(.+?)\*\*` matched just "如果" — condition came out empty
        # and the entire rule (including a literal `**则**` and the trailing
        # `evidence: [...]`) leaked into the action, hence into the terminal UI.
        # The stray `evidence` token also dominated anchor scoring, producing a
        # bogus `cli/decision/evidence.sh` cluster. Parse the line first, then
        # split on the 如果/则 connector; keep the old bold-prefix shape as a
        # fallback for skills written before this format was standardised.
        rule_pattern = re.compile(r"^(\d+)\.\s+(.+?)$", re.MULTILINE)
        for m in rule_pattern.finditer(sec2):
            raw = m.group(2).strip()
            if "如果" not in raw and "**" not in raw:
                continue
            # Provenance markers are for the reader of synthesis.md, not for a CLI prompt.
            raw = re.sub(r"\s*evidence:\s*\[[^\]]*\]", "", raw).strip()
            connector = re.match(
                r"^\*{0,2}如果\*{0,2}\s*(.+?)[，,]?\s*\*{0,2}则\*{0,2}\s*(.+)$", raw
            )
            if connector:
                condition, action = connector.group(1), connector.group(2)
            else:
                fallback = re.match(r"^\*\*(.+?)\*\*[，,]?\s*(.+)$", raw)
                if not fallback:
                    continue
                condition, action = fallback.group(1), fallback.group(2)
                if condition.startswith("如果"):
                    condition = condition[2:]
                if action.startswith("则"):
                    action = action[1:]
            condition = condition.strip().strip("*").strip("，, ")
            action = action.replace("**", "").strip()
            # Drop trailing period and any sub-clause after "."
            action = re.split(r"[.。]\s+", action)[0].rstrip(".。 ")
            if not condition or not action:
                continue
            out["playbook"].append({
                "n": int(m.group(1)),
                "condition": condition,
                "action": action,
            })

    sec9 = _section(text, r"^## 9\.")
    if sec9:
        dim_pattern = re.compile(
            r"^### 9\.(\d+)\s+(.+?)$(?P<body>.*?)(?=^### 9\.|^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        for m in dim_pattern.finditer(sec9):
            body = m.group("body")
            # Iter 26: tolerate both legacy 看什么/在哪看/输出格式 and iter-24+
            # 轴/触发/输出 vocabularies.
            def _alt(aliases: list[str], _body: str = body) -> str:
                for label in aliases:
                    pat = re.search(
                        rf"-\s*\*\*{re.escape(label)}\*\*[：:]\s*(.+?)$",
                        _body, re.MULTILINE,
                    )
                    if pat:
                        return pat.group(1).strip()
                return ""
            out["protocol"].append({
                "n": int(m.group(1)),
                "title": m.group(2).strip(),
                "question": _alt(["看什么", "轴"]),
                "sources": _alt(["在哪看", "触发"]),
                "output_format": _alt(["输出格式", "输出"]),
            })

    sec1 = _section(text, r"^## 1\.")
    if sec1:
        mm_pattern = re.compile(
            r"^### 1\.(\d+)\s+(.+?)$.*?\*\*一句话\*\*[：:]\s*(.+?)$",
            re.MULTILINE | re.DOTALL,
        )
        for m in mm_pattern.finditer(sec1):
            out["mental_models"].append({
                "n": int(m.group(1)),
                "name": m.group(2).strip(),
                "oneliner": m.group(3).strip(),
            })

    return out


def _section(text: str, header_re: str) -> str:
    """Extract one '## N.' section from text. Returns text from header up to next ## or EOF."""
    m = re.search(header_re + r".*?(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(0) if m else ""


def _tokenize_text(text: str) -> list:
    """Token 化中英混合文本. 英文按词, 中文按 2-3 字 n-gram."""
    tokens = []
    # 英文词 (≥3 字符)
    for w in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text):
        wl = w.lower()
        if wl not in STOPWORDS_EN:
            tokens.append(wl)
    # 中文 character n-gram (2-3 字)
    zh = re.sub(r"[a-zA-Z0-9\s\.\,\;\:\(\)（）。，、；：\-\[\]【】「」『』≥<>≤=!?！？\*\$\#\%\^&\+/]", "", text)
    for n in (2, 3):
        for i in range(len(zh) - n + 1):
            t = zh[i:i+n]
            if t not in STOPWORDS_ZH and not all(c in STOPWORDS_ZH for c in t):
                tokens.append(t)
    return tokens


def learn_cluster_anchors(parsed: dict, max_anchors: int = 6, min_freq: int = 2) -> list:
    """从 synthesis 抽 cluster anchor 关键词 (按主题归类规则用).

    优先级:
    1. 智识谱系 (section 7) 的流派名 — 天然的主题标签
    2. mental model 名 + 一句话中的高频词
    3. playbook 规则文本中的高频词

    返回最多 max_anchors 个 anchor (按相关性排序).
    """
    anchor_scores: Counter = Counter()

    # 优先级 1: mental model 名 (每个权重 +3)
    for mm in parsed.get("mental_models", []):
        for tok in _tokenize_text(mm["name"]):
            anchor_scores[tok] += 3
        for tok in _tokenize_text(mm["oneliner"][:60]):
            anchor_scores[tok] += 1

    # 优先级 2: playbook 规则 (每个权重 +1)
    for rule in parsed.get("playbook", []):
        text = rule["condition"] + " " + rule["action"]
        for tok in _tokenize_text(text):
            anchor_scores[tok] += 1

    # 优先级 3: protocol dim 名 (每个权重 +2)
    for dim in parsed.get("protocol", []):
        for tok in _tokenize_text(dim["title"]):
            anchor_scores[tok] += 2

    # 取频次 ≥ min_freq 的, 排序后取 top N
    candidates = [(tok, score) for tok, score in anchor_scores.most_common() if score >= min_freq]

    # 去重: 如果一个 anchor 是另一个的子串且分数低于父, 跳过子串
    selected = []
    for tok, _score in candidates:
        if any(tok in other and tok != other for other, _ in selected):
            continue
        selected.append((tok, _score))
        if len(selected) >= max_anchors:
            break

    return [tok for tok, _ in selected]


def cluster_rules(rules: list, parsed: dict | None = None) -> dict:
    """按动态学的 anchor 给 playbook 规则分组. 返回 dict[cluster_slug] -> list of rules.

    parsed: 完整 parse_synthesis 输出, 用于提取 cluster anchor.
            如果不传, 退到 builtin LLM agent infra keyword (向后兼容).
    """
    if parsed:
        anchors = learn_cluster_anchors(parsed)
    else:
        anchors = []

    if anchors:
        clusters: dict[str, list] = {anchor: [] for anchor in anchors}
        clusters["general-playbook"] = []

        for rule in rules:
            blob = (rule["condition"] + " " + rule["action"]).lower()
            best_anchor = None
            best_score = 0
            for anchor in anchors:
                # 中文 anchor 直接 substring; 英文 anchor 也直接 substring (lowercase 后)
                if anchor.lower() in blob:
                    score = blob.count(anchor.lower())
                    if score > best_score:
                        best_score = score
                        best_anchor = anchor
            if best_anchor:
                clusters[best_anchor].append(rule)
            else:
                clusters["general-playbook"].append(rule)
    else:
        # Fallback: builtin LLM agent infra keywords
        clusters = {k: [] for k in BUILTIN_FALLBACK_KEYWORDS}
        clusters["general-playbook"] = []

        for rule in rules:
            blob = (rule["condition"] + " " + rule["action"]).lower()
            scores = []
            for cslug, kws in BUILTIN_FALLBACK_KEYWORDS.items():
                score = sum(1 for kw in kws if kw.lower() in blob)
                scores.append((score, cslug))
            scores.sort(reverse=True)
            if scores[0][0] > 0:
                clusters[scores[0][1]].append(rule)
            else:
                clusters["general-playbook"].append(rule)

    # 把 cluster slug 标准化 (去除非 ASCII 字符给 bash 文件名用), 保留原 anchor 作为 title
    normalized: dict[str, dict] = {}
    for anchor_text, rs in clusters.items():
        if not rs:
            continue
        norm = slugify(anchor_text)
        # slugify 默认 "untitled" 表示原文全是非 ASCII (中文 anchor); 用 topic-N 兜底
        if not norm or norm == "untitled":
            norm = f"topic-{len(normalized) + 1}"
        if norm in normalized:
            normalized[norm]["rules"].extend(rs)
        else:
            normalized[norm] = {"anchor": anchor_text, "rules": rs}

    return normalized


# ---------- Workflow parsing ----------

def parse_workflows(workflows_path: Path) -> list:
    if not workflows_path.exists():
        return []
    text = workflows_path.read_text(encoding="utf-8")

    workflows = []
    # Iter 26 (codex 4-audit P0-2b): accept both `### 1.` and `### W1.`
    # / `### S1.` shapes. Iter 24 prototypes use `W1` (workflow) / `S1`
    # (supplementary) prefixes; older prototypes use plain `1.`.
    wf_pattern = re.compile(
        r"^###\s+(?:[WS])?(\d+)\.\s+(.+?)$(?P<body>.*?)(?=^###\s+(?:[WS])?\d+\.|^##\s|^---|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    workflow_index = 0
    seen_slugs = set()
    for m in wf_pattern.finditer(text):
        title = m.group(2).strip()
        body = m.group("body")
        workflow_index += 1
        # iter45: 标题形如 `选题与可行性判断 (Decay risk: low)`. slugify 会剥掉中文,
        # 只剩下 ASCII 尾巴 `decay-risk-low` —— 14 条工作流因此塌成 3 个文件名,
        # 后写的覆盖先写的, 11 条工作流的脚本直接丢失. 先摘掉这类元数据括号再 slugify.
        title_for_slug = re.sub(r"[（(]\s*decay\s+risk[^）)]*[）)]", "", title, flags=re.IGNORECASE).strip()
        slug = slugify(title_for_slug)
        # iter46: 同一个坑的第二种形态 —— 中文标题里嵌一小段 ASCII (`演示与交付验收
        # (POC vs 量产)` -> `poc-vs`), slugify 不返回 "untitled" 但拿到的名字既不可读
        # 也极易碰撞. 判据改成「标题主体是中文而 ASCII 残渣很短」, 一律退回编号名.
        cjk_count = len(re.findall(r"[\u4e00-\u9fff]", title_for_slug))
        if slug == "untitled" or (cjk_count >= 4 and len(slug.replace("-", "")) < 8):
            slug = f"workflow-{m.group(1)}"
        # 落盘按名字写文件, 碰撞必须显式改名而不是静默覆盖 (lessons: 生成器 bug 会安静
        # 地删掉产物). 同名即追加序号.
        if slug in seen_slugs:
            base, k = slug, 2
            while slug in seen_slugs:
                slug = f"{base}-{k}"
                k += 1
        seen_slugs.add(slug)

        one_liner_m = re.search(r"\*\*One-liner\*\*[：:]\s*(.+?)$", body, re.MULTILINE)

        def _extract_steps(list_text: str) -> list:
            steps = []
            # Try multi-line `1. ...` first
            for line in list_text.split("\n"):
                step_m = re.match(r"\s*(\d+)\.\s+(.+)$", line)
                if step_m:
                    steps.append(step_m.group(2).strip())
            # Fall back to inline `1) Step1 2) Step2 ...` if no multi-line steps
            if not steps:
                inline_steps = re.findall(r"\d+\)\s+([^0-9)]+?)(?=\s*\d+\)|\s*$)", list_text)
                steps = [x.strip(" ;,，;") for x in inline_steps if x.strip(" ;,，;")]
            return steps

        # Iter 26: tolerate both `- **入门 SOP**:\n  1. step` and inline
        # `- 入门 SOP: 1) step1 2) step2` formats.
        # iter46 (robotics-embodied-ai): 第三种形态 —— SOP 写成独立粗体标题
        # `**入门 SOP（最少 6 步）**` + 换行 + 编号列表, 标题后没有冒号, 后一节
        # `**资深路径**` 也不是 `- ` 列表项. 更阴的是同一张卡片末尾的「时间与人力量级」
        # 里有一行 `- 入门 SOP：现场 1-2 天`, 带冒号, 旧正则**匹配到了它**, 于是
        # sop_m 非 None 但一条编号步骤都抽不出 -> 13 条工作流全被丢弃 ->
        # cli/workflow/ 整个目录不落盘, 退出码仍是 0. 所以判据必须是「抽到步骤没有」,
        # 不是「正则匹配上没有」: 两个 pattern 都试, 谁抽出步骤用谁.
        sop_patterns = [
            r"(?:\*\*入门 SOP\*\*|入门 SOP)[^：:\n]*[：:]\s*\n?(?P<list>.+?)"
            r"(?=\n\s*-\s+(?:\*\*)?(?:资深|每一步|近期变化|典型耗时|关键工具|关键人物|常见失败|来源|Last_updated)|\n\s*###|\Z)",
            r"(?:\*\*)?入门 SOP[^\n]*\n+(?P<list>.+?)"
            r"(?=\n\s*\*\*[^*\n]+\*\*\s*(?:\n|$)"
            r"|\n\s*-?\s*(?:\*\*)?(?:资深|每一步|近期变化|典型耗时|关键工具|关键人物|"
            r"常见失败|判断这一步|时间与人力|来源|Last_updated)|\n\s*###|\Z)",
        ]
        sop_steps = []
        for pat in sop_patterns:
            for cand in re.finditer(pat, body, re.DOTALL):
                steps = _extract_steps(cand.group("list"))
                if len(steps) > len(sop_steps):
                    sop_steps = steps
            if sop_steps:
                break

        fail_m = re.search(
            r"\*\*常见失败模式\*\*[：:]?\s*\n(?P<list>.+?)"
            r"(?=\n- \*\*来源|\n- \*\*Last_updated|\n\s*\*\*[^*\n]+\*\*\s*(?:\n|$)|\n\s*###|\Z)",
            body, re.DOTALL,
        )
        failure_modes = []
        if fail_m:
            for line in fail_m.group("list").split("\n"):
                fm_m = re.match(r"\s*-\s+(.+?)$", line)
                if fm_m:
                    failure_modes.append(fm_m.group(1).strip())

        if sop_steps:
            workflows.append({
                "n": int(m.group(1)),
                "slug": slug,
                "title": title,
                "one_liner": one_liner_m.group(1).strip() if one_liner_m else "",
                "sop_steps": sop_steps,
                "failure_modes": failure_modes,
            })

    return workflows


# ---------- Bash array formatting ----------

def bash_array_lines(items: list, indent: str = "  ") -> str:
    """Format list of strings as bash array body, one quoted item per line."""
    if not items:
        return ""
    return "\n".join(f'{indent}"{bash_escape_quoted(it)}"' for it in items)


# ---------- Templates ----------

COMMON_SH = r'''#!/usr/bin/env bash
# common.sh — shared helpers for {industry-cn} master CLI scripts.
# Pure bash 4 + POSIX coreutils. No external deps.

if [[ -t 1 ]]; then
  MS_BOLD=$'\033[1m'; MS_DIM=$'\033[2m'
  MS_RED=$'\033[31m'; MS_GREEN=$'\033[32m'
  MS_YELLOW=$'\033[33m'; MS_BLUE=$'\033[34m'
  MS_RESET=$'\033[0m'
else
  MS_BOLD=""; MS_DIM=""; MS_RED=""; MS_GREEN=""; MS_YELLOW=""; MS_BLUE=""; MS_RESET=""
fi

ms_section() { printf "\n%s━━ %s ━━%s\n" "$MS_BOLD$MS_BLUE" "$1" "$MS_RESET"; }
ms_info()    { printf "%s%s%s\n" "$MS_DIM" "$1" "$MS_RESET"; }
ms_warn()    { printf "%s⚠ %s%s\n" "$MS_YELLOW" "$1" "$MS_RESET"; }
ms_error()   { printf "%s✗ %s%s\n" "$MS_RED" "$1" "$MS_RESET" >&2; }
ms_ok()      { printf "%s✓ %s%s\n" "$MS_GREEN" "$1" "$MS_RESET"; }
ms_prompt()  { printf "%s? %s%s " "$MS_BOLD" "$1" "$MS_RESET"; }

ms_read_multiline() {
  local result=""
  local line
  while IFS= read -r line; do
    [[ -z "$line" ]] && break
    result+="$line"$'\n'
  done
  printf "%s" "$result"
}

ms_confirm() {
  ms_prompt "$1 [y/N]"
  local ans
  read -r ans
  [[ "$ans" =~ ^[Yy] ]]
}

# Markdown buffer (global)
MS_REPORT_BUFFER=""
ms_buffer_append() { MS_REPORT_BUFFER+="$1"$'\n'; }

ms_emit_md_file() {
  local slug="$1"
  local fname="${slug}-$(date +%Y%m%d-%H%M%S).md"
  printf "%s" "$MS_REPORT_BUFFER" > "$fname"
  ms_ok "报告已写到 $fname"
}

ms_emit_md_stdout() { printf "%s" "$MS_REPORT_BUFFER"; }

ms_json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\t'/\\t}"
  s="${s//$'\r'/}"
  printf "%s" "$s"
}

ms_emit_json() {
  local out="{"
  local first=1
  while [[ $# -ge 2 ]]; do
    [[ $first -eq 1 ]] || out+=","
    first=0
    out+="\"$(ms_json_escape "$1")\":\"$(ms_json_escape "$2")\""
    shift 2
  done
  out+="}"
  printf "%s\n" "$out"
}
'''


PROTOCOL_TEMPLATE = r'''#!/usr/bin/env bash
# agentic.sh — Agentic Protocol CLI for {INDUSTRY_CN}.
# Auto-generated by cli_writer.py. Source: synthesis.md Section 9.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${{SCRIPT_DIR}}/../lib/common.sh"

INDUSTRY="{INDUSTRY_CN}"
DIM_COUNT={DIM_COUNT}

usage() {{
  cat <<EOF
agentic.sh — Agentic Protocol CLI for ${{INDUSTRY}}

拿到 ${{INDUSTRY}} 行业的新问题时，按 ${{DIM_COUNT}} 个研究维度做功课再答。
不直接给答案，而是引导你用资深从业者的研究维度收集信息。

USAGE:
  ./agentic.sh                # interactive walkthrough
  ./agentic.sh --dry-run      # walk through but skip file write
  ./agentic.sh --json         # emit JSON to stdout
  ./agentic.sh --explain      # show backing mental models + sources
  ./agentic.sh --help         # this message
EOF
}}

explain() {{
  cat <<'EOT'
{EXPLAIN_BODY}
EOT
}}

DRY_RUN=0; JSON=0
for arg in "$@"; do
  case "$arg" in
    --help|-h) usage; exit 0 ;;
    --explain) explain; exit 0 ;;
    --dry-run) DRY_RUN=1 ;;
    --json) JSON=1 ;;
  esac
done

declare -a DIM_TITLES=(
{DIM_TITLES}
)
declare -a DIM_QUESTIONS=(
{DIM_QUESTIONS}
)
declare -a DIM_SOURCES=(
{DIM_SOURCES}
)
declare -a DIM_OUTPUT_FORMATS=(
{DIM_OUTPUT_FORMATS}
)
declare -a DIM_FINDINGS=()

if [[ $JSON -eq 0 ]]; then
  ms_section "${{INDUSTRY}} · Agentic Protocol"
  ms_info "拿到的问题是什么? (输入完后，敲一个空行结束)"
  echo
fi

PROBLEM="$(ms_read_multiline)"
ms_buffer_append "# ${{INDUSTRY}} — Agentic Protocol Report"
ms_buffer_append ""
ms_buffer_append "_生成时间: $(date '+%Y-%m-%d %H:%M:%S')_"
ms_buffer_append ""
ms_buffer_append "## 问题"
ms_buffer_append ""
ms_buffer_append "$PROBLEM"
ms_buffer_append ""

for i in "${{!DIM_TITLES[@]}}"; do
  if [[ $JSON -eq 0 ]]; then
    ms_section "${{DIM_TITLES[$i]}}"
    echo "看什么:    ${{DIM_QUESTIONS[$i]}}"
    echo "在哪看:    ${{DIM_SOURCES[$i]}}"
    echo "输出格式:  ${{DIM_OUTPUT_FORMATS[$i]}}"
    echo
    ms_prompt "你的发现 / 推断 (空行结束):"
    echo
  fi
  finding="$(ms_read_multiline)"
  DIM_FINDINGS+=("$finding")

  ms_buffer_append "## ${{DIM_TITLES[$i]}}"
  ms_buffer_append ""
  ms_buffer_append "**看什么**: ${{DIM_QUESTIONS[$i]}}"
  ms_buffer_append ""
  ms_buffer_append "**在哪看**: ${{DIM_SOURCES[$i]}}"
  ms_buffer_append ""
  ms_buffer_append "**发现**:"
  ms_buffer_append ""
  ms_buffer_append "$finding"
  ms_buffer_append ""
done

if [[ $JSON -eq 1 ]]; then
  args=("problem" "$PROBLEM")
  for i in "${{!DIM_TITLES[@]}}"; do
    args+=("dim_${{i}}_title" "${{DIM_TITLES[$i]}}")
    args+=("dim_${{i}}_finding" "${{DIM_FINDINGS[$i]}}")
  done
  ms_emit_json "${{args[@]}}"
elif [[ $DRY_RUN -eq 1 ]]; then
  ms_emit_md_stdout
else
  ms_emit_md_file "agentic-protocol"
fi
'''


DECISION_TEMPLATE = r'''#!/usr/bin/env bash
# {SLUG}.sh — {TOPIC_TITLE} 决策助手 for {INDUSTRY_CN}.
# Auto-generated by cli_writer.py. Source: synthesis.md Section 2 (Playbook).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
source "${{SCRIPT_DIR}}/../lib/common.sh"

INDUSTRY="{INDUSTRY_CN}"
TOPIC="{TOPIC_TITLE}"

usage() {{
  cat <<EOF
{SLUG}.sh — ${{TOPIC}} 决策助手 for ${{INDUSTRY}}

基于 {RULE_COUNT} 条 playbook 规则的交互式决策评估。
你描述情景, 工具帮你判断哪条规则适用, 并给推荐。

USAGE:
  ./{SLUG}.sh             # interactive
  ./{SLUG}.sh --dry-run   # walk through but no file
  ./{SLUG}.sh --json      # JSON to stdout
  ./{SLUG}.sh --explain   # show backing playbook rules + mental models
  ./{SLUG}.sh --help      # this message
EOF
}}

explain() {{
  cat <<'EOT'
{EXPLAIN_BODY}
EOT
}}

DRY_RUN=0; JSON=0
for arg in "$@"; do
  case "$arg" in
    --help|-h) usage; exit 0 ;;
    --explain) explain; exit 0 ;;
    --dry-run) DRY_RUN=1 ;;
    --json) JSON=1 ;;
  esac
done

declare -a RULE_CONDITIONS=(
{RULE_CONDITIONS}
)
declare -a RULE_ACTIONS=(
{RULE_ACTIONS}
)
declare -a APPLIED_RULES=()

ms_section "${{INDUSTRY}} · ${{TOPIC}} 决策评估"
ms_info "本工具基于 ${{#RULE_CONDITIONS[@]}} 条 playbook 规则评估你的情景。"
echo

ms_prompt "请描述当前情景 (空行结束):"
echo
SITUATION="$(ms_read_multiline)"

for i in "${{!RULE_CONDITIONS[@]}}"; do
  ms_section "Rule $((i+1))/${{#RULE_CONDITIONS[@]}}"
  echo "适用情景: ${{RULE_CONDITIONS[$i]}}"
  echo "推荐做法: ${{RULE_ACTIONS[$i]}}"
  if ms_confirm "这条规则 fit 你当前情景吗?"; then
    APPLIED_RULES+=("$((i+1))")
    ms_ok "适用 rule $((i+1))"
  fi
done

ms_buffer_append "# ${{INDUSTRY}} — ${{TOPIC}} 决策报告"
ms_buffer_append ""
ms_buffer_append "_生成时间: $(date '+%Y-%m-%d %H:%M:%S')_"
ms_buffer_append ""
ms_buffer_append "## 情景"
ms_buffer_append ""
ms_buffer_append "$SITUATION"
ms_buffer_append ""
ms_buffer_append "## 适用规则"
ms_buffer_append ""
if [[ ${{#APPLIED_RULES[@]}} -eq 0 ]]; then
  ms_buffer_append "(无适用 playbook 规则 — 此情景在已知 OS 之外, 建议回到 SKILL.md 心智模型层重新分析)"
else
  for ridx in "${{APPLIED_RULES[@]}}"; do
    i=$((ridx-1))
    ms_buffer_append "- **情景**: ${{RULE_CONDITIONS[$i]}} → **做法**: ${{RULE_ACTIONS[$i]}}"
  done
fi
ms_buffer_append ""

if [[ $JSON -eq 1 ]]; then
  ms_emit_json \
    "topic" "${{TOPIC}}" \
    "situation" "${{SITUATION}}" \
    "applied_rules_count" "${{#APPLIED_RULES[@]}}"
elif [[ $DRY_RUN -eq 1 ]]; then
  ms_emit_md_stdout
else
  ms_emit_md_file "{SLUG}-decision"
fi
'''


WORKFLOW_TEMPLATE = r'''#!/usr/bin/env bash
# {SLUG}.sh — {WORKFLOW_TITLE} SOP walkthrough for {INDUSTRY_CN}.
# Auto-generated by cli_writer.py. Source: research/03-workflows.md.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
source "${{SCRIPT_DIR}}/../lib/common.sh"

INDUSTRY="{INDUSTRY_CN}"
WORKFLOW="{WORKFLOW_TITLE}"

usage() {{
  cat <<EOF
{SLUG}.sh — Walk through "${{WORKFLOW}}" SOP for ${{INDUSTRY}}

逐步走完这个工作流的入门 SOP, 然后做失败模式自检, 输出走查报告。

USAGE:
  ./{SLUG}.sh             # interactive
  ./{SLUG}.sh --dry-run
  ./{SLUG}.sh --json
  ./{SLUG}.sh --explain
  ./{SLUG}.sh --help
EOF
}}

explain() {{
  cat <<'EOT'
{EXPLAIN_BODY}
EOT
}}

DRY_RUN=0; JSON=0
for arg in "$@"; do
  case "$arg" in
    --help|-h) usage; exit 0 ;;
    --explain) explain; exit 0 ;;
    --dry-run) DRY_RUN=1 ;;
    --json) JSON=1 ;;
  esac
done

declare -a SOP_STEPS=(
{SOP_STEPS}
)
declare -a FAILURE_MODES=(
{FAILURE_MODES}
)
declare -a STEP_STATUS=()
declare -a STEP_NOTES=()
declare -a FAIL_CHECK=()

ms_section "${{INDUSTRY}} · ${{WORKFLOW}} 走查"
ms_info "逐步走完 ${{#SOP_STEPS[@]}} 步入门 SOP。每步可标 done / skipped / blocked。"
echo

for i in "${{!SOP_STEPS[@]}}"; do
  ms_section "Step $((i+1))/${{#SOP_STEPS[@]}}: ${{SOP_STEPS[$i]}}"
  ms_prompt "状态? [d=done / s=skipped / b=blocked]"
  read -r status
  STEP_STATUS+=("${{status:-d}}")
  case "${{status:-d}}" in
    s) ms_prompt "跳过原因 (一句话):"; read -r note ;;
    b) ms_prompt "blocker (一句话):"; read -r note ;;
    *) note="" ;;
  esac
  STEP_NOTES+=("$note")
done

if [[ ${{#FAILURE_MODES[@]}} -gt 0 ]]; then
  ms_section "失败模式自检"
  for fm in "${{FAILURE_MODES[@]}}"; do
    if ms_confirm "你是否避免了 — '$fm' ?"; then
      FAIL_CHECK+=("✓ $fm")
    else
      FAIL_CHECK+=("✗ $fm")
    fi
  done
fi

ms_buffer_append "# ${{INDUSTRY}} — ${{WORKFLOW}} 走查报告"
ms_buffer_append ""
ms_buffer_append "_生成时间: $(date '+%Y-%m-%d %H:%M:%S')_"
ms_buffer_append ""
ms_buffer_append "## SOP 步骤"
ms_buffer_append ""
for i in "${{!SOP_STEPS[@]}}"; do
  status_icon="?"
  case "${{STEP_STATUS[$i]}}" in
    d|D) status_icon="✓" ;;
    s|S) status_icon="↷" ;;
    b|B) status_icon="✗" ;;
  esac
  if [[ -n "${{STEP_NOTES[$i]}}" ]]; then
    ms_buffer_append "$((i+1)). [${{status_icon}}] ${{SOP_STEPS[$i]}} — ${{STEP_NOTES[$i]}}"
  else
    ms_buffer_append "$((i+1)). [${{status_icon}}] ${{SOP_STEPS[$i]}}"
  fi
done
ms_buffer_append ""
if [[ ${{#FAIL_CHECK[@]}} -gt 0 ]]; then
  ms_buffer_append "## 失败模式自检"
  ms_buffer_append ""
  for line in "${{FAIL_CHECK[@]}}"; do
    ms_buffer_append "- $line"
  done
  ms_buffer_append ""
fi

if [[ $JSON -eq 1 ]]; then
  ms_emit_json \
    "workflow" "${{WORKFLOW}}" \
    "step_count" "${{#SOP_STEPS[@]}}" \
    "failure_check_count" "${{#FAILURE_MODES[@]}}"
elif [[ $DRY_RUN -eq 1 ]]; then
  ms_emit_md_stdout
else
  ms_emit_md_file "{SLUG}-walkthrough"
fi
'''


CLI_README_TEMPLATE = r'''# {INDUSTRY_CN} CLI

把 {INDUSTRY_CN} master skill 的认知 OS 物化成 bash 工具。
不替代 SKILL.md（思维顾问），是它的「执行端」：交互问询 → 应用 playbook / protocol → 输出结构化报告。

## 用法

所有脚本支持 `--help` / `--explain` / `--dry-run` / `--json` 四个标准 flag。

```bash
# 拿到新问题时, 按 N 个研究维度做功课
./protocol/agentic.sh

{EXAMPLE_DECISION_LINE}
{EXAMPLE_WORKFLOW_LINE}

# 看背后的心智模型 / playbook (不交互)
./protocol/agentic.sh --explain
```

## 脚本清单

{SCRIPT_LIST_TABLE}

## 设计与生成

CLI 子树由 `tools/cli_writer.py` 自动从 `references/synthesis.md` (Section 2 Playbook + Section 9 Agentic Protocol) 和 `references/research/03-workflows.md` 生成。

完整 spec 在 master-skill 仓库 `references/cli-spec.md`。

## 重新生成

如果 synthesis.md 或 03-workflows.md 更新了, 重跑:

```bash
python3 <master-skill>/tools/cli_writer.py emit \
  --skill-dir <this-skill-dir> \
  --synthesis references/synthesis.md \
  --workflows references/research/03-workflows.md \
  --industry-cn "{INDUSTRY_CN}"
```
'''


def emit_protocol_explain(protocol: list, mental_models: list) -> str:
    lines = ["这个 Agentic Protocol 把这一行人面对新问题的研究维度结构化。"]
    lines.append("")
    lines.append(f"研究维度 ({len(protocol)} 个):")
    for d in protocol:
        lines.append(f"  9.{d['n']} {d['title']}")
    if mental_models:
        lines.append("")
        lines.append("背后的心智模型:")
        for mm in mental_models[:3]:
            ol = mm["oneliner"][:100]
            lines.append(f"  • {mm['name']}: {ol}")
    lines.append("")
    lines.append("来源: synthesis.md Section 9 + Section 1.")
    return "\n".join(lines)


def emit_decision_explain(topic_title: str, rules: list, mental_models: list) -> str:
    lines = [f"这个决策助手把 {topic_title} 主题下的 playbook 规则组合成交互树。"]
    lines.append("")
    lines.append(f"基于 {len(rules)} 条规则:")
    for r in rules:
        lines.append(f"  • 如果 {r['condition'][:60]} → 则 {r['action'][:60]}")
    if mental_models:
        lines.append("")
        lines.append("相关心智模型:")
        for mm in mental_models[:2]:
            lines.append(f"  • {mm['name']}: {mm['oneliner'][:100]}")
    lines.append("")
    lines.append("来源: synthesis.md Section 2.")
    return "\n".join(lines)


def emit_workflow_explain(wf: dict, mental_models: list) -> str:
    lines = [f"这个 SOP 走查脚本帮你完成 \"{wf['title']}\" 工作流。"]
    if wf.get("one_liner"):
        lines.append("")
        lines.append(f"一句话: {wf['one_liner']}")
    lines.append("")
    lines.append(f"入门 SOP 共 {len(wf['sop_steps'])} 步, 失败模式自检 {len(wf['failure_modes'])} 项。")
    if mental_models:
        lines.append("")
        lines.append("相关心智模型:")
        for mm in mental_models[:2]:
            lines.append(f"  • {mm['name']}: {mm['oneliner'][:100]}")
    lines.append("")
    lines.append("来源: research/03-workflows.md.")
    return "\n".join(lines)


# ---------- Main emit ----------

def cmd_emit(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.exists():
        print(f"✗ skill-dir not found: {skill_dir}", file=sys.stderr)
        return 1

    synthesis_path = Path(args.synthesis).resolve()
    if not synthesis_path.exists():
        print(f"✗ synthesis not found: {synthesis_path}", file=sys.stderr)
        return 1

    workflows_path = Path(args.workflows).resolve()

    industry_cn = args.industry_cn or skill_dir.name.replace("-master", "").replace("-", " ")

    print(f"📂 skill-dir:  {skill_dir}")
    print(f"📄 synthesis:  {synthesis_path}")
    print(f"📄 workflows:  {workflows_path if workflows_path.exists() else '(missing — workflow scripts will be skipped)'}")
    print(f"🏷  industry:   {industry_cn}")
    print()

    parsed = parse_synthesis(synthesis_path)
    workflows = parse_workflows(workflows_path)

    print(f"✓ Parsed {len(parsed['playbook'])} playbook rules")
    print(f"✓ Parsed {len(parsed['protocol'])} Agentic Protocol dims")
    print(f"✓ Parsed {len(parsed['mental_models'])} mental models")
    print(f"✓ Parsed {len(workflows)} workflows")
    print()

    cli_dir = skill_dir / "cli"
    if cli_dir.exists():
        print(f"⚠ cli/ exists, removing for fresh emit")
        shutil.rmtree(cli_dir)

    common_path = cli_dir / "lib" / "common.sh"
    common_content = COMMON_SH.replace("{industry-cn}", industry_cn)
    atomic_write(common_path, common_content, executable=False)
    print(f"  wrote {common_path.relative_to(skill_dir)}")

    scripts_index = []

    if parsed["protocol"]:
        proto_path = cli_dir / "protocol" / "agentic.sh"
        proto_content = PROTOCOL_TEMPLATE.format(
            INDUSTRY_CN=industry_cn,
            DIM_COUNT=len(parsed["protocol"]),
            EXPLAIN_BODY=emit_protocol_explain(parsed["protocol"], parsed["mental_models"]),
            DIM_TITLES=bash_array_lines([d["title"] for d in parsed["protocol"]]),
            DIM_QUESTIONS=bash_array_lines([d["question"] for d in parsed["protocol"]]),
            DIM_SOURCES=bash_array_lines([d["sources"] for d in parsed["protocol"]]),
            DIM_OUTPUT_FORMATS=bash_array_lines([d["output_format"] for d in parsed["protocol"]]),
        )
        atomic_write(proto_path, proto_content, executable=True)
        print(f"  wrote {proto_path.relative_to(skill_dir)}")
        scripts_index.append({
            "category": "protocol",
            "name": "agentic",
            "path": "protocol/agentic.sh",
            "purpose": f"Agentic Protocol ({len(parsed['protocol'])} 维度) — 拿到新问题时按这一行的研究维度做功课",
        })

    clusters = cluster_rules(parsed["playbook"], parsed=parsed)
    decision_count = 0
    for cluster_slug, info in clusters.items():
        rules = info["rules"]
        anchor = info["anchor"]
        # topic_title 优先用原 anchor (含中文); 兜底 cluster_slug
        if cluster_slug == "general-playbook":
            topic_title = "通用 Playbook"
        elif anchor and anchor != cluster_slug:
            topic_title = anchor
        else:
            topic_title = cluster_slug.replace("-", " ").title()
        dec_path = cli_dir / "decision" / f"{cluster_slug}.sh"
        dec_content = DECISION_TEMPLATE.format(
            INDUSTRY_CN=industry_cn,
            SLUG=cluster_slug,
            TOPIC_TITLE=topic_title,
            RULE_COUNT=len(rules),
            EXPLAIN_BODY=emit_decision_explain(topic_title, rules, parsed["mental_models"]),
            RULE_CONDITIONS=bash_array_lines([r["condition"] for r in rules]),
            RULE_ACTIONS=bash_array_lines([r["action"] for r in rules]),
        )
        atomic_write(dec_path, dec_content, executable=True)
        print(f"  wrote {dec_path.relative_to(skill_dir)}")
        scripts_index.append({
            "category": "decision",
            "name": cluster_slug,
            "path": f"decision/{cluster_slug}.sh",
            "purpose": f"{topic_title} 决策树 ({len(rules)} 条规则)",
        })
        decision_count += 1

    workflow_count = 0
    for wf in workflows:
        wf_path = cli_dir / "workflow" / f"{wf['slug']}.sh"
        wf_content = WORKFLOW_TEMPLATE.format(
            INDUSTRY_CN=industry_cn,
            SLUG=wf["slug"],
            WORKFLOW_TITLE=wf["title"].replace("\\", "").replace('"', "'"),
            EXPLAIN_BODY=emit_workflow_explain(wf, parsed["mental_models"]),
            SOP_STEPS=bash_array_lines(wf["sop_steps"]),
            FAILURE_MODES=bash_array_lines(wf["failure_modes"]),
        )
        atomic_write(wf_path, wf_content, executable=True)
        print(f"  wrote {wf_path.relative_to(skill_dir)}")
        scripts_index.append({
            "category": "workflow",
            "name": wf["slug"],
            "path": f"workflow/{wf['slug']}.sh",
            "purpose": f"{wf['title']} SOP 走查",
        })
        workflow_count += 1

    table_lines = ["| 脚本 | 作用 |", "|------|------|"]
    for s in scripts_index:
        table_lines.append(f"| `{s['path']}` | {s['purpose']} |")
    table_str = "\n".join(table_lines)

    example_dec = ""
    if decision_count > 0:
        first_dec = next(s for s in scripts_index if s["category"] == "decision")
        example_dec = f"# 决策树评估 (基于 playbook)\n./{first_dec['path']}"
    example_wf = ""
    if workflow_count > 0:
        first_wf = next(s for s in scripts_index if s["category"] == "workflow")
        example_wf = f"# SOP 走查 (workflow)\n./{first_wf['path']}"

    readme_path = cli_dir / "README.md"
    readme_content = CLI_README_TEMPLATE.format(
        INDUSTRY_CN=industry_cn,
        EXAMPLE_DECISION_LINE=example_dec,
        EXAMPLE_WORKFLOW_LINE=example_wf,
        SCRIPT_LIST_TABLE=table_str,
    )
    atomic_write(readme_path, readme_content)
    print(f"  wrote {readme_path.relative_to(skill_dir)}")

    print()
    print(f"✓ cli/ emitted: 1 protocol · {decision_count} decision · {workflow_count} workflow · 1 lib · 1 README")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate cli/ subtree for a master skill")
    sub = parser.add_subparsers(dest="action", required=True)

    p_emit = sub.add_parser("emit", help="Generate cli/ from synthesis + workflows")
    p_emit.add_argument("--skill-dir", required=True, help="Target skill directory (cli/ will be created inside)")
    p_emit.add_argument("--synthesis", required=True, help="Path to synthesis.md")
    p_emit.add_argument("--workflows", required=True, help="Path to research/03-workflows.md")
    p_emit.add_argument("--industry-cn", help="Industry name in Chinese (default: derived from skill-dir name)")

    args = parser.parse_args()

    if args.action == "emit":
        sys.exit(cmd_emit(args))


if __name__ == "__main__":
    main()
