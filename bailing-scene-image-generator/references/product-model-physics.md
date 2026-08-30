# Product, Model, And Physics

Use this file before prompt writing and reuse one lock across every image prompt.

## Product Identity Lock

Product reference images define identity, not final composition. Lock:

- silhouette, proportions, open or closed state, and volume relationships;
- primary and secondary color ratio;
- material appearance such as textile, leather, metal, glass, ceramic, plastic, paper, powder, liquid, cream, food, or transparent surfaces;
- pattern, logo, label, nameplate, decoration, printed-copy placement, and visual direction;
- structural parts such as handles, caps, lids, ports, zippers, seams, buttons, bases, straps, wheels, clasps, nozzles, pumps, or accessories;
- product scale relative to hands, body, table, shelf, bag, room, cup, tool, food, pet, or other scene objects.

Do not change the product into another style from the same category. Do not add unprovided colors, logos, labels, functions, package quantities, accessories, ports, certifications, or claims.

## Relative Scale Lock

When exact product dimensions, model size, garment size, room size, furniture size, or prop size are not provided, do not invent specific numeric measurements. Build scale from category norms, visible reference proportions, and realistic use logic.

Use relative scale language instead of fabricated numbers:

- apparel: standard adult garment fit unless the user specifies another wearer; shoulder straps, neckline, bust, waist, sleeve/strap position, hem length, pocket height, and skirt/pant volume must match the model's body proportions;
- footwear: match realistic foot length, ankle height, sole thickness, and shoe volume on the model's feet;
- bags and accessories: scale against hand, shoulder, waist, torso, phone, table, or chair without inventing dimensions;
- beauty and small goods: scale against hand, vanity surface, mirror, bottle, compact, brush, or routine context;
- home goods and furniture: scale against room, wall, bed, sofa, table, chair, door, window, or human body;
- food and drink: scale against plate, cup, hand, table setting, packaging, and serving context.

Each planned scene should include at least one credible scale reference when the product size matters: human body, hand, foot, table, chair, door, window, shelf, bed, cup, phone, or other product-relevant object. The reference must support scale without competing with the product.

If product size is highly uncertain, prefer conservative camera choices such as medium close-up, half-body, hand-held, worn detail, tabletop, or localized scene. Avoid wide room views, tiny distant placement, or oversized props that would expose an unreliable size assumption.

For apparel with no measurements, infer only garment category-level fit:

- preserve the reference garment's visible category and length impression, such as mini, midi, ankle-length, floor-length, cropped, fitted, relaxed, oversized, or voluminous;
- do not invent exact centimeter or inch values;
- keep waistline, bust fit, shoulder/strap placement, pocket height, hem fall, fabric volume, and drape physically plausible on an adult model;
- do not transform a long dress into a short dress, a fitted garment into oversized, or a structured garment into a different silhouette unless the user asks.

## Composition Freedom

The final image may change background, camera angle, crop, lighting, product placement, props, model, scene, and art direction as long as product identity remains recognizable and physically plausible.

If the source is a white-background product photo, every prompt must say:

```text
Use the reference image only to lock product identity. Do not replicate the white-background product photo as a white-background single-product image. Create a new realistic scene composition with changed camera angle, crop, lighting, background, and product placement.
```

## Physical Logic

Scene images must obey real physical behavior:

- the product must rest on, hang from, be held by, be worn by, installed on, or placed in the scene with believable contact;
- shadows must match the light source and product position;
- occlusion must make sense when hands, fabric, props, furniture, pets, or models overlap the product;
- perspective and scale must stay stable across all visible objects;
- materials must behave correctly under light: reflections, transparency, softness, wrinkles, liquid, powder, cream, metal, and glass should look plausible;
- do not let products float, bend impossibly, clip through hands, merge with props, or become too small to identify.

## Model Realism Lock

When using a model:

- default to a Chinese model when the user has not specified another ethnicity, region, or target market;
- use an optimistic, sunny, positive expression by default: relaxed confidence, gentle natural smile or bright calm expression, not cold, blank, gloomy, overly seductive, or exaggerated;
- make the model look like a real living person, not a plastic mannequin, wax figure, doll, AI-perfect face, or over-retouched catalog render;
- include natural skin texture, pores, subtle expression, realistic hands, believable joints, natural posture, and non-symmetric micro-imperfections;
- keep product contact physically correct: grip, wearing fit, strap tension, fabric drape, skincare application, shoe fit, bag carry, jewelry scale, or tool handling must be credible;
- avoid distorted fingers, impossible wrists, twisted limbs, floating product, melted edges, incorrect body scale, and mismatched shadows;
- clothing, makeup, hair, nails, and styling should support the product style without stealing attention unless the product is fashion or beauty.

If a model reference is provided, preserve the visible model identity and styling logic as much as the generation tool allows. If no model reference is provided, choose a model that fits the product use case and user-specified audience.
