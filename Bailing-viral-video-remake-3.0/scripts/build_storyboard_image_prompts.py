#!/usr/bin/env python3
"""Create a single director storyboard sheet image prompt."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Storyboard JSON must contain an object")
    return data


def layout_for_count(count: int) -> str:
    if count <= 4:
        cols = count
    elif count <= 6:
        cols = 3
    elif count <= 8:
        cols = 4
    else:
        cols = 4
    rows = math.ceil(count / cols)
    return f"{cols} columns x {rows} rows"


def layout_shape_for_count(count: int) -> tuple[int, int]:
    if count <= 4:
        cols = count
    elif count <= 6:
        cols = 3
    elif count <= 8:
        cols = 4
    else:
        cols = 4
    rows = math.ceil(count / cols)
    return cols, rows


def storyboard_size_for_count(count: int) -> str:
    cols, rows = layout_shape_for_count(count)
    return "2048x1536" if cols >= rows else "1536x2048"


def short(value: Any, limit: int = 120) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def build_sheet_prompt(storyboard: dict[str, Any]) -> str:
    panels = storyboard.get("panels")
    if not isinstance(panels, list) or not panels:
        raise ValueError("storyboard.panels must be a non-empty list")
    product = storyboard.get("product_name", "the product")
    ratio = storyboard.get("ratio", "9:16")
    layout = layout_for_count(len(panels))
    target_size = storyboard_size_for_count(len(panels))
    caption_policy = storyboard.get("caption_layer_policy") if isinstance(storyboard.get("caption_layer_policy"), dict) else {}
    caption_mode = str(caption_policy.get("mode") or "sparse_stickers").strip()
    caption_rule = str(caption_policy.get("rule") or "Use only one readable text layer.").strip()
    panel_lines: list[str] = []
    for panel in panels:
        time = panel.get("time", {}) if isinstance(panel.get("time"), dict) else {}
        panel_lines.append(
            "\n".join([
                f"Frame {panel.get('panel')}: {time.get('start')}-{time.get('end')}s",
                f"Purpose: {short(panel.get('story_purpose'), 80)}",
                f"Reference preserved: {short(panel.get('reference_element_preserved'), 120)}",
                f"Scene style: {short(panel.get('scene_style'), 160)}",
                f"Visual: {short(panel.get('visual_composition'), 180)}",
                f"Model/host role: {short(panel.get('model_or_host_role'), 100)}",
                f"Camera: {short(panel.get('camera_movement'), 90)}",
                f"Action: {short(panel.get('product_action'), 100)}",
                f"Sticker/overlay: {short(panel.get('sticker_overlay_intent'), 110)}",
                f"Sound cue: {short(panel.get('sound_effect_intent'), 90)}",
                f"VO: {short(panel.get('voiceover'), 80)}",
                f"Text: {short(panel.get('on_screen_text_intent'), 80)}",
            ])
        )
    joined = "\n\n".join(panel_lines)
    return f"""Create one single director storyboard sheet image for a {ratio} short ecommerce video.

Target canvas size: {target_size}. This is one storyboard sheet, not separate panel images. Arrange {len(panels)} frame cells in reading order using a clean {layout} grid. Each frame cell must contain a simple visual sketch/painted planning frame plus compact readable notes under or beside the frame.

Product: {product}
Storyboard objective: {storyboard.get('objective', '')}
Overall style: polished ecommerce director storyboard, clean white workspace, reference-faithful scene design per frame, consistent lighting notes, product-first composition, professional advertising previsualization. Use clear visual planning frames while preserving product shape, model/action role when present, camera logic, sticker/overlay language, caption rhythm, sound-cue intent, and scene logic. Keep text labels concise and legible.

Caption typography lock for the final one-pass video: all large Chinese captions and slogan stickers must use one consistent bold white ecommerce headline style across every frame, with heavy sans-serif shape, thick dark outline, soft drop shadow, high contrast, and the same scale logic. If the reference uses slight italic/slanted headline lettering, preserve that slant consistently. Do not switch middle panels into thin subtitle font, gray subtitle boxes, or random lower-third caption style. Use at most two styles: primary punch headline and final brand lockup.

Readable text layer policy for this storyboard: {caption_mode}. {caption_rule} If voiceover is preserved, storyboard frames may show sparse stickers, punch headlines, feature badges, or CTA lockups, but must not present every spoken line as line-by-line subtitles unless caption_driven mode is explicitly selected. Do not visualize duplicate subtitle layers.

Person face marker rule: if a visible person face appears in any storyboard frame, keep the storyboard in a realistic ecommerce planning style and add a red 5x6 grid overlay covering the entire face area. The grid lines must be medium thickness, clearly visible red lines, and limited to the face area. Do not use sketch, oil-paint, blur, blank-face, mask, or face-removal as the default.

Frame cells and notes:
{joined}

Sheet requirements:
- One single image containing all frame cells.
- Use the target canvas size {target_size} unless the user explicitly requested a higher-resolution or 4K storyboard.
- Frame cell count must be exactly {len(panels)}.
- Show panel numbers and timecodes.
- Include short notes for purpose, camera, action, sticker/overlay, sound cue, voiceover, and text intent.
- Include the preserved reference element and model/host role when present.
- Keep product identity consistent across frames.
- Use visual continuity: match the reference video's scene style logic across frames, including model/host presence, action pattern, background type, lighting, palette, prop language, sticker/overlay placement, caption placement, and clean ecommerce tone.
- Show caption/sticker text as a consistent visual typography system across frame cells: same font weight, outline thickness, shadow, white color, scale family, and placement rhythm.
- Show only the intended single readable text layer. Do not draw both voiceover subtitles and separate caption stickers for the same sentence.
- Do not add platform UI, watermarks, prices, copied reference captions, copied logos, unsupported claims, or sexualized framing.
- If any person appears, keep the product as the main subject and use only truthful anonymous adult lifestyle presence.
- If any visible face appears, apply the red 5x6 face-marker overlay only in the storyboard sheet. The marker is not intended for the final video.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build one visual director storyboard sheet prompt")
    parser.add_argument("--storyboard-json", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        storyboard = load_json(Path(args.storyboard_json).expanduser().resolve())
        prompt = build_sheet_prompt(storyboard)
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        txt_path = output_dir / "storyboard_sheet_prompt.txt"
        json_path = output_dir / "storyboard_sheet_prompt.json"
        txt_path.write_text(prompt, encoding="utf-8")
        target_size = storyboard_size_for_count(len(storyboard.get("panels", [])))
        json_path.write_text(
            json.dumps(
                {"prompt": prompt, "suggested_filename": "storyboard_sheet.png", "suggested_size": target_size},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        count = len(storyboard.get("panels", []))
        print(json.dumps({"ok": True, "panel_count": count, "suggested_size": target_size, "prompt_path": str(txt_path), "json_path": str(json_path)}, ensure_ascii=True, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "stage": "storyboard_sheet_prompt", "error": str(exc)}, ensure_ascii=True, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
