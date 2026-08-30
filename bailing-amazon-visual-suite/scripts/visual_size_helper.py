#!/usr/bin/env python3
"""Deterministic export helper for Amazon visual suite images."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageOps


SPECS = {
    "main": (2000, 2000),
    "secondary": (1000, 1000),
    "aplus_desktop": (1464, 600),
    "aplus_mobile": (1600, 1200),
}


def parse_size(value: str) -> Tuple[int, int]:
    try:
        width, height = value.lower().split("x", 1)
        return int(width), int(height)
    except Exception as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError("Size must look like 1000x1000") from exc


def open_image(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Input image not found: {path}")
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    return image


def fit_cover(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def fit_contain(image: Image.Image, size: Tuple[int, int], background: str) -> Image.Image:
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, background)
    if image.mode == "RGBA":
        layer = Image.new("RGB", image.size, background)
        layer.paste(image, mask=image.getchannel("A"))
        image = layer
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image.convert("RGB"), (x, y))
    return canvas


def save_image(image: Image.Image, output: Path, quality: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    suffix = output.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        image.convert("RGB").save(output, quality=quality, optimize=True)
    else:
        image.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resize/crop Amazon visual suite assets.")
    parser.add_argument("--type", required=True, choices=sorted(SPECS))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--size", type=parse_size, help="Override final size, e.g. 2000x2000")
    parser.add_argument("--mode", choices=("cover", "contain"), default="cover")
    parser.add_argument("--background", default="white")
    parser.add_argument("--quality", type=int, default=95)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    if not args.check_only and args.output is None:
        parser.error("--output is required unless --check-only is used")

    size = args.size or SPECS[args.type]
    try:
        image = open_image(args.input)
    except Exception as exc:  # noqa: BLE001
        parser.error(str(exc))

    if args.check_only:
        ok = image.size == size
        print(f"{args.input}: actual={image.width}x{image.height} expected={size[0]}x{size[1]} ok={ok}")
        return 0 if ok else 2

    if args.mode == "contain":
        result = fit_contain(image, size, args.background)
    else:
        result = fit_cover(image, size)

    save_image(result, args.output, args.quality)
    print(f"exported {args.output} {result.width}x{result.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
