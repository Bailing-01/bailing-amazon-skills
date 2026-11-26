#!/usr/bin/env python3
"""rss_collect.py — pull recent items from any RSS 2.0 / Atom feed.

Used by Track 05 (sources) Step 1 to seed candidate newsletters / blogs /
podcasts when you have a feed URL. Substack appends `/feed`, Beehiiv `/feed`
or `/rss`, Ghost `/rss/`, personal blogs commonly `/feed.xml`.

Pure stdlib (urllib + xml.etree). One feed at a time; loop in the shell or
pass a list via --feed-list.

Usage:
  # Single feed → JSONL on stdout
  python3 rss_collect.py --feed https://swyx.substack.com/feed

  # Many feeds from a file (one URL per line, # comments allowed)
  python3 rss_collect.py --feed-list feeds.txt --max 20 --output seeds.jsonl

  # Only items newer than 90 days
  python3 rss_collect.py --feed https://newsletter/foo --since-days 90

Output JSONL (one per item):
  {"type": "rss_item", "feed": "...", "feed_title": "...", "title": "...",
   "link": "...", "published": "...", "author": "...",
   "summary": "...", "content_snippet": "..."}

Exit codes: 0 ok / 1 zero items / 2 HTTP / 3 parse / 4 arg
"""
from __future__ import annotations

import argparse
import datetime as _dt
import email.utils
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

USER_AGENT = "master-skill-rss-collector/1.0"
TIMEOUT = 30.0
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "media": "http://search.yahoo.com/mrss/",
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"rss_collect: {url}: HTTP {e.code} {e.reason}") from None
    except urllib.error.URLError as e:
        raise SystemExit(f"rss_collect: {url}: network — {e.reason}") from None


def strip_html(text: str, max_chars: int = 280) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", " ", text)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_chars]


def parse_date(s: str) -> str:
    """Normalize various RSS / Atom date formats to ISO-8601 string. Returns
    "" if parse fails."""
    if not s:
        return ""
    # Try RFC 2822 first (RSS standard: "Tue, 12 May 2026 14:00:00 GMT")
    try:
        dt = email.utils.parsedate_to_datetime(s)
        if dt:
            return dt.isoformat()
    except (TypeError, ValueError):
        pass
    # ISO 8601 (Atom): pass through after normalizing trailing Z
    s2 = s.strip()
    s2 = re.sub(r"Z$", "+00:00", s2)
    try:
        dt = _dt.datetime.fromisoformat(s2)
        return dt.isoformat()
    except ValueError:
        pass
    return s  # give up — return raw


def parse_rss(root: ET.Element, feed_url: str) -> tuple[str, list[dict]]:
    """Parse RSS 2.0. Return (feed_title, items)."""
    channel = root.find("channel")
    if channel is None:
        return "", []
    feed_title = (channel.findtext("title") or "").strip()
    items: list[dict] = []
    for it in channel.findall("item"):
        link = (it.findtext("link") or "").strip()
        guid = (it.findtext("guid") or "").strip()
        # Author can come from <author>, <dc:creator>, or <itunes:author>
        author = (
            it.findtext("author")
            or it.findtext("dc:creator", namespaces=NS)
            or it.findtext("itunes:author", namespaces=NS)
            or ""
        ).strip()
        pub = (
            it.findtext("pubDate")
            or it.findtext("dc:date", namespaces=NS)
            or ""
        )
        # Description vs content:encoded
        desc = it.findtext("description") or ""
        content = it.findtext("content:encoded", namespaces=NS) or ""
        items.append({
            "type": "rss_item",
            "feed": feed_url,
            "feed_title": feed_title,
            "title": (it.findtext("title") or "").strip(),
            "link": link or guid,
            "guid": guid or link,
            "published": parse_date(pub),
            "author": author,
            "summary": strip_html(desc, 280),
            "content_snippet": strip_html(content, 1200),
        })
    return feed_title, items


