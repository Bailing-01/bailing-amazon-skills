#!/usr/bin/env python3
"""Validate tk-content-pipeline/v1 breakdown and script bundles.

Uses only the Python standard library so it can run in constrained Codex hosts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


PIPELINE_ID = "tk-content-pipeline/v1"
GROUPS = {
    "iteration": ("ITER", "原逻辑迭代"),
    "reshell": ("RESHELL", "原逻辑换壳"),
    "new_logic": ("NEWLOGIC", "新底层逻辑"),
}
VARIANTS = ("A", "B", "C")
PURPOSES = {"留人", "解释", "证明", "信任", "下单"}
HUMANITY_SCORE_FIELDS = ("humanity_score", "feed_score", "sales_score")


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def is_nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None


def get_video_identity(item: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
    canonical = item.get("video")
    if isinstance(canonical, dict):
        return canonical, True
    alias = item.get("source_video")
    if isinstance(alias, dict):
        return alias, False
    return None, False


def get_timeline(item: dict[str, Any]) -> tuple[list[Any] | None, bool]:
    canonical = item.get("timeline")
    if isinstance(canonical, list):
        return canonical, True
    step1 = item.get("step1_extraction")
    if isinstance(step1, dict) and isinstance(step1.get("timeline"), list):
        return step1["timeline"], False
    return None, False


def validate_breakdown(data: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ["root: expected object"], warnings

    if data.get("pipeline_id") != PIPELINE_ID:
        errors.append(f"pipeline_id: expected {PIPELINE_ID!r}")
    if data.get("artifact_type") != "breakdown_bundle":
        errors.append("artifact_type: expected 'breakdown_bundle'")
    if data.get("schema_version") != 1:
        errors.append("schema_version: expected integer 1")

    confirmation = data.get("batch_confirmation")
    if not isinstance(confirmation, dict):
        errors.append("batch_confirmation: required object")
    else:
        step2_confirmed = confirmation.get("step2_confirmed") is True
        canonical_progress = (
            confirmation.get("step1_confirmed") is True
            and confirmation.get("step2_completed") is True
        )
        if not step2_confirmed:
            errors.append(
                "batch_confirmation: require step2_confirmed=true; "
                "step2_completed alone is not user approval"
            )
        elif not canonical_progress:
            warnings.append(
                "batch_confirmation.step2_confirmed=true accepted for compatibility; "
                "canonical bundles should also record step1_confirmed=true + step2_completed=true"
            )

    videos = data.get("videos")
    if not isinstance(videos, list) or not videos:
        return errors + ["videos: expected non-empty array"], warnings

    seen_ids: set[str] = set()
    required_breakdown = (
        "underlying_logic",
        "hook_0_3s",
        "audience",
        "pain",
        "belief_and_action",
        "transferable_logic",
    )
    required_hook = (
        "original_copy",
        "optimized_copy",
        "key_changes",
        "intended_retention_effect",
    )

    for index, item in enumerate(videos):
        prefix = f"videos[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: expected object")
            continue

        identity, canonical_identity = get_video_identity(item)
        if identity is None:
            errors.append(f"{prefix}: missing video object (or compatibility alias source_video)")
            video_id = ""
        else:
            video_id = str(identity.get("video_id", "")).strip()
            if not video_id:
                errors.append(f"{prefix}.video.video_id: required")
            elif video_id in seen_ids:
                errors.append(f"{prefix}.video.video_id: duplicate {video_id!r}")
            else:
                seen_ids.add(video_id)
            if not canonical_identity:
                warnings.append(f"{prefix}: compatibility alias source_video used; canonical field is video")

        timeline, canonical_timeline = get_timeline(item)
        if not timeline:
            errors.append(f"{prefix}.timeline: required non-empty array")
        elif not canonical_timeline:
            warnings.append(
                f"{prefix}: compatibility alias step1_extraction.timeline used; canonical field is timeline"
            )

        breakdown = item.get("video_breakdown")
        if not isinstance(breakdown, dict):
            errors.append(f"{prefix}.video_breakdown: required object")
            continue
        for field in required_breakdown:
            if not is_nonempty(breakdown.get(field)):
                errors.append(f"{prefix}.video_breakdown.{field}: required non-empty value")

        hook = breakdown.get("hook_0_3s")
        if isinstance(hook, dict):
            for field in required_hook:
                if not is_nonempty(hook.get(field)):
                    errors.append(f"{prefix}.video_breakdown.hook_0_3s.{field}: required")

    return errors, warnings


def expected_script_id(video_id: str, group: str, variant: str) -> str:
    group_code = GROUPS[group][0]
    return f"SC-{video_id}-{group_code}-{variant}"


def validate_script(data: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ["root: expected object"], warnings

    if data.get("pipeline_id") != PIPELINE_ID:
        errors.append(f"pipeline_id: expected {PIPELINE_ID!r}")
    if data.get("artifact_type") != "script_bundle":
        errors.append("artifact_type: expected 'script_bundle'")
    if data.get("schema_version") != 1:
        errors.append("schema_version: expected integer 1")
    if not is_nonempty(data.get("generated_at")):
        errors.append("generated_at: required")
    if not is_nonempty(data.get("source_breakdown")):
        errors.append("source_breakdown: required")

    videos = data.get("videos")
    if not isinstance(videos, list) or not videos:
        return errors + ["videos: expected non-empty array"], warnings

    seen_video_ids: set[str] = set()
    all_script_ids: set[str] = set()
    for video_index, video in enumerate(videos):
        prefix = f"videos[{video_index}]"
        if not isinstance(video, dict):
            errors.append(f"{prefix}: expected object")
            continue
        video_id = str(video.get("video_id", "")).strip()
        if not video_id:
            errors.append(f"{prefix}.video_id: required")
        elif video_id in seen_video_ids:
            errors.append(f"{prefix}.video_id: duplicate {video_id!r}")
        else:
            seen_video_ids.add(video_id)

        source_duration = video.get("source_duration_seconds")
        if source_duration is not None and not isinstance(source_duration, (int, float)):
            errors.append(f"{prefix}.source_duration_seconds: expected number when present")

        scripts = video.get("scripts")
        if not isinstance(scripts, list):
            errors.append(f"{prefix}.scripts: expected array")
            continue
        if len(scripts) not in (6, 9):
            errors.append(f"{prefix}.scripts: expected 6 or 9, got {len(scripts)}")
        expected_variants = ("A", "B") if len(scripts) == 6 else VARIANTS

        by_combo: dict[tuple[str, str], dict[str, Any]] = {}
        group_directions: dict[str, list[str]] = {group: [] for group in GROUPS}
        group_voiceovers: dict[str, list[str]] = {group: [] for group in GROUPS}
        iteration_invariants: list[str] = []
        video_voiceovers: set[str] = set()
        video_original_hooks: set[str] = set()

        for script_index, script in enumerate(scripts):
            sp = f"{prefix}.scripts[{script_index}]"
            if not isinstance(script, dict):
                errors.append(f"{sp}: expected object")
                continue
            group = script.get("group")
            variant = script.get("variant")
            if group not in GROUPS:
                errors.append(f"{sp}.group: expected one of {sorted(GROUPS)}")
                continue
            if variant not in VARIANTS:
                errors.append(f"{sp}.variant: expected A, B, or C")
                continue
            combo = (group, variant)
            if combo in by_combo:
                errors.append(f"{sp}: duplicate group/variant {group}/{variant}")
            by_combo[combo] = script

            route = script.get("route")
            if route != GROUPS[group][1]:
                errors.append(f"{sp}.route: expected {GROUPS[group][1]!r} for group {group!r}")

            script_id = str(script.get("script_id", "")).strip()
            expected_id = expected_script_id(video_id, group, variant)
            if script_id != expected_id:
                errors.append(f"{sp}.script_id: expected {expected_id!r}, got {script_id!r}")
            if script_id in all_script_ids:
                errors.append(f"{sp}.script_id: duplicate {script_id!r}")
            elif script_id:
                all_script_ids.add(script_id)

            axes = {
                "test_variable": str(script.get("test_variable", "")).strip(),
                "shell_direction": str(script.get("shell_direction", "")).strip(),
                "new_purchase_path": str(script.get("new_purchase_path", "")).strip(),
            }
            required_axis = {
                "iteration": "test_variable",
                "reshell": "shell_direction",
                "new_logic": "new_purchase_path",
            }[group]
            for axis, value in axes.items():
                if axis == required_axis and not value:
                    errors.append(f"{sp}.{axis}: required for group {group}")
                if axis != required_axis and value:
                    errors.append(f"{sp}.{axis}: must be empty for group {group}")
            if axes[required_axis]:
                group_directions[group].append(normalize_text(axes[required_axis]))

            invariants = script.get("fixed_invariants")
            if not isinstance(invariants, list) or not invariants or not all(is_nonempty(v) for v in invariants):
                errors.append(f"{sp}.fixed_invariants: expected non-empty string array")
            elif group == "iteration":
                iteration_invariants.append(normalize_text("|".join(map(str, invariants))))

            hook = script.get("hook_comparison")
            hook_fields = (
                "original_hook",
                "optimized_hook",
                "key_changes",
                "intended_retention_effect",
            )
            if not isinstance(hook, dict):
                errors.append(f"{sp}.hook_comparison: required object")
            else:
                for field in hook_fields:
                    if not is_nonempty(hook.get(field)):
                        errors.append(f"{sp}.hook_comparison.{field}: required")
                original_hook = normalize_text(hook.get("original_hook"))
                optimized_hook = normalize_text(hook.get("optimized_hook"))
                if original_hook:
                    video_original_hooks.add(original_hook)
                if (
                    original_hook == optimized_hook
                    and "保持" not in str(hook.get("key_changes", ""))
                ):
                    errors.append(
                        f"{sp}.hook_comparison.key_changes: identical hooks must explicitly state Hook 保持不变"
                    )

            segments = script.get("segments")
            segment_voiceovers: list[str] = []
            last_end: float | None = None
            if not isinstance(segments, list) or len(segments) < 2:
                errors.append(f"{sp}.segments: expected at least 2 segments")
            else:
                for segment_index, segment in enumerate(segments):
                    segp = f"{sp}.segments[{segment_index}]"
                    if not isinstance(segment, dict):
                        errors.append(f"{segp}: expected object")
                        continue
                    start = segment.get("start_second")
                    end = segment.get("end_second")
                    if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                        errors.append(f"{segp}: start_second/end_second must be numbers")
                    else:
                        if start < 0 or end <= start:
                            errors.append(f"{segp}: require 0 <= start_second < end_second")
                        if last_end is not None:
                            if start < last_end:
                                errors.append(f"{segp}: overlaps previous segment")
                            elif start - last_end > 0.5:
                                warnings.append(f"{segp}: timeline gap exceeds 0.5 seconds")
                        last_end = float(end)
                    voiceover = segment.get("voiceover")
                    if not is_nonempty(voiceover):
                        errors.append(f"{segp}.voiceover: required")
                    else:
                        segment_voiceovers.append(str(voiceover))
                    if not is_nonempty(segment.get("visual_action")):
                        errors.append(f"{segp}.visual_action: required")
                    if segment.get("purpose") not in PURPOSES:
                        errors.append(f"{segp}.purpose: invalid")

            final_voiceover = str(script.get("final_voiceover", "")).strip()
            if not final_voiceover:
                errors.append(f"{sp}.final_voiceover: required")
            elif normalize_text("".join(segment_voiceovers)) != normalize_text(final_voiceover):
                errors.append(f"{sp}.final_voiceover: must equal concatenated segment voiceovers")
            normalized_final = normalize_text(final_voiceover)
            if isinstance(hook, dict):
                optimized_hook = normalize_text(hook.get("optimized_hook"))
                if optimized_hook and normalized_final and not normalized_final.startswith(optimized_hook):
                    errors.append(f"{sp}.final_voiceover: must start with hook_comparison.optimized_hook")
            if normalized_final in video_voiceovers and normalized_final:
                errors.append(f"{sp}.final_voiceover: duplicate of another version")
            elif normalized_final:
                video_voiceovers.add(normalized_final)
                group_voiceovers[group].append(normalized_final)

            humanity_review = script.get("humanity_review")
            if not isinstance(humanity_review, dict):
                warnings.append(f"{sp}.humanity_review: required for strict human-style delivery")
            else:
                status = humanity_review.get("status")
                if status not in {"approved", "rejected"}:
                    errors.append(f"{sp}.humanity_review.status: expected approved or rejected")
                elif status != "approved":
                    warnings.append(f"{sp}.humanity_review.status: final script is not approved")
                for field in HUMANITY_SCORE_FIELDS:
                    score = humanity_review.get(field)
                    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 5:
                        errors.append(f"{sp}.humanity_review.{field}: expected number from 0 to 5")
                    elif score < 4:
                        warnings.append(f"{sp}.humanity_review.{field}: score below delivery threshold 4")
                for field in ("ai_tells", "read_aloud_issues"):
                    value = humanity_review.get(field)
                    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                        errors.append(f"{sp}.humanity_review.{field}: expected string array")
                rounds = humanity_review.get("revision_rounds")
                if not isinstance(rounds, int) or isinstance(rounds, bool) or not 0 <= rounds <= 2:
                    errors.append(f"{sp}.humanity_review.revision_rounds: expected integer from 0 to 2")
                if not isinstance(humanity_review.get("voice_evidence_gap"), bool):
                    errors.append(f"{sp}.humanity_review.voice_evidence_gap: expected boolean")

            estimated = script.get("estimated_duration_seconds")
            if not isinstance(estimated, (int, float)) or estimated <= 0:
                errors.append(f"{sp}.estimated_duration_seconds: expected positive number")
            elif last_end is not None and abs(float(estimated) - last_end) > 1:
                errors.append(f"{sp}.estimated_duration_seconds: must match final segment end within 1 second")
            if (
                isinstance(source_duration, (int, float))
                and source_duration > 0
                and isinstance(estimated, (int, float))
                and abs(float(estimated) - float(source_duration)) / float(source_duration) > 0.2
                and not str(script.get("duration_note", "")).strip()
            ):
                errors.append(f"{sp}.duration_note: required when duration differs from source by over 20%")

        expected_combos = {(group, variant) for group in GROUPS for variant in expected_variants}
        missing = expected_combos - set(by_combo)
        extra = set(by_combo) - expected_combos
        if missing:
            errors.append(f"{prefix}.scripts: missing combinations {sorted(missing)}")
        if extra:
            errors.append(f"{prefix}.scripts: unexpected combinations {sorted(extra)}")

        expected_per_group = len(expected_variants)
        for group, directions in group_directions.items():
            if len(directions) == expected_per_group and len(set(directions)) != expected_per_group:
                errors.append(
                    f"{prefix}.scripts: {group} directions must be {expected_per_group} distinct values"
                )
        if len(iteration_invariants) == expected_per_group and len(set(iteration_invariants)) != 1:
            errors.append(f"{prefix}.scripts: iteration variants fixed_invariants must be identical")
        if len(video_original_hooks) > 1:
            errors.append(f"{prefix}.scripts: all hook_comparison.original_hook values must preserve one source Hook")

        for group, voiceovers in group_voiceovers.items():
            if len(voiceovers) != expected_per_group:
                continue
            for left in range(expected_per_group):
                for right in range(left + 1, expected_per_group):
                    ratio = SequenceMatcher(None, voiceovers[left], voiceovers[right]).ratio()
                    if group == "iteration" and ratio < 0.45:
                        warnings.append(
                            f"{prefix}.scripts: iteration pair {VARIANTS[left]}/{VARIANTS[right]} "
                            f"similarity {ratio:.3f} suggests variable pollution"
                        )
                    if ratio > 0.985:
                        warnings.append(
                            f"{prefix}.scripts: {group} pair {VARIANTS[left]}/{VARIANTS[right]} "
                            f"similarity {ratio:.3f} suggests insufficient difference"
                        )

    return errors, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Bundle JSON path")
    parser.add_argument(
        "--kind",
        choices=("auto", "breakdown", "script"),
        default="auto",
        help="Bundle type to validate",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat semantic-distance and timeline warnings as failures",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with args.input.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)], "warnings": []}, ensure_ascii=False, indent=2))
        return 1

    kind = args.kind
    if kind == "auto":
        artifact_type = data.get("artifact_type") if isinstance(data, dict) else None
        kind = {"breakdown_bundle": "breakdown", "script_bundle": "script"}.get(artifact_type, "")
        if not kind:
            print(
                json.dumps(
                    {"valid": False, "errors": ["cannot infer kind from artifact_type"], "warnings": []},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

    errors, warnings = validate_breakdown(data) if kind == "breakdown" else validate_script(data)
    valid = not errors and not (args.strict and warnings)
    result = {
        "valid": valid,
        "kind": kind,
        "strict": args.strict,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
