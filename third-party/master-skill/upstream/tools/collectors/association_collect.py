#!/usr/bin/env python3
"""association_collect.py — emit industry-association seed candidates.

Codex 3rd-audit P2 #5. Cold-mode industries (closed-source / specialized
verticals) often have richer association signal than open canon. Industry
associations publish: directories of members, ethics codes, certification
programs, annual conferences, technical standards. All of which are
high-quality surrogate sources.

We don't talk to specific association APIs (every one is different); we
surface a structured search skeleton + agent hints.

Usage:
  python3 association_collect.py --locale zh-CN --industry "保险经纪" --max 6
  python3 association_collect.py --locale en --industry "insurance brokerage"

Output JSONL: per-association entry the agent should hit via WebFetch.

Exit codes: 0 ok / 1 unsupported locale
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

# Search shorthands per locale
SEARCH_PATTERNS: dict[str, list[str]] = {
    "zh-CN": [
        "{industry} 行业协会 官网",
        "{industry} 学会 网站",
        "{industry} 协会 章程 自律规范",
        "{industry} 行业大会 年会 sponsor",
        "{industry} 行业标准 协会",
    ],
    "en": [
        "{industry} industry association",
        "{industry} professional society",
        "{industry} code of ethics",
        "{industry} annual conference sponsors",
        "{industry} certification body",
    ],
}

EXPECTED_FIELDS = [
    "name",
    "url",
    "founded_year",
    "member_count",       # if disclosed
    "primary_focus",      # advocacy / standards / certification / conference
    "code_of_ethics_url",
    "annual_conference",
    "directory_url",      # member listing if public — figures candidates
    "is_government_linked",  # bool — partial-state actor
    "last_active_date",
]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Emit association-source seed candidates.")
    p.add_argument("--locale", required=True, choices=list(SEARCH_PATTERNS.keys()))
    p.add_argument("--industry", required=True)
    p.add_argument("--max", type=int, default=6)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)

    items = []
    for tmpl in SEARCH_PATTERNS[args.locale][:args.max]:
        q = tmpl.format(industry=args.industry)
        items.append({
            "type": "association_seed",
                "materialized": False,
                "requires_webfetch": True,
            "locale": args.locale,
            "search_query": q,
            "search_url": f"https://www.google.com/search?q={urllib.parse.quote(q)}",
            "agent_hint": (
                f"WebSearch '{q}'. Pick top 2-3 association sites. WebFetch each. "
                f"Fill expected_fields. Add to source manifest as `bucket: surrogate_primary` "
                f"with `note: association`. The member directory if public is the highest-value "
                f"signal — it lists figures (Track 01) the agent might otherwise miss."
            ),
            "expected_fields": EXPECTED_FIELDS,
        })

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("a", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    else:
        for it in items:
            print(json.dumps(it, ensure_ascii=False))

    print(f"association_collect: {len(items)} search queries (locale={args.locale}, industry={args.industry})",
          file=sys.stderr)
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
