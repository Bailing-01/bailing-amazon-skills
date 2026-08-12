#!/usr/bin/env python3
"""Generate a viral-video recreation with Volcengine Ark Seedance."""

from __future__ import annotations

import argparse
import base64
import json
import math
import mimetypes
import os
import re
import socket
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

BASE_URL = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
DEFAULT_MODEL = os.environ.get("ARK_SEEDANCE_MODEL", "doubao-seedance-2-0-fast-260128")
TASKS_PATH = "/contents/generations/tasks"
TERMINAL = {"succeeded", "success", "completed", "failed", "cancelled", "canceled"}
SUCCESS = {"succeeded", "success", "completed"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PLACEHOLDER_RE = re.compile(r"\[[A-Z0-9_ -]+\]|<[^>]+>|TODO|TBD", re.I)
MIN_SEEDANCE_DURATION = 4
MAX_SEEDANCE_DURATION = 15


class ArkError(RuntimeError):
    def __init__(self, stage: str, message: str, *, status: int | None = None, detail: str | None = None):
        super().__init__(message)
        self.stage = stage
        self.status = status
        self.detail = detail

    def as_dict(self) -> dict[str, Any]:
        return {"ok": False, "stage": self.stage, "error": str(self), "http_status": self.status, "detail": self.detail}


def api_key() -> str:
    key = os.environ.get("ARK_API_KEY")
    if not key and os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env_key:
                key, _ = winreg.QueryValueEx(env_key, "ARK_API_KEY")
        except OSError:
            pass
    if not key:
        raise ArkError("preflight", "ARK_API_KEY is missing; configure it locally before paid generation")
    return key


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        BASE_URL + path,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=120) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ArkError("api", f"Ark returned HTTP {exc.code}", status=exc.code, detail=detail) from exc
    except (error.URLError, socket.timeout, TimeoutError) as exc:
        raise ArkError("network", "Could not reach Ark or the request timed out", detail=str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ArkError("api", "Ark returned invalid JSON", detail=str(exc)) from exc


def nested_string(data: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, str):
                return value
        for value in data.values():
            found = nested_string(value, keys)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = nested_string(value, keys)
            if found:
                return found
    return None


def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build_content(prompt: str, image_paths: list[Path]) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for path in image_paths:
        content.append({"type": "image_url", "image_url": {"url": data_url(path)}, "role": "reference_image"})
    return content


def safe_download(url: str, output: Path) -> int:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ArkError("download", "Refused a non-HTTPS or invalid video URL")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    try:
        with request.urlopen(request.Request(url, method="GET"), timeout=300) as response, temporary.open("wb") as handle:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > 2 * 1024 * 1024 * 1024:
                    raise ArkError("download", "Video exceeded the 2 GiB safety limit")
                handle.write(chunk)
        temporary.replace(output)
        return total
    except ArkError:
        temporary.unlink(missing_ok=True)
        raise
    except (error.HTTPError, error.URLError, socket.timeout, TimeoutError, OSError) as exc:
        temporary.unlink(missing_ok=True)
        raise ArkError("download", "Video download failed", detail=str(exc)) from exc


def generate_video(
    *,
    prompt: str,
    image_paths: list[Path],
    output: Path,
    model: str,
    ratio: str,
    resolution: str,
    duration: int,
    generate_audio: bool,
    interval: int,
    timeout: int,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "content": build_content(prompt, image_paths),
        "ratio": ratio,
        "resolution": resolution,
        "duration": duration,
        "generate_audio": generate_audio,
    }
    submitted = request_json("POST", TASKS_PATH, payload)
    task_id = nested_string(submitted, ("id", "task_id", "taskId"))
    if not task_id:
        raise ArkError("submit", "Ark response did not contain a task id", detail=json.dumps(submitted, ensure_ascii=False))
    deadline = time.time() + timeout
    final: dict[str, Any] | None = None
    status = "submitted"
    while time.time() < deadline:
        final = request_json("GET", f"{TASKS_PATH}/{task_id}")
        status = (nested_string(final, ("status", "state")) or "unknown").lower()
        print(json.dumps({"task_id": task_id, "status": status}, ensure_ascii=False), file=sys.stderr)
        if status in TERMINAL:
            break
        time.sleep(interval)
    else:
        raise ArkError("poll", f"Task {task_id} timed out after {timeout} seconds", detail=f"last_status={status}")
    if status not in SUCCESS:
        raise ArkError("generation", f"Task {task_id} ended with status {status}", detail=json.dumps(final, ensure_ascii=False))
    video_url = nested_string(final, ("video_url", "output_url", "url"))
    if not video_url:
        raise ArkError("result", f"Task {task_id} succeeded but no video URL was found", detail=json.dumps(final, ensure_ascii=False))
    size = safe_download(video_url, output)
    return {
        "ok": True,
        "task_id": task_id,
        "status": status,
        "model": model,
        "ratio": ratio,
        "resolution": resolution,
        "duration": duration,
        "generate_audio": generate_audio,
        "saved": str(output),
        "bytes": size,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Brief JSON must contain an object")
    return data


def validate_images(values: list[str]) -> list[Path]:
    if not values:
        raise ValueError("At least one --image-path is required for product-faithful generation")
    paths: list[Path] = []
    for value in values:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"Image not found: {value}")
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported image format: {path.suffix}; use JPG, JPEG, PNG, or WebP")
        if path.stat().st_size == 0:
            raise ValueError(f"Image is empty: {path}")
        paths.append(path)
    return paths


def validate_optional_images(values: list[str] | None) -> list[Path]:
    if not values:
        return []
    return validate_images(values)


def looks_like_storyboard(path: Path) -> bool:
    text = " ".join(part.lower() for part in path.parts)
    return "storyboard" in text or "分镜" in text


def validate_storyboard_presence(product_images: list[Path], storyboard_images: list[Path], allow_missing: bool) -> None:
    if allow_missing:
        return
    if storyboard_images:
        return
    if any(looks_like_storyboard(path) for path in product_images):
        return
    raise ValueError(
        "A visual storyboard sheet image is required before Seedance generation. "
        "Generate storyboard_sheet.png first and pass it with --storyboard-image, or include an image path whose name contains storyboard. "
        "Use --allow-missing-storyboard only for explicit diagnostic runs after recording the reason."
    )


def split_inferred_storyboard_images(image_paths: list[Path]) -> tuple[list[Path], list[Path]]:
    storyboard = [path for path in image_paths if looks_like_storyboard(path)]
    product = [path for path in image_paths if not looks_like_storyboard(path)]
    return product, storyboard


def as_timeline(items: Any, field: str) -> tuple[str, float]:
    if not isinstance(items, list) or not items:
        raise ValueError(f"{field} must be a non-empty list")
    lines: list[str] = []
    total = 0.0
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"{field}[{index}] must be an object")
        start = float(item.get("start", 0))
        end = float(item.get("end", 0))
        if end <= start:
            raise ValueError(f"{field}[{index}] has invalid timing")
        total += end - start
        body = "; ".join(f"{key}: {value}" for key, value in item.items() if key not in {"start", "end"} and value)
        lines.append(f"{index}. {start:.1f}-{end:.1f}s: {body}")
    return "\n".join(lines), total


