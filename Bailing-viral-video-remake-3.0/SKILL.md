---
name: Bailing-viral-video-remake-3.0
description: Analyze and recreate viral short-form reference videos without CreatOK API, including shot breakdown, camera movement, pacing, voiceover copy, stickers, overlays, sound effects, hook structure, product adaptation, Seedance prompt writing, and final MP4 generation through Volcengine Ark Seedance 2.0 Fast. Use when the user asks for viral short video recreation, TikTok/Douyin/Xiaohongshu reference-video adaptation, video breakdown with copywriting, productized remake scripts, or generating a reference-duration, reference-ratio, 480p Seedance video from a reference short video and product assets, capped at 15 seconds.
---

# Xinghe Viral Short Video Remake

Create one finished short-form video by analyzing a reference video, rewriting its viral logic for the user's product or topic, and generating the final MP4 with Volcengine Ark Seedance 2.0 Fast. Do not depend on CreatOK API.

The user-facing skill display name is "星河爆款短视频二创2.0". Keep all operational instructions and generated artifacts in English unless the user explicitly asks for localized copy or voiceover.

## Non-Negotiable Outcome

End with a generated video file whenever the user provides enough inputs and generation is not explicitly disabled.

A visual director storyboard sheet image is mandatory for every paid video generation. Text-only `storyboard.json` or `storyboard.md` is not enough. Before calling Seedance, generate one local `storyboard_sheet.png` or equivalent visual storyboard sheet, show or return it when approval is requested, and submit it to the video model together with the product image. Do not skip this step for speed, uncertainty, or because the user did not explicitly ask to see the storyboard. Use a missing-storyboard override only for explicit diagnostic runs, never for normal paid recreation generation.

Default generation settings:

- Model: `doubao-seedance-2-0-fast-260128`
- Resolution: `480p`
- Ratio: follow the reference video aspect ratio by default; choose the nearest Seedance-supported ratio (`9:16`, `16:9`, `1:1`, `3:4`, `4:3`, or `21:9`)
- Duration policy: match the reference video duration when the reference is `<= 15` seconds; cap the generated video at `15` seconds when the reference is longer than `15` seconds
- Audio: enabled by default
- Voiceover language: Mandarin Chinese by default for Chinese ecommerce requests
- API: Volcengine Ark, using local `ARK_API_KEY`

If `ARK_API_KEY` is missing, produce the complete analysis, adapted brief, and Seedance prompt, then stop before paid generation and explain only the missing local configuration.

## Duration Policy

Always derive the output duration from the reference video metadata before writing the adapted brief:

- If `source.duration_seconds <= 15`, set `raw_target_duration_seconds = source.duration_seconds`.
- If `source.duration_seconds > 15`, set `raw_target_duration_seconds = 15`.
- Set `target_duration_seconds = round_half_up(raw_target_duration_seconds)` and submit only this integer value to Seedance. Example: `10.1 -> 10`, `10.5 -> 11`, `12.4 -> 12`.
- Seedance supports 4-15 second generation. If `target_duration_seconds < 4`, stop before paid generation and ask whether to pad the remake to 4 seconds with a product hero hold or use another video model/editing workflow. Do not silently change a sub-4-second reference into a longer video.
- Use the same target duration in the adapted brief `duration`, `shot_plan`, adapted voiceover, adapted on-screen text, storyboard JSON, storyboard sheet notes, Seedance prompt, and generation command.
- Do not default to 15 seconds when the reference video is shorter than 15 seconds.
- If the reference video is longer than 15 seconds, preserve the strongest transferable opening and conversion structure inside the first 15 seconds, or compress the reference structure into 15 seconds while keeping shot order, pacing proportions, model/action logic, stickers, SFX, and voiceover rhythm.
- The sum of all `shot_plan` durations must equal integer `target_duration_seconds` within 0.01 seconds.
- Voiceover and on-screen text timestamps must not exceed `target_duration_seconds`.

## Required Inputs

Require at least one of:

- A local reference video file.
- A supported reference video URL that can be downloaded or inspected.
- A previously extracted set of frames, transcript, and OCR text.

For final generation, also require:

- Product name or topic.
- At least one local product/reference image when product fidelity matters.
- User-provided selling points or visible product facts. Never invent hard claims.

Prefer local files over platform links. If platform links are blocked, ask for the original video file.

## Workflow

