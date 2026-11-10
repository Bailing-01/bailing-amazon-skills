---
name: bailing-amazon-visual-suite
description: "Amazon visual suite generation for cross-border ecommerce. Use when Codex needs to create a complete Amazon image set from product photos, selling points, listings, competitor links, or reference visuals: 1 square main image, 6 square secondary images, 7 desktop A+ modules, and 7 mobile A+ modules. Trigger on requests such as Bailing亚马逊主副图A+4.0, Bailing亚马逊主副图A+, 亚马逊整套图片, 主图副图A+一次性生成, Amazon main images, secondary images, A+ modules, listing image suite, or cross-border Amazon visual workflow."
---

# Bailing亚马逊主副图A+4.2

Create a complete Amazon visual image suite in one run: product analysis, selling-point strategy, layout planning, prompts, generation, deterministic size export, QA, and delivery.

Default output count is fixed unless the user explicitly asks otherwise:

- 1 main image, square 1:1.
- 6 secondary images, square 1000x1000.
- 7 desktop A+ modules, final 1464x600.
- 7 mobile A+ modules, final 1600x1200, unless the live listing already uses another mobile size (for example 600x450); follow the live size when it is known.

Hard count rule: the default deliverable is exactly 21 final images. Do not reinterpret this skill as a 6-image Amazon A+ generator. Do not downgrade, merge, skip, or collapse the output into 6 A+ modules, a collage, or a partial A+ set unless the user explicitly requests a smaller output count in the current task.

## 0. Generation Backend (hard rule, added in 4.2)

- **Preferred route: `gsk img` + gpt-image-2.** Call once per image with `--args-file` JSON that includes the real reference image URL(s) and the full prompt query required by the Prompt Contract below.
- Codex / built-in `image_gen` and other backends are **fallbacks only**. Explain why the preferred route cannot be used and get the user's approval before switching. Do not change backends just to save steps.
- Record the backend, reference images, and full prompt for every image in the generation log so the run can be reproduced.
- Read `references/generation-backend.md` for route details, helper argument rules, and fallback reporting.

## 1. Prompt Contract (added in 4.2: be specific, not abstract)

Every image prompt must include all of the following. Do not write only abstract style words such as "premium" or "atmospheric":

1. **Canvas and safe area:** target size/ratio; where key content sits in the safe area; do not draw bleed lines, crop guides, or helper frames.
2. **Layout:** left/right or top/bottom split (for example 55% product on the left, 45% copy on the right), plus product position and angle.
3. **Series color lock:** one primary/secondary palette for the whole set (hex values or clear color names), reused on every image.
4. **Full Product Master Description:** color, printed text, logo, and structure restated in full on every prompt; do not abbreviate.
5. **On-image text verbatim:** headlines and short lines written exactly as they should appear, plus font style; do not invent extra words.
6. **Product large and complete:** the product occupies enough of the frame and is not cropped (except a close-up that is explicitly labeled as such).
7. **Compliance constraints for this image:** forbidden words; how sensitive words are handled on A+ (see QA).

## 2. Premium A+ Spec (added in 4.2)

- Premium A+ defaults to **7 narrative modules at 1464×600** on desktop. Do not drop to 6 modules or switch to standard A+ 970×600 without an explicit user request.
- Mobile size follows the live listing when known (for example keep 600×450 if that is already live). Otherwise use the default 1600×1200 in this skill.
- Keep the 7-module arc, for example: Hook / emotion open → core benefit → use scene → detail/evidence → What's Included → Comparison → brand close. Do not drop What's Included or Comparison on your own.

## 3. Anti-Regression Gate (added in 4.2)

- **Before a remake:** put the user-approved previous version beside the new plan and compare style, palette, layout, narrative, and product consistency, image by image. The new version must not be weaker than the baseline on any of these.
- **Sample first:** generate 1–2 sample images, get user confirmation, then batch. The user may skip this by saying to generate the full set directly.
- Compliance edits should change only visible wording (angle, occlusion, or wording swaps) while keeping the baseline style and structure. Do not rebuild the whole set, and do not turn a real product label into an anonymous bottle.

