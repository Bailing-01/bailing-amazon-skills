#!/usr/bin/env python3
"""skill_writer.py — generate a {industry}-master skill directory from Phase 2 synthesis.

Usage:
  python3 skill_writer.py create --skill-dir <path> --intake <intake.json> --synthesis <synthesis.md>
  python3 skill_writer.py update --skill-dir <path> --section mental_models --content <patch.md>
  python3 skill_writer.py validate --skill-dir <path>
  python3 skill_writer.py list --base-dir <skills_root>

The script is the bridge from Phase 2 (synthesis.md) to a runnable, installable skill.
Design choices:
  - Pure stdlib (no pip install). Runs on macOS python3 out of the box.
  - Atomic writes (write to .tmp then rename).
  - Backup existing SKILL.md before overwrite (`{file}.bak.{timestamp}`).
  - Fails loudly on missing inputs / malformed synthesis — never silently produces a broken skill.
  - Validation is structure-only; full quality check is Phase 4's job (quality_check.md + subagent run).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants

# Sections expected in synthesis.md (header anchors). Phase 2's 9 outputs.
SYNTHESIS_SECTIONS = {
    "mental_models": r"##\s+1\.\s+心智模型",
    "playbook": r"##\s+2\.\s+标准\s+Playbook",
    "tool_stack": r"##\s+3\.\s+工具栈",
    "workflows": r"##\s+4\.\s+工作流",
    "expression_dna": r"##\s+5\.\s+表达\s+DNA",
    "quality_bars": r"##\s+6\.\s+质量基准",
    "intellectual_genealogy": r"##\s+7\.\s+智识谱系",
    "honest_boundaries": r"##\s+8\.\s+诚实边界",
    "agentic_protocol": r"##\s+9\.\s+Agentic\s+Protocol",
}

# meta.json schema fields we set/preserve
META_FIELDS = [
    "name", "industry", "industry_cn", "triggers", "locale", "profile",
    "focus", "last_research_date", "source_count", "primary_source_ratio",
    "tracks_covered", "mental_models_count", "playbook_rules_count",
    "research_dimensions_count", "sub_skills", "generator", "version",
    "changelog",
]

GENERATOR_VERSION = "master-skill v1.4"

SLOW_UPDATE_START = "<!-- SLOW_UPDATE_START -->"
SLOW_UPDATE_END = "<!-- SLOW_UPDATE_END -->"
SLOW_SECTIONS = {"mental_models", "expression_dna", "intellectual_genealogy"}


# ---------------------------------------------------------------------------
# Errors

class SkillWriterError(Exception):
    """Raised on any unrecoverable issue — never silently produce broken skills."""
    pass


# ---------------------------------------------------------------------------
# Parsing

def parse_synthesis(synthesis_path: Path) -> dict[str, str]:
    """Extract 9 sections from synthesis.md by header anchor.

    Returns dict {section_key: section_body_markdown}. Missing sections raise.
    """
    if not synthesis_path.exists():
        raise SkillWriterError(f"synthesis.md not found: {synthesis_path}")

    text = synthesis_path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}

    # Find each section's start position
    starts: list[tuple[str, int]] = []
    for key, pattern in SYNTHESIS_SECTIONS.items():
        match = re.search(pattern, text, re.MULTILINE)
        if not match:
            raise SkillWriterError(
                f"synthesis.md missing required section '{key}' "
                f"(pattern: {pattern}). Run Phase 2 to completion before skill_writer."
            )
        starts.append((key, match.start()))

    # Sort by position so we can slice up to next section's start
    starts.sort(key=lambda t: t[1])
    for i, (key, start_pos) in enumerate(starts):
        end_pos = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        sections[key] = text[start_pos:end_pos].strip()

    return sections


def parse_intake(intake_path: Path) -> dict[str, Any]:
    """Load intake.json. Validates required fields are present."""
    if not intake_path.exists():
        raise SkillWriterError(f"intake.json not found: {intake_path}")

    try:
        data = json.loads(intake_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SkillWriterError(f"intake.json malformed: {e}") from e

    required = ["industry", "slug", "locale", "profile"]
    missing = [f for f in required if f not in data]
    if missing:
        raise SkillWriterError(f"intake.json missing required fields: {missing}")

    title = data.get("title")
    if title is not None:
        if not isinstance(title, str):
            raise SkillWriterError(
                f"intake.json title must be a string, got {type(title).__name__}"
            )
        n = len(title)
        if n < 4 or n > 12:
            raise SkillWriterError(
                f"intake.json title length {n} outside 4-12 codepoints: {title!r}"
            )
        if any(ch in title for ch in "()（）—/\\\n\t"):
            raise SkillWriterError(
                f"intake.json title contains banned chars (parens/dash/slash/whitespace): {title!r}"
            )

    return data


def parse_template(template_path: Path) -> str:
    """Load skill-template.md. The template itself contains the SKILL.md spec
    inside a fenced markdown block. Extract that block as the actual template
    string with {{placeholder}} markers.
    """
    if not template_path.exists():
        raise SkillWriterError(f"skill-template.md not found: {template_path}")

    text = template_path.read_text(encoding="utf-8")
    # The template wraps the SKILL.md spec in ```markdown ... ``` after the
    # `## \`SKILL.md\` template` heading. Extract the first such block after
    # that heading.
    heading_match = re.search(r"##\s+`SKILL\.md`\s+template", text)
    if not heading_match:
        raise SkillWriterError(
            f"skill-template.md doesn't have the expected '## `SKILL.md` template' "
            f"section. Template format may have drifted from spec."
        )

    after_heading = text[heading_match.end():]
    block_match = re.search(r"```markdown\n(.*?)\n```", after_heading, re.DOTALL)
    if not block_match:
        raise SkillWriterError(
            "skill-template.md: no ```markdown ... ``` block found after the "
            "SKILL.md template heading."
        )

    return block_match.group(1)


# ---------------------------------------------------------------------------
# Counting helpers (for meta.json stats)

def count_mental_models(section_body: str) -> int:
    """Count subsections matching '### 1.1' / '### 1.2' / etc."""
    return len(re.findall(r"^###\s+1\.\d+\s+", section_body, re.MULTILINE))


def count_playbook_rules(section_body: str) -> int:
    """Playbook rules are numbered list items."""
    return len(re.findall(r"^\d+\.\s+\*\*", section_body, re.MULTILINE))


def count_protocol_dimensions(section_body: str) -> int:
    """Agentic Protocol dimensions match '### 9.1' / '### 9.2'."""
    return len(re.findall(r"^###\s+9\.\d+\s+", section_body, re.MULTILINE))


def count_research_sources(research_dir: Path) -> dict[str, int]:
    """Walk research/*.md and count sources for `meta.json.source_count` and
    `primary_source_ratio`.

    Iter 26 (codex 3rd-audit P0 #2a fix): prefer Source Manifest tables
    (Q1 format with `T01-S001` source_ids and explicit `bucket`) when present;
    fall back to legacy `[Primary]/[Secondary]/[Reference]` markers when no
    manifest is found.
    """
    if not research_dir or not research_dir.exists():
        return {"primary": 0, "secondary": 0, "reference": 0, "total": 0,
                "primary_ratio": 0.0}

    # Try manifest path first (iter 26 prefer)
    skill_dir = research_dir.parent.parent
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "research"))
        import source_manifest  # type: ignore
        rows = source_manifest.parse_manifests(skill_dir)
    except ImportError:
        rows = []

    if rows:
        rb = source_manifest.primary_ratio(rows)
        return {
            "primary": rb.first_hand,        # verified + surrogate as one count
            "verified_primary": rb.verified_primary,
            "surrogate_primary": rb.surrogate_primary,
            "secondary": rb.secondary,
            "reference": rb.reference,
            "blacklisted": rb.blacklisted,
            "dead": rb.dead,
            "total": rb.total,
            "primary_ratio": round(rb.ratio, 4),
        }

    # Legacy: count free-text [Primary]/[Secondary]/[Reference] markers
    primary = secondary = reference = 0
    for md_file in research_dir.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        primary += len(re.findall(r"\[Primary\]", text))
        secondary += len(re.findall(r"\[Secondary\]", text))
        reference += len(re.findall(r"\[Reference\]", text))
    total = primary + secondary + reference
    return {
        "primary": primary,
        "secondary": secondary,
        "reference": reference,
        "total": total,
        "primary_ratio": round(primary / total, 2) if total else 0.0,
    }


SKILL_DESCRIPTION_MAX = 1024  # Agent Skills spec cap for frontmatter `description`


def short_industry_name(intake: dict) -> str:
    """iter45: Phase 0 intake often stores a full scope paragraph in `industry`
    (observed: 1,677 chars). The template splices that field into `description`
    three times, producing a frontmatter that blew past the 1024-char spec cap
    by 5x and read `X (X (English) - ...)`. Derive a real name instead: prefer
    `industry_en`, cut at the first bracket / em-dash / full stop, cap at 80.
    """
    raw = (intake.get("industry_en") or intake.get("industry") or "").strip()
    for sep in (" (", "（", " — ", " - ", "。", "；", ";"):
        idx = raw.find(sep)
        if idx > 0:
            raw = raw[:idx]
            break
    raw = raw.strip().rstrip(",，、")
    return raw[:80] if raw else (intake.get("industry_cn") or "")


def clamp_frontmatter_description(skill_md: str, limit: int = SKILL_DESCRIPTION_MAX) -> str:
    """iter45: hard-clamp the YAML `description:` block so a runaway intake field
    can never ship a frontmatter that exceeds the Agent Skills cap. Keeps the
    block-scalar form and trims on a sentence boundary where one is available.
    """
    m = re.search(r"^description:\s*\|\s*\n((?:(?:[ \t]+.*)?\n)+)", skill_md, re.MULTILINE)
    if not m:
        return skill_md
    body = m.group(1)
    text = " ".join(line.strip() for line in body.splitlines() if line.strip())
    if len(text) <= limit:
        return skill_md
    cut = text[:limit]
    for sep in ("。", ". ", "；", "; "):
        idx = cut.rfind(sep)
        if idx > limit * 0.5:
            cut = cut[:idx + len(sep)]
            break
    return skill_md[:m.start(1)] + "  " + cut.strip() + "\n" + skill_md[m.end(1):]


def _decay_risk_from_section(section: str, default: str) -> str:
    """iter45: the registry used to hardcode `high` for tool stack + workflows,
    which contradicted any synthesis declaring `Decay risk: medium` for the same
    module. Read the synthesis instead; fall back to the old default.
    """
    if not section:
        return default
    m = re.search(r"Decay\s+risk:\s*(low|medium|high)", section, re.IGNORECASE)
    return m.group(1).lower() if m else default


def build_time_decay_registry(synthesis_sections: dict[str, str], research_date: str) -> str:
    """Iter 22 fix #3: emit explicit `last_updated` + `decay_risk` markers per
    module so quality_check.check_time_decay_marks() finds them. Synthesis often
    uses prose dates; this registry uses the regex-friendly format.
    """
    tool_risk = _decay_risk_from_section(synthesis_sections.get("tool_stack", ""), "high")
    wf_risk = _decay_risk_from_section(synthesis_sections.get("workflows", ""), "high")
    return f"""
## Time-decay Registry

This skill's modules decay at different speeds. Re-run `update 大师 {{slug}}`
when the dates below cross the recommended cadence listed in this table.

| Module | last_updated | decay_risk | Recommended refresh cadence |
|--------|-------------|-----------|---------------------------|
| Mental models | last_updated: {research_date} | decay_risk: low | 1-2 years |
| Standard playbook | last_updated: {research_date} | decay_risk: low | 6-12 months |
| Tool stack | last_updated: {research_date} | decay_risk: {tool_risk} | 3-6 months |
| Workflows / pipeline | last_updated: {research_date} | decay_risk: {wf_risk} | 3-6 months |
| Expression DNA | last_updated: {research_date} | decay_risk: low | 6-12 months |
| Sources (Track 5) | last_updated: {research_date} | decay_risk: medium | 6 months |
| Glossary / standards / regulations | last_updated: {research_date} | decay_risk: medium | 6 months (regulations may force sooner) |
| Intellectual genealogy | last_updated: {research_date} | decay_risk: low | 1-2 years |
| Honest boundaries | last_updated: {research_date} | decay_risk: low | re-assess each refresh |

last_updated values reflect the synthesis date. Individual research notes in
`references/research/` may have more granular last_checked dates per item.
"""


def format_protocol_dims_for_step2(agentic_protocol_section: str) -> str:
    """从 synthesis Section 9 抽出每个 9.X 维度, 渲染成 Agentic Protocol Step 2 的 markdown.

    输出格式 (兼容两种 synthesis 写法):
        #### 维度 1: {title}
        - 看什么: {what}
        - 在哪看: {where}
        - 输出: {output_format}

    Iter 26 (codex 3rd-audit P0 #2b): tolerate two synthesis vocabularies —
      legacy: `**看什么** / **在哪看** / **输出格式**`
      iter 24+ synthesis: `**轴** / **触发** / **输出**`
    The 5 维度 in iter 24+ synthesis was 100% empty in produced SKILL.md
    until this fix because the regex only matched legacy keys.
    """
    dims_md: list[str] = []
    pat = re.compile(
        r"^###\s+9\.(\d+)\s+(.+?)$(?P<body>.*?)(?=^###\s+9\.|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    # Each tuple: (canonical_label, alt_labels_to_match)
    field_aliases = [
        ("what", ["看什么", "轴"]),
        ("where", ["在哪看", "触发"]),
        ("output", ["输出格式", "输出"]),
    ]
    for m in pat.finditer(agentic_protocol_section):
        dim_num = m.group(1)
        title = m.group(2).strip()
        body = m.group("body")
        extracted: dict[str, str] = {}
        for canonical, aliases in field_aliases:
            for label in aliases:
                p = re.search(
                    rf"-\s*\*\*{re.escape(label)}\*\*[：:]\s*(.+?)$",
                    body, re.MULTILINE,
                )
                if p:
                    extracted[canonical] = p.group(1).strip()
                    break
        block = (
            f"#### 维度 {dim_num}: {title}\n"
            f"- 看什么: {extracted.get('what', '')}\n"
            f"- 在哪看: {extracted.get('where', '')}\n"
            f"- 输出: {extracted.get('output', '')}"
        )
        dims_md.append(block)
    return "\n\n".join(dims_md)


def sanity_check_rendered_skill(skill_md: str) -> list:
    """渲染完成的 SKILL.md 自检. 防止之前那种 "Step 2 占位符没填 / Section 9 重复" 再溜出去.

    检查项:
    - 没有残留的 `{{...}}` placeholder
    - Agentic Protocol Step 2 有内容 (至少含一个 "维度" 或 "dimension" 字样)
    - 心智模型 / 标准 Playbook / 诚实边界 三个核心 section 必须存在
    - "Agentic Protocol" 字样只出现 1 次 (避免 Section 9 重复)

    返回问题列表. 空列表 = pass.
    """
    issues: list = []

    # 1. leftover placeholder
    leftover = re.findall(r"\{\{[^}\n]{1,80}?\}\}", skill_md)
    if leftover:
        # 去重 + 列出最多 5 个
        unique = list(dict.fromkeys(leftover))[:5]
        issues.append(f"leftover {{...}} 占位符: {unique}")

    # 2. Step 2 是否填充 (至少有 "维度" 字样)
    step2_match = re.search(
        r"### Step 2[^\n]*\n(?P<body>.*?)(?=\n### Step 3|\n##\s)",
        skill_md, re.DOTALL,
    )
    if step2_match:
        step2_body = step2_match.group("body")
        if "维度" not in step2_body and "dimension" not in step2_body.lower():
            issues.append("Agentic Protocol Step 2 没有「维度」字样, 可能未被填充")
    else:
        issues.append("找不到 Agentic Protocol Step 2 段")

    # 3. 必须存在的核心 section
    for required_heading in ["## 心智模型", "## 标准 Playbook", "## 诚实边界"]:
        if required_heading not in skill_md:
            issues.append(f"缺少必备 section: {required_heading}")

    # 4. Agentic Protocol 字样只能在「## Agentic Protocol（先研究，再发言）」一处
    ap_section_count = len(re.findall(r"^##\s+Agentic Protocol", skill_md, re.MULTILINE))
    if ap_section_count > 1:
        issues.append(f"Agentic Protocol 顶级 section 出现 {ap_section_count} 次 (应 = 1)")

    return issues


def inject_synthesis_body(skill_md: str, synthesis_sections: dict[str, str],
                          research_date: str) -> str:
    """注入 synthesis 产物到 SKILL.md 模板.

    两步注入:
    1. 把 template 里 Agentic Protocol Step 2 的 `{{# Phase 2.9 ... }}` placeholder
       替换为 Section 9 抽出的真实维度 (维度 1, 2, ...) — 这样 Step 2 不再是空的.
    2. 砍掉 template 中 `## 心智模型` 之后的 stub, 用 synthesis 1-8 重写
       (Section 9 已经在 Step 2 里, 这里不重复.)

    section_order 不再含 agentic_protocol — Step 2 已经填充, 避免重复.
    """
    # ---- Step 1: 用 Section 9 的真实维度替换 Step 2 的 placeholder ----
    protocol_md = format_protocol_dims_for_step2(synthesis_sections.get("agentic_protocol", ""))
    if protocol_md:
        # 匹配模板里 `{{# Phase 2.9 ... \n}}` 多行块. 内嵌的 {{name}} 不能用懒惰
        # 匹配 (会提前停止), 必须用「独占一行的 }}」作为终止锚点.
        skill_md = re.sub(
            r"\{\{#\s*Phase\s*2\.9.*?\n\}\}",
            protocol_md,
            skill_md,
            count=1,
            flags=re.DOTALL,
        )
    # ---- Step 2: 砍 body 后用 synthesis 重写 (不含 agentic_protocol) ----
    body_marker = re.search(r"^##\s+心智模型", skill_md, re.MULTILINE)
    if body_marker is None:
        synth_body = "\n\n---\n\n# Synthesized Body\n\n"
    else:
        # template 末尾通常已经有 `---` 分隔线 (Step 3 之后), 不再额外加避免重复
        trimmed = skill_md[: body_marker.start()].rstrip()
        skill_md = trimmed + "\n\n"
        synth_body = ""

    # Section 9 (agentic_protocol) 已在 Step 2 里, 不再重复
    section_order = [
        ("mental_models", "心智模型"),
        ("playbook", "标准 Playbook"),
        ("tool_stack", "工具栈与选型决策树"),
        ("workflows", "工作流 / Pipeline"),
        ("expression_dna", "表达 DNA"),
        ("quality_bars", "质量基准 + 反模式"),
        ("intellectual_genealogy", "智识谱系"),
        ("honest_boundaries", "诚实边界"),
    ]

    parts: list[str] = [synth_body] if synth_body else []
    for key, friendly_heading in section_order:
        section = synthesis_sections.get(key, "")
        section_body = re.sub(
            r"^##\s+\d+\.\s+[^\n]+\n", f"## {friendly_heading}\n", section,
            count=1, flags=re.MULTILINE,
        )
        if key in SLOW_SECTIONS:
            parts.append(SLOW_UPDATE_START)
            parts.append(section_body.strip())
            parts.append(SLOW_UPDATE_END)
        else:
            parts.append(section_body.strip())
        parts.append("")

    parts.append(build_time_decay_registry(synthesis_sections, research_date))

    return skill_md + "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Writing

def collect_existing_sub_skills(skill_dir: Path) -> list[dict]:
    """Scan skill_dir/sub-skills/ and harvest manifests so they survive regen.

    Codex P2 fix: skill_writer used to always write meta.sub_skills = [] on
    regen, even when person sub-skills had been added under sub-skills/*.
    This made meta.json drift out of sync with the filesystem until manually
    patched. Idempotent: returns [] when dir is missing or empty.
    """
    sub_skills_dir = skill_dir / "sub-skills"
    if not sub_skills_dir.exists() or not sub_skills_dir.is_dir():
        return []
    out: list[dict] = []
    for child in sorted(sub_skills_dir.iterdir()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue
        figure = ""
        perspective = ""
        fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            # Iter 25/26: handle YAML block-scalar markers and inline strings.
            # Block-scalar markers: `|`, `|-`, `|+`, `>`, `>-`, `>+` (any indent
            # indicator suffix). Iter 26 fix (codex 3rd-audit P1 #3): the
            # original regex only matched `|`, missed `|-/|+/>`.
            block_m = re.search(
                r"^description:\s*[|>][-+]?\s*\n((?:(?:[ \t]+.*)?\n)+)",
                fm_text, re.MULTILINE,
            )
            inline_m = re.search(r"^description:\s*(.+)$", fm_text, re.MULTILINE)
            desc = ""
            if block_m:
                # Strip leading indent from each line, join with spaces.
                # Skip empty lines within the block.
                desc_lines = [
                    re.sub(r"^[ \t]+", "", line)
                    for line in block_m.group(1).splitlines()
                    if line.strip()
                ]
                desc = " ".join(desc_lines)
            elif inline_m:
                desc = inline_m.group(1).strip().strip('"').strip("'")
                # Block-scalar markers only (with optional indent indicators):
                # leave desc empty so we don't return literal `|` to caller.
                if re.match(r"^[|>][-+]?$", desc):
                    desc = ""
            if desc:
                seg = re.match(r"([^.。]+?)\s*视角[.。]\s*(.*)", desc)
                if seg:
                    figure = seg.group(1).strip()
                    perspective = seg.group(2).strip()[:200]
                else:
                    head, _, rest = desc.partition(".")
                    figure = head.strip()[:80]
                    perspective = rest.strip()[:200]
        out.append({
            "slug": child.name,
            "path": f"sub-skills/{child.name}/SKILL.md",
            "figure": figure or child.name,
            "perspective": perspective,
        })
    return out


def _safe_copytree(src: Path, dst: Path) -> None:
    """Copy src → dst safely. Iter 26 (codex 3rd-audit P1 #3 hardening):

    - Skip when src == dst (in-place run)
    - Refuse when one is contained in the other (would corrupt source)
    - Use tmp + atomic rename so a failed copy doesn't leave half-deleted dst
    """
    src_resolved = src.resolve()
    dst_resolved = dst.resolve()
    if src_resolved == dst_resolved:
        return  # already in place — common when running skill_writer in-place
    # Containment guard: is src under dst, or dst under src?
    src_str = str(src_resolved)
    dst_str = str(dst_resolved)
    if src_str.startswith(dst_str + "/") or dst_str.startswith(src_str + "/"):
        # src under dst would mean rmtree(dst) deletes src too. dst under src
        # would mean copytree(src, dst) recurses infinitely.
        raise SkillWriterError(
            f"unsafe copytree: src and dst overlap "
            f"(src={src_str}, dst={dst_str}). "
            f"Move research_dir outside the skill_dir or use --in-place."
        )
    # Tmp + atomic rename — if copy fails, dst remains intact
    import tempfile
    parent = dst.parent
    parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".copytree-", dir=parent))
    tmp_target = tmp / "data"
    try:
        shutil.copytree(src, tmp_target)
        if dst.exists():
            backup = dst.with_suffix(dst.suffix + ".bak.{}".format(now_iso_timestamp()))
            dst.rename(backup)
            try:
                tmp_target.rename(dst)
            except Exception:
                # restore backup on failure
                if dst.exists():
                    shutil.rmtree(dst)
                backup.rename(dst)
                raise
            else:
                shutil.rmtree(backup, ignore_errors=True)
        else:
            tmp_target.rename(dst)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def now_iso_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso_timestamp() -> str:
    """Iter 26 (codex 4-audit P1 Safe Copy): nanosecond + pid for backup
    filename uniqueness — second granularity collides under parallel calls."""
    import os, time
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ns = time.time_ns() % 1_000_000  # microsecond fraction (6 digits)
    return f"{ts}-{ns:06d}-{os.getpid()}"


def prune_old_backups(path: Path, keep: int = 3) -> int:
    """Keep at most `keep` backup files matching `<path>.bak.*`. Returns
    count of deleted backups. Idempotent. Used to stop SKILL.md.bak.*
    accumulation in prototype dirs."""
    parent = path.parent
    if not parent.exists():
        return 0
    base = path.name + ".bak."
    candidates = sorted(
        (p for p in parent.iterdir() if p.name.startswith(base)),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    deleted = 0
    for old in candidates[keep:]:
        try:
            old.unlink()
            deleted += 1
        except OSError:
            pass
    return deleted


def atomic_write(path: Path, content: str) -> None:
    """Write to .tmp then rename. Avoids leaving partial files on crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def backup_if_exists(path: Path, keep: int = 3) -> Path | None:
    """If path exists, copy to {path}.bak.{ts}, return backup path. Iter 26:
    also prune old backups so prototype dirs don't accumulate dozens of bak
    files (codex 4-audit P1 Safe Copy)."""
    if not path.exists():
        return None
    backup = path.with_suffix(path.suffix + f".bak.{now_iso_timestamp()}")
    shutil.copy2(path, backup)
    prune_old_backups(path, keep=keep)
    return backup


# ---------------------------------------------------------------------------
# Action: create

def action_create(
    skill_dir: Path,
    intake: dict[str, Any],
    synthesis_sections: dict[str, str],
    template: str,
    research_dir: Path | None,
    emit_cli: bool = True,
) -> dict[str, Any]:
    """Generate a fresh skill directory."""
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Build replacements
    industry = intake["industry"]
    industry_cn = intake.get("industry_cn", industry)
    slug = intake["slug"]
    locale = intake["locale"]
    profile = intake["profile"]
    focus = intake.get("focus", "comprehensive")
    if isinstance(focus, dict):
        # primary/secondary structure
        focus_str = f"{focus.get('primary', 'comprehensive')}+{focus.get('secondary', '')}".rstrip("+")
    else:
        focus_str = str(focus)

    research_date = now_iso_date()

    # Stats
    mm_count = count_mental_models(synthesis_sections["mental_models"])
    pb_count = count_playbook_rules(synthesis_sections["playbook"])
    dim_count = count_protocol_dimensions(synthesis_sections["agentic_protocol"])

    triggers = intake.get("triggers", [])
    triggers_yaml = "\n".join(f'  - "{t}"' for t in triggers) or '  - "{{TODO: fill triggers}}"'

    # Iter 26 (codex 4-audit P0-2a): compute research_stats BEFORE template
    # replacement so the `{{N}}` source_count placeholder uses live manifest
    # data instead of the stale intake value.
    research_stats_for_template = count_research_sources(research_dir) if research_dir else {
        "primary": intake.get("source_count", 0),
        "total": intake.get("source_count", 0),
        "primary_ratio": intake.get("primary_source_ratio", 0.0),
    }

    # Pre-replace the YAML triggers block (iter 18 fix). The template has a
    # multi-line block like:
    #   triggers:
    #     - "{{keyword-1, e.g. 'agent framework'}}"
    #     - "{{keyword-2}}"
    #     - "{{keyword-N}}"
    # which the simple {{x}} replacement won't catch. Use regex to match the
    # whole block and substitute with the actual triggers list.
    template = re.sub(
        r"^triggers:\n(?:\s+-\s+\"\{\{keyword-[^\"\}]+\}\}\"\n){2,}",
        f"triggers:\n{triggers_yaml}\n",
        template,
        count=1,
        flags=re.MULTILINE,
    )

    # display_name: 中文 locale 时用 industry_cn, 其他用 industry. 让 body 文案
    # 在中文 skill 里读起来不生硬 (避免 "收到与 foot and ankle surgery 相关的问题时").
    industry_short = short_industry_name(intake)
    display_name = industry_cn if locale.startswith("zh") else industry_short

    # Replacements for the template's {{...}} placeholders
    replacements = {
        "industry-slug": slug,
        "industry-cn-name": industry_cn,
        "industry-en-name": industry_short,
        "industry-display-name": display_name,
        "one-sentence value prop, e.g. \"automated mastery of LLM agent infrastructure: top builders' mental models, tool stack, current workflows, jargon, and where to keep up\".":
            f"automated mastery of {industry_short}: top builders' mental models, tool stack, current workflows, jargon, and where to keep up.",
        "trigger-cn-1": triggers[0] if len(triggers) > 0 else "造大师",
        "trigger-cn-2": triggers[1] if len(triggers) > 1 else f"{industry_cn} master",
        "trigger-cn-3": triggers[2] if len(triggers) > 2 else f"我做 {industry_cn}",
        "trigger-en-1": triggers[3] if len(triggers) > 3 else industry_short,
        "trigger-en-2": triggers[4] if len(triggers) > 4 else f"{industry_short} infra",
        "en | zh-CN | ja | ko | global": locale,
        "YYYY-MM-DD": research_date,
        "N": str(research_stats_for_template.get("total") or intake.get("source_count", 0)),
        "practitioner | learner | investor | consultant": profile,
        "X.Y": GENERATOR_VERSION.split(" ")[-1].lstrip("v"),
        "punchy one-liner — what this skill changes for the agent. Quote a top figure if natural.":
            (f"装上这个 skill, agent 立刻进入「{display_name}」资深人模式 — 用这一行的心智模型 + 决策规则 + 工作流 + 说话方式 给判断。"
             if locale.startswith("zh")
             else f"This skill makes the agent operate as a senior {industry_short} practitioner — applying the field's mental models, picking the right tools, knowing the current workflows, speaking the jargon."),
        "trigger-list": ", ".join(triggers) or "industry-specific keywords",
    }

    # Apply replacements (order matters — longer patterns first to avoid partial match collisions)
    skill_md = template
    for placeholder, value in sorted(replacements.items(), key=lambda kv: -len(kv[0])):
        skill_md = skill_md.replace("{{" + placeholder + "}}", value)

    skill_md = clamp_frontmatter_description(skill_md)

    # iter 22 fix #1: inject synthesis body in place of the template's
    # placeholder body sections. Replaces the previous shell-only output.
    skill_md = inject_synthesis_body(skill_md, synthesis_sections, research_date)

    # iter 22 fix #2: compute primary_source_ratio from research/ rather than
    # relying on the (often stale) intake.json value
    research_stats = count_research_sources(research_dir) if research_dir else {
        "primary": intake.get("source_count", 0),
        "secondary": 0,
        "reference": 0,
        "total": intake.get("source_count", 0),
        "primary_ratio": intake.get("primary_source_ratio", 0.0),
    }

    # 自检 1: 渲染后 SKILL.md 不应该有 leftover 占位符 / 未注入的 stub
    self_check_issues = sanity_check_rendered_skill(skill_md)
    if self_check_issues:
        msg = "渲染后 SKILL.md 有问题, 不写出. 请检查 template / synthesis / inject 逻辑:\n  - " + "\n  - ".join(self_check_issues)
        raise SkillWriterError(msg)

    # Write SKILL.md
    skill_md_path = skill_dir / "SKILL.md"
    backup_if_exists(skill_md_path)
    atomic_write(skill_md_path, skill_md)

    # Write meta.json
    meta = {
        "name": f"{slug}-master",
        "industry": industry,
        "industry_cn": industry_cn,
        "triggers": triggers,
        "locale": locale,
        "profile": profile,
        "focus": focus,
        "last_research_date": research_date,
        "source_count": research_stats["total"] or intake.get("source_count", 0),
        "primary_source_ratio": research_stats["primary_ratio"]
            if research_stats["total"] > 0
            else intake.get("primary_source_ratio", 0.0),
        "tracks_covered": ["figures", "tools", "workflows", "canon", "sources", "glossary"],
        "mental_models_count": mm_count,
        "playbook_rules_count": pb_count,
        "research_dimensions_count": dim_count,
        "sub_skills": collect_existing_sub_skills(skill_dir),
        "generator": GENERATOR_VERSION,
        "version": GENERATOR_VERSION.split(" ")[-1].lstrip("v"),
        "changelog": [
            {"version": GENERATOR_VERSION.split(" ")[-1].lstrip("v"), "date": research_date,
             "what": "Initial generation"}
        ],
    }
    meta_path = skill_dir / "meta.json"
    atomic_write(meta_path, json.dumps(meta, indent=2, ensure_ascii=False) + "\n")

    # Copy synthesis + research notes (so the skill is self-contained)
    refs_dir = skill_dir / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    if research_dir and research_dir.exists():
        target_research = refs_dir / "research"
        _safe_copytree(research_dir, target_research)
    # iter 22: copy synthesis.md alongside research so quality_check item 12
    # (multi-figure consensus) can find it. Also helps consumers read the full
    # Phase 2 output without having to walk back to the prototype dir.
    # Iter 25 fix: skip copy when src == dst (in-place run).
    synthesis_src = research_dir.parent / "synthesis.md" if research_dir else None
    synthesis_dst = refs_dir / "synthesis.md"
    if synthesis_src and synthesis_src.exists():
        if synthesis_src.resolve() != synthesis_dst.resolve():
            shutil.copy2(synthesis_src, synthesis_dst)

    # Empty placeholder dirs
    (skill_dir / "sub-skills").mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)

    # v0.6: emit cli/ subtree (思维顾问 + 实操 CLI 套件).
    # Reads synthesis.md (Section 2 + Section 9) and research/03-workflows.md
    # to generate bash scripts under cli/.
    cli_emit_result: dict[str, Any] = {"emitted": False}
    if emit_cli:
        cli_writer_path = Path(__file__).resolve().parent / "cli_writer.py"
        synthesis_in_skill = refs_dir / "synthesis.md"
        workflows_in_skill = refs_dir / "research" / "03-workflows.md"
        if cli_writer_path.exists() and synthesis_in_skill.exists() and workflows_in_skill.exists():
            try:
                proc = subprocess.run(
                    [
                        sys.executable, str(cli_writer_path), "emit",
                        "--skill-dir", str(skill_dir),
                        "--synthesis", str(synthesis_in_skill),
                        "--workflows", str(workflows_in_skill),
                        "--industry-cn", industry_cn,
                    ],
                    check=True, capture_output=True, text=True,
                )
                cli_emit_result = {"emitted": True, "stdout": proc.stdout.strip().splitlines()[-1] if proc.stdout else ""}
            except subprocess.CalledProcessError as e:
                print(f"⚠ cli_writer failed (non-fatal): {e.stderr}", file=sys.stderr)
                cli_emit_result = {"emitted": False, "error": e.stderr.strip()}

    return {
        "skill_md": str(skill_md_path),
        "meta_json": str(meta_path),
        "stats": {
            "mental_models": mm_count,
            "playbook_rules": pb_count,
            "agentic_protocol_dims": dim_count,
        },
        "cli": cli_emit_result,
    }


# ---------------------------------------------------------------------------
# Action: validate

def action_validate(skill_dir: Path) -> dict[str, Any]:
    """Structure-only validation. Full quality check is Phase 4's responsibility."""
    issues: list[str] = []

    skill_md = skill_dir / "SKILL.md"
    meta = skill_dir / "meta.json"

    if not skill_md.exists():
        issues.append(f"SKILL.md missing at {skill_md}")
    if not meta.exists():
        issues.append(f"meta.json missing at {meta}")

    if meta.exists():
        try:
            meta_data = json.loads(meta.read_text(encoding="utf-8"))
            for field in ["name", "industry", "locale", "last_research_date", "version"]:
                if field not in meta_data:
                    issues.append(f"meta.json missing required field: {field}")
            mm = meta_data.get("mental_models_count", 0)
            if not (3 <= mm <= 7):
                issues.append(f"mental_models_count={mm} out of [3,7] range")
            pb = meta_data.get("playbook_rules_count", 0)
            if not (5 <= pb <= 10):
                issues.append(f"playbook_rules_count={pb} out of [5,10] range")
            dim = meta_data.get("research_dimensions_count", 0)
            if not (3 <= dim <= 10):
                issues.append(f"research_dimensions_count={dim} out of [3,10] range")
        except json.JSONDecodeError as e:
            issues.append(f"meta.json malformed: {e}")

    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8")
        for required in ["## 激活规则", "## Agentic Protocol", "## 心智模型"]:
            if required not in text:
                issues.append(f"SKILL.md missing required heading: {required}")

    return {"valid": len(issues) == 0, "issues": issues}


# ---------------------------------------------------------------------------
# Action: list

def action_list(base_dir: Path) -> list[dict[str, Any]]:
    """List all *-master skills under base_dir with key metadata."""
    if not base_dir.exists():
        return []
    skills: list[dict[str, Any]] = []
    for child in sorted(base_dir.iterdir()):
        if not child.is_dir() or not child.name.endswith("-master"):
            continue
        meta_path = child / "meta.json"
        if meta_path.exists():
            try:
                meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
                skills.append({
                    "slug": child.name,
                    "industry": meta_data.get("industry"),
                    "locale": meta_data.get("locale"),
                    "last_research_date": meta_data.get("last_research_date"),
                    "version": meta_data.get("version"),
                })
            except json.JSONDecodeError:
                skills.append({"slug": child.name, "error": "meta.json malformed"})
        else:
            skills.append({"slug": child.name, "error": "no meta.json"})
    return skills


# ---------------------------------------------------------------------------
# CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="skill_writer — generate / validate / list master-skill outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="action", required=True)

    p_create = sub.add_parser("create", help="Create a new {industry}-master skill")
    p_create.add_argument("--skill-dir", required=True, type=Path,
                          help="Target directory for the generated skill")
    p_create.add_argument("--intake", required=True, type=Path, help="Path to intake.json")
    p_create.add_argument("--synthesis", required=True, type=Path,
                          help="Path to Phase 2 synthesis.md")
    p_create.add_argument("--template", required=True, type=Path,
                          help="Path to references/skill-template.md")
    p_create.add_argument("--research-dir", type=Path, default=None,
                          help="Path to references/research/ — copied into the new skill")
    p_create.add_argument("--no-cli", action="store_true",
                          help="Skip cli/ subtree emission (默认开启 v0.6 CLI 工具流)")

    p_validate = sub.add_parser("validate", help="Structure-only validation of an existing skill")
    p_validate.add_argument("--skill-dir", required=True, type=Path)

    p_list = sub.add_parser("list", help="List *-master skills in a directory")
    p_list.add_argument("--base-dir", required=True, type=Path,
                        help="Directory containing *-master/ subdirectories")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.action == "create":
            intake = parse_intake(args.intake)
            synthesis_sections = parse_synthesis(args.synthesis)
            template = parse_template(args.template)
            result = action_create(args.skill_dir, intake, synthesis_sections, template,
                                   args.research_dir, emit_cli=not args.no_cli)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if args.action == "validate":
            result = action_validate(args.skill_dir)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result["valid"] else 1

        if args.action == "list":
            result = action_list(args.base_dir)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

    except SkillWriterError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    return 99  # unreachable


if __name__ == "__main__":
    sys.exit(main())
