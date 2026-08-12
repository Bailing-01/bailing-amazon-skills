# Seedance Generation Contract

Use this contract before every paid generation request.

## Defaults

- Provider: Volcengine Ark
- Model: `doubao-seedance-2-0-fast-260128`
- Resolution: `480p`
- Ratio: follow the reference video aspect ratio by default; choose the nearest Seedance-supported ratio (`9:16`, `16:9`, `1:1`, `3:4`, `4:3`, or `21:9`)
- Duration: integer reference duration after round-half-up when the reference is 4-15 seconds; capped at 15 seconds when the reference is longer than 15 seconds
- Audio: enabled
- Output: local `.mp4`

## Required Safety Checks

- Confirm `ARK_API_KEY` is configured locally. Never ask the user to paste it into chat.
- Confirm every image path exists and is a JPG, JPEG, PNG, or WebP file.
- Confirm the prompt does not contain unresolved placeholders.
- Confirm the target duration follows the integer duration policy and is within Seedance's supported 4-15 second range.
- Confirm the output ratio follows the reference-video target ratio unless the user explicitly overrides it.
- Confirm shot timing totals exactly the target duration.
- Confirm ASR/voiceover text came from UTF-8 artifacts such as `reference_audio_analysis.json` or `reference_audio_transcript_utf8.json`, not from terminal-rendered Chinese text. If the terminal display is garbled but the UTF-8 JSON is valid, continue from the JSON. If the saved JSON itself is garbled, correct from OCR/manual context before generation.
- Confirm the prompt uses reference-faithful remake mode and preserves all transferable reference elements instead of defaulting to a generic product video.
- Confirm a storyboard was generated and reviewed before paid generation.
- Confirm a visual storyboard sheet image exists locally. Text-only storyboard files are not sufficient.
- Confirm storyboard panel count matches the adapted shot plan; do not force a fixed panel count.
- Confirm one storyboard sheet prompt/image exists with one frame cell per storyboard panel for every normal paid generation.
- Use `scripts/generate_storyboard_image.py` first for storyboard sheet generation. This tries the deployment helper and then the OpenAI-compatible HTTP image API. Use built-in `image_gen` only as the final fallback if the script/helper/API path cannot produce a local saved storyboard sheet.
- Include the storyboard sheet with product images in the Seedance submission as a narrative, camera-logic, and per-shot scene-style reference. Product photos remain the identity references and must override the storyboard sheet for product appearance.
- Do not submit paid Seedance generation without a storyboard sheet unless the user explicitly approved a diagnostic override after being told the storyboard is mandatory.
- Confirm the storyboard sheet and final prompt preserve model/host presence, actions, camera movement, sticker/overlay style, caption style, sound-effect rhythm, scene style, props, and copy rhythm when those elements exist in the reference.
- Confirm the voiceover adaptation mode. If the user gave no explicit copy direction, selling points, campaign angle, or requested script, the adapted voiceover must use product-swap mode: preserve the reference sentence structure, tone, rhythm, segment order, and timing, and only replace product-specific facts needed for the user's product.
- Confirm `caption_layer_policy` is resolved before prompt writing. The final prompt must allow only one readable text layer: `voiceover_only`, `sparse_stickers`, `caption_driven`, or `no_readable_text`.
- If voiceover is preserved, do not also request line-by-line transcript subtitles by default. Keep only sparse stickers, punch headlines, feature badges, or CTA lockups unless `caption_driven` was explicitly selected.
- If `adapted_on_screen_text` overlaps heavily with `adapted_voiceover`, treat it as timing/style evidence or sparse sticker intent and forbid duplicate subtitles.
- Confirm whether readable captions, slogan stickers, CTA text, or feature badges require consistent typography. If yes, add a one-pass caption typography lock to the Seedance prompt: same bold Chinese headline font style, same outline, same shadow, same color, same placement system, and short per-shot text. The normal output is one finished Seedance video, not a separate editing workflow.
- Confirm the prompt explicitly says not to render duplicate subtitles, auto transcript captions, gray subtitle boxes, or a second subtitle layer when voiceover is present.
- Confirm sticker and overlay intent is explicit: corner marks, checkmarks, feature badges, arrows, phone-frame overlays, product-detail circles, and pop timing.
- Confirm sound-effect intent is explicit: transition whooshes, sticker pops, cloth rubbing, taps, stretch sounds, proof-point accents, and CTA accent sounds.
- Confirm every removed or changed reference element has a concrete reason in `required_replacements`, `negative_constraints`, or the panel-level `adaptation_reason`.
- Confirm any person presence follows `person_presence_policy.md`: no face-reference upload, no review-evasion wording, no celebrity likeness, no identity-continuity requirement.
- If a storyboard sheet contains a red 5x6 face grid, confirm the prompt states that the grid is only a storyboard marker and must not appear in the final video.
- Confirm the final video prompt requests a realistic anonymous adult presenter with a natural visible face when the reference video has a presenter, unless the user explicitly asks for product-only output.
- Confirm product claims are user-supplied or visible. If uncertain, remove the claim.
- Confirm the prompt does not request platform UI, exact logos from the reference video, watermarks, copyrighted characters, or copied captions.

## Retry Policy

Do not retry automatically after a paid generation. If the user dislikes the result, revise one major variable at a time:

- product reference image clarity
- prompt length
- shot count
- action complexity
- amount of on-screen text
- number of reference images

## Final Response Payload

Return:

- MP4 path
- task id
- model
- ratio
- resolution
- duration
- prompt path
- blueprint path when available
- storyboard path
- visual storyboard sheet prompt path
- visual storyboard sheet image path
- manifest path
- warnings
