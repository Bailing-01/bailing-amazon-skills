#!/usr/bin/env python3
"""github_topics.py — pull repos for a given topic from GitHub Search API.

Used by Track 02 (tools) Step 1 to seed the candidate pool with `repo / stars /
last commit / description` rows that come from the canonical source rather
than guesses or SEO articles.

Pure stdlib (urllib + json). No auth required for public read but rate-limit
is 10 req/min unauthenticated; pass `GITHUB_TOKEN` via env to lift to 5000/h.

Usage:
  # Top 30 repos for `llm-agent` topic, sorted by stars
  python3 github_topics.py --topic llm-agent --limit 30

  # Save to seeds.jsonl (one repo per line)
  python3 github_topics.py --topic rag --limit 50 --output seeds.jsonl

  # Filter by language + recency
  python3 github_topics.py --topic agent --language python --pushed-after 2025-06-01

Output: stdout (or --output file) is JSON Lines, one repo per line:

  {"name": "...", "full_name": "owner/repo", "url": "...", "stars": ...,
   "forks": ..., "language": "...", "description": "...",
   "pushed_at": "2026-04-12T...", "created_at": "...", "topics": [...]}

Exit codes:
  0  ≥1 repo returned
  1  no repos / topic empty
  2  HTTP / API error
  3  argument error
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

API_BASE = "https://api.github.com"
USER_AGENT = "master-skill-github-topics-collector/1.0"
DEFAULT_TIMEOUT = 30.0


class CollectorError(SystemExit):
    """SystemExit subclass that carries an explicit exit_code matching the
    docstring (0 ok / 1 zero result / 2 HTTP / 3 parse / 4 args)."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(exit_code)
        self.message = message

    def __str__(self) -> str:
        return self.message


def http_get_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """GET JSON, raising on HTTP error or parse error."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        msg = f"github_topics: HTTP {e.code} {e.reason}"
        if "rate limit" in body.lower():
            msg += " (set GITHUB_TOKEN env to raise unauthenticated 10/min limit)"
        print(msg, file=sys.stderr)
        if body:
            print(body[:500], file=sys.stderr)
        raise CollectorError(msg, exit_code=2) from None
    except urllib.error.URLError as e:
        msg = f"github_topics: network error — {e.reason}"
        print(msg, file=sys.stderr)
        raise CollectorError(msg, exit_code=2) from None
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as e:
        msg = f"github_topics: parse error — {e}"
        print(msg, file=sys.stderr)
        raise CollectorError(msg, exit_code=3) from None


def search_repos(
    topic: str,
    limit: int = 30,
    language: str | None = None,
    pushed_after: str | None = None,
    sort: str = "stars",
    token: str | None = None,
) -> list[dict[str, Any]]:
    """Return up to `limit` repos for the topic, newest-pushed first when
    pushed_after is set, else by stars desc."""
    q_parts = [f"topic:{topic}"]
    if language:
        q_parts.append(f"language:{language}")
    if pushed_after:
        q_parts.append(f"pushed:>={pushed_after}")
    q = " ".join(q_parts)
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    out: list[dict[str, Any]] = []
    per_page = min(100, limit)
    page = 1
    while len(out) < limit:
        url = (
            f"{API_BASE}/search/repositories"
            f"?q={urllib.parse.quote(q)}"
            f"&sort={sort}&order=desc&per_page={per_page}&page={page}"
        )
        body = http_get_json(url, headers=headers)
        items = body.get("items", [])
        if not items:
            break
        out.extend(items)
        if len(items) < per_page:
            break
        page += 1
        if page > 10:  # GitHub search caps at 1000 results
            break
    return out[:limit]


def to_seed_record(repo: dict[str, Any]) -> dict[str, Any]:
    """Trim a github API repo object to the fields we keep in seeds.jsonl."""
    return {
        "type": "github_repo",
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "url": repo.get("html_url"),
        "stars": repo.get("stargazers_count"),
        "forks": repo.get("forks_count"),
        "watchers": repo.get("watchers_count"),
        "open_issues": repo.get("open_issues_count"),
        "language": repo.get("language"),
        "description": repo.get("description"),
        "pushed_at": repo.get("pushed_at"),
        "created_at": repo.get("created_at"),
        "topics": repo.get("topics", []),
        "license": (repo.get("license") or {}).get("spdx_id"),
        "owner_login": (repo.get("owner") or {}).get("login"),
        "owner_type": (repo.get("owner") or {}).get("type"),
    }


def write_jsonl(records: Iterable[dict[str, Any]], dest: Path | None) -> None:
    if dest is None:
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Pull repos from GitHub Search API for a given topic."
    )
    p.add_argument("--topic", required=True, help="GitHub topic, e.g. `llm-agent`")
    p.add_argument("--limit", type=int, default=30,
                   help="Max repos returned (default 30; cap 100/page)")
    p.add_argument("--language", help="Filter by primary language")
    p.add_argument("--pushed-after", metavar="YYYY-MM-DD",
                   help="Only repos pushed on or after this date")
    p.add_argument("--sort", choices=["stars", "forks", "updated"], default="stars")
    p.add_argument("--output", type=Path, help="Write JSONL here (default: stdout)")
    p.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"),
                   help="GitHub token (default: env GITHUB_TOKEN)")
    p.add_argument("--include-archived", action="store_true",
                   help="Keep archived repos (default drops them)")
    args = p.parse_args(argv)

    repos = search_repos(
        topic=args.topic,
        limit=args.limit,
        language=args.language,
        pushed_after=args.pushed_after,
        sort=args.sort,
        token=args.token,
    )

    # Drop archived unless asked
    if not args.include_archived:
        repos = [r for r in repos if not r.get("archived")]

    if not repos:
        print(f"github_topics: 0 repos for topic={args.topic}", file=sys.stderr)
        return 1

    records = [to_seed_record(r) for r in repos]
    write_jsonl(records, args.output)
    print(
        f"github_topics: wrote {len(records)} repos for topic={args.topic}"
        + (f" → {args.output}" if args.output else ""),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