1. Run `scripts/analyze_reference_video.py` on the reference video. It writes metadata, sampled frames, coarse shot candidates, a contact sheet, and an analysis JSON scaffold.
2. Read `source.duration_seconds`, `source.width`, `source.height`, `source.source_ratio`, and `source.target_ratio` from the reference analysis. Set `raw_target_duration_seconds = min(source.duration_seconds, 15)`, then set `target_duration_seconds = round_half_up(raw_target_duration_seconds)`. If the reference video is 15 seconds or shorter, the generated video duration must equal the rounded integer reference duration. If the reference video is longer than 15 seconds, the generated video duration must be exactly 15 seconds. Set the output ratio to the nearest Seedance-supported ratio for the reference dimensions unless the user explicitly overrides it. Every later storyboard, voiceover, on-screen text, prompt, and generation command must use the same integer target duration and output ratio.
3. Ensure local ASR is ready. If `~/.codex/cache/xinghe-asr/asr_ready.json` is missing or stale, run `scripts/setup_local_asr.py` once before reference analysis. Use the `base` model by default for Chinese short-video speech; `tiny` is faster but less reliable for noisy slogan-style audio.
4. Run `scripts/analyze_reference_audio.py` on the same reference video. This is required for local voiceover detection. It extracts the audio track with local ffmpeg and tries local ASR backends. Keyframe-only analysis is incomplete.
5. Inspect the extracted frames/contact sheet and the audio analysis JSON. Fill the analysis JSON with shot meaning, model/host presence, camera movement, subject action, edit rhythm, audio cues, sound effects, OCR text, voiceover transcript, caption style, sticker/overlay style, scene style, props, and copywriting roles. On Windows, terminal-rendered Chinese ASR text is not authoritative; always read the UTF-8 JSON fields or `safe_transcript_files` paths written by the audio script.
6. If local ASR detects speech, preserve the voiceover layer as a core reference asset with timestamps, speaker energy, pacing, and generation rule. If local ASR runs and finds no speech, mark the reference as sticker/SFX-driven unless other evidence proves speech. If ASR is unavailable or fails, mark `voiceover_layer.detected` as unknown/unextracted; do not treat OCR captions as confirmed voiceover.
7. If on-screen text is visible, perform OCR with any available local OCR tool or read it from the frames manually. Do not skip the on-screen-text layer.
8. Align ASR and OCR: determine whether captions are spoken subtitles, standalone stickers, or both. Record the relationship in `voiceover_layer.relationship_to_ocr`.
9. Run `scripts/build_adapted_voiceover.py` after ASR/OCR alignment with `--target-duration <target_duration_seconds>`. Use ASR for speech presence and timing, use OCR/manual caption context for text correction, then adapt the voiceover with the default `product_swap` policy unless the user explicitly provided copy direction or selling-point requirements. Never pass raw ASR text directly into the final video prompt.
10. Before writing `adapted_on_screen_text`, resolve the readable text layer policy. If a spoken voiceover is preserved, do not also create line-by-line subtitles by default. Keep only sparse reference-style stickers, punch headlines, feature badges, or CTA lockups unless the reference is explicitly caption-driven or the user asks for subtitles.
11. Read `references/recreation_schema.md` and format the complete breakdown using that schema. First create a reference-faithful storyboard of the original video, then create the adapted storyboard for the user's product.
12. Analyze the viral mechanism: hook, tension, proof, desire trigger, pacing, and CTA.
13. Run `scripts/build_reference_blueprint.py` on the completed analysis JSON to create a compact `reference_video_blueprint.json`.
14. Rewrite the concept for the user's product or topic with minimal adaptation. Preserve all transferable reference-video elements: model/host presence, actions, shot order, framing, camera movement, scene design, props, sticker/overlay language, caption style, copy rhythm, sound effects, voiceover policy, voiceover style blueprint, and CTA logic. Replace only the original product and disallowed elements. If the user did not provide any copy direction, selling points, or creative requirements, do not rewrite the spoken copy into a new sales script; use the product-swap voiceover policy below.
15. Build a Seedance-ready recreation brief with exact `duration = target_duration_seconds`, exact `ratio = source.target_ratio`, exact shot timing, adapted voiceover, voiceover style blueprint, `caption_layer_policy`, adapted on-screen text intent, sticker/overlay intent, sound-effect intent, model/host role when present in the reference, camera movement, product identity constraints, reference elements to preserve, required replacements, and negative constraints.
16. Run `scripts/build_storyboard.py` before generation. Review the storyboard for visual quality, continuity, narrative logic, product fidelity, readable text layer conflicts, person-presence policy, and claim safety. The storyboard panel count must follow the reference blueprint or product-specific `shot_plan`; do not force a fixed five-panel storyboard.
17. If the storyboard includes people, read `references/person_presence_policy.md` before writing the final Seedance prompt.
18. Run `scripts/build_storyboard_image_prompts.py` to create one visual storyboard sheet prompt. Then generate a single visual storyboard sheet image every time before paid video generation. Use `references/storyboard_image_generation.md` and `scripts/generate_storyboard_image.py` first, so the deployment helper and OpenAI-compatible HTTP image API handle normal storyboard image generation. Use built-in `image_gen` only as the final fallback when the helper/script/API path is unavailable or fails.
19. When submitting to Seedance, include the storyboard sheet together with product images. Treat product photos as identity references and the storyboard sheet as a narrative, camera-logic, model/action, layout, sticker/overlay, caption-style, sound-cue, and per-shot scene-style reference; the storyboard sheet must not override product appearance. If the storyboard sheet is rejected by the video API's input safety checks, regenerate a safer storyboard sheet and retry the preflight. Do not proceed product-only unless the user explicitly approves a diagnostic override.
20. Read `references/generation_contract.md`.
21. Run `scripts/generate_seedance_video.py` with `--brief-json` or `--prompt-file`. Use `--dry-run` only for validation or when the user explicitly asks not to generate.
22. Return the local MP4 path, task id, model, ratio, resolution, target duration, prompt path, blueprint path, storyboard path, visual panel prompt path, audio analysis path, voiceover correction/adaptation path, voiceover detection result, and any validation warnings.

