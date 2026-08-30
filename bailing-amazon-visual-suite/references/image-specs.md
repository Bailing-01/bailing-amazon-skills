# Image Specs

## Required Output Set

| Asset type | Count | Final size | Ratio | Default filename |
|---|---:|---:|---:|---|
| Main image | 1 | 2000x2000 unless user specifies another square size | 1:1 | `main-01.jpg` |
| Secondary image | 6 | 1000x1000 unless user specifies another square size | 1:1 | `secondary-01.jpg` to `secondary-06.jpg` |
| Desktop A+ | 7 | 1464x600 | 61:25 | `aplus-desktop-01.jpg` to `aplus-desktop-07.jpg` |
| Mobile A+ | 7 | 1600x1200 | 4:3 | `aplus-mobile-01.jpg` to `aplus-mobile-07.jpg` |

## Generation Canvas

- Main image: generate or export square.
- Secondary image: generate or export square.
- Desktop A+: if the image model requires dimensions divisible by 16, generate at 1488x608 or 1536x640, keep critical content in the center safe area, then crop or resize to 1464x600.
- Mobile A+: generate 1600x1200 or another 4:3 canvas that can be resized cleanly.

## Safe Areas

- Keep critical product, headline, and labels inside the center 86% of the frame.
- Keep desktop A+ text away from the outer 6% left/right and 8% top/bottom.
- Keep mobile A+ headline readable at phone width; use one headline, one short subcopy, and up to three labels by default.

## Main Image Rules

- Use a real white-background product photo as the source.
- Do not add lifestyle scenes, props, badges, ratings, claims, icons, text, fake packaging, or accessories not shown/provided.
- Optimize white background, product centering, sharpness, and subject occupancy.
- If the product photo is not sufficient for a compliant main image, report the issue and ask for a better source image.

## Naming And Folders

Use a clear output folder:

```text
<product-slug>-amazon-visual-suite-v1/
  main/
  secondary/
  aplus-desktop/
  aplus-mobile/
  qa/
```

Recommended final file extensions are `.jpg` for Amazon-ready exports and `.png` for transparent/intermediate files only.
