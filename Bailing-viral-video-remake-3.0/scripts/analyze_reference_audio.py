#!/usr/bin/env python3
"""Extract local audio and transcribe reference-video speech with local ASR.

This script is intentionally API-free. It supports Windows and macOS/Linux by
discovering ffmpeg from common local locations, then trying local ASR backends:

1. faster-whisper Python package
2. openai-whisper Python package
3. whisper.cpp CLI from WHISPER_CPP_BIN

It always writes a machine-readable JSON result. If ASR is unavailable or fails,
the output must be treated as "not extracted", not as "no voiceover".
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_SAMPLE_RATE = 16000
DEFAULT_INSTALL_TIMEOUT = int(os.environ.get("XINGHE_ASR_INSTALL_TIMEOUT", "900"))
DEFAULT_HF_ENDPOINT = "https://hf-mirror.com"


INSTALL_LOG: list[dict[str, Any]] = []


def asr_ready_path() -> Path:
    return Path.home() / ".codex" / "cache" / "xinghe-asr" / "asr_ready.json"


def load_asr_ready() -> dict[str, Any]:
    path = asr_ready_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def apply_asr_environment(ready: dict[str, Any]) -> None:
    endpoint = str(ready.get("hf_endpoint") or os.environ.get("HF_ENDPOINT") or DEFAULT_HF_ENDPOINT)
    os.environ.setdefault("HF_ENDPOINT", endpoint)
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def pip_install(package: str, *, timeout: int | None = None) -> dict[str, Any]:
    timeout = DEFAULT_INSTALL_TIMEOUT if timeout is None else timeout
    start = time.time()
    command = [sys.executable, "-m", "pip", "install", package, "-q"]
    try:
        completed = run(command, timeout=timeout)
        result = {
            "package": package,
            "ok": completed.returncode == 0,
            "seconds": round(time.time() - start, 2),
            "stdout_tail": (completed.stdout or "")[-1200:],
            "stderr_tail": (completed.stderr or "")[-2400:],
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "package": package,
            "ok": False,
            "seconds": round(time.time() - start, 2),
            "error": f"pip install timed out after {timeout}s",
            "stdout_tail": (exc.stdout or "")[-1200:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-2400:] if isinstance(exc.stderr, str) else "",
        }
    INSTALL_LOG.append(result)
    return result


def find_ffmpeg(auto_install: bool = True) -> str | None:
    explicit = os.environ.get("FFMPEG_PATH")
    if explicit and Path(explicit).is_file():
        return explicit
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).is_file():
            return exe
    except Exception:
        pass
    if auto_install:
        pip_install("imageio-ffmpeg")
        try:
            import imageio_ffmpeg  # type: ignore

            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and Path(exe).is_file():
                return exe
        except Exception:
            pass
    return None


def run(command: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def extract_audio(video: Path, wav_path: Path, sample_rate: int, *, auto_install: bool) -> dict[str, Any]:
    ffmpeg = find_ffmpeg(auto_install=auto_install)
    if not ffmpeg:
        return {
            "ok": False,
            "stage": "audio_extract",
            "error": "ffmpeg was not found. Install ffmpeg, set FFMPEG_PATH, or install imageio-ffmpeg.",
        }
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "wav",
        str(wav_path),
    ]
    completed = run(command)
    if completed.returncode != 0 or not wav_path.is_file() or wav_path.stat().st_size == 0:
        return {
            "ok": False,
            "stage": "audio_extract",
            "error": "ffmpeg failed to extract audio",
            "detail": (completed.stderr or completed.stdout)[-4000:],
            "ffmpeg": ffmpeg,
        }
    return {"ok": True, "wav_path": str(wav_path), "ffmpeg": ffmpeg, "sample_rate": sample_rate}


def as_segment(start: float, end: float, text: str, **extra: Any) -> dict[str, Any]:
    item = {"start": round(float(start), 3), "end": round(float(end), 3), "text": text.strip()}
    item.update(extra)
    return item


def text_quality(segments: list[dict[str, Any]]) -> dict[str, Any]:
    text = "".join(str(seg.get("text", "")) for seg in segments)
    total = len(text)
    if total == 0:
        return {"ok": False, "score": 0.0, "issue": "empty"}
    replacement = text.count("\ufffd")
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    latin = sum(1 for ch in text if ("a" <= ch.lower() <= "z") or ch.isdigit())
    bad_ratio = replacement / total
    cjk_ratio = cjk / total
    ok = bad_ratio <= 0.05 and (cjk_ratio >= 0.25 or latin / total >= 0.25)
    issue = "ok" if ok else "possible_mojibake_or_low_text_quality"
    return {
        "ok": ok,
        "score": round(max(0.0, (1 - bad_ratio) * max(cjk_ratio, latin / total)), 3),
        "total_chars": total,
        "replacement_chars": replacement,
        "cjk_ratio": round(cjk_ratio, 3),
        "latin_digit_ratio": round(latin / total, 3),
        "issue": issue,
    }


def transcribe_faster_whisper(wav_path: Path, language: str | None, model: str, *, auto_install: bool) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as exc:
        if not auto_install:
            return {"ok": False, "backend": "faster-whisper", "error": f"not available: {exc}"}
        install = pip_install("faster-whisper")
        if not install.get("ok"):
            return {"ok": False, "backend": "faster-whisper", "error": "auto-install failed", "install": install}
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception as retry_exc:
            return {"ok": False, "backend": "faster-whisper", "error": f"not available after auto-install: {retry_exc}", "install": install}
    try:
        compute_type = os.environ.get("FASTER_WHISPER_COMPUTE_TYPE", "int8")
        device = os.environ.get("FASTER_WHISPER_DEVICE", "cpu")
        whisper = WhisperModel(model, device=device, compute_type=compute_type)
        segments_iter, info = whisper.transcribe(str(wav_path), language=language, vad_filter=True)
        segments = [as_segment(seg.start, seg.end, seg.text, avg_logprob=getattr(seg, "avg_logprob", None)) for seg in segments_iter]
        return {
            "ok": True,
            "backend": "faster-whisper",
            "model": model,
            "language": getattr(info, "language", language),
            "language_probability": getattr(info, "language_probability", None),
            "segments": segments,
            "text_quality": text_quality(segments),
        }
    except Exception as exc:
        return {"ok": False, "backend": "faster-whisper", "error": str(exc)}


def transcribe_openai_whisper(wav_path: Path, language: str | None, model: str) -> dict[str, Any]:
    try:
        import whisper  # type: ignore
    except Exception as exc:
        return {"ok": False, "backend": "openai-whisper", "error": f"not available: {exc}"}
    try:
        whisper_model = whisper.load_model(model)
        result = whisper_model.transcribe(str(wav_path), language=language, fp16=False, verbose=False)
        segments = [
            as_segment(item.get("start", 0), item.get("end", 0), item.get("text", ""))
            for item in result.get("segments", [])
            if str(item.get("text", "")).strip()
        ]
        return {
            "ok": True,
            "backend": "openai-whisper",
            "model": model,
            "language": result.get("language", language),
            "segments": segments,
            "text_quality": text_quality(segments),
        }
    except Exception as exc:
        return {"ok": False, "backend": "openai-whisper", "error": str(exc)}


def parse_whisper_cpp_output(text: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Common whisper.cpp stdout: [00:00:00.000 --> 00:00:02.000] text
        if line.startswith("[") and "-->" in line and "]" in line:
            try:
                timing, content = line[1:].split("]", 1)
                start_raw, end_raw = [part.strip() for part in timing.split("-->", 1)]
                start = timestamp_to_seconds(start_raw)
                end = timestamp_to_seconds(end_raw)
                content = content.strip()
                if content:
                    segments.append(as_segment(start, end, content))
            except Exception:
                continue
    return segments


def timestamp_to_seconds(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    return float(value)


def transcribe_whisper_cpp(wav_path: Path, language: str | None, model: str | None) -> dict[str, Any]:
    binary = os.environ.get("WHISPER_CPP_BIN") or shutil.which("whisper-cli") or shutil.which("main")
    if not binary:
        return {"ok": False, "backend": "whisper.cpp", "error": "not available: set WHISPER_CPP_BIN or put whisper-cli on PATH"}
    model_path = model or os.environ.get("WHISPER_CPP_MODEL")
    if not model_path:
        return {"ok": False, "backend": "whisper.cpp", "error": "missing model path: set WHISPER_CPP_MODEL or pass --whisper-cpp-model"}
    command = [binary, "-m", model_path, "-f", str(wav_path), "-nt"]
    if language:
        command.extend(["-l", language])
    try:
        completed = run(command, timeout=900)
    except Exception as exc:
        return {"ok": False, "backend": "whisper.cpp", "error": str(exc)}
    combined = (completed.stdout or "") + "\n" + (completed.stderr or "")
    segments = parse_whisper_cpp_output(combined)
    if completed.returncode != 0:
        return {"ok": False, "backend": "whisper.cpp", "error": f"exit code {completed.returncode}", "detail": combined[-4000:]}
    return {"ok": True, "backend": "whisper.cpp", "model": model_path, "language": language, "segments": segments, "text_quality": text_quality(segments)}


def choose_transcription(results: list[dict[str, Any]]) -> dict[str, Any]:
    for result in results:
        quality = result.get("text_quality") if isinstance(result.get("text_quality"), dict) else {}
        if result.get("ok") and result.get("segments") and quality.get("ok", True):
            return result
    for result in results:
        if result.get("ok") and result.get("segments"):
            result = dict(result)
            result["needs_correction"] = True
            return result
    for result in results:
        if result.get("ok"):
            return result
    return {"ok": False, "backend": "none", "attempts": results}


def build_voiceover_layer(transcription: dict[str, Any]) -> dict[str, Any]:
    segments = transcription.get("segments") if isinstance(transcription.get("segments"), list) else []
    cleaned = [seg for seg in segments if str(seg.get("text", "")).strip()]
    detected = bool(cleaned)
    if detected:
        quality = transcription.get("text_quality") if isinstance(transcription.get("text_quality"), dict) else {}
        quality_ok = bool(quality.get("ok", True))
        confidence = 0.86 if transcription.get("backend") in {"faster-whisper", "openai-whisper"} and quality_ok else 0.62
        if quality_ok:
            generation_rule = "Final remake must preserve a clear voiceover layer unless the user explicitly removes voiceover."
        else:
            generation_rule = "Speech timing was detected but ASR text quality is low; correct the transcript with OCR/context before adapting voiceover."
        reason = "local ASR produced timestamped speech segments"
    elif transcription.get("ok"):
        confidence = 0.65
        generation_rule = "Do not force voiceover unless OCR/caption evidence or the user requests it."
        reason = "local ASR ran but found no stable speech segments"
    else:
        confidence = 0.0
        generation_rule = "Voiceover was not extracted; do not treat OCR captions as confirmed voiceover. Ask for confirmation or run a working local ASR backend."
        reason = "no local ASR backend succeeded"
    return {
        "detected": detected,
        "confidence": confidence,
        "language": transcription.get("language"),
        "backend": transcription.get("backend"),
        "segments": cleaned,
        "text_quality": transcription.get("text_quality"),
        "needs_correction": bool(transcription.get("needs_correction")),
        "relationship_to_ocr": "not_evaluated_by_audio_script",
        "reason": reason,
        "generation_rule": generation_rule,
    }


def write_safe_transcript_files(payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
    layer = payload.get("voiceover_layer") if isinstance(payload.get("voiceover_layer"), dict) else {}
    segments = layer.get("segments") if isinstance(layer.get("segments"), list) else []
    safe_segments: list[dict[str, Any]] = []
    lines: list[str] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        start = float(segment.get("start", 0) or 0)
        end = float(segment.get("end", 0) or 0)
        item = {"start": round(start, 3), "end": round(end, 3), "text": text}
        safe_segments.append(item)
        lines.append(f"{start:.2f}-{end:.2f}s: {text}")
    transcript_json = output_dir / "reference_audio_transcript_utf8.json"
    transcript_txt = output_dir / "reference_audio_transcript_utf8.txt"
    unicode_escape_txt = output_dir / "reference_audio_transcript_unicode_escape.txt"
    transcript_json.write_text(
        json.dumps(
            {
                "encoding": "utf-8",
                "terminal_display_is_not_authoritative": True,
                "read_rule": "Read this file with UTF-8 APIs. Do not copy ASR text from PowerShell terminal rendering.",
                "segments": safe_segments,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    transcript_txt.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    unicode_escape_txt.write_text(
        "\n".join(line.encode("unicode_escape").decode("ascii") for line in lines) + ("\n" if lines else ""),
        encoding="ascii",
    )
    return {
        "utf8_json": str(transcript_json),
        "utf8_txt": str(transcript_txt),
        "unicode_escape_txt": str(unicode_escape_txt),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract audio and run local ASR for a reference video")
    parser.add_argument("--video", required=True, help="Local reference video path")
    parser.add_argument("--output-dir", required=True, help="Directory for audio/transcript artifacts")
    parser.add_argument("--language", default=None, help="Optional ASR language, e.g. zh or en")
    parser.add_argument("--model", default=None, help="Whisper model name for Python backends; default reads asr_ready.json then falls back to base")
    parser.add_argument("--whisper-cpp-model", default=None, help="Path to whisper.cpp model file")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--no-auto-install", action="store_true", help="Disable automatic local dependency installation")
    parser.add_argument("--install-timeout", type=int, default=DEFAULT_INSTALL_TIMEOUT, help="Seconds allowed for each automatic pip install")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    ready = load_asr_ready()
    apply_asr_environment(ready)
    global DEFAULT_INSTALL_TIMEOUT
    DEFAULT_INSTALL_TIMEOUT = args.install_timeout
    auto_install = not args.no_auto_install
    model = args.model or str(ready.get("model") or os.environ.get("WHISPER_MODEL") or "base")
    video = Path(args.video).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "reference_audio.wav"
    result_path = output_dir / "reference_audio_analysis.json"

    payload: dict[str, Any] = {
        "ok": False,
        "video": str(video),
        "audio_path": str(wav_path),
        "transcript_status": "unavailable",
        "voiceover_layer": {
            "detected": False,
            "confidence": 0.0,
            "segments": [],
            "generation_rule": "Voiceover was not extracted; do not treat OCR captions as confirmed voiceover.",
        },
    }
    try:
        if not video.is_file():
            raise FileNotFoundError(f"Video not found: {video}")
        audio = extract_audio(video, wav_path, args.sample_rate, auto_install=auto_install)
        payload["audio_extract"] = audio
        payload["auto_install"] = {"enabled": auto_install, "attempts": INSTALL_LOG}
        if not audio.get("ok"):
            payload["audio_track_status"] = "unavailable"
            payload["error"] = audio.get("error")
        else:
            payload["audio_track_status"] = "present"
            attempts = [
                transcribe_faster_whisper(wav_path, args.language, model, auto_install=auto_install),
                transcribe_openai_whisper(wav_path, args.language, model),
                transcribe_whisper_cpp(wav_path, args.language, args.whisper_cpp_model),
            ]
            payload["asr_ready"] = {"path": str(asr_ready_path()), "loaded": bool(ready), "model": model, "hf_endpoint": os.environ.get("HF_ENDPOINT")}
            payload["auto_install"] = {"enabled": auto_install, "attempts": INSTALL_LOG}
            transcription = choose_transcription(attempts)
            payload["asr_attempts"] = attempts
            payload["selected_transcription"] = transcription
            payload["voiceover_layer"] = build_voiceover_layer(transcription)
            payload["transcript_status"] = "tool_generated" if payload["voiceover_layer"]["detected"] else ("tool_generated_empty" if transcription.get("ok") else "unavailable")
            payload["ok"] = bool(transcription.get("ok"))
    except Exception as exc:
        payload["error"] = str(exc)
    payload["terminal_display_is_not_authoritative"] = True
    payload["encoding_policy"] = {
        "files_are_utf8": True,
        "do_not_use_terminal_rendered_chinese_as_transcript": True,
        "authoritative_fields": [
            "voiceover_layer.segments",
            "selected_transcription.segments",
            "safe_transcript_files.utf8_json",
        ],
    }
    payload["safe_transcript_files"] = write_safe_transcript_files(payload, output_dir)
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload.get("ok"), "result_path": str(result_path), "transcript_status": payload.get("transcript_status")}, ensure_ascii=True, indent=2))
    if not payload.get("ok"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
