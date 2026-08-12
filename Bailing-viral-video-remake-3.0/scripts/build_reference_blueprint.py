#!/usr/bin/env python3
"""Compress a completed reference analysis into a reusable recreation blueprint."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Analysis JSON must contain an object")
    return data


def text_items(items: Any, key: str = "text") -> list[str]:
    if not isinstance(items, list):
        return []
    values: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get(key):
            values.append(str(item[key]))
    return values


def shot_structure(shots: Any) -> list[dict[str, Any]]:
    if not isinstance(shots, list):
        return []
    result: list[dict[str, Any]] = []
    for shot in shots:
        if not isinstance(shot, dict):
            continue
        start = shot.get("start")
        end = shot.get("end")
        role = shot.get("attention_job") or shot.get("purpose") or ""
        result.append({
            "start": start,
            "end": end,
            "role": role,
            "framing": shot.get("framing", ""),
            "camera": shot.get("camera", ""),
            "subject": shot.get("subject", ""),
            "action": shot.get("action", ""),
            "transition": shot.get("transition", "cut"),
            "visible_text_role": shot.get("visible_text", ""),
            "model_or_host_role": shot.get("model_or_host_role", ""),
            "caption_style_note": shot.get("caption_style_note", ""),
            "sticker_overlay_note": shot.get("sticker_overlay_note", ""),
            "sound_effect_note": shot.get("sound_effect_note", ""),
            "scene_style_note": shot.get("scene_style_note", ""),
            "reference_element_to_preserve": shot.get("reference_element_to_preserve", ""),
        })
    return result


def infer_caption_style(on_screen: list[str]) -> str:
    if not on_screen:
        return "no visible caption style captured; infer from frames manually"
    return "large short-form ecommerce captions; preserve placement and rhythm but rewrite all text"


def object_or_empty(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def source_target_duration(source: dict[str, Any]) -> tuple[float, int]:
    raw = source.get("raw_target_duration_seconds")
    if raw is None:
        raw = source.get("target_duration_seconds")
    if raw is None:
        raw = min(float(source.get("duration_seconds") or 15), 15)
    raw_float = float(raw)
    return raw_float, min(round_half_up(raw_float), 15)


def build_blueprint(analysis: dict[str, Any]) -> dict[str, Any]:
    source = analysis.get("source", {}) if isinstance(analysis.get("source"), dict) else {}
    assets = analysis.get("analysis_assets", {}) if isinstance(analysis.get("analysis_assets"), dict) else {}
    copy = analysis.get("copywriting", {}) if isinstance(analysis.get("copywriting"), dict) else {}
    rhythm = analysis.get("rhythm", {}) if isinstance(analysis.get("rhythm"), dict) else {}
    viral = analysis.get("viral_mechanism", {}) if isinstance(analysis.get("viral_mechanism"), dict) else {}
    model_presence = object_or_empty(analysis, "model_presence")
    caption_style = object_or_empty(analysis, "caption_style")
    sticker_overlay_style = object_or_empty(analysis, "sticker_overlay_style")
    sound_design = object_or_empty(analysis, "sound_design")
    voiceover_layer = object_or_empty(analysis, "voiceover_layer")
    voiceover_correction = object_or_empty(analysis, "voiceover_correction")
    voiceover_style_blueprint = object_or_empty(analysis, "voiceover_style_blueprint")
    scene_style = object_or_empty(analysis, "scene_style")
    motion_style = object_or_empty(analysis, "motion_style")
    transfer_policy = object_or_empty(analysis, "transfer_policy")
    shots = shot_structure(analysis.get("shots"))
    on_screen_texts = text_items(copy.get("on_screen_text"))
    spoken_texts = text_items(copy.get("spoken_transcript"))
    camera_sequence = [shot["camera"] for shot in shots if shot.get("camera")]
    structure = [
        {
            "start": shot.get("start"),
            "end": shot.get("end"),
            "role": shot.get("role") or f"segment_{index + 1}",
            "transfer_goal": "preserve this segment's narrative job, not exact content",
        }
        for index, shot in enumerate(shots)
    ]
    do_not_copy = [
        "original captions verbatim",
        "reference brand names or logos",
        "watermarks or platform UI",
        "unsupported product claims",
        "copyrighted characters or distinctive protected artwork",
    ]
    risks = viral.get("risks_to_avoid")
    if isinstance(risks, list):
        do_not_copy.extend(str(item) for item in risks if item)
    raw_target_duration, target_duration = source_target_duration(source)
    return {
        "source_summary": {
            "path_or_url": source.get("path_or_url", ""),
            "duration_seconds": source.get("duration_seconds"),
            "raw_target_duration_seconds": raw_target_duration,
            "target_duration_seconds": target_duration,
            "duration_rounding_policy": "round half up to an integer; cap at 15 seconds; Seedance supports 4-15 seconds",
            "ratio": source.get("ratio", ""),
            "platform_style": source.get("platform_style", ""),
            "content_type": source.get("content_type", ""),
            "contact_sheet": assets.get("contact_sheet", ""),
        },
        "structure": structure,
        "camera_style": {
            "sequence": camera_sequence,
            "dominant_pattern": " -> ".join(camera_sequence) if camera_sequence else "",
            "transfer_rule": "match camera intent, shot order, and movement energy while changing product content",
        },
        "edit_rhythm": {
            "first_frame_tactic": rhythm.get("first_frame_tactic", ""),
            "average_shot_seconds": rhythm.get("average_shot_seconds"),
            "cut_density": rhythm.get("cut_density", ""),
            "pace_notes": rhythm.get("pace_notes", ""),
        },
        "visual_style": {
            "background": scene_style.get("background", analysis.get("visual_background", "")),
            "lighting": scene_style.get("lighting", analysis.get("visual_lighting", "")),
            "palette": scene_style.get("palette", analysis.get("visual_palette", "")),
            "caption_style": caption_style or infer_caption_style(on_screen_texts),
            "sticker_overlay_style": sticker_overlay_style,
            "props": scene_style.get("props", analysis.get("visual_props", "")),
            "wardrobe_or_human_styling": scene_style.get("wardrobe_or_human_styling", ""),
            "surface_textures": scene_style.get("surface_textures", ""),
            "manual_fill_note": "Fill visual_background, visual_lighting, visual_palette, and visual_props in the completed analysis for higher fidelity.",
        },
        "reference_fidelity": {
            "default_mode": "reference-faithful remake",
            "model_presence": model_presence,
            "caption_style": caption_style,
            "sticker_overlay_style": sticker_overlay_style,
            "sound_design": sound_design,
            "scene_style": scene_style,
            "motion_style": motion_style,
            "transfer_policy": transfer_policy or {
                "preserve": [
                    "model/host presence if present",
                    "shot order and timing proportions",
                    "framing and camera movement",
                    "subject actions and product interactions",
                    "scene design, lighting, palette, props",
                    "caption placement and rhythm",
                    "voiceover formula and CTA logic",
                ],
                "replace_or_remove": do_not_copy,
            },
        },
        "copy_formula": {
            "voiceover_layer": voiceover_layer,
            "voiceover_correction": voiceover_correction,
            "voiceover_style_blueprint": voiceover_style_blueprint,
            "formula": copy.get("formula", ""),
            "hook": copy.get("hook", ""),
            "pain_or_tension": copy.get("pain_or_tension", ""),
            "product_entry": copy.get("product_entry", ""),
            "proof_or_demo": copy.get("proof_or_demo", ""),
            "cta": copy.get("cta", ""),
            "tone": copy.get("tone", ""),
            "caption_examples_for_analysis_only": on_screen_texts[:8],
            "spoken_examples_for_analysis_only": spoken_texts[:8],
        },
        "viral_mechanism": {
            "scroll_stop_reason": viral.get("scroll_stop_reason", ""),
            "retention_reason": viral.get("retention_reason", ""),
            "conversion_reason": viral.get("conversion_reason", ""),
        },
        "do_not_copy": sorted(set(do_not_copy)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a compact reference video blueprint")
    parser.add_argument("--analysis-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-name", default="reference_video_blueprint.json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        analysis_path = Path(args.analysis_json).expanduser().resolve()
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        blueprint = build_blueprint(load_json(analysis_path))
        output_path = output_dir / args.output_name
        output_path.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": True, "blueprint_path": str(output_path)}, ensure_ascii=True, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "stage": "blueprint", "error": str(exc)}, ensure_ascii=True, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
