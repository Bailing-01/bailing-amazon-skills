#!/usr/bin/env python3
"""cold_detector.py — detect cold-industry mode after Phase 1 wave 1.

Reads `references/research/04-canon.md`, `05-sources.md`, `06-glossary.md`
(wave 1 outputs) plus already-written tracks if any, counts entries, runs the
URL classifier, and returns a verdict the master agent can act on.

The default behavior of "cold detection" used to be: lower the per-track
floors. This script keeps that, but adds a *deep mode* recommendation: rather
than just shrinking, the agent should:

  1. Stop the surface-level web search loop (it's wasting tokens going in
     circles on a thin industry).
  2. Re-engage the user: "I see this is a niche/closed industry. Can you give
     me 3 internal materials — a private podcast, an internal wiki page, a
     supplier doc, a course you took?"
  3. Activate surrogate collectors (industry associations, regulators, course
     syllabi, job descriptions, supplier docs) — see Q5b.

Cold thresholds (configurable via CLI):
  figures < 5            in 01-figures.md  (only checked at --stage full)
  sources < 5            in 05-sources.md
  canon   < 8            in 04-canon.md
  verified_primary < 40% across all research URLs (skipped if URL count < 5)

If ≥ 2 of those thresholds trigger → "cold_deep_mode" recommended.
If ≥ 3 trigger → "cold_too_thin" — agent should warn user that the skill will
have honest-boundary disclaimers regardless of how much we patch.

`--stage wave1` skips figures/tools/workflows tracks (which haven't run yet
when called between wave 1 and wave 2). `--stage full` checks everything;
this is the right choice once wave 2 + 3 also wrote their files.

Usage:
  python3 cold_detector.py --skill-dir <path> --stage wave1
  python3 cold_detector.py --skill-dir <path> --stage full [--json]

Exit codes:
  0  normal industry (nothing to do)
  1  cold_deep_mode (recommend deep-engage user + run surrogate collectors)
  2  cold_too_thin (mark honest boundaries even with deep mode applied)
  3  error (missing dir, etc.)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_verifier  # type: ignore
import source_manifest  # type: ignore

DEFAULT_THRESHOLDS = {
    "figures": 5,
    "sources": 5,
    "canon": 8,
    "verified_primary_ratio": 0.4,
}


def count_entries(path: Path) -> int:
    """Count `### N` (level-3) section headers in a markdown file."""
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^###\s+", text, re.MULTILINE))


def resolve_skill_root(skill_dir: Path) -> Path:
    """Accept either a prototype root or its `output/` subdir.

    Prototype layout keeps the research trail at the ROOT
    (`{proto}/references/research`) while the installable skill lives in
    `{proto}/output/`. Callers pass either; walk up one level when handed
    an `output/` dir whose parent holds the trail.
    """
    if (skill_dir / "references" / "research").exists():
        return skill_dir
    parent = skill_dir.parent
    if skill_dir.name == "output" and (parent / "references" / "research").exists():
        return parent
    return skill_dir


def detect(skill_dir: Path, thresholds: dict, stage: str = "full") -> dict:
    skill_dir = resolve_skill_root(skill_dir)
    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        return {
            "verdict": "error",
            "reason": f"research dir not found: {research_dir}",
            "stage": stage,
            "exit": 3,
        }

    # Wave 1 only produces 04-canon, 05-sources, 06-glossary. Track 01 (figures),
    # 02 (tools), 03 (workflows) are wave 2/3. Skip checks for tracks that
    # haven't run in this stage to avoid false-positive cold mode.
    figures_count = count_entries(research_dir / "01-figures.md") if stage == "full" else None
    sources_count = count_entries(research_dir / "05-sources.md")
    canon_count = count_entries(research_dir / "04-canon.md")

    # Prefer manifest-declared buckets when a Source Manifest exists; fall
    # back to URL-only classification when the agent hasn't written manifests
    # yet. surrogate_primary + verified_primary both count as "first-hand tier"
    # — match the quality_check item 13 logic.
    primary_ratio = None
    blacklist_count = 0
    total_urls = 0
    scan_error = None
    rows = source_manifest.parse_manifests(skill_dir)
    if rows:
        rb = source_manifest.primary_ratio(rows)
        total_urls = rb.total
        primary_ratio = rb.ratio
        blacklist_count = rb.blacklisted
    else:
        try:
            scan = source_verifier.scan_dir(research_dir, locale="all", check_live=False)
            primary_ratio = scan["verified_primary_ratio"]
            blacklist_count = scan["counts"].get("blacklisted", 0)
            total_urls = scan["total_urls"]
        except Exception as e:
            primary_ratio = None
            scan_error = f"{type(e).__name__}: {e}"

    triggers: list[str] = []
    # figures only checked at --stage full (wave 2+ has written 01-figures.md)
    if figures_count is not None and figures_count < thresholds["figures"]:
        triggers.append(f"figures<{thresholds['figures']} (got {figures_count})")
    if sources_count < thresholds["sources"]:
        triggers.append(f"sources<{thresholds['sources']} (got {sources_count})")
    if canon_count < thresholds["canon"]:
        triggers.append(f"canon<{thresholds['canon']} (got {canon_count})")
    if (
        primary_ratio is not None
        and total_urls >= 5
        and primary_ratio < thresholds["verified_primary_ratio"]
    ):
        triggers.append(
            f"verified_primary<{int(thresholds['verified_primary_ratio']*100)}% "
            f"(got {primary_ratio*100:.1f}% of {total_urls} URLs)"
        )

    # Threshold rule (matches docstring): ≥3 triggers → too_thin, ≥2 → deep_mode.
    # Wave 1 stage has fewer checks available so the floor scales: ≥2/≥3 (full),
    # ≥1/≥2 (wave 1) since we have only 3 checks instead of 4.
    if stage == "wave1":
        deep_floor, thin_floor = 1, 2
    else:
        deep_floor, thin_floor = 2, 3
    if len(triggers) >= thin_floor:
        verdict = "cold_too_thin"
        exit_code = 2
    elif len(triggers) >= deep_floor:
        verdict = "cold_deep_mode"
        exit_code = 1
    else:
        verdict = "normal"
        exit_code = 0

    deep_mode_actions = [
        "STOP the surface-level web search loop. Wasting tokens on a thin industry.",
        "RE-ENGAGE the user with this script:",
        "  '我看下来 {industry} 这一行的公开材料比较薄, 这种情况蒸出来效果会受限. "
        "  能不能给我 3 个内部素材 — 例如:",
        "    1) 一份你公司 / 团队的内部 wiki / SOP 链接 (粘贴文本也可)",
        "    2) 一个你订阅的 niche newsletter / Slack / Discord 频道",
        "    3) 一份你做过的实战 case study (匿名化即可)",
        "  这能让 master skill 的厚度从「行业百科」级跳到「这一行的人怎么做事」级.'",
        "ACTIVATE surrogate collectors (Q5b): 行业协会 / 监管文件 / 课程 syllabus / "
        "招聘 JD / 供应商 docs. 标 `bucket: surrogate_primary` 进 manifest, note 字段说明类型 (协会/监管/syllabus/JD/vendor docs).",
        "LOWER per-track floors but RAISE verified_primary ratio bar to ≥ 70% (use less but better).",
    ]
    too_thin_actions = deep_mode_actions + [
        "WARN user: even after deep mode, expect SKILL.md 诚实边界 to flag major "
        "weaknesses on ≥1 dimension (figures / sources / canon).",
        "PROPOSE alternative scope: maybe the user wants a sibling industry that "
        "has more public material? e.g. '足踝外科' very thin → '骨科外科' broader.",
    ]

    out = {
        "verdict": verdict,
        "exit": exit_code,
        "skill_dir": str(skill_dir),
        "stage": stage,
        "counts": {
            "figures": figures_count,
            "sources": sources_count,
            "canon": canon_count,
            "total_urls": total_urls,
            "verified_primary_ratio": primary_ratio,
            "blacklist_count": blacklist_count,
        },
        "thresholds": thresholds,
        "triggers": triggers,
        "scan_error": scan_error,
    }
    if verdict == "cold_deep_mode":
        out["recommended_actions"] = deep_mode_actions
    elif verdict == "cold_too_thin":
        out["recommended_actions"] = too_thin_actions
    else:
        out["recommended_actions"] = []
    return out


def render(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"# cold_detector — {report['skill_dir']}")
    lines.append("")
    lines.append(f"**Verdict**: `{report['verdict']}` (exit {report['exit']})")
    lines.append("")
    c = report["counts"]
    pr = c["verified_primary_ratio"]
    pr_str = "n/a" if pr is None else f"{pr*100:.1f}%"
    lines.append(
        f"counts: figures={c['figures']}  sources={c['sources']}  canon={c['canon']}  "
        f"urls={c['total_urls']}  primary={pr_str}  blacklisted={c['blacklist_count']}"
    )
    lines.append("")
    if report["triggers"]:
        lines.append("triggered thresholds:")
        for t in report["triggers"]:
            lines.append(f"  - {t}")
        lines.append("")
    if report["recommended_actions"]:
        lines.append("recommended actions:")
        for a in report["recommended_actions"]:
            lines.append(f"  - {a}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Detect cold-industry mode after Phase 1 wave 1.")
    p.add_argument("--skill-dir", required=True, type=Path)
    p.add_argument("--stage", choices=["wave1", "full"], default="full",
                   help="`wave1` checks only canon/sources/glossary (run after wave 1 before wave 2). "
                        "`full` checks everything including figures/tools/workflows (after wave 3). Default: full.")
    p.add_argument("--figures-floor", type=int, default=DEFAULT_THRESHOLDS["figures"])
    p.add_argument("--sources-floor", type=int, default=DEFAULT_THRESHOLDS["sources"])
    p.add_argument("--canon-floor", type=int, default=DEFAULT_THRESHOLDS["canon"])
    p.add_argument("--primary-ratio-floor", type=float,
                   default=DEFAULT_THRESHOLDS["verified_primary_ratio"])
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    thresholds = {
        "figures": args.figures_floor,
        "sources": args.sources_floor,
        "canon": args.canon_floor,
        "verified_primary_ratio": args.primary_ratio_floor,
    }
    report = detect(args.skill_dir, thresholds, stage=args.stage)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render(report))
    return int(report["exit"])


if __name__ == "__main__":
    sys.exit(main())