## Video Breakdown Requirements

Always include copywriting in the breakdown. Treat copy as a core asset, not a secondary note.

Capture these layers:

- Spoken voiceover transcript with timestamps.
- Voiceover detection policy: detected, not detected, or not extracted; ASR backend; confidence; language; speaker style if inferable; relationship to OCR.
- On-screen text from OCR, including hooks, captions, stickers, price text, UI-like overlays, and CTA text.
- Sticker and overlay layer: corner marks, checkmarks, thumbs-up badges, speech bubbles, phone-frame outlines, product-detail circles, arrows, emoji-like icons, feature tags, pop-up timing, entrance animation, and visual weight.
- Copywriting structure: hook formula, pain point, contrast, product entry, proof, benefit, objection handling, and CTA.
- Shot structure: timestamp range, framing, camera movement, subject, action, setting, transition, and visual emphasis.
- Model/host layer: whether people appear, body/face framing, actions, relation to product, and whether the person is a presenter, lifestyle model, hand model, or background presence.
- Visual style layer: scene design, background, lighting, palette, props, surface textures, wardrobe, caption placement, caption typography style, overlay rhythm, and platform-native graphic language.
- Sound-design layer: music bed, spoken rhythm, whooshes, pop sounds, cloth rubs, tap sounds, stretch sounds, transition hits, proof-point sound cues, and CTA accent sounds.
- Rhythm: average shot duration, first-frame tactic, cut density, audio beats, pauses, and speed changes.
- Viral mechanism: why the opening stops scrolling, what keeps attention, and what converts.

If OCR or transcription is unavailable, clearly mark the layer as unavailable or not extracted and explain the evidence used. A complete breakdown must still contain copywriting structure, on-screen text intent, and voiceover intent. Never treat OCR captions as confirmed spoken voiceover unless ASR, manual listening, or user-provided transcript confirms it.

## Reference Analysis Command

Use this command before writing the recreation brief:

```powershell
python "<skill>/scripts/analyze_reference_video.py" `
  --video "C:/path/reference.mp4" `
  --output-dir "C:/path/reference-analysis"
```

Useful options:

- `--sample-count 12` extracts more evenly spaced frames.
- `--scene-threshold 18` makes shot detection more sensitive.
- `--max-scene-frames 16` limits the number of saved scene candidate frames.

Use the generated `contact_sheet.jpg`, `reference-analysis-scaffold.json`, and `frames/` directory to complete the breakdown. The scaffold is intentionally not a final analysis; it is a structured workspace for Codex to fill after inspecting the visual evidence and transcript/OCR layers.

## Local Audio and ASR Command

### First-Use Local ASR Setup

Before the first full run on a new machine, or when ASR is slow/unavailable, run:

```powershell
python "<skill>/scripts/setup_local_asr.py" `
  --model "base" `
  --persist-env
```

On macOS/Linux:

```bash
python "<skill>/scripts/setup_local_asr.py" \
  --model "base"
```

Setup behavior:

- Installs missing Python ASR dependencies with the current Python interpreter.
- Uses `imageio-ffmpeg` as the cross-platform ffmpeg fallback when system ffmpeg is unavailable.
- Uses `HF_ENDPOINT=https://hf-mirror.com` by default for model download stability.
- Writes `~/.codex/cache/xinghe-asr/asr_ready.json`.
- On Windows, `--persist-env` may store `HF_ENDPOINT` and `PYTHONUTF8=1` in the user environment so future Codex runs avoid mojibake and repeated setup.
- On Windows, `--persist-env` also stores `PYTHONIOENCODING=utf-8`. This reduces terminal mojibake, but the workflow must still treat UTF-8 files as the authoritative source.
- The setup step may take several minutes the first time because the local Whisper model must be downloaded. Do not repeat it on every video once `asr_ready.json` exists.

