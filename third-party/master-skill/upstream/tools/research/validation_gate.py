#!/usr/bin/env python3
"""validation_gate.py — accept/reject gate for Phase 4 quality verification.

Inspired by Microsoft SkillOpt's validation gate: after quality_check.py runs
the mechanical rubric, this gate aggregates results and makes an accept/reject
decision with structured reasoning.

Usage:
  python3 validation_gate.py gate --skill-dir <path>
  python3 validation_gate.py gate --skill-dir <path> --json
  python3 validation_gate.py gate --skill-dir <path> --threshold 0.7

The gate:
  1. Runs quality_check.py mechanical rubric (17 items)
  2. Computes weighted aggregate score
  3. Returns verdict: accept / reject / conditional_accept
  4. Lists specific failure reasons and improvement suggestions

Pure stdlib. macOS python3 out-of-the-box.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import quality_check as qc

ITEM_WEIGHTS = {
    1: 1.5,   # mental models count — core OS
    2: 1.0,   # mental model limits
    3: 1.0,   # playbook count
    4: 0.8,   # playbook cases
    5: 0.8,   # tool tiers
    6: 0.8,   # workflow senior diffs
    7: 1.2,   # voice DNA — identity-critical
    8: 0.6,   # source ratio
    9: 0.8,   # honest boundary specificity
    10: 0.6,  # time decay marks
    11: 1.0,  # agentic protocol dims
    12: 0.5,  # intellectual genealogy
    13: 0.5,  # meta.json fields
    14: 0.8,  # research files
    15: 0.3,  # synthesis exists
    16: 1.0,  # source manifest
    17: 0.5,  # claim verifier
}

STATUS_SCORES = {
    "pass": 1.0,
    "partial": 0.5,
    "fail": 0.0,
    "needs_subagent": 0.5,
    "skipped": 0.3,
}

DEFAULT_THRESHOLD = 0.70
CONDITIONAL_THRESHOLD = 0.55


def compute_gate_score(rubric_results: list[dict]) -> float:
    total_weight = 0.0
    weighted_score = 0.0
    for item in rubric_results:
        item_id = item.get("id", 0)
        status = item.get("status", "skipped")
        weight = ITEM_WEIGHTS.get(item_id, 0.5)
        score = STATUS_SCORES.get(status, 0.0)
        weighted_score += weight * score
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return round(weighted_score / total_weight, 4)


def classify_failures(rubric_results: list[dict]) -> dict:
    critical_fails = []
    non_critical_fails = []
    improvements = []

    for item in rubric_results:
        item_id = item.get("id", 0)
        status = item.get("status", "skipped")
        label = item.get("label", f"item_{item_id}")
        detail = item.get("detail", "")
        weight = ITEM_WEIGHTS.get(item_id, 0.5)

        if status == "fail":
            entry = {"id": item_id, "label": label, "detail": detail}
            if weight >= 1.0:
                critical_fails.append(entry)
            else:
                non_critical_fails.append(entry)
        elif status == "partial":
            improvements.append({"id": item_id, "label": label, "detail": detail})

    return {
        "critical_fails": critical_fails,
        "non_critical_fails": non_critical_fails,
        "improvements": improvements,
    }


def run_gate(skill_dir: Path, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Run quality_check rubric and apply the validation gate."""
    skill_dir = Path(skill_dir)

    try:
        skill_text = qc.load_skill_text(skill_dir)
    except qc.QCError as e:
        return {
            "verdict": "reject",
            "score": 0.0,
            "reason": f"Cannot load skill: {e}",
            "rubric_results": [],
            "failures": {"critical_fails": [], "non_critical_fails": [], "improvements": []},
        }

    meta = qc.load_meta(skill_dir)

    rubric_results = []
    checkers = [
        (1, "mental_models_count", lambda: qc.check_mental_models_count(skill_text, meta)),
        (2, "mental_model_limits", lambda: qc.check_mental_model_limits(skill_text)),
        (3, "playbook_count", lambda: qc.check_playbook_count(skill_text, meta)),
        (4, "playbook_cases", lambda: qc.check_playbook_cases(skill_text)),
        (5, "tool_tiers", lambda: qc.check_tool_tiers(skill_text, skill_dir)),
        (6, "workflow_senior_diffs", lambda: qc.check_workflow_senior_differences(skill_text)),
        (7, "voice_dna", lambda: qc.check_voice_dna(skill_text, skill_dir)),
        (8, "source_ratio", lambda: qc.check_source_ratio(skill_text, meta, skill_dir)),
        (9, "honest_boundaries", lambda: qc.check_honest_boundaries(skill_text)),
        (10, "time_decay", lambda: qc.check_time_decay_marks(skill_text)),
        (11, "agentic_protocol", lambda: qc.check_agentic_protocol_dims(skill_text, meta)),
    ]

    for item_id, label, checker in checkers:
        try:
            status, detail = checker()
        except Exception as exc:
            status, detail = "fail", f"checker error: {exc}"
        rubric_results.append({"id": item_id, "label": label, "status": status, "detail": detail})

    for item_id, label, check_fn in [
        (12, "intellectual_genealogy", lambda: _check_section_exists(skill_text, "智识谱系")),
        (13, "meta_json", lambda: _check_meta_fields(meta)),
        (14, "research_files", lambda: _check_research_files(skill_dir)),
        (15, "synthesis", lambda: _check_synthesis_exists(skill_dir)),
    ]:
        try:
            status, detail = check_fn()
        except Exception as exc:
            status, detail = "fail", f"checker error: {exc}"
        rubric_results.append({"id": item_id, "label": label, "status": status, "detail": detail})

    score = compute_gate_score(rubric_results)
    failures = classify_failures(rubric_results)

    if score >= threshold and not failures["critical_fails"]:
        verdict = "accept"
        reason = f"Score {score:.2f} >= {threshold:.2f}, no critical failures"
    elif score >= CONDITIONAL_THRESHOLD and not failures["critical_fails"]:
        verdict = "conditional_accept"
        reason = (
            f"Score {score:.2f} between {CONDITIONAL_THRESHOLD:.2f} and {threshold:.2f}. "
            f"{len(failures['improvements'])} items can be improved"
        )
    else:
        crit_labels = [f["label"] for f in failures["critical_fails"]]
        reason = f"Score {score:.2f} < {CONDITIONAL_THRESHOLD:.2f}" if score < CONDITIONAL_THRESHOLD else ""
        if crit_labels:
            reason += f"; critical failures: {', '.join(crit_labels)}"
        verdict = "reject"

    return {
        "verdict": verdict,
        "score": score,
        "threshold": threshold,
        "reason": reason.strip("; "),
        "rubric_results": rubric_results,
        "failures": failures,
        "summary": {
            "pass": sum(1 for r in rubric_results if r["status"] == "pass"),
            "partial": sum(1 for r in rubric_results if r["status"] == "partial"),
            "fail": sum(1 for r in rubric_results if r["status"] == "fail"),
            "skipped": sum(1 for r in rubric_results if r["status"] in ("skipped", "needs_subagent")),
        },
    }


