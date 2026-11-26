#!/usr/bin/env python3
from __future__ import annotations
"""update_skill.py — increment & decay tooling for {industry}-master skills.

Reads target skill's meta.json (last_research_date), computes time-decay age,
and outputs a refresh plan based on Phase 0C decision table:

  < 1 month   : reject (too recent)
  1-3 months  : refresh Tools (02) + Workflows (03) + Sources (05 latest)
  3-6 months  : + Figures (01 recent moves) + Glossary (06 standards)
  6-12 months : recommend synthesis (Phase 2) re-extract on refreshed tracks
  ≥ 12 months : full re-run all 6 tracks + synthesis re-extract (with archive)

Optionally archives old references/research/ to references/research/archive/{date}/
so the agent can re-run targeted tracks without losing the previous version.

Usage:
  python3 update_skill.py plan --skill-dir ./output
  python3 update_skill.py plan --skill-dir ./output --json
  python3 update_skill.py archive --skill-dir ./output
  python3 update_skill.py mark-in-progress --skill-dir ./output --tracks tools,workflows
  python3 update_skill.py finalize --skill-dir ./output

Pure stdlib. Atomic writes. Fail loud on missing meta.json.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

# Per-track decay risk + refresh trigger thresholds (months)
# Aligned with SKILL.md Phase 0C decision table + extraction-framework.md decay rates
TRACK_DECAY = {
    "01-figures":   {"risk": "medium", "refresh_at_months": 6,  "label": "行业大佬 (recent moves)"},
    "02-tools":     {"risk": "high",   "refresh_at_months": 3,  "label": "工具地图"},
    "03-workflows": {"risk": "high",   "refresh_at_months": 3,  "label": "工作流 / SOP"},
    "04-canon":     {"risk": "low",    "refresh_at_months": 24, "label": "知识正典"},
    "05-sources":   {"risk": "high",   "refresh_at_months": 3,  "label": "信息源 (latest section)"},
    "06-glossary":  {"risk": "medium", "refresh_at_months": 6,  "label": "术语 + 标准 (standards section)"},
}


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_meta(skill_dir: Path) -> dict:
    meta_path = skill_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json not found at {meta_path}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def write_meta(skill_dir: Path, meta: dict) -> None:
    meta_path = skill_dir / "meta.json"
    atomic_write(meta_path, json.dumps(meta, indent=2, ensure_ascii=False) + "\n")


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def months_between(d1: date, d2: date) -> int:
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def compute_plan(meta: dict, today: date | None = None) -> dict:
    """Compute refresh plan based on last_research_date and per-track decay."""
    today = today or date.today()
    try:
        last = parse_date(meta["last_research_date"])
    except (KeyError, ValueError) as e:
        raise ValueError(f"meta.json missing/invalid last_research_date: {e}")

    age_months = months_between(last, today)

    if age_months < 1:
        return {
            "status": "rejected",
            "reason": f"last_research_date {last.isoformat()} is only {age_months} months old. Refusing refresh — too recent.",
            "age_months": age_months,
            "tracks_to_refresh": [],
            "tracks_to_keep": list(TRACK_DECAY.keys()),
        }

    tracks_to_refresh = []
    tracks_to_keep = []
    for track, conf in TRACK_DECAY.items():
        if age_months >= conf["refresh_at_months"]:
            tracks_to_refresh.append({
                "track": track,
                "label": conf["label"],
                "decay_risk": conf["risk"],
                "trigger_months": conf["refresh_at_months"],
                "actual_age_months": age_months,
            })
        else:
            tracks_to_keep.append({
                "track": track,
                "label": conf["label"],
                "decay_risk": conf["risk"],
                "remaining_until_refresh": conf["refresh_at_months"] - age_months,
            })

    if age_months >= 12:
        full_rerun = True
        synthesis_re_extract = True
    elif age_months >= 6:
        full_rerun = False
        synthesis_re_extract = True
    else:
        full_rerun = False
        synthesis_re_extract = False

    return {
        "status": "ready",
        "last_research_date": last.isoformat(),
        "today": today.isoformat(),
        "age_months": age_months,
        "full_rerun_recommended": full_rerun,
        "synthesis_re_extract_recommended": synthesis_re_extract,
        "tracks_to_refresh": tracks_to_refresh,
        "tracks_to_keep": tracks_to_keep,
    }


def cmd_plan(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    meta = read_meta(skill_dir)
    plan = compute_plan(meta)

    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0 if plan["status"] == "ready" else 1

    if plan["status"] == "rejected":
        print(f"✗ {plan['reason']}")
        return 1

    print(f"📂 skill:                 {skill_dir.name}")
    print(f"📅 last_research_date:    {plan['last_research_date']}")
    print(f"📅 today:                 {plan['today']}")
    print(f"⏱  age:                   {plan['age_months']} months")
    print()

    if plan["tracks_to_refresh"]:
        print(f"🔄 Refresh ({len(plan['tracks_to_refresh'])} tracks):")
        for t in plan["tracks_to_refresh"]:
            print(f"  • {t['track']}  [{t['decay_risk']:6s}]  {t['label']}")
            print(f"      trigger: ≥ {t['trigger_months']} months  ·  actual: {t['actual_age_months']} months")
    else:
        print("✓ No tracks need refresh — all are within their decay window.")

    print()
    if plan["tracks_to_keep"]:
        print(f"💾 Keep ({len(plan['tracks_to_keep'])} tracks):")
        for t in plan["tracks_to_keep"]:
            print(f"  • {t['track']}  [{t['decay_risk']:6s}]  {t['label']}  (refresh in {t['remaining_until_refresh']} months)")

    print()
    if plan["full_rerun_recommended"]:
        print("⚠ ≥12 months — recommend full Phase 1 re-run (all 6 tracks + synthesis re-extract)")
    elif plan["synthesis_re_extract_recommended"]:
        print("⚠ ≥6 months — recommend synthesis (Phase 2) re-extract on refreshed tracks")

    return 0


def cmd_archive(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    research = skill_dir / "references" / "research"
    if not research.exists():
        print(f"✗ research dir not found: {research}", file=sys.stderr)
        return 1

    archive_dir = research / "archive" / date.today().isoformat()
    if archive_dir.exists():
        print(f"⚠ archive already exists at {archive_dir}, will not overwrite", file=sys.stderr)
        return 1

    archive_dir.mkdir(parents=True)
    moved = 0
    for p in research.iterdir():
        if p.is_dir() and p.name == "archive":
            continue
        if p.is_file():
            shutil.copy2(p, archive_dir / p.name)
            moved += 1

    print(f"✓ archived {moved} files to {archive_dir.relative_to(skill_dir)}")
    return 0


def cmd_mark_in_progress(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    meta = read_meta(skill_dir)

    tracks = [t.strip() for t in args.tracks.split(",") if t.strip()] if args.tracks else []
    valid_tracks = set(TRACK_DECAY.keys())
    short_to_full = {t.split("-", 1)[1]: t for t in valid_tracks}
    expanded = []
    for t in tracks:
        if t in valid_tracks:
            expanded.append(t)
        elif t in short_to_full:
            expanded.append(short_to_full[t])
        else:
            print(f"✗ unknown track: {t}. Valid: {sorted(valid_tracks)}", file=sys.stderr)
            return 1

    meta["update_in_progress"] = True
    meta["update_started_at"] = datetime.now(timezone.utc).isoformat()
    meta["update_tracks"] = expanded

    write_meta(skill_dir, meta)
    print(f"✓ marked update in progress, tracks: {expanded}")
    return 0


def cmd_finalize(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    meta = read_meta(skill_dir)

    if not meta.get("update_in_progress"):
        print("⚠ skill not in update mode (update_in_progress not set)", file=sys.stderr)

    today = date.today().isoformat()
    meta["last_research_date"] = today
    meta["update_in_progress"] = False
    refreshed_tracks = meta.pop("update_tracks", [])
    meta.pop("update_started_at", None)

    cl = meta.setdefault("changelog", [])
    version_str = meta.get("version", "unknown")
    cl.append({
        "version": version_str,
        "date": today,
        "what": f"Increment update — refreshed tracks: {', '.join(refreshed_tracks) if refreshed_tracks else 'none recorded'}",
    })

    write_meta(skill_dir, meta)
    print(f"✓ finalize complete — last_research_date: {today}")
    return 0


def cmd_schedule(args) -> int:
    """生成定时检查的 launchd plist (macOS) 或 cron 行 (Linux).

    检查频率按 skill 中最高 decay 模块决定:
    - high decay (3 月) → 每周检查一次, 第 12 周时提醒该刷
    - medium (6 月)     → 每月检查一次
    - low (24 月)       → 每季度检查一次
    """
    skill_dir = Path(args.skill_dir).resolve()
    meta = read_meta(skill_dir)
    skill_name = meta.get("name", skill_dir.name)

    # 找最高 decay (= refresh_at_months 最小)
    min_refresh = min(c["refresh_at_months"] for c in TRACK_DECAY.values())
    if min_refresh <= 3:
        check_period = "weekly"
        cron_expr = "0 9 * * 1"  # 每周一 9:00
        plist_interval_seconds = 7 * 24 * 60 * 60
    elif min_refresh <= 6:
        check_period = "monthly"
        cron_expr = "0 9 1 * *"  # 每月 1 号 9:00
        plist_interval_seconds = 30 * 24 * 60 * 60
    else:
        check_period = "quarterly"
        cron_expr = "0 9 1 */3 *"  # 每 3 月 1 号 9:00
        plist_interval_seconds = 90 * 24 * 60 * 60

    plan_cmd = (
        f"python3 {Path(__file__).resolve()} plan --skill-dir {skill_dir} --json"
    )

    label = f"com.master-skill.{skill_dir.name}.refresh"
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>{plan_cmd} | /usr/bin/osascript -e 'on run argv
  display notification (item 1 of argv) with title "{skill_name} 刷新检查"
end run' "$(cat)"</string>
  </array>
  <key>StartInterval</key>
  <integer>{plist_interval_seconds}</integer>
  <key>RunAtLoad</key>
  <false/>
  <key>StandardOutPath</key>
  <string>{Path.home()}/.master-skill-refresh.log</string>
  <key>StandardErrorPath</key>
  <string>{Path.home()}/.master-skill-refresh.err</string>
</dict>
</plist>
"""

    if args.write:
        atomic_write(plist_path, plist_content)
        print(f"✓ launchd plist 写入: {plist_path}")
        print()
        print("启用 (一次性):")
        print(f"  launchctl load {plist_path}")
        print()
        print("停用:")
        print(f"  launchctl unload {plist_path}")
        print(f"  rm {plist_path}")
    else:
        print("# === macOS launchd plist ===")
        print(f"# 写入: ~/Library/LaunchAgents/{label}.plist")
        print()
        print(plist_content)
        print(f"# === Linux cron 行 (装到 crontab -e) ===")
        print(f"{cron_expr} {plan_cmd}")
        print()
        print(f"# 检查频率: {check_period} (基于最高 decay = {min_refresh} 月)")
        print(f"# 用 --write 把 plist 直接写到磁盘.")
    return 0


