# Quality Gates

Use this file before prompt writing and again before delivering images when judging whether a scene plan is ready. These gates are internal decision checks; do not output them unless the user asks for reasoning.

## Product Hero Score

Each planned image should pass these checks:

- First-glance visibility: product is immediately identifiable at thumbnail size.
- Frame share: product or worn product occupies enough of the frame for ecommerce reading.
- Contrast: background color, light, and depth separate product edges and key details.
- Guidance: lines, hands, pose, props, shadow, or depth lead attention toward the product.
- Detail preservation: key identity areas remain visible unless the role is a deliberate macro/detail crop.
- Scene support: every major prop or background element explains use, scale, material, comfort, occasion, or brand mood.

Revise the scene or crop if the product would feel secondary to the model, background, props, or atmosphere.

## Product-Scene Fit Gate

Before generation, reject or rewrite scenes that fail two or more:

- Category fit.
- Style fit.
- Audience fit.
- Occasion fit.
- Season and climate fit.
- Price/mood tier fit.
- Platform purpose fit.

When in doubt, choose a more conservative and closer-use scene rather than a dramatic but weakly matched scene.

## Physical And Scale Gate

Check:

- product contact: worn, held, placed, installed, opened, served, or used with believable support;
- scale reference: body, hand, foot, table, room, window, shelf, plate, cup, or other product-relevant object;
- no invented measurements when exact dimensions are missing;
- no floating, clipping, impossible bending, melted edges, or inconsistent shadows;
- for apparel, fit, shoulder/strap/sleeve, waist, pocket, hem, and fabric drape align with adult body proportions unless specified otherwise;
- for small products, avoid wide scenes where the product becomes too tiny or scale becomes unreliable.

## Luminosity And Color Gate

Check:

- scene color is bright, clean, and product-flattering unless the user requests dark mood;
- black products have rim light, pale or controlled backgrounds, and visible material texture;
- white or transparent products have edge contrast and are not lost against pure white;
- colorful products keep accurate color ratio and are not overwhelmed by competing background colors;
- no muddy gray, dirty brown, low-contrast gloom, noisy clutter, or color casts that make the product look cheap.

## Category Failure Avoidance

- Black products: avoid all-dark environments; use edge light and contrast.
- White products: avoid pure white-only scenes; add subtle shadow, texture, and edge separation.
- Transparent/glass products: use controlled highlights, darker edge references, and believable reflections.
- Small products: include hand/table/vanity/shelf scale and keep crop close.
- Apparel: include enough full-body or half-body context to prove length, fit, and wearing logic.
- Footwear: preserve realistic foot volume, shoe pair logic, sole thickness, and ground contact.
- Beauty: avoid fake clinical proof, invented ingredients, or impossible skin results.
- Home goods: avoid impossible room scale, floating installation, or decor that overwhelms the product.
- Electronics/tools: avoid invented screen interfaces, unsafe handling, and unsupported performance visuals.

## Prompt Revision Rule

If a planned prompt is weak, revise before generation. Use the smallest fix that solves the issue:

- increase product scale in frame;
- switch to a closer or more truthful scene;
- simplify props;
- adjust background material or color for contrast;
- add a credible scale reference;
- change model pose or crop so the product dominates;
- replace a mismatched scene family with a category-specific one.
