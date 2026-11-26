#!/usr/bin/env python3
"""meta_skill.py — cross-distillation learning memory.

Inspired by Microsoft SkillOpt's meta_skill.py: maintains optimizer-side memory
distilled from prior distillation runs. Unlike SkillOpt (which uses LLM-driven
reflection), this version is mechanical — it records structured pipeline metrics
and surfaces them as guidance for future runs.

Usage:
  python3 meta_skill.py record --skill-dir <path> --metrics <metrics.json>
  python3 meta_skill.py query --industry <slug>
  python3 meta_skill.py guidance
  python3 meta_skill.py list

The memory file lives at {master_skill_dir}/meta_skill_memory.json.

Pure stdlib. macOS python3 out-of-the-box.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MEMORY_FILENAME = "meta_skill_memory.json"


def _memory_path() -> Path:
    return Path(__file__).resolve().parent.parent / MEMORY_FILENAME


def _load_memory() -> dict:
    path = _memory_path()
    if not path.exists():
        return {"version": 1, "runs": [], "lessons": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "runs": [], "lessons": []}


def _save_memory(data: dict) -> None:
    path = _memory_path()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def record_run(
    industry_slug: str,
    gate_verdict: str,
    gate_score: float,
    metrics: dict,
    lessons: list[str] | None = None,
    skill_dir: str = "",
) -> dict:
    """Record a distillation run's results."""
    memory = _load_memory()

    run_entry = {
        "industry_slug": industry_slug,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_verdict": gate_verdict,
        "gate_score": gate_score,
        "metrics": metrics,
        "skill_dir": skill_dir,
    }
    memory["runs"].append(run_entry)

    if lessons:
        for lesson in lessons:
            memory["lessons"].append({
                "date": run_entry["date"],
                "industry_slug": industry_slug,
                "lesson": lesson,
            })

    _save_memory(memory)
    return run_entry


def query_industry(slug: str) -> list[dict]:
    """Get all runs for a specific industry."""
    memory = _load_memory()
    return [r for r in memory["runs"] if r["industry_slug"] == slug]


def get_guidance() -> dict:
    """Derive guidance from accumulated distillation history."""
    memory = _load_memory()
    runs = memory["runs"]

    if not runs:
        return {"has_history": False, "message": "No prior distillation runs recorded."}

    total = len(runs)
    accepted = sum(1 for r in runs if r["gate_verdict"] == "accept")
    rejected = sum(1 for r in runs if r["gate_verdict"] == "reject")
    conditional = sum(1 for r in runs if r["gate_verdict"] == "conditional_accept")
    avg_score = sum(r["gate_score"] for r in runs) / total if total else 0

    common_failures: dict[str, int] = {}
    for r in runs:
        for fail in r.get("metrics", {}).get("critical_fails", []):
            label = fail if isinstance(fail, str) else fail.get("label", "unknown")
            common_failures[label] = common_failures.get(label, 0) + 1

    top_failures = sorted(common_failures.items(), key=lambda x: -x[1])[:5]

    recent_lessons = memory.get("lessons", [])[-10:]

    return {
        "has_history": True,
        "total_runs": total,
        "accept_rate": round(accepted / total, 2) if total else 0,
        "avg_score": round(avg_score, 3),
        "verdict_distribution": {
            "accept": accepted,
            "conditional_accept": conditional,
            "reject": rejected,
        },
        "top_failure_patterns": top_failures,
        "recent_lessons": [l["lesson"] for l in recent_lessons],
        "recommendation": _derive_recommendation(avg_score, top_failures, recent_lessons),
    }


def _derive_recommendation(avg_score: float, top_failures: list, lessons: list) -> str:
    parts = []
    if avg_score < 0.6:
        parts.append("Average gate score is low — consider spending more time on Phase 1 research depth.")
    if any("voice" in f[0].lower() for f in top_failures):
        parts.append("Voice DNA is a recurring failure — prioritize finding more first-hand quotes and industry dialogue samples.")
    if any("source" in f[0].lower() for f in top_failures):
        parts.append("Source quality is a recurring issue — focus on verified_primary sources in Phase 1.")
    if not parts:
        parts.append("Pipeline is performing well. Continue current approach.")
    return " ".join(parts)


def list_runs() -> list[dict]:
    """List all recorded runs (summary only)."""
    memory = _load_memory()
    return [
        {
            "industry_slug": r["industry_slug"],
            "date": r["date"],
            "verdict": r["gate_verdict"],
            "score": r["gate_score"],
        }
        for r in memory["runs"]
    ]


def main():
    parser = argparse.ArgumentParser(description="Cross-distillation learning memory")
    sub = parser.add_subparsers(dest="command")

    rec_p = sub.add_parser("record", help="Record a distillation run")
    rec_p.add_argument("--skill-dir", required=True)
    rec_p.add_argument("--metrics", required=True, help="Path to metrics JSON")

    query_p = sub.add_parser("query", help="Query runs for an industry")
    query_p.add_argument("--industry", required=True)

    sub.add_parser("guidance", help="Get pipeline guidance from history")
    sub.add_parser("list", help="List all runs")

    args = parser.parse_args()

    if args.command == "record":
        metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
        entry = record_run(
            industry_slug=metrics.get("industry_slug", "unknown"),
            gate_verdict=metrics.get("gate_verdict", "unknown"),
            gate_score=metrics.get("gate_score", 0.0),
            metrics=metrics,
            lessons=metrics.get("lessons"),
            skill_dir=args.skill_dir,
        )
        print(json.dumps(entry, indent=2, ensure_ascii=False))

    elif args.command == "query":
        runs = query_industry(args.industry)
        print(json.dumps(runs, indent=2, ensure_ascii=False))

    elif args.command == "guidance":
        g = get_guidance()
        print(json.dumps(g, indent=2, ensure_ascii=False))

    elif args.command == "list":
        runs = list_runs()
        print(json.dumps(runs, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
