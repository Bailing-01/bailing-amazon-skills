import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


PIPELINE_ID = "tk-content-pipeline/v1"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def run(command, capture=False):
    return subprocess.run(
        [str(value) for value in command],
        check=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def resolve_tool(explicit, name):
    if explicit:
        candidate = Path(explicit)
        if candidate.is_file():
            return str(candidate.resolve())
        raise FileNotFoundError(f"Tool does not exist: {candidate}")
    located = shutil.which(name)
    if located:
        return located
    if os.name == "nt":
        portable = (
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "tianguo-video"
            / "tools"
            / "ffmpeg"
            / "bin"
            / f"{name}.exe"
        )
        if portable.is_file():
            return str(portable)
    raise FileNotFoundError(f"{name} is missing. Run the platform setup script.")


def canonical_video(item, manifest, manifest_dir):
    account = item.get("account") or manifest.get("account") or {}
    metrics = item.get("metrics") or {}
    acquisition = item.get("acquisition") or {}
    local_value = item.get("local_path") or item.get("video") or ""
    local_path = Path(local_value) if local_value else None
    if local_path and not local_path.is_absolute():
        local_path = manifest_dir / local_path
    video_id = str(item.get("video_id") or item.get("id") or "").strip()
    source_url = str(item.get("source_url") or item.get("url") or "").strip()
    if not video_id and source_url:
        match = re.search(r"/video/(\d+)", source_url)
        if match:
            video_id = match.group(1)
    return {
        "video_id": video_id,
        "source_url": source_url,
        "local_path": str(local_path.resolve()) if local_path and local_path.exists() else str(local_path or ""),
        "published_at": item.get("published_at") or item.get("created") or "",
        "metrics": {
            "plays": metrics.get("plays", item.get("plays")),
            "likes": metrics.get("likes", item.get("likes")),
            "comments": metrics.get("comments", item.get("comments")),
            "shares": metrics.get("shares", item.get("shares")),
        },
        "rank": item.get("rank"),
        "account": account,
        "acquisition": {
            "status": acquisition.get("status", "unknown"),
            "error": acquisition.get("error"),
        },
    }


def validate_manifest(data):
    if data.get("pipeline_id") != PIPELINE_ID:
        raise ValueError(f"pipeline_id must be {PIPELINE_ID}")
    if data.get("artifact_type") != "account_manifest":
        raise ValueError("artifact_type must be account_manifest")
    if not isinstance(data.get("videos"), list):
        raise ValueError("videos must be an array")


def download_video(source, videos_dir):
    parsed = urlparse(source["source_url"])
    host = parsed.hostname or ""
    if not (host == "tiktok.com" or host.endswith(".tiktok.com")):
        raise ValueError("Only public TikTok URLs are accepted in account manifests")
    if not source["video_id"]:
        raise ValueError("video_id is required when the URL cannot provide it")
    existing = next(
        (
            path
            for extension in VIDEO_EXTENSIONS
            if (path := videos_dir / f"{source['video_id']}{extension}").is_file()
            and path.stat().st_size >= 1024
        ),
        None,
    )
    if existing:
        return existing.resolve()
    run(
        [
            sys.executable,
            "-m",
            "gallery_dl",
            "--filter",
            "type == 'video' and extension == 'mp4'",
            "--directory",
            videos_dir,
            "--filename",
            "{id}.{extension}",
            "--",
            source["source_url"],
        ]
    )
    output = videos_dir / f"{source['video_id']}.mp4"
    if not output.is_file() or output.stat().st_size < 1024:
        raise RuntimeError("gallery-dl finished without a readable MP4")
    return output.resolve()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def transcript_valid(path, model):
    try:
        payload = read_json(path)
        return payload.get("model") == model and isinstance(payload.get("segments"), list)
    except (OSError, ValueError, TypeError):
        return False


def frames_valid(path):
    try:
        payload = read_json(path)
        return (
            payload.get("strategy") in {"semantic-scene-v1", "semantic-scene-v2"}
            and payload.get("frame_count", 0) > 0
        )
    except (OSError, ValueError, TypeError):
        return False


def prepare_media(source, video, cache_root, ffmpeg, ffprobe, model):
    digest = sha256(video)
    cache = cache_root / digest
    frames = cache / "frames"
    cache.mkdir(parents=True, exist_ok=True)
    frames.mkdir(parents=True, exist_ok=True)
    metadata = cache / "metadata.json"
    audio = cache / "audio.wav"
    transcript = cache / "transcript.json"
    frames_index = cache / "frames.json"
    if not metadata.is_file() or metadata.stat().st_size < 10:
        result = run(
            [
                ffprobe,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                "--",
                video,
            ],
            capture=True,
        )
        metadata.write_text(result.stdout, encoding="utf-8")
    if not audio.is_file() or audio.stat().st_size < 44:
        run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                video,
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                audio,
            ]
        )
    return {
        "source_video": source,
        "video_path": str(video),
        "video_sha256": digest,
        "cache_dir": str(cache),
        "metadata_path": str(metadata),
        "audio_path": str(audio),
        "transcript_path": str(transcript),
        "frames_dir": str(frames),
        "frames_index_path": str(frames_index),
        "model": model,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Prepare every usable video in a tk-content-pipeline/v1 account manifest."
    )
    parser.add_argument("account_manifest")
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--model", choices=["base", "small", "medium"], default="small")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    parser.add_argument("--output")
    args = parser.parse_args()

    manifest_path = Path(args.account_manifest).resolve()
    manifest = read_json(manifest_path)
    validate_manifest(manifest)
    ffmpeg = resolve_tool(args.ffmpeg, "ffmpeg")
    ffprobe = resolve_tool(args.ffprobe, "ffprobe")
    work_dir = Path(args.work_dir).resolve()
    videos_dir = work_dir / "videos"
    cache_root = work_dir / ".video-cache"
    videos_dir.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)

    prepared = []
    failed = []
    for raw_item in manifest["videos"]:
        source = canonical_video(raw_item, manifest, manifest_path.parent)
        try:
            video = Path(source["local_path"]) if source["local_path"] else None
            if not video or not video.is_file():
                if not source["source_url"]:
                    raise FileNotFoundError("local_path is missing and source_url is empty")
                video = download_video(source, videos_dir)
            if video.suffix.lower() not in VIDEO_EXTENSIONS:
                raise ValueError(f"Unsupported video extension: {video.suffix}")
            prepared.append(
                prepare_media(source, video.resolve(), cache_root, ffmpeg, ffprobe, args.model)
            )
        except Exception as exc:  # keep a batch moving while preserving exact failures
            failed.append({"source_video": source, "error": str(exc)})

    jobs = [
        {
            "id": item["source_video"]["video_id"] or item["video_sha256"][:12],
            "audio": item["audio_path"],
            "output": item["transcript_path"],
        }
        for item in prepared
        if not transcript_valid(item["transcript_path"], args.model)
    ]
    jobs_path = work_dir / "transcription-jobs.json"
    write_json(jobs_path, jobs)
    batch_result = {"completed": [], "failed": []}
    if jobs:
        command = [
            sys.executable,
            str(Path(__file__).with_name("transcribe_batch_faster_whisper.py")),
            str(jobs_path),
            "--model",
            args.model,
        ]
        if os.name == "nt":
            model_root = Path(os.environ.get("LOCALAPPDATA", "")) / "tianguo-video" / "models"
        else:
            model_root = Path.home() / "Library" / "Caches" / "tianguo-video" / "models"
        command.extend(["--download-root", str(model_root)])
        result = run(command, capture=True)
        batch_result = json.loads(result.stdout)

    usable = []
    extractor = Path(__file__).with_name("extract-semantic-frames.py")
    for item in prepared:
        if not transcript_valid(item["transcript_path"], args.model):
            failed.append(
                {"source_video": item["source_video"], "error": "transcription failed"}
            )
            continue
        if not frames_valid(item["frames_index_path"]):
            run(
                [
                    sys.executable,
                    extractor,
                    item["video_path"],
                    item["frames_dir"],
                    "--transcript",
                    item["transcript_path"],
                    "--ffmpeg",
                    ffmpeg,
                    "--ffprobe",
                    ffprobe,
                    "--max-frames",
                    "30",
                ],
                capture=True,
            )
        item["frames_index"] = read_json(item["frames_index_path"])
        usable.append(item)

    payload = {
        "pipeline_id": PIPELINE_ID,
        "artifact_type": "prepared_media_manifest",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(manifest_path),
        "model": args.model,
        "videos": usable,
        "failed_videos": failed,
        "batch_transcription": batch_result,
    }
    output = Path(args.output).resolve() if args.output else work_dir / "prepared_media_manifest.json"
    write_json(output, payload)
    print(json.dumps({"output": str(output), "prepared": len(usable), "failed": len(failed)}))
    if not usable:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