def optional_timeline(items: Any, field: str) -> tuple[str, float, bool]:
    if not isinstance(items, list) or not items:
        return "None.", 0.0, False
    lines, total = as_timeline(items, field)
    return lines, total, True


def text_values(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    values: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = str(item.get("text", "")).strip()
            if text:
                values.append(text)
    return values


def normalized_text(value: str) -> str:
    return re.sub(r"[\s，。！？、,.!?;；:：\"'“”‘’（）()\[\]【】\-—_]+", "", value).lower()


def overlap_score(left: str, right: str) -> float:
    left_norm = normalized_text(left)
    right_norm = normalized_text(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm in right_norm or right_norm in left_norm:
        return 1.0
    left_chars = set(left_norm)
    right_chars = set(right_norm)
    if not left_chars or not right_chars:
        return 0.0
    return len(left_chars & right_chars) / max(len(left_chars), len(right_chars))


def infer_text_is_transcript_like(voiceover_items: Any, on_screen_items: Any) -> bool:
    voice_lines = text_values(voiceover_items)
    screen_lines = text_values(on_screen_items)
    if not voice_lines or not screen_lines:
        return False
    matches = 0
    for screen in screen_lines:
        if any(overlap_score(screen, voice) >= 0.72 for voice in voice_lines):
            matches += 1
    return matches >= max(1, min(len(screen_lines), len(voice_lines)) // 2)


def caption_layer_policy(
    brief: dict[str, Any],
    *,
    preserve_voiceover: bool,
    has_voiceover: bool,
    has_on_screen_text: bool,
) -> tuple[str, str, bool]:
    raw_policy = brief.get("caption_layer_policy") if isinstance(brief.get("caption_layer_policy"), dict) else {}
    mode = str(raw_policy.get("mode") or "").strip()
    allow_voiceover_subtitles = bool(raw_policy.get("allow_voiceover_subtitles"))
    relationship = ""
    voiceover_policy = brief.get("voiceover_policy") if isinstance(brief.get("voiceover_policy"), dict) else {}
    for value in (raw_policy.get("relationship_to_voiceover"), voiceover_policy.get("relationship_to_on_screen_text")):
        if value:
            relationship = str(value).strip()
            break
    transcript_like = infer_text_is_transcript_like(brief.get("adapted_voiceover"), brief.get("adapted_on_screen_text"))
    if not mode:
        if preserve_voiceover or has_voiceover:
            if has_on_screen_text:
                if allow_voiceover_subtitles or "caption_driven" in relationship or "subtitle_driven" in relationship:
                    mode = "caption_driven"
                else:
                    mode = "sparse_stickers"
            else:
                mode = "voiceover_only"
        elif has_on_screen_text:
            mode = "caption_driven"
        else:
            mode = "no_readable_text"
    if mode not in {"voiceover_only", "sparse_stickers", "caption_driven", "no_readable_text"}:
        mode = "sparse_stickers" if (preserve_voiceover or has_voiceover) else "caption_driven"
    if (preserve_voiceover or has_voiceover) and transcript_like and not allow_voiceover_subtitles and mode != "caption_driven":
        mode = "sparse_stickers"
    if mode == "voiceover_only":
        instruction = (
            "Readable text layer policy: voiceover_only. Use the spoken voiceover as the copy layer. "
            "Do not render readable subtitles, transcript captions, karaoke captions, lower-third subtitles, or duplicated text. "
            "Only non-readable graphic motion or product-safe decorative marks are allowed."
        )
    elif mode == "sparse_stickers":
        instruction = (
            "Readable text layer policy: sparse_stickers. Use exactly one readable text layer. "
            "Keep only sparse reference-style stickers, punch headlines, feature badges, or CTA lockups when needed. "
            "Do not render line-by-line subtitles matching the voiceover. Do not duplicate the voiceover as captions. "
            "Avoid lower-third transcript subtitles and gray subtitle boxes."
        )
    elif mode == "caption_driven":
        instruction = (
            "Readable text layer policy: caption_driven. The visible text is the single intended readable text layer. "
            "Do not create a second subtitle layer, duplicate captions, or an additional transcript overlay. "
            "If voiceover is present, visible captions must share the same typography system and must not appear twice."
        )
    else:
        instruction = (
            "Readable text layer policy: no_readable_text. Do not render readable captions, subtitles, stickers, badges, or random text."
        )
    if transcript_like and (preserve_voiceover or has_voiceover) and not allow_voiceover_subtitles:
        instruction += " The provided on-screen text appears transcript-like; treat it as timing/style evidence only unless it is clearly a sparse sticker or CTA."
    return mode, instruction, transcript_like


def validate_timeline_bounds(items: Any, field: str, duration: float) -> None:
    if not isinstance(items, list):
        return
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        start = float(item.get("start", 0))
        end = float(item.get("end", 0))
        if start < 0 or end > duration + 0.01:
            raise ValueError(f"{field}[{index}] timing must stay within 0-{duration:g}s; got {start:g}-{end:g}s")


def compact_value(value: Any) -> str:
    if isinstance(value, dict):
        parts = [f"{key}: {compact_value(item)}" for key, item in value.items() if item not in (None, "", [], {})]
        return "; ".join(parts)
    if isinstance(value, list):
        return ", ".join(compact_value(item) for item in value if item not in (None, "", [], {}))
    return str(value).strip()


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def normalize_duration(value: Any) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"duration must be a number; got {value!r}") from exc
    return round_half_up(numeric)


def validate_duration(duration: int) -> None:
    if duration < MIN_SEEDANCE_DURATION or duration > MAX_SEEDANCE_DURATION:
        raise ValueError(
            f"Seedance duration must be between {MIN_SEEDANCE_DURATION:g} and {MAX_SEEDANCE_DURATION:g} seconds; "
            f"got {duration:g}. If the reference is shorter than {MIN_SEEDANCE_DURATION:g}s, pad the adapted brief to "
            f"{MIN_SEEDANCE_DURATION:g}s with a product hero hold or ask the user before changing duration."
        )


def build_prompt_from_brief(brief: dict[str, Any], ratio: str, duration: int) -> str:
    product = str(brief.get("product_name") or "the user's product").strip()
    objective = str(brief.get("objective") or "recreate the reference video's viral structure for the user's product").strip()
    voiceover_policy = brief.get("voiceover_policy") if isinstance(brief.get("voiceover_policy"), dict) else {}
    preserve_voiceover = bool(voiceover_policy.get("preserve_voiceover"))
    voiceover, voiceover_total, has_voiceover = optional_timeline(brief.get("adapted_voiceover"), "adapted_voiceover")
    if preserve_voiceover and not has_voiceover:
        raise ValueError("adapted_voiceover must be provided when voiceover_policy.preserve_voiceover is true")
    validate_timeline_bounds(brief.get("adapted_voiceover"), "adapted_voiceover", duration)
    shots, shot_total = as_timeline(brief.get("shot_plan"), "shot_plan")
    if abs(round(shot_total, 3) - round(float(duration), 3)) > 0.01:
        raise ValueError(f"shot_plan duration must total {duration} seconds; got {shot_total:g}")
    validate_timeline_bounds(brief.get("shot_plan"), "shot_plan", duration)
    on_screen_text = brief.get("adapted_on_screen_text") or []
    on_screen_lines = "None."
    if on_screen_text:
        on_screen_lines, _ = as_timeline(on_screen_text, "adapted_on_screen_text")
        validate_timeline_bounds(on_screen_text, "adapted_on_screen_text", duration)
    caption_mode, caption_policy_instruction, transcript_like_text = caption_layer_policy(
        brief,
        preserve_voiceover=preserve_voiceover,
        has_voiceover=has_voiceover,
        has_on_screen_text=bool(on_screen_text),
    )
    negative = brief.get("negative_constraints") or []
    if isinstance(negative, list):
        negative_text = "; ".join(str(item) for item in negative if item)
    else:
        negative_text = str(negative)
    logic = brief.get("reference_logic_to_preserve") or []
    logic_text = "; ".join(str(item) for item in logic) if isinstance(logic, list) else str(logic)
    preserve = brief.get("reference_elements_to_preserve") or []
    preserve_text = "; ".join(str(item) for item in preserve) if isinstance(preserve, list) else str(preserve)
    replacements = brief.get("required_replacements") or []
    replacements_text = "; ".join(str(item) for item in replacements) if isinstance(replacements, list) else str(replacements)
    constraints = str(brief.get("product_identity_constraints") or "Preserve the product exactly from the first reference image.").strip()
    facts = str(brief.get("user_supplied_facts") or "Use only directly visible product facts and user-supplied facts.").strip()
    language = str(brief.get("voiceover_language") or "zh-CN").strip()
    voiceover_style = brief.get("voiceover_style_blueprint") if isinstance(brief.get("voiceover_style_blueprint"), dict) else {}
    voiceover_style_text = compact_value(voiceover_style)
    storyboard_usage = str(brief.get("storyboard_sheet_usage") or "").strip()
    fidelity_mode = str(brief.get("reference_fidelity_mode") or "reference-faithful").strip()
    sticker_layer = brief.get("sticker_overlay_intent") or brief.get("sticker_overlay_style") or ""
    if isinstance(sticker_layer, list):
        sticker_layer_text = "; ".join(str(item) for item in sticker_layer if item)
    elif isinstance(sticker_layer, dict):
        sticker_layer_text = "; ".join(f"{key}: {value}" for key, value in sticker_layer.items() if value)
    else:
        sticker_layer_text = str(sticker_layer).strip()
    sound_layer = brief.get("sound_effect_intent") or brief.get("sound_design") or ""
    if isinstance(sound_layer, list):
        sound_layer_text = "; ".join(str(item) for item in sound_layer if item)
    elif isinstance(sound_layer, dict):
        sound_layer_text = "; ".join(f"{key}: {value}" for key, value in sound_layer.items() if value)
    else:
        sound_layer_text = str(sound_layer).strip()
    voiceover_generation_instruction = str(voiceover_policy.get("generation_instruction") or "").strip()
    speaker_style = str(voiceover_policy.get("speaker_style") or "").strip()
    if preserve_voiceover:
        voiceover_rule = (
            "Audio must include a clear spoken voiceover. Do not omit the voiceover. "
            "Keep voiceover louder than music and sound effects. "
            f"Speaker style: {speaker_style or 'match the reference speaker energy'}. "
            f"Voiceover style blueprint: {voiceover_style_text or 'match the reference voiceover emotion, pace, pause pattern, and energy curve'}. "
            f"{voiceover_generation_instruction}"
        ).strip()
    else:
        source_detected = voiceover_policy.get("source_detected")
        if source_detected is False:
            voiceover_rule = "Reference voiceover was not detected; do not force spoken narration unless the adapted_voiceover timeline is intentionally provided."
        else:
            voiceover_rule = "If voiceover extraction was unavailable, do not treat visual captions as confirmed speech; use the provided adapted voiceover only if the brief explicitly requires it."
    if preserve_voiceover or has_voiceover:
        audio_direction = (
            "generate native spoken voiceover, energetic but credible commercial pacing, clean short-video music bed, "
            "stronger reference-style sound effects, transition whooshes, sticker-pop accents, cloth rubbing sounds, "
            "tap sounds, gentle stretch sounds, proof-point hits, and CTA accent. Keep audio synchronized to the shot timing."
        )
    else:
        audio_direction = (
            "do not generate spoken narration. Use a clean short-video music bed plus stronger reference-style sound effects, "
            "transition whooshes, sticker-pop accents, product-handling sounds, proof-point hits, and CTA accent. "
            "Keep audio synchronized to the shot timing."
        )

    return f"""Create one {duration}-second {ratio} viral ecommerce short video for {product}.

Objective: {objective}
Reference-fidelity mode: {fidelity_mode}. Preserve all transferable elements from the reference video and do not simplify it into a generic product video. Keep the reference video's model/host presence when present, actions, shot order, framing, camera movement, scene design, props, caption style, voiceover rhythm, and CTA logic unless an element is listed under required replacements or negative constraints.
Reference-video logic to preserve: {logic_text or 'hook, rhythm, demonstration payoff, and CTA structure'}
Reference elements to preserve: {preserve_text or 'model/host role if present; shot count and shot order; actions; camera movement; scene style; caption style; copy rhythm; CTA logic'}
Required replacements only: {replacements_text or 'replace the reference product with the user product; rewrite exact captions and script; remove watermark, platform UI, original brand assets, and unsupported claims'}
Product identity constraints: {constraints}
Storyboard sheet usage: {storyboard_usage or 'If a storyboard sheet is provided as a later reference image, use it as the director reference for narrative logic, shot order, model/action role, layout, camera movement, timing, sticker/overlay style, caption style, sound-cue intent, and per-shot scene style. Product photos remain the identity references and override the storyboard sheet for product appearance. If the storyboard contains a red 5x6 face grid, treat it only as a storyboard marker; do not render the grid, a blank face, a mask, or a blurred face in the final video.'}
Allowed product facts and claims: {facts}

Timeline and visual plan:
{shots}

Voiceover language: {language}
Voiceover policy: {voiceover_rule}
Voiceover style transfer: {voiceover_style_text or 'match the reference voiceover emotion, pace, slogan rhythm, pause pattern, and energy curve; keep the voice forward in the mix.'}
Spoken voiceover script:
{voiceover}

On-screen text intent:
{on_screen_lines}

{caption_policy_instruction}

One-pass caption typography lock: render any allowed readable Chinese sticker, headline, CTA, or caption text directly in this generated video using one consistent reference-matched typography system. Use bold white ecommerce headline text, heavy sans-serif shape, thick dark outline, soft drop shadow, high contrast, and the same scale and placement logic across every shot. If the reference captions are slightly italic or slanted, keep the same slant consistently. Do not switch middle shots into small thin subtitle font, gray subtitle boxes, random lower-third subtitles, duplicated subtitles, or mixed fonts. Use at most two text styles: primary punch headline and final brand lockup. Keep each allowed readable text moment short, readable, and close to its storyboard placement. Current caption mode: {caption_mode}. Transcript-like on-screen text risk detected: {str(transcript_like_text).lower()}.

Sticker and overlay direction: {sticker_layer_text or 'Preserve the reference-style sticker system as a separate visual layer: corner marker feel, checkmarks, feature badges, product-detail callouts, arrows or phone-frame overlays when present, bold ecommerce caption stickers, and visible pop-in timing. Rewrite all wording and remove original brand marks.'}

Audio direction: {audio_direction} {sound_layer_text}

Camera and edit rules: match the reference video's camera intent, shot order, motion direction, edit rhythm, and model/action blocking. Use simple cuts when needed for reliability, keep clear product visibility in the first 2 seconds, one main action per shot, and smooth camera movement. Preserve product shape, color, packaging, logo position, label layout, printed text placement, material, accessories, and visible components from the first image.

Negative constraints: {negative_text}; no red face grid in the final video; no blank face; no faceless host; no mask; no blurred face; no copied captions from the reference video; no watermark; no platform UI; no fake price; no unsupported medical, safety, efficacy, nutritional, durability, ranking, certification, warranty, or discount claims; no deformed hands; no product morphing; no extra logos; no random text."""


def effective_ratio(value: Any) -> str:
    ratio = str(value or "").strip()
    allowed = {"9:16", "1:1", "16:9", "3:4", "4:3", "21:9", "adaptive"}
    if ratio in allowed:
        return ratio
    return "9:16"


def read_prompt(args: argparse.Namespace) -> tuple[str, dict[str, Any], int, str]:
    if args.prompt_file:
        prompt_path = Path(args.prompt_file).expanduser().resolve()
        prompt = prompt_path.read_text(encoding="utf-8-sig")
        source = {"mode": "prompt_file", "prompt_source": str(prompt_path)}
        raw_duration = args.duration if args.duration is not None else 15
        duration = normalize_duration(raw_duration)
        source["raw_duration"] = raw_duration
        ratio = effective_ratio(args.ratio or "9:16")
    else:
        brief_path = Path(args.brief_json).expanduser().resolve()
        brief = load_json(brief_path)
        brief_duration = brief.get("duration")
        raw_duration = args.duration if args.duration is not None else brief_duration if brief_duration is not None else 15
        duration = normalize_duration(raw_duration)
        validate_duration(duration)
        ratio = effective_ratio(args.ratio or brief.get("target_ratio") or brief.get("ratio") or "9:16")
        prompt = build_prompt_from_brief(brief, ratio, duration)
        source = {
            "mode": "brief_json",
            "brief_source": str(brief_path),
            "brief_duration": brief.get("duration"),
            "brief_ratio": brief.get("ratio"),
            "brief_target_ratio": brief.get("target_ratio"),
            "raw_duration": raw_duration,
        }
    validate_duration(duration)
    placeholders = PLACEHOLDER_RE.findall(prompt)
    if placeholders:
        raise ValueError(f"Prompt contains unresolved placeholders: {placeholders[:8]}")
    return prompt, source, duration, ratio


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a reference-duration viral recreation video with Ark Seedance")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--brief-json", help="Adapted recreation brief JSON")
    source.add_argument("--prompt-file", help="Complete Seedance prompt text file")
    parser.add_argument("--image-path", action="append", required=True)
    parser.add_argument("--storyboard-image", action="append", help="Required visual director storyboard sheet image to submit with product images")
    parser.add_argument("--allow-missing-storyboard", action="store_true", help="Diagnostic override only. Paid reference remake generation should not use this.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-name", default="xinghe-viral-video-recreate.mp4")
    parser.add_argument("--ratio", choices=["9:16", "1:1", "16:9", "3:4", "4:3", "21:9", "adaptive"], default=None, help="Override output ratio. For brief JSON, default follows brief.ratio from the reference video; prompt files default to 9:16.")
    parser.add_argument("--resolution", choices=["480p", "720p", "1080p", "2K"], default="480p")
    parser.add_argument("--duration", type=float, default=None, help="Target duration in seconds. Values are rounded half up to an integer before submitting to Seedance. For brief JSON, default reads brief.duration; otherwise defaults to 15. Seedance requires 4-15 seconds.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--no-generate-audio", dest="generate_audio", action="store_false")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(generate_audio=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "xinghe-viral-video-result.json"
    prompt_path = output_dir / "xinghe-viral-video-seedance-prompt.txt"
    manifest_path = output_dir / "xinghe-viral-video-manifest.json"
    try:
        raw_image_paths = validate_images(args.image_path)
        product_image_paths, inferred_storyboard_paths = split_inferred_storyboard_images(raw_image_paths)
        storyboard_image_paths = inferred_storyboard_paths + validate_optional_images(args.storyboard_image)
        if not product_image_paths:
            raise ValueError("At least one non-storyboard product image must be provided with --image-path")
        validate_storyboard_presence(product_image_paths, storyboard_image_paths, args.allow_missing_storyboard)
        image_paths = product_image_paths + storyboard_image_paths
        prompt, source, duration, ratio = read_prompt(args)
        prompt_path.write_text(prompt, encoding="utf-8")
        manifest = {
            "ok": True,
            "dry_run": args.dry_run,
            "model": args.model,
            "ratio": ratio,
            "resolution": args.resolution,
            "duration": duration,
            "duration_rounding_policy": "round half up to an integer before submitting to Seedance",
            "generate_audio": args.generate_audio,
            "product_images": [str(path) for path in product_image_paths],
            "storyboard_images": [str(path) for path in storyboard_image_paths],
            "images": [str(path) for path in image_paths],
            "storyboard_required": not args.allow_missing_storyboard,
            "prompt_path": str(prompt_path),
            **source,
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        generation = None
        if not args.dry_run:
            generation = generate_video(
                prompt=prompt,
                image_paths=image_paths,
                output=output_dir / args.output_name,
                model=args.model,
                ratio=ratio,
                resolution=args.resolution,
                duration=duration,
                generate_audio=args.generate_audio,
                interval=args.interval,
                timeout=args.timeout,
            )
        payload = {**manifest, "generation": generation, "manifest_path": str(manifest_path)}
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({**payload, "result_path": str(result_path)}, ensure_ascii=True, indent=2))
    except (ValueError, ArkError, OSError) as exc:
        payload = exc.as_dict() if isinstance(exc, ArkError) else {"ok": False, "stage": "preflight", "error": str(exc)}
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({**payload, "result_path": str(result_path)}, ensure_ascii=True, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
