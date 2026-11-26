#!/usr/bin/env python3
"""extract_mentions.py — pull figure / tool / book / company mentions from transcripts.

Reads JSONL produced by `srt_to_transcript.py --jsonl` (or any JSONL with a
`text` field) and emits an entity manifest. Output is a JSON object that the
master-skill entity graph can ingest:

  {
    "source": "<input>",
    "person": [{"name": "Yann LeCun", "count": 3, "first_cue": 12}, ...],
    "tool":   [{"name": "LangChain", "count": 5, ...}, ...],
    "book":   [{"name": "ReAct paper", "count": 2, ...}, ...],
    "company":[{"name": "Anthropic", "count": 4, ...}, ...]
  }

Heuristic-only: capitalized 1-3-token phrases scoped by surrounding cue
context. Quality varies; this is a *seed* for the entity graph, not the
authoritative output. Pair with manual review or an NER model for harder
domains.

Usage:
  python3 extract_mentions.py <input.jsonl> [output.json|-]
  python3 extract_mentions.py <input.jsonl> --types person,tool      # subset
  python3 extract_mentions.py <input.jsonl> --min-count 2            # filter rares

Exit codes: 0 ok / 1 missing / 2 parse / 3 args
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Patterns
PROPER = re.compile(r"\b([A-Z][a-zA-Z]{1,29}(?:\s+[A-Z][a-zA-Z]{1,29}){0,2})\b")
ACRONYM = re.compile(r"\b([A-Z]{2,8})\b")

# Context cue → entity type bias.
TYPE_HINTS = {
    "person": [
        r"\b(said|told|wrote|writes|proposes|argues)\b",
        r"\b(co-?founder|CEO|CTO|professor|engineer|researcher)\b",
        r"\bcalled\s+\w+\b",
        "教授", "博士", "院士", "创始人", "认为", "提出", "说",
    ],
    "tool": [
        r"\b(framework|library|tool|platform|SDK|API|CLI|UI|database|model)\b",
        r"\b(use|using|run|install|deploy)\b",
        "框架", "工具", "平台", "用了", "装上", "跑", "迁到",
    ],
    "book": [
        r"\b(book|paper|article|essay|chapter|edition)\b",
        r"\bin\s+\w{2,4}\d{4}\b",   # "in CVPR2024"
        "书", "论文", "文章", "篇", "章",
    ],
    "company": [
        r"\b(company|startup|firm|lab|team|Inc\.?|Ltd\.?)\b",
        r"\b(funded|raised|acquired)\b",
        "公司", "团队", "实验室", "成立", "融资", "收购",
    ],
}

# Stop-list — capitalized words that aren't entities
STOP_TOKENS = {
    # Pronouns + articles
    "I", "We", "You", "They", "He", "She", "It", "The", "A", "An",
    "My", "Our", "Your", "Their", "His", "Her", "Its",
    # Conjunctions + adverbs
    "And", "But", "Or", "So", "Then", "Now", "Today", "Tomorrow",
    "Yesterday", "Anyway", "However", "Therefore", "Otherwise",
    # Calendar
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    # Conversational tokens that often appear sentence-initial
    "Yes", "No", "Maybe", "OK", "Okay", "Sure", "Right", "Yeah",
    "Welcome", "Thanks", "Hi", "Hello", "Hey", "Bye", "Goodbye",
    "Please", "Sorry", "Excuse", "Pardon",
    "Today's", "Tomorrow's", "Tonight", "Tonight's",
    # Common chinese-mixed conversation tokens
    "Wow", "Oh", "Ah", "Um", "Mm", "Hm", "Huh",
}

# Acronyms that look uppercase but aren't entities (filler / discourse markers
# / common 2-3-char tokens). The ACRONYM regex matches `[A-Z]{2,8}` so without
# this stop list, "OK" / "AI" (when used as adjective) etc. all become tools.
STOP_ACRONYMS = {
    "OK", "TV", "PR", "QA", "NB", "PS",     # short conversational
    "II", "III", "IV", "V", "VI", "VII",    # roman numerals
    "USA", "UK", "EU", "USD", "CNY", "JPY", "EUR", "GBP",  # geography / currency
    "AM", "PM", "BC", "AD", "CE", "BCE",    # time
    "FAQ", "TODO", "TBD", "DIY", "ASAP",    # generic web/biz boilerplate
    "WTF", "OMG", "LOL", "ROFL", "BRB",     # internet
    "NSFW", "TMI", "AFAIK", "IMO", "IMHO",
}


def detect_type(name: str, surrounding: str) -> str:
    s = surrounding.lower()
    scores = {t: 0 for t in TYPE_HINTS}
    for t, patterns in TYPE_HINTS.items():
        for p in patterns:
            if re.search(p, s, re.IGNORECASE):
                scores[t] += 1
    # Heuristic: contains "Mr.", "Dr.", "Ms.", "Prof." → person
    if re.match(r"^(?:Mr\.|Dr\.|Ms\.|Prof\.|Sir)\s+", name):
        scores["person"] += 3
    # 2+ tokens with each capitalized → likely person
    if " " in name and all(t[0].isupper() for t in name.split()):
        scores["person"] += 1
    # Single CamelCase-style or one-word lowercase mix → likely tool
    if " " not in name and (name.lower() != name) and not any(c == " " for c in name):
        scores["tool"] += 1
    if scores["company"] > scores["person"] and scores["company"] > 0:
        return "company"
    if scores["person"] > 0:
        return "person"
    if scores["book"] > 0:
        return "book"
    if scores["tool"] > 0:
        return "tool"
    # default: longer phrases lean person, single word leans tool
    if " " in name:
        return "person"
    return "tool"


def extract(text: str) -> list[str]:
    """Pull candidate proper nouns + acronyms from a string."""
    candidates: list[str] = []
    for m in PROPER.finditer(text):
        n = m.group(1).strip()
        if n in STOP_TOKENS:
            continue
        if len(n) < 3:
            continue
        candidates.append(n)
    for m in ACRONYM.finditer(text):
        a = m.group(1)
        if a in STOP_ACRONYMS:
            continue
        candidates.append(a)
    return candidates


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Extract entity mentions from transcript JSONL.")
    p.add_argument("input", type=Path)
    p.add_argument("output", nargs="?", default=None,
                   help="Output JSON (default <input>.mentions.json). `-` = stdout.")
    p.add_argument("--types", default="person,tool,book,company",
                   help="Comma-separated subset of types to include")
    p.add_argument("--min-count", type=int, default=1,
                   help="Drop mentions appearing < N times")
    p.add_argument("--source-name",
                   help="Override the `source` field (default: input filename)")
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"extract_mentions: input not found: {args.input}", file=sys.stderr)
        return 1

    requested_types = {t.strip() for t in args.types.split(",") if t.strip()}

    cues: list[dict] = []
    with args.input.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                cues.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    by_type: dict[str, Counter] = {t: Counter() for t in TYPE_HINTS}
    first_cue: dict[tuple[str, str], int] = {}
    for i, cue in enumerate(cues):
        text = cue.get("text", "")
        if not text:
            continue
        for n in extract(text):
            t = detect_type(n, text)
            by_type[t][n] += 1
            key = (t, n)
            if key not in first_cue:
                first_cue[key] = i

    out: dict = {
        "source": args.source_name or str(args.input),
        "cue_count": len(cues),
    }
    for t in TYPE_HINTS:
        if t not in requested_types:
            continue
        items = []
        for name, count in by_type[t].most_common():
            if count < args.min_count:
                continue
            items.append({
                "name": name,
                "count": count,
                "first_cue_index": first_cue.get((t, name)),
            })
        out[t] = items

    serialized = json.dumps(out, ensure_ascii=False, indent=2)
    output = args.output
    if output == "-":
        print(serialized)
    else:
        out_path = Path(output) if output else args.input.with_suffix(".mentions.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(serialized + "\n", encoding="utf-8")
        print(f"extract_mentions: wrote → {out_path}", file=sys.stderr)
    print(
        f"extract_mentions: scanned {len(cues)} cues, "
        f"types={','.join(sorted(requested_types))}, "
        f"counts=" + " ".join(f"{t}={len(out.get(t, []))}" for t in sorted(requested_types)),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