def cmd_apply_patch(args) -> int:
    """Apply a structured patch to SKILL.md with slow-update protection.

    Inspired by SkillOpt's ReflACT Update stage. Uses patch_editor.py for
    atomic edit operations that respect SLOW_UPDATE-protected regions.
    """
    skill_dir = Path(args.skill_dir).resolve()
    skill_md = skill_dir / "SKILL.md"
    patch_path = Path(args.patch).resolve()

    if not skill_md.exists():
        print(f"✗ SKILL.md not found at {skill_md}", file=sys.stderr)
        return 1
    if not patch_path.exists():
        print(f"✗ patch file not found: {patch_path}", file=sys.stderr)
        return 1

    # Import patch_editor from sibling module
    tools_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(tools_dir))
    import patch_editor

    result = patch_editor.apply_patch_from_file(
        skill_md, patch_path, dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"📂 skill: {skill_dir.name}")
        print(f"Applied: {result['applied']}/{result['total_edits']}")
        print(f"Skipped (protected): {result['skipped_protected']}")
        print(f"Skipped (other): {result['skipped_other']}")
        print(f"Errors: {result['errors']}")
        if args.dry_run:
            print("(dry-run — no files changed)")
        for r in result["reports"]:
            status_icon = "✓" if r["status"].startswith("applied") else "⊘"
            print(f"  {status_icon} [{r['index']}] {r['op']}: {r['status']}")

    return 0 if result["errors"] == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="update / decay tool for master skills")
    sub = parser.add_subparsers(dest="action", required=True)

    p_plan = sub.add_parser("plan", help="Compute refresh plan based on last_research_date")
    p_plan.add_argument("--skill-dir", required=True)
    p_plan.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable")

    p_archive = sub.add_parser("archive", help="Archive existing research/ to research/archive/{today}/")
    p_archive.add_argument("--skill-dir", required=True)

    p_mark = sub.add_parser("mark-in-progress", help="Set update_in_progress + tracks list in meta.json")
    p_mark.add_argument("--skill-dir", required=True)
    p_mark.add_argument("--tracks", required=True,
                        help="Comma-separated tracks: figures,tools,workflows,canon,sources,glossary")

    p_finalize = sub.add_parser("finalize", help="Mark update done, bump last_research_date, append changelog")
    p_finalize.add_argument("--skill-dir", required=True)

    p_schedule = sub.add_parser("schedule", help="生成定时刷新检查的 launchd plist + cron 命令")
    p_schedule.add_argument("--skill-dir", required=True)
    p_schedule.add_argument("--write", action="store_true",
                             help="把 plist 直接写到 ~/Library/LaunchAgents/ (默认只打印)")

    p_patch = sub.add_parser("apply-patch",
                              help="Apply structured edits to SKILL.md with slow-update protection")
    p_patch.add_argument("--skill-dir", required=True)
    p_patch.add_argument("--patch", required=True, help="Path to patch.json (SkillOpt edit format)")
    p_patch.add_argument("--dry-run", action="store_true")
    p_patch.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.action == "plan":
        sys.exit(cmd_plan(args))
    elif args.action == "archive":
        sys.exit(cmd_archive(args))
    elif args.action == "mark-in-progress":
        sys.exit(cmd_mark_in_progress(args))
    elif args.action == "finalize":
        sys.exit(cmd_finalize(args))
    elif args.action == "schedule":
        sys.exit(cmd_schedule(args))
    elif args.action == "apply-patch":
        sys.exit(cmd_apply_patch(args))


if __name__ == "__main__":
    main()
