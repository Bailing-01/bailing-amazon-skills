#!/usr/bin/env python3
"""transcript_scorer.py — score transcript cues for "actionable density".

Reads JSONL produced by `srt_to_transcript.py --jsonl`, scores each cue, and
emits the same JSONL plus a numeric `actionable_score` per cue. Optionally
filter to the top-K cues by score so Phase 2 / Phase 3 only ingests the high-
density chunks instead of the entire transcript.

The score is a cheap heuristic, not a model:
  + 1 per industry-jargon hit (term density)
  + 2 per proper-noun mention (figure / tool / company / book — caps + 2-30 chars)
  + 1 per number / percentage (data point)
  + 1 per decision verb (`we use`, `I'd go with`, `选择`, `用`, `决定`, `推荐`)
  - 2 if cue matches an opener / closer / ad / 寒暄 pattern
  - 1 if cue is < 10 words (likely filler)

Usage:
  python3 transcript_scorer.py <input.jsonl> [output.jsonl|-]
  python3 transcript_scorer.py <input.jsonl> --top 50 -            # top 50 to stdout
  python3 transcript_scorer.py <input.jsonl> --jargon-list jargon.txt
  python3 transcript_scorer.py <input.jsonl> --min-score 4         # filter

Exit codes: 0 ok / 1 input missing / 2 parse / 3 args
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns

PROPER_NOUN = re.compile(r"\b([A-Z][a-zA-Z]{1,29}(?:[\s\-][A-Z][a-zA-Z]{1,29}){0,3})\b")
NUMBER_OR_PCT = re.compile(r"\b(?:\d{1,4}(?:\.\d+)?%|\d{2,}(?:[,，]\d{3})*(?:\.\d+)?)\b")
ACRONYM = re.compile(r"\b([A-Z]{2,6})\b")

DECISION_VERBS = [
    # English
    r"\bwe use\b", r"\bwe chose\b", r"\bwe went with\b", r"\bI prefer\b",
    r"\bI'd go with\b", r"\bI recommend\b", r"\byou should\b",
    r"\binstead of\b", r"\bthe trick is\b", r"\bthe key is\b",
    r"\brule of thumb\b", r"\bthe right call\b",
    # Chinese
    "选择", "推荐", "决定", "用[^,，。]{0,10}的方式", "我会(?:选|用|走|去)",
    "建议", "应该", "千万不要", "不要", "宁可", "宁愿",
    "[关键诀窍核心]在于",
]
DECISION_RE = re.compile(
    "(" + "|".join(DECISION_VERBS) + ")",
    re.IGNORECASE,
)

OPENER_CLOSER_AD = [
    # Generic openers
    r"^welcome to\b",
    r"^hi\s+(?:everyone|guys|all)\b",
    r"^hello\s+(?:everyone|guys|all)\b",
    r"^thanks for (?:listening|joining)",
    r"\b(?:like|subscribe|share)\b.{0,40}\b(?:channel|podcast|video)\b",
    # Ads
    r"\bsponsored by\b",
    r"\bbrought to you by\b",
    r"\b(?:promo|coupon)\s+code\b",
    r"\bgo to .* and use code\b",
    # Chinese
    r"^欢迎",
    r"^大家好",
    r"^各位听众",
    r"\b(?:订阅|关注|点赞)\s*(?:我们的)?\s*(?:频道|节目|播客)",
    r"\b本期由.{0,30}赞助\b",
    r"\b感谢收听\b",
    r"^[嗯哦呃嗯啊喂哎]",  # filler vocalizations
]
OPENER_RE = re.compile("(" + "|".join(OPENER_CLOSER_AD) + ")", re.IGNORECASE)


def load_jargon(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.split("#", 1)[0].strip().lower()
        if s:
            out.add(s)
    return out


def score_cue(text: str, jargon: set[str]) -> tuple[float, dict]:
    """Return (score, breakdown_dict). Score is now per-100-words density,
    so a 500-word ad with 5 names doesn't beat a 30-word decisive insight.

    Hard rule (iter 25, codex P1 #10): if the cue is dominated by opener /
    closer / ad / 寒暄 patterns (≥ 2 hits), the cue is auto-zeroed regardless
    of other signal — the proper noun is in the ad copy, not the substance.
    """
    if not text:
        return 0.0, {}

    lower = text.lower()
    proper = PROPER_NOUN.findall(text)
    proper = [p for p in proper if p.lower() not in {"i", "the", "and", "but", "we", "you", "they"}]
    n_proper = len(proper)
    n_numbers = len(NUMBER_OR_PCT.findall(text))
    n_acronyms = len([a for a in ACRONYM.findall(text) if a not in {"I", "II", "III"}])
    n_decisions = len(DECISION_RE.findall(text))
    n_openers = len(OPENER_RE.findall(text))
    n_jargon = sum(1 for j in jargon if j and j in lower) if jargon else 0
    word_count = len(text.split())

    # Hard filter: ≥ 2 opener/ad hits = auto-zero (the cue is structurally an ad)
    if n_openers >= 2:
        return 0.0, {
            "hard_zeroed": True,
            "reason": "≥ 2 opener/ad markers — structural ad/closer cue",
            "openers_ads": n_openers,
            "word_count": word_count,
        }

    raw = 0.0
    raw += 2.0 * n_proper
    raw += 1.0 * n_numbers
    raw += 1.0 * n_acronyms
    raw += 1.0 * n_decisions
    raw += 1.0 * n_jargon
    raw -= 2.0 * n_openers  # one opener still penalized
    if word_count < 10:
        raw -= 1.0

    # Length-normalize: density per 100 words. Short decisive cues beat long
    # ones with the same raw count of names because density is what we want.
    # Floor at 10 words so a 3-word "Pinecone wins." doesn't get inflated to
    # absurd density.
    norm = raw / max(word_count, 10) * 100.0

    return round(norm, 2), {
        "raw_score": round(raw, 2),
        "density_per_100_words": round(norm, 2),
        "proper_nouns": n_proper,
        "numbers": n_numbers,
        "acronyms": n_acronyms,
        "decision_verbs": n_decisions,
        "openers_ads": n_openers,
        "jargon_hits": n_jargon,
        "word_count": word_count,
        "samples": proper[:3],
    }


def process(
    input_path: Path,
    output: Path | str | None,
    top: int | None,
    min_score: int | None,
    jargon: set[str],
) -> int:
    cues: list[dict] = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                cue = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = cue.get("text", "")
            score, breakdown = score_cue(text, jargon)
            cue["actionable_score"] = score
            cue["scoring"] = breakdown
            cues.append(cue)

    if not cues:
        print("transcript_scorer: no cues parsed", file=sys.stderr)
        return 2

    if top is not None:
        cues_sorted = sorted(cues, key=lambda c: -c["actionable_score"])[:top]
    elif min_score is not None:
        cues_sorted = [c for c in cues if c["actionable_score"] >= min_score]
    else:
        cues_sorted = cues

    if output == "-":
        for c in cues_sorted:
            print(json.dumps(c, ensure_ascii=False))
    else:
        out_path = Path(output) if output else input_path.with_suffix(".scored.jsonl")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for c in cues_sorted:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"transcript_scorer: wrote {len(cues_sorted)} / {len(cues)} cues → {out_path}",
              file=sys.stderr)

    avg = sum(c["actionable_score"] for c in cues) / len(cues)
    top_avg = sum(c["actionable_score"] for c in cues_sorted) / max(1, len(cues_sorted))
    print(
        f"transcript_scorer: scored {len(cues)} cues, "
        f"mean={avg:.2f}, top-set mean={top_avg:.2f}",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Score transcript JSONL by actionable density.")
    p.add_argument("input", type=Path, help="Input JSONL from srt_to_transcript --jsonl")
    p.add_argument("output", nargs="?", default=None,
                   help="Output JSONL (default <input>.scored.jsonl). `-` = stdout.")
    p.add_argument("--top", type=int, help="Keep only top-K cues by score")
    p.add_argument("--min-score", type=int, help="Filter cues below this score")
    p.add_argument("--jargon-list", type=Path,
                   help="Optional file of one-jargon-per-line strings to credit (lowercased compare)")
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"transcript_scorer: input not found: {args.input}", file=sys.stderr)
        return 1
    jargon = load_jargon(args.jargon_list) if args.jargon_list else set()
    return process(args.input, args.output, args.top, args.min_score, jargon)


if __name__ == "__main__":
    sys.exit(main())
