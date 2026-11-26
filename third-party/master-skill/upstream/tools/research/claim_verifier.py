#!/usr/bin/env python3
"""claim_verifier.py — reverse-search SKILL.md claims against the source pool.

After Phase 3 writes SKILL.md, run this to check each high-stakes claim
(mental model summaries, playbook rules, quality benchmarks) against the
research notes that supposedly backed them. Flags claims whose key terms
don't appear in ≥ 2 distinct research files — those are likely Phase 2/3
hallucinations or rhetorical filler dressed up as evidence.

This is a *safety net*, not a primary check. The mechanical primary check is
quality_check.py items 13-16. Use claim_verifier when you want a second
opinion on whether a SKILL.md actually traces back to the research.

Usage:
  python3 claim_verifier.py --skill-dir <path>
  python3 claim_verifier.py --skill-dir <path> --json
  python3 claim_verifier.py --skill-dir <path> --output report.md

Sections inspected (default):
  - 心智模型 (## 1. 心智模型 / ### 1.N)
  - 标准 Playbook (## 2.) — each numbered rule
  - 质量基准 / 反模式 (## 6.) — bullet items

Output: each claim → keyword set → file matches → verdict.

  supported: keywords appear in ≥ 2 distinct research files
  weak:      keywords appear in 1 file
  unsupported: 0 matches at all
  skipped:   < 3 high-content keywords (claim too generic to verify)

Exit codes: 0 ok / 1 ≥ 1 unsupported / 2 ≥ 1/3 weak+unsupported / 3 dir error
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

# Stop words for keyword extraction
STOP_EN = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "could", "may", "might", "must", "can", "this",
    "that", "these", "those", "it", "its", "we", "you", "they", "them",
    "as", "at", "by", "for", "from", "in", "into", "of", "on", "to", "with",
    "if", "then", "than", "so", "such", "just", "only", "very", "much",
    "most", "more", "less", "few", "many", "some", "any", "all", "no", "not",
    "what", "when", "where", "which", "who", "whom", "why", "how",
    "good", "bad", "well", "right", "wrong", "thing", "things", "case",
    "way", "time", "today", "make", "made", "use", "used", "using",
    "industry", "field", "approach", "method", "model", "models",
    "framework", "tool", "tools", "system", "process", "work", "works",
    "important", "useful", "helpful",
}
STOP_ZH = {
    "的", "地", "得", "了", "是", "在", "和", "与", "或", "而", "且", "也",
    "都", "就", "还", "再", "又", "更", "最", "很", "太", "非常", "比较",
    "我", "你", "他", "她", "它", "我们", "你们", "他们", "这", "那", "这个",
    "那个", "这些", "那些", "什么", "怎么", "为什么", "如何", "哪个", "哪里",
    "因此", "所以", "但是", "然而", "如果", "那么", "可能", "也许", "应该",
    "可以", "需要", "必须", "已经", "正在", "将要", "对", "错", "好", "坏",
    "时候", "事情", "方面", "情况", "问题", "工作", "方法", "工具", "系统",
    "重要", "有用",
}

KEY_TOKEN = re.compile(
    r"[A-Za-z][A-Za-z0-9\-]{2,}"  # English/code tokens
    r"|[一-鿿]{2,}",       # Chinese 2-gram+ chunks
    re.UNICODE,
)


def extract_keywords(text: str, max_n: int = 10) -> list[str]:
    """Pull a small set of distinctive keywords from a claim — proper nouns
    and content words. Drops stop words. Returns up to max_n unique terms."""
    if not text:
        return []
    seen: dict[str, int] = {}
    for tok in KEY_TOKEN.findall(text):
        low = tok.lower()
        if low in STOP_EN or tok in STOP_ZH:
            continue
        if len(tok) < 3:
            continue
        # Proper nouns get extra weight
        weight = 2 if (tok != low and tok[0].isupper()) else 1
        seen[tok] = seen.get(tok, 0) + weight
    sorted_tokens = sorted(seen.items(), key=lambda kv: -kv[1])
    return [t for t, _ in sorted_tokens[:max_n]]


def extract_claims(skill_text: str) -> list[dict]:
    """Pull claims from SKILL.md mental-model section + playbook section.

    Returns [{section, anchor, claim_id, text, keywords}].
    """
    out: list[dict] = []

    # Mental models section (### 1.N headers)
    mm_matches = list(re.finditer(
        r"^###\s+1\.(\d+)\s+(.+?)$(.*?)(?=^###\s+1\.\d+\s+|^##\s|\Z)",
        skill_text, re.MULTILINE | re.DOTALL,
    ))
    for m in mm_matches:
        title = m.group(2).strip()
        body = m.group(3).strip()
        # Take first 2 paragraphs as the claim
        claim_text = " ".join(re.split(r"\n\s*\n", body)[:2]).strip()
        if not claim_text:
            claim_text = title
        out.append({
            "section": "mental_model",
            "anchor": f"1.{m.group(1)}",
            "title": title,
            "text": claim_text[:500],
            "keywords": extract_keywords(title + " " + claim_text),
        })

    # Playbook rules — numbered items in `## 2. 标准 Playbook` / `## 标准 Playbook`
    pb_section = re.search(
        r"##\s+(?:2\.\s+)?标准\s+Playbook(.*?)(?=^##\s|\Z)",
        skill_text, re.MULTILINE | re.DOTALL,
    )
    if pb_section:
        rules = re.findall(
            r"^(\d+)\.\s+\*\*(.+?)\*\*([^\n]*(?:\n(?!\d+\.\s+\*\*).*)*)",
            pb_section.group(1),
            re.MULTILINE,
        )
        for num, title, body in rules:
            text = title + " " + body
            out.append({
                "section": "playbook",
                "anchor": f"2.{num}",
                "title": title.strip()[:120],
                "text": text.strip()[:500],
                "keywords": extract_keywords(text),
            })

    return out


def find_in_files(keywords: list[str], files: Iterable[Path], window: int = 600) -> dict:
    """For each keyword + file, find the positions it appears (capped at 5).
    Returns:
      {
        "by_keyword": {kw → [file_relpath, ...]} — files that contain the kw,
        "co_occurrences": [{file, kws_in_window}, ...] — every contiguous
            `window`-char span containing ≥ 2 keywords. This is what defines
            "supported" — scattered keywords across a file isn't enough.
      }
    """
    by_keyword: dict[str, list[str]] = {kw: [] for kw in keywords}
    co_occurrences: list[dict] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        # Per-file kw → list of positions
        positions: dict[str, list[int]] = {}
        for kw in keywords:
            pattern = re.escape(kw)
            flags = re.IGNORECASE if kw.lower() == kw else 0
            hits = [m.start() for m in re.finditer(pattern, text, flags=flags)][:5]
            if hits:
                positions[kw] = hits
                by_keyword[kw].append(f.name)
        # Find windows where ≥ 2 distinct keywords co-occur
        all_hits: list[tuple[int, str]] = []
        for kw, ps in positions.items():
            for p in ps:
                all_hits.append((p, kw))
        all_hits.sort()
        for i, (p, kw) in enumerate(all_hits):
            seen_in_window: set[str] = {kw}
            for q, kw2 in all_hits[i + 1:]:
                if q - p > window:
                    break
                seen_in_window.add(kw2)
                if len(seen_in_window) >= 2:
                    co_occurrences.append({
                        "file": f.name,
                        "start_offset": p,
                        "kws_in_window": sorted(seen_in_window),
                    })
                    break
    return {"by_keyword": by_keyword, "co_occurrences": co_occurrences}


# Iter 26 (codex 4-audit P0-1b): import source_manifest so claim_verifier can
# verify cited evidence_ids actually exist in the manifest, not just look like
# the right shape. Same lazy-import pattern as quality_check.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from . import source_manifest  # type: ignore
except ImportError:
    import source_manifest  # type: ignore[no-redef]


def find_evidence_ids(claim_text: str) -> list[str]:
    """Pull `evidence: [Txx-Sxxx, ...]` source_ids from a claim body.
    Iter 26: tolerate all markdown variations: bare / `**evidence**:` / `**evidence:**` /
    space before colon / fullwidth colon.
    """
    out: set[str] = set()
    for m in re.finditer(
        r"\*{0,2}evidence\*{0,2}\s*[:：]\*{0,2}\s*\[\s*([^\]]+)\]",
        claim_text, re.IGNORECASE,
    ):
        for tok in re.split(r"[,，;；\s]+", m.group(1)):
            tok = tok.strip()
            if re.match(r"^(?:T\d{2}-)?S\d+$", tok):
                out.add(tok)
    return sorted(out)


def _load_manifest_ids(skill_dir: Path) -> set[str]:
    """Return the set of source_id strings declared in the skill's Source
    Manifest tables. Empty set if no manifest. Used to verify that
    `evidence: [Txx-Sxxx]` citations name an actual manifest entry."""
    try:
        rows = source_manifest.parse_manifests(skill_dir)
        return {r.source_id for r in rows}
    except Exception:
        return set()


def verify(skill_dir: Path, min_keywords: int = 3) -> dict:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md = skill_dir / "references" / "synthesis.md"
    if not skill_md.exists():
        return {"verdict": "error", "reason": "no SKILL.md or synthesis.md"}

    research_dir = skill_dir / "references" / "research"
    research_files: list[Path] = list(research_dir.glob("*.md")) if research_dir.exists() else []
    # Also include synthesis.md and any user-provided transcripts
    extras: list[Path] = []
    syn = skill_dir / "references" / "synthesis.md"
    if syn.exists() and syn != skill_md:
        extras.append(syn)
    sources_dir = skill_dir / "sources"
    if sources_dir.exists():
        extras.extend(sources_dir.rglob("*.txt"))
        extras.extend(sources_dir.rglob("*.md"))
    haystack = research_files + extras

    if not haystack:
        return {"verdict": "error", "reason": "no research files or sources to verify against"}

    skill_text = skill_md.read_text(encoding="utf-8")
    claims = extract_claims(skill_text)
    if not claims:
        return {"verdict": "skipped", "reason": "no claims extracted from SKILL.md"}

    # Iter 26: load manifest source IDs so we can verify cited evidence_ids exist
    manifest_ids = _load_manifest_ids(skill_dir)

    results: list[dict] = []
    counts = {"supported": 0, "weak": 0, "unsupported": 0, "skipped": 0}
    for c in claims:
        kws = c["keywords"]
        evidence_ids = find_evidence_ids(c["text"])
        # Iter 26: split evidence_ids into known/unknown for visibility
        unknown_ev_ids = (
            [eid for eid in evidence_ids if eid not in manifest_ids]
            if manifest_ids else []
        )
        if len(kws) < min_keywords:
            results.append({**c, "matches": {}, "co_occurrences": [],
                            "evidence_ids": evidence_ids,
                            "unknown_evidence_ids": unknown_ev_ids,
                            "verdict": "skipped",
                            "reason": f"only {len(kws)} keywords (< {min_keywords})"})
            counts["skipped"] += 1
            continue
        m_data = find_in_files(kws, haystack)
        co_occurrences = m_data["co_occurrences"]
        by_keyword = m_data["by_keyword"]
        files_with_co_occurrence = {co["file"] for co in co_occurrences}
        kws_with_hits = sum(1 for kw in kws if by_keyword.get(kw))

        # Verdict rule (iter 26 — codex 4-audit P0-1b extended):
        # supported = ≥ 2 distinct files contain ≥ 2-keyword co-occurrence
        #             AND ≥ 2 evidence_ids cited on the claim, all known to manifest.
        # If no evidence_ids on claim (legacy): require co-occurrence in ≥ 2 files.
        # weak = some hits but no co-occurrence in 2+ files / fewer than 2 evidence_ids
        #        / cites unknown evidence_ids.
        # unsupported = no keyword hits at all.
        if not kws_with_hits:
            verdict = "unsupported"
        elif unknown_ev_ids:
            # Citing IDs that aren't in the manifest — typo or hallucination
            verdict = "weak"
        elif len(files_with_co_occurrence) >= 2 and (
            len(evidence_ids) >= 2 or not evidence_ids
        ):
            verdict = "supported"
        else:
            verdict = "weak"
        counts[verdict] += 1
        results.append({**c, "matches": by_keyword, "co_occurrences": co_occurrences[:5],
                        "files_with_co_occurrence": sorted(files_with_co_occurrence),
                        "evidence_ids": evidence_ids,
                        "unknown_evidence_ids": unknown_ev_ids,
                        "kws_with_hits": kws_with_hits, "verdict": verdict})

    if counts["unsupported"] >= 1:
        agg_verdict = "fail"
    elif counts["weak"] > len(results) // 3:
        agg_verdict = "partial"
    else:
        agg_verdict = "pass"

    return {
        "verdict": agg_verdict,
        "skill_file": str(skill_md.relative_to(skill_dir)),
        "research_files": [str(f.relative_to(skill_dir)) for f in haystack],
        "counts": counts,
        "claims": results,
    }


def render(report: dict) -> str:
    if report.get("verdict") in ("error", "skipped"):
        return f"# claim_verifier — {report['verdict']}\n\n{report.get('reason')}\n"

    lines: list[str] = []
    lines.append(f"# claim_verifier — {report.get('skill_file', '?')}")
    lines.append("")
    lines.append(f"**Verdict**: `{report['verdict']}`")
    lines.append("")
    c = report["counts"]
    lines.append(
        f"counts: {c['supported']} supported / {c['weak']} weak / "
        f"{c['unsupported']} unsupported / {c['skipped']} skipped"
    )
    lines.append("")
    icons = {"supported": "✅", "weak": "⚠️", "unsupported": "❌", "skipped": "—"}
    lines.append("| anchor | section | verdict | co-occur files | evidence_ids | claim |")
    lines.append("|--------|---------|---------|----------------|--------------|-------|")
    for cl in report["claims"]:
        co_files = ", ".join(cl.get("files_with_co_occurrence", []))[:50]
        ev_ids = ", ".join(cl.get("evidence_ids", []))[:30]
        snippet = (cl["title"] or cl["text"][:60]).replace("|", "\\|")
        lines.append(
            f"| {cl['anchor']} | {cl['section']} | "
            f"{icons.get(cl['verdict'], '?')} {cl['verdict']} | {co_files} | {ev_ids} | {snippet} |"
        )
    lines.append("")
    if report["verdict"] == "fail":
        lines.append("**FAIL**: ≥1 claim unsupported by any research file. "
                     "Either find evidence and add `evidence: [Sxxx]` to the claim, "
                     "or rewrite/remove it.")
    elif report["verdict"] == "partial":
        lines.append("**PARTIAL**: many claims only land in 1 source. Consider "
                     "promoting them to playbook (single-source rules) or finding a "
                     "second source.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Reverse-search SKILL.md claims against research/.")
    p.add_argument("--skill-dir", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    p.add_argument("--output", type=Path, help="Write report here (markdown by default)")
    p.add_argument("--min-keywords", type=int, default=3,
                   help="Skip claims with fewer than N keywords (too generic to verify)")
    args = p.parse_args(argv)

    report = verify(args.skill_dir, min_keywords=args.min_keywords)

    out: str
    if args.json:
        out = json.dumps(report, indent=2, ensure_ascii=False)
    else:
        out = render(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out + "\n", encoding="utf-8")
        print(f"claim_verifier: wrote {args.output}", file=sys.stderr)
    else:
        print(out)

    return {
        "pass": 0,
        "partial": 1,
        "fail": 2,
        "error": 3,
        "skipped": 0,
    }.get(report.get("verdict", "error"), 3)


if __name__ == "__main__":
    sys.exit(main())
