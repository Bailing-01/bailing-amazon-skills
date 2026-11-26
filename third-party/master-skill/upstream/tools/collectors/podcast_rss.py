#!/usr/bin/env python3
"""podcast_rss.py — pull episode metadata from a podcast RSS feed.

Apple Podcast / Spotify don't expose their own catalog as RSS, but **every
podcast's underlying feed is RSS** (the platforms re-publish it). To find a
feed URL:

  - Substack-hosted podcasts: append `/feed` to the show home page
  - Anchor / Spotify for Podcasters: anchor.fm/s/<id>/podcast/rss
  - Buzzsprout / Transistor / Megaphone: each show has a public RSS URL on
    the show page footer
  - Apple Podcasts: use https://itunes.apple.com/lookup?id=<showid>&entity=podcast
    to retrieve the `feedUrl` field, then fetch that.

This script is the ingest side: given the RSS URL, it returns episode-level
records with podcast-specific fields (duration, audio_url, episode_number,
season, transcript_url, guests).

Usage:
  # Top 30 episodes of Latent Space
  python3 podcast_rss.py --feed https://api.substack.com/feed/podcast/12345.rss --max 30

  # Look up an Apple Podcast feed first, then ingest
  python3 podcast_rss.py --apple-id 1715789198 --max 20

  # Save to seeds.jsonl
  python3 podcast_rss.py --feed <url> --output seeds.jsonl

Output JSONL (one episode per line):
  {"type": "podcast_episode", "feed": "...", "show_title": "...", "show_host": "...",
   "title": "...", "guid": "...", "link": "...", "audio_url": "...",
   "duration_sec": 7200, "episode_number": 137, "season": 4,
   "published": "2026-04-15T...", "summary": "...", "guests": [...],
   "transcript_url": null}

Exit codes: 0 ok / 1 zero / 2 HTTP / 3 arg
"""
from __future__ import annotations

import argparse
import datetime as _dt
import email.utils
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

USER_AGENT = "master-skill-podcast-collector/1.0"
TIMEOUT = 30.0
NS = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "podcast": "https://podcastindex.org/namespace/1.0",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "atom": "http://www.w3.org/2005/Atom",
}


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"podcast_rss: {url}: HTTP {e.code} {e.reason}") from None
    except urllib.error.URLError as e:
        raise SystemExit(f"podcast_rss: {url}: network — {e.reason}") from None


def resolve_apple_feed(apple_id: str | int) -> str:
    """Use iTunes Lookup API to convert an Apple Podcast show ID → its RSS feed URL."""
    url = f"https://itunes.apple.com/lookup?id={apple_id}&entity=podcast"
    body = http_get(url)
    data = json.loads(body.decode("utf-8"))
    results = data.get("results") or []
    if not results:
        raise SystemExit(f"podcast_rss: no Apple Podcast results for id={apple_id}")
    feed = results[0].get("feedUrl")
    if not feed:
        raise SystemExit(f"podcast_rss: Apple result missing feedUrl: {results[0]}")
    return feed


def parse_duration(text: str) -> int | None:
    """itunes:duration may be `HH:MM:SS`, `MM:SS`, or seconds-as-int. Return seconds."""
    if not text:
        return None
    text = text.strip()
    if text.isdigit():
        return int(text)
    parts = text.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 1:
        return nums[0]
    return None


def parse_date(s: str) -> str:
    if not s:
        return ""
    try:
        dt = email.utils.parsedate_to_datetime(s)
        return dt.isoformat() if dt else s
    except (TypeError, ValueError):
        return s


def extract_guests(title: str, summary: str) -> list[str]:
    """Heuristic: pull names that follow `with`, `feat.`, `featuring`, `:` from
    the episode title. Returns up to 4 guesses; manual review still required."""
    candidates: list[str] = []
    for pattern in [
        r"(?:with|feat\.?|featuring|hosting|guests?:)\s+([^,—–\-]+(?:,\s*[^,—–\-]+){0,3})",
        r":\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}){0,3})",
    ]:
        m = re.search(pattern, title, re.IGNORECASE)
        if m:
            for n in re.split(r",|\s+(?:and|&)\s+", m.group(1)):
                n = n.strip()
                if 3 <= len(n) <= 40 and n[0].isupper():
                    candidates.append(n)
            break
    return list(dict.fromkeys(candidates))[:4]


def parse_feed(body: bytes, feed_url: str) -> list[dict]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise SystemExit(f"podcast_rss: parse error — {e}")
    channel = root.find("channel")
    if channel is None:
        raise SystemExit("podcast_rss: not an RSS feed (no <channel>)")

    show_title = (channel.findtext("title") or "").strip()
    show_host = (channel.findtext("itunes:author", namespaces=NS) or "").strip()
    show_summary = (channel.findtext("itunes:summary", namespaces=NS) or "").strip()

    items: list[dict] = []
    for it in channel.findall("item"):
        title = (it.findtext("title") or "").strip()
        # Audio URL: <enclosure url="...">
        audio_url = ""
        enc = it.find("enclosure")
        if enc is not None:
            audio_url = enc.get("url", "") or ""
        # Duration
        dur_text = it.findtext("itunes:duration", namespaces=NS) or ""
        duration_sec = parse_duration(dur_text)
        # Episode / season
        ep_num_raw = it.findtext("itunes:episode", namespaces=NS) or ""
        season_raw = it.findtext("itunes:season", namespaces=NS) or ""
        # Summary
        summary = (
            it.findtext("itunes:summary", namespaces=NS)
            or it.findtext("description")
            or ""
        ).strip()
        # Transcript (Podcasting 2.0)
        transcript_url = ""
        for tr in it.findall("podcast:transcript", NS):
            transcript_url = tr.get("url", "") or ""
            if tr.get("type", "").lower() in {"text/vtt", "application/srt", "text/srt"}:
                break

        guests = extract_guests(title, summary)

        items.append({
            "type": "podcast_episode",
            "feed": feed_url,
            "show_title": show_title,
            "show_host": show_host,
            "show_summary": show_summary[:300],
            "title": title,
            "guid": (it.findtext("guid") or "").strip(),
            "link": (it.findtext("link") or "").strip(),
            "audio_url": audio_url,
            "duration_sec": duration_sec,
            "duration_text": dur_text,
            "episode_number": int(ep_num_raw) if ep_num_raw.isdigit() else None,
            "season": int(season_raw) if season_raw.isdigit() else None,
            "published": parse_date(it.findtext("pubDate") or ""),
            "summary": re.sub(r"<[^>]+>", " ", summary)[:400],
            "guests": guests,
            "transcript_url": transcript_url or None,
        })
    return items


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pull episodes from a podcast RSS feed.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--feed", help="Direct RSS feed URL")
    g.add_argument("--apple-id", help="Apple Podcast show ID; will be resolved to feedUrl via iTunes Lookup")
    p.add_argument("--max", type=int, default=30, help="Max episodes (default 30)")
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)

    if args.apple_id:
        feed_url = resolve_apple_feed(args.apple_id)
        print(f"podcast_rss: apple_id={args.apple_id} → feed {feed_url}", file=sys.stderr)
    else:
        feed_url = args.feed

    body = http_get(feed_url)
    items = parse_feed(body, feed_url)
    items = items[:args.max]

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

    print(f"podcast_rss: wrote {len(items)} episodes from {feed_url}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
