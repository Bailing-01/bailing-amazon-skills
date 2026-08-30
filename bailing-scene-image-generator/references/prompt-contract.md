# Prompt Contract

Each scene image must be generated independently. Do not place multiple scene images on one canvas.

## Required Prompt Blocks

Every prompt must include:

1. `square 1:1 ecommerce product scene image, 1024x1024 composition`.
2. `Campaign Visual System Lock`: shared palette, brightness, background material family, lighting quality, prop taste, model styling logic, and retouching feel for the whole set.
3. `Product Hero Lock`: how the product stays dominant, bright, readable, separated from the scene, and supported by composition lines or props.
4. `Product Identity Lock`: preserve the exact visible product identity from references.
5. `Product-Scene Match Lock`: category fit, style fit, audience fit, occasion fit, season fit, price/mood fit, and platform fit for the set.
6. `Match Rationale`: one sentence explaining why this exact scene suits the product's style and use scenario.
7. `Relative Scale Lock`: preserve realistic category-normal scale relationships without inventing exact dimensions; name the scale reference used in the scene.
8. `Scene Role`: one role from the scene plan or the user's requested scene role.
9. `Use Scenario`: the real usage moment, environment, or display context.
10. `Style Direction`: product-matched visual style, color mood, lighting, and prop system within the campaign lock.
11. `Camera And Composition`: angle, distance, crop, product scale, foreground/background depth, product placement, and eye-path toward the product.
12. `Physical Logic`: support, contact, shadow, occlusion, perspective, gravity, material behavior, and scale.
13. `Model Direction` when applicable: model type, default Chinese model unless otherwise specified, optimistic sunny positive expression, pose, natural skin texture, product interaction, and body contact rules.
14. `Quality Gate Lock`: product hero visibility, product-scene fit, physical scale, luminosity/color, and category failure avoidance for this specific image.
15. `Variation From Other Images`: how this image differs from the rest of the set without breaking the campaign system.
16. `Negative Constraints`: no fake claims, fake badges, fake certification, fake reviews, watermark, random logos, unsupported functions, wrong accessories, product drift, fabricated dimensions, distorted model anatomy, dull/muddy scene color, clutter that competes with the product, style-scene mismatch, or white-background replication.

## Product Reference Clause

Use this clause whenever product photos are provided:

```text
Use all uploaded product reference images as strict visual source of truth for product identity only. Preserve the same silhouette, proportions, structure, color-area ratio, material texture, finish, logo or label placement, patterns, decorative elements, and included accessories. Do not copy the source photo background, lighting, camera angle, crop, or white-background product-photo composition.
```

## Scene Quality Clause

Use this quality language in every prompt:

```text
Real-shot commercial photography texture, 8K high-definition look, realistic lens feel, natural light behavior, product-led composition, luminous clean color, bright airy commercial light, product clearly separated from the scene, crisp focus on the product, fine material texture, realistic shadows, believable environment depth, accurate perspective, clean edges, no watermark, no compression artifacts, no distorted product geometry, no plastic CG/rendered appearance.
```

## Product Hero Clause

Use this clause in every prompt:

```text
The product must be the visual hero: occupy the primary attention zone, remain large enough to read on mobile, be the brightest or clearest object in the frame, and be framed by background lines, props, depth, or model pose. Scene elements must support product desirability and never compete with or visually bury the product.
```

## Product-Scene Match Clause

Use this clause in every prompt:

```text
The scene must be specifically matched to the product's category, visible design style, target user, real usage occasion, season, price/mood tier, and ecommerce/social-commerce purpose. Avoid generic attractive backgrounds. Every prop, model styling choice, background material, and lighting choice must either clarify product use, elevate product desirability, prove scale/fit/material, or express the correct brand mood.
```

## Quality Gate Clause

Use this clause in every prompt:

```text
Before generation, this prompt must pass product hero visibility, product-scene fit, physical scale, luminosity/color, and category failure-avoidance checks. If any scene element would make the product secondary, mismatched, unclear, physically implausible, dull, muddy, too small, or claim-like, revise the scene toward a closer and more product-led use case.
```

## Relative Scale Clause

Use this clause whenever dimensions are not provided:

```text
No exact dimensions were provided. Do not invent measurements. Use realistic category-normal relative scale based on the reference image and product type. Include a credible scale reference in the scene, such as the model's body, hand, foot, table, chair, door, window, shelf, or other relevant object, while keeping it subordinate to the product. Keep proportions physically plausible and avoid wide views or props that imply unreliable size claims.
```

## Model Clause

Use this clause when the product needs a model:

```text
Use a realistic natural Chinese human model by default unless the user specified another ethnicity, region, or target market. The model should have an optimistic, sunny, positive expression: relaxed confidence, gentle natural smile or bright calm expression. The model must feel like a real living person with natural skin texture, pores, subtle expression, realistic hands, believable joints, natural posture, and physically correct contact with the product. Avoid cold blank expression, gloomy mood, mannequin skin, waxy face, over-smoothed retouching, distorted fingers, twisted limbs, floating product, and impossible wearing or holding logic.
```

## Copy And Text

Default scene images should be primarily photographic and may omit on-image text unless the user asks for poster, ad, banner, or ecommerce copy. If text is requested, keep it short and do not invent unsupported claims, certifications, prices, discounts, reviews, ratings, or performance data.

## Prompt-Only Mode

If the user explicitly asks for prompts only, output one complete prompt per planned image and do not call generation tools. Keep the same product, scene, physics, model, and negative constraints.
