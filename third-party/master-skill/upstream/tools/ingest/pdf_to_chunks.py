#!/usr/bin/env python3
"""pdf_to_chunks.py — extract text from a PDF as structured chunks.

Designed for industry reports / academic papers / course slides being fed into
the source_pool. Each chunk has page number + section heading guess + text +
word count, so the downstream Phase 2 / 3 agent can cite specific pages.

Lazy install: pymupdf (fitz) is preferred (faster + better layout). Falls back
to pdfplumber if pymupdf unavailable. Both prompt y/N before installing; pass
AUTO_YES=1 to skip.

Usage:
  python3 pdf_to_chunks.py <input.pdf> [output.jsonl]
  python3 pdf_to_chunks.py <input.pdf> -                  # JSONL to stdout
  python3 pdf_to_chunks.py <input.pdf> --by-page          # one chunk per page
  python3 pdf_to_chunks.py <input.pdf> --max-chars 1500   # split larger pages

Default chunking: one chunk per page. Pages > --max-chars get split on
paragraph boundaries.

Output JSONL (one chunk per line):
  {"source": "<input>", "page": 1, "section": null, "text": "...",
   "word_count": 320}

Exit codes: 0 ok / 1 file missing / 2 parse error / 4 user declined install
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Resolve _lazy regardless of how the script is invoked
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lazy import ensure_pkg, check_pkg  # noqa: E402


def split_paragraphs(text: str, max_chars: int) -> list[str]:
    """Split a long page on blank lines while keeping each piece <= max_chars."""
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


def detect_section(text: str) -> str | None:
    """Cheap heuristic: a section header is a line ≤ 80 chars in ALL CAPS,
    or starting with a numeric prefix `1.`, `2.1`, etc."""
    for line in text.splitlines()[:5]:
        s = line.strip()
        if 4 <= len(s) <= 80 and s == s.upper() and re.search(r"[A-Z]", s):
            return s
        if re.match(r"^[\d]+(\.[\d]+)*\s+\w", s):
            return s
    return None


def extract_pymupdf(path: Path) -> list[tuple[int, str]]:
    import fitz  # type: ignore[import-not-found]
    pages: list[tuple[int, str]] = []
    with fitz.open(str(path)) as doc:
        for i in range(doc.page_count):
            page = doc.load_page(i)
            text = page.get_text("text") or ""
            pages.append((i + 1, text))
    return pages


def extract_pdfplumber(path: Path) -> list[tuple[int, str]]:
    import pdfplumber  # type: ignore[import-not-found]
    pages: list[tuple[int, str]] = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append((i + 1, text))
    return pages


def chunkify(
    pages: list[tuple[int, str]],
    source: str,
    by_page: bool,
    max_chars: int,
) -> list[dict]:
    out: list[dict] = []
    for page_no, raw in pages:
        if not raw.strip():
            continue
        text = re.sub(r"[ \t]+", " ", raw)
        text = re.sub(r"\n{3,}", "\n\n", text)
        section = detect_section(text)
        if by_page or len(text) <= max_chars:
            out.append({
                "source": source,
                "page": page_no,
                "section": section,
                "text": text.strip(),
                "word_count": len(text.split()),
            })
            continue
        for piece in split_paragraphs(text, max_chars=max_chars):
            out.append({
                "source": source,
                "page": page_no,
                "section": section,
                "text": piece.strip(),
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
    print(f"pdf_to_chunks: wrote {len(records)} chunks → {p}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Extract a PDF as JSONL chunks.")
    p.add_argument("input", nargs="?", type=Path,
                   help="Input PDF (omit only with --check-deps)")
    p.add_argument("output", nargs="?", default=None,
                   help="Output path (- for stdout). Default: <input>.chunks.jsonl")
    p.add_argument("--by-page", action="store_true",
                   help="One chunk per page (no further splitting)")
    p.add_argument("--max-chars", type=int, default=2400,
                   help="Split pages larger than this on paragraph boundaries (default 2400)")
    p.add_argument("--prefer", choices=["pymupdf", "pdfplumber"], default="pymupdf",
                   help="Preferred extractor (default pymupdf)")
    p.add_argument("--check-deps", action="store_true",
                   help="Print which optional deps are installed, exit. Doesn't try to install.")
    p.add_argument("--strict", action="store_true",
                   help="With --check-deps, exit non-zero if any required dep is missing "
                        "(useful in CI). Without --strict, --check-deps always exits 0.")
    args = p.parse_args(argv)

    if args.check_deps:
        all_ok = True
        for name, imp in [("pymupdf", "fitz"), ("pdfplumber", "pdfplumber")]:
            ok = check_pkg(name, imp)
            tag = "✓" if ok else "✗"
            print(f"{tag} {name}: {'available' if ok else 'NOT installed'}")
            if not ok:
                all_ok = False
        # Iter 26 (codex 4-audit P2): with --strict, missing deps fails CI.
        # Either pymupdf OR pdfplumber works (we have a fallback chain), so
        # strict-mode failure means BOTH are missing.
        if args.strict and not all_ok and not check_pkg("pdfplumber"):
            return 7
        return 0

    if not args.input:
        p.error("input is required (or use --check-deps)")
    if not args.input.exists():
        print(f"pdf_to_chunks: input not found: {args.input}", file=sys.stderr)
        return 1

    # Lazy install (pymupdf preferred). pdfplumber fallback if pymupdf install
    # was declined.
    extractor_name = args.prefer
    try:
        if args.prefer == "pymupdf":
            ensure_pkg("pymupdf", import_name="fitz")
            pages = extract_pymupdf(args.input)
        else:
            ensure_pkg("pdfplumber")
            pages = extract_pdfplumber(args.input)
    except SystemExit:
        # User declined → try the other backend
        other = "pdfplumber" if args.prefer == "pymupdf" else "pymupdf"
        print(
            f"pdf_to_chunks: {args.prefer} unavailable; trying {other}",
            file=sys.stderr,
        )
        try:
            if other == "pymupdf":
                ensure_pkg("pymupdf", import_name="fitz")
                pages = extract_pymupdf(args.input)
            else:
                ensure_pkg("pdfplumber")
                pages = extract_pdfplumber(args.input)
            extractor_name = other
        except SystemExit as e:
            return int(e.code or 4)

    print(f"pdf_to_chunks: extracted {len(pages)} pages with {extractor_name}", file=sys.stderr)
    records = chunkify(pages, source=str(args.input), by_page=args.by_page, max_chars=args.max_chars)

    out = args.output
    if out is None:
        out = args.input.with_suffix(args.input.suffix + ".chunks.jsonl")
    write(records, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
