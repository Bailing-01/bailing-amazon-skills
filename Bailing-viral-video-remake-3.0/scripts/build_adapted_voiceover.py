#!/usr/bin/env python3
"""Correct reference ASR and adapt voiceover timing to the user's product.

This script treats ASR as timing evidence, not final copy. OCR/manual captions
and product facts are used to correct likely ASR errors. By default, the adapted
voiceover is a conservative product-substitution version of the reference
voiceover, not a newly written sales script.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


VOICEOVER_STYLE_BLUEPRINT = {
    "speaker": "young energetic Mandarin commercial voice",
    "emotion": "excited, refreshing, bright, shareable, punchy",
    "pace": "fast but clear; slogan-like phrases, not slow explanation",
    "delivery": "short commercial punches with rising endings and tiny pauses",
    "energy_curve": "strong hook -> sensory excitement -> product payoff -> share/CTA lift",
    "timing_rule": "Keep each spoken line close to the original segment length; do not overfill the target-duration timeline.",
    "mix_rule": "Voiceover must sit in front of music and sound effects.",
    "avoid": [
        "flat narration",
        "slow explanatory reading",
        "overly long sentences",
        "unsupported product claims",
        "copying the original brand slogan verbatim",
    ],
}


MIN_SEEDANCE_DURATION = 4
MAX_SEEDANCE_DURATION = 15


TEXT_FIXES = {
    "\u73fe\u5728": "\u73b0\u5728",
    "\u6c23\u6ce1": "\u6c14\u6ce1",
    "\u77ac\u9593": "\u77ac\u95f4",
    "\u5feb\u6a02": "\u5feb\u4e50",
    "\u723d\u5c31\u73fe\u5728": "\u723d\uff0c\u5c31\u73b0\u5728\uff01",
    "\u723d\u5c31\u73b0\u5728": "\u723d\uff0c\u5c31\u73b0\u5728\uff01",
    "\u6c14\u6ce1\u66b4\u529b": "\u6c14\u6ce1\u7206\u88c2",
    "\u6c23\u6ce1\u66b4\u529b": "\u6c14\u6ce1\u7206\u88c2",
    "\u5531\u7701": "\u7545\u723d",
    "\u5145\u9577": "\u5145\u80fd",
    "\u5145\u957f": "\u5145\u80fd",
    "\u7bc0\u6bbc": "\u89e3\u6e34",
    "\u8282\u58f3": "\u89e3\u6e34",
    "\u958b\u61f7": "\u5f00\u6000",
    "\u53ef\u53ef\u53ef\u6a02": "\u53ef\u53e3\u53ef\u4e50",
    "\u53ef\u53ef\u53ef\u4e50": "\u53ef\u53e3\u53ef\u4e50",
}


def read_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    value = Path(path).expanduser().resolve()
    if not value.is_file():
        return {}
    data = json.loads(value.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{value} must contain a JSON object")
    return data


def split_facts(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[;,\n\uff0c\uff1b]+", value) if item.strip()]


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def normalize_duration(value: float) -> int:
    return round_half_up(float(value))


def normalize_text(text: str) -> str:
    text = str(text or "").strip()
    for src, dst in TEXT_FIXES.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+", "", text)
    return text


def normalize_punctuation(text: str) -> str:
    text = normalize_text(text)
    if text and not text.endswith(("\uff01", "\u3002", "?", "\uff1f", "!")):
        text += "\uff01"
    return text


def timeline_items(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    result: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("corrected_text") or "").strip()
        if not text:
            continue
        time_obj = item.get("time") if isinstance(item.get("time"), dict) else {}
        result.append(
            {
                "start": float(item.get("start", time_obj.get("start", 0)) or 0),
                "end": float(item.get("end", time_obj.get("end", 0)) or 0),
                "text": text,
                **{k: v for k, v in item.items() if k not in {"start", "end", "text", "time"}},
            }
        )
    return result


def extract_ocr_items(analysis: dict[str, Any], ocr_data: dict[str, Any]) -> list[dict[str, Any]]:
    items = timeline_items(ocr_data.get("on_screen_text") or ocr_data.get("items"))
    if items:
        return items
    copywriting = analysis.get("copywriting") if isinstance(analysis.get("copywriting"), dict) else {}
    return timeline_items(copywriting.get("on_screen_text"))


def best_timed_overlap(segment: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    start = float(segment.get("start", 0))
    end = float(segment.get("end", 0))
    best: dict[str, Any] | None = None
    best_overlap = 0.0
    for item in candidates:
        item_start = float(item.get("start", 0))
        item_end = float(item.get("end", 0))
        overlap = max(0.0, min(end, item_end) - max(start, item_start))
        if overlap > best_overlap:
            best = item
            best_overlap = overlap
    return best if best_overlap > 0 else None


def correct_reference_voiceover(audio: dict[str, Any], ocr_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    layer = audio.get("voiceover_layer") if isinstance(audio.get("voiceover_layer"), dict) else {}
    segments = timeline_items(layer.get("segments"))
    corrected: list[dict[str, Any]] = []
    for segment in segments:
        asr_text = normalize_punctuation(segment.get("text", ""))
        ocr = best_timed_overlap(segment, ocr_items)
        ocr_text = normalize_punctuation(ocr.get("text", "")) if ocr else ""
        if ocr_text and len(ocr_text) >= 2:
            text = ocr_text
            evidence = "ocr_over_asr"
        else:
            text = asr_text
            evidence = "asr_context_normalized"
        corrected.append(
            {
                "start": round(float(segment["start"]), 2),
                "end": round(float(segment["end"]), 2),
                "asr_text": segment.get("text", ""),
                "ocr_text": ocr_text,
                "corrected_text": text,
                "evidence": evidence,
            }
        )
    return corrected


def infer_category(product_facts: list[str]) -> str:
    blob = " ".join(product_facts).lower()
    if any(token in blob for token in ["sprite", "\u96ea\u78a7", "\u53ef\u4e50", "\u6c7d\u6c34", "\u996e\u6599", "soda"]):
        return "carbonated_beverage"
    if any(token in blob for token in ["\u6d17\u8863\u6db2", "\u6d17\u8863", "\u67d4\u987a", "\u62a4\u8863", "laundry", "detergent"]):
        return "laundry_care"
    if any(token in blob for token in ["\u5185\u88e4", "\u7eaf\u68c9", "\u5973\u58eb", "underwear", "cotton"]):
        return "apparel_underwear"
    return "generic_ecommerce"


def product_label(product_facts: list[str]) -> str:
    if not product_facts:
        return ""
    first = str(product_facts[0]).strip()
    if not first:
        return ""
    return first[:24]


def conservative_product_substitution(text: str, product_facts: list[str]) -> str:
    """Keep sentence structure intact and only swap obvious product-specific terms.

    This intentionally does not invent new selling points. When no safe product
    term is found, the corrected reference line is returned unchanged.
    """

    value = normalize_punctuation(text)
    label = product_label(product_facts)
    category = infer_category(product_facts)
    if not label:
        return value

    category_terms = {
        "carbonated_beverage": ["\u996e\u6599", "\u6c7d\u6c34", "\u53ef\u4e50", "\u96ea\u78a7", "\u8fd9\u74f6"],
        "laundry_care": ["\u6d17\u8863\u6db2", "\u67d4\u987a\u5242", "\u7559\u9999\u73e0", "\u6d17\u8863\u73e0", "\u6d17\u8863\u51dd\u73e0"],
        "apparel_underwear": ["\u5185\u88e4", "\u8863\u670d", "\u8fd9\u4ef6", "\u8fd9\u6761"],
        "generic_ecommerce": [],
    }
    for term in category_terms.get(category, []):
        if term in value and term != label:
            value = value.replace(term, label)
    return value


def default_lines_for_category(category: str) -> list[str]:
    if category == "carbonated_beverage":
        return [
            "\u723d\uff0c\u5c31\u73b0\u5728\uff01",
            "\u6c14\u6ce1\u7206\u5f00\u7684\u77ac\u95f4\uff01",
            "\u7545\u723d\u89e3\u6e34\uff01",
            "\u5feb\u4e50\u5145\u80fd\uff01",
            "\u5feb\u4e50\uff0c\u5c31\u8981\u5206\u4eab\uff01",
            "\u8fd9\u4e00\u53e3\uff0c\u51b0\u723d\u5230\u4f4d\uff01",
            "\u5373\u523b\u5f00\u723d\uff01",
        ]
    if category == "apparel_underwear":
        return [
            "\u8212\u670d\uff0c\u5148\u7ed9\u81ea\u5df1\uff01",
            "\u7eaf\u68c9\u8d34\u80a4\uff0c\u67d4\u8f6f\u4e0d\u95f7\uff01",
            "\u7ec6\u8282\u770b\u5f97\u89c1\uff0c\u4e0a\u8eab\u66f4\u5b89\u5fc3\uff01",
            "\u6bcf\u5929\u90fd\u8981\u597d\u597d\u7a7f\uff01",
            "\u6e05\u723d\u8212\u9002\uff01",
            "\u73b0\u5728\u5c31\u6362\u4e0a\uff01",
        ]
    return [
        "\u4e00\u773c\u5c31\u60f3\u8bd5\uff01",
        "\u7ec6\u8282\u771f\u7684\u5f88\u52a0\u5206\uff01",
        "\u597d\u770b\u53c8\u597d\u7528\uff01",
        "\u65e5\u5e38\u7528\u8d77\u6765\u5f88\u987a\u624b\uff01",
        "\u8d28\u611f\u5230\u4f4d\uff01",
        "\u8fd9\u6b3e\u53ef\u4ee5\u51b2\uff01",
    ]


def default_times_for_duration(target_duration: float) -> list[tuple[float, float]]:
    ratios = [(0.0, 0.16), (0.16, 0.28), (0.28, 0.48), (0.48, 0.64), (0.64, 0.83), (0.83, 1.0)]
    return [(round(start * target_duration, 2), round(end * target_duration, 2)) for start, end in ratios]


def adapt_to_reference_timing(
    corrected: list[dict[str, Any]],
    product_facts: list[str],
    target_duration: float,
    rewrite_mode: str,
) -> list[dict[str, Any]]:
    category = infer_category(product_facts)
    lines = default_lines_for_category(category)
    usable = []
    for segment in corrected:
        start = float(segment.get("start", 0))
        end = float(segment.get("end", 0))
        if start >= target_duration:
            continue
        clipped = {**segment, "start": start, "end": min(end, target_duration)}
        if clipped["end"] > clipped["start"]:
            usable.append(clipped)
    if not usable:
        default_times = default_times_for_duration(target_duration)
        return [
            {
                "start": start,
                "end": end,
                "text": lines[index % len(lines)],
                "adaptation_mode": "fallback_category_template_no_reference_transcript",
            }
            for index, (start, end) in enumerate(default_times)
        ]
    adapted: list[dict[str, Any]] = []
    for index, segment in enumerate(usable):
        reference_text = segment.get("corrected_text", "")
        if rewrite_mode == "category_template":
            adapted_text = lines[index % len(lines)]
            adaptation_mode = "category_template"
        else:
            adapted_text = conservative_product_substitution(reference_text, product_facts)
            adaptation_mode = "product_swap"
        adapted.append(
            {
                "start": segment["start"],
                "end": segment["end"],
                "text": adapted_text,
                "reference_text": reference_text,
                "timing_source": "reference_asr_segment",
                "adaptation_mode": adaptation_mode,
            }
        )
    return adapted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Correct ASR voiceover and adapt it to user product facts")
    parser.add_argument("--audio-json", required=True)
    parser.add_argument("--analysis-json", help="Completed/scaffold reference analysis JSON with copywriting.on_screen_text")
    parser.add_argument("--ocr-json", help="Optional OCR/on-screen-text JSON")
    parser.add_argument("--product-name", default="")
    parser.add_argument("--product-fact", action="append", help="Visible or user-supplied product fact. Can be repeated.")
    parser.add_argument("--user-facts", default="", help="Semicolon/comma/newline separated product facts")
    parser.add_argument(
        "--rewrite-mode",
        choices=["product_swap", "category_template"],
        default="product_swap",
        help="product_swap keeps reference sentence structure and only replaces obvious product terms. category_template is only for explicit user copy/creative requirements.",
    )
    parser.add_argument("--target-duration", type=float, default=15, help="Target output duration in seconds. Values are rounded half up to an integer; rounded value must be 4-15.")
    parser.add_argument("--output-dir", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    audio = read_json(args.audio_json)
    rounded_duration = normalize_duration(args.target_duration)
    if rounded_duration < MIN_SEEDANCE_DURATION or rounded_duration > MAX_SEEDANCE_DURATION:
        raise ValueError(f"--target-duration must round to an integer between 4 and 15 seconds; got raw={args.target_duration:g}, rounded={rounded_duration:g}")
    analysis = read_json(args.analysis_json)
    ocr_data = read_json(args.ocr_json)
    product_facts = split_facts(args.user_facts)
    product_facts.extend(str(item).strip() for item in (args.product_fact or []) if str(item).strip())
    if args.product_name:
        product_facts.insert(0, args.product_name)

    ocr_items = extract_ocr_items(analysis, ocr_data)
    corrected = correct_reference_voiceover(audio, ocr_items)
    adapted = adapt_to_reference_timing(corrected, product_facts, rounded_duration, args.rewrite_mode)
    layer = audio.get("voiceover_layer") if isinstance(audio.get("voiceover_layer"), dict) else {}
    detected = bool(layer.get("detected"))

    payload = {
        "ok": True,
        "source_asr_status": audio.get("transcript_status"),
        "correction_policy": "Use ASR for speech presence and timing; use OCR/manual captions plus context to correct words. Default rewrite mode is product_swap: preserve the reference sentence structure, tone, rhythm, segment order, and timing, and only replace obvious product-specific terms from user-provided or visible product facts. Never invent unsupported claims.",
        "rewrite_mode": args.rewrite_mode,
        "reference_voiceover_corrected": corrected,
        "product_facts": product_facts,
        "raw_target_duration": args.target_duration,
        "target_duration": rounded_duration,
        "adapted_voiceover": adapted,
        "voiceover_style_blueprint": VOICEOVER_STYLE_BLUEPRINT,
        "voiceover_policy": {
            "source_detected": detected,
            "source_confidence": layer.get("confidence", 0),
            "preserve_voiceover": detected,
            "speaker_style": VOICEOVER_STYLE_BLUEPRINT["speaker"],
            "relationship_to_on_screen_text": "match_or_correct_with_ocr",
            "generation_instruction": "Follow voiceover_style_blueprint exactly: energetic Mandarin commercial voice, fast clear slogan rhythm, rising endings, tiny pauses, voice in front of music and SFX.",
        },
        "claim_safety": {
            "forbidden_without_user_proof": [
                "medical, health, therapeutic, antibacterial, anti-allergy, or safety claims",
                "official certification, ranking, patent, warranty, price, or discount claims",
                "nutritional claims such as zero sugar or low calorie unless user-supplied",
            ]
        },
    }

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "voiceover_correction_and_adaptation.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output_path": str(output_path), "adapted_lines": len(adapted)}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
