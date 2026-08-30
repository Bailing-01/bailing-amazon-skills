# Page Task Table

Use this default 21-image task table unless the user explicitly requests a smaller count. Category requirements may change the selling logic or order, but must not reduce the default count.

Hard count rule:

- Default output must include all 21 IDs below.
- Do not treat Amazon A+ as only 6 images.
- Do not replace the 21 separate final images with a collage.
- If execution starts with A+ only, continue afterward until main image, secondary images, desktop A+, and mobile A+ are all complete.

## Main Image

| ID | Role | Buyer task | Visual proof |
|---|---|---|---|
| main-01 | Search/result main image | Recognize the exact product quickly | Real product on pure white background, clear edges, centered, high subject occupancy |

## Six Secondary Images

| ID | Role | Buyer question | Visual proof direction |
|---|---|---|---|
| secondary-01 | Core benefit | What is the main reason to buy? | Strongest product benefit in one scene or clean studio composition |
| secondary-02 | Pain-point scene | What problem does it solve? | Before/after, user frustration, or real context contrast |
| secondary-03 | Function/structure | How does it work? | Structural callouts, mechanism, material, or feature close-up |
| secondary-04 | Size/fit/compatibility | Will it fit my use case? | Scale reference, dimensions, model choices, or compatibility caveat |
| secondary-05 | Use steps | Is it easy to use? | 3-step operation, hand interaction, installation, opening, cleaning, or daily flow |
| secondary-06 | Trust/package recap | What exactly do I get and why trust it? | Included items, packaging, care, conservative proof, or selling-point summary |

## Seven Desktop A+ Modules

| ID | Role | Buyer question | Visual proof direction |
|---|---|---|---|
| aplus-desktop-01 | Brand/product opening | What is this product's promise? | Wide hero scene with product and campaign headline |
| aplus-desktop-02 | Buyer demand | Why do I need it? | High-priority pain point or desired result |
| aplus-desktop-03 | Core feature | What makes it different? | Mechanism, structure, technology, craft, or detail evidence |
| aplus-desktop-04 | Scenario proof | Where does it fit in real life? | Lifestyle/use environment with product scale |
| aplus-desktop-05 | Detail trust | Can I trust the material/build? | Macro, texture, parts, finish, or visible construction |
| aplus-desktop-06 | Comparison/choice | Why choose this version? | Conservative comparison, size/version guide, or feature matrix without fake competitor claims |
| aplus-desktop-07 | Closing summary | What should I remember before purchase? | Cohesive recap with product and 3-4 confirmed reasons |

## Seven Mobile A+ Modules

Use the same selling logic as desktop A+, but compose each as a mobile-first 1600x1200 module.

| ID | Role | Mobile composition requirement |
|---|---|---|
| aplus-mobile-01 | Product opening | Larger product, shorter headline, single dominant focal point |
| aplus-mobile-02 | Buyer demand | One scene/action, minimal labels |
| aplus-mobile-03 | Core feature | Macro or structure detail must remain readable |
| aplus-mobile-04 | Scenario proof | Product scale and context must be obvious in one second |
| aplus-mobile-05 | Detail trust | Detail crop or material proof over dense text |
| aplus-mobile-06 | Comparison/choice | Simplify comparison to the fewest useful points |
| aplus-mobile-07 | Closing summary | Clear product recap, no crowded checklist |

## Required Fields For Each Row

For every planned image, include:

- `id`
- `asset_type`
- `final_size`
- `buyer_question`
- `selling_point`
- `information_confidence`
- `visual_proof`
- `headline`
- `subcopy`
- `layout_direction`
- `source_material`
- `risk_note`

## Completion Check

Before final delivery, verify these IDs exist as separate final images:

```text
main-01
secondary-01
secondary-02
secondary-03
secondary-04
secondary-05
secondary-06
aplus-desktop-01
aplus-desktop-02
aplus-desktop-03
aplus-desktop-04
aplus-desktop-05
aplus-desktop-06
aplus-desktop-07
aplus-mobile-01
aplus-mobile-02
aplus-mobile-03
aplus-mobile-04
aplus-mobile-05
aplus-mobile-06
aplus-mobile-07
```

If any ID is missing, the task is incomplete unless the user explicitly requested fewer images.
