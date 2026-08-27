import argparse
import json
from pathlib import Path

import ctranslate2
import faster_whisper
from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-root", required=True)
    parser.add_argument("--marker", required=True)
    args = parser.parse_args()

    WhisperModel(
        "tiny",
        device="cpu",
        compute_type="int8",
        download_root=args.download_root,
    )
    payload = {
        "verified": True,
        "faster_whisper": getattr(faster_whisper, "__version__", "unknown"),
        "ctranslate2": ctranslate2.__version__,
    }
    Path(args.marker).parent.mkdir(parents=True, exist_ok=True)
    Path(args.marker).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