## Required Workflow

1. Require at least one real product white-background image before producing the main image. Do not invent a main product image.
2. Read `references/workflow.md` before planning.
3. Read `references/image-specs.md` before writing prompts or resizing outputs.
4. Read `references/page-task-table.md` before creating the 21-image task table.
5. Read `references/quality-rules.md` before generation and again before delivery QA.
6. Read `references/generation-backend.md` before choosing the generation route. Follow section 0: prefer `gsk img` + gpt-image-2.
7. Build a complete `Product Master Description` and reuse the full text in every generated visual prompt (Prompt Contract item 4).
8. Generate every final visual as a separate image. Do not use a collage as a substitute for an individual final image.
9. Use the backend order in section 0 and `references/generation-backend.md`. If the preferred `gsk img` + gpt-image-2 route is unavailable or failed, explain the reason and get user approval before falling back to a Bailing deployment helper, a fixed API script, or built-in `image_gen`.
10. When passing product or reference images to a PowerShell helper, follow `references/generation-backend.md`: pass one semicolon-joined string to `-ReferenceImage`, never a PowerShell array or comma-separated path list.
11. For multi-image helper generation, follow `references/generation-backend.md`: prefer 3-second staggered background submission, then automatically fall back to serial generation if background jobs fail.
12. Use `scripts/visual_size_helper.py` only for deterministic resize, crop, padding, format conversion, and dimension checks.
13. Use `scripts/make_contact_sheet.py` only to create a review overview from finished images.
14. Treat fewer than 21 final images as incomplete execution unless the user explicitly requested fewer images. Report incomplete execution and continue generating the missing groups rather than stopping at 6 A+ modules.
15. For remakes, pass the anti-regression gate in section 3 (baseline comparison and 1–2 samples) before batch generation.

## Inputs

Collect these if available, but do not block except for the real white-background product image needed for the main image:

- Product name, category, platform, marketplace site, and target buyer.
- White-background product images and optional side/detail/packaging/lifestyle images.
- Listing title, bullet points, description, A+ copy, product facts, parameters, certificates, and forbidden claims.
- Brand assets, colors, reference visuals, competitor pages, and style preferences.

If platform or marketplace is missing, default to Amazon US and English image copy.

## Planning Contract

Before generation, output a concise plan containing:

- Product Image Analysis.
- Information Confidence: `confirmed`, `reasonable inference`, or `needs confirmation`.
- Buyer Demand Map.
- Demand-to-Selling-Point Match.
- Product Master Description.
- Campaign Style Lock and Product Consistency Lock.
- Complete 21-image task table with image id, asset type, final size, buyer question, selling point, visual proof, headline, subcopy, layout, required source material, and risk note.

Use conservative copy for unproven points. Do not put `needs confirmation` claims on images.

## Generation Contract

Generate in this order:

1. Main image.
2. Six secondary images.
3. Seven desktop A+ modules.
4. Seven mobile A+ modules.

Completion requires all four groups. If any group is missing, continue with the missing group. A run that only creates A+ images, only creates 6 modules, or only creates a contact sheet is not complete.

Desktop and mobile A+ modules may share the same selling logic, but must be independently composed for their final aspect ratios. Do not stretch, squeeze, or crop desktop modules into mobile modules as the final design.

## Delivery Contract

Deliver:

- Generation method used: `gsk img` + gpt-image-2, or an approved fallback (Bailing helper, fixed API script, or built-in `image_gen`).
- Save directory.
- Numbered file list grouped by main, secondary, desktop A+, and mobile A+.
- Contact sheet path when created.
- Generation log with backend, reference images, and full prompt per image.
- QA notes covering product consistency, physical logic, text legibility, language, unsupported claims, dimensions, repeated template risk, and (for remakes) baseline regression checks.
- Missing evidence list for claims, parameters, certifications, compatibility, performance, or compliance language.

Include an explicit final count line in delivery: `Final kept image count: 21/21`. If the count is lower, state `Incomplete` and list the missing IDs.
