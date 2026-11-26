#!/usr/bin/env python3
"""patch_editor.py — structured edit operations with slow-update protection.

Inspired by Microsoft SkillOpt's ReflACT Update stage. Provides 4 atomic edit
operations (append / insert_after / replace / delete) that respect
SLOW_UPDATE-protected regions in skill markdown files.

Usage:
  python3 patch_editor.py apply --skill <SKILL.md> --patch <patch.json>
  python3 patch_editor.py apply --skill <SKILL.md> --patch <patch.json> --dry-run
  python3 patch_editor.py check-region --skill <SKILL.md> --target "some text"

The patch JSON schema:
  {
    "reasoning": "why these edits address the issue",
    "edits": [
      {"op": "append",       "content": "markdown to add at end"},
      {"op": "insert_after", "target": "heading/text to insert after", "content": "markdown"},
      {"op": "replace",      "target": "exact text to replace",       "content": "replacement"},
      {"op": "delete",       "target": "exact text to remove"}
    ]
  }

Pure stdlib. macOS python3 out-of-the-box.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SLOW_UPDATE_START = "<!-- SLOW_UPDATE_START -->"
SLOW_UPDATE_END = "<!-- SLOW_UPDATE_END -->"


def is_in_slow_update_region(skill: str, target: str) -> bool:
    target_idx = skill.find(target)
    if target_idx == -1:
        return False
    search_from = 0
    while True:
        start_idx = skill.find(SLOW_UPDATE_START, search_from)
        if start_idx == -1:
            return False
        end_idx = skill.find(SLOW_UPDATE_END, start_idx)
        if end_idx == -1:
            return False
        region_end = end_idx + len(SLOW_UPDATE_END)
        if start_idx <= target_idx < region_end:
            return True
        search_from = region_end


def strip_slow_update_markers(text: str) -> str:
    return text.replace(SLOW_UPDATE_START, "").replace(SLOW_UPDATE_END, "")


def _apply_single_edit(skill: str, edit: dict) -> tuple[str, dict]:
    op = edit.get("op", "")
    content = strip_slow_update_markers(edit.get("content", "").strip())
    target = edit.get("target", "")
    report = {
        "op": op,
        "target": target[:200],
        "content_preview": content[:200],
        "status": "unknown",
    }

    if target and is_in_slow_update_region(skill, target):
        report["status"] = "skipped_protected_slow_update_region"
        return skill, report

    if op == "append":
        su_start = skill.find(SLOW_UPDATE_START)
        if su_start != -1:
            before = skill[:su_start].rstrip()
            after = skill[su_start:]
            report["status"] = "applied_append_before_slow_update"
            return before + "\n\n" + content + "\n\n" + after, report
        report["status"] = "applied_append"
        return skill.rstrip() + "\n\n" + content + "\n", report

    if op == "insert_after":
        if not target or target not in skill:
            su_start = skill.find(SLOW_UPDATE_START)
            if su_start != -1:
                before = skill[:su_start].rstrip()
                after = skill[su_start:]
                report["status"] = "fallback_insert_before_slow_update"
                return before + "\n\n" + content + "\n\n" + after, report
            report["status"] = "fallback_append"
            return skill.rstrip() + "\n\n" + content + "\n", report
        idx = skill.index(target) + len(target)
        newline = skill.find("\n", idx)
        insert_at = newline + 1 if newline != -1 else len(skill)
        report["status"] = "applied_insert_after"
        return skill[:insert_at] + "\n" + content + "\n" + skill[insert_at:], report

    if op == "replace":
        if not target:
            report["status"] = "skipped_replace_missing_target"
            return skill, report
        if target not in skill:
            report["status"] = "skipped_replace_target_not_found"
            return skill, report
        report["status"] = "applied_replace"
        return skill.replace(target, content, 1), report

    if op == "delete":
        if not target:
            report["status"] = "skipped_delete_missing_target"
            return skill, report
        if target not in skill:
            report["status"] = "skipped_delete_target_not_found"
            return skill, report
        report["status"] = "applied_delete"
        return skill.replace(target, "", 1), report

    report["status"] = "skipped_unknown_op"
    return skill, report


def apply_patch(skill: str, patch: dict) -> tuple[str, list[dict]]:
    """Apply a patch (list of edits) sequentially. Returns (updated_skill, reports)."""
    edits = patch.get("edits", [])
    reports: list[dict] = []
    for idx, edit in enumerate(edits, 1):
        try:
            skill, report = _apply_single_edit(skill, edit)
            report["index"] = idx
        except Exception as exc:
            report = {
                "index": idx, "op": "", "target": "", "content_preview": "",
                "status": "error", "error": str(exc),
            }
        reports.append(report)
    return skill, reports


def apply_patch_from_file(skill_path: Path, patch_path: Path, dry_run: bool = False) -> dict:
    """Load skill + patch from disk, apply, optionally write back."""
    skill_text = skill_path.read_text(encoding="utf-8")
    patch = json.loads(patch_path.read_text(encoding="utf-8"))

    updated, reports = apply_patch(skill_text, patch)

    applied = sum(1 for r in reports if r["status"].startswith("applied"))
    skipped = sum(1 for r in reports if r["status"].startswith("skipped"))
    errors = sum(1 for r in reports if r["status"] == "error")

    if not dry_run and applied > 0:
        skill_path.write_text(updated, encoding="utf-8")

    return {
        "skill_path": str(skill_path),
        "dry_run": dry_run,
        "total_edits": len(reports),
        "applied": applied,
        "skipped_protected": sum(1 for r in reports if "protected" in r["status"]),
        "skipped_other": skipped - sum(1 for r in reports if "protected" in r["status"]),
        "errors": errors,
        "reports": reports,
    }


def main():
    parser = argparse.ArgumentParser(description="Patch editor with slow-update protection")
    sub = parser.add_subparsers(dest="command")

    apply_p = sub.add_parser("apply", help="Apply a patch to a skill file")
    apply_p.add_argument("--skill", required=True, help="Path to SKILL.md")
    apply_p.add_argument("--patch", required=True, help="Path to patch.json")
    apply_p.add_argument("--dry-run", action="store_true", help="Don't write changes")
    apply_p.add_argument("--json", action="store_true", help="JSON output")

    check_p = sub.add_parser("check-region", help="Check if text is in slow-update region")
    check_p.add_argument("--skill", required=True, help="Path to SKILL.md")
    check_p.add_argument("--target", required=True, help="Text to check")

    args = parser.parse_args()

    if args.command == "apply":
        result = apply_patch_from_file(
            Path(args.skill), Path(args.patch), dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Applied: {result['applied']}/{result['total_edits']}")
            print(f"Skipped (protected): {result['skipped_protected']}")
            print(f"Skipped (other): {result['skipped_other']}")
            print(f"Errors: {result['errors']}")
            if result['dry_run']:
                print("(dry-run — no files changed)")

    elif args.command == "check-region":
        skill_text = Path(args.skill).read_text(encoding="utf-8")
        in_region = is_in_slow_update_region(skill_text, args.target)
        print(f"In slow-update region: {in_region}")
        sys.exit(0 if not in_region else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
