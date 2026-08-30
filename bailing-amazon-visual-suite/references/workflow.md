# Workflow

Run the complete Amazon visual suite in one pass unless the user explicitly asks for planning only.

## 1. Product Parsing

Identify visible facts from product photos:

- Category, shape, silhouette, proportions, color, material look, texture, structure, openings, handles, wheels, lids, buttons, accessories, packaging, logo, labels, pattern placement, and readable text.
- Possible use contexts and buyer scenarios.
- Unknown facts that require user confirmation.

Write a `Product Master Description` that locks the product identity for all generated images. Preserve this identity across the full set.

## 2. Information Confidence

Classify every claim:

- `confirmed`: provided by the user, visible in the image, or readable on packaging.
- `reasonable inference`: conservative inference from the visible product or common use.
- `needs confirmation`: material, capacity, certification, compatibility, test data, guarantee, medical effect, review, sales number, ranking, or performance claim not proven by user material.

Use confirmed claims first. Use reasonable inference with soft wording. Do not put needs-confirmation claims on images.

## 3. Buyer Demand Map

Rank buyer concerns in this order unless category evidence suggests otherwise:

1. Attraction: why notice this product.
2. Understanding: what it does and where it fits.
3. Trust: why believe the product.
4. Comparison: why choose this SKU.
5. Purchase: how to choose, use, and reduce risk.

## 4. Selling Point Match

Convert product facts into visual proof. Each image must answer one buyer question and show one dominant proof method:

- Scene proof.
- Action proof.
- Texture or detail proof.
- Scale or size proof.
- Before/after or comparison proof.
- Structure or mechanism proof.
- Package or included-items proof.

## 5. Style Locks

Create these locks before prompts:

- `Campaign Style Lock`: platform, marketplace language, design direction, palette, lighting, typography mood, label style, and density.
- `Product Consistency Lock`: product identity, structure, color-area ratio, material look, logo/label placement, and physical scale.
- `Layout Diversity Lock`: at least five distinct layout structures across the 13 selling images other than main image; no more than three images may use the same large-product-plus-top-title formula.

## 6. Prompt Writing

Every prompt must be standalone and include:

- Exact asset type and final role.
- Product Master Description.
- Campaign Style Lock.
- Product Consistency Lock.
- Buyer question and selling point.
- Visual proof method.
- Headline, optional subcopy, and short labels in the marketplace language.
- Required source images.
- Forbidden unsupported claims and forbidden design elements.

## 7. Generation Backend

Prefer this order:

1. Existing Bailing deployment helper or fixed API route available in the current workspace or configured environment.
2. Bundled compatible fixed-interface generation scripts when present and configured.
3. Built-in `image_gen` final fallback.

Never write API keys into skill files. Read credentials only from the environment or existing project configuration.

## 8. Post-Processing

Use deterministic post-processing only after final images are generated:

- Resize, crop, pad, format convert, and dimension check.
- Generate a contact sheet from finished images.

Do not locally compose final commercial images from pieces. If a layout is wrong, regenerate the image.

