#!/usr/bin/env python3
"""merge_research.py — aggregate 6 research/*.md files into a Phase 1.5 review summary.

Usage:
  python3 merge_research.py merge --skill-dir <path>          # writes synthesis-summary.md + .json
  python3 merge_research.py show --skill-dir <path>           # prints the review table

Reads `{skill-dir}/references/research/01-figures.md` through `06-glossary.md`,
counts primary/secondary sources, extracts each track's "Phase 2 提炼提示" block,
and produces a structured summary for the user to review at SKILL.md Phase 1.5 checkpoint.

Pure stdlib. No pip install. macOS python3 out-of-the-box.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Tracks expected in references/research/. The order matters — used in the
# rendered summary table.
TRACKS = [
    ("01-figures", "Figures"),
    ("02-tools", "Tools"),
    ("03-workflows", "Workflows"),
    ("04-canon", "Canon"),
    ("05-sources", "Sources"),
    ("06-glossary", "Glossary"),
]

# Cold-signal thresholds per track (from each track's own quality self-check).
# Iter 23: these are baselines for technical industries. Real cold-industry
# detection uses item count + adaptive expectation per industry type. See
# adaptive_floor() below.
COLD_THRESHOLDS_DEFAULT = {
    "01-figures": 10,
    "02-tools": 15,
    "03-workflows": 3,
    "04-canon": 15,
    "05-sources": 10,
    "06-glossary": 25,
}

# Industry-type multipliers applied to default floors. From extraction-framework
# § 一's industry-type-aware candidate floors. Applied when intake.json's
# `industry_type` field is set; otherwise default to "technical".
INDUSTRY_TYPE_MULTIPLIERS = {
    "technical": 1.0,
    "academic": 0.8,
    "vertical_operational": 0.5,
    "regulated_specialized": 0.3,
}


def adaptive_floor(track_key: str, industry_type: str = "technical") -> int:
    """Iter 23 fix: adapt cold floor to industry type."""
    base = COLD_THRESHOLDS_DEFAULT.get(track_key, 5)
    mult = INDUSTRY_TYPE_MULTIPLIERS.get(industry_type, 1.0)
    return max(2, int(base * mult))


# ---------------------------------------------------------------------------

class MergeError(Exception):
    pass


def detect_cross_track_contradictions(tracks: dict[str, Any]) -> list[str]:
    """Iter 23 fix: scan tracks' Phase 2 interface blocks for likely
    cross-track contradictions. Heuristic — looks for a term mentioned as
    important in one track but explicitly contradicted/missing in another.
    Returns a list of human-readable contradiction descriptions for Phase 1.5
    user review. Empty list = no signals found (does not mean no contradictions
    exist; this is a low-recall, high-signal heuristic).
    """
    contradictions: list[str] = []

    # Aggregate keywords from each track's Phase 2 interface.
    # Preserve original case so the uppercase heuristic below can identify
    # tool / proper-noun candidates (codex P2 fix). Compare set membership
    # case-insensitively to avoid double-counting "AutoGen" vs "autogen".
    track_keywords_raw: dict[str, set[str]] = {}
    track_keywords_lower: dict[str, set[str]] = {}
    for track_key, t in tracks.items():
        if t.get("missing"):
            continue
        text = t.get("phase2_interface") or ""
        words = re.findall(r"[\w一-鿿-]{3,}", text)
        raw = set(w for w in words if len(w) >= 4)
        track_keywords_raw[track_key] = raw
        track_keywords_lower[track_key] = set(w.lower() for w in raw)

    # Compare track 01 (figures) vs track 02 (tools): if a tool name is
    # mentioned in tools as 必备 but absent from any figure's discussion, flag
    if "01-figures" in track_keywords_lower and "02-tools" in track_keywords_lower:
        only_in_tools_lower = (
            track_keywords_lower["02-tools"] - track_keywords_lower["01-figures"]
        )
        only_in_tools_raw = {
            w for w in track_keywords_raw["02-tools"] if w.lower() in only_in_tools_lower
        }
        # Filter to items that look like tool names (not regular english words)
        notable = [w for w in only_in_tools_raw
                   if any(c.isupper() for c in w) and len(w) > 5]
        if len(notable) >= 5:
            contradictions.append(
                f"Track 02 (tools) mentions {len(notable)} items not surfaced in "
                f"Track 01 (figures) discussion — heuristic suggests tool-figures "
                f"signal asymmetry; verify the tool authors are in figures' candidate pool"
            )

    # Compare track 04 (canon) vs track 01 (figures): canon authors should
    # appear as figures candidates
    if "04-canon" in track_keywords_lower and "01-figures" in track_keywords_lower:
        canon_only_lower = (
            track_keywords_lower["04-canon"] - track_keywords_lower["01-figures"]
        )
        canon_only_raw = {
            w for w in track_keywords_raw["04-canon"] if w.lower() in canon_only_lower
        }
        notable = [w for w in canon_only_raw
                   if any(c.isupper() for c in w) and 5 <= len(w) <= 20]
        if len(notable) >= 8:
            contradictions.append(
                f"Track 04 (canon) names {len(notable)} entities not in Track 01 — "
                f"key authors / lecturers may be missing from figures retained"
            )

    return contradictions


def parse_track(path: Path, track_key: str, industry_type: str = "technical") -> dict[str, Any]:
    """Parse a single track .md file into a stats dict.

    industry_type drives adaptive cold floors via adaptive_floor().
    Defaults to 'technical' so existing callers stay backward compatible.
    """
    if not path.exists():
        return {"missing": True, "path": str(path)}

    text = path.read_text(encoding="utf-8")

    # Source counts via citation markers used uniformly across track templates
    primary = len(re.findall(r"\[Primary\]", text))
    secondary = len(re.findall(r"\[Secondary\]", text))
    reference = len(re.findall(r"\[Reference\]", text))

    # Tier-typed endorsements (iter-13 cleanup added these to multiple tracks)
    figure_long = len(re.findall(r"\[type:\s*figure_long\]", text))
    figure_short = len(re.findall(r"\[type:\s*figure_short\]", text))
    course_syllabus = len(re.findall(r"\[type:\s*course_syllabus\]", text))

    # Per-track item count via heading patterns. Different tracks use different
    # depths/numbering, so we use track-specific patterns.
    item_count = count_items(text, track_key)

    # Extract the "Phase 2 提炼提示" block — each track template ends with one
    phase2_match = re.search(
        r"##\s*Phase\s*2\s*提炼提示\n(.*?)(?=\n##\s|\Z)",
        text,
        re.DOTALL,
    )
    phase2_content = phase2_match.group(1).strip() if phase2_match else None

    # Cold-signal detection: only matches explicit positive declarations of cold
    # status, not generic mentions of "冷僻" (which appears in every track template's
    # boilerplate "**冷僻信号**:" subheading regardless of actual state).
    # Looks for sentences like "本 track 信号薄弱" / "冷门领域协议生效" / "冷僻领域，仅找到 N 位".
    cold_signal = bool(re.search(
        r"(?:本.{0,8}(?:track|维度|轨)?\s*(?:信号薄弱|不足))"
        r"|(?:冷门领域协议生效)"
        r"|(?:冷僻领域[，,]\s*仅找到)"
        r"|(?:维度信号薄弱)",
        phase2_content or "",
    ))

    total_sources = primary + secondary + reference
    primary_ratio = (primary / total_sources) if total_sources else 0.0

    threshold = adaptive_floor(track_key, industry_type)
    item_below_floor = item_count < threshold

    return {
        "path": str(path),
        "missing": False,
        "item_count": item_count,
        "item_floor": threshold,
        "item_below_floor": item_below_floor,
        "source_counts": {
            "primary": primary,
            "secondary": secondary,
            "reference": reference,
            "total": total_sources,
        },
        "primary_ratio": round(primary_ratio, 2),
        "endorsement_types": {
            "figure_long": figure_long,
            "figure_short": figure_short,
            "course_syllabus": course_syllabus,
        },
        "cold_signal_self_reported": cold_signal,
        "phase2_interface": phase2_content,
    }


def count_items(text: str, track_key: str) -> int:
    """Count primary items per-track. Track-specific patterns reflect each
    template's heading conventions.
    """
    if track_key == "01-figures":
        return len(re.findall(r"^###\s+\d+\.\s+", text, re.MULTILINE))
    if track_key == "02-tools":
        return len(re.findall(r"^###\s+\d+\.\s+", text, re.MULTILINE))
    if track_key == "03-workflows":
        return len(re.findall(r"^###\s+\d+\.\s+", text, re.MULTILINE))
    if track_key == "04-canon":
        # 4-type taxonomy: 📖 books / 📄 papers / 🎓 courses / 💡 concepts
        return len(re.findall(r"^###\s+(?:📖|📄|🎓|💡)\s*\d+\.\s+", text, re.MULTILINE))
    if track_key == "05-sources":
        # Per-source headings start with type icon
        return len(re.findall(r"^###\s+(?:📰|🎙️|🎪|👥|📊|.{1,3})\s*\d+\.\s+",
                              text, re.MULTILINE))
    if track_key == "06-glossary":
        return len(re.findall(r"^###\s+\d+\.\s+", text, re.MULTILINE))
    # Generic fallback
    return len(re.findall(r"^###\s+\d+", text, re.MULTILINE))


def aggregate(skill_dir: Path) -> dict[str, Any]:
    """Run parse_track on all 6 tracks, build aggregate stats."""
    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        raise MergeError(f"references/research/ not found at {research_dir}")

    # Read intake.json for industry_type (drives adaptive cold floors).
    industry_type = "technical"
    intake_path = skill_dir / "intake.json"
    if intake_path.exists():
        try:
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
            industry_type = intake.get("industry_type") or "technical"
        except (json.JSONDecodeError, OSError):
            pass

    tracks: dict[str, Any] = {}
    for track_key, _ in TRACKS:
        path = research_dir / f"{track_key}.md"
        tracks[track_key] = parse_track(path, track_key, industry_type)

    # Aggregate
    present = [t for t in tracks.values() if not t.get("missing")]
    total_primary = sum(t["source_counts"]["primary"] for t in present)
    total_secondary = sum(t["source_counts"]["secondary"] for t in present)
    total_reference = sum(t["source_counts"]["reference"] for t in present)
    grand_total = total_primary + total_secondary + total_reference

    overall_primary_ratio = (total_primary / grand_total) if grand_total else 0.0

    cold_tracks = [k for k, t in tracks.items()
                   if not t.get("missing")
                   and (t.get("item_below_floor") or t.get("cold_signal_self_reported"))]

    contradictions = detect_cross_track_contradictions(tracks)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill_dir": str(skill_dir),
        "industry_type": industry_type,
        "tracks": tracks,
        "totals": {
            "primary": total_primary,
            "secondary": total_secondary,
            "reference": total_reference,
            "grand_total": grand_total,
            "overall_primary_ratio": round(overall_primary_ratio, 2),
        },
        "cold_tracks": cold_tracks,
        "is_cold_industry": len(cold_tracks) >= 3,
        "cross_track_contradictions": contradictions,
    }


# ---------------------------------------------------------------------------
# Rendering

def render_table(summary: dict[str, Any]) -> str:
    """Render the Phase 1.5 review table per SKILL.md spec."""
    lines: list[str] = []
    lines.append("# Phase 1.5 Research Review")
    lines.append("")
    lines.append(f"_Generated: {summary['generated_at']}_")
    lines.append("")

    lines.append("| # | Track | 项数 | 来源 (P/S/R) | 一手比例 | Cold? |")
    lines.append("|---|-------|------|-------------|---------|-------|")

    for i, (track_key, track_label) in enumerate(TRACKS, 1):
        t = summary["tracks"][track_key]
        if t.get("missing"):
            lines.append(f"| {i} | {track_label} | — | MISSING | — | ❌ |")
            continue
        sc = t["source_counts"]
        cold_marker = "🔵" if t.get("item_below_floor") or t.get("cold_signal_self_reported") else "✅"
        lines.append(
            f"| {i} | {track_label} | {t['item_count']} (floor {t['item_floor']}) "
            f"| {sc['primary']}/{sc['secondary']}/{sc['reference']} "
            f"| {int(t['primary_ratio'] * 100)}% | {cold_marker} |"
        )

    totals = summary["totals"]
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append(f"- 总来源数: {totals['grand_total']}")
    lines.append(f"  - Primary: {totals['primary']}")
    lines.append(f"  - Secondary: {totals['secondary']}")
    lines.append(f"  - Reference: {totals['reference']}")
    lines.append(f"- 总体一手比例: {int(totals['overall_primary_ratio'] * 100)}%")
    lines.append(f"- 冷僻 track 数: {len(summary['cold_tracks'])}")
    if summary["cold_tracks"]:
        lines.append(f"  - 受影响: {', '.join(summary['cold_tracks'])}")
    lines.append(f"- 整体行业判定: {'⚠️  COLD INDUSTRY' if summary['is_cold_industry'] else '✅ NORMAL'}")
    lines.append("")

    # Quality gate verdict
    lines.append("## 质量关卡判定")
    lines.append("")
    issues: list[str] = []
    if totals["overall_primary_ratio"] < 0.5:
        issues.append(
            f"一手来源比例 {int(totals['overall_primary_ratio'] * 100)}% < 50% — "
            f"研究主要靠二手转述，Phase 2 提炼会受影响"
        )
    # Per-track primary ratio warning (iter 18 fix)
    weak_tracks = [
        (tk, summary["tracks"][tk]["primary_ratio"])
        for tk, _ in TRACKS
        if not summary["tracks"][tk].get("missing")
        and summary["tracks"][tk]["primary_ratio"] < 0.4
    ]
    if weak_tracks:
        names = ", ".join(f"{tk} ({int(r * 100)}%)" for tk, r in weak_tracks)
        issues.append(
            f"个别 track 一手比例 < 40%: {names} — "
            f"该 track 的提炼质量明显弱于其他，建议针对性补 research"
        )
    if summary["is_cold_industry"]:
        issues.append(
            f"冷僻 track ≥ 3 个 ({', '.join(summary['cold_tracks'])}) — "
            f"建议在 Phase 2.8 诚实边界明确标注信号薄弱维度"
        )
    missing_tracks = [tk for tk, _ in TRACKS if summary["tracks"][tk].get("missing")]
    if missing_tracks:
        issues.append(f"缺失 track: {', '.join(missing_tracks)} — 必须补完才能进 Phase 2")

    contras = summary.get("cross_track_contradictions", [])
    if contras:
        for c in contras:
            issues.append(f"跨 track 信号矛盾: {c}")

    if issues:
        for issue in issues:
            lines.append(f"- ❌ {issue}")
        lines.append("")
        lines.append("**关卡判定: ⚠️ NEEDS REVIEW** — 用户需要决定继续 / 补 research / 缩小行业范围")
    else:
        lines.append("- ✅ 一手比例 ≥ 50%")
        lines.append("- ✅ 冷僻 track < 3")
        lines.append("- ✅ 6 个 track 都有内容")
        lines.append("- ✅ 无跨 track 矛盾信号")
        lines.append("")
        lines.append("**关卡判定: ✅ PASS** — 可以进 Phase 2")
    lines.append("")

    # Per-track Phase 2 interface (preserved verbatim, since each track's
    # subagent already prepared it)
    lines.append("## 各 Track Phase 2 接口")
    lines.append("")
    for track_key, track_label in TRACKS:
        t = summary["tracks"][track_key]
        lines.append(f"### {track_label} ({track_key})")
        if t.get("missing"):
            lines.append("_MISSING — 该 track 文件未生成_")
            lines.append("")
            continue
        if t.get("phase2_interface"):
            lines.append(t["phase2_interface"])
        else:
            lines.append("_Phase 2 接口段未找到 — 检查 track 文件结尾是否有 `## Phase 2 提炼提示` 节_")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI

def cmd_merge(args: argparse.Namespace) -> int:
    summary = aggregate(args.skill_dir)
    out_dir = args.skill_dir / "references"
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "synthesis-summary.md"
    json_path = out_dir / "synthesis-summary.json"

    md_content = render_table(summary)
    md_path.write_text(md_content, encoding="utf-8")

    # JSON output strips the inline phase2_interface (it's preserved in the .md)
    summary_json = {**summary}
    summary_json["tracks"] = {
        k: {kk: vv for kk, vv in v.items() if kk != "phase2_interface"}
        for k, v in summary["tracks"].items()
    }
    json_path.write_text(json.dumps(summary_json, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    print(json.dumps({
        "summary_md": str(md_path),
        "summary_json": str(json_path),
        "verdict_pass": (
            summary["totals"]["overall_primary_ratio"] >= 0.5
            and not summary["is_cold_industry"]
            and not any(summary["tracks"][tk].get("missing") for tk, _ in TRACKS)
            and not summary.get("cross_track_contradictions")
        ),
        "cold_tracks": summary["cold_tracks"],
        "cross_track_contradictions": summary.get("cross_track_contradictions", []),
        "totals": summary["totals"],
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    summary = aggregate(args.skill_dir)
    print(render_table(summary))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="merge_research — Phase 1.5 review aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="action", required=True)

    p_merge = sub.add_parser("merge", help="Aggregate research, write summary files")
    p_merge.add_argument("--skill-dir", required=True, type=Path)

    p_show = sub.add_parser("show", help="Print the Phase 1.5 review table to stdout")
    p_show.add_argument("--skill-dir", required=True, type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action == "merge":
            return cmd_merge(args)
        if args.action == "show":
            return cmd_show(args)
    except MergeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    return 99


if __name__ == "__main__":
    sys.exit(main())
