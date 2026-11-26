#!/usr/bin/env python3
"""arxiv_collect.py — pull papers from arXiv API for canon / figures discovery.

Used by Track 04 (canon) Step 1 to seed candidate papers, and by Track 01
(figures) to find core authors of citation hubs.

arXiv API: http://export.arxiv.org/api/query — Atom XML response. We parse
with xml.etree (stdlib) to avoid a feedparser dependency.

Usage:
  # Recent cs.LG (Machine Learning) papers
  python3 arxiv_collect.py --query "cat:cs.LG" --max 30

  # Search all categories by keyword
  python3 arxiv_collect.py --query "all:agent" --max 50 --output seeds.jsonl

  # Recent papers by a specific author
  python3 arxiv_collect.py --author "Yann LeCun" --max 20

  # Recent submissions, last N days
  python3 arxiv_collect.py --query "cat:cs.AI" --since-days 30

Output JSONL: one paper per line.
  {"type": "arxiv_paper", "arxiv_id": "...", "title": "...",
   "authors": [...], "abstract": "...", "published": "...",
   "primary_category": "cs.AI", "categories": [...], "pdf_url": "...",
   "doi": null}

Exit codes: 0 ok / 1 empty / 2 HTTP error / 3 arg error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

API = "http://export.arxiv.org/api/query"
USER_AGENT = "master-skill-arxiv-collector/1.0"
TIMEOUT = 30.0
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _http_error(msg: str, exit_code: int = 2) -> SystemExit:
    print(msg, file=sys.stderr)
    return SystemExit(exit_code)


def fetch_atom(query: str, start: int, max_results: int, sort_by: str) -> bytes:
    params = {
        "search_query": query,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": sort_by,
        "sortOrder": "descending",
    }
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise _http_error(f"arxiv_collect: HTTP {e.code} {e.reason}", 2) from None
    except urllib.error.URLError as e:
        raise _http_error(f"arxiv_collect: network — {e.reason}", 2) from None


def parse_entry(entry: ET.Element) -> dict:
    def t(tag: str) -> str:
        el = entry.find(f"atom:{tag}", NS)
        return (el.text or "").strip() if el is not None else ""

    arxiv_id_full = t("id")  # e.g. http://arxiv.org/abs/2305.12345v2
    arxiv_id = arxiv_id_full.rsplit("/", 1)[-1] if arxiv_id_full else ""
    pdf_url = ""
    for link in entry.findall("atom:link", NS):
        if link.get("title") == "pdf":
            pdf_url = link.get("href", "")
            break
    if not pdf_url and arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    authors = [
        (a.findtext("atom:name", default="", namespaces=NS) or "").strip()
        for a in entry.findall("atom:author", NS)
    ]
    primary_cat = entry.find("arxiv:primary_category", NS)
    cats = [
        c.get("term", "")
        for c in entry.findall("atom:category", NS)
    ]
    doi_el = entry.find("arxiv:doi", NS)
    return {
        "type": "arxiv_paper",
        "arxiv_id": arxiv_id,
        "title": " ".join(t("title").split()),  # collapse whitespace
        "authors": authors,
        "abstract": " ".join(t("summary").split()),
        "published": t("published"),
        "updated": t("updated"),
        "primary_category": primary_cat.get("term") if primary_cat is not None else None,
        "categories": cats,
        "pdf_url": pdf_url,
        "abs_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "",
        "doi": doi_el.text.strip() if doi_el is not None and doi_el.text else None,
    }


def search(
    query: str,
    max_results: int,
    sort_by: str = "submittedDate",
    page_size: int = 100,
) -> Iterable[dict]:
    fetched = 0
    start = 0
    while fetched < max_results:
        n = min(page_size, max_results - fetched)
        body = fetch_atom(query, start=start, max_results=n, sort_by=sort_by)
        root = ET.fromstring(body)
        entries = root.findall("atom:entry", NS)
        if not entries:
            break
        for e in entries:
            yield parse_entry(e)
            fetched += 1
            if fetched >= max_results:
                return
        if len(entries) < n:
            break
        start += n
        # arXiv API politeness: 3-second min between requests
        time.sleep(3.0)


def build_query(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.query:
        parts.append(args.query)
    if args.author:
        # arXiv uses au:LastName for author search; supply full and let arXiv match
        parts.append(f"au:{args.author}")
    if args.since_days:
        cutoff = _dt.date.today() - _dt.timedelta(days=args.since_days)
        # arXiv supports submittedDate range. format: YYYYMMDD0000
        d = cutoff.strftime("%Y%m%d")
        parts.append(f"submittedDate:[{d}0000+TO+999912312359]")
    if not parts:
        raise SystemExit("arxiv_collect: must give --query or --author or --since-days")
    return " AND ".join(f"({p})" if " " in p or "+" in p else p for p in parts)


def write_jsonl(records: Iterable[dict], dest: Path | None) -> int:
    count = 0
    if dest is None:
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
            count += 1
        return count
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Pull papers from arXiv for canon / figures seed discovery."
    )
    p.add_argument("--query", help="arXiv search_query expression, e.g. 'cat:cs.LG' "
                                    "or 'ti:retrieval+AND+abs:augmented'")
    p.add_argument("--author", help="Search by author name (au:)")
    p.add_argument("--since-days", type=int, help="Only papers from last N days")
    p.add_argument("--max", type=int, default=30, help="Max papers (default 30)")
    p.add_argument("--sort-by", default="submittedDate",
                   choices=["submittedDate", "lastUpdatedDate", "relevance"])
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)

    q = build_query(args)
    records = list(search(q, max_results=args.max, sort_by=args.sort_by))
    if not records:
        print(f"arxiv_collect: 0 papers for query={q}", file=sys.stderr)
        return 1
    n = write_jsonl(records, args.output)
    print(
        f"arxiv_collect: wrote {n} papers for query=`{q}`"
        + (f" → {args.output}" if args.output else ""),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
