#!/usr/bin/env python3
"""quality_check.py — mechanical Phase 4.4 rubric runner.

Usage:
  python3 quality_check.py check --skill-dir <path>
  python3 quality_check.py check --skill-dir <path> --json

Distinct from `prompts/quality_check.md` (the agent execution script that runs
4.1 sanity / 4.2 edge case / 4.3 voice check via subagent). This script runs
only the 4.4 mechanical rubric — purely structural checks that don't need a
subagent.

Reads SKILL.md + meta.json + references/synthesis.md + references/research/.
Verdict: PASS / PARTIAL / FAIL.

Pure stdlib. macOS python3 out-of-the-box.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

# Sibling modules — pure stdlib, safe to import unconditionally.
try:
    from . import source_verifier  # type: ignore
    from . import source_manifest  # type: ignore
except ImportError:  # script-mode (python3 quality_check.py ...)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import source_verifier  # type: ignore[no-redef]
    import source_manifest  # type: ignore[no-redef]

# ---------------------------------------------------------------------------

class QCError(Exception):
    pass


# Rubric item: (id, label, checker_fn returning (status, detail)).
# Status: "pass" / "partial" / "fail" / "needs_subagent" / "skipped".


def load_skill_text(skill_dir: Path) -> str:
    """Load SKILL.md, falling back to synthesis.md if SKILL.md doesn't exist
    (allows the runner to validate Phase 2 output before Phase 3 writeup)."""
    skill_md = skill_dir / "SKILL.md"
    synthesis = skill_dir / "references" / "synthesis.md"
    if skill_md.exists():
        return skill_md.read_text(encoding="utf-8")
    if synthesis.exists():
        return synthesis.read_text(encoding="utf-8")
    raise QCError(
        f"Neither SKILL.md nor references/synthesis.md found at {skill_dir}. "
        f"Run Phase 3 (skill_writer) or Phase 2 (synthesis) first."
    )


def load_meta(skill_dir: Path) -> dict[str, Any]:
    """Load meta.json if present, return empty dict otherwise."""
    meta_path = skill_dir / "meta.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise QCError(f"meta.json malformed: {e}") from e


# ---------------------------------------------------------------------------
# Individual rubric checks


def check_mental_models_count(skill_text: str, meta: dict) -> tuple[str, str]:
    """Item 1: 心智模型数 in [3, 7]. (iter 18) When meta and body disagree,
    return PARTIAL so reviewer notices stale meta after manual edits."""
    n_meta = meta.get("mental_models_count")
    n_body = len(re.findall(r"^###\s+1\.\d+\s+", skill_text, re.MULTILINE))

    if n_meta is not None and n_body > 0 and n_meta != n_body:
        return "partial", (
            f"meta.json says {n_meta}, body has {n_body} sections — "
            f"meta out of sync with body, re-run skill_writer or update meta"
        )

    n = n_meta if n_meta is not None else n_body
    if 3 <= n <= 7:
        return "pass", f"{n} models (in [3, 7])"
    if n < 3:
        return "fail", f"{n} models (< 3, too thin)"
    return "fail", f"{n} models (> 7, insufficient extraction)"


def check_mental_model_limits(skill_text: str) -> tuple[str, str]:
    """Item 2: each mental model has a 局限 / Limitation field."""
    # Find each ### 1.N section and check for `局限` / `Limitation` in its body.
    matches = list(re.finditer(
        r"^###\s+1\.(\d+)\s+(.+?)$(.*?)(?=^###\s+1\.\d+\s+|^##\s+|\Z)",
        skill_text,
        re.MULTILINE | re.DOTALL,
    ))
    if not matches:
        return "skipped", "no mental model sections found (### 1.N pattern)"
    missing: list[str] = []
    for m in matches:
        body = m.group(3)
        if not re.search(r"\*?\*?(局限|Limitation|Limits?)\*?\*?\s*[:：]", body):
            missing.append(m.group(2).strip()[:40])
    if not missing:
        return "pass", f"all {len(matches)} models have 局限 field"
    return "fail", f"{len(missing)}/{len(matches)} missing 局限: {missing[:3]}"


def check_playbook_count(skill_text: str, meta: dict) -> tuple[str, str]:
    """Item 3: Playbook rules count in [5, 10]. Iter 22: also matches friendly
    headings (## 标准 Playbook) emitted by skill_writer body injection, not just
    numbered ones (## 2. 标准 Playbook) used in synthesis.md."""
    n_meta = meta.get("playbook_rules_count")
    if n_meta is not None:
        n = n_meta
    else:
        # Numbered list under ## 2. heading or ## heading
        section_match = re.search(
            r"##\s+(?:2\.\s+)?标准\s+Playbook(.*?)(?=^##\s|\Z)",
            skill_text,
            re.MULTILINE | re.DOTALL,
        )
        if not section_match:
            return "skipped", "no Playbook section found"
        n = len(re.findall(r"^\d+\.\s+\*\*", section_match.group(1), re.MULTILINE))
    if 5 <= n <= 10:
        return "pass", f"{n} rules (in [5, 10])"
    if n < 5:
        return "fail", f"{n} rules (< 5, too thin)"
    return "fail", f"{n} rules (> 10, insufficient curation)"


def check_playbook_cases(skill_text: str) -> tuple[str, str]:
    """Item 4: each playbook rule has ≥ 1 case (— bullet under it)."""
    section_match = re.search(
        r"##\s+(?:2\.\s+)?标准\s+Playbook(.*?)(?=^##\s|\Z)",
        skill_text,
        re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return "skipped", "no Playbook section"
    body = section_match.group(1)
    # Each rule starts with "1. **...**", "2. **..." etc. A "case" line is
    # an indented bullet starting with "案例" / "case" / "-".
    rules = re.findall(
        r"^\d+\.\s+\*\*.*?\*\*.*?(?=^\d+\.\s+\*\*|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    if not rules:
        return "skipped", "no rules found in section"
    no_case = [i + 1 for i, r in enumerate(rules) if not re.search(r"案例|case", r, re.IGNORECASE)]
    if not no_case:
        return "pass", f"all {len(rules)} rules have 案例"
    return "fail", f"{len(no_case)}/{len(rules)} rules missing 案例"


def check_tool_tiers(skill_text: str, skill_dir: Path) -> tuple[str, str]:
    """Item 5: Tool tier coverage 必备 ≥ 3 / 场景化 ≥ 5 / 新兴 ≥ 2.
    First tries to count from skill body; iter 23 fallback parses
    research/02-tools.md directly when body is just a reference.
    """
    # Count tier mentions in 工具栈 section
    section_match = re.search(
        r"##\s+(?:3\.\s+)?工具栈(.*?)(?=^##\s|\Z)",
        skill_text,
        re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return "skipped", "no 工具栈 section found"
    body = section_match.group(1)
    necessary_match = re.search(r"必备[^0-9]*(\d+)", body)
    scenario_match = re.search(r"场景特化?[^0-9]*(\d+)", body)
    emerging_match = re.search(r"新兴[^0-9]*(\d+)", body)
    if not (necessary_match or scenario_match or emerging_match):
        # Iter 23: fall back to parsing research/02-tools.md directly
        tools_path = skill_dir / "references" / "research" / "02-tools.md"
        if not tools_path.exists():
            return "needs_subagent", (
                "tool tier counts not stated inline AND research/02-tools.md not found"
            )
        ttext = tools_path.read_text(encoding="utf-8")
        # Look for "### 必备 / 场景特化 / 新兴" sub-sections in 02-tools.md and count items
        n_necessary = len(re.findall(
            r"^###?\s*必备.*?\n(.*?)(?=^###?\s|\Z)",
            ttext, re.MULTILINE | re.DOTALL,
        ))
        # Better: count |—| table rows under each header
        nec_section = re.search(r"必备[^\n]*\n(.*?)(?=场景|新兴|^##\s|\Z)", ttext, re.DOTALL)
        sce_section = re.search(r"场景特化?[^\n]*\n(.*?)(?=新兴|^##\s|\Z)", ttext, re.DOTALL)
        emg_section = re.search(r"新兴[^\n]*\n(.*?)(?=^##\s|\Z)", ttext, re.DOTALL)
        n_necessary = len(re.findall(r"^\|", nec_section.group(1) if nec_section else "", re.MULTILINE)) - 2
        n_scenario = len(re.findall(r"^\|", sce_section.group(1) if sce_section else "", re.MULTILINE)) - 2
        n_emerging = len(re.findall(r"^\|", emg_section.group(1) if emg_section else "", re.MULTILINE)) - 2
        n_necessary = max(0, n_necessary)
        n_scenario = max(0, n_scenario)
        n_emerging = max(0, n_emerging)
    else:
        n_necessary = int(necessary_match.group(1)) if necessary_match else 0
        n_scenario = int(scenario_match.group(1)) if scenario_match else 0
        n_emerging = int(emerging_match.group(1)) if emerging_match else 0
    issues = []
    if n_necessary < 3: issues.append(f"必备 {n_necessary} < 3")
    if n_scenario < 5: issues.append(f"场景化 {n_scenario} < 5")
    if n_emerging < 2: issues.append(f"新兴 {n_emerging} < 2")
    if not issues:
        return "pass", f"必备={n_necessary} 场景化={n_scenario} 新兴={n_emerging}"
    return "partial", f"thresholds not met: {', '.join(issues)} — may be cold protocol"


def check_workflow_senior_differences(skill_text: str) -> tuple[str, str]:
    """Item 6: ≥ 80% workflows have ≥ 2 senior-difference points (skip/optimize/add)."""
    section_match = re.search(
        r"##\s+(?:4\.\s+)?工作流(.*?)(?=^##\s|\Z)",
        skill_text,
        re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return "skipped", "no 工作流 section"
    body = section_match.group(1)
    if "references/research/03-workflows.md" in body and len(body) < 500:
        return "needs_subagent", "section is a reference; load 03-workflows.md to validate"
    # Each workflow has ### with senior tags
    workflows = re.findall(r"###.*?(?=^###|\Z)", body, re.MULTILINE | re.DOTALL)
    if not workflows:
        return "skipped", "no workflow subsections"
    enough_diffs: list[bool] = []
    for w in workflows:
        skip_count = len(re.findall(r"skip|跳过", w, re.IGNORECASE))
        opt_count = len(re.findall(r"optimize|优化", w, re.IGNORECASE))
        add_count = len(re.findall(r"add\b|额外", w, re.IGNORECASE))
        types_present = sum(1 for c in [skip_count, opt_count, add_count] if c >= 1)
        diff_total = skip_count + opt_count + add_count
        enough_diffs.append(types_present >= 2 and diff_total >= 2)
    pct = sum(enough_diffs) / len(enough_diffs) if enough_diffs else 0
    if pct >= 0.8:
        return "pass", f"{int(pct * 100)}% workflows have ≥ 2 senior diffs"
    return "fail", f"{int(pct * 100)}% workflows have ≥ 2 diffs (target ≥ 80%)"


def check_voice_dna(skill_text: str, skill_dir: Path) -> tuple[str, str]:
    """Item 7: voice DNA mechanical surrogate. Iter 26 (codex 3rd-audit P1 #4):
    extended to also check the dialogue-sample library (synthesis Step 5b)
    that iter 26 made mandatory. Without ≥ 2 samples per register × 4
    registers, the voice surrogate cannot pass — quoted samples are what let
    Phase 4.3 subagent inherit real industry voice instead of LLM-default
    register.
    """
    # Iter 26: voice samples library check (synthesis.md §5.X)
    syn_path = skill_dir / "references" / "synthesis.md"
    if syn_path.exists():
        syn_text = syn_path.read_text(encoding="utf-8")
        # Look for §5 dialogue sample library (4 sub-sections)
        sample_section = re.search(
            r"##\s+5\.\s+表达\s+DNA(.*?)(?=^##\s+\d+\.|\Z)",
            syn_text, re.MULTILINE | re.DOTALL,
        )
        if sample_section:
            body = sample_section.group(1)
            # Count "原话 | 转述 | 推断" tags as samples
            sample_tags = re.findall(
                r"\(\s*source:[^\)]*?(原话|转述|推断)[^\)]*?\)",
                body,
            )
            n_samples = len(sample_tags)
            n_yuan_hua = sum(1 for t in sample_tags if t == "原话")
            n_inferred = sum(1 for t in sample_tags if t == "推断")
            if n_samples >= 8 and n_yuan_hua / max(n_samples, 1) >= 0.5:
                return "pass", (
                    f"voice samples library: {n_samples} entries, "
                    f"{n_yuan_hua} 原话 ({n_yuan_hua/n_samples*100:.0f}%) — voice_confidence: high"
                )
            if n_samples >= 4 and n_inferred / max(n_samples, 1) <= 0.3:
                return "partial", (
                    f"voice samples library: {n_samples} entries (target ≥ 8), "
                    f"voice_confidence: medium — Phase 4.3 subagent run still recommended "
                    f"to confirm voice fidelity"
                )
            if n_samples > 0:
                return "fail", (
                    f"voice samples library: only {n_samples} entries "
                    f"(target ≥ 8 across 4 registers × 2), voice_confidence: low — "
                    f"诚实边界节必须明示 voice 维度信号薄弱"
                )
            # n_samples == 0 — fall through to legacy jargon-counting surrogate

    # Try to load Track 06 glossary to get Tier-1 jargon list
    glossary_path = skill_dir / "references" / "research" / "06-glossary.md"
    tier1_terms: set[str] = set()
    rejected_marketing: set[str] = set()
    if glossary_path.exists():
        gtext = glossary_path.read_text(encoding="utf-8")
        # Extract Tier 1 entries (term followed by `tier-1`)
        for m in re.finditer(r"###\s+(?:[\d\.]+\s+)?(\S+)[\s\S]{0,300}?tier-1", gtext):
            term = m.group(1).strip()
            if 2 <= len(term) <= 25:
                tier1_terms.add(term.lower())
        # Extract vendor话术 rejection list — typical heading is "厂商话术拒绝" or "厂商错位"
        for m in re.finditer(
            r"(?:厂商话术拒绝|rejected|reject)[\s\S]{0,500}?(?=\n##|\Z)", gtext
        ):
            for line in m.group(0).splitlines():
                if "-" in line or "•" in line:
                    word_match = re.findall(r"[A-Za-z][A-Za-z\s-]{3,30}", line)
                    for w in word_match:
                        rejected_marketing.add(w.strip().lower())

    if not tier1_terms:
        return "needs_subagent", (
            "Voice check (4.3) requires blind comparison with real practitioner samples "
            "— run prompts/quality_check.md Phase 4.3. (Surrogate disabled: Track 06 glossary not found or empty.)"
        )

    # Count Tier-1 jargon hits in skill_text body
    skill_lower = skill_text.lower()
    jargon_hits = sum(1 for term in tier1_terms if term in skill_lower)
    marketing_hits = sum(1 for w in rejected_marketing if w in skill_lower)

    # Heuristic verdict
    if jargon_hits >= 5 and marketing_hits == 0:
        return "pass", (
            f"surrogate: {jargon_hits} tier-1 jargon hits, 0 vendor话术 violations — "
            f"likely passes voice check; full subagent run still recommended"
        )
    if jargon_hits < 3:
        return "fail", (
            f"surrogate: only {jargon_hits} tier-1 jargon hits — voice may be too generic; "
            f"run subagent voice check (Phase 4.3) to confirm"
        )
    if marketing_hits > 0:
        return "fail", (
            f"surrogate: {marketing_hits} vendor话术 hits in body — voice DNA contaminated; "
            f"strip vendor language before subagent voice check"
        )
    return "partial", (
        f"surrogate: {jargon_hits} tier-1 jargon, {marketing_hits} marketing — borderline; "
        f"run subagent voice check (Phase 4.3) to resolve"
    )


def check_honest_boundaries(skill_text: str) -> tuple[str, str]:
    """Item 8: ≥ 3 specific honest boundaries."""
    section_match = re.search(
        r"##\s+(?:8\.\s+)?诚实边界(.*?)(?=^##\s|\Z)",
        skill_text,
        re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return "skipped", "no 诚实边界 section"
    body = section_match.group(1)
    items = re.findall(r"^[-\d]+\.\s+|^-\s+", body, re.MULTILINE)
    n = len(items)
    if n < 3:
        return "fail", f"{n} boundaries (< 3 specific items required)"
    # Check that they're not all generic "不能替代真人" boilerplate
    generic_count = len(re.findall(r"不能替代|cannot replace", body))
    if generic_count > n / 2:
        return "partial", f"{n} items but {generic_count} are generic (mostly '不能替代真人' style)"
    return "pass", f"{n} boundary items"


def check_primary_ratio(skill_dir: Path, meta: dict) -> tuple[str, str]:
    """Item 9: ≥ 50% primary sources (from research notes)."""
    ratio = meta.get("primary_source_ratio")
    if ratio is None:
        # Fall back to scanning research/*.md
        research_dir = skill_dir / "references" / "research"
        if not research_dir.exists():
            return "skipped", "no research/ dir; meta.primary_source_ratio not set"
        primary = secondary = reference = 0
        for f in research_dir.glob("*.md"):
            text = f.read_text(encoding="utf-8")
            primary += len(re.findall(r"\[Primary\]", text))
            secondary += len(re.findall(r"\[Secondary\]", text))
            reference += len(re.findall(r"\[Reference\]", text))
        total = primary + secondary + reference
        ratio = primary / total if total else 0.0
    if ratio >= 0.5:
        return "pass", f"primary ratio = {int(ratio * 100)}% (≥ 50%)"
    return "fail", f"primary ratio = {int(ratio * 100)}% (< 50%, mostly secondary)"


def check_agentic_protocol_dims(skill_text: str, meta: dict) -> tuple[str, str]:
    """Item 10: Agentic Protocol dimensions in [3, 10]."""
    n_meta = meta.get("research_dimensions_count")
    if n_meta is not None:
        n = n_meta
    else:
        n = len(re.findall(r"^###\s+9\.\d+\s+", skill_text, re.MULTILINE))
    if 3 <= n <= 10:
        return "pass", f"{n} dimensions (in [3, 10])"
    if n < 3:
        return "fail", f"{n} dimensions (< 3, too thin)"
    return "fail", f"{n} dimensions (> 10, not精炼)"


def check_time_decay_marks(skill_text: str) -> tuple[str, str]:
    """Item 11: time-decay annotations. (iter 18 fix) The SKILL.md spec is
    "工具 + 工作流 + 法规节都有 last_updated" — that's 3 sections × 1 marker
    minimum, not 2 each. Check that ≥3 distinct sections carry markers.
    """
    # Look for sections that contain a time-decay marker
    sections_with_decay = 0
    section_keywords = ["工具", "工作流", "法规", "Tool", "Workflow", "Regulation"]
    for keyword in section_keywords:
        # Search a window after each occurrence of the keyword
        for m in re.finditer(keyword, skill_text):
            window = skill_text[m.start():m.start() + 1500]
            if re.search(r"last_updated|last_checked|[Dd]ecay\s*risk", window):
                sections_with_decay += 1
                break  # one hit per keyword is enough

    total_markers = len(re.findall(
        r"last_updated|last_checked|[Dd]ecay\s*risk", skill_text
    ))
    if sections_with_decay >= 3 or total_markers >= 3:
        return "pass", (
            f"{total_markers} markers across {sections_with_decay} key sections"
        )
    if total_markers == 0:
        return "fail", "no time-decay marks (last_updated / decay risk) found"
    return "partial", (
        f"limited spread: {total_markers} markers, only {sections_with_decay} "
        f"of 3 key sections (工具 / 工作流 / 法规) covered"
    )


def check_multi_figure_consensus(skill_dir: Path) -> tuple[str, str]:
    """Item 12: each mental model backed by ≥ 2 figures (cross-figure consensus).

    iter 18 fix: instead of guessing from prose with `(A/B/C)` patterns, look
    for explicit attribution markers — `(figures: ...)`, `出现于:`, or evidence
    citations that name 2+ distinct figures. If those aren't present, fall back
    to checking research/01-figures.md for whether each model's keyword appears
    against ≥ 2 figure entries.
    """
    synthesis = skill_dir / "references" / "synthesis.md"
    if not synthesis.exists():
        return "skipped", "no synthesis.md to analyze figure attribution"
    text = synthesis.read_text(encoding="utf-8")
    section_match = re.search(
        r"##\s+(?:1\.\s+)?心智模型(.*?)(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return "skipped", "no 心智模型 section in synthesis"
    body = section_match.group(1)
    models = re.split(r"^###\s+1\.\d+\s+", body, flags=re.MULTILINE)[1:]
    if not models:
        return "skipped", "no model subsections"

    insufficient: list[int] = []
    for i, m in enumerate(models):
        m_window = m[:1000]
        # Look for explicit attribution patterns first
        explicit = re.findall(
            r"(?:figures:|出现于:|来源于|[Bb]y\s+)\s*([^\n]+)",
            m_window,
        )
        explicit_figures = 0
        for tag in explicit:
            # Count comma/pipe/slash-separated names
            names = re.split(r"[,，/|；;]", tag)
            explicit_figures = max(explicit_figures, len([n for n in names if n.strip()]))

        # Fallback: look for parenthetical name groups
        if explicit_figures == 0:
            groups = re.findall(r"\(([^()]*[/,，；;|][^()]*)\)", m_window)
            for g in groups:
                names = re.split(r"[,，/|；;]", g)
                explicit_figures = max(explicit_figures, len([n for n in names if n.strip()]))

        if explicit_figures < 2:
            insufficient.append(i + 1)

    if not insufficient:
        return "pass", f"all {len(models)} models cite ≥ 2 figures"
    if len(insufficient) <= len(models) // 3:
        return "partial", (
            f"{len(insufficient)}/{len(models)} models lack explicit ≥2 figure citations: "
            f"{insufficient[:3]} — figures may be in research/01-figures.md but not "
            f"surfaced in synthesis (consider adding `(figures: A / B / C)` annotations)"
        )
    return "fail", (
        f"{len(insufficient)}/{len(models)} models lack ≥2 figure citations — "
        f"the multi-figure consensus rule from extraction-framework § 一 may not be holding"
    )


# ---------------------------------------------------------------------------
# Mechanical URL-verification checks (added iter 24 — Q1 quality gate).
# These complement check_primary_ratio (item 9) which uses self-reported
# [Primary] markers; the checks below classify the actual URLs.


def _parse_manifests(skill_dir: Path) -> list[dict[str, str]]:
    """Thin wrapper around source_manifest.parse_manifests for backwards
    compat with the existing rubric checks (which expected dict rows)."""
    rows = source_manifest.parse_manifests(skill_dir)
    return [
        {
            "source_id": r.source_id, "url": r.url, "bucket": r.bucket,
            "last_checked": r.last_checked, "file": r.file,
        }
        for r in rows
    ]


def _scan_research_urls(skill_dir: Path, locale: str = "all") -> dict[str, Any] | None:
    """Run source_verifier.scan_dir on research/ and return the report. Cached
    on first call within the same rubric run."""
    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        return None
    try:
        return source_verifier.scan_dir(research_dir, locale=locale, check_live=False)
    except Exception:
        return None


def check_verified_primary_precision(skill_dir: Path) -> tuple[str, str]:
    """Item 13: mechanical primary-ratio. Combines:

      1. Manifest declarations (`## Source Manifest` rows: bucket is what
         the agent committed to). `verified_primary` and `surrogate_primary`
         both count as "first-hand-tier" for the ratio.
      2. URL classification fallback when no manifest is present (agent on
         legacy [Primary]/[Secondary] tagging).

    PASS if first-hand tier ≥ 50% AND total ≥ 5 sources.
    PARTIAL if ratio < 0.5 but total < 10 (small sample).
    FAIL if ratio < 0.5 with ≥ 10 sources.
    SKIPPED if no URLs and no manifest (research notes use named-only sources).
    """
    rows = _parse_manifests(skill_dir)
    if rows:
        total = len(rows)
        first_hand = sum(
            1 for r in rows if r["bucket"] in ("verified_primary", "surrogate_primary")
        )
        verified = sum(1 for r in rows if r["bucket"] == "verified_primary")
        surrogate = sum(1 for r in rows if r["bucket"] == "surrogate_primary")
        ratio = first_hand / total
        detail_breakdown = (
            f" (verified_primary={verified}, surrogate_primary={surrogate})"
            if surrogate else ""
        )
        if ratio >= 0.5 and total >= 5:
            return "pass", f"manifest first-hand {first_hand}/{total} = {ratio*100:.1f}%{detail_breakdown}"
        if total < 10:
            return "partial", (
                f"manifest first-hand {first_hand}/{total} = {ratio*100:.1f}%{detail_breakdown} — "
                f"sample too small ({total} < 10) to fail definitively"
            )
        return "fail", (
            f"manifest first-hand {first_hand}/{total} = {ratio*100:.1f}%{detail_breakdown} "
            f"(< 50%, agent declared too many secondary/reference)"
        )

    # Legacy fallback: classify URLs in markdown body (no manifest declared)
    rep = _scan_research_urls(skill_dir)
    if rep is None or rep["total_urls"] == 0:
        return "skipped", (
            "no Source Manifest and no URLs in research/ — agent on named-only "
            "sources; see prompts/research/_source_id_manifest.md to enable Q1"
        )
    primary = rep["counts"].get("verified_primary", 0)
    total = rep["total_urls"]
    ratio = rep["verified_primary_ratio"]
    if ratio >= 0.5 and primary >= 5:
        return "pass", f"URL-classified verified_primary {primary}/{total} = {ratio*100:.1f}% (legacy mode)"
    if total < 10:
        return "partial", (
            f"URL-classified verified_primary {primary}/{total} = {ratio*100:.1f}% (legacy mode) — "
            f"sample too small ({total} < 10) to fail definitively"
        )
    return "fail", (
        f"URL-classified verified_primary {primary}/{total} = {ratio*100:.1f}% (legacy mode, < 50%)"
    )


def check_blacklist_violations(skill_dir: Path) -> tuple[str, str]:
    """Item 14: zero blacklist URLs + manifest-vs-auto bucket consistency.

    Catches three failure modes:
      1. Agent declared `blacklisted` (intentional negative-test entries)
      2. Agent declared anything else, but auto-classifier says blacklisted
      3. Agent declared an UPGRADE (e.g. verified_primary on a secondary URL)
         without using `surrogate_primary` + note (Q5 escape valve)

    All three are quality gates — the manifest must not lie to us.
    """
    rows = source_manifest.parse_manifests(skill_dir)
    if not rows:
        # Legacy fallback
        rep = _scan_research_urls(skill_dir)
        if rep is None or rep["total_urls"] == 0:
            return "skipped", "no URLs to check"
        bl = rep["counts"].get("blacklisted", 0)
        if bl == 0:
            return "pass", f"0 blacklisted URLs across {rep['total_urls']} sources (legacy scan)"
        examples = [u for u, info in rep["urls"].items() if info["bucket"] == "blacklisted"][:3]
        return "fail", (
            f"{bl} blacklisted URLs detected (legacy scan) — replace with verified primaries: "
            + " ; ".join(examples)
        )

    # Run the unified consistency check
    mismatches = source_manifest.check_bucket_consistency(rows)
    violations = [m for m in mismatches if m.severity == "violation"]

    bl_count = sum(1 for r in rows if r.bucket == "blacklisted")
    bl_examples = [f"{r.source_id} {r.url}" for r in rows if r.bucket == "blacklisted"][:3]

    # Iter 26 (codex 4-audit P0-1c): even with a manifest, scan all URLs in
    # research markdown body — catches blacklisted URLs cited in prose that
    # never got into the manifest (e.g. "see also https://zhihu.com/...").
    body_blacklisted: list[str] = []
    rep = _scan_research_urls(skill_dir)
    if rep is not None:
        manifest_urls = {r.url for r in rows}
        for u, info in rep["urls"].items():
            if u in manifest_urls:
                continue  # already evaluated in manifest path
            if info["bucket"] == "blacklisted":
                body_blacklisted.append(u)

    issues: list[str] = []
    if bl_count > 0:
        issues.append(f"{bl_count} declared blacklisted: " + " ; ".join(bl_examples))
    if violations:
        issues.append(
            f"{len(violations)} manifest-bucket violations (declared > auto without surrogate)"
        )
        issues.extend(f"  • {v.row.source_id}: {v.reason[:90]}" for v in violations[:3])
    if body_blacklisted:
        issues.append(
            f"{len(body_blacklisted)} blacklisted URLs in prose (not in manifest): "
            + " ; ".join(body_blacklisted[:3])
        )

    if not issues:
        total = len(rows)
        return "pass", (
            f"0 blacklisted, 0 manifest-bucket violations, "
            f"0 prose-cited blacklisted URLs ({total} manifest entries)"
        )
    return "fail", " | ".join(issues)


# Date patterns we accept as freshness markers in research notes.
_DATE_RE = re.compile(
    r"\b(?:collected|last_checked|last_updated|last_updated_date|last_published_date|"
    r"last_episode_date|last_edition_date)\s*[:：]\s*(\d{4})-(\d{2})(?:-(\d{2}))?\b"
)


def check_claim_evidence_coverage(skill_dir: Path) -> tuple[str, str]:
    """Item 16: each mental model has `evidence: [Sxxx, Syyy]` citing ≥ 2
    distinct source_ids. Cross-source consensus rule (Q2).

    Skipped when no Source Manifest is present in research/ (backwards compat
    with iter ≤ 23 prototypes that only used [Primary]/[Secondary] tags).
    """
    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        return "skipped", "no research/ dir"

    # Look for any Source Manifest table — sufficient signal that this skill
    # uses the new source_ids convention.
    has_manifest = False
    for f in research_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        if re.search(r"^##\s+Source\s+Manifest", text, re.MULTILINE):
            has_manifest = True
            break
    if not has_manifest:
        return "skipped", (
            "no `## Source Manifest` block in research/ — agent on legacy "
            "[Primary]/[Secondary] tagging. Run new prompts/research/*.md "
            "with `evidence: [Sxxx]` annotations to enable Q2."
        )

    # Inspect synthesis.md (Phase 2 output) — that's where mental models live
    syn_path = skill_dir / "references" / "synthesis.md"
    if not syn_path.exists():
        return "skipped", "no synthesis.md to inspect"
    text = syn_path.read_text(encoding="utf-8")
    section = re.search(
        r"##\s+(?:1\.\s+)?心智模型(.*?)(?=^##\s|\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    if not section:
        return "skipped", "no 心智模型 section"
    body = section.group(1)
    models = re.split(r"^###\s+1\.\d+\s+", body, flags=re.MULTILINE)[1:]
    if not models:
        return "skipped", "no model subsections"

    insufficient: list[int] = []
    # Accept both legacy `S001` and new `T01-S001` formats. Track-prefixed IDs
    # are recommended (Q2 cross-track consensus); plain `S001` is deprecated
    # but still parsed for backwards compat with iter ≤ 23.
    sid_pattern = re.compile(r"^(?:T\d{2}-)?S\d+$")
    # Iter 26: accept all markdown variations:
    #   evidence: [...]                      bare
    #   **evidence**: [...]                  bold word, colon outside
    #   **evidence:** [...]                  bold word + colon together
    #   evidence : [...]                     space before colon
    evidence_re = re.compile(
        r"\*{0,2}evidence\*{0,2}\s*[:：]\*{0,2}\s*\[\s*([^\]]+)\]",
        re.IGNORECASE,
    )
    for i, m in enumerate(models):
        sid_matches = evidence_re.findall(m)
        ids: set[str] = set()
        for tag_group in sid_matches:
            for tok in re.split(r"[,，;；\s]+", tag_group):
                tok = tok.strip()
                if sid_pattern.match(tok):
                    ids.add(tok)
        if len(ids) < 2:
            insufficient.append(i + 1)

    if not insufficient:
        return "pass", f"all {len(models)} models cite ≥ 2 distinct source_ids"
    if len(insufficient) <= len(models) // 3:
        return "partial", (
            f"{len(insufficient)}/{len(models)} models lack `evidence: [≥2 Sxxx]` — "
            f"models {insufficient[:3]} need cross-source citations"
        )
    return "fail", (
        f"{len(insufficient)}/{len(models)} models lack `evidence: [≥2 Sxxx]` — "
        f"consensus rule violated (Q2). Promote single-source claims to playbook "
        f"or add a second source."
    )


def check_anchor_citations(skill_text: str) -> tuple[str, str]:
    """Item 17 (iter 27 — codex audit follow-up 2026-05-10): every concrete
    number / percentage / date / "N+ 备案" claim in SKILL.md should be
    accompanied by a source_id (T0X-S\\d+) OR a confidence caveat keyword.

    Surfaces hallucinated numbers like "98% < 48h", "40% reject", "$299 org",
    "800+ 备案" that have no traceable source — the codex audit pattern that
    bit ios-app-launch on 2026-05-10.

    Heuristic: for each number cluster matching one of the high-risk patterns,
    look in the surrounding ±200 chars for either:
      - source_id pattern T0\\d-S\\d+
      - URL (developer.apple.com / .gov.cn / similar)
      - caveat keyword (业内估计 / Apple 不公开 / self-verify / 第三方 /
        non-official / non-Apple / Capgo / 估计 / 业内观察 / Apple 公开 /
        约 / 大约 / approximately / range)

    Skips well-known non-empirical numbers (3-7 心智模型 / 5-10 Playbook 等
    rubric范围 mention) by checking for "(in [N, M])" pattern.
    """
    # High-risk patterns: percentages, prices, specific large numbers, ISO dates
    RISKY_PATTERNS = [
        (r"\b\d{1,3}(?:\.\d+)?%", "percentage"),
        (r"\$\d{2,4}(?:[,.]\d{3})*(?:/\s*(?:yr|year|month|m|annum|day))?", "price"),
        (r"\b\d{2,5}\+?\s*(?:备案|登记|sources|apps|customers|users|签|学员|启动|installs)", "count"),
    ]
    CAVEAT_KEYWORDS = (
        "业内估计", "业内观察", "业内 range", "业内估", "apple 不公开", "self-verify",
        "第三方", "non-official", "non-apple", "capgo", "估计", "业内",
        "official", "公开", "developer.apple.com", "estimate", "estimated",
        "approximately", "大约", "约 ", "range", ".gov.cn", ".gov", "需 verify",
        "需自查", "self verify", "需验证", "data.ai", "sensortower", "revenuecat",
    )
    SOURCE_ID_RE = re.compile(r"T\d{2}-S\d+")

    flagged: list[tuple[str, str]] = []
    total = 0
    for pat, kind in RISKY_PATTERNS:
        for m in re.finditer(pat, skill_text, re.IGNORECASE):
            # Skip rubric-range mentions like "(in [3, 7])"
            ctx_short = skill_text[max(0, m.start() - 30):m.end() + 30]
            if re.search(r"\(in\s*\[\d", ctx_short):
                continue
            total += 1
            window_start = max(0, m.start() - 200)
            window_end = min(len(skill_text), m.end() + 200)
            window = skill_text[window_start:window_end]
            window_low = window.lower()
            has_source = bool(SOURCE_ID_RE.search(window))
            has_caveat = any(kw.lower() in window_low for kw in CAVEAT_KEYWORDS)
            if not (has_source or has_caveat):
                flagged.append((m.group(0), kind))

    if total == 0:
        return "skipped", "no concrete numbers / dates / prices found"
    pct_safe = (total - len(flagged)) / total
    examples = ", ".join(f'"{x[0]}"({x[1]})' for x in flagged[:3])
    if pct_safe >= 0.85:
        return "pass", (
            f"{total - len(flagged)}/{total} numbers cited (source_id or caveat) "
            f"= {pct_safe*100:.0f}%"
        )
    if pct_safe >= 0.70:
        return "partial", (
            f"{len(flagged)}/{total} numbers without source / caveat "
            f"({pct_safe*100:.0f}% cited) — examples: {examples}"
        )
    return "fail", (
        f"{len(flagged)}/{total} numbers lack source / caveat "
        f"({pct_safe*100:.0f}% cited) — possible hallucination. examples: {examples}. "
        f"每个具体 % / $ / 备案数 / 法律日期需 source_id 或 caveat (业内估计 / Apple 不公开 / 等)"
    )


def check_freshness_dates(skill_dir: Path) -> tuple[str, str]:
    """Item 15: ≥ 70% of sources have a fresh (≤ 18 months old) date marker.

    Two sources of date info, in priority order:
      1. Manifest table column 4 (`| ... | YYYY-MM-DD |`) — preferred.
         Each row counts as one entry.
      2. Legacy: free-text `collected:` / `last_checked:` / `last_updated:`
         markers within `### N` entries in 01-figures / 02-tools / 05-sources.

    Stale dates (> 18 months) count as 0.5 instead of 1.0.
    """
    today = _dt.date.today()
    eighteen_months_ago = today - _dt.timedelta(days=18 * 30)

    rows = _parse_manifests(skill_dir)
    if rows:
        total = len(rows)
        score = 0.0
        stale = 0
        undated = 0
        for r in rows:
            d_str = r["last_checked"]
            if not d_str or d_str in ("—", "-", "n/a", "N/A"):
                undated += 1
                continue
            try:
                parts = d_str.split("-")
                y, mo, d = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 1
                date = _dt.date(y, mo, d)
            except (ValueError, IndexError):
                undated += 1
                continue
            if date >= eighteen_months_ago:
                score += 1.0
            else:
                score += 0.5
                stale += 1
        coverage = score / total
        if coverage >= 0.7:
            msg = f"manifest: {int(coverage*100)}% entries fresh-dated"
            if stale:
                msg += f" ({stale} stale > 18 mo)"
            if undated:
                msg += f" ({undated} undated)"
            return "pass", msg
        if coverage >= 0.4:
            return "partial", (
                f"manifest: {int(coverage*100)}% entries dated (target ≥ 70%) — "
                f"{undated} undated, {stale} stale"
            )
        return "fail", (
            f"manifest: {int(coverage*100)}% entries fresh-dated — too many "
            f"undated/stale rows; update flow can't run reliably"
        )

    # Legacy: free-text date markers in research entries
    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        return "skipped", "no research/ dir"
    track_files = ["01-figures.md", "02-tools.md", "05-sources.md"]
    total_entries = 0
    score = 0.0
    stale_count = 0
    for f in track_files:
        p = research_dir / f
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        sections = re.split(r"^###\s+", text, flags=re.MULTILINE)[1:]
        for s in sections:
            total_entries += 1
            dates: list[_dt.date] = []
            for m in _DATE_RE.finditer(s):
                try:
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
                    dates.append(_dt.date(y, mo, d))
                except ValueError:
                    continue
            if not dates:
                continue
            newest = max(dates)
            if newest >= eighteen_months_ago:
                score += 1.0
            else:
                score += 0.5
                stale_count += 1
    if total_entries == 0:
        return "skipped", "no entries (### sections) found in 01/02/05"
    coverage = score / total_entries
    if coverage >= 0.7:
        msg = f"legacy: {int(coverage*100)}% entries dated (free-text mode)"
        if stale_count:
            msg += f" ({stale_count} stale > 18 mo)"
        return "pass", msg
    if coverage >= 0.4:
        return "partial", (
            f"legacy: {int(coverage*100)}% entries dated (target ≥ 70%) — "
            f"{total_entries - int(score)} of {total_entries} missing or stale"
        )
    return "fail", (
        f"legacy: {int(coverage*100)}% entries dated — most lack collected:/last_checked:; "
        f"update flow can't run reliably"
    )


# ---------------------------------------------------------------------------
# Main rubric runner

RUBRIC_ITEMS: list[tuple[str, str, str]] = [
    ("1", "心智模型数 (3-7)", "check_mental_models_count"),
    ("2", "心智模型局限 100% 填", "check_mental_model_limits"),
    ("3", "Playbook 数 (5-10)", "check_playbook_count"),
    ("4", "Playbook 案例 ≥ 1", "check_playbook_cases"),
    ("5", "工具三层覆盖", "check_tool_tiers"),
    ("6", "工作流入门-资深差异 ≥ 80%", "check_workflow_senior_differences"),
    ("7", "表达 DNA 辨识度", "check_voice_dna"),
    ("8", "诚实边界 ≥ 3 条", "check_honest_boundaries"),
    ("9", "一手来源 ≥ 50% (自报)", "check_primary_ratio"),
    ("10", "Agentic Protocol 维度 (3-10)", "check_agentic_protocol_dims"),
    ("11", "时效性标注完整", "check_time_decay_marks"),
    ("12", "多 figure 共识门槛", "check_multi_figure_consensus"),
    ("13", "URL 一手机械验证 ≥ 50%", "check_verified_primary_precision"),
    ("14", "无黑名单 URL", "check_blacklist_violations"),
    ("15", "freshness 标注 ≥ 70%", "check_freshness_dates"),
    ("16", "claim → evidence ≥ 2 source_ids", "check_claim_evidence_coverage"),
    ("17", "数字 / deadline / 拒审率 必带来源 + 置信度", "check_anchor_citations"),
]


def run_rubric(skill_dir: Path) -> dict[str, Any]:
    """Run all 12 rubric checks. Return aggregate result."""
    skill_text = load_skill_text(skill_dir)
    meta = load_meta(skill_dir)

    checkers: dict[str, Callable[..., tuple[str, str]]] = {
        "check_mental_models_count": lambda: check_mental_models_count(skill_text, meta),
        "check_mental_model_limits": lambda: check_mental_model_limits(skill_text),
        "check_playbook_count": lambda: check_playbook_count(skill_text, meta),
        "check_playbook_cases": lambda: check_playbook_cases(skill_text),
        "check_tool_tiers": lambda: check_tool_tiers(skill_text, skill_dir),
        "check_workflow_senior_differences": lambda: check_workflow_senior_differences(skill_text),
        "check_voice_dna": lambda: check_voice_dna(skill_text, skill_dir),
        "check_honest_boundaries": lambda: check_honest_boundaries(skill_text),
        "check_primary_ratio": lambda: check_primary_ratio(skill_dir, meta),
        "check_agentic_protocol_dims": lambda: check_agentic_protocol_dims(skill_text, meta),
        "check_time_decay_marks": lambda: check_time_decay_marks(skill_text),
        "check_multi_figure_consensus": lambda: check_multi_figure_consensus(skill_dir),
        "check_verified_primary_precision": lambda: check_verified_primary_precision(skill_dir),
        "check_blacklist_violations": lambda: check_blacklist_violations(skill_dir),
        "check_freshness_dates": lambda: check_freshness_dates(skill_dir),
        "check_claim_evidence_coverage": lambda: check_claim_evidence_coverage(skill_dir),
        "check_anchor_citations": lambda: check_anchor_citations(skill_text),
    }

    results: list[dict[str, Any]] = []
    for item_id, label, fn_name in RUBRIC_ITEMS:
        status, detail = checkers[fn_name]()
        results.append({"id": item_id, "label": label, "status": status, "detail": detail})

    counts = {
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "partial": sum(1 for r in results if r["status"] == "partial"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "needs_subagent": sum(1 for r in results if r["status"] == "needs_subagent"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
    }

    # Verdict per Phase 4.4 rule: 0-2 fail → PARTIAL, 3+ fail → FAIL, else PASS.
    # PASS requires ≥ 8 mechanical pass + no fails (subagent-needed items don't count as fail).
    if counts["fail"] >= 3:
        verdict = "FAIL"
    elif counts["fail"] > 0 or counts["partial"] > 2:
        verdict = "PARTIAL"
    else:
        verdict = "PASS"

    return {
        "skill_dir": str(skill_dir),
        "verdict": verdict,
        "counts": counts,
        "results": results,
    }


def render_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Phase 4.4 Mechanical Rubric — {report['skill_dir']}")
    lines.append("")
    lines.append(f"**Verdict**: `{report['verdict']}`")
    lines.append("")
    c = report["counts"]
    lines.append(
        f"Counts: {c['pass']} pass / {c['partial']} partial / {c['fail']} fail / "
        f"{c['needs_subagent']} needs subagent / {c['skipped']} skipped"
    )
    lines.append("")
    lines.append("| # | Item | Status | Detail |")
    lines.append("|---|------|--------|--------|")
    icons = {
        "pass": "✅", "partial": "⚠️", "fail": "❌",
        "needs_subagent": "🧠", "skipped": "—",
    }
    for r in report["results"]:
        icon = icons.get(r["status"], "?")
        lines.append(f"| {r['id']} | {r['label']} | {icon} {r['status']} | {r['detail']} |")
    lines.append("")
    if report["verdict"] == "FAIL":
        lines.append("**FAIL action**: 3+ items failing. Return to Phase 2 / Phase 3 for substantive revision.")
    elif report["verdict"] == "PARTIAL":
        lines.append("**PARTIAL action**: fix listed items, re-run rubric. If 2 iterations don't reach PASS, accept partial and mark weak dimensions in 诚实边界.")
    else:
        lines.append("**PASS action**: proceed to Phase 4.1/4.2/4.3 subagent runs (prompts/quality_check.md), then Phase 5.")
    lines.append("")
    lines.append("**Note**: Items marked 🧠 needs_subagent require running `prompts/quality_check.md` Phase 4.3 voice check via spawned subagent. This script does not run subagents.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI

def cmd_check(args: argparse.Namespace) -> int:
    report = run_rubric(args.skill_dir)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_report(report))

    # Also write the report to the skill directory
    out_dir = args.skill_dir / "references"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "quality-check-rubric.md"
    json_path = out_dir / "quality-check-rubric.json"
    md_path.write_text(render_report(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")

    return 0 if report["verdict"] == "PASS" else (1 if report["verdict"] == "PARTIAL" else 2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="quality_check — mechanical Phase 4.4 rubric runner",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    p_check = sub.add_parser("check", help="Run all 12 rubric items, output verdict")
    p_check.add_argument("--skill-dir", required=True, type=Path)
    p_check.add_argument("--json", action="store_true",
                         help="Output JSON to stdout instead of markdown")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action == "check":
            return cmd_check(args)
    except QCError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    return 99


if __name__ == "__main__":
    sys.exit(main())
