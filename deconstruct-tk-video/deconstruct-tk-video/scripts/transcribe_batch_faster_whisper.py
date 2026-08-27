import argparse
import json
import os
import platform
from pathlib import Path

from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jobs_json")
    parser.add_argument("--model", default="small")
    parser.add_argument("--language")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--download-root")
    args = parser.parse_args()

    jobs = json.loads(Path(args.jobs_json).read_text(encoding="utf-8-sig"))
    if not jobs:
        print(json.dumps({"completed": [], "failed": []}))
        return

    device = args.device
    if device == "auto":
        device = "cuda" if platform.system() == "Windows" and os.system("nvidia-smi >NUL 2>&1") == 0 else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    try:
        model = WhisperModel(args.model, device=device, compute_type=compute_type, download_root=args.download_root)
    except Exception:
        if device != "cuda":
            raise
        device, compute_type = "cpu", "int8"
        model = WhisperModel(args.model, device=device, compute_type=compute_type, download_root=args.download_root)

    completed, failed = [], []
    for job in jobs:
        try:
            segments, info = model.transcribe(job["audio"], language=args.language, vad_filter=True, beam_size=5)
            payload = {
                "language": info.language,
                "language_probability": info.language_probability,
                "device": device,
                "model": args.model,
                "source": "faster-whisper-batch",
                "segments": [
                    {"start": item.start, "end": item.end, "text": item.text.strip()}
                    for item in segments
                ],
            }
            Path(job["output"]).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            completed.append(job.get("id", job["audio"]))
        except Exception as exc:
            failed.append({"id": job.get("id", job["audio"]), "error": str(exc)})
    print(json.dumps({"completed": completed, "failed": failed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
