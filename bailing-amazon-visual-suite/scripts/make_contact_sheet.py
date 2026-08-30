#!/usr/bin/env python3
"""Create a deterministic review contact sheet from finished images."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def collect_images(input_dir: Path, output: Path, exclude_dirs: set[str]) -> list[Path]:
    output = output.resolve()
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.suffix.lower() in IMAGE_EXTS
        and path.resolve() != output
        and not any(part.lower() in exclude_dirs for part in path.parts)
    )


def load_thumb(path: Path, thumb_size: tuple[int, int]) -> Image.Image:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail(thumb_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", thumb_size, "white")
    x = (thumb_size[0] - image.width) // 2
    y = (thumb_size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser(description="Make an image contact sheet.")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--thumb-width", type=int, default=360)
    parser.add_argument("--thumb-height", type=int, default=270)
    parser.add_argument(
        "--exclude-dirs",
        default="raw,source,sources,input,inputs",
        help="Comma-separated directory names to exclude from the sheet.",
    )
    args = parser.parse_args()

    exclude_dirs = {item.strip().lower() for item in args.exclude_dirs.split(",") if item.strip()}
    images = collect_images(args.input_dir, args.output, exclude_dirs)
    if not images:
        raise SystemExit(f"No images found in {args.input_dir}")

    label_h = 34
    gap = 18
    margin = 24
    columns = max(1, args.columns)
    rows = math.ceil(len(images) / columns)
    cell_w = args.thumb_width
    cell_h = args.thumb_height + label_h
    width = margin * 2 + columns * cell_w + (columns - 1) * gap
    height = margin * 2 + rows * cell_h + (rows - 1) * gap

    sheet = Image.new("RGB", (width, height), "#f3f4f6")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for idx, path in enumerate(images):
        row = idx // columns
        col = idx % columns
        x = margin + col * (cell_w + gap)
        y = margin + row * (cell_h + gap)
        thumb = load_thumb(path, (args.thumb_width, args.thumb_height))
        sheet.paste(thumb, (x, y))
        label = path.name[:48]
        draw.text((x, y + args.thumb_height + 8), label, fill="#111827", font=font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=92, optimize=True)
    print(f"created {args.output} from {len(images)} images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
