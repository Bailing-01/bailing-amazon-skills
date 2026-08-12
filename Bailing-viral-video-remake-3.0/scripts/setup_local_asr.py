#!/usr/bin/env python3
"""Prepare local ASR for reference-video voiceover analysis.

This script is designed to be run during skill installation or first use. It is
local-only and API-free. It installs faster-whisper when missing, downloads and
loads a small local model, then writes ~/.codex/cache/xinghe-asr/asr_ready.json.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_HF_ENDPOINT = "https://hf-mirror.com"
DEFAULT_MODEL = "base"
DEFAULT_TIMEOUT = int(os.environ.get("XINGHE_ASR_SETUP_TIMEOUT", "900"))


def cache_dir() -> Path:
    return Path.home() / ".codex" / "cache" / "xinghe-asr"


def ready_path() -> Path:
    return cache_dir() / "asr_ready.json"


def run(command: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def pip_install(package: str, timeout: int) -> dict[str, Any]:
    start = time.time()
    try:
        completed = run([sys.executable, "-m", "pip", "install", package, "-q"], timeout=timeout)
        return {
            "package": package,
            "ok": completed.returncode == 0,
            "seconds": round(time.time() - start, 2),
            "stdout_tail": (completed.stdout or "")[-1200:],
            "stderr_tail": (completed.stderr or "")[-2400:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "package": package,
            "ok": False,
            "seconds": round(time.time() - start, 2),
            "error": f"pip install timed out after {timeout}s",
            "stdout_tail": (exc.stdout or "")[-1200:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-2400:] if isinstance(exc.stderr, str) else "",
        }


def ensure_faster_whisper(timeout: int) -> dict[str, Any]:
    try:
        import faster_whisper  # type: ignore  # noqa: F401

        return {"ok": True, "installed": True, "install": None}
    except Exception as exc:
        install = pip_install("faster-whisper", timeout)
        if not install.get("ok"):
            return {"ok": False, "installed": False, "error": f"faster-whisper unavailable: {exc}", "install": install}
        try:
            import faster_whisper  # type: ignore  # noqa: F401

            return {"ok": True, "installed": True, "install": install}
        except Exception as retry_exc:
            return {"ok": False, "installed": False, "error": str(retry_exc), "install": install}


def persist_user_env(name: str, value: str) -> dict[str, Any]:
    if platform.system().lower() == "windows":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            return {"ok": True, "scope": "HKCU\\Environment", "name": name, "value": value}
        except Exception as exc:
            return {"ok": False, "name": name, "error": str(exc)}
    shell = os.environ.get("SHELL", "")
    return {"ok": False, "name": name, "error": f"automatic persistent env not implemented for shell {shell}; ready json will still be used"}


def load_model(model: str, device: str, compute_type: str, timeout: int) -> dict[str, Any]:
    start = time.time()
    try:
        from faster_whisper import WhisperModel  # type: ignore

        WhisperModel(model, device=device, compute_type=compute_type)
        return {"ok": True, "model": model, "device": device, "compute_type": compute_type, "seconds": round(time.time() - start, 2)}
    except Exception as exc:
        return {"ok": False, "model": model, "device": device, "compute_type": compute_type, "seconds": round(time.time() - start, 2), "error": str(exc)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install and verify local ASR for Xinghe viral video remake")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="faster-whisper model to prepare; base is recommended for Chinese")
    parser.add_argument("--device", default=os.environ.get("FASTER_WHISPER_DEVICE", "cpu"))
    parser.add_argument("--compute-type", default=os.environ.get("FASTER_WHISPER_COMPUTE_TYPE", "int8"))
    parser.add_argument("--hf-endpoint", default=os.environ.get("HF_ENDPOINT", DEFAULT_HF_ENDPOINT))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--persist-env", action="store_true", help="Persist HF_ENDPOINT, PYTHONUTF8, and PYTHONIOENCODING for future shells when supported")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cache_dir().mkdir(parents=True, exist_ok=True)
    os.environ["HF_ENDPOINT"] = args.hf_endpoint
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    payload: dict[str, Any] = {
        "ok": False,
        "backend": "faster-whisper",
        "model": args.model,
        "device": args.device,
        "compute_type": args.compute_type,
        "hf_endpoint": args.hf_endpoint,
        "python_utf8_required": True,
        "python_io_encoding": "utf-8",
        "python": sys.executable,
        "platform": platform.platform(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    setup = ensure_faster_whisper(args.timeout)
    payload["dependency"] = setup
    if setup.get("ok"):
        verify = load_model(args.model, args.device, args.compute_type, args.timeout)
        payload["verify"] = verify
        payload["ok"] = bool(verify.get("ok"))
    if args.persist_env:
        payload["persist_env"] = [
            persist_user_env("HF_ENDPOINT", args.hf_endpoint),
            persist_user_env("PYTHONUTF8", "1"),
            persist_user_env("PYTHONIOENCODING", "utf-8"),
        ]
    ready_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "ready_path": str(ready_path()), "model": args.model}, ensure_ascii=True, indent=2))
    if not payload["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
