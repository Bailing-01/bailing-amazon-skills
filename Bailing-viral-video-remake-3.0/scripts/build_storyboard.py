#!/usr/bin/env python3
"""Build a pre-generation storyboard from a recreation brief."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


UNSUPPORTED_CLAIM_TERMS = {
    "antibacterial", "anti-bacterial", "sterilize", "sterilizing", "medical", "cure", "heal",
    "guaranteed", "100%", "best", "number one", "certified", "\u6297\u83cc", "\u6291\u83cc", "\u533b\u7528", "\u6cbb\u7597",
    "\u6cbb\u6108", "\u4fdd\u8bc1", "\u7b2c\u4e00", "\u6700", "100%",
}
PERSON_POLICY_TERMS = {
    "bypass face review", "evade face review", "avoid face detection", "circumvent", "\u5ba1\u6838\u89c4\u907f",
    "\u89c4\u907f\u5ba1\u6838", "\u7ed5\u8fc7\u5ba1\u6838", "\u7ed5\u5ba1\u6838", "\u4eba\u8138\u5ba1\u6838", "same face", "consistent face",
    "face reference", "celebrity likeness", "\u660e\u661f\u8138", "\u540c\u4e00\u5f20\u8138", "\u4eba\u8138\u53c2\u8003",
}
PERSON_PRESENCE_HINTS = {
    "model", "host", "presenter", "person", "people", "hand", "hands", "body", "face", "lifestyle",
    "\u6a21\u7279", "\u771f\u4eba", "\u4eba\u7269", "\u4e3b\u64ad", "\u4e3b\u6301", "\u624b\u90e8", "\u4e0a\u8eab", "\u8138", "\u534a\u8eab",
}


MIN_SEEDANCE_DURATION = 4
MAX_SEEDANCE_DURATION = 15


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def normalize_duration(value: Any) -> int:
    return round_half_up(float(value))


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def timeline_items(items: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and "start" in item and "end" in item:
                normalized = dict(item)
                normalized["start"] = float(item["start"])
                normalized["end"] = float(item["end"])
                result.append(normalized)
    return result


def overlapping_text(start: float, end: float, items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in items:
        item_start = float(item.get("start", 0))
        item_end = float(item.get("end", 0))
        overlap = max(0.0, min(end, item_end) - max(start, item_start))
        if overlap > 0:
            text = str(item.get("text", "")).strip()
            if text:
                lines.append(text)
    return " / ".join(lines)


def validate_terms(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for term in UNSUPPORTED_CLAIM_TERMS:
        token = term.lower()
        if re.fullmatch(r"[a-z0-9 -]+", token):
            if re.search(rf"\b{re.escape(token)}\b", lowered):
                found.append(term)
        elif token in lowered:
            found.append(term)
    return sorted(found)


def validate_person_policy(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for term in PERSON_POLICY_TERMS:
        token = term.lower()
        if re.fullmatch(r"[a-z0-9 -]+", token):
            if re.search(rf"\b{re.escape(token)}\b", lowered):
                found.append(term)
        elif token in lowered:
            found.append(term)
    return sorted(found)


def has_person_presence_hint(text: str) -> bool:
    lowered = text.lower()
    return any(hint.lower() in lowered for hint in PERSON_PRESENCE_HINTS)


def normalized_text(value: str) -> str:
    return re.sub(r"[\s，。！？、,.!?;；:：\"'“”‘’（）()\[\]【】\-—_]+", "", value).lower()


def overlap_score(left: str, right: str) -> float:
    left_norm = normalized_text(left)
    right_norm = normalized_text(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm in right_norm or right_norm in left_norm:
        return 1.0
    left_chars = set(left_norm)
    right_chars = set(right_norm)
    if not left_chars or not right_chars:
        return 0.0
    return len(left_chars & right_chars) / max(len(left_chars), len(right_chars))


def infer_transcript_like_text(voice: list[dict[str, Any]], text: list[dict[str, Any]]) -> bool:
    voice_lines = [str(item.get("text", "")).strip() for item in voice if str(item.get("text", "")).strip()]
    text_lines = [str(item.get("text", "")).strip() for item in text if str(item.get("text", "")).strip()]
    if not voice_lines or not text_lines:
        return False
    matches = 0
    for text_line in text_lines:
        if any(overlap_score(text_line, voice_line) >= 0.72 for voice_line in voice_lines):
            matches += 1
    return matches >= max(1, min(len(text_lines), len(voice_lines)) // 2)


def resolve_caption_mode(brief: dict[str, Any], voice: list[dict[str, Any]], text: list[dict[str, Any]]) -> tuple[str, bool]:
    raw_policy = brief.get("caption_layer_policy") if isinstance(brief.get("caption_layer_policy"), dict) else {}
    mode = str(raw_policy.get("mode") or "").strip()
    allow_voiceover_subtitles = bool(raw_policy.get("allow_voiceover_subtitles"))
    voiceover_policy = brief.get("voiceover_policy") if isinstance(brief.get("voiceover_policy"), dict) else {}
    preserve_voiceover = bool(voiceover_policy.get("preserve_voiceover"))
    transcript_like = infer_transcript_like_text(voice, text)
    if mode not in {"voiceover_only", "sparse_stickers", "caption_driven", "no_readable_text"}:
        if preserve_voiceover or voice:
            mode = "sparse_stickers" if text else "voiceover_only"
        elif text:
            mode = "caption_driven"
        else:
            mode = "no_readable_text"
    if (preserve_voiceover or voice) and transcript_like and not allow_voiceover_subtitles and mode != "caption_driven":
        mode = "sparse_stickers"
    return mode, transcript_like


def build_storyboard(brief: dict[str, Any], blueprint: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    shots = brief.get("shot_plan")
    if not isinstance(shots, list) or not shots:
        raise ValueError("brief shot_plan must be a non-empty list")
    brief_duration = brief.get("duration")
    raw_target_duration = brief_duration if brief_duration is not None else 15
    target_duration = normalize_duration(raw_target_duration)
    if target_duration < MIN_SEEDANCE_DURATION or target_duration > MAX_SEEDANCE_DURATION:
        raise ValueError(f"brief duration must round to an integer between 4 and 15 seconds; got raw={raw_target_duration!r}, rounded={target_duration:g}")
    voice = timeline_items(brief.get("adapted_voiceover"))
    text = timeline_items(brief.get("adapted_on_screen_text"))
    caption_mode, transcript_like_text = resolve_caption_mode(brief, voice, text)
    product_constraints = str(brief.get("product_identity_constraints") or "").strip()
    warnings: list[str] = []
    if transcript_like_text and caption_mode != "caption_driven":
        warnings.append(
            "Adapted on-screen text overlaps with the voiceover. Treat it as timing/style evidence or sparse stickers only; do not create line-by-line subtitles by default."
        )
    panels: list[dict[str, Any]] = []
    total = 0.0
    person_role_count = 0
    for index, shot in enumerate(shots, 1):
        if not isinstance(shot, dict):
            raise ValueError(f"shot_plan[{index}] must be an object")
        start = float(shot.get("start", 0))
        end = float(shot.get("end", 0))
        if end <= start:
            raise ValueError(f"shot_plan[{index}] has invalid timing")
        total += end - start
        voice_line = overlapping_text(start, end, voice)
        text_line = overlapping_text(start, end, text)
        combined = " ".join(str(value) for value in shot.values()) + " " + voice_line + " " + text_line
        risky = validate_terms(combined)
        if risky:
            warnings.append(f"Panel {index} may contain unsupported claim terms: {', '.join(risky)}")
        person_policy = validate_person_policy(combined)
        if person_policy:
            warnings.append(f"Panel {index} may contain face-review or identity-reference risk terms: {', '.join(person_policy)}")
        model_or_host_role = str(shot.get("model_or_host_role", "")).strip()
        if model_or_host_role:
            person_role_count += 1
        panels.append({
            "panel": index,
            "time": {"start": start, "end": end, "duration": round(end - start, 3)},
            "story_purpose": shot.get("purpose", ""),
            "reference_element_preserved": shot.get(
                "reference_element_preserved",
                "Preserve this reference shot's narrative job, camera intent, scene style, action logic, and caption role.",
            ),
            "adaptation_reason": shot.get("adaptation_reason", "Only the product and disallowed reference-specific elements are adapted."),
            "scene_style": shot.get("scene_style", "match the reference video's background, lighting, palette, props, and caption style for this segment"),
            "visual_composition": shot.get("visual", ""),
            "framing": shot.get("framing", "infer from visual composition"),
            "model_or_host_role": model_or_host_role,
            "camera_movement": shot.get("camera", ""),
            "product_action": shot.get("action", ""),
            "sticker_overlay_intent": shot.get("sticker_overlay", "match the reference video's sticker, badge, corner-marker, checkmark, callout, and pop timing for this segment"),
            "sound_effect_intent": shot.get("sound_effect", "match the reference video's transition, sticker-pop, product-handling, cloth, tap, stretch, or CTA accent sound for this segment"),
            "caption_layer_policy": caption_mode,
            "product_fidelity_constraint": product_constraints,
            "voiceover": voice_line,
            "on_screen_text_intent": text_line,
            "continuity_note": "Keep the same product identity, palette, lighting, and background logic as adjacent panels.",
            "risk_note": "No copied reference captions, no unsupported claims, no platform UI, no watermark.",
        })
    if abs(round(total, 3) - round(target_duration, 3)) > 0.01:
        raise ValueError(f"storyboard duration must total {target_duration:g} seconds; got {total:g}")
    if not product_constraints:
        warnings.append("Product identity constraints are empty.")
    person_context = " ".join(
        str(value)
        for value in (
            brief.get("reference_logic_to_preserve"),
            brief.get("reference_elements_to_preserve"),
            brief.get("objective"),
        )
    )
    if has_person_presence_hint(person_context) and person_role_count == 0:
        warnings.append("Reference logic suggests model/host/person presence, but no panel has model_or_host_role. Fill this field before paid generation.")
    blueprint_summary = {}
    if blueprint:
        blueprint_summary = {
            "structure": blueprint.get("structure", []),
            "camera_style": blueprint.get("camera_style", {}),
            "visual_style": blueprint.get("visual_style", {}),
            "reference_fidelity": blueprint.get("reference_fidelity", {}),
            "copy_formula": blueprint.get("copy_formula", {}),
            "do_not_copy": blueprint.get("do_not_copy", []),
        }
    storyboard = {
        "product_name": brief.get("product_name", ""),
        "objective": brief.get("objective", ""),
        "duration": target_duration,
        "ratio": brief.get("ratio", "9:16"),
        "voiceover_language": brief.get("voiceover_language", "zh-CN"),
        "caption_layer_policy": {
            "mode": caption_mode,
            "transcript_like_on_screen_text_detected": transcript_like_text,
            "rule": "Use only one readable text layer. With preserved voiceover, do not create line-by-line transcript subtitles unless caption_driven mode is explicit.",
        },
        "blueprint_summary": blueprint_summary,
        "panels": panels,
        "continuity_checklist": [
            "First panel shows the product or core problem immediately.",
            "Every panel advances the selling story.",
            "Camera movement follows the reference blueprint's intent.",
            "Lighting, background, color palette, and prop style remain coherent.",
            "Each panel has one main action only.",
            "Voiceover and on-screen text do not copy the reference captions.",
            "Final panel is a clean CTA or hero lockup.",
        ],
        "warnings": warnings,
    }
    return storyboard, warnings


def markdown(storyboard: dict[str, Any]) -> str:
    lines = [
        f"# Storyboard: {storyboard.get('product_name', '')}",
        "",
        f"Objective: {storyboard.get('objective', '')}",
        f"Duration: {storyboard.get('duration')}s",
        f"Ratio: {storyboard.get('ratio')}",
        "",
        "## Panels",
    ]
    for panel in storyboard["panels"]:
        time = panel["time"]
        lines.extend([
            "",
            f"### Panel {panel['panel']} | {time['start']:.1f}-{time['end']:.1f}s",
            f"- Purpose: {panel['story_purpose']}",
            f"- Reference preserved: {panel['reference_element_preserved']}",
            f"- Adaptation reason: {panel['adaptation_reason']}",
            f"- Scene style: {panel['scene_style']}",
            f"- Visual: {panel['visual_composition']}",
            f"- Model/host role: {panel['model_or_host_role']}",
            f"- Camera: {panel['camera_movement']}",
            f"- Action: {panel['product_action']}",
            f"- Sticker/overlay: {panel['sticker_overlay_intent']}",
            f"- Sound effect: {panel['sound_effect_intent']}",
            f"- Voiceover: {panel['voiceover']}",
            f"- Text intent: {panel['on_screen_text_intent']}",
            f"- Continuity: {panel['continuity_note']}",
            f"- Risk: {panel['risk_note']}",
        ])
    lines.extend(["", "## Continuity Checklist"])
    lines.extend(f"- [ ] {item}" for item in storyboard["continuity_checklist"])
    if storyboard.get("warnings"):
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {item}" for item in storyboard["warnings"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a storyboard before Seedance generation")
    parser.add_argument("--brief-json", required=True)
    parser.add_argument("--blueprint-json")
    parser.add_argument("--output-dir", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        brief = load_json(Path(args.brief_json).expanduser().resolve())
        blueprint = load_json(Path(args.blueprint_json).expanduser().resolve()) if args.blueprint_json else None
        storyboard, warnings = build_storyboard(brief, blueprint)
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "storyboard.json"
        md_path = output_dir / "storyboard.md"
        json_path.write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(markdown(storyboard), encoding="utf-8")
        print(json.dumps({"ok": True, "storyboard_json": str(json_path), "storyboard_md": str(md_path), "warnings": warnings}, ensure_ascii=True, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "stage": "storyboard", "error": str(exc)}, ensure_ascii=True, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
