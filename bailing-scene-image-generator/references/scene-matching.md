# Product-Scene Matching

Use this file before visual-system planning. The goal is to make the scene feel specifically made for the product's style and real usage, not like a generic attractive background.

## Product-Scene Match Lock

Create one concise lock for the whole set. Include:

- product category and real use logic;
- visible product style: identify category mood and finer style signals such as casual, sporty, elegant, cute, minimalist, luxury, outdoor, homey, professional, functional, youthful, mature, festive, French, quiet luxury, sweet-cool, technical, retro, resort, commuter, premium basic, or other clear style;
- material and sensory signals such as cotton-linen, chiffon, knit, leather, metal, glass, acrylic, matte plastic, glossy ceramic, transparent, soft, structured, breathable, crisp, plush, or technical;
- emotional direction such as fresh, relaxed, refined, professional, energetic, warm, delicate, bold, trustworthy, playful, calming, or powerful;
- target audience and body/user context when inferable;
- likely season, time of day, and occasion;
- price/mood tier: value, everyday commercial, premium, luxury, professional, playful, or technical;
- scene families that fit the product;
- scene families to avoid because they weaken credibility or product desire.

When the user gives an explicit scene, obey it unless it contradicts product truth or safety. If the user gives only product photos, infer conservatively from visible product category and style.

## Matching Dimensions

Evaluate every scene across these dimensions before prompt writing:

- Category Fit: Is this where the product would realistically be worn, used, placed, installed, carried, served, or displayed?
- Style Fit: Does the environment match the product's design language, material, color, silhouette, and mood?
- Audience Fit: Would the target buyer recognize the model, room, props, and occasion as relevant to them?
- Occasion Fit: Is the scene tied to a believable moment such as commute, workout, dinner, vacation, party, office, home routine, gifting, storage, cooking, travel, or outdoor use?
- Season And Climate Fit: Do clothing, light, props, and environment match the product's likely season and usage temperature?
- Price/Mood Fit: Does the setting support the product's perceived tier instead of making it feel cheaper, random, or over-staged?
- Platform Fit: For ecommerce, is the product readable and decision-useful; for social commerce, is it still product-led and shareable?

If a planned scene fails two or more dimensions, replace it before generation.

## Three Scene Pools

Build scenes from three pools before assigning the eight-image set:

- Core Use Pool: the most realistic situations where the buyer would wear, use, place, install, carry, serve, or operate the product. These scenes prove basic credibility.
- Style Extension Pool: environments that amplify the product's design language, emotional tone, season, and audience aspiration without losing realism.
- Conversion Proof Pool: scenes that help a buyer decide, such as fit, size, scale, material, detail, texture, storage, installation, grip, comfort, capacity, routine, or compatibility when provided.

Default eight-image sets should include all three pools. Avoid making all eight images pure mood scenes, and avoid making all eight images flat technical proof scenes.

## Scene Family Guidance

Use these as decision examples, not rigid templates:

- Fashion dresses: model-led wearing scenes, resort terrace, gallery corridor, garden party, refined street, brunch patio, boutique fitting room, event entrance, mirror/detail styling. Avoid kitchens, messy bedrooms, gym scenes, office desks, or generic cafes unless the dress style supports them.
- Athletic shoes and sportswear: track, clean gym, training path, locker-room detail, stretching, warm-up, road running, studio sport set. Avoid fragile luxury rooms, unrelated cafes, or overly formal spaces.
- Bags and accessories: outfit pairing, hand/shoulder carry, travel check-in, desk-to-evening transition, boutique display, car/entryway placement. Avoid contexts where scale or carrying logic becomes unclear.
- Beauty and personal care: vanity, bathroom routine, clean sink, hand texture, mirror light, travel pouch, shelf display. Avoid medical clinics or efficacy-test scenes unless verified by the user.
- Home goods: room placement, touch/use interaction, installation detail, before/after ambience without false claims, scale against furniture/window/wall. Avoid random outdoor scenes unless product supports it.
- Kitchen, food, and tableware: serving, preparation, table setting, ingredient-adjacent scenes only when ingredients are provided or obvious. Avoid health claims or invented recipe functions.
- Electronics and tools: work surface, hand operation, port/control visibility if provided, safe use posture, organized storage, productivity scene. Avoid unsupported features shown on screens.

## Mismatch Rejection

Reject or revise scenes that:

- could fit almost any product after swapping the object;
- make the product look smaller, cheaper, duller, or less useful;
- introduce props that imply unprovided accessories, functions, ingredients, certifications, or bundles;
- clash with the product's visual language, such as playful props for severe luxury products or heavy formal sets for lightweight casual goods;
- require exact dimensions that were not provided;
- use models whose age, styling, expression, body context, or action conflicts with the product's buyer or use case.

## Style-Scene Red Flags

- Formal or evening apparel in kitchens, messy bedrooms, gyms, basic offices, or random sidewalks unless the specific style supports contrast.
- Sport and outdoor goods in fragile luxury rooms, static sitting rooms, or scenes with no movement/use logic.
- Beauty packaging in cluttered bathrooms, medical clinics, fake laboratories, or treatment-result scenes.
- Home goods in spaces where size, installation, or room scale becomes implausible.
- Tools and electronics in settings that hide operation, ports, safety, or scale.
- Value/everyday products in excessively luxurious scenes that make the product feel unbelievable.
- Premium products in cheap, crowded, dirty, or random scenes that lower perceived value.
- Products with bright or delicate colors in muddy, dark, or heavily color-contaminated environments.

## Scene Role Mapping

For the default eight images, assign each role to a matching scene family:

1. Main hero: highest-confidence style and occasion fit.
2. Close use: proves the product's most important use or wearing logic.
3. Detail atmosphere: material, craft, texture, finish, or construction in a matching environment.
4. Interaction: hand/body/object contact that clarifies use and scale.
5. Spatial display: believable placement or environment that supports product tier.
6. Function/benefit: visual proof of a real benefit without unsupported claims.
7. Social lifestyle: a natural shareable moment that target buyers would want.
8. Brand mood: strongest product-style expression, still product-readable.

Each planned image should include a one-line reason: `Match Rationale`, explaining why that scene suits the product.
