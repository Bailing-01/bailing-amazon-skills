#!/usr/bin/env python3
"""Extract reference-video evidence for viral recreation analysis."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont


MIN_SEEDANCE_DURATION = 4
MAX_SEEDANCE_DURATION = 15
SUPPORTED_RATIOS = {
    "9:16": 9 / 16,
    "1:1": 1.0,
    "16:9": 16 / 9,
    "3:4": 3 / 4,
    "4:3": 4 / 3,
    "21:9": 21 / 9,
}


def frame_time(frame: av.VideoFrame) -> float:
    return float(frame.pts * frame.time_base) if frame.pts is not None else 0.0


def small_luma(image: Image.Image, size: tuple[int, int] = (48, 64)) -> np.ndarray:
    return np.asarray(image.convert("L").resize(size), dtype=np.float32)


def save_frame(frame: av.VideoFrame, path: Path) -> dict[str, Any]:
    image = frame.to_image()
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, quality=92)
    return {"time": round(frame_time(frame), 3), "path": str(path), "width": image.width, "height": image.height}


def contact_sheet(items: list[dict[str, Any]], output: Path, thumb_width: int = 220) -> None:
    if not items:
        return
    thumbs: list[tuple[Image.Image, str]] = []
    for item in items:
        image = Image.open(item["path"]).convert("RGB")
        ratio = thumb_width / image.width
        thumb = image.resize((thumb_width, max(1, int(image.height * ratio))))
        label = f"{item['time']:.2f}s"
        thumbs.append((thumb, label))
    cols = min(4, len(thumbs))
    rows = math.ceil(len(thumbs) / cols)
    label_h = 24
    cell_h = max(img.height for img, _ in thumbs) + label_h
    sheet = Image.new("RGB", (cols * thumb_width, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (thumb, label) in enumerate(thumbs):
        x = (index % cols) * thumb_width
        y = (index // cols) * cell_h
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y + thumb.height, x + thumb_width, y + cell_h), fill="white")
        draw.text((x + 6, y + thumb.height + 5), label, fill="black", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def target_duration_seconds(duration: float) -> int:
    if duration <= 0:
        return MAX_SEEDANCE_DURATION
    return min(round_half_up(duration), MAX_SEEDANCE_DURATION)


def exact_ratio(width: int, height: int) -> str:
    if width <= 0 or height <= 0:
        return "unknown"
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def nearest_supported_ratio(width: int, height: int) -> str:
    if width <= 0 or height <= 0:
        return "9:16"
    aspect = width / height
    return min(SUPPORTED_RATIOS, key=lambda ratio: abs(SUPPORTED_RATIOS[ratio] - aspect))


def analyze(video: Path, output_dir: Path, sample_count: int, scene_threshold: float, max_scene_frames: int) -> dict[str, Any]:
    if not video.is_file():
        raise ValueError(f"Video not found: {video}")
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames"
    scenes_dir = output_dir / "scene_candidates"
    frames_dir.mkdir(parents=True, exist_ok=True)
    scenes_dir.mkdir(parents=True, exist_ok=True)

    container = av.open(str(video))
    video_stream = next((stream for stream in container.streams if stream.type == "video"), None)
    if video_stream is None:
        raise ValueError("No video stream found")
    audio_stream = next((stream for stream in container.streams if stream.type == "audio"), None)
    duration = float(container.duration / 1_000_000) if container.duration else 0.0
    fps = float(video_stream.average_rate) if video_stream.average_rate else None
    width = video_stream.codec_context.width
    height = video_stream.codec_context.height
    source_ratio = exact_ratio(width, height)
    target_ratio = nearest_supported_ratio(width, height)

    sample_targets = [duration * i / max(1, sample_count - 1) for i in range(sample_count)] if duration else []
    samples: list[dict[str, Any]] = []
    scenes: list[dict[str, Any]] = []
    previous: np.ndarray | None = None
    target_index = 0

    for frame in container.decode(video_stream):
        time_s = frame_time(frame)
        image = frame.to_image()
        while target_index < len(sample_targets) and time_s >= sample_targets[target_index]:
            path = frames_dir / f"sample_{target_index + 1:02d}_{time_s:.2f}s.jpg"
            image.save(path, quality=92)
            samples.append({"time": round(time_s, 3), "path": str(path), "width": image.width, "height": image.height})
            target_index += 1

        luma = small_luma(image)
        if previous is not None and len(scenes) < max_scene_frames:
            diff = float(np.mean(np.abs(luma - previous)))
            if diff >= scene_threshold:
                path = scenes_dir / f"scene_{len(scenes) + 1:02d}_{time_s:.2f}s_diff_{diff:.1f}.jpg"
                image.save(path, quality=92)
                scenes.append({"time": round(time_s, 3), "path": str(path), "difference": round(diff, 2)})
        previous = luma
        if target_index >= len(sample_targets) and len(scenes) >= max_scene_frames:
            break

    sheet_path = output_dir / "contact_sheet.jpg"
    contact_sheet(samples, sheet_path)
    scene_sheet_path = output_dir / "scene_contact_sheet.jpg"
    contact_sheet(scenes, scene_sheet_path)

    raw_target_duration = min(duration, float(MAX_SEEDANCE_DURATION)) if duration else float(MAX_SEEDANCE_DURATION)
    target_duration = target_duration_seconds(duration)
    metadata = {
        "path": str(video),
        "duration_seconds": round(duration, 3),
        "raw_target_duration_seconds": round(raw_target_duration, 3),
        "target_duration_seconds": target_duration,
        "duration_rounding_policy": "round half up to an integer; cap at 15 seconds; Seedance supports 4-15 seconds",
        "duration_supported_by_seedance": MIN_SEEDANCE_DURATION <= target_duration <= MAX_SEEDANCE_DURATION,
        "width": width,
        "height": height,
        "source_ratio": source_ratio,
        "target_ratio": target_ratio,
        "ratio": target_ratio,
        "ratio_policy": "match the reference video aspect ratio by choosing the nearest Seedance-supported ratio",
        "fps": fps,
        "audio_track_status": "present" if audio_stream else "absent",
        "sample_count": len(samples),
        "scene_candidate_count": len(scenes),
    }
    scaffold = {
        "source": {
            "path_or_url": str(video),
            "duration_seconds": round(duration, 3),
            "raw_target_duration_seconds": round(raw_target_duration, 3),
            "target_duration_seconds": target_duration,
            "duration_rounding_policy": "round half up to an integer; cap at 15 seconds; Seedance supports 4-15 seconds",
            "duration_supported_by_seedance": MIN_SEEDANCE_DURATION <= target_duration <= MAX_SEEDANCE_DURATION,
            "source_ratio": source_ratio,
            "target_ratio": target_ratio,
            "ratio": target_ratio,
            "ratio_policy": "match the reference video aspect ratio by choosing the nearest Seedance-supported ratio",
            "width": width,
            "height": height,
            "fps": fps,
            "platform_style": "unknown",
            "content_type": "unknown",
        },
        "analysis_assets": {
            "contact_sheet": str(sheet_path),
            "scene_contact_sheet": str(scene_sheet_path) if scenes else "",
            "sampled_frames": samples,
            "scene_candidate_frames": scenes,
            "audio_track_status": metadata["audio_track_status"],
            "ocr_status": "pending",
            "transcript_status": "pending" if audio_stream else "unavailable",
        },
        "copywriting": {
            "spoken_transcript": [],
            "on_screen_text": [],
            "formula": "",
            "hook": "",
            "pain_or_tension": "",
            "product_entry": "",
            "proof_or_demo": "",
            "cta": "",
            "tone": "",
        },
        "shots": [],
        "rhythm": {
            "first_frame_tactic": "",
            "average_shot_seconds": None,
            "cut_density": "",
            "music_or_sfx": "",
            "pace_notes": "",
        },
        "viral_mechanism": {
            "scroll_stop_reason": "",
            "retention_reason": "",
            "conversion_reason": "",
            "risks_to_avoid": [],
        },
    }
    metadata_path = output_dir / "reference-video-metadata.json"
    scaffold_path = output_dir / "reference-analysis-scaffold.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    scaffold_path.write_text(json.dumps(scaffold, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "metadata_path": str(metadata_path),
        "scaffold_path": str(scaffold_path),
        "contact_sheet": str(sheet_path),
        "scene_contact_sheet": str(scene_sheet_path) if scenes else None,
        "metadata": metadata,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract evidence assets for reference-video recreation analysis")
    parser.add_argument("--video", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--sample-count", type=int, default=12)
    parser.add_argument("--scene-threshold", type=float, default=22.0)
    parser.add_argument("--max-scene-frames", type=int, default=16)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        result = analyze(
            Path(args.video).expanduser().resolve(),
            Path(args.output_dir).expanduser().resolve(),
            args.sample_count,
            args.scene_threshold,
            args.max_scene_frames,
        )
        print(json.dumps(result, ensure_ascii=True, indent=2))
    except (ValueError, OSError, av.error.FFmpegError) as exc:
        print(json.dumps({"ok": False, "stage": "reference_analysis", "error": str(exc)}, ensure_ascii=True, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
