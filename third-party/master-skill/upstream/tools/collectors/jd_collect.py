#!/usr/bin/env python3
"""jd_collect.py — pull job description seed data for surrogate skill discovery.

Codex 3rd-audit P2 #5: cold-mode industries (e.g. 农村信贷代理) often have
sparse public canon but rich job-description signal — JDs reveal real-world
workflows / tools / responsibility hierarchies that no academic paper
captures. This collector emits a JSONL skeleton + agent hints to drive
WebSearch on Boss直聘 / 拉勾 / LinkedIn.

We don't talk to BOSS / 拉勾 APIs (auth + rate limits); instead we surface
candidate search URLs + the structure the agent should fill via WebFetch.

Usage:
  python3 jd_collect.py --locale zh-CN --role "保险经纪人" --max 10
  python3 jd_collect.py --locale en --role "insurance broker" --max 10

Output JSONL (one JD seed entry per line):
  {"type": "jd_seed", "locale": "...", "platform": "...",
   "search_url": "...", "agent_hint": "...",
   "expected_fields": [...]}

Exit codes: 0 ok / 1 unsupported locale / 2 args
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

PLATFORMS: dict[str, list[dict]] = {
    "zh-CN": [
        {"name": "BOSS 直聘", "search": "https://www.zhipin.com/web/geek/job?query={q}"},
        {"name": "拉勾网", "search": "https://www.lagou.com/zhaopin/?query={q}"},
        {"name": "智联招聘", "search": "https://sou.zhaopin.com/?kw={q}"},
        {"name": "前程无忧 51job", "search": "https://search.51job.com/list/000000,000000,0000,00,9,99,{q},2,1.html"},
    ],
    "en": [
        {"name": "LinkedIn Jobs", "search": "https://www.linkedin.com/jobs/search/?keywords={q}"},
        {"name": "Indeed", "search": "https://www.indeed.com/jobs?q={q}"},
        {"name": "Glassdoor", "search": "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={q}"},
    ],
}

EXPECTED_FIELDS = [
    "title",
    "company",
    "responsibilities",  # list of bullet points → workflow steps
    "requirements",      # list of bullet points → tools + canon hints
    "salary_range",
    "location",
    "posted_date",
    "url",
]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Emit JD seed candidates for an industry role.")
    p.add_argument("--locale", required=True, choices=list(PLATFORMS.keys()))
    p.add_argument("--role", required=True, help="Role title to search (e.g. '保险经纪人')")
    p.add_argument("--max", type=int, default=8)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)

    q = urllib.parse.quote(args.role)
    items = []
    for plat in PLATFORMS[args.locale][:args.max]:
        items.append({
            "type": "jd_seed",
                "materialized": False,
                "requires_webfetch": True,
            "locale": args.locale,
            "platform": plat["name"],
            "search_url": plat["search"].format(q=q),
            "agent_hint": (
                f"WebFetch the search_url, scroll through 5-10 listings, fill expected_fields. "
                f"Look for *responsibilities* clusters that repeat across ≥ 3 JDs — that's a "
                f"workflow signal. Look for *required tools* or '熟悉 X' clusters — that's "
                f"Track 02 input."
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

    print(f"jd_collect: {len(items)} seeds (locale={args.locale}, role={args.role})",
          file=sys.stderr)
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
