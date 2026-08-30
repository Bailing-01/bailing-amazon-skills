# Visual System

Read this file before scene planning. A scene-image set should feel like one campaign, not eight unrelated pictures.

## Campaign Visual System Lock

Create one lock for the full set and reuse it in every prompt. Include:

- palette: product-derived dominant colors plus restrained neutrals; keep the product's strongest color as the campaign accent;
- brightness: clean, translucent, airy commercial light; avoid muddy gray, dirty red, brown cast, flat shadow, or heavy low-contrast backgrounds unless the user asks for a dark mood;
- background system: shared material family chosen from the product's matched scene family, such as clean track surface for athletic products, luminous terrace/gallery for elegant apparel, vanity/bathroom for beauty, organized desk for electronics, or believable room placement for home goods;
- lighting system: one consistent light logic such as fresh morning daylight, soft high-key studio, or luminous window light;
- prop system: props must be few, clean, product-relevant, and color-coordinated; they should never compete with the product;
- model styling: when models appear, default to a Chinese model unless the user specifies otherwise; clothing, skin tone, positive sunny expression, pose, and crop must feel from the same campaign as the still-life images;
- retouching feel: real-shot commercial photography texture with an 8K high-definition look, crisp product texture, bright whites, clean shadows, believable environment depth, and no plastic CG/rendered appearance.

## Product Hero Lock

Every image must actively highlight the product. The prompt must specify:

- product occupies the primary attention zone and remains immediately readable on mobile;
- product is the brightest or most contrast-clear object in the frame unless the user requests a dark campaign;
- background lines, props, hands, body angle, or set shapes guide the eye toward the product;
- foreground/background depth separates the product from the scene;
- scene elements explain use, scale, comfort, style, material, or mood; remove elements that do not support the product;
- crop must not cut away key identity areas unless the role is an intentional detail crop.
- the selected environment must pass the product-scene match test: category, style, audience, occasion, season, and mood tier should all support the product.

## Clarity And Luminosity Rules

For default ecommerce scene images:

- prefer fresh whites, clean pinks, soft blush, pale gray, light concrete, sky blue, controlled green, or other product-matched bright accents;
- keep white products bright but not blown out; preserve knit, leather, plastic, metal, glass, or fabric texture;
- use soft fill light to lift shadows and keep color transparent;
- avoid dirty track reds, dull beige, heavy brown wood, gray cast, dim indoor light, or noisy background color when the product is light-colored;
- if outdoor scenes use greenery, keep it blurred and secondary so green does not overpower the product.

## Unified Variety

Vary composition without changing the campaign:

- change camera distance, angle, crop, body interaction, or set geometry;
- keep the same color family, light quality, product retouching, and prop taste;
- do not jump between unrelated aesthetics such as luxury studio, random home entryway, gritty street, casual phone snap, and sports poster unless the user asks for style exploration.

## Product-Supporting Scene Test

Before generation, check each planned image:

- What does this scene prove or amplify about the product?
- Does this scene match the product category, style, user, occasion, season, and mood tier?
- Does the product still dominate the first glance?
- Are the colors making the product cleaner, brighter, and more desirable?
- Are props and model styling subordinate to the product?
- Does this image belong to the same campaign as the other seven?

If any answer is weak, revise the scene role before writing the prompt.