Run this command for every local reference video before writing the recreation brief:

```powershell
python "<skill>/scripts/analyze_reference_audio.py" `
  --video "C:/path/reference.mp4" `
  --output-dir "C:/path/reference-audio" `
  --language "zh"
```

On macOS/Linux:

```bash
python "<skill>/scripts/analyze_reference_audio.py" \
  --video "/path/reference.mp4" \
  --output-dir "/path/reference-audio" \
  --language "zh"
```

The script is local-only and API-free. It extracts audio through local `ffmpeg` and then tries these local ASR backends in order:

- `faster-whisper` Python package.
- `openai-whisper` Python package.
- `whisper.cpp` CLI through `WHISPER_CPP_BIN` and `WHISPER_CPP_MODEL`.

Automatic setup:

- The script automatically attempts to install missing local dependencies during skill execution.
- If `ffmpeg` is missing, it installs `imageio-ffmpeg` and uses the bundled ffmpeg binary.
- If `faster-whisper` is missing, it installs `faster-whisper` with the current Python interpreter and then retries local ASR.
- Use `--no-auto-install` only when the user explicitly wants no environment changes.
- Use `--install-timeout 900` or another value to control the maximum time allowed for each automatic install.
- If automatic installation fails or times out, the workflow must continue with a clear `voiceover not extracted` status instead of silently treating captions as speech.

Cross-platform setup rules:

- Windows: the script can auto-install Python-based dependencies; `FFMPEG_PATH` is optional when `imageio-ffmpeg` can be installed.
- macOS: the script can auto-install Python-based dependencies; system `ffmpeg`, Homebrew ffmpeg, `FFMPEG_PATH`, or `imageio-ffmpeg` are supported.
- If `imageio-ffmpeg` is installed, the script can use its bundled ffmpeg when system ffmpeg is unavailable.

Output files:

- `reference_audio.wav`
- `reference_audio_analysis.json`
- `reference_audio_transcript_utf8.json`
- `reference_audio_transcript_utf8.txt`
- `reference_audio_transcript_unicode_escape.txt`

Windows encoding rule:

- Do not judge ASR transcript quality from PowerShell/Codex terminal rendering. Terminal output may display UTF-8 Chinese as mojibake even when the saved JSON is correct.
- Do not copy terminal-rendered garbled text into the analysis, storyboard, brief, voiceover correction, or final prompt.
- The authoritative transcript sources are `reference_audio_analysis.json -> voiceover_layer.segments`, `selected_transcription.segments`, and `reference_audio_transcript_utf8.json`.
- If Chinese appears garbled only in terminal output, continue by reading the UTF-8 JSON directly. If the saved UTF-8 JSON itself contains mojibake or replacement characters, mark `needs_correction` and correct from OCR/manual context before adapting.

Interpretation rules:

- `voiceover_layer.detected = true`: final remake should preserve a clear voiceover layer unless the user explicitly removes it.
- `voiceover_layer.detected = false` with successful ASR and no segments: the reference is likely music/SFX/sticker driven; do not force voiceover unless the user asks.
- ASR unavailable or failed: voiceover is not extracted, not absent. Do not use OCR captions as confirmed speech. Ask for confirmation, install a local ASR backend, or mark the voiceover decision as unresolved.

Use `voiceover_layer.relationship_to_ocr` to record whether speech matches captions, differs from captions, or whether captions are standalone stickers.

## Voiceover Correction and Adaptation Command

After ASR and OCR/manual caption reading, run:

```powershell
python "<skill>/scripts/build_adapted_voiceover.py" `
  --audio-json "C:/path/reference-audio/reference_audio_analysis.json" `
  --analysis-json "C:/path/reference-analysis-completed.json" `
  --product-name "product name" `
  --product-fact "visible or user-supplied fact" `
  --rewrite-mode "product_swap" `
  --target-duration "12" `
  --output-dir "C:/path/voiceover"
```

On macOS/Linux:

```bash
python "<skill>/scripts/build_adapted_voiceover.py" \
  --audio-json "/path/reference-audio/reference_audio_analysis.json" \
  --analysis-json "/path/reference-analysis-completed.json" \
  --product-name "product name" \
  --product-fact "visible or user-supplied fact" \
  --rewrite-mode "product_swap" \
  --target-duration "12" \
  --output-dir "/path/voiceover"
```

