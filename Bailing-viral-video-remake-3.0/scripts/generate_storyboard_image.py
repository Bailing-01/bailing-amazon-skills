#!/usr/bin/env python3
"""Generate a visual director storyboard sheet with helper/API fallback."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import socket
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib import error, request

DEFAULT_MODEL = "gpt-image-2"
DEFAULT_BASE_URL = "https://xinghe.xin/v1"
DEFAULT_SIZE = "auto"
LANDSCAPE_STORYBOARD_SIZE = "2048x1536"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class ImageGenerationError(RuntimeError):
    def __init__(self, stage: str, message: str, *, detail: str | None = None, status: int | None = None):
        super().__init__(message)
        self.stage = stage
        self.detail = detail
        self.status = status

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "stage": self.stage,
            "error": str(self),
            "detail": self.detail,
            "http_status": self.status,
        }


def env_first(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env_key:
                for name in names:
                    try:
                        value, _ = winreg.QueryValueEx(env_key, name)
                        if value:
                            return str(value)
                    except OSError:
                        continue
        except OSError:
            pass
    return None


def api_key() -> str:
    key = env_first("IMG_API_KEY", "OPENAI_API_KEY", "API_KEY")
    if not key:
        raise ImageGenerationError("preflight", "No image API key found in IMG_API_KEY, OPENAI_API_KEY, or API_KEY")
    return key


def model_name() -> str:
    return env_first("OPENAI_IMAGE_MODEL", "IMG_MODEL", "OPENAI_MODEL", "IMAGE_MODEL") or DEFAULT_MODEL


def base_url() -> str:
    return (env_first("OPENAI_BASE_URL", "OPENAI_API_BASE", "IMG_BASE_URL", "BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def generations_url() -> str:
    return env_first("OPENAI_IMAGE_GENERATIONS_URL", "IMG_GENERATIONS_URL") or f"{base_url()}/images/generations"


def edits_url() -> str:
    return env_first("OPENAI_IMAGE_EDITS_URL", "IMG_EDITS_URL") or f"{base_url()}/images/edits"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def build_prompt_from_storyboard(storyboard_json: Path) -> str:
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    from build_storyboard_image_prompts import build_sheet_prompt

    return build_sheet_prompt(load_json(storyboard_json))


def storyboard_size_from_json(storyboard_json: Path) -> str:
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    from build_storyboard_image_prompts import storyboard_size_for_count

    storyboard = load_json(storyboard_json)
    panels = storyboard.get("panels")
    if not isinstance(panels, list) or not panels:
        return LANDSCAPE_STORYBOARD_SIZE
    return storyboard_size_for_count(len(panels))


def resolve_size(size: str, storyboard_json: Path | None) -> str:
    if size != "auto":
        return size
    if storyboard_json is not None:
        return storyboard_size_from_json(storyboard_json)
    return LANDSCAPE_STORYBOARD_SIZE


def validate_reference_images(values: list[str] | None) -> list[Path]:
    paths: list[Path] = []
    for value in values or []:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"Reference image not found: {value}")
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported image format: {path.suffix}; use JPG, JPEG, PNG, or WebP")
        if path.stat().st_size == 0:
            raise ValueError(f"Reference image is empty: {path}")
        paths.append(path)
    return paths


def helper_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        raise ImageGenerationError("helper", "LOCALAPPDATA is not set")
    return Path(local_appdata) / "ApiCodexOneClick" / "tools" / "generate-image.ps1"


def parse_helper_output(output: str, output_dir: Path) -> Path | None:
    candidates: list[Path] = []
    for line in output.splitlines():
        for match in re.findall(r"[A-Za-z]:\\[^\r\n\"<>|]+?\.(?:png|jpg|jpeg|webp)", line, flags=re.I):
            candidates.append(Path(match.strip()).resolve())
        md_match = re.search(r"!\[[^\]]*\]\(([^)]+)\)", line)
        if md_match:
            candidates.append(Path(md_match.group(1).strip()).resolve())
    for candidate in candidates:
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    newest = sorted(
        [path for path in output_dir.glob("*") if path.suffix.lower() in ALLOWED_EXTENSIONS and path.is_file()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return newest[0].resolve() if newest else None


def run_helper(prompt: str, reference_images: list[Path], output_dir: Path, file_name: str, size: str) -> dict[str, Any]:
    helper = helper_path()
    if not helper.is_file():
        raise ImageGenerationError("helper", f"Deployment helper not found: {helper}")
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(helper),
        "-Prompt",
        prompt,
        "-OutputDir",
        str(output_dir),
        "-Size",
        size,
        "-FileName",
        file_name,
    ]
    if reference_images:
        command.append("-ReferenceImage")
        command.extend(str(path) for path in reference_images)
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    combined = (completed.stdout or "") + "\n" + (completed.stderr or "")
    if completed.returncode != 0:
        raise ImageGenerationError("helper", f"Deployment helper failed with code {completed.returncode}", detail=combined[-4000:])
    saved = parse_helper_output(combined, output_dir)
    if not saved:
        raise ImageGenerationError("helper", "Deployment helper did not return a saved image path", detail=combined[-4000:])
    return {"provider": "deployment_helper", "saved": str(saved), "stdout": completed.stdout, "stderr": completed.stderr}


def request_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=300) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ImageGenerationError("api", f"Image API returned HTTP {exc.code}", detail=detail, status=exc.code) from exc
    except (error.URLError, socket.timeout, TimeoutError) as exc:
        raise ImageGenerationError("network", "Image API request failed or timed out", detail=str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ImageGenerationError("api", "Image API returned invalid JSON", detail=str(exc)) from exc


def multipart_form(fields: dict[str, str], files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = f"----xinghe-storyboard-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")
    for name, path in files:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n".encode("utf-8")
        )
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def request_multipart(url: str, fields: dict[str, str], files: list[tuple[str, Path]]) -> dict[str, Any]:
    body, content_type = multipart_form(fields, files)
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": content_type},
    )
    try:
        with request.urlopen(req, timeout=300) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ImageGenerationError("api", f"Image edit API returned HTTP {exc.code}", detail=detail, status=exc.code) from exc
    except (error.URLError, socket.timeout, TimeoutError) as exc:
        raise ImageGenerationError("network", "Image edit API request failed or timed out", detail=str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ImageGenerationError("api", "Image edit API returned invalid JSON", detail=str(exc)) from exc


def nested_values(data: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and isinstance(value, str):
                found.append(value)
            else:
                found.extend(nested_values(value, keys))
    elif isinstance(data, list):
        for item in data:
            found.extend(nested_values(item, keys))
    return found


def save_api_result(data: dict[str, Any], output_path: Path) -> dict[str, Any]:
    b64_values = nested_values(data, {"b64_json", "base64", "image_base64"})
    if b64_values:
        output_path.write_bytes(base64.b64decode(b64_values[0]))
        return {"provider": "direct_api", "saved": str(output_path), "response_type": "b64_json"}
    urls = nested_values(data, {"url", "image_url", "output_url"})
    if urls:
        req = request.Request(urls[0], method="GET")
        with request.urlopen(req, timeout=300) as response:
            output_path.write_bytes(response.read())
        return {"provider": "direct_api", "saved": str(output_path), "response_type": "url", "url": urls[0]}
    raise ImageGenerationError("api", "Image API response did not include b64_json or url", detail=json.dumps(data, ensure_ascii=False)[:4000])


def run_direct_api(prompt: str, reference_images: list[Path], output_path: Path, size: str) -> dict[str, Any]:
    if reference_images:
        fields = {"model": model_name(), "prompt": prompt, "size": size}
        files = [("image", path) for path in reference_images]
        data = request_multipart(edits_url(), fields, files)
    else:
        data = request_json(generations_url(), {"model": model_name(), "prompt": prompt, "size": size})
    return save_api_result(data, output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate one visual director storyboard sheet image with fallback")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--storyboard-json", help="Storyboard JSON produced by build_storyboard.py")
    source.add_argument("--prompt-file", help="Existing storyboard sheet prompt text file")
    parser.add_argument("--reference-image", action="append", help="Product/reference image to pass into image generation")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-name", default="storyboard_sheet.png")
    parser.add_argument("--size", default=DEFAULT_SIZE, help="Storyboard image size. Default auto chooses 2048x1536 or 1536x2048 from panel layout.")
    parser.add_argument("--skip-helper", action="store_true", help="Skip deployment helper and use direct API fallback")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.output_name
    result_path = output_dir / "storyboard-image-result.json"
    manifest_path = output_dir / "storyboard-image-manifest.json"
    prompt_path = output_dir / "storyboard_sheet_prompt.txt"
    try:
        if args.storyboard_json:
            source_path = Path(args.storyboard_json).expanduser().resolve()
            prompt = build_prompt_from_storyboard(source_path)
            source = {"mode": "storyboard_json", "storyboard_source": str(source_path)}
            size = resolve_size(args.size, source_path)
        else:
            source_path = Path(args.prompt_file).expanduser().resolve()
            prompt = source_path.read_text(encoding="utf-8-sig")
            source = {"mode": "prompt_file", "prompt_source": str(source_path)}
            size = resolve_size(args.size, None)
        prompt_path.write_text(prompt, encoding="utf-8")
        reference_images = validate_reference_images(args.reference_image)
        manifest = {
            "ok": True,
            "dry_run": args.dry_run,
            "size": size,
            "requested_size": args.size,
            "output_path": str(output_path),
            "prompt_path": str(prompt_path),
            "reference_images": [str(path) for path in reference_images],
            **source,
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        generation: dict[str, Any] | None = None
        helper_error: dict[str, Any] | None = None
        if not args.dry_run:
            if not args.skip_helper:
                try:
                    generation = run_helper(prompt, reference_images, output_dir, args.output_name, size)
                    saved = Path(generation["saved"]).resolve()
                    if saved != output_path.resolve():
                        output_path.write_bytes(saved.read_bytes())
                        generation["copied_to"] = str(output_path)
                except ImageGenerationError as exc:
                    helper_error = exc.as_dict()
            if generation is None:
                generation = run_direct_api(prompt, reference_images, output_path, size)
            if not output_path.is_file() or output_path.stat().st_size == 0:
                raise ImageGenerationError("save", f"Generated image was not saved: {output_path}")
        payload = {**manifest, "generation": generation, "helper_error": helper_error, "manifest_path": str(manifest_path)}
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({**payload, "result_path": str(result_path)}, ensure_ascii=True, indent=2))
    except (ValueError, OSError, json.JSONDecodeError, ImageGenerationError) as exc:
        payload = exc.as_dict() if isinstance(exc, ImageGenerationError) else {"ok": False, "stage": "preflight", "error": str(exc)}
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({**payload, "result_path": str(result_path)}, ensure_ascii=True, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
