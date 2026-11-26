#!/usr/bin/env python3
"""srt_to_transcript.py — strip timestamps, line numbers, HTML tags from .srt/.vtt files.

Two output modes:

  Default (text)   — paragraph-grouped plain text, one paragraph per blank
                     line. Drop-in for the existing master-skill pipeline:
                       python3 srt_to_transcript.py in.srt [out.txt]
                     Output goes to `<input_stem>_transcript.txt` if not set.

  --jsonl          — structured per-cue records preserving timestamps + speaker
                     when present. Each line:
                       {"start": "00:01:23,400", "end": "00:01:25,200",
                        "speaker": "S1" | null, "text": "...", "word_count": 7}
                     Output goes to `<input_stem>.jsonl` if not set, or honors
                     the second positional output path.

Speaker labels (`SPEAKER_00:`, `S1:`, `[S2]`) embedded in cue text by upstream
diarization (Q4a) are extracted into the `speaker` field; raw `text` keeps the
spoken content only.

Features (all modes):
  - Skip cue numbers (pure-digit lines)
  - Skip VTT NOTE blocks
  - Strip HTML/VTT tags (`<i>`, `<c>`, `align:left`, etc.)
  - Dedupe consecutive duplicate cues (auto-subs emit dupes constantly)
  - Stats to stderr (words, cues, dupe-strip ratio)

Pure stdlib. macOS python3 out-of-the-box.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CUE_NUMBER = re.compile(r"^\d+$")
TIMECODE_LINE = re.compile(
    r"^(\d{2}:\d{2}:\d{2}[\.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[\.,]\d{3})"
)
TIMECODE_PREFIX = re.compile(r"^\d{2}:\d{2}:\d{2}")
HTML_TAG = re.compile(r"<[^>]+>")
VTT_DIRECTIVE = re.compile(r"\b(?:align|position|line|size|vertical):[^\s]+", re.IGNORECASE)
WEBVTT_HEADER = re.compile(r"^WEBVTT\b", re.IGNORECASE)
NOTE_LINE = re.compile(r"^NOTE\b", re.IGNORECASE)
SENTENCE_END = re.compile(r"[。！？.!?]$")
# Speaker labels at the start of a cue: "SPEAKER_00: text" / "S1: text" /
# "[S2] text" / "（主持人）text". Captured group 1 = label, group 2 = body.
SPEAKER_PREFIX = re.compile(
    r"^\s*(?:\[\s*([^\]]{1,30})\s*\]|\(\s*([^\)]{1,30})\s*\)|"
    r"(SPEAKER_\d+|S\d+|主持人|嘉宾[A-Z\d]?))[:：]?\s+(.*)$"
)


# ---------------------------------------------------------------------------
# Cue extraction (used by both modes)


def parse_cues(content: str) -> list[dict]:
    """Walk an SRT/VTT and return [{start, end, lines: [str]}]. Cleans VTT
    NOTE blocks, strips HTML/VTT directives, drops cue numbers."""
    cues: list[dict] = []
    cur: dict | None = None
    in_note_block = False
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            in_note_block = False
            if cur and cur.get("lines"):
                cues.append(cur)
                cur = None
            else:
                cur = None
            continue
        if NOTE_LINE.match(stripped):
            in_note_block = True
            continue
        if in_note_block:
            continue
        if WEBVTT_HEADER.match(stripped):
            continue
        if CUE_NUMBER.match(stripped):
            # next line should be a timecode; flush any pending
            if cur and cur.get("lines"):
                cues.append(cur)
            cur = {"start": "", "end": "", "lines": []}
            continue
        m = TIMECODE_LINE.match(stripped)
        if m:
            if cur is None:
                cur = {"start": "", "end": "", "lines": []}
            cur["start"] = m.group(1)
            cur["end"] = m.group(2)
            continue
        if TIMECODE_PREFIX.match(stripped):
            # Lone timecode without arrow — skip
            continue
        # Body line
        cleaned = HTML_TAG.sub("", stripped)
        cleaned = VTT_DIRECTIVE.sub("", cleaned).strip()
        if not cleaned:
            continue
        if cur is None:
            cur = {"start": "", "end": "", "lines": []}
        cur["lines"].append(cleaned)
    if cur and cur.get("lines"):
        cues.append(cur)
    return cues


def split_speaker(text: str) -> tuple[str | None, str]:
    """If `text` starts with a speaker tag, peel it off. Returns (speaker, body)."""
    m = SPEAKER_PREFIX.match(text)
    if not m:
        return None, text
    label = m.group(1) or m.group(2) or m.group(3)
    body = m.group(4)
    return label.strip() if label else None, body.strip()


def dedupe_consecutive_cues(cues: list[dict]) -> tuple[list[dict], int]:
    """Drop consecutive cues whose joined text matches the previous cue."""
    out: list[dict] = []
    dupes = 0
    last_text = None
    for c in cues:
        joined = " ".join(c["lines"]).strip()
        if joined == last_text:
            dupes += 1
            continue
        out.append(c)
        last_text = joined
    return out, dupes


# ---------------------------------------------------------------------------
# Text-mode (paragraph-grouped) output


def group_paragraphs(cues: list[dict], max_len: int = 200) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for c in cues:
        for line in c["lines"]:
            current.append(line)
            joined = " ".join(current)
            if len(joined) >= max_len or SENTENCE_END.search(line):
                paragraphs.append(joined)
                current = []
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def write_text(input_path: Path, output_path: Path, cues: list[dict]) -> dict:
    paragraphs = group_paragraphs(cues)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(paragraphs) + "\n", encoding="utf-8")
    return {
        "mode": "text",
        "paragraphs": len(paragraphs),
        "words_approx": sum(len(p.split()) for p in paragraphs),
    }


# ---------------------------------------------------------------------------
# JSONL mode output


def write_jsonl(input_path: Path, output_path: Path, cues: list[dict]) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    total_words = 0
    speakers_seen: set[str] = set()
    with output_path.open("w", encoding="utf-8") as f:
        for c in cues:
            joined = " ".join(c["lines"]).strip()
            speaker, body = split_speaker(joined)
            if not body:
                continue
            n += 1
            if speaker:
                speakers_seen.add(speaker)
            wc = len(body.split())
            total_words += wc
            f.write(json.dumps({
                "start": c.get("start") or None,
                "end": c.get("end") or None,
                "speaker": speaker,
                "text": body,
                "word_count": wc,
            }, ensure_ascii=False) + "\n")
    return {
        "mode": "jsonl",
        "cues_written": n,
        "speakers": sorted(speakers_seen),
        "words_approx": total_words,
    }


# ---------------------------------------------------------------------------
# Main


def transcribe(
    input_path: Path,
    output_path: Path | None,
    jsonl: bool,
) -> Path:
    if not input_path.exists():
        print(f"ERROR: input not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    if output_path is None:
        if jsonl:
            output_path = input_path.with_name(f"{input_path.stem}.jsonl")
        else:
            output_path = input_path.with_name(f"{input_path.stem}_transcript.txt")

    content = input_path.read_text(encoding="utf-8", errors="replace")
    cues = parse_cues(content)
    cues, dupes = dedupe_consecutive_cues(cues)

    if jsonl:
        result = write_jsonl(input_path, output_path, cues)
    else:
        result = write_text(input_path, output_path, cues)

    stats = {
        "input": str(input_path),
        "output": str(output_path),
        "raw_cues": len(cues) + dupes,
        "after_dedupe": len(cues),
        "dupes_stripped": dupes,
        **result,
    }
    for k, v in stats.items():
        print(f"{k}: {v}", file=sys.stderr)
    return output_path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Convert .srt/.vtt to text or JSONL transcript.",
    )
    p.add_argument("input", type=Path, help="Input .srt or .vtt file")
    p.add_argument("output", nargs="?", type=Path, default=None,
                   help="Output path (default: <input>_transcript.txt or <input>.jsonl with --jsonl)")
    p.add_argument("--jsonl", action="store_true",
                   help="Emit structured JSONL with per-cue start/end/speaker/text instead of paragraphs")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    transcribe(args.input, args.output, jsonl=args.jsonl)
    return 0


if __name__ == "__main__":
    sys.exit(main())