def _check_section_exists(skill_text: str, heading: str) -> tuple[str, str]:
    import re
    if re.search(rf"##\s+(?:\d+\.\s+)?{re.escape(heading)}", skill_text):
        return "pass", f"{heading} section found"
    return "fail", f"{heading} section missing"


def _check_meta_fields(meta: dict) -> tuple[str, str]:
    required = ["name", "industry", "locale", "last_research_date"]
    missing = [f for f in required if f not in meta]
    if not missing:
        return "pass", f"meta.json has all required fields"
    return "partial", f"meta.json missing: {missing}"


def _check_research_files(skill_dir: Path) -> tuple[str, str]:
    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        return "fail", "references/research/ directory missing"
    expected = [f"0{i}" for i in range(1, 7)]
    found = []
    for f in research_dir.glob("*.md"):
        for e in expected:
            if f.name.startswith(e):
                found.append(e)
    missing = set(expected) - set(found)
    if not missing:
        return "pass", f"all 6 research tracks present"
    return "partial", f"missing tracks: {sorted(missing)}"


def _check_synthesis_exists(skill_dir: Path) -> tuple[str, str]:
    syn = skill_dir / "references" / "synthesis.md"
    if syn.exists() and syn.stat().st_size > 500:
        return "pass", "synthesis.md present and non-trivial"
    if syn.exists():
        return "partial", "synthesis.md exists but very small"
    return "fail", "synthesis.md missing"


def main():
    parser = argparse.ArgumentParser(description="Validation gate for Phase 4")
    sub = parser.add_subparsers(dest="command")

    gate_p = sub.add_parser("gate", help="Run validation gate")
    gate_p.add_argument("--skill-dir", required=True, help="Path to skill directory")
    gate_p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    gate_p.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "gate":
        result = run_gate(Path(args.skill_dir), threshold=args.threshold)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            v = result["verdict"].upper()
            s = result["summary"]
            print(f"Verdict: {v}  (score: {result['score']:.2f})")
            print(f"Rubric: {s['pass']} pass / {s['partial']} partial / {s['fail']} fail / {s['skipped']} skipped")
            if result["failures"]["critical_fails"]:
                print("Critical failures:")
                for f in result["failures"]["critical_fails"]:
                    print(f"  - [{f['id']}] {f['label']}: {f['detail']}")
            if result["failures"]["improvements"]:
                print("Improvements:")
                for f in result["failures"]["improvements"]:
                    print(f"  - [{f['id']}] {f['label']}: {f['detail']}")
            print(f"Reason: {result['reason']}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
