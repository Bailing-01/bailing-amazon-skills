# Scene Planning

Use this file to plan the default set before prompt writing.

## Inputs To Extract

- Product category and real use logic.
- Visible product style: shape, color, material, finish, pattern, packaging, and brand mood.
- User-provided style words, target platform, audience, use scenario, season, region, and model requirements.
- Product-scene fit from `Product-Scene Match Lock`: category fit, style fit, audience fit, occasion fit, season fit, price/mood fit, and platform fit.
- Category template choice from `category-templates.md` when the product category is recognizable.
- Three scene pools: core use, style extension, and conversion proof.
- Whether the product needs body scale, hand interaction, try-on, wearable fit, installation, food serving, room placement, or outdoor proof.

## Default Eight-Image Set

When the user does not provide a different structure, generate these eight roles inside one `Campaign Visual System Lock` and one `Product-Scene Match Lock`:

1. Main hero scene: product-led first impression, clear silhouette, brand-matched environment.
2. Close use scene: closer camera distance, product being used or naturally placed in use, with hands/body/background leading attention to the product.
3. Detail atmosphere: material or craft detail with bright clean light and product-matched background, not a flat texture crop or dull surface shot.
4. Handheld or interaction scene: hand, body, pet, tool, furniture, or object interaction when physically appropriate.
5. Spatial display scene: product placed in a believable room, tabletop, shelf, vanity, bag, outfit, kitchen, bathroom, studio, outdoor, or other product-relevant space.
6. Function or benefit scene: visual proof of a real function, convenience, scale, organization, fit, texture, taste, or use moment.
7. Social lifestyle scene: natural, editorial, shareable composition with lived-in details that still match the campaign palette and keep the product dominant.
8. Brand mood scene: stronger art direction, premium campaign feel, distinctive lighting or set design while keeping product readable and central.

If a role does not fit the product, replace it with a more relevant role while preserving eight clearly different outputs.

For each role, write a brief `Match Rationale` before prompt writing. The rationale must name why the scene fits the product's style and usage, such as "black resort dress + refined terrace dinner occasion" or "running shoe + clean track warm-up scale proof." If the rationale would sound generic, revise the scene.

## Pool Balance

The default eight images should normally include:

- Core Use Pool: at least 3 images that show realistic wearing, use, placement, installation, carrying, serving, operation, or routine.
- Style Extension Pool: at least 2 images that lift brand mood, scene taste, audience aspiration, or seasonal emotion while staying realistic.
- Conversion Proof Pool: at least 2 images that clarify fit, scale, detail, material, construction, function, storage, comfort, or handling.
- Flexible Slot: 1 image assigned to the strongest missing buyer-decision need for the product.

If the product category has a stronger template in `category-templates.md`, use that template's eight roles and still check that the set covers core use, style extension, and conversion proof.

## Variation Requirements

Across the set, vary:

- camera angle: front three-quarter, side, top-down, low angle, close crop, medium scene, partial macro, environmental crop;
- product scale: full product, medium product, hand/body scale, close detail, room/table scale;
- lighting: vary direction and intensity subtly, but keep the same campaign light quality and avoid muddy, dim, or color-contaminated lighting;
- scene density: clean hero, practical use, prop-supported scene, lived-in social scene, campaign-style set, all subordinate to the product;
- background and props: only use props that support product use or style; do not add random accessories that imply unprovided bundle contents.

## Product-Supporting Composition

Each planned scene must define how the environment highlights the product:

- contrast support: background color makes the product silhouette and accent color cleaner;
- line support: track lines, table edges, body pose, props, or set curves guide the eye to the product;
- depth support: foreground/background blur or layered planes separate the product from the scene;
- scale support: model, hand, floor, room, or object scale clarifies product size and use;
- mood support: scene emotion fits the product style instead of becoming generic decor.

Do not plan a scene that could work for any product. The setting must be product-specific enough that removing the product would make the image lose its purpose.

## Scene Selection Rules

- Choose scenes from the product's real use, the user's request, visible product category, or a reasonable category inference.
- Avoid generic lifestyle scenes that do not explain the product.
- Do not choose a scene only because it is visually attractive. It must support at least one product decision dimension: fit, use, scale, material, comfort, storage, installation, taste, occasion, or brand mood.
- Keep scene family, model styling, props, and lighting aligned with the product's style tier. A premium product needs a controlled premium context; a practical everyday product needs believable everyday context; a technical product needs functional proof.
- Prefer scenes that would become meaningless if the product were removed. If the image still works as a generic lifestyle photo without the product, make the product interaction, scale proof, or style match stronger.
- For home goods, show believable room placement, scale, contact, shadows, and matching interior style.
- For beauty and personal care, prefer hands, vanity, bathroom, routine, texture, packaging, and sensory scene logic without medical claims.
- For fashion, accessories, shoes, and bags, include model or body-scale display unless the user excludes models.
- For food and drink, show serving, preparation, texture, packaging, table scene, and consumption context without inventing ingredients or health claims.
- For electronics and tools, show operation, ports or controls only if visible/provided, desk/workspace/use environment, scale, and safe handling.

## Model Inclusion

Include a model when the product needs wearing, carrying, holding, try-on, body-scale proof, skincare application, makeup application, food consumption, sports use, parenting use, or any scene where a human demonstrates the product better than a still-life setup.

Match model age range, gender presentation, styling, body type, and cultural context to the product and target use case when the user gives those details. If not specified, choose a natural commercial model that fits the product category without stereotyping or oversexualizing.