def parse_atom(root: ET.Element, feed_url: str) -> tuple[str, list[dict]]:
    feed_title = (root.findtext("atom:title", default="", namespaces=NS) or "").strip()
    items: list[dict] = []
    for entry in root.findall("atom:entry", NS):
        # atom:link with rel="alternate"
        link_url = ""
        for link in entry.findall("atom:link", NS):
            if link.get("rel", "alternate") == "alternate":
                link_url = link.get("href") or ""
                break
        if not link_url:
            link_el = entry.find("atom:link", NS)
            if link_el is not None:
                link_url = link_el.get("href", "") or ""
        author = ""
        a_el = entry.find("atom:author", NS)
        if a_el is not None:
            author = (a_el.findtext("atom:name", default="", namespaces=NS) or "").strip()
        summary = entry.findtext("atom:summary", default="", namespaces=NS) or ""
        content = entry.findtext("atom:content", default="", namespaces=NS) or ""
        items.append({
            "type": "rss_item",
            "feed": feed_url,
            "feed_title": feed_title,
            "title": (entry.findtext("atom:title", default="", namespaces=NS) or "").strip(),
            "link": link_url,
            "guid": (entry.findtext("atom:id", default="", namespaces=NS) or "").strip(),
            "published": parse_date(
                entry.findtext("atom:published", default="", namespaces=NS)
                or entry.findtext("atom:updated", default="", namespaces=NS)
            ),
            "author": author,
            "summary": strip_html(summary, 280),
            "content_snippet": strip_html(content, 1200),
        })
    return feed_title, items


def collect(feed_url: str, max_items: int, since_days: int | None) -> list[dict]:
    body = fetch(feed_url)
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise SystemExit(f"rss_collect: {feed_url} parse error — {e}") from None

    # Identify format. Atom root tag is `{atom}feed`, RSS is `rss`.
    tag = root.tag.lower()
    if tag.endswith("rss"):
        _, items = parse_rss(root, feed_url)
    elif tag.endswith("feed"):
        _, items = parse_atom(root, feed_url)
    else:
        raise SystemExit(f"rss_collect: {feed_url}: unknown root tag `{tag}`")

    if since_days is not None:
        cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=since_days)
        kept: list[dict] = []
        for it in items:
            try:
                d = _dt.datetime.fromisoformat(it["published"])
                if d.tzinfo is None:
                    d = d.replace(tzinfo=_dt.timezone.utc)
                if d >= cutoff:
                    kept.append(it)
            except (ValueError, TypeError):
                # Items without parseable dates: keep them (better than dropping)
                kept.append(it)
        items = kept

    return items[:max_items]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pull items from RSS / Atom feeds.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--feed", help="Single feed URL")
    g.add_argument("--feed-list", type=Path, help="File of feed URLs (one per line)")
    p.add_argument("--max", type=int, default=20, help="Max items per feed (default 20)")
    p.add_argument("--since-days", type=int, help="Filter items newer than N days")
    p.add_argument("--output", type=Path, help="Append JSONL here (default stdout)")
    args = p.parse_args(argv)

    feeds: list[str] = []
    if args.feed:
        feeds = [args.feed]
    elif args.feed_list:
        for line in args.feed_list.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                feeds.append(line)

    all_items: list[dict] = []
    for url in feeds:
        try:
            items = collect(url, max_items=args.max, since_days=args.since_days)
            all_items.extend(items)
            print(f"rss_collect: {url} → {len(items)} items", file=sys.stderr)
        except SystemExit as e:
            print(f"rss_collect: skipping {url}: {e}", file=sys.stderr)
            continue

    if not all_items:
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("a", encoding="utf-8") as f:
            for it in all_items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    else:
        for it in all_items:
            print(json.dumps(it, ensure_ascii=False))

    print(
        f"rss_collect: total {len(all_items)} items across {len(feeds)} feeds",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
