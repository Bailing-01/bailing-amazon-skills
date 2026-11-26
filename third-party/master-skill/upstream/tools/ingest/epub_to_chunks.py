#!/usr/bin/env python3
"""epub_to_chunks.py — extract text from an EPUB ebook as structured chunks.

Each EPUB chapter (HTML doc) becomes one chunk with its title (from `<h1>` or
TOC) + plain text. Chapters longer than --max-chars are split on `<h2>` /
paragraph boundaries.

Lazy install: ebooklib + html2text (or beautifulsoup4 fallback).

Usage:
  python3 epub_to_chunks.py <input.epub> [output.jsonl|-]
  python3 epub_to_chunks.py book.epub --max-chars 3000

Output JSONL (one chunk per line):
  {"source": "...", "chapter_index": 1, "chapter_title": "...",
   "text": "...", "word_count": ...}

Exit codes: 0 ok / 1 file missing / 2 parse / 4 user declined install
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lazy import ensure_pkg  # noqa: E402


def extract_chapters(path: Path) -> list[tuple[int, str, str]]:
    """Return [(idx, title, plain_text)] per chapter."""
    ensure_pkg("ebooklib")
    ensure_pkg("html2text")
    from ebooklib import epub  # type: ignore[import-not-found]
    from ebooklib import ITEM_DOCUMENT  # type: ignore[import-not-found]
    import html2text  # type: ignore[import-not-found]

    h2t = html2text.HTML2Text()
    h2t.ignore_links = False
    h2t.ignore_images = True
    h2t.body_width = 0  # don't wrap

    book = epub.read_epub(str(path))
    out: list[tuple[int, str, str]] = []
    for i, item in enumerate(book.get_items_of_type(ITEM_DOCUMENT)):
        html = item.get_content().decode("utf-8", errors="replace")
        # Title: first <h1> / <h2> / <title>
        m = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.IGNORECASE | re.DOTALL)
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else item.get_name() or f"chapter-{i}"
        text = h2t.handle(html).strip()
        # Strip multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        if text:
            out.append((i, title[:120], text))
    return out


def split_paragraphs(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    paragraphs = re.split(r"\n\s*\n", text.strip())
    chunks: list[str] = []
    cur = ""
    for p in paragraphs:
        candidate = (cur + "\n\n" + p) if cur else p
        if len(candidate) > max_chars and cur:
            chunks.append(cur.strip())
            cur = p
        else:
            cur = candidate
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def chunkify(chapters: list[tuple[int, str, str]], source: str, max_chars: int) -> list[dict]:
    out: list[dict] = []
    for idx, title, text in chapters:
        for piece in split_paragraphs(text, max_chars=max_chars):
            out.append({
                "source": source,
                "chapter_index": idx,
                "chapter_title": title,
                "text": piece,
                "word_count": len(piece.split()),
            })
    return out


def write(records: list[dict], dest: Path | str) -> None:
    if dest == "-":
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
        return
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"epub_to_chunks: wrote {len(records)} chunks → {p}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Extract an EPUB as JSONL chunks.")
    p.add_argument("input", type=Path)
    p.add_argument("output", nargs="?", default=None)
    p.add_argument("--max-chars", type=int, default=3000)
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"epub_to_chunks: input not found: {args.input}", file=sys.stderr)
        return 1

    chapters = extract_chapters(args.input)
    print(f"epub_to_chunks: {len(chapters)} chapters", file=sys.stderr)
    records = chunkify(chapters, source=str(args.input), max_chars=args.max_chars)

    out = args.output
    if out is None:
        out = args.input.with_suffix(args.input.suffix + ".chunks.jsonl")
    write(records, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