The output `voiceover_correction_and_adaptation.json` is the only safe source for final spoken copy. It includes:

- `reference_voiceover_corrected`: ASR timing plus OCR/context correction.
- `adapted_voiceover`: product-safe Mandarin voiceover aligned to the reference speech rhythm.
- `voiceover_style_blueprint`: speaker energy, emotion, pace, delivery, pause style, and mixing instructions.
- `voiceover_policy`: whether to preserve a spoken voiceover layer.

Rules:

- Use ASR for speech presence and timing.
- Use OCR/manual captions and context to correct ASR wording.
- Read ASR text from UTF-8 JSON/text artifacts, not from terminal-rendered output or chat summaries of terminal output.
- Use the product photo and user-provided facts to adapt only product-specific information by default.
- Never pass raw ASR output directly into Seedance.
- If ASR text contains mojibake or low-quality recognition, keep the timing but rewrite the words from OCR/context.
- If the reference uses punchy slogan delivery, the adapted voiceover must preserve the emotional rhythm even when the exact wording changes.
- Keep adapted lines short enough for the segment duration. Do not write long explanatory ecommerce copy when the reference has fast slogan beats.

Default no-requirement voiceover policy:

- If the user provides no explicit copy direction, selling points, campaign angle, tone change, or requested script, the adapted voiceover is not a new sales script.
- Preserve the reference voiceover sentence structure, tone, speaking style, rhythm, pause pattern, emotional curve, segment count, segment order, and timestamps.
- Only replace product-related information that must change for the user's product: product name, category, fragrance/flavor, material, color, size, specification, visible packaging facts, and user-supplied product facts.
- If a reference line does not contain product-specific information that must change, keep the corrected reference line unchanged except for safety cleanup.
- Do not add new benefits, claims, proof points, objections, CTA lines, or marketing explanations when the user did not provide them.
- Do not turn a casual sharing script into a polished AI ecommerce script by default.
- Use larger script rewriting only when the user explicitly provides copy requirements or asks for a different selling angle.

## Blueprint Command

After the scaffold has been completed, compress it into a reusable reference blueprint:

```powershell
python "<skill>/scripts/build_reference_blueprint.py" `
  --analysis-json "C:/path/reference-analysis-completed.json" `
  --output-dir "C:/path/blueprint"
```

The blueprint is the compact transfer layer. It should contain structure, camera style, edit rhythm, visual style, copy formula, and do-not-copy items. Use the blueprint to guide the product-specific recreation brief instead of feeding a long analysis report into generation.

## Default Mode: Reference-Faithful Remake

The default mode is reference-faithful remake, not generic product-video generation.

Preserve every transferable element from the reference video unless there is a specific replacement reason:

- model/host presence, including whether the reference uses a presenter, lifestyle model, hands, body-only demonstration, or product-only setup
- shot count, shot order, timing proportions, transitions, and edit rhythm
- framing, camera height, lens feel, motion direction, push/pull/pan/tilt/orbit behavior, and handheld or stabilized energy
- subject actions, product interactions, gestures, demonstrations, and reveal logic
- scene design, background, lighting, color palette, props, wardrobe direction, surface textures, and overall platform style
- stickers, badges, checkmarks, corner marks, phone-frame overlays, arrows, feature tags, and pop-up timing
- sound effects, including transition whooshes, sticker pops, cloth handling, taps, stretch sounds, and CTA accents
- voiceover structure, sentence pattern, line length, pacing, tone, hook formula, objection handling, proof rhythm, and CTA logic
- on-screen text role, placement, visual weight, timing, caption rhythm, and graphic style

Do not proactively remove reference elements just to make generation safer or simpler. Replace or omit only:

- the original product, brand, logo, watermark, seller identity, platform UI, or exact brand assets
- exact copied captions, protected scripts, copyrighted characters, distinctive protected artwork, or music lyrics
- unsupported medical, health, safety, antibacterial, anti-allergy, certification, ranking, patent, warranty, price, discount, or comparative claims unless the user supplied proof
- unsafe, sexualized, underage, celebrity-likeness, or identity-continuity requirements
- face-reference upload or any instruction that tries to bypass model review

If the reference video includes a person, preserve that role by writing truthful anonymous adult model/presenter language. Do not require the same face across shots and do not upload a face as an identity reference. If the product category genuinely needs a model, keep the model/action layer instead of forcing a product-only video.

## Storyboard Command

Before paid generation, create a storyboard from the recreation brief:

