#!/usr/bin/env python3
"""syllabus_collect.py — emit university course syllabus seed candidates.

Codex 3rd-audit P2 #5. Cold-mode industries with sparse popular canon
sometimes have rich academic syllabus signal: lecture notes, reading lists,
assignments. These map to Track 04 canon recommendations + Track 06 glossary.

Drives WebSearch on .edu domains for course pages by industry keyword.

Usage:
  python3 syllabus_collect.py --locale en --industry "insurance brokerage"
  python3 syllabus_collect.py --locale zh-CN --industry "保险精算"

Output JSONL: per-course-search seed.

Exit codes: 0 ok / 1 unsupported locale
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

DOMAIN_HINTS: dict[str, list[str]] = {
    "en": [
        "site:.edu",
        "site:.ac.uk",
        "site:.edu.au",
        "site:harvard.edu OR site:mit.edu OR site:stanford.edu",
        "site:cmu.edu OR site:berkeley.edu OR site:princeton.edu",
    ],
    "zh-CN": [
        "site:tsinghua.edu.cn",
        "site:pku.edu.cn",
        "site:fudan.edu.cn OR site:sjtu.edu.cn",
        "site:ruc.edu.cn OR site:cufe.edu.cn",
        "site:edu.cn",
    ],
}

KEYWORDS_PER_LOCALE: dict[str, list[str]] = {
    "en": [
        "{industry} syllabus",
        "{industry} course outline",
        "{industry} reading list",
        "{industry} lecture notes",
    ],
    "zh-CN": [
        "{industry} 教学大纲",
        "{industry} 课程介绍",
        "{industry} 推荐阅读",
        "{industry} 讲义",
    ],
}

EXPECTED_FIELDS = [
    "course_title",
    "instructor",
    "institution",
    "syllabus_url",
    "year_offered",
    "reading_list",       # list[{title, author, source_url}] — Track 04 canon
    "key_topics",         # list[str] — Track 06 glossary
    "homework_or_projects",  # workflow signal
]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Emit syllabus seed candidates.")
    p.add_argument("--locale", required=True, choices=list(DOMAIN_HINTS.keys()))
    p.add_argument("--industry", required=True)
    p.add_argument("--max", type=int, default=8)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)

    items = []
    for kw in KEYWORDS_PER_LOCALE[args.locale]:
        for site in DOMAIN_HINTS[args.locale][:2]:  # top 2 site filters per keyword
            q = f"{kw.format(industry=args.industry)} {site}"
            items.append({
                "type": "syllabus_seed",
                "materialized": False,
                "requires_webfetch": True,
                "locale": args.locale,
                "search_query": q,
                "search_url": f"https://www.google.com/search?q={urllib.parse.quote(q)}",
                "agent_hint": (
                    f"WebSearch '{q}'. Pick 1-2 syllabi. WebFetch each. "
                    f"Fill expected_fields. The reading_list is direct Track 04 canon input. "
                    f"The key_topics map to Track 06 glossary. Mark these in manifest as "
                    f"`bucket: surrogate_primary`, `note: syllabus`."
                ),
                "expected_fields": EXPECTED_FIELDS,
            })
            if len(items) >= args.max:
                break
        if len(items) >= args.max:
            break

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("a", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    else:
        for it in items:
            print(json.dumps(it, ensure_ascii=False))

    print(f"syllabus_collect: {len(items)} search queries", file=sys.stderr)
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
