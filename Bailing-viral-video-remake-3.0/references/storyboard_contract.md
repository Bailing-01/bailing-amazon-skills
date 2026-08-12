# Storyboard Contract

Generate a storyboard before every paid Seedance recreation.

## Purpose

The storyboard is the quality gate between the product-specific brief and video generation. In this skill, the default storyboard is a reference-faithful director plan: it should preserve the reference video's shot structure, model/host role, actions, camera movement, sticker/overlay language, caption rhythm, sound-effect rhythm, and scene style while replacing the product and disallowed elements. It prevents disconnected shots, inconsistent visual style, weak product logic, unsupported claims, and overcomplicated Seedance prompts. A complete storyboard always includes both the text breakdown and one visual director storyboard sheet image.

## Required Panel Fields

Each panel must include:

- start and end time
- story purpose
- reference element preserved
- adaptation reason when a reference element changes
- scene style matched to the reference video
- visual composition
- framing
- model/host role when present in the reference
- camera movement
- product action
- product fidelity constraint
- voiceover line
- on-screen text intent
- readable text layer policy: `voiceover_only`, `sparse_stickers`, `caption_driven`, or `no_readable_text`
- sticker/overlay intent
- sound-effect intent
- continuity note
- risk note

If voiceover is preserved, do not storyboard both line-by-line voiceover subtitles and separate caption/sticker text for the same sentence. Use one readable text layer only. Default to sparse stickers, punch headlines, feature badges, and CTA lockups instead of transcript subtitles, unless the reference is explicitly caption-driven or the user asks for subtitles.

## Panel Count Rule

Do not force a fixed storyboard length. The panel count must follow the reference blueprint or product-specific `shot_plan`.

Examples:

- A five-shot reference structure produces five storyboard panels.
- A seven-shot reference structure produces seven storyboard panels.
- A fast montage reference may produce more panels if each segment has a distinct narrative or camera job.

The total duration must equal the integer target duration from the duration policy. Round the raw reference duration half up when it is 4-15 seconds, cap at 15 seconds when the reference is longer than 15 seconds, and ask before padding if the rounded target is shorter than Seedance's supported minimum duration.

If the reference contains more shots than can be reliably generated in 15 seconds, merge only adjacent shots with the same narrative and camera job. Record the merge in `adaptation_reason`. Do not collapse a model-led reference into a product-only storyboard unless the model element is unsafe, legally blocked, or explicitly rejected by the user.

## Visual Storyboard Sheet Rule

Generate one storyboard sheet image before every paid video generation. The sheet must contain multiple frame cells in reading order; each cell represents one storyboard panel and includes short notes for time, shot purpose, reference-matched scene style, camera movement, action, voiceover, and on-screen text intent.

The number of frame cells must equal the adapted `shot_plan` count. For example, a seven-shot reference produces one storyboard sheet with seven frame cells, not seven separate storyboard images.

The storyboard sheet should preview composition, lighting, product placement, camera angle, model/host role when present, gestures/actions, mood, props, background, sticker/overlay style, caption style, sound cues, and continuity. Its scene style should be derived from the reference-video blueprint unless the user asks for a new style. It is a director planning artifact, not a final video frame, and not a way to bypass person or face policies.

## Person Face Marker Rule

When a visible face appears in a visual storyboard sheet, render the person in a realistic ecommerce storyboard style and add a red 5x6 grid overlay across the full face area. The grid should be medium thickness, clearly visible, and confined to the face area. Do not use sketch, oil-paint, blank-face, blur, mask, or face-removal as the default storyboard treatment.

The final video prompt must clarify that this red grid is only a storyboard marker and must not appear in the generated video. The final video should use a realistic anonymous adult presenter with a natural visible face, no face identity reference, no celebrity likeness, no red grid, and no blank face.

## Review Questions

- Does the first panel stop scrolling in under 2 seconds?
- Does every panel advance the selling story?
- Does the camera style match the reference blueprint?
- Does the storyboard preserve the reference video's model/host role when one exists?
- Does each panel state what was preserved from the reference and why anything changed?
- Does the visual style stay coherent across panels?
- Are reference stickers, badges, checkmarks, corner marks, phone-frame overlays, and feature tags carried into the adapted storyboard?
- Are transition sounds, sticker pops, cloth sounds, tap sounds, stretch sounds, and CTA accents described where they matter?
- If a person appears, is the person truthful, anonymous, adult, and secondary to the product?
- Is there exactly one main action per panel?
- Are claims conservative and supported by user facts or visible evidence?
- Is the final panel a clean CTA or hero lockup?
- Would the prompt still work if exact text rendering drifts?
- Is there exactly one readable text layer, without duplicated subtitles when voiceover is present?

## Completion Bar

Do not submit paid generation until the storyboard:

- totals exactly the target duration
- has the same number of panels as the adapted `shot_plan`
- has a generated visual storyboard sheet image saved locally
- has the visual storyboard sheet included in the Seedance submission with product images
- has no empty panel fields
- preserves reference model/host presence, action logic, camera movement, sticker/overlay style, sound-effect rhythm, caption style, and scene style unless a concrete adaptation reason is recorded
- has a resolved readable text layer policy and does not duplicate voiceover as a second subtitle layer by default
- has no copied reference captions or brands
- has no attempt to use sketch, oil-painting, blur, crop, or other style conversion to bypass face-review limits
- if a visible face appears in the storyboard sheet, uses the red 5x6 face-marker rule and instructs the final video prompt not to render the marker
- has no unsupported medical, safety, efficacy, antibacterial, ranking, certification, warranty, price, or discount claims
- has product identity constraints repeated in panel-level language
