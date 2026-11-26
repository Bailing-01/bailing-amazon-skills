#!/usr/bin/env python3
"""whisper_transcribe.py — transcribe audio to SRT using faster-whisper.

Called by local_video.sh after ffmpeg has produced a 16 kHz mono WAV.
Imports faster_whisper lazily inside transcribe() so the module loads cheap
when the user is just running --help or hitting an arg-parse error.

Usage:
  python3 whisper_transcribe.py --input audio.wav --output out.srt [--model medium] [--language zh]

  # With speaker diarization (Q4a — needs pyannote.audio + a HuggingFace token):
  python3 whisper_transcribe.py --input audio.wav --output out.srt --diarize

Models (auto-downloaded by faster-whisper on first use, cached in ~/.cache):
  tiny       ~75 MB   fastest, lowest quality
  base       ~150 MB
  small      ~500 MB
  medium     ~1.5 GB  recommended default
  large-v3   ~3 GB    best quality, slower

Language: pass `zh` / `en` / `ja` / etc. to skip auto-detect (faster + more
accurate when you know the language already). Default = auto-detect.

Diarization (--diarize):
  Uses pyannote.audio's `speaker-diarization-3.1` pipeline. Lazy-installs
  pyannote.audio on first use. Requires:
    1. A HuggingFace token in env (HUGGINGFACE_TOKEN or HF_TOKEN). Free at
       https://hf.co/settings/tokens
    2. Accept model card terms at https://hf.co/pyannote/speaker-diarization-3.1
       and https://hf.co/pyannote/segmentation-3.0
  When enabled, each SRT cue is prefixed with `SPEAKER_NN: ` so srt_to_transcript
  --jsonl can pull the speaker into a structured field.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def format_ts(seconds: float) -> str:
    """SRT timestamp: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe(
    audio: Path,
    output: Path,
    model_name: str,
    language: str | None,
    diarize: bool = False,
    hf_token: str | None = None,
) -> dict:
    # Lazy import — keeps `--help` cheap and isolates the heavy dep.
    from faster_whisper import WhisperModel

    print(f"[whisper] loading model: {model_name}", file=sys.stderr)
    # int8 is the fastest reasonable compute_type on Apple Silicon CPU; users
    # with a CUDA GPU can override via env (FASTER_WHISPER_DEVICE=cuda).
    import os
    device = os.environ.get("FASTER_WHISPER_DEVICE", "auto")
    compute_type = os.environ.get("FASTER_WHISPER_COMPUTE", "int8")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    print(f"[whisper] transcribing {audio.name} ...", file=sys.stderr)
    segments_iter, info = model.transcribe(
        str(audio),
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    print(
        f"[whisper] detected language: {info.language} "
        f"(prob: {info.language_probability:.2f}, duration: {info.duration:.1f}s)",
        file=sys.stderr,
    )

    # Materialize segments — diarization needs them as a list and we want to
    # iterate twice (assign speakers, then write SRT).
    whisper_segments = [
        {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        for seg in segments_iter
    ]

    speaker_map: dict[int, str] = {}
    diarize_info: dict = {}
    if diarize:
        speaker_map, diarize_info = run_diarization(audio, whisper_segments, hf_token)

    seg_count = 0
    with output.open("w", encoding="utf-8") as f:
        for i, seg in enumerate(whisper_segments, 1):
            speaker = speaker_map.get(i - 1)
            text = seg["text"]
            if speaker:
                text = f"{speaker}: {text}"
            f.write(f"{i}\n")
            f.write(f"{format_ts(seg['start'])} --> {format_ts(seg['end'])}\n")
            f.write(f"{text}\n\n")
            seg_count = i

    print(f"[whisper] wrote {seg_count} segments → {output}", file=sys.stderr)
    result = {
        "segments": seg_count,
        "language": info.language,
        "duration": info.duration,
    }
    if diarize:
        result["diarization"] = diarize_info
    return result


def run_diarization(
    audio: Path,
    whisper_segments: list[dict],
    hf_token: str | None,
) -> tuple[dict[int, str], dict]:
    """Run pyannote.audio speaker-diarization-3.1 on the audio. Returns:
       (segment_idx → speaker label, info dict)

    Lazy-installs pyannote.audio. Requires HF token in env or arg.
    """
    import os
    token = hf_token or os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
    if not token:
        print(
            "ERROR: --diarize requires a HuggingFace token. Set HF_TOKEN env var "
            "(get one at https://hf.co/settings/tokens) and accept model card "
            "at https://hf.co/pyannote/speaker-diarization-3.1.",
            file=sys.stderr,
        )
        return {}, {"error": "no_hf_token"}

    # Lazy install pyannote.audio
    try:
        from pyannote.audio import Pipeline  # type: ignore[import-not-found]
    except ImportError:
        print("[diarize] pyannote.audio not installed.", file=sys.stderr)
        if os.environ.get("AUTO_YES") != "1" and not sys.stdin.isatty():
            print(
                "[diarize] non-tty stdin and AUTO_YES not set; skipping diarization. "
                "Install manually: python3 -m pip install pyannote.audio",
                file=sys.stderr,
            )
            return {}, {"error": "not_installed"}
        if os.environ.get("AUTO_YES") == "1":
            print("[diarize] AUTO_YES=1 → installing pyannote.audio", file=sys.stderr)
        else:
            ans = input("[diarize] python3 -m pip install pyannote.audio? [y/N] ")
            if not ans.strip().lower().startswith("y"):
                print("[diarize] declined; skipping diarization", file=sys.stderr)
                return {}, {"error": "user_declined"}
        import subprocess
        rc = subprocess.call(
            [sys.executable, "-m", "pip", "install", "pyannote.audio"],
            stdout=sys.stderr, stderr=sys.stderr,
        )
        if rc != 0:
            print(f"[diarize] pip install failed (exit {rc})", file=sys.stderr)
            return {}, {"error": f"pip_install_failed_{rc}"}
        from pyannote.audio import Pipeline  # type: ignore[import-not-found,no-redef]

    print("[diarize] loading pyannote.audio speaker-diarization-3.1 ...", file=sys.stderr)
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token,
        )
    except Exception as e:
        print(
            f"[diarize] failed to load pipeline: {e}\n"
            "Make sure you've accepted the model card terms at "
            "https://hf.co/pyannote/speaker-diarization-3.1 and "
            "https://hf.co/pyannote/segmentation-3.0",
            file=sys.stderr,
        )
        return {}, {"error": f"load_failed: {type(e).__name__}"}

    print(f"[diarize] running on {audio.name} ...", file=sys.stderr)
    try:
        diarization = pipeline(str(audio))
    except Exception as e:
        print(f"[diarize] inference failed: {e}", file=sys.stderr)
        return {}, {"error": f"inference_failed: {type(e).__name__}"}

    # Build (start, end, speaker) turn list
    turns: list[tuple[float, float, str]] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append((turn.start, turn.end, str(speaker)))
    speakers_seen: set[str] = {t[2] for t in turns}
    print(f"[diarize] {len(turns)} turns, {len(speakers_seen)} speakers", file=sys.stderr)

    # Assign each whisper segment to the speaker whose turn has max overlap
    speaker_map: dict[int, str] = {}
    for i, seg in enumerate(whisper_segments):
        best_speaker: str | None = None
        best_overlap = 0.0
        for ts, te, sp in turns:
            overlap = max(0.0, min(seg["end"], te) - max(seg["start"], ts))
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = sp
        if best_speaker:
            speaker_map[i] = best_speaker

    return speaker_map, {
        "turns": len(turns),
        "speakers": len(speakers_seen),
        "labels": sorted(speakers_seen),
        "segments_assigned": len(speaker_map),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe audio to SRT using faster-whisper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, type=Path,
                        help="Input audio (WAV recommended, 16 kHz mono).")
    parser.add_argument("--output", required=True, type=Path,
                        help="Output SRT path.")
    parser.add_argument("--model", default="medium",
                        help="Whisper model: tiny / base / small / medium / large-v3 (default: medium).")
    parser.add_argument("--language", default=None,
                        help="Force language (zh / en / ja / ...). Default: auto-detect.")
    parser.add_argument("--diarize", action="store_true",
                        help="Run pyannote.audio speaker diarization, prefix each cue with SPEAKER_NN")
    parser.add_argument("--hf-token", default=None,
                        help="HuggingFace token for pyannote (default: env HF_TOKEN/HUGGINGFACE_TOKEN)")
    parser.add_argument("--allow-no-diarization", action="store_true",
                        help="When --diarize requested but pyannote/HF token unavailable, "
                             "silently fall back to no-diarization (default: hard-fail). "
                             "Use only when you've decided diarization is best-effort.")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Iter 26 (codex 4-audit P2): when --diarize fails and --allow-no-diarization
    # is NOT set, do NOT leave the bare-no-speaker SRT on disk. Use a tmp
    # output, only swap to final path on success.
    final_output = args.output
    use_tmp = args.diarize and not args.allow_no_diarization
    write_target = (
        final_output.with_suffix(final_output.suffix + ".tmp") if use_tmp else final_output
    )
    try:
        result = transcribe(
            args.input, write_target, args.model, args.language,
            diarize=args.diarize, hf_token=args.hf_token,
        )
        if args.diarize and not args.allow_no_diarization:
            d_info = result.get("diarization", {})
            if d_info.get("error"):
                # Delete the tmp SRT (no-speaker fallback) — caller asked for
                # diarized output or nothing.
                try:
                    write_target.unlink()
                except OSError:
                    pass
                print(
                    f"ERROR: --diarize requested but failed: {d_info['error']}\n"
                    f"       Tmp output {write_target.name} deleted, target {final_output.name} unchanged.\n"
                    f"       To accept the no-diarize fallback, re-run with --allow-no-diarization.",
                    file=sys.stderr,
                )
                return 5
            # Diarize succeeded — promote tmp to final
            if use_tmp:
                if final_output.exists():
                    final_output.unlink()
                write_target.rename(final_output)
    except ImportError as e:
        print(f"ERROR: faster-whisper not importable: {e}", file=sys.stderr)
        print("       Install with: pip3 install faster-whisper", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: transcription failed: {e}", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
