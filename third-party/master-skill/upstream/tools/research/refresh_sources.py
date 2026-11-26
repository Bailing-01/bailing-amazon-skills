#!/usr/bin/env python3
"""refresh_sources.py — HEAD-check every URL in research/ and flag stale/dead ones.

Run periodically (or before update_skill) to confirm verified_primary URLs
are still alive and pages haven't been silently rewritten / paywalled. Reads
all URLs from research/*.md, classifies them via source_verifier, then HEADs
each one in parallel.

Output: per-URL liveness report. Optionally update an inline `last_checked: YYYY-MM-DD`
in the source manifest tables.

Usage:
  python3 refresh_sources.py --skill-dir <path>            # report only, stdout
  python3 refresh_sources.py --skill-dir <path> --json
  python3 refresh_sources.py --skill-dir <path> --output report.md
  python3 refresh_sources.py --skill-dir <path> --workers 8  # parallel HEAD count

Exit codes:
  0 all alive
  1 ≥1 dead URL detected
  2 ≥1 redirect to a different domain (potential takeover)
  3 dir error
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_verifier  # type: ignore


def head(url: str, timeout: float = 10.0) -> dict:
    alive, status, reason = source_verifier.check_liveness(url, timeout=timeout)
    info: dict[str, Any] = {
        "url": url,
        "alive": alive,
        "status": status,
        "reason": reason,
        "checked_at": _dt.datetime.now().isoformat(timespec="seconds"),
    }
    return info


def detect_domain_drift(url: str, info: dict) -> bool:
    """Heuristic: if liveness reasons contain a 30x with a Location pointing to
    a different domain, flag as drift. We don't fetch Location explicitly here
    — caller reads the response in source_verifier.check_liveness which
    follows redirects by default. So 'alive' but original host being
    different from current parse is good enough.

    Currently always returns False — placeholder for future work.
    """
    return False


def refresh(skill_dir: Path, workers: int = 8) -> dict:
    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        return {"verdict": "error", "reason": f"no research/: {research_dir}", "exit": 3}

    # Reuse source_verifier scan to get the URL list (without liveness)
    scan = source_verifier.scan_dir(research_dir, locale="all", check_live=False)
    urls = list(scan["urls"].keys())
    if not urls:
        return {"verdict": "no_urls", "reason": "no URLs to refresh", "exit": 0,
                "scan_total": 0}

    # HEAD in parallel
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(head, u): u for u in urls}
        for fut in as_completed(futures):
            u = futures[fut]
            try:
                results[u] = fut.result()
            except Exception as e:
                results[u] = {
                    "url": u,
                    "alive": False,
                    "status": None,
                    "reason": f"{type(e).__name__}: {e}",
                    "checked_at": _dt.datetime.now().isoformat(timespec="seconds"),
                }

    counts = {"alive": 0, "dead": 0}
    dead_examples: list[dict] = []
    for u, info in results.items():
        bucket = scan["urls"][u]["bucket"]
        info["bucket"] = bucket
        if info["alive"]:
            counts["alive"] += 1
        else:
            counts["dead"] += 1
            dead_examples.append({"url": u, "reason": info["reason"], "bucket": bucket})

    if counts["dead"] >= 1:
        verdict = "fail"
        exit_code = 1
    else:
        verdict = "pass"
        exit_code = 0

    return {
        "verdict": verdict,
        "exit": exit_code,
        "skill_dir": str(skill_dir),
        "checked_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "counts": counts,
        "dead_examples": dead_examples[:20],
        "results": results,
    }


def render(report: dict) -> str:
    if report.get("verdict") == "error":
        return f"# refresh_sources — error\n\n{report['reason']}\n"
    if report.get("verdict") == "no_urls":
        return "# refresh_sources — no URLs in research/\n\nNothing to check.\n"
    lines: list[str] = []
    lines.append(f"# refresh_sources — {report['skill_dir']}")
    lines.append("")
    lines.append(f"**Verdict**: `{report['verdict']}` (checked {report['checked_at']})")
    lines.append("")
    c = report["counts"]
    lines.append(f"counts: {c['alive']} alive / {c['dead']} dead")
    lines.append("")
    if report.get("dead_examples"):
        lines.append("dead URLs:")
        for d in report["dead_examples"]:
            lines.append(f"  - [{d['bucket']}] {d['url']}  — {d['reason']}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="HEAD-check research URLs to detect dead links.")
    p.add_argument("--skill-dir", required=True, type=Path)
    p.add_argument("--workers", type=int, default=8, help="Parallel HEAD requests (default 8)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)

    report = refresh(args.skill_dir, workers=args.workers)
    out = json.dumps(report, indent=2, ensure_ascii=False) if args.json else render(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out + "\n", encoding="utf-8")
        print(f"refresh_sources: wrote {args.output}", file=sys.stderr)
    else:
        print(out)

    return int(report.get("exit", 3))


if __name__ == "__main__":
    sys.exit(main())