```powershell
python "<skill>/scripts/build_storyboard.py" `
  --brief-json "C:/path/recreation-brief.json" `
  --blueprint-json "C:/path/reference_video_blueprint.json" `
  --output-dir "C:/path/storyboard"
```

Review `storyboard.md` and `storyboard.json` before generating. The storyboard must confirm:

- every panel has a visual objective, framing, camera movement, action, voiceover, and text intent
- every panel states which reference elements are preserved and why any reference element changed
- panel count follows the reference blueprint or recreation brief shot count
- product identity remains stable across panels
- any person presence follows `references/person_presence_policy.md`
- scene style and lighting are consistent
- all panels total exactly the target duration
- copywriting flows from hook to proof to CTA
- unsupported claims and copied reference elements are removed

## Visual Storyboard Sheet

A storyboard is incomplete if it only contains text. For every normal paid Seedance recreation run, create one director storyboard sheet prompt before video generation:

```powershell
python "<skill>/scripts/build_storyboard_image_prompts.py" `
  --storyboard-json "C:/path/storyboard.json" `
  --output-dir "C:/path/storyboard-panels"
```

Then use image generation to create a single `storyboard_sheet.png`. This visual storyboard sheet is mandatory before paid Seedance generation. The sheet must contain one frame cell per storyboard panel, arranged in reading order, with short text notes for time, shot purpose, preserved reference element, reference-matched scene style, model/action role, camera movement, action, voiceover, and on-screen text intent. The number of frame cells must equal the storyboard panel count, which comes from the reference-video shot structure or the adapted brief. Do not force a fixed number such as five panels.

The storyboard sheet is for director review and pre-generation approval only. The final Seedance prompt should still use the structured brief and storyboard logic, not long image-generation prompts copied verbatim.

When the storyboard sheet is later submitted to Seedance, it becomes a director reference, not an identity reference. It should help the video model understand:

- shot order and narrative logic
- scene style per shot
- model or host role when present in the reference
- action blocking and product interaction
- camera movement and framing
- sticker, overlay, caption, and sound-cue timing

It must not override the product photo. Product shape, color, packaging, logo position, label layout, printed text placement, material, and accessories must come from the product image.

Storyboard image quality rules:

- Prefer one clear portrait storyboard sheet with one cell per shot, arranged in reading order.
- Normal storyboard sheets must request one of two standard sizes: `2048x1536` for landscape/grid-heavy sheets or `1536x2048` for portrait/tall sheets. Choose the orientation from the storyboard layout. If the user asks for high resolution or 4K, request the highest available image size, then verify the actual saved pixel dimensions because image providers may return a different size.
- Avoid overly wide storyboard sheets with realistic faces when Seedance input safety rejects them. If the storyboard is rejected, regenerate a Seedance-safe sheet with clearer product focus and the face-marker rule below, then retry with the storyboard sheet included. Do not bypass the storyboard requirement unless the user explicitly approves a diagnostic exception.
- Keep frame cells visually close to the reference video's style: scene design, lighting, camera height, model action, stickers, captions, and sound-effect notes must match the reference instead of becoming generic product-ad visuals.

## Storyboard Image Generation Command

For normal storyboard image generation, run:

```powershell
python "<skill>/scripts/generate_storyboard_image.py" `
  --storyboard-json "C:/path/storyboard.json" `
  --reference-image "C:/path/product-primary.png" `
  --output-dir "C:/path/storyboard-image"
```

The script first uses `%LOCALAPPDATA%/ApiCodexOneClick/tools/generate-image.ps1`. If the helper is missing or fails, it falls back to OpenAI-compatible HTTP endpoints, defaulting to `https://xinghe.xin/v1/images/edits` for reference-image generation and `https://xinghe.xin/v1/images/generations` for text-only generation. It writes `storyboard_sheet.png`, `storyboard-image-manifest.json`, and `storyboard-image-result.json`. Use built-in `image_gen` only as the last fallback if this script path cannot produce a local saved storyboard sheet.

## Storyboard Face-Marker Rule

If a storyboard sheet contains a visible person face, do not use sketch, oil-paint, blank-face, blur, mask, or face-removal styles as the default. Use a realistic ecommerce storyboard frame and add a red 5x6 grid overlay covering the entire face area. The grid must be medium-thickness red lines, clearly visible, and limited to the face area. Keep the background, clothing, pose, product, and composition unchanged.

When the storyboard sheet is submitted to Seedance, the final video prompt must explicitly say that the red face grid is only a storyboard marker. The final video must show a realistic anonymous adult presenter with a natural visible face, no red grid, no blank face, no mask, no blur, no celebrity likeness, and no face identity reference.

