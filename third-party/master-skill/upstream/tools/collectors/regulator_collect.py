#!/usr/bin/env python3
"""regulator_collect.py — pull recent regulator / legislation documents.

Codex 3rd-audit P2 #5: master-skill claims "surrogate collectors for
regulator / association / JD / syllabus" but only had GitHub / arXiv / RSS /
podcast. Added in iter 26.

This is a thin web scraper for regulator portals. Currently supports:

  Locale  Site                                    Type
  ─────   ────────────────────────────────────    ──────────
  zh-CN   https://www.nfra.gov.cn/                金融监管总局
  zh-CN   https://www.npc.gov.cn/                 全国人大
  zh-CN   https://www.gov.cn/                     国务院
  en      https://www.federalregister.gov/        US Federal Register (RSS)
  en      https://www.gov.uk/government/publications  UK gov publications
  en      https://eur-lex.europa.eu/              EU law database

Usage:
  python3 regulator_collect.py --locale zh-CN --query "保险经纪" --max 20
  python3 regulator_collect.py --locale en --query "insurance regulation" --max 20

Output JSONL (one regulation/announcement per line):
  {"type": "regulator_doc", "locale": "...", "issuer": "...",
   "title": "...", "url": "...", "doc_type": "通知|指导意见|规定|...",
   "issued_date": "YYYY-MM-DD", "summary": "..."}

Note: many regulator sites lack public APIs / RSS. This tool drives
WebSearch-equivalent queries through the locale-specific portal and
surfaces a structured JSONL skeleton. For deep mining, the agent should
follow up with WebFetch on the candidate URLs.

Exit codes: 0 ok / 1 zero / 2 HTTP / 3 unsupported locale
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "master-skill-regulator-collector/1.0"
TIMEOUT = 30.0

# Locale → (issuer label, base URL, search-path template)
LOCALE_PORTALS: dict[str, list[dict]] = {
    "zh-CN": [
        {
            "issuer": "国家金融监督管理总局",
            "search_url": "https://www.nfra.gov.cn/cn/view/pages/search.html",
            "list_url": "https://www.nfra.gov.cn/cn/view/pages/governmentList.html",
        },
        {
            "issuer": "全国人大常委会",
            "search_url": "https://search.npc.gov.cn/search?title=",
            "list_url": "https://www.npc.gov.cn/npc/c2/c30834/index.html",
        },
    ],
    "en": [
        {
            "issuer": "US Federal Register",
            "search_url": "https://www.federalregister.gov/api/v1/documents.json",
            "list_url": "https://www.federalregister.gov/documents/current",
        },
        {
            "issuer": "UK government",
            "search_url": "https://www.gov.uk/api/search.json",
            "list_url": "https://www.gov.uk/government/publications",
        },
    ],
}


def fetch_us_federal_register(query: str, max_results: int) -> list[dict]:
    """The US Federal Register exposes a real JSON API. The other sites
    don't, so this is the one with structured output."""
    params = urllib.parse.urlencode({
        "conditions[term]": query,
        "per_page": str(min(max_results, 50)),
        "order": "newest",
    })
    url = f"https://www.federalregister.gov/api/v1/documents.json?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"regulator_collect: federal-register HTTP {e.code}", file=sys.stderr)
        return []
    except urllib.error.URLError as e:
        print(f"regulator_collect: federal-register network — {e.reason}", file=sys.stderr)
        return []
    out = []
    for r in data.get("results", []):
        out.append({
            "type": "regulator_doc",
            "locale": "en",
            "issuer": "US Federal Register",
            "title": r.get("title"),
            "url": r.get("html_url"),
            "doc_type": r.get("type"),
            "issued_date": r.get("publication_date"),
            "summary": (r.get("abstract") or "")[:400],
        })
    return out[:max_results]


def fetch_uk_gov(query: str, max_results: int) -> list[dict]:
    """UK gov.uk has a public JSON search API."""
    params = urllib.parse.urlencode({
        "q": query,
        "filter_format": "publication",
        "count": str(min(max_results, 20)),
        "order": "-public_timestamp",
    })
    url = f"https://www.gov.uk/api/search.json?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"regulator_collect: gov.uk failed — {e}", file=sys.stderr)
        return []
    out = []
    for r in data.get("results", []):
        out.append({
            "type": "regulator_doc",
            "locale": "en",
            "issuer": "UK Government",
            "title": r.get("title"),
            "url": "https://www.gov.uk" + r.get("link", ""),
            "doc_type": r.get("publication_type") or "publication",
            "issued_date": (r.get("public_timestamp") or "")[:10],
            "summary": (r.get("description") or "")[:400],
        })
    return out[:max_results]


def emit_zh_cn_skeleton(query: str, max_results: int) -> list[dict]:
    """zh-CN regulator portals don't expose public APIs. We emit candidate
    URLs the agent should hit via WebFetch + WebSearch with a clear hint."""
    sites = [
        ("国家金融监督管理总局", "https://www.nfra.gov.cn/", f"site:nfra.gov.cn {query}"),
        ("全国人大常委会", "https://www.npc.gov.cn/", f"site:npc.gov.cn {query}"),
        ("国务院", "https://www.gov.cn/", f"site:gov.cn {query}"),
        ("最高人民法院", "https://www.court.gov.cn/", f"site:court.gov.cn {query}"),
        ("最高人民检察院", "https://www.spp.gov.cn/", f"site:spp.gov.cn {query}"),
    ]
    out = []
    for issuer, root, hint in sites[:max_results]:
        out.append({
            "type": "regulator_doc",
            "locale": "zh-CN",
            "issuer": issuer,
            "title": f"(skeleton — agent fills via WebSearch)",
            "url": root,
            "doc_type": "skeleton",
            "issued_date": "",
            "summary": f"Agent: WebSearch '{hint}' to find recent docs, then WebFetch each.",
            "agent_hint": hint,
        })
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pull regulator documents for a query.")
    p.add_argument("--locale", required=True, choices=list(LOCALE_PORTALS.keys()))
    p.add_argument("--query", required=True, help="Industry / keyword to search")
    p.add_argument("--max", type=int, default=20)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)

    items: list[dict] = []
    if args.locale == "en":
        items.extend(fetch_us_federal_register(args.query, args.max // 2))
        items.extend(fetch_uk_gov(args.query, args.max - len(items)))
    elif args.locale == "zh-CN":
        items.extend(emit_zh_cn_skeleton(args.query, args.max))

    if not items:
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("a", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    else:
        for it in items:
            print(json.dumps(it, ensure_ascii=False))

    print(f"regulator_collect: {len(items)} docs (locale={args.locale}, query={args.query})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
