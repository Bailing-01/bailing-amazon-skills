import argparse
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path


STRATEGY = "semantic-scene-v2"
MANDATORY_REASONS = {"opening", "ending"}


def run(command):
    return subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def probe_video(ffprobe, video):
    result = run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=avg_frame_rate,r_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            video,
        ]
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "30/1"
    fps = float(Fraction(rate))
    duration = float(data["format"]["duration"])
    return duration, fps


def detect_scene_changes(ffmpeg, video, threshold):
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "info",
            "-i",
            video,
            "-vf",
            f"select=gt(scene\\,{threshold}),showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:])
    return [
        float(value)
        for value in re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", result.stderr)
    ]


def transcript_boundaries(path):
    if not path or not Path(path).is_file():
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    boundaries = []
    previous = -10.0
    for segment in data.get("segments", []):
        start = float(segment.get("start", 0))
        if start - previous >= 2.5:
            boundaries.append(start)
            previous = start
    return boundaries


def even_pick(values, count):
    if count <= 0:
        return []
    if len(values) <= count:
        return values
    if count == 1:
        return [values[len(values) // 2]]
    indexes = {round(i * (len(values) - 1) / (count - 1)) for i in range(count)}
    return [values[index] for index in sorted(indexes)]


def add_candidate(selected, timestamp, reason, duration, minimum_gap=0.2):
    timestamp = min(max(float(timestamp), 0.0), max(duration - 0.04, 0.0))
    for item in selected:
        if abs(item["timestamp"] - timestamp) < minimum_gap:
            if reason not in item["reasons"]:
                item["reasons"].append(reason)
            return
    selected.append({"timestamp": timestamp, "reasons": [reason]})


def build_candidates(duration, scenes, transcript, maximum):
    selected = []

    for timestamp in (0, 0.5, 1, 1.5, 2, 2.5, 3):
        if timestamp < duration:
            add_candidate(selected, timestamp, "opening", duration)
    for timestamp in (duration - 3, duration - 2, duration - 1, duration - 0.1):
        if timestamp >= 0:
            add_candidate(selected, timestamp, "ending", duration)

    scene_values = []
    for timestamp in scenes:
        if all(abs(timestamp - item["timestamp"]) >= 0.4 for item in selected):
            scene_values.append(timestamp)
    mandatory_count = len(selected)
    effective_maximum = max(maximum, mandatory_count)
    reserved = min(4, max(0, effective_maximum - len(selected)))
    scene_slots = max(0, effective_maximum - len(selected) - reserved)
    for timestamp in even_pick(scene_values, scene_slots):
        add_candidate(selected, timestamp, "scene-change", duration, 0.35)

    for timestamp in transcript:
        if len(selected) >= effective_maximum:
            break
        if all(abs(timestamp - item["timestamp"]) >= 1.0 for item in selected):
            add_candidate(selected, timestamp, "speech-boundary", duration, 0.8)

    timestamp = 5.0
    while timestamp < duration - 3 and len(selected) < effective_maximum:
        if all(abs(timestamp - item["timestamp"]) > 2.5 for item in selected):
            add_candidate(selected, timestamp, "long-shot-fallback", duration, 0.5)
        timestamp += 5.0

    selected = sorted(selected, key=lambda item: item["timestamp"])
    for item in selected:
        item["mandatory"] = bool(MANDATORY_REASONS.intersection(item["reasons"]))
    return selected, {
        "requested_max_frames": maximum,
        "effective_max_frames": effective_maximum,
        "mandatory_frame_count": mandatory_count,
        "cap_raised_for_mandatory_frames": mandatory_count > maximum,
        "scene_candidates_not_selected": max(0, len(scene_values) - scene_slots),
    }


def extract_frames(ffmpeg, video, output_dir, candidates, fps):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("frame_*.jpg"):
        old.unlink()

    frame_map = {}
    for item in candidates:
        number = max(0, round(item["timestamp"] * fps))
        if number in frame_map:
            frame_map[number]["reasons"].extend(
                reason
                for reason in item["reasons"]
                if reason not in frame_map[number]["reasons"]
            )
        else:
            frame_map[number] = item

    numbers = sorted(frame_map)
    expression = "+".join(f"eq(n\\,{number})" for number in numbers)
    run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            video,
            "-map",
            "0:v:0",
            "-vf",
            f"select={expression},scale=960:-2:force_original_aspect_ratio=decrease",
            "-fps_mode",
            "vfr",
            str(output / "frame_%03d.jpg"),
        ]
    )

    files = sorted(output.glob("frame_*.jpg"))
    if len(files) != len(numbers):
        raise RuntimeError(
            f"Frame extraction incomplete: requested {len(numbers)}, produced {len(files)}"
        )
    records = []
    for number, file_path in zip(numbers, files):
        item = frame_map[number]
        records.append(
            {
                "file": file_path.name,
                "timestamp": round(number / fps, 3),
                "reasons": item["reasons"],
                "mandatory": item.get("mandatory", False),
                "quality_status": "pending-visual-review",
            }
        )
    return records


def coverage_audit(records, duration, cap_stats):
    timestamps = [item["timestamp"] for item in records]
    gaps = []
    points = [0.0, *timestamps, duration]
    for left, right in zip(points, points[1:]):
        if right - left > 5.5:
            gaps.append({"start": round(left, 3), "end": round(right, 3)})

    warnings = []
    if cap_stats["cap_raised_for_mandatory_frames"]:
        warnings.append("requested cap was lower than mandatory frame count")
    if cap_stats["scene_candidates_not_selected"]:
        warnings.append("some scene-change candidates were not selected; visual audit required")
    if gaps:
        warnings.append("timeline contains gaps longer than 5.5 seconds")

    return {
        "status": "visual-review-required" if warnings else "machine-check-passed",
        "timeline_gaps_over_5_5s": gaps,
        "warnings": warnings,
        "required_visual_checks": [
            "opening-hook-complete",
            "ending-cta-complete",
            "scene-changes-covered",
            "speech-to-picture-aligned",
            "text-price-offer-changes-covered",
            "no-black-flash-transition-or-blurry-evidence-frame",
        ],
        "block_step_2_until_visual_checks_pass": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("frames")
    parser.add_argument("--transcript")
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--ffprobe", required=True)
    parser.add_argument("--max-frames", type=int, default=30)
    parser.add_argument("--scene-threshold", type=float, default=0.28)
    args = parser.parse_args()

    duration, fps = probe_video(args.ffprobe, args.video)
    scenes = detect_scene_changes(
        args.ffmpeg, args.video, args.scene_threshold
    )
    boundaries = transcript_boundaries(args.transcript)
    candidates, cap_stats = build_candidates(
        duration, scenes, boundaries, args.max_frames
    )
    records = extract_frames(
        args.ffmpeg, args.video, args.frames, candidates, fps
    )

    payload = {
        "schema_version": 1,
        "strategy": STRATEGY,
        "duration_seconds": duration,
        "fps": fps,
        "scene_threshold": args.scene_threshold,
        "detected_scene_changes": len(scenes),
        "frame_count": len(records),
        "cap": cap_stats,
        "coverage_audit": coverage_audit(records, duration, cap_stats),
        "frames": records,
    }
    index = Path(args.frames).parent / "frames.json"
    index.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