If Seedance rejects a storyboard image because of person/privacy safety, do not remove the reference video's person layer by default. First try a safer storyboard sheet using the red 5x6 face grid marker while preserving the model role, pose, action, clothing, scene style, and product interaction. Only fall back to product-only storyboard guidance when the generation API repeatedly rejects all person-storyboard inputs.

## Recreation Rules

- Recreate the viral structure, pacing, shot logic, model/host role, actions, camera language, scene style, sticker/overlay language, sound effects, caption style, voiceover rhythm, and conversion logic.
- Do not copy exact protected scripts, captions, logos, watermarks, characters, music lyrics, platform UI, or brand-specific creative assets.
- Replace the reference video's product, claims, and proof with user-supplied facts or directly visible product evidence. Keep all other transferable elements unless they appear in the disallowed list.
- Keep claims conservative. Do not invent medical, safety, efficacy, nutritional, durability, ranking, certification, warranty, discount, or price claims.
- For ecommerce, keep the product identity stable across all shots: shape, color, packaging, label layout, logo position, printed text placement, material, accessories, and visible components.
- Prefer one clear action per shot. Avoid overloaded prompts that ask Seedance to perform many changes at once.
- Preserve the emotional arc: hook, curiosity, demonstration, payoff, CTA.
- Keep the final Seedance prompt concrete, timed, and visually executable.

## Seedance Prompt Rules

The final prompt must include:

- One-line video objective.
- Exact duration, reference-matched ratio, resolution intent, and audio intent.
- Reference image identity constraints.
- Reference-fidelity mode: preserve all transferable elements from the reference video and only replace/omit elements listed in the replacement policy or negative constraints.
- A shot timeline matching the adapted storyboard or reference shot count, totaling exactly the target duration.
- Model/host role when the reference contains people.
- Sticker/overlay intent per shot, including what should appear, where it appears, and when it pops in.
- Sound-effect intent per shot, including whoosh, pop, tap, cloth, stretch, and CTA accent cues.
- Voiceover script and voiceover style blueprint when the reference has speech; otherwise an explicit no-spoken-voiceover audio policy. Always include on-screen text intent, even if the model should avoid hard-rendered readable text.
- Camera movement per shot.
- Product/action constraints per shot.
- Negative constraints.

For Seedance reliability, request simple cuts and stable camera movement. Text must be generated in the same one-pass Seedance video and should not be added later unless the user explicitly requests a separate editing workflow. Because Seedance can drift on text, reduce the number of hard-readable text moments, keep text short, and lock one caption typography system across the whole prompt.

Voiceover style transfer rules:

- Do not only provide the adapted script. Also provide the reference-style speaker energy, emotion, pace, delivery shape, pause pattern, and audio mix rule.
- If the reference has excited slogan-like delivery, keep the adapted script short, punchy, and rhythmically close to the reference speech segments.
- If native Seedance voiceover ignores or flattens the style, shorten the script, emphasize the style blueprint near the top of the prompt, and make the audio direction say that voiceover is louder and more forward than music and SFX.
- Native Seedance voiceover is not guaranteed to perfectly match timing. For normal one-pass generation, keep the script compact, rhythmic, and short enough for native Seedance voiceover.

## Voiceover And Readable Text Layer Policy

Avoid double subtitles. Seedance may create a caption-like text layer from spoken voiceover when the prompt also asks for on-screen text. Therefore every adapted brief must resolve `caption_layer_policy` before video generation.

Supported modes:

- `voiceover_only`: use spoken voiceover as the copy layer. Do not render readable subtitles, transcript captions, karaoke captions, lower-third subtitles, or duplicated text. Use this when the reference mainly uses speech and no important visible sticker/headline layer.
- `sparse_stickers`: default when voiceover is preserved and the reference also has visible text. Keep only sparse reference-style stickers, punch headlines, feature badges, or CTA lockups. Do not render line-by-line subtitles matching the voiceover.
- `caption_driven`: use visible captions as the single readable text layer. Use this only when the reference is truly caption-led or the user explicitly asks for subtitles. If voiceover is also present, do not create a second subtitle layer.
- `no_readable_text`: no readable captions, stickers, badges, or random text.

Rules:

- Do not include both adapted spoken voiceover and per-sentence on-screen subtitles by default.
- If `adapted_on_screen_text` overlaps heavily with `adapted_voiceover`, treat it as timing/style evidence unless `caption_layer_policy.mode = caption_driven`.
- With preserved voiceover, `adapted_on_screen_text` should describe sticker/headline/CTA intent, not a full transcript subtitle track.
- The storyboard sheet may show the intended sticker/headline text style, but it must not visualize two readable layers for the same spoken line.
- The final Seedance prompt must explicitly say "Use exactly one readable text layer" and forbid duplicate subtitles.

