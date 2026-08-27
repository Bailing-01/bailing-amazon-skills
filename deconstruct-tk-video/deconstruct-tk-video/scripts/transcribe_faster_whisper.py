import argparse
import json
import os
import platform
from pathlib import Path

from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audio")
    parser.add_argument("output")
    parser.add_argument("--model", default="small")
    parser.add_argument("--language")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--download-root")
    args = parser.parse_args()

    device = args.device
    if device == "auto":
        device = "cuda" if platform.system() == "Windows" and os.system("nvidia-smi >NUL 2>&1") == 0 else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    try:
        model = WhisperModel(
            args.model,
            device=device,
            compute_type=compute_type,
            download_root=args.download_root,
        )
    except Exception:
        if device != "cuda":
            raise
        device, compute_type = "cpu", "int8"
        model = WhisperModel(
            args.model,
            device=device,
            compute_type=compute_type,
            download_root=args.download_root,
        )

    segments, info = model.transcribe(
        args.audio,
        language=args.language,
        vad_filter=True,
        beam_size=5,
    )
    payload = {
        "language": info.language,
        "language_probability": info.language_probability,
        "device": device,
        "model": args.model,
        "segments": [
            {"start": item.start, "end": item.end, "text": item.text.strip()}
            for item in segments
        ],
    }
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