## Generation Command

Use a brief JSON when possible. Normal paid generation must include `--storyboard-image`; missing-storyboard generation is only allowed for explicit diagnostic runs.

```powershell
python "<skill>/scripts/generate_seedance_video.py" `
  --brief-json "C:/path/recreation-brief.json" `
  --image-path "C:/path/product-primary.png" `
  --storyboard-image "C:/path/storyboard-sheet.png" `
  --output-dir "C:/path/out"
```

Use a prompt file when the prompt is already complete:

```powershell
python "<skill>/scripts/generate_seedance_video.py" `
  --prompt-file "C:/path/seedance-prompt.txt" `
  --image-path "C:/path/product-primary.png" `
  --storyboard-image "C:/path/storyboard-sheet.png" `
  --output-dir "C:/path/out"
```

Use `--dry-run` to validate inputs and write artifacts without submitting a paid Ark task.

## One-Pass Caption Consistency

Do not add captions later by default. The video should be generated as one finished Seedance output unless the user explicitly asks for a separate editing workflow.

When the reference video uses visible captions, slogan stickers, CTA text, or feature badges, treat caption style as a controlled visual system:

- First apply `caption_layer_policy`. If the mode is `voiceover_only`, do not request readable captions. If the mode is `sparse_stickers`, request only sparse sticker/headline/CTA text, not transcript subtitles. If the mode is `caption_driven`, captions are the single readable text layer.
- Define one global caption typography lock before the shot timeline: bold white Chinese ecommerce headline text, heavy sans-serif, slight italic/slant if the reference uses it, thick dark outline, soft drop shadow, high contrast, no gray subtitle boxes, no thin subtitle font.
- Reuse the same font weight, outline thickness, shadow, color, and perspective across all shots.
- Allow at most two text styles: primary punch headline and final brand lockup. Do not let middle shots switch to a small subtitle style unless the reference clearly does that.
- Keep each readable line short enough for Seedance: preferably 4-10 Chinese characters, one line when possible, two lines only for the final brand lockup.
- Specify caption placement per shot using stable zones: center punch, lower-center punch, right hero lockup, or top sticker. Do not mix random lower-third subtitles with large headline stickers.
- Ask the model to maintain consistent typography from the storyboard sheet and not reinterpret captions as normal subtitles.
- Always forbid duplicate subtitle layers when voiceover is present. The model must not render one auto-subtitle layer plus one requested on-screen text layer.
- If text consistency is more important than exact wording, prioritize matching font style, scale, placement, and rhythm over rendering every character perfectly.

## Quality Check

Before returning the result, check:

- A reference blueprint exists when a reference video was supplied.
- A storyboard exists and has been reviewed before paid generation.
- A visual storyboard sheet image exists locally and is submitted to Seedance with product images.
- The brief and prompt explicitly preserve model/host presence, actions, camera movement, caption style, scene style, and copy rhythm when those elements exist in the reference.
- Any removed reference element has a concrete adaptation reason.
- If people appear, the prompt uses truthful anonymous adult lifestyle-model language and does not attempt to bypass face-review limits.
- The adapted script follows the default product-swap policy when the user gave no copy requirements, or follows the explicit user copy direction when provided. It must remove protected brand slogans and unsupported claims.
- The prompt includes spoken copy when voiceover is preserved, or an explicit no-spoken-voiceover policy when speech is absent. It always includes on-screen text intent.
- The prompt has a resolved `caption_layer_policy` and explicitly allows only one readable text layer. When voiceover is preserved, it must not also request line-by-line transcript subtitles unless `caption_driven` was explicitly selected.
- If readable captions or sticker text matter, the prompt contains a one-pass caption typography lock and per-shot caption placement rules.
- Shot durations total the target duration.
- Ratio follows the reference-video target ratio unless the user explicitly overrides it; resolution is `480p`, model is `doubao-seedance-2-0-fast-260128` unless the user explicitly overrides.
- Product claims come only from the user or visible evidence.
- Product identity constraints are explicit.
- The final MP4 path exists after generation.

## Optimization Notes

- If the first generation drifts, reduce shot count, shorten actions, use fewer reference images, and make the product identity constraints stricter.
- If stickers or sound effects feel weak, strengthen them in the brief as a separate overlay-and-sound layer rather than hiding them inside the general caption or audio paragraph.
- If text rendering is poor, move text into voiceover and describe on-screen text as graphic intent rather than exact required typography.
- If the video feels generic, strengthen the first 2 seconds: visible product, immediate motion, conflict, or curiosity gap.
- If product fidelity is weak, use one clear primary image and one detail image rather than many mixed references.
